import argparse
import json
from pathlib import Path
import sqlite3


DATABASE_PATH = Path(__file__).resolve().parents[1] / "data" / "orders.db"


def get_order(order_id: int) -> dict | None:
    sql = """
        SELECT
            orders.id,
            customers.name AS customer_name,
            orders.order_date,
            orders.status,
            orders.total_amount
        FROM orders
        JOIN customers ON orders.customer_id = customers.id
        WHERE orders.id = ?
    """

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    row = connection.execute(sql, (order_id,)).fetchone()
    connection.close()

    return dict(row) if row else None


def get_order_items(order_id: int) -> list[dict]:
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

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    rows = connection.execute(sql, (order_id,)).fetchall()
    connection.close()

    return [dict(row) for row in rows]


def main() -> None:
    parser = argparse.ArgumentParser(description="Get the line items for one order.")
    parser.add_argument("order_id", type=int)
    args = parser.parse_args()

    order = get_order(args.order_id)
    if order is None:
        raise SystemExit(f"Order {args.order_id} was not found.")

    print(json.dumps({"order": order, "items": get_order_items(args.order_id)}, indent=2))


if __name__ == "__main__":
    main()
