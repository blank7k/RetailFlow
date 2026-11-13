
from pathlib import Path
import pandas as pd
from sqlalchemy import text

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_data(engine, summary, quarantine):

    processed_dir = PROJECT_ROOT / "data" / "processed"
    quarantine_dir = PROJECT_ROOT / "data" / "quarantine"

    processed_dir.mkdir(parents=True, exist_ok=True)
    quarantine_dir.mkdir(parents=True, exist_ok=True)

    # Save processed dataset as Parquet
    parquet_path = processed_dir / "order_summary.parquet"

    summary.to_parquet(
        parquet_path,
        index=False
    )

    print(f"Parquet saved: {parquet_path}")

    # Save problematic records for investigation
    for name, df in quarantine.items():

        output_path = (
            quarantine_dir / f"{name}_invalid.csv"
        )

        df.to_csv(output_path, index=False)

        print(
            f"{name}: {len(df)} quarantined records"
        )

    # Create analytics schema
    with engine.begin() as connection:
        connection.execute(
            text("CREATE SCHEMA IF NOT EXISTS analytics")
        )

    # Load analytical data into PostgreSQL
    summary.to_sql(
        name="order_summary",
        con=engine,
        schema="analytics",
        if_exists="replace",
        index=False,
        chunksize=5000
    )

    print("Analytics table loaded successfully!")
    print("Total analytical orders:", len(summary))
