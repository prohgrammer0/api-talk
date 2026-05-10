SELECT
    order_items.product_name,
    order_items.quantity,
    order_items.unit_price,
    order_items.quantity * order_items.unit_price AS line_total
FROM order_items
WHERE order_items.order_id = ?
ORDER BY order_items.id;
