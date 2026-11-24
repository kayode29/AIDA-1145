
"""Cedar Trail Sales Warehouse - AIDA 1145 Week 9 Lab 5."""

from __future__ import annotations

import argparse
import csv
import json
import sqlite3
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any


LAB_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = LAB_DIR / "data"
OUTPUT_DIR = LAB_DIR / "outputs"
SQL_DIR = LAB_DIR / "sql"

REQUIRED_ORDER_FIELDS = {
    "line_id", "order_id", "order_date", "store_code", "customer_id",
    "sku", "quantity", "unit_price_cents", "discount_rate", "status",
}

REQUIRED_PRODUCT_FIELDS = {"sku", "product_name", "category"}
REQUIRED_CUSTOMER_FIELDS = {"customer_id", "customer_name", "customer_segment"}
REQUIRED_STORE_FIELDS = {"store_code", "store_name", "region"}


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames is None:
            raise ValueError(f"CSV has no header row: {path.name}")
        return [dict(row) for row in reader]


def validate_required_fields(
    rows: list[dict[str, str]], required: set[str], label: str
) -> None:
    if not rows:
        raise ValueError(f"{label} contains no data rows")
    available = set(rows[0])
    missing = sorted(required - available)
    if missing:
        raise ValueError(
            f"{label} is missing required columns: {', '.join(missing)}"
        )


def calculate_line_amounts(
    quantity_text: str,
    unit_price_cents_text: str,
    discount_rate_text: str,
) -> tuple[int, int, int]:
    """Return gross, discount, and net amounts as whole cents."""
    try:
        quantity = int(quantity_text)
        unit_price = int(unit_price_cents_text)
        discount_rate = Decimal(discount_rate_text)
    except (ValueError, InvalidOperation, TypeError):
        raise ValueError("Quantity, price, or discount rate is invalid")

    if quantity <= 0:
        raise ValueError("Quantity must be greater than zero")
    if unit_price < 0:
        raise ValueError("Unit price cannot be negative")
    if not discount_rate.is_finite() or not Decimal("0") <= discount_rate <= Decimal("1"):
        raise ValueError("Discount rate must be between 0 and 1")

    gross = quantity * unit_price
    discount = int(
        (Decimal(gross) * discount_rate).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
    )
    net = gross - discount
    return gross, discount, net


def validate_source_rows(order_rows: list[dict[str, str]]) -> dict[str, Any]:
    """Check source identifiers, statuses, dates, and numeric values."""
    problems: list[dict[str, str]] = []
    seen_line_ids: set[str] = set()
    allowed_statuses = {"COMPLETED", "CANCELLED", "PENDING"}

    for row_number, row in enumerate(order_rows, start=2):
        line_id = (row.get("line_id") or "").strip()
        status = (row.get("status") or "").strip().upper()

        if not line_id:
            problems.append({
                "row_number": str(row_number),
                "line_id": "",
                "problem": "Blank line_id",
            })
        elif line_id in seen_line_ids:
            problems.append({
                "row_number": str(row_number),
                "line_id": line_id,
                "problem": "Duplicate line_id",
            })
        else:
            seen_line_ids.add(line_id)

        if status not in allowed_statuses:
            problems.append({
                "row_number": str(row_number),
                "line_id": line_id,
                "problem": f"Invalid status: {status}",
            })

        try:
            date.fromisoformat(row["order_date"])
        except (ValueError, TypeError, KeyError):
            problems.append({
                "row_number": str(row_number),
                "line_id": line_id,
                "problem": "Invalid order_date",
            })

        try:
            calculate_line_amounts(
                row["quantity"],
                row["unit_price_cents"],
                row["discount_rate"],
            )
        except (ValueError, KeyError) as error:
            problems.append({
                "row_number": str(row_number),
                "line_id": line_id,
                "problem": str(error),
            })

        for field in ("order_id", "store_code", "customer_id", "sku"):
            if not (row.get(field) or "").strip():
                problems.append({
                    "row_number": str(row_number),
                    "line_id": line_id,
                    "problem": f"Blank required value: {field}",
                })

    return {
        "source_row_count": len(order_rows),
        "invalid_row_count": len(problems),
        "passed": len(problems) == 0,
        "problems": problems,
    }


