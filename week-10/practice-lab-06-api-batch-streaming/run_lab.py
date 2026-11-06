"""Offline, fully worked API-to-batch example for AIDA 1145 Week 10.

The JSON files stand in for API responses so this lab runs without a network,
account, credential, or third-party package. The code demonstrates pagination,
deduplication, record validation, freshness checks, release gates, and retry
decisions without making real requests or sleeping.
"""

from __future__ import annotations

import csv
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
OUTPUTS = ROOT / "outputs"
MAX_DATA_AGE_MINUTES = 15
MIN_USABLE_COVERAGE_PERCENT = 95.0
MAX_INVALID_RATE_PERCENT = 2.0
BASE_BACKOFF_SECONDS = 2
MAX_BACKOFF_SECONDS = 60
MAX_RETRIES = 3

# The cursor value returned by page 1 maps to the local file that simulates
# the next API response. In a live client, this mapping would be an HTTP call.
CURSOR_TO_FILE = {"page-02": DATA / "api_page_02.json"}


def read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def read_expected_stations() -> dict[str, dict[str, str]]:
    with (DATA / "expected_stations.csv").open(newline="", encoding="utf-8") as file:
        return {row["station_id"]: row for row in csv.DictReader(file)}


def retrieve_all_pages() -> tuple[list[dict[str, Any]], datetime, int]:
    """Follow each next_cursor until the source says the result is complete."""
    next_file: Path | None = DATA / "api_page_01.json"
    seen_cursors: set[str] = set()
    all_items: list[dict[str, Any]] = []
    retrieved_at: datetime | None = None
    page_count = 0

    while next_file is not None:
        page = read_json(next_file)
        page_count += 1
        page_time = datetime.fromisoformat(page["retrieved_at"])
        if retrieved_at is None:
            retrieved_at = page_time
        elif page_time != retrieved_at:
            raise ValueError("The pages in one batch must use the same retrieval time.")

        items = page.get("items")
        if not isinstance(items, list):
            raise ValueError(f"Page {page_count} has no valid items list.")
        all_items.extend(items)

        cursor = page.get("next_cursor")
        if cursor is None:
            next_file = None
        else:
            if cursor in seen_cursors:
                raise ValueError(f"Pagination loop detected at cursor {cursor!r}.")
            seen_cursors.add(cursor)
            next_file = CURSOR_TO_FILE.get(cursor)
            if next_file is None:
                raise ValueError(f"No response is available for cursor {cursor!r}.")

    if retrieved_at is None:
        raise ValueError("The batch did not contain any API pages.")
    return all_items, retrieved_at, page_count


