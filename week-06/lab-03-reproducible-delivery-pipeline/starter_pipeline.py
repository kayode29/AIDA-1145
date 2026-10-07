"""AIDA 1145 Week 6 Lab 3 - Reproducible Delivery Pipeline."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
from datetime import date, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "data" / "delivery_events.csv"
WORK = ROOT / "work"


class PipelineError(RuntimeError):
    """A problem that should stop the pipeline with a useful message."""


def file_sha256(path: Path) -> str:
    """TODO 1: Return SHA-256 fingerprint for a file."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_paths(run_date: str) -> dict[str, Path]:
    """TODO 2: Return paths used by the pipeline run."""
    run_folder = WORK / run_date

    return {
        "run_folder": run_folder,
        "raw": run_folder / "raw.csv",
        "clean": run_folder / "clean.csv",
        "quarantine": run_folder / "quarantine.csv",
        "manifest": run_folder / "manifest.json",
        "summary": run_folder / "outputs" / "delivery_summary.csv",
    }


def write_manifest(paths: dict[str, Path], manifest: dict) -> None:
    """TODO 3: Save the manifest as formatted JSON."""
    paths["run_folder"].mkdir(parents=True, exist_ok=True)

    with paths["manifest"].open("w", encoding="utf-8") as file:
        json.dump(manifest, file, indent=2)
        file.write("\n")


def extract(paths: dict[str, Path], manifest: dict) -> None:
    """TODO 4: Preserve the source CSV and record its fingerprint."""
    source_hash = file_sha256(SOURCE)

    if paths["raw"].exists():
        raw_hash = file_sha256(paths["raw"])

        if raw_hash != source_hash:
            raise PipelineError(
                "Existing raw.csv does not match the source file. "
                "The raw evidence was not overwritten."
            )
    else:
        paths["run_folder"].mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SOURCE, paths["raw"])

    manifest["input_sha256"] = source_hash
    manifest["stages"]["extract"] = "SUCCEEDED"


def transform(paths: dict[str, Path], manifest: dict) -> None:
    """TODO 5: Validate, quarantine, and deduplicate records."""

    valid_rows = []
    quarantine_rows = []
    duplicate_count = 0

    with paths["raw"].open(
        "r", encoding="utf-8", newline=""
    ) as file:
        reader = csv.DictReader(file)

        for source_row, row in enumerate(reader, start=2):
            reasons = []

            parcel_id = (row.get("parcel_id") or "").strip()
            event_date = (row.get("event_date") or "").strip()

            # Check parcel ID.
            if not parcel_id:
                reasons.append("parcel_id is blank")

            # Check exact YYYY-MM-DD date.
            try:
                datetime.strptime(event_date, "%Y-%m-%d")
            except ValueError:
                reasons.append(
                    "event_date is not a valid YYYY-MM-DD date"
                )

            if reasons:
                rejected = dict(row)
                rejected["source_row"] = source_row
                rejected["reason"] = "; ".join(reasons)
                quarantine_rows.append(rejected)
            else:
                accepted = dict(row)
                accepted["source_row"] = source_row
                valid_rows.append(accepted)

    # Keep newest record for each parcel.
    selected = {}

    for row in valid_rows:
        parcel_id = row["parcel_id"]

        if parcel_id not in selected:
            selected[parcel_id] = row
            continue

        current = selected[parcel_id]

        current_time = datetime.fromisoformat(
            current["source_updated_at"].replace("Z", "+00:00")
        )

        new_time = datetime.fromisoformat(
            row["source_updated_at"].replace("Z", "+00:00")
        )

        if new_time > current_time:
            selected[parcel_id] = row

        # If timestamps are equal, keep the earlier source row.
        duplicate_count += 1

    clean_rows = list(selected.values())

    clean_fields = [
        "parcel_id",
        "event_date",
        "hub",
        "event_type",
        "source_updated_at",
        "source_row",
    ]

    quarantine_fields = [
        "parcel_id",
        "event_date",
        "hub",
        "event_type",
        "source_updated_at",
        "source_row",
        "reason",
    ]

    paths["run_folder"].mkdir(parents=True, exist_ok=True)

    with paths["clean"].open(
        "w", encoding="utf-8", newline=""
    ) as file:
        writer = csv.DictWriter(file, fieldnames=clean_fields)
        writer.writeheader()
        writer.writerows(clean_rows)

    with paths["quarantine"].open(
        "w", encoding="utf-8", newline=""
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=quarantine_fields
        )
        writer.writeheader()
        writer.writerows(quarantine_rows)

    input_count = (
        len(clean_rows)
        + len(quarantine_rows)
        + duplicate_count
    )

    manifest["counts"] = {
        "input": input_count,
        "clean": len(clean_rows),
        "quarantined": len(quarantine_rows),
        "duplicate_non_survivors": duplicate_count,
    }

    manifest["clean_sha256"] = file_sha256(paths["clean"])
    manifest["quarantine_sha256"] = file_sha256(
        paths["quarantine"]
    )

    manifest["stages"]["transform"] = "SUCCEEDED"


