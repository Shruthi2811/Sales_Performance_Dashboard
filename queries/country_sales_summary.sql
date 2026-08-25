SELECT
    Country,
    ROUND(SUM(Sales), 2) AS total_revenue,
    COUNT(DISTINCT InvoiceNo) AS total_orders,
    SUM(Quantity) AS total_units_sold,
    COUNT(DISTINCT CustomerID) AS unique_customers,
    ROUND(SUM(Sales) / COUNT(DISTINCT InvoiceNo), 2) AS average_order_value,
    ROUND(SUM(Sales) / COUNT(DISTINCT CustomerID), 2) AS revenue_per_customer
FROM analysis_ready_sales
WHERE IsCancelled = FALSE
GROUP BY Country
ORDER BY total_revenue DESC, Country;
