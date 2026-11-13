
import pandas as pd


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

    # Normalise identifier columns
    for df, columns in [
        (orders, ["order_id", "customer_id"]),
        (customers, ["customer_id"]),
        (items, ["order_id", "order_item_id"]),
        (payments, ["order_id", "payment_sequential"]),
        (reviews, ["order_id", "review_id"])
    ]:
        for column in columns:
            df[column] = (
                df[column]
                .astype("string")
                .str.strip()
            )

    # Convert numerical fields
    for column in ["price", "freight_value"]:
        items[column] = pd.to_numeric(
            items[column], errors="coerce"
        )

    payments["payment_value"] = pd.to_numeric(
        payments["payment_value"], errors="coerce"
    )

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
                "orphan_order_id",
                ~items["order_id"].isin(valid_order_ids)
            ),
            (
                "invalid_price",
                items["price"].isna()
                | items["price"].lt(0)
            ),
            (
                "invalid_freight",
                items["freight_value"].isna()
                | items["freight_value"].lt(0)
            ),
            (
                "duplicate_order_item_key",
                items.duplicated(
                    ["order_id", "order_item_id"],
                    keep=False
                )
            )
        ]
    )

    # Validate payments
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
                | payments["payment_value"].lt(0)
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
                "invalid_review_score",
                reviews["review_score"].isna()
                | ~reviews["review_score"].between(1, 5)
            )
        ]
    )

    # Customer ID must be unique in the lookup table
    customers = customers[
        customers["customer_id"].notna()
        & customers["customer_id"].ne("")
    ].copy()

    if customers["customer_id"].duplicated().any():
        raise ValueError(
            "Duplicate customer_id found in customers table"
        )

    clean = {
        "orders": orders_clean,
        "customers": customers,
        "items": items_clean,
        "payments": payments_clean,
        "reviews": reviews_clean
    }

    quarantine = {
        "orders": orders_bad,
        "items": items_bad,
        "payments": payments_bad,
        "reviews": reviews_bad
    }

    return clean, quarantine
