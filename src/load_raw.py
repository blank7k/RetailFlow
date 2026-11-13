
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, URL, text

load_dotenv()

RAW_DIR = Path("data/raw")

files = {
    "orders": "olist_orders_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "payments": "olist_order_payments_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
    "products": "olist_products_dataset.csv",
    "categories": "product_category_name_translation.csv"
}

# Create PostgreSQL connection
url = URL.create(
    "postgresql+psycopg",
    username=os.getenv("PG_USER"),
    password=os.getenv("PG_PASSWORD"),
    host=os.getenv("PG_HOST", "localhost"),
    port=int(os.getenv("PG_PORT", "5432")),
    database=os.getenv("PG_DATABASE", "retailflow")
)

engine = create_engine(url)

# Create raw schema
with engine.begin() as connection:
    connection.execute(
        text("CREATE SCHEMA IF NOT EXISTS raw")
    )

# Load each CSV
for table_name, filename in files.items():

    file_path = RAW_DIR / filename

    print(f"\nLoading: {table_name}")

    if not file_path.exists():
        print(f"File missing: {filename}")
        continue

    df = pd.read_csv(file_path, low_memory=False)

    df.to_sql(
        name=table_name,
        con=engine,
        schema="raw",
        if_exists="replace",
        index=False,
        chunksize=5000,
        method="multi"
    )

    print(f"Loaded {len(df)} records")

print("\nRaw data loading completed!")

engine.dispose()
