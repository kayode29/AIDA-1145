import argparse
import csv
import hashlib
import json
import os
from collections import defaultdict
from pathlib import Path

REQUIRED_COLUMNS = {"ticket_id", "branch", "hours", "revision"}


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def write_csv(path, rows, columns):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def file_hash(path):
    digest = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def run(source, manifest, run_dir, release_dir):
    source = Path(source)
    manifest = Path(manifest)
    run_dir = Path(run_dir)
    release_dir = Path(release_dir)

    if run_dir.exists():
        raise FileExistsError(
            f"Run folder already exists. Use a new run identity: {run_dir}"
        )

    run_dir.mkdir(parents=True)
    release_dir.mkdir(parents=True, exist_ok=True)

    previous_report = release_dir / "report.csv"
    previous_available = previous_report.exists()
    previous_run_id = None

    metadata_path = release_dir / "release_metadata.json"
    if metadata_path.exists():
        try:
            previous_run_id = json.loads(
                metadata_path.read_text(encoding="utf-8")
            ).get("run_id")
        except (OSError, json.JSONDecodeError):
            previous_run_id = "metadata unreadable"

    source_id = source.name
    source_sha256 = None
    input_rows = []
    selected = []
    evidence = []
    conflicts = []
    schema_errors = []
    manifest_data = json.loads(
    manifest.read_text(encoding="utf-8")
)

    try:
        source_sha256 = file_hash(source)

        with source.open("r", newline="", encoding="utf-8-sig") as file:
            reader = csv.DictReader(file)
            headers = set(reader.fieldnames or [])
            missing = sorted(REQUIRED_COLUMNS - headers)
            input_rows = list(reader)

            manifest_data = json.loads(
                manifest.read_text(encoding="utf-8")
            )

        if missing:
            schema_errors.append(
                "Missing required columns: " + ", ".join(missing)
            )
            for number, row in enumerate(input_rows, start=2):
                evidence.append({
                    "row_number": number,
                    "ticket_id": row.get("ticket_id", ""),
                    "branch": row.get("branch", ""),
                    "hours": row.get("hours", ""),
                    "revision": row.get("revision", ""),
                    "classification": "exception",
                    "reason": "Required source column(s) missing"
                })
        else:
            manifest_data = json.loads(
                manifest.read_text(encoding="utf-8")
            )

    except (OSError, json.JSONDecodeError, csv.Error) as error:
        schema_errors.append(f"Input or manifest error: {error}")

    expected_branches = manifest_data.get("expected_branches", [])
    expected_count = manifest_data.get("expected_distinct_tickets", 0)
    handoff_complete = manifest_data.get("handoff_complete", False)
    batch_id = manifest_data.get("batch_id", "unknown")

    if not schema_errors:
        valid_groups = defaultdict(list)

        for number, row in enumerate(input_rows, start=2):
            ticket = (row.get("ticket_id") or "").strip()
            branch = (row.get("branch") or "").strip()
            hours_text = (row.get("hours") or "").strip()
            revision_text = (row.get("revision") or "").strip()

            problems = []

            if not ticket:
                problems.append("Missing ticket ID")

            if branch not in expected_branches:
                problems.append("Branch is not in the manifest")

            try:
                hours = int(hours_text)
                if hours < 0:
                    problems.append("Hours must be non-negative")
            except ValueError:
                hours = None
                problems.append("Hours must be an integer")

            try:
                revision = int(revision_text)
                if revision <= 0:
                    problems.append("Revision must be positive")
            except ValueError:
                revision = None
                problems.append("Revision must be an integer")

            if problems:
                evidence.append({
                    "row_number": number,
                    "ticket_id": ticket,
                    "branch": branch,
                    "hours": hours_text,
                    "revision": revision_text,
                    "classification": "exception",
                    "reason": "; ".join(problems)
                })
                continue

            record = {
                "row_number": number,
                "ticket_id": ticket,
                "branch": branch,
                "hours": hours,
                "revision": revision
            }
            valid_groups[(ticket, revision)].append(record)

        # Identify retransmissions and distinct valid candidates.
        candidates = defaultdict(list)

        for key, records in valid_groups.items():
            unique = {}

            for record in records:
                identity = (
                    record["ticket_id"],
                    record["branch"],
                    record["hours"],
                    record["revision"]
                )

                if identity not in unique:
                    unique[identity] = record
                else:
                    evidence.append({
                        **record,
                        "classification": "retransmitted",
                        "reason": "Identical ticket and revision already received"
                    })

            distinct_records = list(unique.values())

            if len(distinct_records) > 1:
                conflicts.append({
                    "ticket_id": key[0],
                    "revision": key[1]
                })

            candidates[key[0]].extend(distinct_records)

        # Resolve tickets, ensuring that any conflict holds that ticket.
        conflict_tickets = {item["ticket_id"] for item in conflicts}

        for ticket, records in candidates.items():
            if ticket in conflict_tickets:
                for record in records:
                    matching_conflict = any(
                        item["ticket_id"] == ticket
                        and item["revision"] == record["revision"]
                        for item in conflicts
                    )
                    reason = (
                        "Distinct values conflict at this ticket revision"
                        if matching_conflict
                        else "Ticket held because another revision conflicts"
                    )
                    evidence.append({
                        **record,
                        "classification": "exception",
                        "reason": reason
                    })
                continue

            highest = max(record["revision"] for record in records)

            for record in records:
                if record["revision"] == highest:
                    selected.append(record)
                    evidence.append({
                        **record,
                        "classification": "selected",
                        "reason": "Highest valid revision for ticket"
                    })
                else:
                    evidence.append({
                        **record,
                        "classification": "superseded",
                        "reason": "Lower valid revision superseded by newer revision"
                    })

    # Calculate exact row-accounting totals.
    categories = {
        "selected": 0,
        "superseded": 0,
        "retransmitted": 0,
        "exceptions": 0
    }

    for item in evidence:
        classification = item["classification"]
        if classification == "exception":
            categories["exceptions"] += 1
        else:
            categories[classification] += 1

    input_count = len(input_rows)
    accounted = sum(categories.values())
    reconciliation_pass = input_count == accounted

    observed_branches = sorted({item["branch"] for item in selected})
    selected_tickets = sorted({item["ticket_id"] for item in selected})

    gates = {
        "schema_valid": len(schema_errors) == 0,
        "handoff_complete": handoff_complete is True,
        "zero_exceptions": categories["exceptions"] == 0,
        "zero_conflicts": len(conflicts) == 0,
        "ticket_count_matches": len(selected_tickets) == expected_count,
        "all_expected_branches_covered": set(expected_branches).issubset(
            set(observed_branches)
        ),
        "row_reconciliation": reconciliation_pass
    }

    reasons = [
        name for name, passed in gates.items() if not passed
    ]

    if schema_errors:
        reasons.extend(schema_errors)

    decision = "RELEASE" if all(gates.values()) else "HOLD"

    summary = {
        "run_id": run_dir.name,
        "batch_id": batch_id,
        "source_identifier": source_id,
        "source_sha256": source_sha256,
        "decision": decision,
        "input_rows": input_count,
        "counts": categories,
        "accounted_rows": accounted,
        "expected_distinct_tickets": expected_count,
        "observed_distinct_tickets": len(selected_tickets),
        "selected_ticket_ids": selected_tickets,
        "expected_branches": expected_branches,
        "observed_branches": observed_branches,
        "conflicts": conflicts,
        "schema_errors": schema_errors,
        "gates": gates,
        "release_reasons": reasons,
        "previous_report_available": previous_available,
        "previous_report_run_id": previous_run_id
    }

    columns = [
        "row_number", "ticket_id", "branch", "hours",
        "revision", "classification", "reason"
    ]

    write_csv(run_dir / "row_classifications.csv", evidence, columns)
    write_json(run_dir / "summary.json", summary)

    if decision == "RELEASE":
        totals = defaultdict(int)

        for record in selected:
            totals[record["branch"]] += record["hours"]

        report = [
            {
                "branch": branch,
                "total_hours": totals[branch]
            }
            for branch in sorted(totals)
        ]

        selected_output = [
            {
                "ticket_id": item["ticket_id"],
                "branch": item["branch"],
                "hours": item["hours"],
                "revision": item["revision"]
            }
            for item in sorted(selected, key=lambda item: item["ticket_id"])
        ]

        # Prepare all outputs before replacing the last passing report.
        temp_report = release_dir / "report.tmp.csv"
        temp_selected = release_dir / "selected_records.tmp.csv"
        temp_metadata = release_dir / "release_metadata.tmp.json"

        write_csv(
            temp_report,
            report,
            ["branch", "total_hours"]
        )
        write_csv(
            temp_selected,
            selected_output,
            ["ticket_id", "branch", "hours", "revision"]
        )
        write_json(temp_metadata, {
            "run_id": run_dir.name,
            "batch_id": batch_id,
            "source_identifier": source_id,
            "decision": decision
        })

        os.replace(temp_report, previous_report)
        os.replace(
            temp_selected,
            release_dir / "selected_records.csv"
        )
        os.replace(
            temp_metadata,
            metadata_path
        )

        summary["published_report"] = str(previous_report)
        write_json(run_dir / "summary.json", summary)

    print(json.dumps({
        "run_id": run_dir.name,
        "decision": decision,
        "input_rows": input_count,
        "counts": categories,
        "gates": gates,
        "previous_report_available": previous_available
    }, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    parser.add_argument("manifest")
    parser.add_argument("run_dir")
    parser.add_argument("release_dir")
    args = parser.parse_args()

    run(args.source, args.manifest, args.run_dir, args.release_dir)
