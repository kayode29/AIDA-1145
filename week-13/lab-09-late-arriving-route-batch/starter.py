"""Lab 9: Recover a late-arriving route batch."""
import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

REQUIRED = [
    "event_id", "revision", "depot", "units",
    "event_time_utc", "arrived_at_utc"
]


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_time(value):
    if not isinstance(value, str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value
    ):
        raise ValueError("timestamp must use UTC YYYY-MM-DDTHH:MM:SSZ")
    return datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")


def positive_integer(value, field, allow_zero=False):
    if not isinstance(value, str) or not re.fullmatch(r"\d+", value):
        raise ValueError(f"{field} must be an integer")
    number = int(value)
    if number < 0 or (number == 0 and not allow_zero):
        rule = "non-negative" if allow_zero else "positive"
        raise ValueError(f"{field} must be a {rule} integer")
    return number


def load_manifest(path):
    errors = []
    try:
        with path.open("r", encoding="utf-8-sig") as handle:
            manifest = json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        return None, [f"Cannot read manifest: {exc}"], None, None

    if not isinstance(manifest, dict):
        return None, ["Manifest must be a JSON object"], None, None

    batch = manifest.get("batch_id")
    if not isinstance(batch, str) or not batch.strip():
        errors.append("batch_id must be nonempty")

    try:
        cutoff = parse_time(manifest.get("reporting_cutoff_utc"))
    except (ValueError, TypeError) as exc:
        cutoff = None
        errors.append(f"Invalid reporting_cutoff_utc: {exc}")

    try:
        as_of = parse_time(manifest.get("snapshot_as_of_utc"))
    except (ValueError, TypeError) as exc:
        as_of = None
        errors.append(f"Invalid snapshot_as_of_utc: {exc}")

    expected = manifest.get("expected_event_ids")
    if (
        not isinstance(expected, list)
        or any(not isinstance(x, str) or not x.strip() for x in expected)
        or len(expected) != len(set(expected))
    ):
        errors.append("expected_event_ids must be a list of unique nonempty IDs")

    return manifest, errors, cutoff, as_of


