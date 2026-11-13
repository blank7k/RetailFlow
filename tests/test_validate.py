import pandas as pd

from src.validate import validate_data


def valid_data():
    return {
        "orders": pd.DataFrame({
            "order_id": ["O1"],
            "customer_id": ["C1"],
            "order_status": ["delivered"],
            "order_purchase_timestamp": ["2018-01-01"]
        }),
        "customers": pd.DataFrame({
            "customer_id": ["C1"],
            "customer_unique_id": ["U1"],
            "customer_city": ["Sao Paulo"],
            "customer_state": ["SP"]
        }),
        "items": pd.DataFrame({
            "order_id": ["O1"],
            "order_item_id": [1],
            "product_id": ["P1"],
            "price": [10.00],
            "freight_value": [2.00]
        }),
        "payments": pd.DataFrame({
            "order_id": ["O1"],
            "payment_sequential": [1],
            "payment_type": ["credit_card"],
            "payment_value": [12.00]
        }),
        "reviews": pd.DataFrame({
            "review_id": ["R1"],
            "order_id": ["O1"],
            "review_score": [5]
        }),
        "products": pd.DataFrame({
            "product_id": ["P1"]
        })
    }


def test_missing_order_id_is_quarantined():
    data = valid_data()
    data["orders"].loc[0, "order_id"] = None

    clean, quarantine = validate_data(data)

    assert clean["orders"].empty
    assert quarantine["orders"]["validation_errors"].str.contains(
        "missing_order_id"
    ).all()


def test_all_duplicate_order_ids_are_quarantined():
    data = valid_data()
    data["orders"] = pd.concat(
        [data["orders"], data["orders"]],
        ignore_index=True
    )

    clean, quarantine = validate_data(data)

    assert clean["orders"].empty
    assert len(quarantine["orders"]) == 2
    assert quarantine["orders"]["validation_errors"].str.contains(
        "duplicate_order_id"
    ).all()


def test_all_rows_with_duplicate_item_keys_are_quarantined():
    data = valid_data()
    data["items"] = pd.concat(
        [data["items"], data["items"]],
        ignore_index=True
    )

    clean, quarantine = validate_data(data)

    assert clean["items"].empty
    assert len(quarantine["items"]) == 2
    assert quarantine["items"]["validation_errors"].str.contains(
        "duplicate_order_item_key"
    ).all()


def test_negative_item_price_is_quarantined():
    data = valid_data()
    data["items"].loc[0, "price"] = -1

    clean, quarantine = validate_data(data)

    assert clean["items"].empty
    assert "invalid_price" in quarantine["items"].iloc[0]["validation_errors"]


def test_invalid_review_score_is_quarantined():
    data = valid_data()
    data["reviews"].loc[0, "review_score"] = 6

    clean, quarantine = validate_data(data)

    assert clean["reviews"].empty
    assert "invalid_review_score" in quarantine["reviews"].iloc[0]["validation_errors"]


def test_missing_customer_id_is_quarantined_and_reported(caplog):
    caplog.set_level("INFO", logger="retailflow")
    data = valid_data()
    data["customers"].loc[0, "customer_id"] = None

    clean, quarantine = validate_data(data)

    assert clean["customers"].empty
    assert "missing_customer_id" in quarantine["customers"].iloc[0]["validation_errors"]
    assert "missing_id=1" in caplog.text


def test_duplicate_customer_ids_are_quarantined_as_a_group():
    data = valid_data()
    data["customers"] = pd.concat(
        [data["customers"], data["customers"]],
        ignore_index=True
    )

    clean, quarantine = validate_data(data)

    assert clean["customers"].empty
    assert len(quarantine["customers"]) == 2
    assert quarantine["customers"]["validation_errors"].str.contains(
        "duplicate_customer_id"
    ).all()


def test_missing_order_item_id_is_quarantined():
    data = valid_data()
    data["items"].loc[0, "order_item_id"] = None

    clean, quarantine = validate_data(data)

    assert clean["items"].empty
    assert "missing_order_item_id" in quarantine["items"].iloc[0]["validation_errors"]


def test_missing_or_unknown_product_id_is_quarantined():
    data = valid_data()
    data["items"].loc[0, "product_id"] = "UNKNOWN"

    clean, quarantine = validate_data(data)

    assert clean["items"].empty
    assert "orphan_product_id" in quarantine["items"].iloc[0]["validation_errors"]


def test_missing_product_id_is_quarantined():
    data = valid_data()
    data["items"].loc[0, "product_id"] = None

    clean, quarantine = validate_data(data)

    assert clean["items"].empty
    assert "missing_product_id" in quarantine["items"].iloc[0]["validation_errors"]


def test_duplicate_review_ids_are_quarantined_as_a_group():
    data = valid_data()
    data["reviews"] = pd.concat(
        [data["reviews"], data["reviews"]],
        ignore_index=True
    )

    clean, quarantine = validate_data(data)

    assert clean["reviews"].empty
    assert len(quarantine["reviews"]) == 2
    assert quarantine["reviews"]["validation_errors"].str.contains(
        "duplicate_review_id"
    ).all()


def test_negative_payment_is_retained_pending_transaction_semantics():
    data = valid_data()
    data["payments"].loc[0, "payment_value"] = -12

    clean, quarantine = validate_data(data)

    assert clean["payments"]["payment_value"].iloc[0] == -12
    assert quarantine["payments"].empty