def build_dimensions(
    product_rows: list[dict[str, str]],
    customer_rows: list[dict[str, str]],
    store_rows: list[dict[str, str]],
    order_rows: list[dict[str, str]],
) -> dict[str, Any]:
    """Build dimensions and lookup dictionaries using stable sorted keys."""
    products = []
    product_key_by_sku: dict[str, int] = {}

    for key, row in enumerate(
        sorted(product_rows, key=lambda item: item["sku"]), start=1
    ):
        product = {
            "product_key": key,
            "sku": row["sku"],
            "product_name": row["product_name"],
            "category": row["category"],
        }
        products.append(product)
        product_key_by_sku[row["sku"]] = key

    # Key 0 is reserved for an unknown product. No product details are guessed.
    product_key_by_sku["UNKNOWN"] = 0

    customers = []
    customer_key_by_id: dict[str, int] = {}
    for key, row in enumerate(
        sorted(customer_rows, key=lambda item: item["customer_id"]), start=1
    ):
        customers.append({
            "customer_key": key,
            "customer_id": row["customer_id"],
            "customer_name": row["customer_name"],
            "customer_segment": row["customer_segment"],
        })
        customer_key_by_id[row["customer_id"]] = key

    stores = []
    store_key_by_code: dict[str, int] = {}
    for key, row in enumerate(
        sorted(store_rows, key=lambda item: item["store_code"]), start=1
    ):
        stores.append({
            "store_key": key,
            "store_code": row["store_code"],
            "store_name": row["store_name"],
            "region": row["region"],
        })
        store_key_by_code[row["store_code"]] = key

    dates = []
    date_key_by_date: dict[str, int] = {}
    unique_dates = sorted({
        row["order_date"] for row in order_rows if row.get("order_date")
    })

    for date_text in unique_dates:
        parsed = date.fromisoformat(date_text)
        date_key = int(parsed.strftime("%Y%m%d"))
        dates.append({
            "date_key": date_key,
            "full_date": date_text,
            "calendar_year": parsed.year,
            "calendar_month": parsed.month,
            "month_name": parsed.strftime("%B"),
        })
        date_key_by_date[date_text] = date_key

    return {
        "products": products,
        "customers": customers,
        "stores": stores,
        "dates": dates,
        "product_key_by_sku": product_key_by_sku,
        "customer_key_by_id": customer_key_by_id,
        "store_key_by_code": store_key_by_code,
        "date_key_by_date": date_key_by_date,
    }


def build_fact_rows(
    order_rows: list[dict[str, str]],
    dimensions: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, str]], dict[str, int]]:
    """Build completed sales facts, exceptions, and the row ledger."""
    facts: list[dict[str, Any]] = []
    exceptions: list[dict[str, str]] = []
    seen_line_ids: set[str] = set()

    ledger = {
        "input_rows": len(order_rows),
        "completed_rows": 0,
        "cancelled_rows": 0,
        "pending_rows": 0,
        "other_status_rows": 0,
        "distinct_completed_orders": 0,
        "fact_rows": 0,
        "completed_units": 0,
    }

    completed_orders: set[str] = set()

    for row in order_rows:
        status = (row.get("status") or "").strip().upper()

        if status == "CANCELLED":
            ledger["cancelled_rows"] += 1
            continue
        if status == "PENDING":
            ledger["pending_rows"] += 1
            continue
        if status != "COMPLETED":
            ledger["other_status_rows"] += 1
            exceptions.append({
                "line_id": row.get("line_id", ""),
                "sku": row.get("sku", ""),
                "problem": f"Unsupported status: {status}",
            })
            continue

        ledger["completed_rows"] += 1
        completed_orders.add(row.get("order_id", ""))

        line_id = (row.get("line_id") or "").strip()
        if not line_id or line_id in seen_line_ids:
            exceptions.append({
                "line_id": line_id,
                "sku": row.get("sku", ""),
                "problem": "Blank or duplicate line_id; fact row not loaded",
            })
            continue
        seen_line_ids.add(line_id)

        try:
            gross, discount, net = calculate_line_amounts(
                row["quantity"],
                row["unit_price_cents"],
                row["discount_rate"],
            )
            date_key = dimensions["date_key_by_date"][row["order_date"]]
            customer_key = dimensions["customer_key_by_id"][row["customer_id"]]
            store_key = dimensions["store_key_by_code"][row["store_code"]]
            quantity = int(row["quantity"])
        except (ValueError, KeyError, TypeError) as error:
            exceptions.append({
                "line_id": line_id,
                "sku": row.get("sku", ""),
                "problem": f"Could not build fact row: {error}",
            })
            continue

        sku = row["sku"]
        product_key = dimensions["product_key_by_sku"].get(sku, 0)

        if product_key == 0:
            exceptions.append({
                "line_id": line_id,
                "sku": sku,
                "problem": "Unmatched product SKU; unknown product key 0 used",
            })

        facts.append({
            "line_id": line_id,
            "order_id": row["order_id"],
            "source_sku": sku,
            "date_key": date_key,
            "product_key": product_key,
            "customer_key": customer_key,
            "store_key": store_key,
            "quantity": quantity,
            "unit_price_cents": int(row["unit_price_cents"]),
            "discount_rate": row["discount_rate"],
            "gross_cents": gross,
            "discount_cents": discount,
            "net_cents": net,
        })
        ledger["completed_units"] += quantity

    ledger["distinct_completed_orders"] = len(completed_orders)
    ledger["fact_rows"] = len(facts)
    return facts, exceptions, ledger


