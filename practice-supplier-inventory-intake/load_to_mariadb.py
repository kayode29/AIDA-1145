import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine


ROOT = Path(__file__).parent
CLEAN_FILE = ROOT / "outputs" / "clean_inventory.csv"


def main() -> None:
    database_url = os.getenv("MARIADB_URL")
    if not database_url:
        raise SystemExit(
            "Set MARIADB_URL first. See README.md for the exact PowerShell command."
        )

    clean_inventory = pd.read_csv(CLEAN_FILE)
    engine = create_engine(database_url)
    clean_inventory.to_sql(
        "stg_supplier_inventory", con=engine, if_exists="replace", index=False
    )
    print(f"Loaded {len(clean_inventory)} clean records into stg_supplier_inventory.")


if __name__ == "__main__":
    main()
