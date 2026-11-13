
from pathlib import Path
from decimal import Decimal
import logging

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from sqlalchemy import Numeric, text

PROJECT_ROOT = Path(__file__).resolve().parent.parent
logger = logging.getLogger("retailflow")


def build_parquet_table(summary):
    table = pa.Table.from_pandas(summary, preserve_index=False)
    for column in ("merchandise_value", "freight_value", "payment_total"):
        column_index = table.schema.get_field_index(column)
        values = [
            None if pd.isna(value) else Decimal(str(value))
            for value in summary[column]
        ]
        table = table.set_column(
            column_index,
            column,
            pa.array(values, type=pa.decimal128(12, 2))
        )
    return table


def load_data(engine, summary, quarantine):

    processed_dir = PROJECT_ROOT / "data" / "processed"
    quarantine_dir = PROJECT_ROOT / "data" / "quarantine"

    processed_dir.mkdir(parents=True, exist_ok=True)
    quarantine_dir.mkdir(parents=True, exist_ok=True)

    # Write exact financial values as decimal(12,2) for Parquet/Athena.
    parquet_path = processed_dir / "order_summary.parquet"
    pq.write_table(build_parquet_table(summary), parquet_path)
    logger.info("Parquet saved: %s", parquet_path)

    # Save problematic records for investigation
    for name, df in quarantine.items():

        output_path = (
            quarantine_dir / f"{name}_invalid.csv"
        )

        df.to_csv(output_path, index=False)

        logger.info("%s: %d quarantined records", name, len(df))

    # This MVP uses a full refresh: to_sql replaces the analytics table each run.
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
        chunksize=5000,
        dtype={
            "merchandise_value": Numeric(12, 2),
            "freight_value": Numeric(12, 2),
            "payment_total": Numeric(12, 2)
        }
    )

    logger.info("Analytics table loaded successfully")
    logger.info("Total analytical orders: %d", len(summary))
