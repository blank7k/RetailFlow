
import pandas as pd
import pytest

from src.transform import transform_data


def sample_data():

    return {
        "orders": pd.DataFrame({
            "order_id": ["O101", "O102"],
            "customer_id": ["C001", "C002"],
            "order_status": ["delivered", "delivered"],
            "order_purchase_timestamp": pd.to_datetime([
                "2020-01-01",
                "2020-01-02"
            ])
        }),

        "customers": pd.DataFrame({
            "customer_id": ["C001", "C002"],
            "customer_unique_id": ["U001", "U002"],
            "customer_city": ["Mumbai", "Pune"],
            "customer_state": ["MH", "MH"]
        }),

        "items": pd.DataFrame({
            "order_id": ["O101", "O101", "O102"],
            "price": [10.00, 5.00, 25.00],
            "freight_value": [1.00, 2.00, 4.00]
        }),

        "payments": pd.DataFrame({
            "order_id": ["O101", "O101"],
            "payment_value": [10.00, 8.00]
        }),

        "reviews": pd.DataFrame({
            "review_id": pd.Series(dtype="object"),
            "order_id": pd.Series(dtype="object"),
            "review_score": pd.Series(dtype="float64")
        })
    }


def test_one_row_per_order():
    result = transform_data(sample_data())

    assert len(result) == 2
    assert result["order_id"].is_unique


def test_item_aggregation():
    result = transform_data(sample_data())

    order = result.loc[
        result["order_id"] == "O101"
    ].iloc[0]

    assert order["item_count"] == 2
    assert order["merchandise_value"] == pytest.approx(15.00)
    assert order["freight_value"] == pytest.approx(3.00)


def test_payment_aggregation_without_fanout():
    result = transform_data(sample_data())

    order = result.loc[
        result["order_id"] == "O101"
    ].iloc[0]

    assert order["payment_count"] == 2
    assert order["payment_total"] == pytest.approx(18.00)


def test_orders_without_payments_are_preserved():
    result = transform_data(sample_data())

    order = result.loc[
        result["order_id"] == "O102"
    ].iloc[0]

    assert order["payment_count"] == 0
    assert pd.isna(order["payment_total"])
