import json
from pathlib import Path
import sqlite3


DATABASE_PATH = Path(__file__).resolve().parents[1] / "data" / "orders.db"


def create_order() -> dict:
    order = {
        "customer_id": 2,
        "order_date": "2026-05-06",
        "status": "open",
        "items": [
            {
                "product_name": "API Integration Workshop",
                "quantity": 1,
                "unit_price": 1200.00,
            },
            {
                "product_name": "Support Retainer",
                "quantity": 2,
                "unit_price": 350.00,
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
            INSERT INTO orders (customer_id, order_date, status, total_amount)
            VALUES (?, ?, ?, ?)
        """,
        (order["customer_id"], order["order_date"], order["status"], total_amount),
    )
    order_id = cursor.lastrowid

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
    print(json.dumps(create_order(), indent=2))


if __name__ == "__main__":
    main()
