"""Worked example: validate a delivery batch and publish only a complete run."""
import argparse
import csv
import json
from pathlib import Path

FIELDS = {"event_id", "location", "units"}

def run(source, outdir):
    source, outdir = Path(source), Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    with source.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        missing = FIELDS - set(reader.fieldnames or [])
        if missing:
            raise ValueError("Missing required columns: " + ", ".join(sorted(missing)))
        rows = list(reader)
    accepted, rejected, seen = [], [], set()
    for number, row in enumerate(rows, 2):
        key = (row.get("event_id") or "").strip()
        location = (row.get("location") or "").strip()
        reason = []
        if not key: reason.append("missing event_id")
        if not location: reason.append("missing location")
        try:
            units = int(row.get("units", ""))
            if units < 0: reason.append("negative units")
        except (TypeError, ValueError):
            units = None
            reason.append("units must be an integer")
        if key and key in seen: reason.append("duplicate event_id")
        if key: seen.add(key)
        if reason:
            rejected.append({"source_line": number, "event_id": key, "reason": "; ".join(reason)})
        else:
            accepted.append({"event_id": key, "location": location, "units": units})
    # Every input row must be accounted for; strict release requires zero rejects.
    assert len(rows) == len(accepted) + len(rejected)
    status = "PASS" if not rejected else "HOLD"
    for name, records, columns in [("accepted.csv", accepted, ["event_id", "location", "units"]), ("rejected.csv", rejected, ["source_line", "event_id", "reason"])]:
        with (outdir/name).open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=columns); w.writeheader(); w.writerows(records)
    summary = {"source": str(source), "input_rows": len(rows), "accepted_rows": len(accepted), "rejected_rows": len(rejected), "accepted_units": sum(r["units"] for r in accepted), "release": status}
    (outdir/"run_summary.json").write_text(json.dumps(summary, indent=2)+"\n", encoding="utf-8")
    # A held run does not produce a publishable report. Remove stale report on rerun.
    report = outdir/"published_totals.csv"
    if status == "PASS":
        totals = {}
        for r in accepted: totals[r["location"]] = totals.get(r["location"], 0) + r["units"]
        with report.open("w", newline="", encoding="utf-8") as f:
            w = csv.writer(f); w.writerow(["location", "units"]); w.writerows(sorted(totals.items()))
    elif report.exists(): report.unlink()
    return summary

if __name__ == "__main__":
    parser = argparse.ArgumentParser(); parser.add_argument("source"); parser.add_argument("output")
    args = parser.parse_args(); print(json.dumps(run(args.source, args.output), indent=2))
