from pathlib import Path

import pandas as pd


ROOT = Path(__file__).parent
DATA_FILE = ROOT / "data" / "supplier_inventory.csv"
OUTPUTS = ROOT / "outputs"


def standardize_columns(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with predictable snake_case column names."""
    clean = frame.copy()
    clean.columns = (
        clean.columns.str.strip().str.lower().str.replace(" ", "_", regex=False)
    )
    return clean


def add_rejection_reasons(frame: pd.DataFrame) -> pd.DataFrame:
    """Apply the Week 4 data contract and record every failed rule."""
    checked = frame.copy()
    for column in ["supplier_id", "product_sku", "product_name"]:
        checked[column] = checked[column].astype("string").str.strip()

    checked["quantity"] = pd.to_numeric(checked["quantity"], errors="coerce")
    checked["unit_cost"] = pd.to_numeric(checked["unit_cost"], errors="coerce")
    checked["received_at"] = pd.to_datetime(checked["received_at"], errors="coerce")
    checked["rejection_reason"] = ""

    checked.loc[checked["supplier_id"].isna() | (checked["supplier_id"] == ""), "rejection_reason"] += "Missing supplier ID; "
    checked.loc[checked["product_sku"].isna() | (checked["product_sku"] == ""), "rejection_reason"] += "Missing product SKU; "
    checked.loc[checked["product_name"].isna() | (checked["product_name"] == ""), "rejection_reason"] += "Missing product name; "
    checked.loc[checked["quantity"].isna() | (checked["quantity"] <= 0), "rejection_reason"] += "Invalid quantity; "
    checked.loc[checked["unit_cost"].isna() | (checked["unit_cost"] <= 0), "rejection_reason"] += "Invalid unit cost; "
    checked.loc[checked["received_at"].isna(), "rejection_reason"] += "Invalid received date; "
    return checked


def main() -> None:
    OUTPUTS.mkdir(exist_ok=True)
    raw = pd.read_csv(DATA_FILE)
    checked = add_rejection_reasons(standardize_columns(raw))

    initially_valid = checked["rejection_reason"].eq("")
    duplicate = checked.duplicated(
        subset=["supplier_id", "product_sku", "received_at"], keep="first"
    ) & initially_valid
    checked.loc[duplicate, "rejection_reason"] = "Duplicate supplier/product/date record; "

    valid = checked["rejection_reason"].eq("")
    clean = checked.loc[valid].copy()
    rejected = checked.loc[~valid].copy()
    duplicates = checked.loc[duplicate].copy()

    clean.to_csv(OUTPUTS / "clean_inventory.csv", index=False)
    rejected.to_csv(OUTPUTS / "rejected_inventory.csv", index=False)
    duplicates.to_csv(OUTPUTS / "duplicate_inventory.csv", index=False)

    summary = pd.DataFrame(
        [{
            "incoming_records": len(raw),
            "clean_records": len(clean),
            "rejected_records": len(rejected),
            "duplicate_records": len(duplicates),
        }]
    )
    summary.to_csv(OUTPUTS / "ingestion_summary.csv", index=False)

    print(summary.to_string(index=False))
    print("\nClean records saved to outputs/clean_inventory.csv")
    print("Rejected records saved to outputs/rejected_inventory.csv")


if __name__ == "__main__":
    main()
