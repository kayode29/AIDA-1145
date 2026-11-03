"""Starter scaffold for AIDA 1145 Week 9 Graded Lab 5.

Complete the TODO functions using the instructions in README.md. Use only
Python's standard library. Do not change the supplied source CSV files.
"""

from __future__ import annotations

import argparse
import csv
import sqlite3
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Any


LAB_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = LAB_DIR / "data"
OUTPUT_DIR = LAB_DIR / "outputs"

REQUIRED_ORDER_FIELDS = {
    "line_id", "order_id", "order_date", "store_code", "customer_id",
    "sku", "quantity", "unit_price_cents", "discount_rate", "status",
}


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    """Read a UTF-8 CSV and return its rows as dictionaries."""
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames is None:
            raise ValueError(f"CSV has no header row: {path.name}")
        return [dict(row) for row in reader]


def validate_required_fields(rows: list[dict[str, str]], required: set[str], label: str) -> None:
    """Raise a clear error if the CSV is missing a required column."""
    if not rows:
        raise ValueError(f"{label} contains no data rows")
    available = set(rows[0])
    missing = sorted(required - available)
    if missing:
        raise ValueError(f"{label} is missing required columns: {', '.join(missing)}")


def calculate_line_amounts(
    quantity_text: str,
    unit_price_cents_text: str,
    discount_rate_text: str,
) -> tuple[int, int, int]:
    """Return (gross_cents, discount_cents, net_cents) using the lab rule.

    TODO: validate the values, calculate gross cents, round the discount to a
    whole cent with ROUND_HALF_UP, and return the three integer-cent amounts.
    """
    raise NotImplementedError("Complete the line-level money calculation")


def validate_source_rows(order_rows: list[dict[str, str]]) -> dict[str, Any]:
    """Check source identifiers and basic row values; return check evidence.

    TODO: detect duplicate or blank line_id values, invalid statuses, dates,
    non-positive quantities, negative prices, and invalid discount rates. Do
    not silently drop a bad row. Report which rows need investigation.
    """
    raise NotImplementedError("Complete source validation")


def build_dimensions(
    product_rows: list[dict[str, str]],
    customer_rows: list[dict[str, str]],
    store_rows: list[dict[str, str]],
    order_rows: list[dict[str, str]],
) -> dict[str, Any]:
    """Build dimensions and business-key-to-surrogate-key lookups.

    TODO: build product, customer, store, and date dimensions. Keep a distinct
    unknown product member for an unmatched SKU so the completed sale can be
    preserved and reported. Do not invent its product name or category.
    """
    raise NotImplementedError("Complete dimension construction")


def build_fact_rows(
    order_rows: list[dict[str, str]],
    dimensions: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, str]], dict[str, int]]:
    """Build candidate fact rows, exceptions, and a status/row ledger.

    TODO: include only COMPLETED lines in the sales fact, preserve each line
    once, calculate its measures, resolve dimension keys, and record every
    unknown mapping in the exception list. Return counts that also show
    CANCELLED and PENDING rows rather than hiding them.
    """
    raise NotImplementedError("Complete fact construction and row ledger")


def validate_model(
    order_rows: list[dict[str, str]],
    fact_rows: list[dict[str, Any]],
    exceptions: list[dict[str, str]],
    dimensions: dict[str, Any],
) -> dict[str, Any]:
    """Return named validation checks and an ACCEPT/HOLD status.

    TODO: check grain/uniqueness, row preservation, dimension key uniqueness,
    foreign-key coverage, unresolved product mappings, cent totals, and the
    approved/candidate release conditions. ACCEPT only when required checks
    pass for the selected catalogue version and batch.
    """
    raise NotImplementedError("Complete model validation and release status")


def write_sqlite_database(
    db_path: Path,
    dimensions: dict[str, Any],
    fact_rows: list[dict[str, Any]],
) -> None:
    """Create a fresh SQLite database and load the model.

    TODO: create the dimension and fact tables, enable foreign keys, load the
    rows, and ensure repeated runs do not append duplicate facts.
    """
    raise NotImplementedError("Complete schema creation and database loading")


def write_outputs(
    output_dir: Path,
    dimensions: dict[str, Any],
    fact_rows: list[dict[str, Any]],
    exceptions: list[dict[str, str]],
    row_ledger: dict[str, int],
    checks: dict[str, Any],
    db_path: Path,
) -> None:
    """Write the CSV and JSON evidence described in outputs/README.md.

    TODO: use clear column names, keep money in cents in machine-readable
    outputs, and label the selected catalogue version and release status.
    """
    raise NotImplementedError("Complete report and evidence generation")


def run(catalogue_name: str) -> None:
    """Load one named catalogue version, build, validate, and save the run."""
    order_rows = read_csv_rows(DATA_DIR / "order_lines.csv")
    product_file = {
        "candidate": "product_catalog_candidate.csv",
        "approved-v2": "product_catalog_approved_v2.csv",
    }[catalogue_name]
    product_rows = read_csv_rows(DATA_DIR / product_file)
    customer_rows = read_csv_rows(DATA_DIR / "customer_catalog.csv")
    store_rows = read_csv_rows(DATA_DIR / "store_catalog.csv")

    validate_required_fields(order_rows, REQUIRED_ORDER_FIELDS, "order_lines.csv")
    # TODO: validate required headers for the three reference files too.
    source_checks = validate_source_rows(order_rows)
    dimensions = build_dimensions(product_rows, customer_rows, store_rows, order_rows)
    fact_rows, exceptions, row_ledger = build_fact_rows(order_rows, dimensions)
    checks = validate_model(order_rows, fact_rows, exceptions, dimensions)
    checks["source_checks"] = source_checks

    version_output = OUTPUT_DIR / catalogue_name
    db_path = version_output / "cedar_trail_warehouse.sqlite"
    write_sqlite_database(db_path, dimensions, fact_rows)
    write_outputs(version_output, dimensions, fact_rows, exceptions, row_ledger, checks, db_path)
    print(f"Completed {catalogue_name} run. Review {version_output} and its decision evidence.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Cedar Trail Week 9 sales warehouse.")
    parser.add_argument(
        "--catalogue",
        choices=("candidate", "approved-v2"),
        required=True,
        help="Choose the candidate catalogue for Part A or approved-v2 for Part B.",
    )
    args = parser.parse_args()
    run(args.catalogue)


if __name__ == "__main__":
    main()
