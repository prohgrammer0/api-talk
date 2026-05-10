import argparse
import json
from pathlib import Path
import sqlite3


DATABASE_PATH = Path(__file__).resolve().parents[1] / "data" / "orders.db"


def list_order_items(order_id: int | None = None) -> list[dict]:
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

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    rows = connection.execute(sql, parameters).fetchall()
    connection.close()

    return [dict(row) for row in rows]


def main() -> None:
    parser = argparse.ArgumentParser(
        description="List order items, optionally filtered by order ID."
    )
    parser.add_argument("--order-id", type=int)
    args = parser.parse_args()

    print(json.dumps(list_order_items(order_id=args.order_id), indent=2))


if __name__ == "__main__":
    main()