def publish(paths: dict[str, Path], manifest: dict) -> None:
    """TODO 6: Create delivery summary after hash verification."""

    actual_hash = file_sha256(paths["clean"])

    if actual_hash != manifest.get("clean_sha256"):
        raise PipelineError(
            "clean.csv fingerprint does not match the manifest. "
            "Publish stopped."
        )

    counts = {}

    with paths["clean"].open(
        "r", encoding="utf-8", newline=""
    ) as file:
        reader = csv.DictReader(file)

        for row in reader:
            event_type = row["event_type"]
            counts[event_type] = counts.get(event_type, 0) + 1

    paths["summary"].parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with paths["summary"].open(
        "w", encoding="utf-8", newline=""
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=["event_type", "parcel_count"]
        )

        writer.writeheader()

        for event_type in sorted(counts):
            writer.writerow(
                {
                    "event_type": event_type,
                    "parcel_count": counts[event_type],
                }
            )

    manifest["summary_sha256"] = file_sha256(
        paths["summary"]
    )

    manifest["stages"]["publish"] = "SUCCEEDED"


def run(
    run_date: str,
    fail_after_transform: bool = False,
    resume: bool = False,
) -> dict:
    """TODO 7: Coordinate extract, transform, publish and resume."""

    paths = None
    manifest = None

    try:
        # Validate exact YYYY-MM-DD format.
        datetime.strptime(run_date, "%Y-%m-%d")
        date.fromisoformat(run_date)

        paths = run_paths(run_date)

        # -------------------------
        # RESUME
        # -------------------------
        if resume:

            if not paths["manifest"].exists():
                raise PipelineError(
                    f"No manifest found for {run_date}."
                )

            with paths["manifest"].open(
                "r", encoding="utf-8"
            ) as file:
                manifest = json.load(file)

            if manifest.get("status") != "FAILED":
                raise PipelineError(
                    "Resume is allowed only after a FAILED run."
                )

            if (
                manifest.get("stages", {}).get("transform")
                != "SUCCEEDED"
            ):
                raise PipelineError(
                    "Resume is allowed only when transform succeeded."
                )

            actual_hash = file_sha256(paths["clean"])

            if actual_hash != manifest.get("clean_sha256"):
                raise PipelineError(
                    "clean.csv fingerprint does not match "
                    "the manifest. Resume stopped."
                )

            publish(paths, manifest)

            manifest["status"] = "SUCCEEDED"

            write_manifest(paths, manifest)

            return manifest

        # -------------------------
        # NORMAL RUN
        # -------------------------

        manifest = {
            "run_date": run_date,
            "status": "RUNNING",
            "stages": {
                "extract": "PENDING",
                "transform": "PENDING",
                "publish": "PENDING",
            },
        }

        write_manifest(paths, manifest)

        # Extract.
        extract(paths, manifest)
        write_manifest(paths, manifest)

        # Transform.
        transform(paths, manifest)
        write_manifest(paths, manifest)

        # Controlled failure.
        if fail_after_transform:

            manifest["status"] = "FAILED"
            manifest["stages"]["publish"] = "FAILED"

            manifest["error"] = (
                "Controlled failure requested after "
                "successful transform."
            )

            write_manifest(paths, manifest)

            raise PipelineError(
                "Controlled failure requested after transform."
            )

        # Publish.
        publish(paths, manifest)

        manifest["status"] = "SUCCEEDED"

        write_manifest(paths, manifest)

        return manifest

    except Exception as exc:

        if (
            paths is not None
            and manifest is not None
            and manifest.get("status") != "FAILED"
        ):
            manifest["status"] = "FAILED"
            manifest["error"] = str(exc)
            write_manifest(paths, manifest)

        raise


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the delivery-events pipeline"
    )

    parser.add_argument(
        "--run-date",
        required=True,
        help="Run label: YYYY-MM-DD"
    )

    parser.add_argument(
        "--fail-after-transform",
        action="store_true"
    )

    parser.add_argument(
        "--resume",
        action="store_true"
    )

    args = parser.parse_args()

    try:
        result = run(
            args.run_date,
            args.fail_after_transform,
            args.resume
        )

        print(json.dumps(result, indent=2))

    except (
        PipelineError,
        ValueError,
        NotImplementedError
    ) as exc:

        print(f"PIPELINE_FAILED: {exc}")
        raise SystemExit(2)


if __name__ == "__main__":
    main()