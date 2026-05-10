SELECT
    orders.id,
    customers.name AS customer_name,
    orders.order_date,
    orders.status,
    orders.total_amount
FROM orders
JOIN customers ON orders.customer_id = customers.id
WHERE orders.status = ?
ORDER BY orders.order_date, orders.id;
