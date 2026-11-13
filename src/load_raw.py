
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, URL, text

if __package__:
    from .logger import logger
else:
    from logger import logger

PROJECT_ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = PROJECT_ROOT / "data" / "raw"

files = {
    "orders": "olist_orders_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "payments": "olist_order_payments_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
    "products": "olist_products_dataset.csv",
    "categories": "product_category_name_translation.csv"
}

def main():
    load_dotenv(PROJECT_ROOT / ".env")

    missing_files = [
        filename for filename in files.values()
        if not (RAW_DIR / filename).is_file()
    ]
    if missing_files:
        missing_list = ", ".join(missing_files)
        raise FileNotFoundError(
            f"Required CSV file(s) missing from {RAW_DIR}: {missing_list}"
        )

    password = os.getenv("PG_PASSWORD")
    if not password:
        raise RuntimeError("PG_PASSWORD not found in .env or environment")

    url = URL.create(
        "postgresql+psycopg",
        username=os.getenv("PG_USER", "postgres"),
        password=password,
        host=os.getenv("PG_HOST", "localhost"),
        port=int(os.getenv("PG_PORT", "5432")),
        database=os.getenv("PG_DATABASE", "retailflow")
    )
    engine = create_engine(url)

    try:
        with engine.begin() as connection:
            connection.execute(
                text("CREATE SCHEMA IF NOT EXISTS raw")
            )

        for table_name, filename in files.items():
            logger.info("Loading %s from %s", table_name, filename)
            df = pd.read_csv(RAW_DIR / filename, low_memory=False)
            df.to_sql(
                name=table_name,
                con=engine,
                schema="raw",
                if_exists="replace",
                index=False,
                chunksize=5000,
                method="multi"
            )
            logger.info("Loaded %d records into raw.%s", len(df), table_name)

        logger.info("Raw data loading completed")
    except Exception:
        logger.exception("Raw data loading failed")
        raise
    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