def run(manifest_path, source_path, output_path):
    manifest_path = Path(manifest_path)
    source_path = Path(source_path)
    output_path = Path(output_path)

    if output_path.exists():
        raise FileExistsError(
            f"Output folder already exists: {output_path}. Use a new folder."
        )

    output_path.mkdir(parents=True)

    manifest, manifest_errors, cutoff, as_of = load_manifest(manifest_path)
    rows = []
    header_errors = []
    source_error = None
    headers = []

    try:
        with source_path.open("r", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            headers = reader.fieldnames or []
            missing_columns = [c for c in REQUIRED if c not in headers]
            if missing_columns:
                header_errors.append(
                    "Missing required columns: " + ", ".join(missing_columns)
                )
            for row_number, row in enumerate(reader, start=2):
                rows.append({
                    "source_row": row_number,
                    "values": row,
                    "classification": "",
                    "reason": ""
                })
    except (OSError, csv.Error) as exc:
        source_error = f"Cannot read source CSV: {exc}"

    # Every input row receives exactly one classification.
    if manifest_errors or header_errors or source_error:
        reasons = manifest_errors + header_errors
        if source_error:
            reasons.append(source_error)
        for item in rows:
            item["classification"] = "error"
            item["reason"] = "; ".join(reasons)

    else:
        valid = []

        for item in rows:
            row = item["values"]
            problems = []

            event_id = row.get("event_id")
            depot = row.get("depot")

            if not isinstance(event_id, str) or not event_id.strip():
                problems.append("event_id is empty")
            if not isinstance(depot, str) or not depot.strip():
                problems.append("depot is empty")

            revision = None
            units = None
            event_time = None
            arrival_time = None

            try:
                revision = positive_integer(row.get("revision"), "revision")
            except ValueError as exc:
                problems.append(str(exc))

            try:
                units = positive_integer(
                    row.get("units"), "units", allow_zero=True
                )
            except ValueError as exc:
                problems.append(str(exc))

            try:
                event_time = parse_time(row.get("event_time_utc"))
                if event_time > cutoff:
                    problems.append("event time is after reporting cutoff")
            except (ValueError, TypeError) as exc:
                problems.append(f"Invalid event_time_utc: {exc}")

            try:
                arrival_time = parse_time(row.get("arrived_at_utc"))
                if arrival_time > as_of:
                    problems.append("arrival time is after snapshot as-of time")
            except (ValueError, TypeError) as exc:
                problems.append(f"Invalid arrived_at_utc: {exc}")

            if problems:
                item["classification"] = "error"
                item["reason"] = "; ".join(problems)
            else:
                # Include every supplied CSV field in the exact-row signature.
                signature = tuple(row.get(column) for column in headers)
                valid.append({
                    "item": item,
                    "event_id": event_id,
                    "revision": revision,
                    "units": units,
                    "depot": depot,
                    "signature": signature
                })

        # Group valid rows by event ID and revision.
        groups = defaultdict(list)
        for candidate in valid:
            groups[(candidate["event_id"], candidate["revision"])].append(
                candidate
            )

        candidates_by_id = defaultdict(list)
        conflict_ids = set()

        for (event_id, revision), group in groups.items():
            distinct = {}

            for candidate in group:
                signature = candidate["signature"]
                if signature in distinct:
                    candidate["item"]["classification"] = "replay"
                    candidate["item"]["reason"] = (
                        f"Identical retransmission of {event_id} "
                        f"revision {revision}"
                    )
                else:
                    distinct[signature] = candidate

            if len(distinct) > 1:
                conflict_ids.add(event_id)
                for candidate in distinct.values():
                    candidate["item"]["classification"] = "error"
                    candidate["item"]["reason"] = (
                        f"Same-revision conflict: {event_id} "
                        f"revision {revision}"
                    )
            else:
                candidate = next(iter(distinct.values()))
                candidates_by_id[event_id].append(candidate)

        selected = []

        # A conflict prevents selection of every version for that event ID.
        for event_id in sorted(candidates_by_id):
            if event_id in conflict_ids:
                for candidate in candidates_by_id[event_id]:
                    candidate["item"]["classification"] = "error"
                    candidate["item"]["reason"] = (
                        f"Event ID {event_id} is conflicted; no version selected"
                    )
                continue

            versions = candidates_by_id[event_id]
            highest = max(candidate["revision"] for candidate in versions)

            for candidate in versions:
                if candidate["revision"] == highest:
                    candidate["item"]["classification"] = "selected"
                    candidate["item"]["reason"] = (
                        f"Highest valid revision {highest} selected"
                    )
                    selected.append(candidate)
                else:
                    candidate["item"]["classification"] = "superseded"
                    candidate["item"]["reason"] = (
                        f"Revision {candidate['revision']} superseded "
                        f"by revision {highest}"
                    )

    # Count classifications and reconcile every source row.
    counts = Counter(item["classification"] for item in rows)
    for name in ("selected", "superseded", "replay", "error"):
        counts.setdefault(name, 0)

    input_count = len(rows)
    accounted = (
        counts["selected"] + counts["superseded"]
        + counts["replay"] + counts["error"]
    )
    reconciliation_passed = input_count == accounted

    selected_ids = sorted(
        item["values"]["event_id"]
        for item in rows
        if item["classification"] == "selected"
    )

    selected_set = set(selected_ids)
    expected = (
        set(manifest["expected_event_ids"])
        if manifest and isinstance(manifest.get("expected_event_ids"), list)
        and all(isinstance(x, str) for x in manifest["expected_event_ids"])
        else set()
    )

    missing = sorted(expected - selected_set)
    unexpected = sorted(selected_set - expected)

    reasons = []
    if manifest_errors:
        reasons.extend(manifest_errors)
    if header_errors:
        reasons.extend(header_errors)
    if source_error:
        reasons.append(source_error)
    if counts["error"]:
        reasons.append(f"{counts['error']} error row(s)")
    if conflict_ids:
        reasons.append("Same-revision conflicts: " + ", ".join(sorted(conflict_ids)))
    if missing:
        reasons.append("Missing expected IDs: " + ", ".join(missing))
    if unexpected:
        reasons.append("Unexpected selected IDs: " + ", ".join(unexpected))
    if not reconciliation_passed:
        reasons.append("Row-accounting reconciliation failed")

    passed = (
        not reasons
        and not manifest_errors
        and not conflict_ids
        and not missing
        and not unexpected
        and counts["error"] == 0
        and reconciliation_passed
    )
    status = "PASS" if passed else "HOLD"

    # Write row-level evidence.
    evidence_path = output_path / "row_evidence.csv"
    with evidence_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "source_row", "event_id", "revision",
                "classification", "reason"
            ]
        )
        writer.writeheader()
        for item in rows:
            values = item["values"]
            writer.writerow({
                "source_row": item["source_row"],
                "event_id": values.get("event_id", ""),
                "revision": values.get("revision", ""),
                "classification": item["classification"],
                "reason": item["reason"]
            })

    depot_totals = defaultdict(int)
    selected_details = []

    for item in rows:
        if item["classification"] == "selected":
            values = item["values"]
            depot_totals[values["depot"]] += int(values["units"])
            selected_details.append({
                "event_id": values["event_id"],
                "revision": int(values["revision"]),
                "depot": values["depot"],
                "units": int(values["units"])
            })

    # Only a passing run may publish a depot report.
    if passed:
        with (output_path / "depot_totals.csv").open(
            "w", encoding="utf-8", newline=""
        ) as handle:
            writer = csv.writer(handle)
            writer.writerow(["depot", "units"])
            for depot in sorted(depot_totals):
                writer.writerow([depot, depot_totals[depot]])

    summary = {
        "batch_id": manifest.get("batch_id") if manifest else None,
        "manifest": str(manifest_path.resolve()),
        "source": str(source_path.resolve()),
        "manifest_sha256": (
            sha256(manifest_path) if manifest_path.is_file() else None
        ),
        "source_sha256": (
            sha256(source_path) if source_path.is_file() else None
        ),
        "reporting_cutoff_utc": (
            manifest.get("reporting_cutoff_utc") if manifest else None
        ),
        "snapshot_as_of_utc": (
            manifest.get("snapshot_as_of_utc") if manifest else None
        ),
        "expected_event_ids": sorted(expected),
        "selected_event_ids": sorted(selected_set),
        "selected_events": sorted(
            selected_details, key=lambda x: x["event_id"]
        ),
        "missing_event_ids": missing,
        "unexpected_event_ids": unexpected,
        "conflict_event_ids": sorted(conflict_ids) if "conflict_ids" in locals() else [],
        "input_rows": input_count,
        "classification_counts": dict(counts),
        "row_accounting": {
            "input_rows": input_count,
            "accounted_rows": accounted,
            "passed": reconciliation_passed
        },
        "depot_totals": dict(sorted(depot_totals.items())),
        "status": status,
        "reasons": reasons
    }

    with (output_path / "summary.json").open(
        "w", encoding="utf-8"
    ) as handle:
        json.dump(summary, handle, indent=2)

    print(f"Status: {status}")
    print(f"Input rows: {input_count}")
    print(f"Classification counts: {dict(counts)}")
    print(f"Missing IDs: {missing}")
    print(f"Unexpected IDs: {unexpected}")
    print(f"Output: {output_path.resolve()}")
    if passed:
        print(f"Depot totals: {dict(sorted(depot_totals.items()))}")
    else:
        print("No depot report released.")
        print("Reasons: " + "; ".join(reasons))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    parser.add_argument("source")
    parser.add_argument("output")
    args = parser.parse_args()
    run(args.manifest, args.source, args.output)
