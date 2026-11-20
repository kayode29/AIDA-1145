"""Lab 6 scaffold. Complete each TODO and keep the input files unchanged."""
from pathlib import Path
import csv
import json
from datetime import datetime

LAB = Path(__file__).resolve().parents[1]

def read_expected():
    with (LAB / 'data' / 'expected_sensors.csv').open(newline='', encoding='utf-8') as f:
        return {row['sensor_id'] for row in csv.DictReader(f)}

def read_pages(batch_dir):
    """Return the readings, common retrieval time, and number of pages read."""
    # TODO: load each JSON page. Stop when next_cursor is None.
    # Reject an unknown or repeated cursor and inconsistent retrieved_at values.
    raise NotImplementedError('Complete pagination')

def process(readings, retrieved_at, expected):
    """Deduplicate by reading_id; check values and age; return results and counts."""
    # TODO: apply the rules in the README. Preserve invalid and stale rows in quarantine.
    # Treat conflicting content for the same reading_id as a reason to HOLD.
    raise NotImplementedError('Complete validation and duplicate handling')

def run_batch(name):
    batch_dir = LAB / 'data' / name
    output_dir = LAB / 'outputs' / name
    output_dir.mkdir(parents=True, exist_ok=True)
    expected = read_expected()
    readings, retrieved_at, page_count = read_pages(batch_dir)
    results = process(readings, retrieved_at, expected)
    # TODO: write accepted.csv, quarantine.csv and summary.json in output_dir.
    # Include all fields and measures required in README.md.
    raise NotImplementedError('Write the output files')

if __name__ == '__main__':
    # Part A: run_batch('initial'). Part B: also run_batch('retry').
    run_batch('initial')