def validate_model(
    order_rows: list[dict[str, str]],
    fact_rows: list[dict[str, Any]],
    exceptions: list[dict[str, str]],
    dimensions: dict[str, Any],
) -> dict[str, Any]:
    """Check warehouse grain, keys, preservation, and release conditions."""
    line_ids = [row["line_id"] for row in fact_rows]
    product_keys = [row["product_key"] for row in dimensions["products"]]
    customer_keys = [row["customer_key"] for row in dimensions["customers"]]
    store_keys = [row["store_key"] for row in dimensions["stores"]]
    date_keys = [row["date_key"] for row in dimensions["dates"]]

    checks = {
        "fact_line_id_unique": len(line_ids) == len(set(line_ids)),
        "fact_rows_match_completed_source_rows": (
            len(fact_rows)
            == sum(
                1 for row in order_rows
                if (row.get("status") or "").upper() == "COMPLETED"
            )
        ),
        "product_dimension_keys_unique": (
            len(product_keys) == len(set(product_keys))
        ),
        "customer_dimension_keys_unique": (
            len(customer_keys) == len(set(customer_keys))
        ),
        "store_dimension_keys_unique": (
            len(store_keys) == len(set(store_keys))
        ),
        "date_dimension_keys_unique": (
            len(date_keys) == len(set(date_keys))
        ),
        "foreign_keys_resolve": all(
            row["product_key"] in {0, *product_keys}
            and row["customer_key"] in set(customer_keys)
            and row["store_key"] in set(store_keys)
            and row["date_key"] in set(date_keys)
            for row in fact_rows
        ),
        "money_is_non_negative": all(
            row["gross_cents"] >= 0
            and row["discount_cents"] >= 0
            and row["net_cents"] >= 0
            for row in fact_rows
        ),
        "net_equals_gross_less_discount": all(
            row["net_cents"]
            == row["gross_cents"] - row["discount_cents"]
            for row in fact_rows
        ),
    }

    unresolved = [
        item for item in exceptions
        if "Unmatched product SKU" in item["problem"]
    ]
    checks["no_unresolved_product_mappings"] = len(unresolved) == 0

    failures = [name for name, passed in checks.items() if not passed]
    if unresolved:
        failures.append("unresolved product mappings require investigation")

    return {
        "catalogue": dimensions.get("catalogue_name", "not specified"),
        "checks": checks,
        "unresolved_product_count": len(unresolved),
        "exception_count": len(exceptions),
        "failures": failures,
        "release_status": "ACCEPT" if not failures else "HOLD",
    }


