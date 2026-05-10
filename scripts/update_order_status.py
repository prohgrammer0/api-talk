import argparse
import json
from pathlib import Path
import sqlite3


DATABASE_PATH = Path(__file__).resolve().parents[1] / "data" / "orders.db"


def update_order_status(order_id: int, status: str) -> dict | None:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row

    cursor = connection.execute(
        """
            UPDATE orders
            SET status = ?
            WHERE id = ?
        """,
        (status, order_id),
    )
    if cursor.rowcount == 0:
        connection.close()
        return None

    row = connection.execute(
        """
            SELECT
                orders.id,
                customers.name AS customer_name,
                orders.order_date,
                orders.status,
                orders.total_amount
            FROM orders
            JOIN customers ON orders.customer_id = customers.id
            WHERE orders.id = ?
        """,
        (order_id,),
    ).fetchone()

    connection.commit()
    connection.close()

    return dict(row)


def main() -> None:
    parser = argparse.ArgumentParser(description="Update just the status of an order.")
    parser.add_argument("order_id", type=int)
    parser.add_argument("status", choices=["open", "shipped", "cancelled"])
    args = parser.parse_args()

    order = update_order_status(args.order_id, args.status)
    if order is None:
        raise SystemExit(f"Order {args.order_id} was not found.")

    print(json.dumps(order, indent=2))


if __name__ == "__main__":
    main()
