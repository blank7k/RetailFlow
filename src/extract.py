
import pandas as pd
from sqlalchemy import text


def extract_data(engine):

    queries = {
        "orders": """
            SELECT
                order_id,
                customer_id,
                order_status,
                order_purchase_timestamp
            FROM raw.orders
        """,

        "customers": """
            SELECT
                customer_id,
                customer_unique_id,
                customer_city,
                customer_state
            FROM raw.customers
        """,

        "items": """
            SELECT
                order_id,
                order_item_id,
                product_id,
                price,
                freight_value
            FROM raw.order_items
        """,

        "payments": """
            SELECT
                order_id,
                payment_sequential,
                payment_type,
                payment_value
            FROM raw.payments
        """,

        "reviews": """
            SELECT
                review_id,
                order_id,
                review_score
            FROM raw.reviews
        """
    }

    data = {}

    with engine.connect() as connection:

        for name, query in queries.items():

            print(f"Extracting {name}...")

            data[name] = pd.read_sql_query(
                text(query),
                connection
            )

            print(
                f"Extracted {len(data[name])} records"
            )

    return data