def write_sqlite_database(
    db_path: Path,
    dimensions: dict[str, Any],
    fact_rows: list[dict[str, Any]],
) -> None:
    """Create a fresh SQLite database and load the warehouse tables."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    schema_path = SQL_DIR / "schema.sql"

    with sqlite3.connect(db_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(schema_path.read_text(encoding="utf-8"))

        connection.executemany(
            """
            INSERT INTO dim_date
            (date_key, full_date, calendar_year, calendar_month, month_name)
            VALUES (:date_key, :full_date, :calendar_year, :calendar_month, :month_name)
            """,
            dimensions["dates"],
        )

        # schema.sql already inserts the special unknown product with key 0.
        connection.executemany(
            """
            INSERT INTO dim_product
            (product_key, sku, product_name, category)
            VALUES (:product_key, :sku, :product_name, :category)
            """,
            [p for p in dimensions["products"] if p["product_key"] != 0],
        )

        connection.executemany(
            """
            INSERT INTO dim_customer
            (customer_key, customer_id, customer_name, customer_segment)
            VALUES (:customer_key, :customer_id, :customer_name, :customer_segment)
            """,
            dimensions["customers"],
        )

        connection.executemany(
            """
            INSERT INTO dim_store
            (store_key, store_code, store_name, region)
            VALUES (:store_key, :store_code, :store_name, :region)
            """,
            dimensions["stores"],
        )

        connection.executemany(
            """
            INSERT INTO fact_sales
            (line_id, order_id, source_sku, date_key, product_key,
             customer_key, store_key, quantity, unit_price_cents,
             discount_rate, gross_cents, discount_cents, net_cents)
            VALUES
            (:line_id, :order_id, :source_sku, :date_key, :product_key,
             :customer_key, :store_key, :quantity, :unit_price_cents,
             :discount_rate, :gross_cents, :discount_cents, :net_cents)
            """,
            fact_rows,
        )


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return

    with path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, content: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(content, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def query_to_rows(db_path: Path, query_file: str) -> list[dict[str, Any]]:
    sql_text = (SQL_DIR / query_file).read_text(encoding="utf-8")
    with sqlite3.connect(db_path) as connection:
        connection.row_factory = sqlite3.Row
        return [
            dict(row)
            for row in connection.execute(sql_text).fetchall()
        ]


def write_outputs(
    output_dir: Path,
    dimensions: dict[str, Any],
    fact_rows: list[dict[str, Any]],
    exceptions: list[dict[str, str]],
    row_ledger: dict[str, int],
    checks: dict[str, Any],
    db_path: Path,
) -> None:
    """Write the CSV and JSON evidence described in outputs/README.md."""
    output_dir.mkdir(parents=True, exist_ok=True)

    write_json(output_dir / "run_summary.json", {
        "catalogue": checks["catalogue"],
        "release_status": checks["release_status"],
        "fact_row_count": len(fact_rows),
        "gross_cents": sum(row["gross_cents"] for row in fact_rows),
        "discount_cents": sum(row["discount_cents"] for row in fact_rows),
        "net_cents": sum(row["net_cents"] for row in fact_rows),
        "unresolved_product_count": checks["unresolved_product_count"],
        "checks": checks["checks"],
        "failures": checks["failures"],
        "database_file": db_path.name,
    })

    write_json(output_dir / "row_ledger.json", row_ledger)
    write_csv(output_dir / "fact_sales.csv", fact_rows)
    write_csv(output_dir / "exception_rows.csv", exceptions)

    reports = {
        "sales_by_month_category.csv": "sales_by_month_category.sql",
        "sales_by_region.csv": "sales_by_region.sql",
        "order_value_summary.csv": "order_value_summary.sql",
    }
    for output_name, query_name in reports.items():
        report_rows = query_to_rows(db_path, query_name)
        write_csv(output_dir / output_name, report_rows)


def run(catalogue_name: str) -> None:
    order_rows = read_csv_rows(DATA_DIR / "order_lines.csv")

    product_file = {
        "candidate": "product_catalog_candidate.csv",
        "approved-v2": "product_catalog_approved_v2.csv",
    }[catalogue_name]

    product_rows = read_csv_rows(DATA_DIR / product_file)
    customer_rows = read_csv_rows(DATA_DIR / "customer_catalog.csv")
    store_rows = read_csv_rows(DATA_DIR / "store_catalog.csv")

    validate_required_fields(order_rows, REQUIRED_ORDER_FIELDS, "order_lines.csv")
    validate_required_fields(product_rows, REQUIRED_PRODUCT_FIELDS, product_file)
    validate_required_fields(customer_rows, REQUIRED_CUSTOMER_FIELDS, "customer_catalog.csv")
    validate_required_fields(store_rows, REQUIRED_STORE_FIELDS, "store_catalog.csv")

    source_checks = validate_source_rows(order_rows)

    dimensions = build_dimensions(
        product_rows, customer_rows, store_rows, order_rows
    )
    dimensions["catalogue_name"] = catalogue_name

    fact_rows, exceptions, row_ledger = build_fact_rows(
        order_rows, dimensions
    )

    checks = validate_model(
        order_rows, fact_rows, exceptions, dimensions
    )
    checks["source_checks"] = source_checks

    if not source_checks["passed"]:
        checks["failures"].append("source validation failed")
        checks["release_status"] = "HOLD"

    version_output = OUTPUT_DIR / catalogue_name
    db_path = version_output / "cedar_trail_warehouse.sqlite"

    write_sqlite_database(db_path, dimensions, fact_rows)
    write_outputs(
        version_output,
        dimensions,
        fact_rows,
        exceptions,
        row_ledger,
        checks,
        db_path,
    )

    print(f"Catalogue: {catalogue_name}")
    print(f"Release status: {checks['release_status']}")
    print(f"Fact rows: {len(fact_rows)}")
    print(f"Exceptions: {len(exceptions)}")
    print(f"Output folder: {version_output}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build the Cedar Trail Week 9 sales warehouse."
    )
    parser.add_argument(
        "--catalogue",
        choices=("candidate", "approved-v2"),
        required=True,
        help="Choose candidate for Part A or approved-v2 for Part B.",
    )
    args = parser.parse_args()
    run(args.catalogue)


if __name__ == "__main__":
    main()
