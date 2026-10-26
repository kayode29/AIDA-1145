"""Week 8 Lab 4 scaffold: community-program registration reconciliation.

Implement the TODO functions using Python's standard library. Keep diagnostic
and accepted outputs separate, preserve integer cents, and fail closed when an
acceptance condition is not met. See README.md and contracts/registration_contract.json.
"""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUTPUTS = ROOT / "outputs"
REGISTRATION_COLUMNS = [
    "registration_id", "program_code", "seats", "fee_cents",
    "status", "registered_at", "batch_id",
]
CATALOGUE_COLUMNS = ["program_code", "program_name", "capacity", "catalog_version"]


def read_csv(path: Path, expected_columns: list[str]) -> list[dict[str, str]]:
    """Read a CSV and reject a header that does not exactly match the contract."""
    # TODO: Use csv.DictReader, tolerate a UTF-8 BOM, and validate fieldnames.
    raise NotImplementedError


def validate_source(rows: list[dict[str, str]]) -> None:
    """Validate required values, types, key uniqueness, status, and batch."""
    # TODO: Reject invalid input with an informative ValueError.
    raise NotImplementedError


def duplicate_catalogue_keys(rows: list[dict[str, str]]) -> dict[str, int]:
    """Return each duplicated program_code and its count."""
    # TODO: Counter is imported for this step.
    raise NotImplementedError


def unmatched_registrations(
    active_rows: list[dict[str, str]], catalogue_rows: list[dict[str, str]]
) -> list[dict[str, str]]:
    """Return registration_id/program_code pairs lacking a catalogue match."""
    # TODO: Implement as a key-set/anti-join diagnostic.
    raise NotImplementedError


def join_preview(
    active_rows: list[dict[str, str]], catalogue_rows: list[dict[str, str]]
) -> list[dict[str, str]]:
    """Return a left-join preview without hiding fan-out or unmatched rows."""
    # TODO: Preserve every match; emit one null-catalogue row when unmatched.
    raise NotImplementedError


def main() -> None:
    """Profile candidate, reconcile the approved reference, and write evidence."""
    # TODO: Follow the acceptance conditions in the lab README and contract.
    # Suggested outputs: candidate_join_preview.csv, row_ledger.json,
    # accepted_registrations.csv, and run_summary.json.
    OUTPUTS.mkdir(exist_ok=True)
    raise NotImplementedError("Complete the Week 8 reconciliation pipeline")


if __name__ == "__main__":
    main()
