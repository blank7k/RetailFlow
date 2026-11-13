
import os
from logger import logger
from dotenv import load_dotenv
from sqlalchemy import URL, create_engine

from extract import extract_data
from validate import validate_data
from transform import transform_data
from load import load_data

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")


def main():

    password = os.getenv("PG_PASSWORD")

    if not password:
        raise RuntimeError(
            "PG_PASSWORD not found in .env"
        )

    # Create PostgreSQL connection
    url = URL.create(
        "postgresql+psycopg",
        username=os.getenv("PG_USER", "postgres"),
        password=password,
        host=os.getenv("PG_HOST", "localhost"),
        port=int(os.getenv("PG_PORT", "5432")),
        database=os.getenv("PG_DATABASE", "retailflow")
    )

    engine = create_engine(
        url,
        pool_pre_ping=True
    )

    try:

        print("\n===== RETAILFLOW ETL STARTED =====")

        # STEP 1: Extract
        data = extract_data(engine)

        # STEP 2: Validate
        clean, quarantine = validate_data(data)

        print("\n===== VALIDATION RESULTS =====")

        for name, df in clean.items():
            print(f"{name}: {len(df)} valid records")

        # STEP 3: Transform
        print("\n===== TRANSFORMING DATA =====")

        summary = transform_data(clean)

        print(
            "Analytical dataset shape:",
            summary.shape
        )

        # STEP 4: Load
        print("\n===== LOADING DATA =====")

        load_data(
            engine,
            summary,
            quarantine
        )

        print("\n===== PIPELINE COMPLETED =====")

    finally:
        engine.dispose()


if __name__ == "__main__":
    main()
