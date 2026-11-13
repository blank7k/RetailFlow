from decimal import Decimal

import pandas as pd
import pyarrow as pa

from src.load import build_parquet_table


def test_financial_parquet_columns_use_decimal_12_2():
    summary = pd.DataFrame({
        "order_id": ["O1", "O2"],
        "merchandise_value": [Decimal("12.34"), None],
        "freight_value": [Decimal("1.20"), None],
        "payment_total": [Decimal("13.54"), None]
    })

    table = build_parquet_table(summary)

    for column in ("merchandise_value", "freight_value", "payment_total"):
        assert table.schema.field(column).type == pa.decimal128(12, 2)


def test_raw_loader_import_is_safe():
    import src.load_raw as load_raw

    assert callable(load_raw.main)


def test_raw_loader_fails_clearly_when_required_csv_is_missing(
    monkeypatch,
    tmp_path
):
    import src.load_raw as load_raw

    monkeypatch.setattr(load_raw, "RAW_DIR", tmp_path)
    monkeypatch.setattr(load_raw, "files", {"orders": "required.csv"})

    try:
        load_raw.main()
    except FileNotFoundError as error:
        assert "required.csv" in str(error)
    else:
        raise AssertionError("Missing CSV should stop raw loading")
