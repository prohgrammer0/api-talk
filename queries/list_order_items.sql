SELECT
    order_items.id,
    order_items.order_id,
    customers.name AS customer_name,
    order_items.product_name,
    order_items.quantity,
    order_items.unit_price,
    order_items.quantity * order_items.unit_price AS line_total
FROM order_items
JOIN orders ON order_items.order_id = orders.id
JOIN customers ON orders.customer_id = customers.id
ORDER BY order_items.order_id, order_items.id;
