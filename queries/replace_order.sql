UPDATE orders
SET customer_id = ?, order_date = ?, status = ?, total_amount = ?
WHERE id = ?;

DELETE FROM order_items WHERE order_id = ?;

INSERT INTO order_items (order_id, product_name, quantity, unit_price)
VALUES (?, ?, ?, ?);

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
