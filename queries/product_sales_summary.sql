SELECT
    StockCode,
    Description,
    ROUND(SUM(Sales), 2) AS total_revenue,
    SUM(Quantity) AS total_units_sold,
    COUNT(DISTINCT InvoiceNo) AS total_orders,
    COUNT(DISTINCT CustomerID) AS unique_customers,
    ROUND(AVG(UnitPrice), 2) AS average_unit_price
FROM analysis_ready_sales
WHERE IsCancelled = FALSE
GROUP BY StockCode, Description
ORDER BY total_revenue DESC, total_units_sold DESC, StockCode;
