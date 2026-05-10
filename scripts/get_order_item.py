import argparse
import json
from pathlib import Path
import sqlite3


DATABASE_PATH = Path(__file__).resolve().parents[1] / "data" / "orders.db"


def get_order_item(item_id: int) -> dict | None:
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

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    row = connection.execute(sql, (item_id,)).fetchone()
    connection.close()

    return dict(row) if row else None


def main() -> None:
    parser = argparse.ArgumentParser(description="Get one order item by ID.")
    parser.add_argument("item_id", type=int)
    args = parser.parse_args()

    item = get_order_item(args.item_id)
    if item is None:
        raise SystemExit(f"Order item {args.item_id} was not found.")

    print(json.dumps(item, indent=2))


if __name__ == "__main__":
    main()
