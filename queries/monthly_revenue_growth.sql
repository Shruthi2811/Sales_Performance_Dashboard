WITH monthly_revenue AS (
    SELECT
        InvoiceMonth,
        ROUND(SUM(Sales), 2) AS monthly_revenue
    FROM analysis_ready_sales
    WHERE IsCancelled = FALSE
    GROUP BY InvoiceMonth
),
monthly_growth AS (
    SELECT
        InvoiceMonth,
        monthly_revenue,
        LAG(monthly_revenue) OVER (ORDER BY InvoiceMonth) AS previous_month_revenue
    FROM monthly_revenue
)
SELECT
    InvoiceMonth,
    monthly_revenue,
    previous_month_revenue,
    ROUND(
        100.0 * (monthly_revenue - previous_month_revenue) / previous_month_revenue,
        2
    ) AS monthly_revenue_growth_pct
FROM monthly_growth
ORDER BY InvoiceMonth;