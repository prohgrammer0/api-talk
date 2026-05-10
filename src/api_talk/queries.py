from pathlib import Path

from api_talk.db import DATABASE_PATH, connect, row_to_dict

VALID_STATUSES = {"open", "shipped", "cancelled"}


def list_customers(db_path: Path = DATABASE_PATH) -> list[dict]:
    sql = """
        SELECT
            customers.id,
            customers.name,
            customers.segment,
            customers.region
        FROM customers
        ORDER BY customers.name
    """
    with connect(db_path) as connection:
        rows = connection.execute(sql).fetchall()
    return [row_to_dict(row) for row in rows]


def get_customer(customer_id: int, db_path: Path = DATABASE_PATH) -> dict | None:
    sql = """
        SELECT
            customers.id,
            customers.name,
            customers.segment,
            customers.region
        FROM customers
        WHERE customers.id = ?
    """
    with connect(db_path) as connection:
        row = connection.execute(sql, (customer_id,)).fetchone()
    return row_to_dict(row) if row else None


def get_order(order_id: int, db_path: Path = DATABASE_PATH) -> dict | None:
    sql = """
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
        WHERE orders.id = ?
    """
    with connect(db_path) as connection:
        row = connection.execute(sql, (order_id,)).fetchone()
    return row_to_dict(row) if row else None


def list_orders(status: str | None = None, db_path: Path = DATABASE_PATH) -> list[dict]:
    if status:
        sql = """
            SELECT
                orders.id,
                customers.name AS customer_name,
                orders.order_date,
                orders.status,
                orders.total_amount
            FROM orders
            JOIN customers ON orders.customer_id = customers.id
            WHERE orders.status = ?
            ORDER BY orders.order_date, orders.id
        """
        parameters = (status,)
    else:
        sql = """
            SELECT
                orders.id,
                customers.name AS customer_name,
                orders.order_date,
                orders.status,
                orders.total_amount
            FROM orders
            JOIN customers ON orders.customer_id = customers.id
            ORDER BY orders.order_date, orders.id
        """
        parameters = ()

    with connect(db_path) as connection:
        rows = connection.execute(sql, parameters).fetchall()
    return [row_to_dict(row) for row in rows]


def list_order_items(
    order_id: int | None = None,
    db_path: Path = DATABASE_PATH,
) -> list[dict]:
    if order_id is None:
        sql = """
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
            ORDER BY order_items.order_id, order_items.id
        """
        parameters = ()
    else:
        sql = """
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
            WHERE order_items.order_id = ?
            ORDER BY order_items.id
        """
        parameters = (order_id,)

    with connect(db_path) as connection:
        rows = connection.execute(sql, parameters).fetchall()
    return [row_to_dict(row) for row in rows]


def get_order_item(item_id: int, db_path: Path = DATABASE_PATH) -> dict | None:
    sql = """
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
        WHERE order_items.id = ?
    """
    with connect(db_path) as connection:
        row = connection.execute(sql, (item_id,)).fetchone()
    return row_to_dict(row) if row else None


def get_order_items(order_id: int, db_path: Path = DATABASE_PATH) -> list[dict]:
    sql = """
        SELECT
            order_items.product_name,
            order_items.quantity,
            order_items.unit_price,
            order_items.quantity * order_items.unit_price AS line_total
        FROM order_items
        WHERE order_items.order_id = ?
        ORDER BY order_items.id
    """
    with connect(db_path) as connection:
        rows = connection.execute(sql, (order_id,)).fetchall()
    return [row_to_dict(row) for row in rows]


def create_order(
    customer_id: int,
    order_date: str,
    status: str,
    items: list[dict],
    db_path: Path = DATABASE_PATH,
) -> dict:
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status: {status}")
    if not items:
        raise ValueError("An order must have at least one item.")

    total_amount = _calculate_total(items)

    with connect(db_path) as connection:
        cursor = connection.execute(
            """
                INSERT INTO orders (customer_id, order_date, status, total_amount)
                VALUES (?, ?, ?, ?)
            """,
            (customer_id, order_date, status, total_amount),
        )
        order_id = cursor.lastrowid
        _insert_order_items(connection, order_id, items)
        connection.commit()

    order = get_order(order_id, db_path)
    if order is None:
        raise RuntimeError("Order was created but could not be read back.")
    return order


def replace_order(
    order_id: int,
    customer_id: int,
    order_date: str,
    status: str,
    items: list[dict],
    db_path: Path = DATABASE_PATH,
) -> dict | None:
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status: {status}")
    if not items:
        raise ValueError("An order must have at least one item.")

    total_amount = _calculate_total(items)

    with connect(db_path) as connection:
        cursor = connection.execute(
            """
                UPDATE orders
                SET customer_id = ?, order_date = ?, status = ?, total_amount = ?
                WHERE id = ?
            """,
            (customer_id, order_date, status, total_amount, order_id),
        )
        if cursor.rowcount == 0:
            return None

        connection.execute("DELETE FROM order_items WHERE order_id = ?", (order_id,))
        _insert_order_items(connection, order_id, items)
        connection.commit()

    return get_order(order_id, db_path)


def update_order_status(
    order_id: int,
    status: str,
    db_path: Path = DATABASE_PATH,
) -> dict | None:
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status: {status}")

    with connect(db_path) as connection:
        cursor = connection.execute(
            "UPDATE orders SET status = ? WHERE id = ?",
            (status, order_id),
        )
        if cursor.rowcount == 0:
            return None
        connection.commit()

    return get_order(order_id, db_path)


def delete_order(order_id: int, db_path: Path = DATABASE_PATH) -> bool:
    with connect(db_path) as connection:
        connection.execute("DELETE FROM order_items WHERE order_id = ?", (order_id,))
        cursor = connection.execute("DELETE FROM orders WHERE id = ?", (order_id,))
        connection.commit()
    return cursor.rowcount > 0


def customer_spend(db_path: Path = DATABASE_PATH) -> list[dict]:
    sql = """
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
        ORDER BY total_spend DESC
    """
    with connect(db_path) as connection:
        rows = connection.execute(sql).fetchall()
    return [row_to_dict(row) for row in rows]


def _calculate_total(items: list[dict]) -> float:
    total = 0.0
    for item in items:
        quantity = int(item["quantity"])
        unit_price = float(item["unit_price"])
        if quantity <= 0:
            raise ValueError("Item quantity must be greater than zero.")
        if unit_price < 0:
            raise ValueError("Item unit_price must be zero or greater.")
        total += quantity * unit_price
    return round(total, 2)


def _insert_order_items(connection, order_id: int, items: list[dict]) -> None:
    connection.executemany(
        """
            INSERT INTO order_items (order_id, product_name, quantity, unit_price)
            VALUES (?, ?, ?, ?)
        """,
        [
            (
                order_id,
                item["product_name"],
                int(item["quantity"]),
                float(item["unit_price"]),
            )
            for item in items
        ],
    )
