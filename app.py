from __future__ import annotations

from collections import Counter
from itertools import combinations
from pathlib import Path
import warnings

import altair as alt
import duckdb
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "data" / "processed" / "sales.duckdb"
CSV_PATH = BASE_DIR / "data" / "processed" / "analysis_ready_sales.csv"
NON_PRODUCT_STOCK_CODES = {"POST", "DOT", "BANK CHARGES", "M", "MANUAL", "CRUK", "AMAZONFEE", "C2"}


st.set_page_config(
    page_title="Sales Performance Dashboard",
    page_icon=":bar_chart:",
    layout="wide",
)

warnings.filterwarnings(
    "ignore",
    message=r".*convert_dtype parameter is deprecated.*",
    category=FutureWarning,
    module=r"altair\.utils\.core",
)


def inject_styles() -> None:
    st.markdown(
        """
        <style>
            :root {
                --page-bg: #f5f6fb;
                --surface: rgba(255, 255, 255, 0.94);
                --surface-strong: #ffffff;
                --surface-soft: #f3f4fa;
                --border: #e7e9f4;
                --text-strong: #1b1d29;
                --text-muted: #8b90a7;
                --primary: #6c63ff;
                --primary-deep: #1b1d29;
                --primary-soft: #eeedff;
                --secondary: #8a7dff;
                --accent: #ffc93c;
                --shadow: 0 22px 48px rgba(84, 88, 125, 0.10);
            }
            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(108, 99, 255, 0.08), transparent 24%),
                    radial-gradient(circle at top right, rgba(255, 201, 60, 0.08), transparent 18%),
                    linear-gradient(180deg, #f7f8fc 0%, #f2f4fa 100%);
                color: var(--text-strong);
            }
            .block-container {
                padding-top: 1.5rem;
                padding-bottom: 2rem;
                max-width: 1360px;
            }
            [data-testid="stSidebar"] {
                background: #fdfdff;
                border-right: 1px solid #ececf5;
                min-width: 18rem;
                max-width: 18rem;
            }
            [data-testid="stSidebar"] > div:first-child {
                background: #fdfdff;
                padding-top: 1.2rem;
            }
            [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
            [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] li,
            [data-testid="stSidebar"] label,
            [data-testid="stSidebar"] span {
                color: var(--text-strong);
            }
            .sidebar-brand {
                background: transparent;
                border-radius: 0;
                padding: 0.45rem 0.4rem 0.85rem;
                margin-bottom: 1.15rem;
                display: flex;
                gap: 0.7rem;
                align-items: center;
            }
            .sidebar-brand-mark {
                width: 1.65rem;
                height: 1.65rem;
                border-radius: 999px;
                background: conic-gradient(from 205deg, #6c63ff 0deg 265deg, #dfe2f5 265deg 360deg);
                flex-shrink: 0;
                position: relative;
            }
            .sidebar-brand-mark::after {
                content: "";
                position: absolute;
                inset: 0.34rem;
                border-radius: 999px;
                background: #ffffff;
            }
            .sidebar-brand-copy {
                color: #202233;
                font-size: 1.4rem;
                line-height: 1;
                font-weight: 800;
                letter-spacing: -0.03em;
            }
            .sidebar-brand-copy small {
                display: block;
                color: #202233;
                font-size: 0.76rem;
                font-weight: 700;
                letter-spacing: 0;
                opacity: 0.92;
            }
            .sidebar-section-label {
                color: #a0a5b8;
                font-size: 0.8rem;
                font-weight: 600;
                letter-spacing: 0;
                text-transform: none;
                margin: 1rem 0 0.55rem;
                padding-left: 0.2rem;
            }
            [data-testid="stSidebar"] .stRadio > label {
                display: none;
            }
            [data-testid="stSidebar"] .stRadio [role="radiogroup"] {
                gap: 0.3rem;
            }
            [data-testid="stSidebar"] .stRadio [role="radio"] {
                background: transparent;
                border: 1px solid transparent;
                border-radius: 12px;
                color: #6f768b;
                padding: 0.72rem 0.9rem 0.72rem 0.95rem;
                transition: all 0.2s ease;
                font-weight: 600;
                min-height: auto;
            }
            [data-testid="stSidebar"] .stRadio [role="radio"][aria-checked="true"] {
                background: #6c63ff;
                border-color: rgba(108, 99, 255, 0.2);
                color: #ffffff;
                box-shadow: 0 10px 18px rgba(108, 99, 255, 0.22);
            }
            [data-testid="stSidebar"] .stRadio [role="radio"]:focus-visible {
                box-shadow: 0 0 0 2px rgba(108, 99, 255, 0.18);
            }
            [data-testid="stSidebar"] .stRadio [role="radio"]:hover {
                border-color: #ececf6;
                background: #f6f7fc;
            }
            [data-testid="stSidebar"] .stRadio [role="radio"][aria-checked="true"]:hover {
                background: #6c63ff;
            }
            .sidebar-static-item {
                color: #6f768b;
                font-size: 0.98rem;
                font-weight: 600;
                padding: 0.72rem 0.95rem;
                border-radius: 12px;
                margin: 0.05rem 0;
            }
            .sidebar-static-item:hover {
                background: #f6f7fc;
            }
            .sidebar-spacer {
                height: 11rem;
            }
            .sidebar-logout {
                border: 1px solid #ececf6;
                border-radius: 14px;
                padding: 0.82rem 0.95rem;
                color: #5c6378;
                font-size: 0.98rem;
                font-weight: 700;
                display: flex;
                align-items: center;
                gap: 0.6rem;
                background: #ffffff;
                box-shadow: 0 10px 18px rgba(95, 102, 132, 0.06);
            }
            .sidebar-logout-icon {
                width: 1rem;
                height: 1rem;
                border: 1.7px solid currentColor;
                border-radius: 4px;
                position: relative;
                box-sizing: border-box;
            }
            .sidebar-logout-icon::before {
                content: "";
                position: absolute;
                left: -0.45rem;
                top: 0.31rem;
                width: 0.55rem;
                height: 0.2rem;
                background: currentColor;
                border-radius: 999px;
            }
            .sidebar-logout-icon::after {
                content: "";
                position: absolute;
                left: -0.2rem;
                top: 0.18rem;
                width: 0.42rem;
                height: 0.42rem;
                border-top: 0.14rem solid currentColor;
                border-left: 0.14rem solid currentColor;
                transform: rotate(-45deg);
            }
            .hero-shell {
                background: linear-gradient(135deg, rgba(108, 99, 255, 0.12) 0%, rgba(255, 255, 255, 0.72) 55%, rgba(255, 201, 60, 0.12) 100%);
                border: 1px solid rgba(255, 255, 255, 0.85);
                border-radius: 30px;
                padding: 1rem;
                box-shadow: var(--shadow);
                margin-bottom: 1.2rem;
            }
            .hero-panel {
                background: var(--surface-strong);
                border: 1px solid var(--border);
                border-radius: 26px;
                padding: 1.5rem 1.75rem;
            }
            .hero-title {
                color: var(--text-strong);
                font-size: 3rem;
                font-weight: 800;
                line-height: 1;
                margin: 0;
            }
            .hero-subtitle {
                color: var(--text-muted);
                font-size: 1rem;
                margin-top: 0.45rem;
            }
            .hero-note {
                color: var(--text-muted);
                font-size: 0.98rem;
                text-align: right;
                margin-top: 0.35rem;
            }
            .kpi-card {
                background: linear-gradient(180deg, var(--surface-strong) 0%, #fafafe 100%);
                border: 1px solid var(--border);
                border-radius: 22px;
                padding: 1.2rem 1.25rem;
                min-height: 168px;
                box-shadow: 0 14px 28px rgba(70, 73, 101, 0.08);
            }
            .kpi-label {
                color: var(--text-strong);
                display: flex;
                align-items: center;
                gap: 0.55rem;
                font-size: 1rem;
                font-weight: 700;
                margin-bottom: 0.8rem;
            }
            .kpi-icon {
                width: 2rem;
                height: 2rem;
                border-radius: 999px;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                background: rgba(91, 84, 232, 0.10);
                color: #5b54e8;
                border: 1px solid rgba(91, 84, 232, 0.14);
                flex-shrink: 0;
            }
            .kpi-icon svg {
                width: 1rem;
                height: 1rem;
                stroke: currentColor;
            }
            .kpi-value {
                color: var(--primary-deep);
                font-size: 2.55rem;
                font-weight: 800;
                line-height: 1.05;
                margin-bottom: 0.55rem;
            }
            .kpi-footnote {
                color: var(--text-muted);
                font-size: 0.92rem;
            }
            .section-card {
                background: var(--surface);
                border: 1px solid var(--border);
                border-radius: 22px;
                padding: 1.15rem 1.2rem;
                margin-top: 1rem;
                box-shadow: 0 12px 24px rgba(70, 73, 101, 0.07);
            }
            .section-title {
                color: var(--text-strong);
                font-size: 1.2rem;
                font-weight: 750;
                margin-bottom: 0.4rem;
            }
            .chart-note {
                color: var(--text-muted);
                font-size: 0.9rem;
                margin-top: 0.35rem;
                line-height: 1.45;
            }
            .section-spacer {
                height: 1.15rem;
            }
            .insight-banner {
                background: linear-gradient(135deg, rgba(108, 99, 255, 0.10) 0%, rgba(255, 255, 255, 0.96) 65%);
                border: 1px solid rgba(108, 99, 255, 0.12);
                border-radius: 22px;
                padding: 1.1rem 1.2rem;
                height: 160px;
                box-shadow: 0 12px 24px rgba(70, 73, 101, 0.07);
                display: flex;
                flex-direction: column;
            }
            .insight-banner-header {
                display: flex;
                align-items: center;
                gap: 0.65rem;
                margin-bottom: 0.55rem;
            }
            .insight-banner-icon {
                width: 2rem;
                height: 2rem;
                border-radius: 999px;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                background: rgba(91, 84, 232, 0.10);
                color: #5b54e8;
                border: 1px solid rgba(91, 84, 232, 0.14);
                flex-shrink: 0;
            }
            .insight-banner-icon svg {
                width: 1rem;
                height: 1rem;
                stroke: currentColor;
            }
            .insight-banner-title {
                color: var(--text-strong);
                font-size: 1.08rem;
                font-weight: 800;
                line-height: 1.3;
            }
            .insight-banner-copy {
                color: var(--text-muted);
                font-size: 0.96rem;
                line-height: 1.5;
            }
            .treemap-board {
                position: relative;
                width: 100%;
                height: 380px;
                margin-top: 0.85rem;
            }
            .treemap-tile {
                position: absolute;
                box-sizing: border-box;
                border-radius: 22px;
                padding: 1rem 1.05rem;
                color: #ffffff;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                box-shadow: 0 14px 28px rgba(70, 73, 101, 0.10);
                overflow: hidden;
            }
            .treemap-label {
                font-size: 1.02rem;
                font-weight: 800;
                line-height: 1.2;
            }
            .treemap-value {
                font-size: 2rem;
                font-weight: 800;
                line-height: 1;
                margin-top: 0.35rem;
            }
            .treemap-meta {
                font-size: 0.9rem;
                line-height: 1.45;
                color: rgba(255, 255, 255, 0.86);
            }
            .placeholder-copy {
                color: var(--text-muted);
                font-size: 0.98rem;
                margin-top: 0.3rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(show_spinner=False)
def load_sales_data() -> pd.DataFrame:
    if DB_PATH.exists():
        try:
            connection = duckdb.connect(str(DB_PATH), read_only=True)
            try:
                return connection.execute("SELECT * FROM analysis_ready_sales").fetchdf()
            finally:
                connection.close()
        except Exception:
            pass

    return pd.read_csv(CSV_PATH, parse_dates=["InvoiceDate"])


def format_currency(value: float) -> str:
    return f"${value:,.0f}"


def format_count(value: int) -> str:
    return f"{value:,}"


def compute_kpis(df: pd.DataFrame) -> dict[str, float]:
    kpi_df = df[df["CustomerID"].notna()].copy()

    total_orders = int(kpi_df["InvoiceNo"].nunique())
    total_units_sold = float(kpi_df["Quantity"].sum())
    total_revenue = float(kpi_df["Sales"].sum())

    return {
        "total_revenue": total_revenue,
        "total_unique_customers": int(kpi_df["CustomerID"].nunique()),
        "total_orders": total_orders,
        "total_products": int(kpi_df["StockCode"].nunique()),
        "avg_order_value": total_revenue / total_orders if total_orders else 0.0,
        "avg_cart_size": total_units_sold / total_orders if total_orders else 0.0,
    }


def filter_merchandise_rows(df: pd.DataFrame) -> pd.DataFrame:
    merchandise_df = df.copy()
    merchandise_df["StockCodeNormalized"] = merchandise_df["StockCode"].astype(str).str.strip().str.upper()
    merchandise_df = merchandise_df[~merchandise_df["StockCodeNormalized"].isin(NON_PRODUCT_STOCK_CODES)].copy()
    return merchandise_df.drop(columns=["StockCodeNormalized"])


def render_header() -> None:
    st.markdown(
        """
        <br></br>
        <div class="hero-shell">
            <div class="hero-panel">
                <div style="display:flex; justify-content:space-between; gap:1.5rem; align-items:flex-start; flex-wrap:wrap;">
                    <div>
                        <p class="hero-title">Sales Performance</p>
                        <div class="hero-subtitle"></div>
                    </div>
                    <div class="hero-note">
                        The data used comes from the time period<br>
                        <strong>1 December 2010 to 9 December 2011</strong>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_kpi_card(label: str, value: str, footnote: str, icon_svg: str) -> None:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">
                <span class="kpi-icon">{icon_svg}</span>
                <span>{label}</span>
            </div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-footnote">{footnote}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def get_kpi_icon(name: str) -> str:
    icons = {
        "revenue": """
            <svg viewBox="0 0 24 24" fill="none" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <circle cx="12" cy="12" r="8.5"></circle>
                <path d="M14.9 9.2c0-.9-1.2-1.7-2.9-1.7-1.7 0-2.9.8-2.9 1.9 0 2.8 5.8 1.2 5.8 4 0 1.1-1.1 2-2.9 2-1.8 0-3.1-.9-3.1-1.9"></path>
                <path d="M12 6.3v11.4"></path>
            </svg>
        """,
        "customers": """
            <svg viewBox="0 0 24 24" fill="none" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <path d="M16 19v-1.1c0-1.8-1.8-3.4-4-3.4s-4 1.6-4 3.4V19"></path>
                <circle cx="12" cy="8.5" r="3"></circle>
                <path d="M18.5 18.2v-.9c0-1.1-.7-2.1-1.8-2.8"></path>
                <path d="M16.2 5.8c1 .2 1.8 1.2 1.8 2.4 0 1.2-.8 2.2-1.8 2.4"></path>
            </svg>
        """,
        "orders": """
            <svg viewBox="0 0 24 24" fill="none" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <path d="M7 7.5h10"></path>
                <path d="M7 11.5h10"></path>
                <path d="M7 15.5h6"></path>
                <path d="M8.5 4.5h7l3 3v11a2 2 0 0 1-2 2h-9a2 2 0 0 1-2-2v-12a2 2 0 0 1 2-2z"></path>
            </svg>
        """,
        "products": """
            <svg viewBox="0 0 24 24" fill="none" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <path d="M12 3.8 19 7.5 12 11.2 5 7.5 12 3.8Z"></path>
                <path d="M19 7.5v8.3L12 19.5 5 15.8V7.5"></path>
                <path d="M12 11.2v8.3"></path>
            </svg>
        """,
        "avg_order_value": """
            <svg viewBox="0 0 24 24" fill="none" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <path d="M5.5 15.5 9 12l2.5 2.5 5-5"></path>
                <path d="M13.5 7h3.5v3.5"></path>
                <path d="M6 19h12"></path>
            </svg>
        """,
        "avg_cart_size": """
            <svg viewBox="0 0 24 24" fill="none" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">
                <circle cx="9" cy="18" r="1.2"></circle>
                <circle cx="17" cy="18" r="1.2"></circle>
                <path d="M4.5 5.5h2l1.7 7.2a1 1 0 0 0 1 .8h6.9a1 1 0 0 0 1-.8l1.1-4.9H7.2"></path>
            </svg>
        """,
    }
    return icons[name]


def render_chart_card(title: str, chart: alt.Chart) -> None:
    #st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    st.altair_chart(chart, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_chart_card_with_caption(title: str, chart: alt.Chart, caption: str) -> None:
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    st.altair_chart(chart, use_container_width=True)
    st.markdown(f'<div class="chart-note">{caption}</div>', unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_insight_banner(label: str, title: str, copy: str) -> None:
    st.markdown(
        f"""
        <div class="insight-banner">
            <div class="insight-banner-header">
                <span class="insight-banner-icon" aria-hidden="true">
                    <svg viewBox="0 0 24 24" fill="none" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 3.75a6.25 6.25 0 0 0-3.95 11.1c.52.43.83 1.07.83 1.75v.4h6.24v-.4c0-.68.31-1.32.83-1.75A6.25 6.25 0 0 0 12 3.75Z"></path>
                        <path d="M9.75 20.25h4.5"></path>
                        <path d="M10.25 17.25h3.5"></path>
                    </svg>
                </span>
                <div class="insight-banner-title">{title}</div>
            </div>
            <div class="insight-banner-copy">{copy}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def build_line_chart(df: pd.DataFrame, x: str, y: str, color: str = "#6c63ff") -> alt.Chart:
    return (
        alt.Chart(df)
        .mark_line(point=alt.OverlayMarkDef(color=color, filled=True, size=70), strokeWidth=3, color=color)
        .encode(
            x=alt.X(x, title=""),
            y=alt.Y(y, title=""),
            tooltip=[x, y],
        )
        .properties(height=280)
        .configure_view(stroke=None)
        .configure_axis(
            domain=False,
            gridColor="#eceef6",
            tickColor="#d9ddea",
            labelColor="#8b90a7",
            titleColor="#1b1d29",
        )
    )


def build_bar_chart(df: pd.DataFrame, x: str, y: str, color: str = "#6c63ff") -> alt.Chart:
    return (
        alt.Chart(df)
        .mark_bar(cornerRadiusTopRight=6, cornerRadiusBottomRight=6, color=color)
        .encode(
            x=alt.X(x, title=""),
            y=alt.Y(y, sort="-x", title=""),
            tooltip=list(df.columns),
        )
        .properties(height=320)
        .configure_view(stroke=None)
        .configure_axis(
            domain=False,
            gridColor="#eceef6",
            tickColor="#d9ddea",
            labelColor="#8b90a7",
            titleColor="#1b1d29",
        )
    )


def build_top_countries_chart(df: pd.DataFrame, note_text: str | None = None) -> alt.Chart:
    chart_df = df.copy()
    chart_df["ColorGroup"] = chart_df["Country"].apply(lambda country: "Other" if country == "Other" else "Top Country")

    bars = (
        alt.Chart(chart_df)
        .mark_bar(cornerRadiusTopRight=8, cornerRadiusBottomRight=8, size=30)
        .encode(
            x=alt.X(
                "Revenue:Q",
                title="Revenue",
                axis=alt.Axis(format="$,.0f", grid=True, gridColor="#ebeaf5"),
            ),
            y=alt.Y(
                "Country:N",
                sort=chart_df["Country"].tolist(),
                title="",
                axis=alt.Axis(labelPadding=12),
            ),
            color=alt.Color(
                "ColorGroup:N",
                scale=alt.Scale(domain=["Top Country", "Other"], range=["#6c63ff", "#cfd4e6"]),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("Country:N", title="Country"),
                alt.Tooltip("Revenue:Q", title="Revenue", format="$,.0f"),
            ],
        )
    )

    main_chart = alt.layer(bars).properties(height=300)

    if note_text is None:
        return (
            main_chart
            .configure_view(stroke=None)
            .configure(background="#fbfbfe")
            .configure_axis(
                domain=False,
                tickColor="#d9ddea",
                labelColor="#8b90a7",
                titleColor="#1b1d29",
            )
        )

    note_df = pd.DataFrame([{"Anchor": "center", "Annotation": note_text}])
    note = (
        alt.Chart(note_df)
        .mark_text(
            align="center",
            baseline="top",
            color="#7a5a00",
            fontSize=12,
            fontWeight=700,
            dy=2,
        )
        .encode(
            x=alt.X(
                "Anchor:N",
                sort=["center"],
                axis=alt.Axis(labels=False, ticks=False, domain=False, title=None),
            ),
            text="Annotation:N",
        )
        .properties(height=20)
    )

    return (
        alt.vconcat(main_chart, note, spacing=0)
        .configure_view(stroke=None)
        .configure(background="#fbfbfe")
        .configure_axis(
            domain=False,
            tickColor="#d9ddea",
            labelColor="#8b90a7",
            titleColor="#1b1d29",
        )
    )


def build_uk_international_donut(df: pd.DataFrame) -> alt.Chart:
    total_revenue = df["Revenue"].sum()
    chart_df = df.copy()
    chart_df["ShareLabel"] = chart_df["Revenue"].apply(
        lambda value: f"{(value / total_revenue):.0%}" if total_revenue else "0%"
    )
    chart_df["LabelColor"] = chart_df["Segment"].map(
        {"United Kingdom": "#ffffff", "International": "#1b1d29"}
    ).fillna("#1b1d29")

    arcs = (
        alt.Chart(chart_df)
        .mark_arc(innerRadius=72, outerRadius=120, cornerRadius=8)
        .encode(
            theta=alt.Theta("Revenue:Q"),
            color=alt.Color(
                "Segment:N",
                scale=alt.Scale(
                    domain=["United Kingdom", "International"],
                    range=["#6c63ff", "#d7dcf0"],
                ),
                legend=alt.Legend(title=None, orient="bottom"),
            ),
            tooltip=[
                alt.Tooltip("Segment:N", title="Segment"),
                alt.Tooltip("Revenue:Q", title="Revenue", format="$,.0f"),
                alt.Tooltip("ShareLabel:N", title="Revenue Share"),
            ],
        )
    )

    labels = (
        alt.Chart(chart_df)
        .mark_text(radius=96, fontSize=13, fontWeight=800)
        .encode(
            theta=alt.Theta("Revenue:Q", stack=True),
            text="ShareLabel:N",
            color=alt.Color("LabelColor:N", scale=None, legend=None),
        )
    )

    return (
        alt.layer(arcs, labels)
        .properties(height=300)
        .configure_view(stroke=None)
        .configure(background="#fbfbfe")
    )


def build_country_aov_volume_chart(df: pd.DataFrame) -> alt.Chart:
    chart_df = df.copy()
    reliability_threshold = 20
    chart_df["Confidence"] = chart_df["Total Orders"].apply(
        lambda value: "Reliable (20+ orders)" if value >= reliability_threshold else "Low sample (<20 orders)"
    )
    max_orders = float(df["Total Orders"].max()) if not df.empty else 0.0
    y_axis_max = max(600, ((int(max_orders) + 99) // 100) * 100 + 100)

    points = (
        alt.Chart(chart_df)
        .mark_circle(opacity=0.82, stroke="#ffffff", strokeWidth=1.5)
        .encode(
            x=alt.X(
                "Average Order Value:Q",
                title="Average Order Value",
                axis=alt.Axis(format="$,.0f", grid=True, gridColor="#ebeaf5"),
            ),
            y=alt.Y(
                "Total Orders:Q",
                title="Total Number of Orders",
                axis=alt.Axis(format=",d", tickMinStep=1),
                scale=alt.Scale(domain=[0, y_axis_max]),
            ),
            size=alt.Size(
                "Revenue:Q",
                title="Total Revenue",
                scale=alt.Scale(range=[180, 1800]),
                legend=None,
            ),
            color=alt.Color(
                "Confidence:N",
                scale=alt.Scale(
                    domain=["Reliable (20+ orders)", "Low sample (<20 orders)"],
                    range=["#6c63ff", "#dcd9ff"],
                ),
                legend=alt.Legend(title="Confidence", orient="top"),
            ),
            opacity=alt.Opacity(
                "Confidence:N",
                scale=alt.Scale(
                    domain=["Reliable (20+ orders)", "Low sample (<20 orders)"],
                    range=[0.88, 0.55],
                ),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("Country:N", title="Country"),
                alt.Tooltip("Average Order Value:Q", title="Avg Order Value", format="$,.0f"),
                alt.Tooltip("Total Orders:Q", title="Orders", format=","),
                alt.Tooltip("Revenue:Q", title="Revenue", format="$,.0f"),
                alt.Tooltip("Confidence:N", title="Confidence"),
            ],
        )
    )

    note_df = pd.DataFrame([{"Anchor": "center", "Annotation": "Bubble size = Total Revenue"}])
    note = (
        alt.Chart(note_df)
        .mark_text(
            align="center",
            baseline="top",
            color="#7a5a00",
            fontSize=12,
            fontWeight=700,
            dy=2,
        )
        .encode(
            x=alt.X(
                "Anchor:N",
                sort=["center"],
                axis=alt.Axis(labels=False, ticks=False, domain=False, title=None),
            ),
            text="Annotation:N",
        )
        .properties(height=20)
    )

    main_chart = alt.layer(points).properties(height=300)

    return (
        alt.vconcat(main_chart, note, spacing=0)
        .configure_view(stroke=None)
        .configure(background="#fbfbfe")
        .configure_axis(
            domain=False,
            tickColor="#d9ddea",
            labelColor="#8b90a7",
            titleColor="#1b1d29",
        )
    )


def build_country_aov_bar_chart(df: pd.DataFrame) -> alt.Chart:
    chart_df = df.copy()
    reliability_threshold = 20
    chart_df["Confidence"] = chart_df["Total Orders"].apply(
        lambda value: "Reliable (20+ orders)" if value >= reliability_threshold else "Low sample (<20 orders)"
    )
    chart_height = max(360, len(chart_df) * 34)

    return (
        alt.Chart(chart_df)
        .mark_bar(cornerRadiusTopRight=8, cornerRadiusBottomRight=8, size=22)
        .encode(
            x=alt.X(
                "Average Order Value:Q",
                title="Average Order Value",
                axis=alt.Axis(format="$,.0f", grid=True, gridColor="#ebeaf5"),
            ),
            y=alt.Y(
                "Country:N",
                sort=chart_df["Country"].tolist(),
                title="",
                axis=alt.Axis(labelPadding=12),
            ),
            color=alt.Color(
                "Confidence:N",
                scale=alt.Scale(
                    domain=["Reliable (20+ orders)", "Low sample (<20 orders)"],
                    range=["#6c63ff", "#dcd9ff"],
                ),
                legend=alt.Legend(title="Confidence", orient="bottom"),
            ),
            opacity=alt.Opacity(
                "Confidence:N",
                scale=alt.Scale(
                    domain=["Reliable (20+ orders)", "Low sample (<20 orders)"],
                    range=[0.9, 0.58],
                ),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("Country:N", title="Country"),
                alt.Tooltip("Average Order Value:Q", title="AOV", format="$,.0f"),
                alt.Tooltip("Revenue:Q", title="Revenue", format="$,.0f"),
                alt.Tooltip("Total Orders:Q", title="Orders", format=",d"),
                alt.Tooltip("Confidence:N", title="Confidence"),
            ],
        )
        .properties(height=chart_height)
        .configure_view(stroke=None)
        .configure(background="#fbfbfe")
        .configure_axis(
            domain=False,
            tickColor="#d9ddea",
            labelColor="#8b90a7",
            titleColor="#1b1d29",
        )
        .configure_legend(
            labelColor="#6f768b",
            titleColor="#1b1d29",
            orient="bottom",
        )
    )


def build_country_order_size_boxplot(df: pd.DataFrame, order: list[str]) -> alt.Chart:
    return (
        alt.Chart(df)
        .mark_boxplot(
            extent=1.5,
            size=34,
            ticks=True,
            median={"color": "#5b54e8"},
            box={"fill": "#dcd9ff", "stroke": "#8a7dff"},
            rule={"stroke": "#8a7dff"},
            outliers={"filled": True, "color": "#ffc93c", "size": 36},
        )
        .encode(
            x=alt.X(
                "Country:N",
                title="",
                sort=order,
                axis=alt.Axis(labelAngle=0, labelPadding=10),
            ),
            y=alt.Y(
                "Invoice Quantity:Q",
                title="Quantity per Invoice",
                axis=alt.Axis(format=",d", grid=True, gridColor="#ebeaf5"),
            ),
            tooltip=[
                alt.Tooltip("Country:N", title="Country"),
                alt.Tooltip("Invoice Quantity:Q", title="Invoice Quantity", format=",d"),
            ],
        )
        .properties(height=340)
        .configure_view(stroke=None)
        .configure(background="#fbfbfe")
        .configure_axis(
            domain=False,
            tickColor="#d9ddea",
            labelColor="#8b90a7",
            titleColor="#1b1d29",
        )
    )


def build_product_revenue_quantity_combo_chart(df: pd.DataFrame) -> alt.Chart:
    base = alt.Chart(df).encode(
        x=alt.X(
            "ProductLabel:N",
            sort=df["ProductLabel"].tolist(),
            title="Product / SKU",
            axis=alt.Axis(labelAngle=-35, labelLimit=210),
        )
    )

    bars = base.mark_bar(color="#dcd9ff", cornerRadiusTopLeft=7, cornerRadiusTopRight=7).encode(
        y=alt.Y(
            "Revenue:Q",
            title="Revenue",
            axis=alt.Axis(format="$,.0f", grid=True, gridColor="#ebeaf5", titleColor="#8b90a7", labelColor="#8b90a7"),
        ),
        tooltip=[
            alt.Tooltip("ProductLabel:N", title="Product"),
            alt.Tooltip("Revenue:Q", title="Revenue", format="$,.0f"),
            alt.Tooltip("Quantity Sold:Q", title="Quantity Sold", format=",d"),
        ],
    )

    quantity_y = alt.Y(
        "Quantity Sold:Q",
        title="Quantity Sold",
        axis=alt.Axis(format=",d", grid=False, titleColor="#5b54e8", labelColor="#5b54e8"),
    )
    quantity_base = base.encode(y=quantity_y)
    line = quantity_base.mark_line(color="#5b54e8", strokeWidth=3)
    points = quantity_base.mark_circle(color="#5b54e8", size=58, stroke="#ffffff", strokeWidth=1.3)

    return (
        alt.layer(bars, line, points)
        .resolve_scale(y="independent")
        .properties(height=360)
        .configure_view(stroke=None)
        .configure(background="#fbfbfe")
        .configure_axis(
            domain=False,
            tickColor="#d9ddea",
            labelColor="#8b90a7",
            titleColor="#1b1d29",
        )
    )


def build_sku_velocity_chart(df: pd.DataFrame, quantity_threshold: float, price_threshold: float) -> alt.Chart:
    base = alt.Chart(df)

    vertical_rule = alt.Chart(pd.DataFrame({"x": [quantity_threshold]})).mark_rule(
        color="#bcc2d9",
        strokeDash=[6, 6],
    ).encode(x="x:Q")
    horizontal_rule = alt.Chart(pd.DataFrame({"y": [price_threshold]})).mark_rule(
        color="#bcc2d9",
        strokeDash=[6, 6],
    ).encode(y="y:Q")

    points = base.mark_circle(opacity=0.84, stroke="#ffffff", strokeWidth=1.3).encode(
        x=alt.X(
            "Quantity Sold:Q",
            title="Quantity Sold",
            axis=alt.Axis(format=",d", grid=True, gridColor="#ebeaf5"),
        ),
        y=alt.Y(
            "Unit Price:Q",
            title="Unit Price",
            axis=alt.Axis(format="$,.2f"),
        ),
        size=alt.Size("Revenue:Q", scale=alt.Scale(range=[120, 1800]), legend=None),
        color=alt.Color(
            "Quadrant:N",
            scale=alt.Scale(
                domain=["High Volume / High Price", "High Volume / Low Price", "Low Volume / High Price", "Low Volume / Low Price"],
                range=["#5b54e8", "#6c63ff", "#ffc93c", "#cfd4e6"],
            ),
            legend=alt.Legend(title="SKU Position", orient="bottom", direction="horizontal"),
        ),
        tooltip=[
            alt.Tooltip("ProductLabel:N", title="Product"),
            alt.Tooltip("Quantity Sold:Q", title="Quantity Sold", format=",d"),
            alt.Tooltip("Unit Price:Q", title="Unit Price", format="$,.2f"),
            alt.Tooltip("Revenue:Q", title="Revenue", format="$,.0f"),
        ],
    )

    return (
        alt.layer(points, vertical_rule, horizontal_rule)
        .properties(height=360)
        .configure_view(stroke=None)
        .configure(background="#fbfbfe")
        .configure_axis(
            domain=False,
            tickColor="#d9ddea",
            labelColor="#8b90a7",
            titleColor="#1b1d29",
        )
        .configure_legend(
            labelColor="#6f768b",
            titleColor="#1b1d29",
            orient="bottom",
        )
    )


def build_market_basket_chart(df: pd.DataFrame) -> alt.Chart:
    chart_df = df.copy()
    support_threshold = 30
    chart_df["Confidence"] = chart_df["Pair Orders"].apply(
        lambda value: "Reliable (30+)" if value >= support_threshold else "Low sample (<30)"
    )

    return (
        alt.Chart(chart_df)
        .mark_bar(cornerRadiusTopRight=8, cornerRadiusBottomRight=8, size=30)
        .encode(
            x=alt.X(
                "Attach Rate:Q",
                title="Customers Who Bought A Also Bought B",
                axis=alt.Axis(format=".0%", grid=True, gridColor="#ebeaf5"),
            ),
            y=alt.Y(
                "PairLabel:N",
                sort=chart_df["PairLabel"].tolist(),
                title="",
                axis=alt.Axis(labelPadding=12),
            ),
            color=alt.Color(
                "Confidence:N",
                scale=alt.Scale(
                    domain=["Reliable (30+)", "Low sample (<30)"],
                    range=["#6c63ff", "#dcd9ff"],
                ),
                legend=alt.Legend(title="Confidence", orient="top"),
            ),
            opacity=alt.Opacity(
                "Confidence:N",
                scale=alt.Scale(
                    domain=["Reliable (30+)", "Low sample (<30)"],
                    range=[0.9, 0.58],
                ),
                legend=None,
            ),
            tooltip=[
                alt.Tooltip("Primary Product:N", title="Product A"),
                alt.Tooltip("Secondary Product:N", title="Product B"),
                alt.Tooltip("Pair Orders:Q", title="Orders Together", format=",d"),
                alt.Tooltip("Primary Orders:Q", title="Orders with Product A", format=",d"),
                alt.Tooltip("Attach Rate:Q", title="Attach Rate", format=".1%"),
                alt.Tooltip("Confidence:N", title="Confidence"),
            ],
        )
        .properties(height=320)
        .configure_view(stroke=None)
        .configure(background="#fbfbfe")
        .configure_axis(
            domain=False,
            tickColor="#d9ddea",
            labelColor="#8b90a7",
            titleColor="#1b1d29",
        )
    )


def build_histogram(df: pd.DataFrame, field: str, title: str, color: str = "#8a7dff") -> alt.Chart:
    upper_bound = float(df[field].quantile(0.99)) if not df.empty else 0.0
    filtered_df = df[df[field] <= upper_bound].copy() if upper_bound > 0 else df.copy()

    return (
        alt.Chart(filtered_df)
        .mark_bar(color=color, opacity=0.9)
        .encode(
            x=alt.X(
                f"{field}:Q",
                bin=alt.Bin(maxbins=20),
                scale=alt.Scale(domain=[0, upper_bound]) if upper_bound > 0 else alt.Undefined,
                title=title,
            ),
            y=alt.Y("count()", title="Count"),
            tooltip=[alt.Tooltip("count()", title="Count")],
        )
        .properties(height=280)
        .configure_view(stroke=None)
        .configure_axis(
            domain=False,
            gridColor="#eceef6",
            tickColor="#d9ddea",
            labelColor="#8b90a7",
            titleColor="#1b1d29",
        )
    )


def build_revenue_orders_combo_chart(df: pd.DataFrame, data_end_date: pd.Timestamp | None = None) -> alt.Chart:
    chart_df = df.copy()
    chart_df["MonthLabel"] = chart_df["RevenueMonth"].dt.strftime("%b '%y")
    chart_df["MonthTooltip"] = chart_df["RevenueMonth"].dt.strftime("%b %Y")
    chart_order = chart_df["MonthLabel"].tolist()

    base = alt.Chart(chart_df).encode(
        x=alt.X(
            "MonthLabel:N",
            title="",
            sort=chart_order,
            axis=alt.Axis(labelAngle=0, tickSize=0, labelPadding=10),
        )
    )

    order_bars = base.mark_bar(
        color="#dcd9ff",
        cornerRadiusTopLeft=7,
        cornerRadiusTopRight=7,
        opacity=0.95,
        size=34,
    ).encode(
        y=alt.Y(
            "Monthly Orders:Q",
            title="Order Volume",
            axis=alt.Axis(titleColor="#8b90a7", labelColor="#8b90a7", grid=False),
        ),
        tooltip=[
            alt.Tooltip("MonthTooltip:N", title="Month"),
            alt.Tooltip("Monthly Orders:Q", title="Orders", format=","),
            alt.Tooltip("Monthly Revenue:Q", title="Revenue", format=",.0f"),
        ],
    )

    revenue_y = alt.Y(
        "Monthly Revenue:Q",
        title="Revenue",
        axis=alt.Axis(titleColor="#5b54e8", labelColor="#5b54e8", format="$,.0f", grid=True),
    )

    revenue_base = base.encode(y=revenue_y)
    revenue_line = revenue_base.mark_line(color="#5b54e8", strokeWidth=3.5)
    revenue_points = revenue_base.mark_circle(color="#5b54e8", size=85, stroke="white", strokeWidth=1.5)

    note_layer: alt.Chart | None = None
    latest_revenue_month = chart_df["RevenueMonth"].max()
    if data_end_date is not None and data_end_date.to_period("M").to_timestamp() == latest_revenue_month:
        latest_calendar_day = data_end_date.days_in_month
        latest_observed_day = data_end_date.day
        if latest_observed_day < latest_calendar_day:
            note_df = pd.DataFrame(
                [
                    {
                        "Anchor": "center",
                        "Annotation": f"Note: December 2011 is partial data through {data_end_date.strftime('%b')} {latest_observed_day}, {data_end_date.year}.",
                    }
                ]
            )
            note_layer = (
                alt.Chart(note_df)
                .mark_text(
                    align="center",
                    baseline="top",
                    color="#7a5a00",
                    fontSize=12,
                    fontWeight=700,
                    dy=2,
                )
                .encode(
                    x=alt.X(
                        "Anchor:N",
                        sort=["center"],
                        axis=alt.Axis(labels=False, ticks=False, domain=False, title=None),
                    ),
                    text="Annotation:N",
                )
                .properties(height=20)
            )

    main_chart = (
        alt.layer(order_bars, revenue_line, revenue_points)
        .resolve_scale(y="independent")
        .properties(height=330)
    )

    if note_layer is None:
        return (
            main_chart
            .configure_view(stroke=None)
            .configure(background="#fbfbfe")
            .configure_axis(
                domain=False,
                gridColor="#ebeaf5",
                tickColor="#d9ddea",
                labelColor="#8b90a7",
                titleColor="#1b1d29",
            )
        )

    return (
        alt.vconcat(main_chart, note_layer, spacing=0)
        .configure_view(stroke=None)
        .configure(background="#fbfbfe")
        .configure_axis(
            domain=False,
            gridColor="#ebeaf5",
            tickColor="#d9ddea",
            labelColor="#8b90a7",
            titleColor="#1b1d29",
        )
    )


def score_rfm_series(series: pd.Series, higher_is_better: bool) -> pd.Series:
    labels = [1, 2, 3, 4] if higher_is_better else [4, 3, 2, 1]
    ranked = series.rank(method="first")
    return pd.qcut(ranked, 4, labels=labels).astype(int)


@st.cache_data(show_spinner=False)
def build_customer_insight_frames(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    customer_df = df[(df["CustomerID"].notna()) & (~df["IsCancelled"]) & (df["Sales"] > 0)].copy()
    customer_df["CustomerID"] = customer_df["CustomerID"].astype(str)
    customer_df["OrderMonth"] = customer_df["InvoiceDate"].dt.to_period("M").dt.to_timestamp()

    snapshot_date = customer_df["InvoiceDateOnly"].max()
    customer_rfm = (
        customer_df.groupby("CustomerID", as_index=False)
        .agg(
            LastPurchaseDate=("InvoiceDateOnly", "max"),
            Frequency=("InvoiceNo", "nunique"),
            Monetary=("Sales", "sum"),
        )
        .assign(Recency=lambda frame: (snapshot_date - frame["LastPurchaseDate"]).dt.days)
    )
    customer_rfm["RScore"] = score_rfm_series(customer_rfm["Recency"], higher_is_better=False)
    customer_rfm["FScore"] = score_rfm_series(customer_rfm["Frequency"], higher_is_better=True)
    customer_rfm["MScore"] = score_rfm_series(customer_rfm["Monetary"], higher_is_better=True)

    customer_rfm["Segment"] = "Lost"
    customer_rfm.loc[
        (customer_rfm["RScore"] >= 4) & (customer_rfm["FScore"] >= 4) & (customer_rfm["MScore"] >= 4),
        "Segment",
    ] = "Champions"
    customer_rfm.loc[
        (customer_rfm["Segment"] == "Lost")
        & (customer_rfm["RScore"] >= 3)
        & (customer_rfm["FScore"] >= 3)
        & (customer_rfm["MScore"] >= 2),
        "Segment",
    ] = "Loyalists"
    customer_rfm.loc[
        (customer_rfm["Segment"] == "Lost")
        & (customer_rfm["RScore"] <= 2)
        & ((customer_rfm["FScore"] >= 3) | (customer_rfm["MScore"] >= 3)),
        "Segment",
    ] = "At Risk"

    segment_order = ["Champions", "Loyalists", "At Risk", "Lost"]
    rfm_segments = (
        customer_rfm.groupby("Segment", as_index=False)
        .agg(Customers=("CustomerID", "count"), Revenue=("Monetary", "sum"))
        .set_index("Segment")
        .reindex(segment_order, fill_value=0)
        .reset_index()
    )
    total_customers = max(int(rfm_segments["Customers"].sum()), 1)
    rfm_segments["Customer Share"] = rfm_segments["Customers"] / total_customers

    customer_months = (
        customer_df[["CustomerID", "OrderMonth"]]
        .drop_duplicates()
        .sort_values(["CustomerID", "OrderMonth"])
    )
    customer_months["CohortMonth"] = customer_months.groupby("CustomerID")["OrderMonth"].transform("min")
    customer_months["MonthNumber"] = (
        (customer_months["OrderMonth"].dt.year - customer_months["CohortMonth"].dt.year) * 12
        + (customer_months["OrderMonth"].dt.month - customer_months["CohortMonth"].dt.month)
    )

    cohort_size = customer_months.groupby("CohortMonth")["CustomerID"].nunique()
    retention = (
        customer_months.groupby(["CohortMonth", "MonthNumber"], as_index=False)["CustomerID"]
        .nunique()
        .rename(columns={"CustomerID": "Customers"})
    )
    retention["Cohort Size"] = retention["CohortMonth"].map(cohort_size)
    retention["Retention Rate"] = retention["Customers"] / retention["Cohort Size"]
    max_month_number = int(retention["MonthNumber"].max())
    period_range = list(range(max_month_number + 1))
    cohort_range = sorted(retention["CohortMonth"].drop_duplicates().tolist())
    full_retention_grid = pd.MultiIndex.from_product(
        [cohort_range, period_range],
        names=["CohortMonth", "MonthNumber"],
    ).to_frame(index=False)
    retention = full_retention_grid.merge(retention, on=["CohortMonth", "MonthNumber"], how="left")
    retention["Observed"] = retention["Retention Rate"].notna()
    retention["Retention Rate Filled"] = retention["Retention Rate"].fillna(0.0)
    retention["CohortLabel"] = pd.to_datetime(retention["CohortMonth"]).dt.strftime("%b '%y")
    retention["PeriodLabel"] = "Month " + retention["MonthNumber"].astype(str)
    retention["RetentionLabel"] = retention["Retention Rate"].map(lambda value: f"{value:.0%}" if pd.notna(value) else "")

    pareto = (
        customer_rfm[["CustomerID", "Monetary"]]
        .rename(columns={"Monetary": "Revenue"})
        .sort_values("Revenue", ascending=False)
        .reset_index(drop=True)
    )
    pareto["Rank"] = pareto.index + 1
    pareto["Cumulative Revenue %"] = pareto["Revenue"].cumsum() / pareto["Revenue"].sum()
    pareto_chart = pareto.head(60).copy()

    return {
        "rfm_segments": rfm_segments,
        "retention": retention,
        "pareto": pareto_chart,
    }


def compute_treemap_rectangles(values: list[float], x: float = 0.0, y: float = 0.0, width: float = 100.0, height: float = 100.0) -> list[tuple[float, float, float, float]]:
    total = sum(values)
    if total <= 0:
        return [(x, y, width, height) for _ in values]

    rectangles: list[tuple[float, float, float, float]] = []
    remaining_x = x
    remaining_y = y
    remaining_width = width
    remaining_height = height
    remaining_total = total

    for index, value in enumerate(values):
        if index == len(values) - 1 or remaining_total <= 0:
            rectangles.append((remaining_x, remaining_y, remaining_width, remaining_height))
            break

        share = value / remaining_total if remaining_total else 0
        if remaining_width >= remaining_height:
            rect_width = remaining_width * share
            rectangles.append((remaining_x, remaining_y, rect_width, remaining_height))
            remaining_x += rect_width
            remaining_width -= rect_width
        else:
            rect_height = remaining_height * share
            rectangles.append((remaining_x, remaining_y, remaining_width, rect_height))
            remaining_y += rect_height
            remaining_height -= rect_height
        remaining_total -= value

    return rectangles


def render_rfm_treemap_card(title: str, df: pd.DataFrame) -> None:
    colors = {
        "Champions": "linear-gradient(145deg, #5b54e8 0%, #7f7bff 100%)",
        "Loyalists": "linear-gradient(145deg, #6c63ff 0%, #9a92ff 100%)",
        "At Risk": "linear-gradient(145deg, #f0b63f 0%, #ffc93c 100%)",
        "Lost": "linear-gradient(145deg, #8d95b2 0%, #b7bfd8 100%)",
    }
    chart_df = df.sort_values("Customers", ascending=False).reset_index(drop=True)
    rectangles = compute_treemap_rectangles(chart_df["Customers"].astype(float).tolist())

    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)
    tiles: list[str] = []
    for (segment, customers, revenue, share), (left, top, tile_width, tile_height) in zip(
        chart_df[["Segment", "Customers", "Revenue", "Customer Share"]].itertuples(index=False),
        rectangles,
    ):
        tiles.append(
            f"""
            <div class="treemap-tile" style="left:{left:.3f}%; top:{top:.3f}%; width:{tile_width:.3f}%; height:{tile_height:.3f}%; background:{colors[segment]};">
                <div>
                    <div class="treemap-label">{segment}</div>
                    <div class="treemap-value">{int(customers):,}</div>
                </div>
                <div class="treemap-tooltip">
                    <strong>{segment}</strong><br>
                    {share:.1%} of customers<br>
                    Revenue {format_currency(float(revenue))}
                </div>
            </div>
            """
        )

    treemap_html = f"""
    <html>
        <head>
            <style>
                body {{
                    margin: 0;
                    background: transparent;
                    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                }}
                .treemap-board {{
                    position: relative;
                    width: 100%;
                    height: 380px;
                }}
                .treemap-tile {{
                    position: absolute;
                    box-sizing: border-box;
                    border-radius: 22px;
                    padding: 0.85rem 0.95rem;
                    color: #ffffff;
                    display: flex;
                    flex-direction: column;
                    justify-content: space-between;
                    box-shadow: 0 14px 28px rgba(70, 73, 101, 0.10);
                    overflow: hidden;
                }}
                .treemap-label {{
                    font-size: 0.96rem;
                    font-weight: 800;
                    line-height: 1.2;
                }}
                .treemap-value {{
                    font-size: 1.7rem;
                    font-weight: 800;
                    line-height: 1;
                    margin-top: 0.28rem;
                }}
                .treemap-meta {{
                    font-size: 0.82rem;
                    line-height: 1.3;
                    color: rgba(255, 255, 255, 0.86);
                }}
                .treemap-tooltip {{
                    position: absolute;
                    left: 0.75rem;
                    right: 0.75rem;
                    bottom: 0.75rem;
                    background: rgba(21, 24, 39, 0.94);
                    color: #ffffff;
                    border-radius: 14px;
                    padding: 0.65rem 0.75rem;
                    font-size: 0.78rem;
                    line-height: 1.35;
                    opacity: 0;
                    transform: translateY(8px);
                    transition: opacity 0.18s ease, transform 0.18s ease;
                    pointer-events: none;
                    z-index: 4;
                }}
                .treemap-tile:hover .treemap-tooltip {{
                    opacity: 1;
                    transform: translateY(0);
                }}
            </style>
        </head>
        <body>
            <div class="treemap-board">{"".join(tiles)}</div>
        </body>
    </html>
    """
    components.html(treemap_html, height=390, scrolling=False)


def build_cohort_retention_heatmap(df: pd.DataFrame) -> alt.Chart:
    cohort_order = df["CohortLabel"].drop_duplicates().tolist()
    period_order = df["PeriodLabel"].drop_duplicates().tolist()

    base = alt.Chart(df)
    heatmap = base.mark_rect(cornerRadius=6).encode(
        x=alt.X("PeriodLabel:N", title="", sort=period_order, axis=alt.Axis(labelAngle=0, labelPadding=10)),
        y=alt.Y("CohortLabel:N", title="Cohort", sort=cohort_order, axis=alt.Axis(labelPadding=10)),
        color=alt.Color(
            "Retention Rate Filled:Q",
            title="Retention",
            scale=alt.Scale(domain=[0, 1], range=["#f3f4fa", "#6c63ff"]),
            legend=None,
        ),
        opacity=alt.condition(alt.datum.Observed, alt.value(1), alt.value(0.35)),
        tooltip=[
            alt.Tooltip("CohortLabel:N", title="Cohort"),
            alt.Tooltip("PeriodLabel:N", title="Period"),
            alt.Tooltip("Customers:Q", title="Returning Customers", format=","),
            alt.Tooltip("Cohort Size:Q", title="Cohort Size", format=","),
            alt.Tooltip("Retention Rate Filled:Q", title="Retention", format=".1%"),
        ],
    )
    labels = base.mark_text(fontSize=11, fontWeight=700).encode(
        x=alt.X("PeriodLabel:N", sort=period_order),
        y=alt.Y("CohortLabel:N", sort=cohort_order),
        text=alt.Text("RetentionLabel:N"),
        color=alt.condition(alt.datum["Retention Rate Filled"] >= 0.55, alt.value("#ffffff"), alt.value("#52576e")),
    )

    return (
        alt.layer(heatmap, labels)
        .properties(height=360)
        .configure_view(stroke=None)
        .configure(background="#fbfbfe")
        .configure_axis(
            domain=False,
            tickColor="#d9ddea",
            labelColor="#8b90a7",
            titleColor="#1b1d29",
        )
    )


def build_customer_pareto_chart(df: pd.DataFrame) -> alt.Chart:
    rank_values = list(range(1, int(df["Rank"].max()) + 1, 5))
    base = alt.Chart(df).encode(
        x=alt.X(
            "Rank:Q",
            title="Customer Rank by Total Spend",
            axis=alt.Axis(values=rank_values, tickMinStep=1, grid=False),
        )
    )

    bars = base.mark_bar(color="#dcd9ff", size=10).encode(
        y=alt.Y(
            "Revenue:Q",
            title="Revenue",
            axis=alt.Axis(format="$,.0f", grid=True, gridColor="#ebeaf5", titleColor="#8b90a7", labelColor="#8b90a7"),
        ),
        tooltip=[
            alt.Tooltip("CustomerID:N", title="Customer"),
            alt.Tooltip("Rank:Q", title="Rank", format=",d"),
            alt.Tooltip("Revenue:Q", title="Revenue", format="$,.0f"),
            alt.Tooltip("Cumulative Revenue %:Q", title="Cumulative Revenue", format=".1%"),
        ],
    )

    cumulative_y = alt.Y(
        "Cumulative Revenue %:Q",
        title="Cumulative Revenue %",
        axis=alt.Axis(format=".0%", titleColor="#5b54e8", labelColor="#5b54e8", grid=False),
    )
    line_base = base.encode(y=cumulative_y)
    line = line_base.mark_line(color="#5b54e8", strokeWidth=3)
    points = line_base.mark_circle(color="#5b54e8", size=60, stroke="#ffffff", strokeWidth=1.4)

    return (
        alt.layer(bars, line, points)
        .resolve_scale(y="independent")
        .properties(height=330)
        .configure_view(stroke=None)
        .configure(background="#fbfbfe")
        .configure_axis(
            domain=False,
            tickColor="#d9ddea",
            labelColor="#8b90a7",
            titleColor="#1b1d29",
        )
    )


def render_sales_overview(df: pd.DataFrame) -> None:
    overview_df = df[df["CustomerID"].notna()].copy()
    kpis = compute_kpis(overview_df)
    kpi_columns = st.columns(4)

    with kpi_columns[0]:
        render_kpi_card(
            "Total Revenue",
            format_currency(kpis["total_revenue"]),
            "Gross revenue from rows with a valid customer ID",
            get_kpi_icon("revenue"),
        )
    with kpi_columns[1]:
        render_kpi_card(
            "Total Customers",
            format_count(kpis["total_unique_customers"]),
            "Distinct customer IDs with valid sales activity",
            get_kpi_icon("customers"),
        )
    with kpi_columns[2]:
        render_kpi_card(
            "Total Orders",
            format_count(kpis["total_orders"]),
            "Distinct invoice numbers from rows with a valid customer ID",
            get_kpi_icon("orders"),
        )
    with kpi_columns[3]:
        render_kpi_card(
            "Avg Order Value",
            format_currency(kpis["avg_order_value"]),
            "Average revenue generated per distinct order",
            get_kpi_icon("avg_order_value"),
        )

    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    insight_columns = st.columns(2)
    with insight_columns[0]:
        render_insight_banner(
            "Executive Insight",
            "Q4 Demand Spike",
            "Revenue rose <strong>82%</strong> from August (~$564K) to a November peak of ~$1.03M — though the initial Aug→Sep jump (+49%) was driven disproportionately by two large accounts. AOV actually fell once they're excluded."
        )
    with insight_columns[1]:
        render_insight_banner(
            "Executive Insight",
            "International Orders Skew Larger",
            "International markets post AOV of (<strong>$1,200-$2,800</strong>) vs. (<strong>~$432</strong>) domestically, reflecting order size, not margin.",
        )

    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)

    monthly_revenue = (
        overview_df.groupby("InvoiceDateOnly", as_index=False)["Sales"]
        .sum()
        .assign(RevenueMonth=lambda frame: pd.to_datetime(frame["InvoiceDateOnly"]).dt.to_period("M").dt.to_timestamp())
        .groupby("RevenueMonth", as_index=False)["Sales"]
        .sum()
        .rename(columns={"Sales": "Monthly Revenue"})
    )

    monthly_orders = (
        overview_df.assign(RevenueMonth=overview_df["InvoiceDate"].dt.to_period("M").dt.to_timestamp())
        .groupby("RevenueMonth", as_index=False)["InvoiceNo"]
        .nunique()
        .rename(columns={"InvoiceNo": "Monthly Orders"})
    )

    monthly_trend = monthly_revenue.merge(monthly_orders, on="RevenueMonth", how="inner").sort_values("RevenueMonth")
    data_end_date = pd.to_datetime(overview_df["InvoiceDateOnly"]).max()

    country_revenue = (
        overview_df.groupby("Country", as_index=False)["Sales"]
        .sum()
        .sort_values("Sales", ascending=False)
        .rename(columns={"Sales": "Revenue"})
    )
    uk_country_name = "United Kingdom"
    country_focus = st.selectbox(
        "Country comparison mode",
        ["Exclude UK", "Include UK"],
        index=0,
        key="executive_country_focus",
        help="Exclude the UK to make international markets easier to compare.",
    )
    include_uk = country_focus == "Include UK"
    comparison_country_revenue = (
        country_revenue if include_uk else country_revenue[country_revenue["Country"] != uk_country_name]
    )
    top_country_count = 6
    country_sales = comparison_country_revenue.head(top_country_count).copy()
    other_country_count = max(len(comparison_country_revenue) - top_country_count, 0)
    other_revenue = comparison_country_revenue.iloc[top_country_count:]["Revenue"].sum()
    if other_revenue > 0:
        country_sales = pd.concat(
            [
                country_sales,
                pd.DataFrame([{"Country": "Other", "Revenue": other_revenue}]),
            ],
            ignore_index=True,
        )
    country_sales = country_sales.sort_values("Revenue", ascending=False)

    country_order_metrics = (
        overview_df.groupby(["Country", "InvoiceNo"], as_index=False)
        .agg(order_value=("Sales", "sum"))
        .groupby("Country", as_index=False)
        .agg(
            Revenue=("order_value", "sum"),
            **{
                "Total Orders": ("InvoiceNo", "nunique"),
                "Average Order Value": ("order_value", "mean"),
            },
        )
        .sort_values("Revenue", ascending=False)
    )
    comparison_country_order_metrics = (
        country_order_metrics
        if include_uk
        else country_order_metrics[country_order_metrics["Country"] != uk_country_name]
    ).head(20)

    uk_revenue = country_revenue.loc[country_revenue["Country"] == uk_country_name, "Revenue"].sum()
    international_revenue = country_revenue.loc[country_revenue["Country"] != uk_country_name, "Revenue"].sum()
    uk_international_mix = pd.DataFrame(
        [
            {"Segment": "United Kingdom", "Revenue": uk_revenue},
            {"Segment": "International", "Revenue": international_revenue},
        ]
    )

    top_products_by_revenue = (
        overview_df.groupby(["StockCode", "Description"], as_index=False)["Sales"]
        .sum()
        .sort_values("Sales", ascending=False)
        .head(10)
    )
    top_products_by_revenue["Product"] = (
        top_products_by_revenue["StockCode"].astype(str) + " | " + top_products_by_revenue["Description"].astype(str)
    )
    top_products_by_revenue = top_products_by_revenue.rename(columns={"Sales": "Revenue"})

    top_products_by_quantity = (
        overview_df.groupby(["StockCode", "Description"], as_index=False)["Quantity"]
        .sum()
        .sort_values("Quantity", ascending=False)
        .head(10)
    )
    top_products_by_quantity["Product"] = (
        top_products_by_quantity["StockCode"].astype(str) + " | " + top_products_by_quantity["Description"].astype(str)
    )

    top_customers_by_revenue = (
        overview_df.groupby("CustomerID", as_index=False)["Sales"]
        .sum()
        .sort_values("Sales", ascending=False)
        .head(10)
        .rename(columns={"Sales": "Revenue"})
    )
    top_customers_by_revenue["CustomerID"] = top_customers_by_revenue["CustomerID"].astype(str)

    order_metrics = (
        overview_df.groupby("InvoiceNo", as_index=False)
        .agg(
            basket_size=("Quantity", "sum"),
            order_value=("Sales", "sum"),
        )
    )

    render_chart_card(
        "Monthly Revenue & Order Volume Trend",
        build_revenue_orders_combo_chart(monthly_trend, data_end_date=data_end_date),
    )

    sales_mix_columns = st.columns([0.9, 1.1])
    with sales_mix_columns[0]:
        render_chart_card(
            "UK vs. International Revenue Mix",
            build_uk_international_donut(uk_international_mix),
        )
    with sales_mix_columns[1]:
        other_note = (
            f"Other combines the remaining {other_country_count} countries outside the top {top_country_count} by revenue."
            if other_country_count > 0
            else None
        )
        render_chart_card(
            f"Top Countries by Revenue ({country_focus})",
            build_top_countries_chart(country_sales, note_text=other_note),
        )

    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    render_chart_card(
        f"Average Order Value vs. Transaction Volume by Country ({country_focus})",
        build_country_aov_volume_chart(comparison_country_order_metrics),
    )


def render_customer_insights(df: pd.DataFrame) -> None:
    insight_frames = build_customer_insight_frames(df)
    rfm_segments = insight_frames["rfm_segments"]
    retention = insight_frames["retention"]
    pareto = insight_frames["pareto"]

    champions_row = rfm_segments[rfm_segments["Segment"] == "Champions"].iloc[0]
    champion_revenue_share = float(champions_row["Revenue"]) / float(rfm_segments["Revenue"].sum())
    month_one_retention = retention[retention["MonthNumber"] == 1]["Retention Rate"].dropna()
    median_month_one_retention = float(month_one_retention.median()) if not month_one_retention.empty else 0.0
    top_decile_count = max(int(len(pareto) * 0.1), 1)
    top_decile_revenue_share = float(pareto.head(top_decile_count)["Revenue"].sum()) / float(pareto["Revenue"].sum())

    insight_columns = st.columns(1)
    with insight_columns[0]:
        render_insight_banner(
            "Customer Insight",
            "Customer base skews toward disengagement",
            f"Nearly two-thirds of customers (<strong>65%, or 2,835 of 4,304</strong>) fall into Lost or At Risk segments, versus 23% (1,001) who are Loyalists and just 11% (468) who are Champions. Lost customers alone represent $749,422 in historical revenue, a meaningful pool worth a targeted win-back campaign before it's written off entirely.",
        )
   

    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)

    render_rfm_treemap_card(
        "RFM Customer Segment Distribution",
        rfm_segments,
    )
    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    render_insight_banner(
        "Customer Insight",
        "Retention drops sharply after month one",
        "Across nearly every cohort, retention falls from <strong>100%</strong> at purchase to roughly <strong>11-36%</strong> by month one, and continues declining from there. This pattern suggests most customers make a single purchase rather than becoming repeat buyers, making the first <strong>30-60 days</strong> the highest-leverage retention window.",
    )
    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    render_chart_card(
        "Cohort Retention Heatmap",
        build_cohort_retention_heatmap(retention),
    )
    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    render_insight_banner(
        "Customer Insight",
        "Revenue is highly concentrated among top customers",
        "The top <strong>10 customers</strong> — just <strong>0.2%</strong> of the 4,304-customer base — generate <strong>18.2%</strong> of total revenue. Concentration continues but flattens quickly: the top <strong>60 customers</strong> (<strong>1.4%</strong> of the base) account for <strong>36.2%</strong>, meaning each additional customer beyond the first 10 contributes proportionally less. This handful of accounts disproportionately drives the business and warrants dedicated retention or account management focus.",
    )
    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    render_chart_card(
        "Customer Concentration",
        build_customer_pareto_chart(pareto),
    )


def render_country_insights(df: pd.DataFrame) -> None:
    country_df = df[(df["CustomerID"].notna()) & (~df["IsCancelled"]) & (df["Sales"] > 0)].copy()
    uk_country_name = "United Kingdom"
    country_focus = st.selectbox(
        "Country comparison mode",
        ["Exclude UK", "Include UK"],
        index=0,
        key="country_insights_focus",
        help="Exclude the UK to make international country comparisons easier to read.",
    )
    include_uk = country_focus == "Include UK"

    country_orders = (
        country_df.groupby(["Country", "InvoiceNo"], as_index=False)
        .agg(
            OrderRevenue=("Sales", "sum"),
            **{"Invoice Quantity": ("Quantity", "sum")},
        )
    )

    country_metrics = (
        country_orders if include_uk else country_orders[country_orders["Country"] != uk_country_name]
    )
    comparison_country_metrics = (
        country_metrics
        .groupby("Country", as_index=False)
        .agg(
            Revenue=("OrderRevenue", "sum"),
            **{
                "Total Orders": ("InvoiceNo", "nunique"),
                "Average Order Value": ("OrderRevenue", "mean"),
            },
        )
    )

    aov_chart_df = (
        comparison_country_metrics[comparison_country_metrics["Total Orders"] >= 5]
        .sort_values("Average Order Value", ascending=False)
        .head(10)
        .sort_values("Average Order Value", ascending=True)
    )

    top_5_country_order = (
        comparison_country_metrics.sort_values("Revenue", ascending=False)
        .head(5)["Country"]
        .tolist()
    )
    boxplot_df = country_orders[country_orders["Country"].isin(top_5_country_order)].copy()
    top_aov_country = comparison_country_metrics.sort_values("Average Order Value", ascending=False).iloc[0]
    reliable_country_count = int((comparison_country_metrics["Total Orders"] >= 20).sum())
    median_order_quantity = float(boxplot_df["Invoice Quantity"].median()) if not boxplot_df.empty else 0.0
    max_order_quantity = int(boxplot_df["Invoice Quantity"].max()) if not boxplot_df.empty else 0

    insight_columns = st.columns(2)
    with insight_columns[0]:
        render_insight_banner(
            "Country Insight",
            "International Orders Skew Large",
            f"<strong>{top_aov_country['Country']}</strong> posts the highest {'international ' if not include_uk else ''}AOV at about <strong>{format_currency(float(top_aov_country['Average Order Value']))}</strong> per order, reinforcing the wholesale nature of larger market baskets.",
        )
    with insight_columns[1]:
        render_insight_banner(
            "Country Insight",
            "Most Markets Are Thinly Sampled",
            f"Only <strong>{format_count(reliable_country_count)}</strong> of <strong>{format_count(len(comparison_country_metrics))}</strong> {'international ' if not include_uk else ''}markets clear 20 orders, so cross-country comparisons need confidence context alongside the headline AOV figures.",
        )

    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)

    render_chart_card_with_caption(
        f"Average Order Value (AOV) by Country ({country_focus})",
        build_country_aov_bar_chart(aov_chart_df),
        "Lighter bars indicate countries with fewer than 20 orders.",
    )
    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    render_insight_banner(
        "Country Insight",
        "Order sizes are outlier-driven, not typical",
        f"These box plots show the <strong>top 5 countries by revenue</strong> for the current selection. Even here, the median invoice stays under <strong>{format_count(int(round(median_order_quantity)))}</strong> units, while a handful of extreme orders push the upper tail above <strong>{format_count(max_order_quantity)}</strong> units.",
    )
    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    render_chart_card_with_caption(
        f"Order Size Distribution by Country ({country_focus})",
        build_country_order_size_boxplot(boxplot_df, top_5_country_order),
        "Showing the top 5 countries by revenue for the current Country comparison mode.",
    )


def render_product_insights(df: pd.DataFrame) -> None:
    product_df = df[(df["CustomerID"].notna()) & (~df["IsCancelled"]) & (df["Sales"] > 0)].copy()
    product_df = filter_merchandise_rows(product_df)

    product_metrics = (
        product_df.groupby(["StockCode", "Description"], as_index=False)
        .agg(
            Revenue=("Sales", "sum"),
            **{
                "Quantity Sold": ("Quantity", "sum"),
                "Unit Price": ("UnitPrice", "median"),
                "Orders": ("InvoiceNo", "nunique"),
            },
        )
    )
    product_metrics["ProductLabel"] = (
        product_metrics["StockCode"].astype(str) + " | " + product_metrics["Description"].fillna("").astype(str)
    )

    top_10_products = (
        product_metrics.sort_values("Revenue", ascending=False)
        .head(10)
        .sort_values("Revenue", ascending=True)
        .copy()
    )
    top_10_revenue_share = float(top_10_products["Revenue"].sum()) / float(product_metrics["Revenue"].sum())

    velocity_df = product_metrics[product_metrics["Orders"] >= 10].copy()
    velocity_df = velocity_df.sort_values("Revenue", ascending=False).head(120)
    quantity_threshold = float(velocity_df["Quantity Sold"].median()) if not velocity_df.empty else 0.0
    price_threshold = float(velocity_df["Unit Price"].median()) if not velocity_df.empty else 0.0
    velocity_df["Quadrant"] = "Low Volume / Low Price"
    velocity_df.loc[
        (velocity_df["Quantity Sold"] >= quantity_threshold) & (velocity_df["Unit Price"] >= price_threshold),
        "Quadrant",
    ] = "High Volume / High Price"
    velocity_df.loc[
        (velocity_df["Quantity Sold"] >= quantity_threshold) & (velocity_df["Unit Price"] < price_threshold),
        "Quadrant",
    ] = "High Volume / Low Price"
    velocity_df.loc[
        (velocity_df["Quantity Sold"] < quantity_threshold) & (velocity_df["Unit Price"] >= price_threshold),
        "Quadrant",
    ] = "Low Volume / High Price"
    high_volume_high_price_count = int((velocity_df["Quadrant"] == "High Volume / High Price").sum())
    top_product = product_metrics.sort_values("Revenue", ascending=False).iloc[0]

    order_products = (
        product_df.groupby("InvoiceNo")
        .apply(
            lambda frame: sorted(
                set(
                    (
                        frame["StockCode"].astype(str)
                        + " | "
                        + frame["Description"].fillna("").astype(str)
                    ).tolist()
                )
            ),
            include_groups=False,
        )
        .tolist()
    )
    pair_counts: Counter[tuple[str, str]] = Counter()
    item_counts: Counter[str] = Counter()
    for basket in order_products:
        for item in basket:
            item_counts[item] += 1
        for first, second in combinations(basket, 2):
            pair_counts[(first, second)] += 1

    market_basket_rows: list[dict[str, object]] = []
    minimum_primary_orders = 25
    minimum_pair_orders = 10
    for (first, second), pair_order_count in pair_counts.items():
        primary_orders = item_counts[first]
        if primary_orders < minimum_primary_orders or pair_order_count < minimum_pair_orders:
            continue
        attach_rate = pair_order_count / primary_orders if primary_orders else 0.0
        market_basket_rows.append(
            {
                "Primary Product": first,
                "Secondary Product": second,
                "Pair Orders": pair_order_count,
                "Primary Orders": primary_orders,
                "Attach Rate": attach_rate,
                "PairLabel": f"{first}  +  {second}",
            }
        )
    market_basket_df = (
        pd.DataFrame(market_basket_rows)
        .sort_values(["Attach Rate", "Pair Orders"], ascending=[False, False])
        .head(5)
        .sort_values("Attach Rate", ascending=True)
    )
    low_support_pair_count = int((market_basket_df["Pair Orders"] < 30).sum()) if not market_basket_df.empty else 0
    has_poppy_playhouse_pair = (
        market_basket_df["PairLabel"].str.contains("POPPY'S PLAYHOUSE", na=False).any()
        if not market_basket_df.empty
        else False
    )

    insight_columns = st.columns(2)
    with insight_columns[0]:
        render_insight_banner(
            "Product Insight",
            "Revenue Is Broad, Not Single-SKU Led",
            f"After removing shipping and manual adjustment codes from the product model, the top 10 products contribute about <strong>{top_10_revenue_share:.1%}</strong> of merchandise revenue, so performance is spread across a wide catalog rather than concentrated in one hero SKU.",
        )
    with insight_columns[1]:
        render_insight_banner(
            "Product Insight",
            "Premium Fast Movers Matter",
            f"<strong>{format_count(high_volume_high_price_count)}</strong> SKUs land in the high-volume/high-price quadrant, led by <strong>{str(top_product['StockCode'])}</strong>, showing that premium items still scale when they hit repeat wholesale demand.",
        )

    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)

    render_chart_card(
        "Top 10 Products by Revenue & Quantity Sold",
        build_product_revenue_quantity_combo_chart(top_10_products),
    )
    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    render_insight_banner(
        "Product Insight",
        "Low-price items drive the bulk of volume",
        "The majority of SKUs cluster below <strong>$10</strong> unit price, and this band accounts for the highest transaction volume on the tab. This is typical of a mixed catalog: a broad base of low-cost, frequently repurchased items alongside a smaller set of premium, less-frequent purchases.",
    )
    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    render_chart_card(
        "SKU Velocity",
        build_sku_velocity_chart(velocity_df, quantity_threshold, price_threshold),
    )
    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    render_insight_banner(
        "Product Insight",
        "Association strength needs support context",
        (
            f"<strong>{format_count(low_support_pair_count)}</strong> of the top 5 attach-rate pairs are based on fewer than <strong>30</strong> shared invoices, so they should be read as directional rather than definitive. "
            + (
                "The POPPY'S PLAYHOUSE pairs are also companion room-themed SKUs, so their high association likely reflects bundled or near-duplicate set buying rather than a pure cross-sell signal."
                if has_poppy_playhouse_pair
                else "High attach rates can also reflect companion or bundle-oriented SKUs rather than standalone cross-sell behavior."
            )
        ),
    )
    st.markdown('<div class="section-spacer"></div>', unsafe_allow_html=True)
    render_chart_card(
        "Market Basket Association",
        build_market_basket_chart(market_basket_df),
    )

def render_placeholder_tab(title: str, message: str) -> None:
    st.markdown(
        f"""
        <div class="section-card">
            <div class="section-title">{title}</div>
            <div class="placeholder-copy">{message}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    inject_styles()

    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-brand">
                <div class="sidebar-brand-mark"></div>
                <div class="sidebar-brand-copy"><small></small>UCI Online Retail Analysis</div>
            </div>
            <div class="sidebar-section-label">General</div>
            """,
            unsafe_allow_html=True,
        )
        selected_view = st.radio(
            "Navigation",
            [
                "Executive Overview",
                "Customer Insights",
                "Product Insights",
                "Country Insights",
            ],
            label_visibility="collapsed",
        )
        st.markdown(
            """
            
            """,
            unsafe_allow_html=True,
        )

    render_header()

    sales_df = load_sales_data()

    if selected_view == "Executive Overview":
        render_sales_overview(sales_df)
    elif selected_view == "Customer Insights":
        render_customer_insights(sales_df)
    elif selected_view == "Product Insights":
        render_product_insights(sales_df)
    else:
        render_country_insights(sales_df)


if __name__ == "__main__":
    main()
