import argparse
import json
from pathlib import Path
import sqlite3


DATABASE_PATH = Path(__file__).resolve().parents[1] / "data" / "orders.db"


def replace_order(order_id: int) -> dict | None:
    order = {
        "customer_id": 1,
        "order_date": "2026-05-07",
        "status": "open",
        "items": [
            {
                "product_name": "Revised Analytics Dashboard License",
                "quantity": 3,
                "unit_price": 500.00,
            },
            {
                "product_name": "Implementation Support",
                "quantity": 2,
                "unit_price": 280.50,
            },
        ],
    }
    total_amount = sum(
        item["quantity"] * item["unit_price"]
        for item in order["items"]
    )

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    cursor = connection.execute(
        """
            UPDATE orders
            SET customer_id = ?, order_date = ?, status = ?, total_amount = ?
            WHERE id = ?
        """,
        (
            order["customer_id"],
            order["order_date"],
            order["status"],
            total_amount,
            order_id,
        ),
    )
    if cursor.rowcount == 0:
        connection.close()
        return None

    connection.execute("DELETE FROM order_items WHERE order_id = ?", (order_id,))
    connection.executemany(
        """
            INSERT INTO order_items (order_id, product_name, quantity, unit_price)
            VALUES (?, ?, ?, ?)
        """,
        [
            (
                order_id,
                item["product_name"],
                item["quantity"],
                item["unit_price"],
            )
            for item in order["items"]
        ],
    )

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
    parser = argparse.ArgumentParser(description="Replace an order with a full payload.")
    parser.add_argument("order_id", type=int)
    args = parser.parse_args()

    order = replace_order(args.order_id)
    if order is None:
        raise SystemExit(f"Order {args.order_id} was not found.")

    print(json.dumps(order, indent=2))


if __name__ == "__main__":
    main()
