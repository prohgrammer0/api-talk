SELECT
    customers.id AS customer_id,
    customers.name AS customer_name,
    customers.segment,
    customers.region,
    COUNT(orders.id) AS order_count,
    ROUND(SUM(orders.total_amount), 2) AS total_spend
FROM customers
JOIN orders ON customers.id = orders.customer_id
WHERE orders.status != 'cancelled'
GROUP BY customers.id, customers.name, customers.segment, customers.region
ORDER BY total_spend DESC;
