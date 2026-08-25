from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from cleaning_tasks import build_cleaning_report, create_analysis_ready_sales, prepare_dataframe


def find_raw_workbook() -> Path:
    raw_directory = Path(__file__).resolve().parents[1] / "data" / "raw"
    excel_files = sorted(raw_directory.glob("*.xlsx"))

    if not excel_files:
        raise FileNotFoundError(f"No .xlsx files found in {raw_directory}")

    return excel_files[0]


def load_dataframe(workbook_path: Path) -> pd.DataFrame:
    return pd.read_excel(workbook_path)


def save_cleaning_summary(summary_df: pd.DataFrame) -> Path:
    reports_directory = Path(__file__).resolve().parents[1] / "reports"
    reports_directory.mkdir(parents=True, exist_ok=True)
    output_path = reports_directory / "cleaning_summary.csv"
    summary_df.to_csv(output_path, index=False)
    return output_path


def save_analysis_ready_sales(df: pd.DataFrame) -> Path:
    reports_directory = Path(__file__).resolve().parents[1] / "data" / "processed"
    reports_directory.mkdir(parents=True, exist_ok=True)
    output_path = reports_directory / "analysis_ready_sales.csv"
    df.to_csv(output_path, index=False)
    return output_path


def print_dataframe_slice(df: pd.DataFrame, start: int = 1, end: int = 5, label: str = "Rows") -> None:
    print(f"\n{label} {start} to {end}:")
    start_index = max(start - 1, 0)
    end_index = min(end, len(df))
    print(df.iloc[start_index:end_index].to_string(index=True))


def print_basic_stats(df: pd.DataFrame) -> None:
    print("\nBasic stats:")

    for column in df.columns:
        series = df[column]
        non_null = int(series.notna().sum())
        missing = int(series.isna().sum())
        unique = int(series.nunique(dropna=True))

        print(f"\n{column}: non-null={non_null}, missing={missing}, unique={unique}")

        if pd.api.types.is_datetime64_any_dtype(series):
            print(f"min={series.min()}, max={series.max()}")
            continue

        if pd.api.types.is_numeric_dtype(series) and not pd.api.types.is_bool_dtype(series):
            print(
                f"min={series.min()}, "
                f"max={series.max()}, "
                f"mean={series.mean():.2f}"
            )
            continue

        top_values = series.astype("string").value_counts(dropna=True).head(3).to_dict()
        print(f"top values={top_values}")


def print_cleaning_summary_table(summary_df: pd.DataFrame) -> None:
    print("\nCleaning summary table:")
    print(summary_df.to_string(index=False))


def print_cleaning_report(report: dict[str, object]) -> None:
    print("\nCleaning report:")
    print(f"cancelled invoices={report['cancelled_invoices']}")
    print(f"unique cancelled invoices={report['unique_cancelled_invoices']}")

    negative_quantity = report["negative_quantity"]
    print(f"negative quantity rows={negative_quantity['count']}")
    if not negative_quantity["sample"].empty:
        print(negative_quantity["sample"].to_string(index=False))

    non_positive_unit_price = report["non_positive_unit_price"]
    print(f"zero or negative unit price rows={non_positive_unit_price['count']}")
    if not non_positive_unit_price["sample"].empty:
        print(non_positive_unit_price["sample"].to_string(index=False))

    duplicates = report["duplicates"]
    print(f"duplicate rows={duplicates['count']}")

    missing_customer_id = report["missing_customer_id"]
    print(
        "missing CustomerID rows="
        f"{missing_customer_id['count']} ({missing_customer_id['ratio']:.2%})"
    )


def main() -> None:
    workbook_path = find_raw_workbook()
    df = load_dataframe(workbook_path)
    df = prepare_dataframe(df)
    cleaning_report = build_cleaning_report(df)
    analysis_ready_df = create_analysis_ready_sales(df)
    summary_output_path = save_cleaning_summary(cleaning_report["cleaning_summary"])
    analysis_ready_output_path = save_analysis_ready_sales(analysis_ready_df)

    print(f"File: {workbook_path}")
    print(f"Shape: {df.shape}")
    print(f"Cleaning summary saved to: {summary_output_path}")
    print(f"Analysis-ready sales saved to: {analysis_ready_output_path}")
    print(f"Analysis-ready shape: {analysis_ready_df.shape}")
    print_dataframe_slice(df, start=1, end=5, label="Records")
    print_dataframe_slice(df, start=10, end=20, label="Rows")
    print_basic_stats(df)
    print_cleaning_summary_table(cleaning_report["cleaning_summary"])
    print_cleaning_report(cleaning_report)


if __name__ == "__main__":
    main()
