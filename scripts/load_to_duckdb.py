from __future__ import annotations

from pathlib import Path

import duckdb


def find_processed_csv() -> Path:
    csv_path = Path(__file__).resolve().parents[1] / "data" / "processed" / "analysis_ready_sales.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Processed CSV not found: {csv_path}")
    return csv_path


def database_path() -> Path:
    return Path(__file__).resolve().parents[1] / "data" / "processed" / "sales.duckdb"


def load_csv_to_duckdb(csv_path: Path, db_path: Path, table_name: str = "analysis_ready_sales") -> None:
    connection = duckdb.connect(str(db_path))
    try:
        connection.execute(f"DROP TABLE IF EXISTS {table_name}")
        connection.execute(
            f"""
            CREATE TABLE {table_name} AS
            SELECT *
            FROM read_csv_auto(
                ?,
                HEADER = TRUE,
                types = {{
                    'InvoiceNo': 'VARCHAR',
                    'StockCode': 'VARCHAR',
                    'Description': 'VARCHAR',
                    'InvoiceDate': 'TIMESTAMP',
                    'CustomerID': 'BIGINT',
                    'Country': 'VARCHAR',
                    'IsCancelled': 'BOOLEAN',
                    'IsMissingCustomerID': 'BOOLEAN',
                    'InvoiceDateOnly': 'DATE'
                }}
            )
            """,
            [str(csv_path)],
        )

        row_count = connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        print(f"Database: {db_path}")
        print(f"Table: {table_name}")
        print(f"Rows loaded: {row_count}")
    finally:
        connection.close()


def main() -> None:
    csv_path = find_processed_csv()
    db_path = database_path()
    load_csv_to_duckdb(csv_path, db_path)


if __name__ == "__main__":
    main()
