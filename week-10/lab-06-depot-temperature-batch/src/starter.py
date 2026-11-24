
"""Week 10 Graded Lab 6: Depot Sensor Batch."""
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone
import csv
import json
import math

LAB = Path(__file__).resolve().parents[1]


def read_expected():
    with (LAB / "data" / "expected_sensors.csv").open(
        newline="", encoding="utf-8"
    ) as f:
        return {row["sensor_id"] for row in csv.DictReader(f)}


def parse_utc(value):
    """Parse a timestamp and require UTC."""
    if not isinstance(value, str) or not value:
        raise ValueError("Missing or invalid timestamp")

    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))

    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ValueError("Timestamp must be UTC")

    return parsed.astimezone(timezone.utc)


def read_pages(batch_dir):
    """Follow pagination and return readings, retrieval time and page count."""
    readings = []
    retrieved_at = None
    cursor = "page_01"
    visited = set()
    page_count = 0

    while cursor is not None:
        if cursor in visited:
            raise ValueError(f"Repeated pagination cursor: {cursor}")

        visited.add(cursor)
        page_path = batch_dir / f"{cursor}.json"

        if not page_path.is_file():
            raise ValueError(f"Unknown pagination cursor: {cursor}")

        with page_path.open(encoding="utf-8") as f:
            page = json.load(f)

        page_time = page.get("retrieved_at")

        if retrieved_at is None:
            retrieved_at = page_time
            parse_utc(retrieved_at)
        elif page_time != retrieved_at:
            raise ValueError("Pages have inconsistent retrieved_at times")

        items = page.get("items")
        if not isinstance(items, list):
            raise ValueError("Page items must be a list")

        readings.extend(items)
        page_count += 1

        next_cursor = page.get("next_cursor")

        if next_cursor is not None and (
            not isinstance(next_cursor, str) or not next_cursor
        ):
            raise ValueError("Invalid pagination cursor")

        cursor = next_cursor

    return readings, retrieved_at, page_count


def process(readings, retrieved_at, expected):
    """Deduplicate, validate, classify and calculate batch measures."""
    retrieval_time = parse_utc(retrieved_at)

    groups = defaultdict(list)

    for index, row in enumerate(readings):
        if not isinstance(row, dict):
            row = {"_invalid_record": str(row)}

        reading_id = row.get("reading_id")

        # Give records without an ID separate internal identities.
        key = reading_id if isinstance(reading_id, str) and reading_id else (
            f"__missing_id_{index}"
        )
        groups[key].append(row)

    accepted = []
    quarantine = []
    duplicate_count = 0
    conflict_count = 0
    invalid_unique_count = 0
    source_sensors = set()
    usable_sensors = set()

    for reading_id, copies in groups.items():
        # Compare complete records, not just their IDs.
        variants = {}
        for row in copies:
            signature = json.dumps(
                row, sort_keys=True, separators=(",", ":"), default=str
            )
            variants[signature] = row

        duplicate_count += len(copies) - len(variants)

        if len(variants) > 1:
            conflict_count += 1

            for row in variants.values():
                quarantine.append({
                    "reading_id": row.get("reading_id", ""),
                    "sensor_id": row.get("sensor_id", ""),
                    "observed_at": row.get("observed_at", ""),
                    "temperature_c": row.get("temperature_c", ""),
                    "age_minutes": "",
                    "reason": "Conflicting content for the same reading_id"
                })
            continue

        row = next(iter(variants.values()))
        reasons = []
        age_minutes = ""

        if row.get("_invalid_record") is not None:
            reasons.append("Record must be a JSON object")

        if not isinstance(row.get("reading_id"), str) or not row.get("reading_id"):
            reasons.append("Missing or invalid reading_id")

        sensor_id = row.get("sensor_id")

        if sensor_id not in expected:
            reasons.append("Unexpected or missing sensor_id")
        else:
            source_sensors.add(sensor_id)

        temperature = row.get("temperature_c")

        if (
            isinstance(temperature, bool)
            or not isinstance(temperature, (int, float))
            or not math.isfinite(temperature)
            or not -10 <= temperature <= 30
        ):
            reasons.append("temperature_c must be numeric from -10 through 30")

        observed_time = None

        try:
            observed_time = parse_utc(row.get("observed_at"))
            if observed_time > retrieval_time:
                reasons.append("observed_at is later than retrieved_at")
            else:
                age_minutes = round(
                    (retrieval_time - observed_time).total_seconds() / 60, 2
                )
        except (ValueError, TypeError, OverflowError):
            reasons.append("Missing or invalid UTC observed_at timestamp")

        if reasons:
            invalid_unique_count += 1
            quarantine.append({
                "reading_id": row.get("reading_id", ""),
                "sensor_id": sensor_id or "",
                "observed_at": row.get("observed_at", ""),
                "temperature_c": temperature if temperature is not None else "",
                "age_minutes": age_minutes,
                "reason": "; ".join(reasons)
            })
            continue

        if age_minutes > 15:
            quarantine.append({
                "reading_id": row["reading_id"],
                "sensor_id": sensor_id,
                "observed_at": row["observed_at"],
                "temperature_c": temperature,
                "age_minutes": age_minutes,
                "reason": "Stale reading: older than 15 minutes"
            })
            continue

        accepted.append({
            "reading_id": row["reading_id"],
            "sensor_id": sensor_id,
            "observed_at": row["observed_at"],
            "temperature_c": temperature,
            "age_minutes": age_minutes
        })
        usable_sensors.add(sensor_id)

    unique_count = len(groups)
    expected_count = len(expected)

    source_coverage = (
        round(len(source_sensors) / expected_count * 100, 2)
        if expected_count else 0
    )

    usable_coverage = (
        round(len(usable_sensors) / expected_count * 100, 2)
        if expected_count else 0
    )

    invalid_rate = (
        round(invalid_unique_count / unique_count * 100, 2)
        if unique_count else None
    )

    decision = (
        "ACCEPT"
        if unique_count > 0
        and conflict_count == 0
        and usable_coverage >= 95
        and invalid_rate is not None
        and invalid_rate <= 2
        else "HOLD"
    )

    return {
        "accepted": accepted,
        "quarantine": quarantine,
        "unique_reading_count": unique_count,
        "duplicate_delivery_count": duplicate_count,
        "expected_sensor_count": expected_count,
        "source_coverage_percent": source_coverage,
        "usable_and_fresh_coverage_percent": usable_coverage,
        "invalid_reading_count": invalid_unique_count,
        "invalid_reading_rate_percent": invalid_rate,
        "conflict_count": conflict_count,
        "source_sensors_found": len(source_sensors),
        "usable_fresh_sensors": len(usable_sensors),
        "decision": decision
    }


