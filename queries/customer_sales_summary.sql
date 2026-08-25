SELECT
    CustomerID,
    ROUND(SUM(Sales), 2) AS total_revenue,
    COUNT(DISTINCT InvoiceNo) AS total_orders,
    SUM(Quantity) AS total_units_sold,
    ROUND(SUM(Sales) / COUNT(DISTINCT InvoiceNo), 2) AS average_order_value,
    MIN(InvoiceDate) AS first_order_date,
    MAX(InvoiceDate) AS last_order_date
FROM analysis_ready_sales
WHERE IsCancelled = FALSE
  AND CustomerID IS NOT NULL
GROUP BY CustomerID
ORDER BY total_revenue DESC, CustomerID;
