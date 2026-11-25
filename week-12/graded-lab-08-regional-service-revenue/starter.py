import argparse
import csv
import hashlib
import json
from collections import defaultdict
from datetime import date
from pathlib import Path

ENTRY_COLUMNS = [
    "entry_id", "work_order", "service_date",
    "site_id", "units", "unit_cents"
]
HISTORY_COLUMNS = ["site_id", "region", "valid_from", "valid_to"]


def read_csv(path):
    with open(path, "r", newline="", encoding="utf-8-sig") as file:
        reader = csv.DictReader(file)
        if reader.fieldnames is None:
            raise ValueError(f"{path} has no CSV header.")
        return reader.fieldnames, list(reader)


def write_csv(path, columns, rows):
    with open(path, "w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as file:
        for block in iter(lambda: file.read(65536), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_iso_date(value):
    parsed = date.fromisoformat(value)
    if parsed.isoformat() != value:
        raise ValueError("Date must use YYYY-MM-DD format.")
    return parsed


def run(entries_path, history_path, output_path):
    entries_path = Path(entries_path)
    history_path = Path(history_path)
    output_path = Path(output_path)

    if output_path.exists() and any(output_path.iterdir()):
        raise ValueError(
            f"Output folder is not empty: {output_path}. "
            "Choose a new output folder."
        )
    output_path.mkdir(parents=True, exist_ok=True)

    summary = {
        "status": "HOLD",
        "release_reasons": [],
        "source_file": entries_path.name,
        "source_sha256": sha256(entries_path),
        "history_file": history_path.name,
        "history_sha256": sha256(history_path)
    }

    source_headers, source_rows = read_csv(entries_path)
    history_headers, history_rows = read_csv(history_path)

    missing_source = sorted(set(ENTRY_COLUMNS) - set(source_headers))
    missing_history = sorted(set(HISTORY_COLUMNS) - set(history_headers))

    if missing_source or missing_history:
        raise ValueError(
            f"Missing source columns: {missing_source}; "
            f"missing history columns: {missing_history}"
        )

    canonical_by_id = {}
    canonical = []
    source_diagnostics = []
    replays = []
    source_errors = []

    for row_number, original in enumerate(source_rows, start=2):
        row = {column: original.get(column, "") or "" for column in ENTRY_COLUMNS}
        entry_id = row["entry_id"]
        errors = []

        for field in ["entry_id", "work_order", "service_date", "site_id"]:
            if not row[field].strip():
                errors.append(f"{field} is empty")

        try:
            service_date = parse_iso_date(row["service_date"])
        except (ValueError, TypeError):
            service_date = None
            errors.append("service_date is not a valid ISO date")

        try:
            units = int(row["units"])
            if str(units) != row["units"] or units <= 0:
                raise ValueError()
        except (ValueError, TypeError):
            units = None
            errors.append("units must be a positive integer")

        try:
            unit_cents = int(row["unit_cents"])
            if str(unit_cents) != row["unit_cents"] or unit_cents < 0:
                raise ValueError()
        except (ValueError, TypeError):
            unit_cents = None
            errors.append("unit_cents must be a non-negative integer")

        if errors:
            classification = "SOURCE_ERROR"
            reason = "; ".join(errors)
            source_errors.append({
                "input_row": row_number,
                "entry_id": entry_id,
                "reason": reason
            })
        elif entry_id in canonical_by_id:
            if row == canonical_by_id[entry_id]:
                classification = "IDENTICAL_RETRANSMISSION"
                reason = "Exact repeat of the canonical entry"
                replays.append({
                    "input_row": row_number,
                    **row
                })
            else:
                classification = "SOURCE_ERROR"
                reason = "Conflicting values for an existing entry_id"
                source_errors.append({
                    "input_row": row_number,
                    "entry_id": entry_id,
                    "reason": reason
                })
        else:
            classification = "CANONICAL"
            reason = "First valid occurrence of this entry_id"
            canonical_by_id[entry_id] = row
            canonical.append({
                **row,
                "_service_date": service_date,
                "_units": units,
                "_unit_cents": unit_cents,
                "_entry_cents": units * unit_cents
            })

        source_diagnostics.append({
            "input_row": row_number,
            "entry_id": entry_id,
            "classification": classification,
            "reason": reason
        })

    reference_diagnostics = []
    valid_history = []

    for row_number, original in enumerate(history_rows, start=2):
        row = {column: original.get(column, "") or "" for column in HISTORY_COLUMNS}
        errors = []

        for field in HISTORY_COLUMNS:
            if not row[field].strip():
                errors.append(f"{field} is empty")

        try:
            valid_from = parse_iso_date(row["valid_from"])
            valid_to = parse_iso_date(row["valid_to"])
            if valid_from >= valid_to:
                errors.append("valid_from must be earlier than valid_to")
        except (ValueError, TypeError):
            valid_from = None
            valid_to = None
            errors.append("invalid effective-date interval")

        if errors:
            reference_diagnostics.append({
                "history_row": row_number,
                **row,
                "classification": "INVALID",
                "reason": "; ".join(errors)
            })
        else:
            valid_history.append({
                **row,
                "_valid_from": valid_from,
                "_valid_to": valid_to
            })
            reference_diagnostics.append({
                "history_row": row_number,
                **row,
                "classification": "VALID",
                "reason": "Valid half-open effective-date interval"
            })

    match_diagnostics = []
    matched_entries = []
    zero_matches = 0
    multiple_matches = 0

    for entry in canonical:
        matches = [
            history for history in valid_history
            if history["site_id"] == entry["site_id"]
            and history["_valid_from"] <= entry["_service_date"] < history["_valid_to"]
        ]

        regions = ";".join(sorted({item["region"] for item in matches}))
        match_count = len(matches)

        if match_count == 0:
            zero_matches += 1
            result = "MISSING"
            reason = "No history row matched site and service date"
        elif match_count > 1:
            multiple_matches += 1
            result = "AMBIGUOUS"
            reason = "More than one history row matched site and service date"
        else:
            result = "MATCHED"
            reason = "Exactly one effective-dated history row matched"
            matched_entries.append((entry, matches[0]["region"]))

        match_diagnostics.append({
            "entry_id": entry["entry_id"],
            "work_order": entry["work_order"],
            "service_date": entry["service_date"],
            "site_id": entry["site_id"],
            "match_count": match_count,
            "matched_regions": regions,
            "result": result,
            "reason": reason
        })

    reasons = []
    if source_errors:
        reasons.append("One or more source rows contain errors.")
    if reference_diagnostics and any(
        row["classification"] == "INVALID" for row in reference_diagnostics
    ):
        reasons.append("One or more site-history intervals are invalid.")
    if zero_matches:
        reasons.append("One or more entries have no effective-dated history match.")
    if multiple_matches:
        reasons.append("One or more entries have multiple effective-dated history matches.")

    input_count = len(source_rows)
    canonical_count = len(canonical)
    replay_count = len(replays)
    error_count = len(source_errors)
    accounting_pass = input_count == canonical_count + replay_count + error_count

    if not accounting_pass:
        reasons.append("Source row accounting does not reconcile.")

    source_revenue = sum(item["_entry_cents"] for item in canonical)
    facts = []

    if not reasons:
        for entry, region in matched_entries:
            facts.append({
                "entry_id": entry["entry_id"],
                "work_order": entry["work_order"],
                "service_date": entry["service_date"],
                "site_id": entry["site_id"],
                "region": region,
                "units": entry["_units"],
                "unit_cents": entry["_unit_cents"],
                "entry_cents": entry["_entry_cents"]
            })

        fact_revenue = sum(item["entry_cents"] for item in facts)
        reconciliation_pass = (
            len(facts) == canonical_count and fact_revenue == source_revenue
        )

        if not reconciliation_pass:
            reasons.append("Fact count or revenue does not reconcile to canonical source.")

    summary.update({
        "status": "PASS" if not reasons else "HOLD",
        "release_reasons": reasons,
        "row_accounting": {
            "input_rows": input_count,
            "canonical_entries": canonical_count,
            "identical_retransmissions": replay_count,
            "source_error_rows": error_count,
            "accounting_pass": accounting_pass
        },
        "matching": {
            "zero_matches": zero_matches,
            "multiple_matches": multiple_matches,
            "matched_entries": len(matched_entries)
        },
        "reference": {
            "valid_intervals": sum(
                row["classification"] == "VALID"
                for row in reference_diagnostics
            ),
            "invalid_intervals": sum(
                row["classification"] == "INVALID"
                for row in reference_diagnostics
            )
        },
        "canonical_source_revenue_cents": source_revenue
    })

    write_csv(
        output_path / "source_diagnostics.csv",
        ["input_row", "entry_id", "classification", "reason"],
        source_diagnostics
    )
    write_csv(
        output_path / "replays.csv",
        ["input_row"] + ENTRY_COLUMNS,
        replays
    )
    write_csv(
        output_path / "source_errors.csv",
        ["input_row", "entry_id", "reason"],
        source_errors
    )
    write_csv(
        output_path / "reference_diagnostics.csv",
        ["history_row"] + HISTORY_COLUMNS + ["classification", "reason"],
        reference_diagnostics
    )
    write_csv(
        output_path / "match_diagnostics.csv",
        ["entry_id", "work_order", "service_date", "site_id",
         "match_count", "matched_regions", "result", "reason"],
        match_diagnostics
    )

    if summary["status"] == "PASS":
        regional = defaultdict(list)
        for fact in facts:
            regional[fact["region"]].append(fact)

        report = []
        for region in sorted(regional):
            items = regional[region]
            report.append({
                "region": region,
                "entry_count": len(items),
                "total_units": sum(item["units"] for item in items),
                "revenue_cents": sum(item["entry_cents"] for item in items),
                "distinct_work_orders": len({
                    item["work_order"] for item in items
                })
            })

        fact_revenue = sum(item["entry_cents"] for item in facts)
        summary["reconciliation"] = {
            "canonical_entry_count": canonical_count,
            "fact_count": len(facts),
            "canonical_revenue_cents": source_revenue,
            "fact_revenue_cents": fact_revenue,
            "fact_count_matches": len(facts) == canonical_count,
            "revenue_matches": fact_revenue == source_revenue,
            "global_distinct_work_orders": len({
                item["work_order"] for item in facts
            })
        }

        write_csv(
            output_path / "facts.csv",
            ["entry_id", "work_order", "service_date", "site_id",
             "region", "units", "unit_cents", "entry_cents"],
            facts
        )
        write_csv(
            output_path / "regional_report.csv",
            ["region", "entry_count", "total_units",
             "revenue_cents", "distinct_work_orders"],
            report
        )
        with open(output_path / "reconciliation.json", "w", encoding="utf-8") as file:
            json.dump(summary["reconciliation"], file, indent=2)

    with open(output_path / "summary.json", "w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2)

    print(f"Decision: {summary['status']}")
    print(f"Input rows: {input_count}")
    print(f"Canonical entries: {canonical_count}")
    print(f"Identical retransmissions: {replay_count}")
    print(f"Source errors: {error_count}")
    print(f"Entries with zero matches: {zero_matches}")
    print(f"Entries with multiple matches: {multiple_matches}")
    print(f"Canonical source revenue: {source_revenue} cents")
    if summary["status"] == "PASS":
        print(f"Released facts: {len(facts)}")
        print(f"Released revenue: {fact_revenue} cents")
    else:
        print("No fact table or regional report was released.")
        for reason in reasons:
            print(f"HOLD reason: {reason}")
    print(f"Output folder: {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Validate and reconcile regional service revenue."
    )
    parser.add_argument("entries", help="Service entries CSV")
    parser.add_argument("history", help="Site history CSV")
    parser.add_argument("output", help="New or empty output folder")
    args = parser.parse_args()
    run(args.entries, args.history, args.output)