def run_batch(name):
    batch_dir = LAB / "data" / name
    output_dir = LAB / "outputs" / name
    output_dir.mkdir(parents=True, exist_ok=True)

    expected = read_expected()
    readings, retrieved_at, page_count = read_pages(batch_dir)
    results = process(readings, retrieved_at, expected)

    accepted_fields = [
        "reading_id", "sensor_id", "observed_at",
        "temperature_c", "age_minutes"
    ]
    quarantine_fields = accepted_fields + ["reason"]

    with (output_dir / "accepted.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(f, fieldnames=accepted_fields)
        writer.writeheader()
        writer.writerows(results["accepted"])

    with (output_dir / "quarantine.csv").open(
        "w", newline="", encoding="utf-8"
    ) as f:
        writer = csv.DictWriter(f, fieldnames=quarantine_fields)
        writer.writeheader()
        writer.writerows(results["quarantine"])

    summary = {
        "batch": name,
        "retrieved_at": retrieved_at,
        "pages_read": page_count,
        "pagination_complete": True,
        "delivered_row_count": len(readings),
        "unique_reading_count": results["unique_reading_count"],
        "duplicate_delivery_count": results["duplicate_delivery_count"],
        "expected_sensor_count": results["expected_sensor_count"],
        "source_sensors_found": results["source_sensors_found"],
        "source_coverage_percent": results["source_coverage_percent"],
        "usable_fresh_sensors": results["usable_fresh_sensors"],
        "usable_and_fresh_coverage_percent":
            results["usable_and_fresh_coverage_percent"],
        "invalid_reading_count": results["invalid_reading_count"],
        "invalid_reading_rate_percent":
            results["invalid_reading_rate_percent"],
        "conflict_count": results["conflict_count"],
        "accepted_row_count": len(results["accepted"]),
        "quarantine_row_count": len(results["quarantine"]),
        "decision": results["decision"]
    }

    with (output_dir / "summary.json").open("w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"\n{ name.upper() } BATCH")
    print(f"Pages read: {page_count}")
    print(f"Delivered rows: {len(readings)}")
    print(f"Unique readings: {results['unique_reading_count']}")
    print(f"Duplicate deliveries: {results['duplicate_delivery_count']}")
    print(f"Source coverage: {results['source_coverage_percent']}%")
    print(
        "Usable and fresh coverage: "
        f"{results['usable_and_fresh_coverage_percent']}%"
    )
    print(
        "Invalid-reading rate: "
        f"{results['invalid_reading_rate_percent']}%"
    )
    print(f"Conflicts: {results['conflict_count']}")
    print(f"Accepted rows: {len(results['accepted'])}")
    print(f"Quarantine rows: {len(results['quarantine'])}")
    print(f"Decision: {results['decision']}")


if __name__ == "__main__":
    run_batch("initial")
    run_batch("retry")
