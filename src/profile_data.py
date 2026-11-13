
from pathlib import Path
import pandas as pd

# Location of our raw source files
RAW_DIR = Path("data/raw")

# Files we will initially analyse
files = {
    "orders": "olist_orders_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "payments": "olist_order_payments_dataset.csv",
    "reviews": "olist_order_reviews_dataset.csv",
    "products": "olist_products_dataset.csv",
    "categories": "product_category_name_translation.csv"
}

for table_name, filename in files.items():

    file_path = RAW_DIR / filename

    if not file_path.exists():
        print(f"File not found: {filename}")
        continue

    # Read CSV into a Pandas DataFrame
    df = pd.read_csv(file_path, low_memory=False)

    print("\n" + "=" * 50)
    print(f"TABLE: {table_name.upper()}")
    print("=" * 50)

    # Number of rows and columns
    print("Shape:", df.shape)

    # Check column names and data types
    print("\nColumn information:")
    print(df.info())

    # Check missing values
    print("\nMissing values:")
    print(df.isnull().sum())

    # Check completely duplicate rows
    print("\nDuplicate rows:", df.duplicated().sum())

    # Display first two records
    print("\nSample records:")
    print(df.head(2).to_string(index=False))
