-- Payment totals are recorded payments, not recognized revenue.
-- Exclude or separately analyze cancelled/unavailable orders for sales reporting.

-- Monthly order volume
SELECT
    DATE_TRUNC('month', order_purchase_timestamp) AS month,
    COUNT(*) AS total_orders
FROM analytics.order_summary
GROUP BY 1
ORDER BY 1;

-- Average recorded payment by order status
SELECT
    order_status,
    COUNT(*) AS total_orders,
    ROUND(AVG(payment_total)::numeric, 2) AS average_recorded_payment
FROM analytics.order_summary
WHERE payment_total IS NOT NULL
GROUP BY order_status
ORDER BY total_orders DESC;

-- Repeat-customer purchasing behavior
SELECT
    customer_unique_id,
    COUNT(DISTINCT order_id) AS total_orders,
    ROUND(SUM(payment_total)::numeric, 2) AS recorded_payment_total
FROM analytics.order_summary
WHERE customer_unique_id IS NOT NULL
GROUP BY customer_unique_id
HAVING COUNT(DISTINCT order_id) > 1
ORDER BY recorded_payment_total DESC
LIMIT 20;
