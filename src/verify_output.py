import pandas as pd

df = pd.read_parquet(
    "data/processed/order_summary.parquet"
)

print("Dataset shape:", df.shape)

print("\nFirst 5 records:")
print(df.head().to_string(index=False))

print("\nColumn types:")
print(df.dtypes)

print("\nAre order IDs unique?")
print(df["order_id"].is_unique)