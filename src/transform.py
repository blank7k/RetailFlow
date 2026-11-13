
from decimal import Decimal

import pandas as pd


MONEY_QUANTUM = Decimal("0.01")


def quantize_money(value):
    if pd.isna(value):
        return None
    return Decimal(str(value)).quantize(MONEY_QUANTUM)


def transform_data(clean):

    orders = clean["orders"].copy()
    customers = clean["customers"].copy()
    items = clean["items"].copy()
    payments = clean["payments"].copy()
    reviews = clean["reviews"].copy()

    # STEP 1: Aggregate product items by order
    item_totals = (
        items
        .groupby("order_id", as_index=False)
        .agg(
            item_count=("order_id", "size"),
            merchandise_value=("price", "sum"),
            freight_value=("freight_value", "sum")
        )
    )

    # STEP 2: Aggregate payments by order
    payment_totals = (
        payments
        .groupby("order_id", as_index=False)
        .agg(
            payment_count=("order_id", "size"),
            payment_total=("payment_value", "sum")
        )
    )

    # STEP 3: Aggregate reviews by order
    review_totals = (
        reviews
        .groupby("order_id", as_index=False)
        .agg(
            average_review_score=("review_score", "mean"),
            review_count=("review_id", "count")
        )
    )

    # STEP 4: Select customer information
    customer_details = customers[
        [
            "customer_id",
            "customer_unique_id",
            "customer_city",
            "customer_state"
        ]
    ]

    # STEP 5: Start with orders
    summary = orders.merge(
        customer_details,
        on="customer_id",
        how="left",
        validate="many_to_one"
    )

    # STEP 6: Join pre-aggregated tables
    summary = summary.merge(
        item_totals,
        on="order_id",
        how="left",
        validate="one_to_one"
    )

    summary = summary.merge(
        payment_totals,
        on="order_id",
        how="left",
        validate="one_to_one"
    )

    summary = summary.merge(
        review_totals,
        on="order_id",
        how="left",
        validate="one_to_one"
    )

    # STEP 7: Fill missing counts, not missing money
    for column in [
        "item_count",
        "payment_count",
        "review_count"
    ]:
        summary[column] = (
            summary[column]
            .fillna(0)
            .astype("int64")
        )

    # Normalize money to exact two-decimal values for PostgreSQL and Parquet.
    for column in [
        "merchandise_value",
        "freight_value",
        "payment_total"
    ]:
        summary[column] = summary[column].map(quantize_money)

    # STEP 8: Verify the final grain
    if summary["order_id"].duplicated().any():
        raise ValueError(
            "Duplicate order IDs found in final summary"
        )

    if len(summary) != len(orders):
        raise ValueError(
            "Order count changed during transformation"
        )

    return summary
