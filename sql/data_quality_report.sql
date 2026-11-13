
SELECT
    COUNT(*) AS total_orders,

    COUNT(DISTINCT order_id) AS unique_orders,

    COUNT(*) FILTER (
        WHERE item_count = 0
    ) AS orders_without_items,

    COUNT(*) FILTER (
        WHERE payment_count = 0
    ) AS orders_without_payments,

    COUNT(*) FILTER (
        WHERE order_status = 'delivered'
        AND payment_count = 0
    ) AS delivered_without_payment,

    COUNT(*) FILTER (
        WHERE customer_id IS NULL
    ) AS orders_without_customer_id

FROM analytics.order_summary;


-- Investigate orders without items

SELECT
    order_status,
    COUNT(*) AS affected_orders

FROM analytics.order_summary

WHERE item_count = 0

GROUP BY order_status

ORDER BY affected_orders DESC;
