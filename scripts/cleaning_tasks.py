from __future__ import annotations

from typing import Any

import pandas as pd


def parse_invoice_dates(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["InvoiceDate"] = pd.to_datetime(df["InvoiceDate"], errors="coerce")
    return df


def create_sales_column(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Sales"] = df["Quantity"] * df["UnitPrice"]
    return df


def identify_cancelled_invoices(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    invoice_numbers = df["InvoiceNo"].astype("string").str.strip()
    df["IsCancelled"] = invoice_numbers.str.startswith("C", na=False)
    return df


def normalize_customer_id(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["CustomerID"] = df["CustomerID"].astype("Int64")
    return df


def is_missing_customer_id(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["IsMissingCustomerID"] = df["CustomerID"].isna()
    return df


def invoice_date_parse(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["InvoiceMonth"] = df["InvoiceDate"].dt.month
    df["InvoiceDateOnly"] = df["InvoiceDate"].dt.date
    return df

def standardize_text_fields(df: pd.DataFrame, fields: list[str]) -> pd.DataFrame:
    df = df.copy()
    for field in fields:
        if field in df.columns:
            df[field] = (
                df[field]
                .astype("string")
                .str.strip()
                .str.replace(r"\s+", " ", regex=True)
            )
    return df


def inspect_negative_quantity(df: pd.DataFrame, sample_size: int = 5) -> dict[str, Any]:
    negative_rows = df[df["Quantity"] < 0]
    return {
        "count": int(len(negative_rows)),
        "sample": negative_rows.head(sample_size),
    }


def inspect_non_positive_unit_price(df: pd.DataFrame, sample_size: int = 5) -> dict[str, Any]:
    flagged_rows = df[df["UnitPrice"] <= 0]
    return {
        "count": int(len(flagged_rows)),
        "sample": flagged_rows.head(sample_size),
    }


def check_duplicates(df: pd.DataFrame) -> dict[str, Any]:
    duplicate_count = int(df.duplicated().sum())
    return {
        "count": duplicate_count,
        "has_duplicates": duplicate_count > 0,
    }


def check_missing_customer_id(df: pd.DataFrame) -> dict[str, Any]:
    missing_count = int(df["CustomerID"].isna().sum())
    return {
        "count": missing_count,
        "ratio": missing_count / len(df) if len(df) else 0,
    }


def prepare_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df = standardize_text_fields(df, ["InvoiceNo", "StockCode", "Description", "Country"])
    df = parse_invoice_dates(df)
    df = normalize_customer_id(df)
    df = create_sales_column(df)
    df = identify_cancelled_invoices(df)
    df = is_missing_customer_id(df)
    df = invoice_date_parse(df)
    return df


def create_analysis_ready_sales(df: pd.DataFrame) -> pd.DataFrame:
    filtered_df = df[
        (df["Quantity"] >= 1)
        & (df["UnitPrice"] >= 1)
    ].copy()
    return filtered_df


def build_cleaning_report(df: pd.DataFrame) -> dict[str, Any]:
    cancelled_rows = df[df["IsCancelled"]]
    unique_cancelled = cancelled_rows["InvoiceNo"].astype("string").nunique(dropna=True)
    negative_quantity = inspect_negative_quantity(df)
    non_positive_unit_price = inspect_non_positive_unit_price(df)
    duplicates = check_duplicates(df)
    missing_customer_id = check_missing_customer_id(df)
    invalid_invoice_dates = int(df["InvoiceDate"].isna().sum())
    text_fields = ["InvoiceNo", "StockCode", "Description", "Country"]

    cleaning_summary = pd.DataFrame(
        [
            {
                "Step": "Parse InvoiceDate as datetime",
                "Issue Found": "Dates may be stored as text or mixed formats.",
                "Action Taken": "Converted InvoiceDate with pd.to_datetime(errors='coerce').",
                "Rows Affected": invalid_invoice_dates,
                "Reason": "Datetime values are needed for time-based analysis and invalid dates should surface as missing.",
            },
            {
                "Step": "Create Sales column",
                "Issue Found": "Sales was not explicitly stored in the raw data.",
                "Action Taken": "Created Sales as Quantity * UnitPrice.",
                "Rows Affected": int(len(df)),
                "Reason": "A transaction-level revenue field simplifies reporting and downstream analysis.",
            },
            {
                "Step": "Identify cancelled invoices",
                "Issue Found": "Cancelled transactions are embedded in InvoiceNo values starting with C.",
                "Action Taken": "Flagged cancelled rows in IsCancelled.",
                "Rows Affected": int(len(cancelled_rows)),
                "Reason": "Cancellations should be easy to filter separately from completed sales.",
            },
            {
                "Step": "Inspect negative Quantity",
                "Issue Found": "Some rows have negative quantities.",
                "Action Taken": "Kept rows and surfaced them for review in the report.",
                "Rows Affected": negative_quantity["count"],
                "Reason": "Negative quantity often indicates returns, reversals, or corrections.",
            },
            {
                "Step": "Inspect zero or negative UnitPrice",
                "Issue Found": "Some rows have zero or negative unit prices.",
                "Action Taken": "Kept rows and surfaced them for review in the report.",
                "Rows Affected": non_positive_unit_price["count"],
                "Reason": "These rows may represent free items, adjustments, or data quality issues.",
            },
            {
                "Step": "Check duplicates",
                "Issue Found": "Some rows are exact duplicates.",
                "Action Taken": "Counted duplicate rows without dropping them.",
                "Rows Affected": duplicates["count"],
                "Reason": "Duplicates should be reviewed before removal to avoid losing valid repeated transactions.",
            },
            {
                "Step": "Check missing CustomerID",
                "Issue Found": "Some transactions are missing CustomerID.",
                "Action Taken": "Flagged missing CustomerID rows in IsMissingCustomerID.",
                "Rows Affected": missing_customer_id["count"],
                "Reason": "Missing customer identifiers limit customer-level analysis and segmentation.",
            },
            {
                "Step": "Standardize text fields",
                "Issue Found": "Text fields can contain extra spaces or inconsistent spacing.",
                "Action Taken": f"Trimmed and normalized whitespace in {', '.join(text_fields)}.",
                "Rows Affected": int(len(df)),
                "Reason": "Standardized text reduces duplicate-like values caused by formatting differences.",
            },
        ]
    )

    return {
        "cancelled_invoices": int(len(cancelled_rows)),
        "unique_cancelled_invoices": int(unique_cancelled),
        "negative_quantity": negative_quantity,
        "non_positive_unit_price": non_positive_unit_price,
        "duplicates": duplicates,
        "missing_customer_id": missing_customer_id,
        "cleaning_summary": cleaning_summary,
    }
