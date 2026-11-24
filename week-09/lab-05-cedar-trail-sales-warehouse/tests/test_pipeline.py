
"""Unit tests for the Cedar Trail Sales Warehouse pipeline."""

import sys
import unittest
from pathlib import Path

# Make the project root available for importing the pipeline.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.starter_pipeline import (
    DATA_DIR,
    build_dimensions,
    build_fact_rows,
    calculate_line_amounts,
    read_csv_rows,
    validate_model,
    validate_source_rows,
)


class TestSalesCalculations(unittest.TestCase):
    """Test line-level sales calculations."""

    def test_normal_sales_calculation(self):
        gross, discount, net = calculate_line_amounts("2", "3499", "0.10")

        self.assertEqual(gross, 6998)
        self.assertEqual(discount, 700)
        self.assertEqual(net, 6298)

    def test_zero_discount(self):
        gross, discount, net = calculate_line_amounts("1", "1299", "0")

        self.assertEqual(gross, 1299)
        self.assertEqual(discount, 0)
        self.assertEqual(net, 1299)

    def test_round_half_up(self):
        gross, discount, net = calculate_line_amounts("1", "5", "0.5")

        self.assertEqual(gross, 5)
        self.assertEqual(discount, 3)
        self.assertEqual(net, 2)

    def test_invalid_zero_quantity(self):
        with self.assertRaises(ValueError):
            calculate_line_amounts("0", "3499", "0.10")

    def test_invalid_negative_quantity(self):
        with self.assertRaises(ValueError):
            calculate_line_amounts("-1", "3499", "0.10")

    def test_invalid_negative_price(self):
        with self.assertRaises(ValueError):
            calculate_line_amounts("1", "-100", "0.10")

    def test_invalid_discount_above_one(self):
        with self.assertRaises(ValueError):
            calculate_line_amounts("1", "1000", "1.5")

    def test_invalid_negative_discount(self):
        with self.assertRaises(ValueError):
            calculate_line_amounts("1", "1000", "-0.1")

    def test_invalid_non_numeric_quantity(self):
        with self.assertRaises(ValueError):
            calculate_line_amounts("abc", "1000", "0.10")


class TestSourceValidation(unittest.TestCase):
    """Test source CSV validation."""

    def setUp(self):
        self.order_rows = read_csv_rows(DATA_DIR / "order_lines.csv")

    def test_source_file_has_twelve_rows(self):
        self.assertEqual(len(self.order_rows), 12)

    def test_source_rows_pass_validation(self):
        result = validate_source_rows(self.order_rows)

        self.assertTrue(result["passed"])
        self.assertEqual(result["source_row_count"], 12)
        self.assertEqual(result["invalid_row_count"], 0)

    def test_duplicate_line_id_is_detected(self):
        rows = [dict(row) for row in self.order_rows]
        rows[1]["line_id"] = rows[0]["line_id"]

        result = validate_source_rows(rows)

        self.assertFalse(result["passed"])
        self.assertTrue(
            any("Duplicate line_id" in item["problem"]
                for item in result["problems"])
        )


