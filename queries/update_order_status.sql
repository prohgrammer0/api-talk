UPDATE orders SET status = ? WHERE id = ?;

SELECT
    orders.id,
    customers.name AS customer_name,
    customers.segment AS customer_segment,
    customers.region AS customer_region,
    orders.order_date,
    orders.status,
    orders.total_amount
FROM orders
JOIN customers ON orders.customer_id = customers.id
WHERE orders.id = ?;