def retry_example(status: int, retry_after: int | None, retry_number: int) -> tuple[str, str]:
    """Return a teaching decision and delay; never performs an actual wait."""
    if 200 <= status < 300:
        return "accept response; validate its records", ""
    if status == 401:
        return "stop and check credentials securely", ""
    if status not in {429, 500, 502, 503, 504}:
        return "stop and investigate the response", ""
    if retry_number > MAX_RETRIES:
        return "stop after retry limit; alert the operator", ""
    if retry_after is not None:
        return "wait as requested by Retry-After, then retry", str(retry_after)
    delay = min(MAX_BACKOFF_SECONDS, BASE_BACKOFF_SECONDS * (2 ** (retry_number - 1)))
    return "bounded exponential backoff, then retry", str(delay)


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    OUTPUTS.mkdir(exist_ok=True)
    expected = read_expected_stations()
    raw_items, retrieved_at, page_count = retrieve_all_pages()

    # A stable observation_id makes a repeat of the same batch idempotent.
    # Exact repeated page-boundary records count as duplicate deliveries, not
    # as additional station observations. Conflicting repeated IDs are held.
    unique_by_id: dict[str, dict[str, Any]] = {}
    duplicate_deliveries = 0
    conflicting_ids: set[str] = set()
    for item in raw_items:
        observation_id = str(item.get("observation_id", "")).strip()
        if not observation_id:
            continue
        if observation_id in unique_by_id:
            if item == unique_by_id[observation_id]:
                duplicate_deliveries += 1
            else:
                conflicting_ids.add(observation_id)
        else:
            unique_by_id[observation_id] = item

    quarantine: list[dict[str, Any]] = []
    accepted: list[dict[str, Any]] = []
    station_ids_received = {
        str(item.get("station_id", "")).strip()
        for item in unique_by_id.values()
        if str(item.get("station_id", "")).strip() in expected
    }

    for observation_id, item in unique_by_id.items():
        station_id = str(item.get("station_id", "")).strip()
        reasons: list[str] = []

        if observation_id in conflicting_ids:
            reasons.append("CONFLICTING_DUPLICATE_ID")
        if station_id not in expected:
            reasons.append("UNKNOWN_STATION_ID")

        available = item.get("bikes_available")
        capacity = item.get("dock_capacity")
        # bool is a subclass of int in Python, so exclude it explicitly.
        if not isinstance(available, int) or isinstance(available, bool):
            reasons.append("AVAILABLE_COUNT_NOT_INTEGER")
        if not isinstance(capacity, int) or isinstance(capacity, bool):
            reasons.append("CAPACITY_NOT_INTEGER")
        if isinstance(available, int) and not isinstance(available, bool) and available < 0:
            reasons.append("NEGATIVE_AVAILABLE_COUNT")
        if isinstance(capacity, int) and not isinstance(capacity, bool) and capacity <= 0:
            reasons.append("CAPACITY_MUST_BE_POSITIVE")
        if (
            isinstance(available, int)
            and not isinstance(available, bool)
            and isinstance(capacity, int)
            and not isinstance(capacity, bool)
            and available > capacity
        ):
            reasons.append("AVAILABLE_EXCEEDS_CAPACITY")

        try:
            observed_at = datetime.fromisoformat(item["observed_at"])
            if observed_at.utcoffset() != retrieved_at.utcoffset():
                reasons.append("TIMESTAMP_OFFSET_MISMATCH")
            age_minutes = (retrieved_at - observed_at).total_seconds() / 60
            if age_minutes < 0:
                reasons.append("OBSERVATION_IS_IN_THE_FUTURE")
            elif age_minutes > MAX_DATA_AGE_MINUTES:
                reasons.append("STALE_OBSERVATION")
        except (KeyError, TypeError, ValueError):
            observed_at = None
            age_minutes = math.nan
            reasons.append("INVALID_OBSERVED_AT")

        if reasons:
            quarantine.append(
                {
                    "observation_id": observation_id,
                    "station_id": station_id,
                    "observed_at": item.get("observed_at", ""),
                    "bikes_available": available,
                    "dock_capacity": capacity,
                    "age_minutes": "" if math.isnan(age_minutes) else round(age_minutes, 1),
                    "reason": ";".join(reasons),
                }
            )
            continue

        availability_percent = available / capacity * 100
        accepted.append(
            {
                "observation_id": observation_id,
                "station_id": station_id,
                "station_name": expected[station_id]["station_name"],
                "service_area": expected[station_id]["service_area"],
                "observed_at": item["observed_at"],
                "retrieved_at": retrieved_at.isoformat(),
                "age_minutes": round(age_minutes, 1),
                "bikes_available": available,
                "dock_capacity": capacity,
                "availability_percent": round(availability_percent, 1),
            }
        )

    unique_expected_received = len(station_ids_received)
    expected_station_count = len(expected)
    source_coverage = unique_expected_received / expected_station_count * 100
    usable_coverage = len({row["station_id"] for row in accepted}) / expected_station_count * 100
    invalid_count = sum("STALE_OBSERVATION" not in row["reason"] for row in quarantine)
    stale_count = sum("STALE_OBSERVATION" in row["reason"] for row in quarantine)
    invalid_rate = invalid_count / len(unique_by_id) * 100 if unique_by_id else 0.0
    missing_stations = sorted(set(expected) - station_ids_received)
    pagination_complete = True  # retrieve_all_pages returned only after a null cursor.

    gates = [
        {"gate": "Pagination reached a terminal cursor", "observed": str(pagination_complete), "rule": "must be True", "pass": pagination_complete},
        {"gate": "Expected station source coverage", "observed": f"{source_coverage:.1f}%", "rule": "at least 95%", "pass": source_coverage >= 95.0},
        {"gate": "Usable and fresh station coverage", "observed": f"{usable_coverage:.1f}%", "rule": f"at least {MIN_USABLE_COVERAGE_PERCENT:.1f}%", "pass": usable_coverage >= MIN_USABLE_COVERAGE_PERCENT},
        {"gate": "Invalid-record rate", "observed": f"{invalid_rate:.1f}%", "rule": f"at most {MAX_INVALID_RATE_PERCENT:.1f}%", "pass": invalid_rate <= MAX_INVALID_RATE_PERCENT},
    ]
    decision = "ACCEPT" if all(row["pass"] for row in gates) else "HOLD"

    # Demonstrate idempotency without writing the same records twice.
    first_run_keys = set(unique_by_id)
    second_run_keys = first_run_keys | set(unique_by_id)

    retry_cases = [
        (503, 60, 1, "Service asks client to wait 60 seconds"),
        (429, 30, 1, "Rate limit asks client to wait 30 seconds"),
        (503, None, 3, "No Retry-After header; third retry uses capped exponential backoff"),
        (401, None, 1, "Authentication failure is not fixed by repeating the same request"),
    ]
    retry_rows = []
    for status, retry_after, retry_number, explanation in retry_cases:
        action, delay = retry_example(status, retry_after, retry_number)
        retry_rows.append(
            {
                "http_status": status,
                "retry_after_seconds": "" if retry_after is None else retry_after,
                "retry_number": retry_number,
                "action": action,
                "wait_seconds": delay,
                "reason": explanation,
            }
        )

    write_csv(
        OUTPUTS / "accepted_observations.csv",
        ["observation_id", "station_id", "station_name", "service_area", "observed_at", "retrieved_at", "age_minutes", "bikes_available", "dock_capacity", "availability_percent"],
        accepted,
    )
    write_csv(
        OUTPUTS / "quarantine.csv",
        ["observation_id", "station_id", "observed_at", "bikes_available", "dock_capacity", "age_minutes", "reason"],
        quarantine,
    )
    write_csv(
        OUTPUTS / "release_gates.csv",
        ["gate", "observed", "rule", "pass"],
        gates,
    )
    write_csv(
        OUTPUTS / "retry_policy_examples.csv",
        ["http_status", "retry_after_seconds", "retry_number", "action", "wait_seconds", "reason"],
        retry_rows,
    )

    summary = {
        "business_case": "Harbourline Bike Share station availability",
        "retrieved_at": retrieved_at.isoformat(),
        "pages_read": page_count,
        "pagination_complete": pagination_complete,
        "raw_records_received": len(raw_items),
        "unique_observations": len(unique_by_id),
        "duplicate_deliveries_ignored": duplicate_deliveries,
        "expected_stations": expected_station_count,
        "expected_stations_received": unique_expected_received,
        "missing_stations": missing_stations,
        "source_coverage_percent": round(source_coverage, 1),
        "accepted_fresh_observations": len(accepted),
        "usable_fresh_coverage_percent": round(usable_coverage, 1),
        "invalid_observations": invalid_count,
        "stale_observations": stale_count,
        "invalid_rate_percent": round(invalid_rate, 1),
        "age_limit_minutes_inclusive": MAX_DATA_AGE_MINUTES,
        "rerun_unique_keys_after_first_run": len(first_run_keys),
        "rerun_unique_keys_after_second_run": len(second_run_keys),
        "decision": decision,
        "decision_reason": "The batch is held because usable fresh coverage and the invalid-record rate fail the stated release gates." if decision == "HOLD" else "All stated release gates passed.",
    }
    with (OUTPUTS / "run_summary.json").open("w", encoding="utf-8") as file:
        json.dump(summary, file, indent=2)
        file.write("\n")

    print("Harbourline Bike Share API batch summary")
    print(f"Pages read: {page_count}; pagination complete: {pagination_complete}")
    print(f"Records received: {len(raw_items)}; unique observations: {len(unique_by_id)}; duplicate deliveries ignored: {duplicate_deliveries}")
    print(f"Expected station source coverage: {source_coverage:.1f}% ({unique_expected_received}/{expected_station_count})")
    print(f"Usable and fresh coverage: {usable_coverage:.1f}% ({len(accepted)}/{expected_station_count})")
    print(f"Invalid rate: {invalid_rate:.1f}% ({invalid_count}/{len(unique_by_id)}); stale observations: {stale_count}")
    print(f"Idempotency check: unique keys remain {len(first_run_keys)} after a simulated rerun")
    print(f"Release decision: {decision}")
    print("Open outputs/ to inspect the accepted rows, quarantine, gates, retry examples, and run summary.")


if __name__ == "__main__":
    main()
