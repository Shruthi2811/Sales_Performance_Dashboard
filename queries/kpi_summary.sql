-- KPI summary for the DuckDB table created from data/processed/analysis_ready_sales.csv
-- Table name: analysis_ready_sales
--
-- Note:
-- analysis_ready_sales already excludes cancelled invoices, non-positive quantities,
-- and non-positive prices. Because of that, cancellation_rate cannot be calculated
-- from this table alone. It is returned as NULL below.

WITH customer_order_counts AS (
    SELECT
        CustomerID,
        COUNT(DISTINCT InvoiceNo) AS order_count
    FROM analysis_ready_sales
    WHERE CustomerID IS NOT NULL
    GROUP BY CustomerID
)
SELECT
    SUM(Sales) AS total_revenue,
    COUNT(DISTINCT InvoiceNo) AS total_orders,
    SUM(Quantity) AS total_units_sold,
    COUNT(DISTINCT a.CustomerID) AS unique_customers,
    SUM(Sales) / COUNT(DISTINCT InvoiceNo) AS average_order_value,
    SUM(Sales) / COUNT(DISTINCT a.CustomerID) AS revenue_per_customer,
    NULL AS cancellation_rate,
    COUNT(DISTINCT CASE WHEN c.order_count > 1 THEN a.CustomerID END) * 1.0
        / COUNT(DISTINCT a.CustomerID) AS repeat_customer_rate
FROM analysis_ready_sales AS a
LEFT JOIN customer_order_counts AS c
    ON a.CustomerID = c.CustomerID;
