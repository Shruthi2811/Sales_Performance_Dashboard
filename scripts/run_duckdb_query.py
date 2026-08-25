from __future__ import annotations

import argparse
from pathlib import Path

import duckdb


def default_database_path() -> Path:
    return Path(__file__).resolve().parents[1] / "data" / "processed" / "sales.duckdb"


def default_query_path() -> Path:
    return Path(__file__).resolve().parents[1] / "queries" / "kpi_summary.sql"


def resolve_path(raw_path: str | None, fallback: Path) -> Path:
    if raw_path is None:
        return fallback

    path = Path(raw_path)
    if not path.is_absolute():
        path = Path.cwd() / path
    return path


def default_table_name(sql_path: Path) -> str:
    return sql_path.stem


def validate_inputs(db_path: Path, sql_path: Path) -> None:
    if not db_path.exists():
        raise FileNotFoundError(f"DuckDB database not found: {db_path}")

    if not sql_path.exists():
        raise FileNotFoundError(f"SQL file not found: {sql_path}")


def read_sql(sql_path: Path) -> str:
    return sql_path.read_text().strip().rstrip(";")


def run_query_file(db_path: Path, sql_path: Path, read_only: bool = True) -> None:
    validate_inputs(db_path, sql_path)

    sql = read_sql(sql_path)
    connection = duckdb.connect(str(db_path), read_only=read_only)
    try:
        result = connection.execute(sql).fetchdf()
        print(f"Database: {db_path}")
        print(f"SQL file: {sql_path}")
        print(result.to_string(index=False))
    finally:
        connection.close()


def materialize_query_file_to_table(db_path: Path, sql_path: Path, table_name: str) -> None:
    validate_inputs(db_path, sql_path)

    sql = read_sql(sql_path)
    connection = duckdb.connect(str(db_path), read_only=False)
    try:
        connection.execute(f"DROP TABLE IF EXISTS {table_name}")
        connection.execute(f"CREATE TABLE {table_name} AS {sql}")
        row_count = connection.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        print(f"Database: {db_path}")
        print(f"SQL file: {sql_path}")
        print(f"Materialized table: {table_name}")
        print(f"Rows written: {row_count}")
    finally:
        connection.close()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a SQL file against DuckDB or materialize it into a table."
    )
    parser.add_argument(
        "--sql",
        default=str(default_query_path()),
        help="Path to the SQL file to run.",
    )
    parser.add_argument(
        "--db",
        default=str(default_database_path()),
        help="Path to the DuckDB database file.",
    )
    parser.add_argument(
        "--table",
        help="Materialize the SQL result into this table name. Defaults to the SQL filename stem when --materialize is used without --table.",
    )
    parser.add_argument(
        "--materialize",
        action="store_true",
        help="Write the SQL result into a DuckDB table instead of printing it.",
    )
    parser.add_argument(
        "--read-write",
        action="store_true",
        help="Run the query in read-write mode instead of read-only mode.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    sql_path = resolve_path(args.sql, default_query_path())
    db_path = resolve_path(args.db, default_database_path())

    if args.materialize:
        table_name = args.table or default_table_name(sql_path)
        materialize_query_file_to_table(db_path, sql_path, table_name)
        return

    run_query_file(db_path, sql_path, read_only=not args.read_write)


if __name__ == "__main__":
    main()
