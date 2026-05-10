SELECT
    customers.id,
    customers.name,
    customers.segment,
    customers.region
FROM customers
WHERE customers.id = ?;