class TestWarehouseConstruction(unittest.TestCase):
    """Test dimensions, fact rows, exceptions, and release checks."""

    def setUp(self):
        self.order_rows = read_csv_rows(DATA_DIR / "order_lines.csv")
        self.customer_rows = read_csv_rows(DATA_DIR / "customer_catalog.csv")
        self.store_rows = read_csv_rows(DATA_DIR / "store_catalog.csv")

    def build_for_catalogue(self, catalogue_name):
        if catalogue_name == "candidate":
            product_file = "product_catalog_candidate.csv"
        else:
            product_file = "product_catalog_approved_v2.csv"

        product_rows = read_csv_rows(DATA_DIR / product_file)

        dimensions = build_dimensions(
            product_rows,
            self.customer_rows,
            self.store_rows,
            self.order_rows,
        )
        dimensions["catalogue_name"] = catalogue_name

        facts, exceptions, ledger = build_fact_rows(
            self.order_rows,
            dimensions,
        )

        checks = validate_model(
            self.order_rows,
            facts,
            exceptions,
            dimensions,
        )

        return dimensions, facts, exceptions, ledger, checks

    def test_candidate_catalogue_preserves_all_completed_sales(self):
        dimensions, facts, exceptions, ledger, checks = (
            self.build_for_catalogue("candidate")
        )

        self.assertEqual(len(facts), 10)
        self.assertEqual(ledger["input_rows"], 12)
        self.assertEqual(ledger["completed_rows"], 10)
        self.assertEqual(ledger["cancelled_rows"], 1)
        self.assertEqual(ledger["pending_rows"], 1)
        self.assertEqual(ledger["distinct_completed_orders"], 8)
        self.assertEqual(ledger["completed_units"], 15)

    def test_candidate_catalogue_has_one_unknown_product(self):
        dimensions, facts, exceptions, ledger, checks = (
            self.build_for_catalogue("candidate")
        )

        unknown_facts = [
            row for row in facts if row["product_key"] == 0
        ]

        self.assertEqual(len(unknown_facts), 1)
        self.assertEqual(unknown_facts[0]["source_sku"], "SKU-999")
        self.assertEqual(unknown_facts[0]["line_id"], "L1005-01")

        self.assertEqual(len(exceptions), 1)
        self.assertEqual(checks["release_status"], "HOLD")

    def test_approved_catalogue_resolves_sku_999(self):
        dimensions, facts, exceptions, ledger, checks = (
            self.build_for_catalogue("approved-v2")
        )

        sku_999_facts = [
            row for row in facts if row["source_sku"] == "SKU-999"
        ]

        self.assertEqual(len(sku_999_facts), 1)
        self.assertNotEqual(sku_999_facts[0]["product_key"], 0)
        self.assertEqual(len(exceptions), 0)
        self.assertEqual(checks["release_status"], "ACCEPT")
        self.assertEqual(checks["failures"], [])

    def test_only_completed_rows_enter_fact_table(self):
        dimensions, facts, exceptions, ledger, checks = (
            self.build_for_catalogue("approved-v2")
        )

        self.assertEqual(len(facts), 10)

        fact_order_ids = {row["order_id"] for row in facts}

        self.assertNotIn("O1007", fact_order_ids)
        self.assertNotIn("O1008", fact_order_ids)

    def test_fact_line_ids_are_unique(self):
        dimensions, facts, exceptions, ledger, checks = (
            self.build_for_catalogue("approved-v2")
        )

        line_ids = [row["line_id"] for row in facts]

        self.assertEqual(len(line_ids), len(set(line_ids)))

    def test_sales_totals_are_correct(self):
        dimensions, facts, exceptions, ledger, checks = (
            self.build_for_catalogue("approved-v2")
        )

        gross_total = sum(row["gross_cents"] for row in facts)
        discount_total = sum(row["discount_cents"] for row in facts)
        net_total = sum(row["net_cents"] for row in facts)

        self.assertEqual(gross_total, 57985)
        self.assertEqual(discount_total, 4955)
        self.assertEqual(net_total, 53030)

    def test_net_sales_equal_gross_less_discount(self):
        dimensions, facts, exceptions, ledger, checks = (
            self.build_for_catalogue("approved-v2")
        )

        for row in facts:
            self.assertEqual(
                row["net_cents"],
                row["gross_cents"] - row["discount_cents"],
            )

    def test_approved_validation_checks_all_pass(self):
        dimensions, facts, exceptions, ledger, checks = (
            self.build_for_catalogue("approved-v2")
        )

        self.assertTrue(all(checks["checks"].values()))
        self.assertEqual(checks["release_status"], "ACCEPT")

    def test_candidate_validation_is_hold(self):
        dimensions, facts, exceptions, ledger, checks = (
            self.build_for_catalogue("candidate")
        )

        self.assertFalse(
            checks["checks"]["no_unresolved_product_mappings"]
        )
        self.assertEqual(checks["release_status"], "HOLD")


if __name__ == "__main__":
    unittest.main(verbosity=2)
