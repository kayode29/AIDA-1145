"""Complete the TODO sections to clean the supplied fictional pickup data."""

from pathlib import Path
import argparse
import json
import pandas as pd


ROOT = Path(__file__).resolve().parent

STATUS_MAP = {
    "received": "received",
    "in transit": "in_transit",
    "delivered": "delivered",
    "cancelled": "cancelled",
}


def process(input_path: Path, output_dir: Path, site_policy: str) -> dict:
    """Read, validate, transform and save one run of the input file."""

    # TODO 1: Read the CSV
    frame = pd.read_csv(
        input_path,
        dtype="string",
        keep_default_na=False
    )

    # TODO 2: Add source row numbers
    frame["source_row"] = range(2, len(frame) + 2)

    # TODO 3 and 4: Validate rows and create cleaned fields
    reasons = []
    status_clean = []
    quantity_boxes_number = []
    pickup_site_quality = []

    for _, row in frame.iterrows():
        row_reasons = []

        # Donation ID
        donation_id = row["donation_id"].strip()

        if donation_id == "":
            row_reasons.append("missing_donation_id")

        # Recorded date
        recorded_on = row["recorded_on"].strip()
        valid_date = False

        try:
            parsed_date = pd.to_datetime(
                recorded_on,
                format="%Y-%m-%d",
                errors="raise"
            )

            if parsed_date.strftime("%Y-%m-%d") == recorded_on:
                valid_date = True

        except (ValueError, TypeError):
            valid_date = False

        if not valid_date:
            row_reasons.append("invalid_recorded_on")

        # Status
        status = row["status"].strip().lower()

        if status in STATUS_MAP:
            status_clean.append(STATUS_MAP[status])
        else:
            status_clean.append("")
            row_reasons.append("unknown_status")

        # Quantity
        quantity = row["quantity_boxes"].strip()

        try:
            number = int(quantity)

            if number <= 0:
                row_reasons.append("invalid_quantity_boxes")
                quantity_boxes_number.append(pd.NA)
            else:
                quantity_boxes_number.append(number)

        except (ValueError, TypeError):
            row_reasons.append("invalid_quantity_boxes")
            quantity_boxes_number.append(pd.NA)

        # Pickup site
        pickup_site = row["pickup_site"].strip()

        if pickup_site == "":
            pickup_site_quality.append("missing")

            if site_policy == "reject":
                row_reasons.append("missing_pickup_site")
        else:
            pickup_site_quality.append("present")

        reasons.append(";".join(row_reasons))

    frame["status_clean"] = status_clean
    frame["quantity_boxes_number"] = quantity_boxes_number
    frame["pickup_site_quality"] = pickup_site_quality
    frame["rejection_reason"] = reasons

    # TODO 6: Separate rejected and valid rows
    rejected = frame[frame["rejection_reason"] != ""].copy()
    valid = frame[frame["rejection_reason"] == ""].copy()

    # TODO 7: Sort and remove duplicate donation IDs
    valid = valid.sort_values(
        by=["donation_id", "source_updated_at", "source_row"],
        ascending=[True, False, True],
        kind="stable"
    )

    duplicate_rows = valid[
        valid.duplicated(
            subset=["donation_id"],
            keep="first"
        )
    ].copy()

    clean = valid.drop_duplicates(
        subset=["donation_id"],
        keep="first"
    ).copy()

    # TODO 8: Create output folder and files
    output_dir.mkdir(parents=True, exist_ok=True)

    clean.to_csv(
        output_dir / "clean_pickups.csv",
        index=False
    )

    rejected.to_csv(
        output_dir / "rejected_pickups.csv",
        index=False
    )

    duplicate_rows.to_csv(
        output_dir / "duplicate_rows.csv",
        index=False
    )

    summary = {
        "input_rows": len(frame),
        "clean_rows": len(clean),
        "rejected_rows": len(rejected),
        "duplicate_non_survivors": len(duplicate_rows),
        "site_policy": site_policy,
    }

    with open(
        output_dir / "summary.json",
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(summary, file, indent=2)

    # TODO 9: Return summary
    return summary


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--site-policy",
        choices=["flag", "reject"],
        required=True
    )

    parser.add_argument(
        "--output",
        default="outputs/baseline"
    )

    args = parser.parse_args()

    output_dir = ROOT / args.output

    summary = process(
        ROOT / "data" / "donation_pickups.csv",
        output_dir,
        args.site_policy
    )

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
