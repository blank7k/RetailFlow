
import logging
from decimal import Decimal, InvalidOperation

import pandas as pd

logger = logging.getLogger("retailflow")


def parse_decimal(value):
    if pd.isna(value):
        return None
    try:
        amount = Decimal(str(value).strip())
    except (InvalidOperation, ValueError):
        return None
    return amount if amount.is_finite() else None


def is_negative(value):
    return value is not None and value < Decimal("0")


def split_valid_invalid(df, rules):

    errors = pd.Series(
        "",
        index=df.index,
        dtype="object"
    )

    for error_name, condition in rules:

        condition = condition.fillna(False)

        errors.loc[condition] += error_name + ";"

    valid = df.loc[errors.eq("")].copy()

    invalid = df.loc[errors.ne("")].copy()

    invalid["validation_errors"] = errors.loc[
        errors.ne("")
    ]

    return valid, invalid


def validate_data(data):

    orders = data["orders"].copy()
    customers = data["customers"].copy()
    items = data["items"].copy()
    payments = data["payments"].copy()
    reviews = data["reviews"].copy()
    products = data["products"].copy()

    # Normalise identifier columns
    for df, columns in [
        (orders, ["order_id", "customer_id"]),
        (customers, ["customer_id"]),
        (items, ["order_id", "order_item_id", "product_id"]),
        (payments, ["order_id", "payment_sequential"]),
        (reviews, ["order_id", "review_id"]),
        (products, ["product_id"])
    ]:
        for column in columns:
            df[column] = (
                df[column]
                .astype("string")
                .str.strip()
            )

    # Convert numerical fields
    for column in ["price", "freight_value"]:
        items[column] = items[column].map(parse_decimal)

    payments["payment_value"] = payments["payment_value"].map(parse_decimal)

    reviews["review_score"] = pd.to_numeric(
        reviews["review_score"], errors="coerce"
    )

    orders["order_purchase_timestamp"] = pd.to_datetime(
        orders["order_purchase_timestamp"],
        errors="coerce"
    )

    # Validate orders
    orders_clean, orders_bad = split_valid_invalid(
        orders,
        [
            (
                "missing_order_id",
                orders["order_id"].isna()
                | orders["order_id"].eq("")
            ),
            (
                "duplicate_order_id",
                orders["order_id"].duplicated(keep=False)
            ),
            (
                "invalid_purchase_timestamp",
                orders["order_purchase_timestamp"].isna()
            )
        ]
    )

    valid_order_ids = set(
        orders_clean["order_id"]
    )
    valid_product_ids = set(
        products.loc[
            products["product_id"].notna()
            & products["product_id"].ne(""),
            "product_id"
        ]
    )

    # Validate order items
    items_clean, items_bad = split_valid_invalid(
        items,
        [
            (
                "missing_order_id",
                items["order_id"].isna()
                | items["order_id"].eq("")
            ),
            (
                "missing_order_item_id",
                items["order_item_id"].isna()
                | items["order_item_id"].eq("")
            ),
            (
                "missing_product_id",
                items["product_id"].isna()
                | items["product_id"].eq("")
            ),
            (
                "orphan_order_id",
                ~items["order_id"].isin(valid_order_ids)
            ),
            (
                "orphan_product_id",
                items["product_id"].notna()
                & items["product_id"].ne("")
                & ~items["product_id"].isin(valid_product_ids)
            ),
            (
                "invalid_price",
                items["price"].isna()
                | items["price"].map(is_negative)
            ),
            (
                "invalid_freight",
                items["freight_value"].isna()
                | items["freight_value"].map(is_negative)
            ),
            (
                "duplicate_order_item_key",
                # All rows for a repeated (order_id, order_item_id) are quarantined.
                items.duplicated(
                    ["order_id", "order_item_id"],
                    keep=False
                )
            )
        ]
    )

    # Negative payments are retained because their transaction meaning is unknown.
    payments_clean, payments_bad = split_valid_invalid(
        payments,
        [
            (
                "missing_order_id",
                payments["order_id"].isna()
                | payments["order_id"].eq("")
            ),
            (
                "orphan_order_id",
                ~payments["order_id"].isin(valid_order_ids)
            ),
            (
                "invalid_payment_value",
                payments["payment_value"].isna()
            ),
            (
                "duplicate_payment_key",
                payments.duplicated(
                    ["order_id", "payment_sequential"],
                    keep=False
                )
            )
        ]
    )

    # Validate reviews
    reviews_clean, reviews_bad = split_valid_invalid(
        reviews,
        [
            (
                "missing_order_id",
                reviews["order_id"].isna()
                | reviews["order_id"].eq("")
            ),
            (
                "orphan_order_id",
                ~reviews["order_id"].isin(valid_order_ids)
            ),
            (
                "duplicate_review_id",
                reviews["review_id"].notna()
                & reviews["review_id"].ne("")
                & reviews["review_id"].duplicated(keep=False)
            ),
            (
                "invalid_review_score",
                reviews["review_score"].isna()
                | ~reviews["review_score"].between(1, 5)
            )
        ]
    )

    # Quarantine every row in a duplicate customer_id group, as with item keys.
    missing_customer_id = (
        customers["customer_id"].isna()
        | customers["customer_id"].eq("")
    )
    duplicate_customer_id = (
        customers["customer_id"].duplicated(keep=False)
        & ~missing_customer_id
    )
    customers_clean, customers_bad = split_valid_invalid(
        customers,
        [
            ("missing_customer_id", missing_customer_id),
            ("duplicate_customer_id", duplicate_customer_id)
        ]
    )
    logger.info(
        "Customer quality metrics: total=%d valid=%d quarantined=%d "
        "missing_id=%d duplicate_id=%d",
        len(customers),
        len(customers_clean),
        len(customers_bad),
        int(missing_customer_id.sum()),
        int(duplicate_customer_id.sum())
    )

    clean = {
        "orders": orders_clean,
        "customers": customers_clean,
        "items": items_clean,
        "payments": payments_clean,
        "reviews": reviews_clean
    }

    quarantine = {
        "orders": orders_bad,
        "customers": customers_bad,
        "items": items_bad,
        "payments": payments_bad,
        "reviews": reviews_bad
    }

    return clean, quarantine
