import argparse
import json
from pathlib import Path
import sqlite3


DATABASE_PATH = Path(__file__).resolve().parents[1] / "data" / "orders.db"


def list_orders(status: str | None = None) -> list[dict]:
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

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    rows = connection.execute(sql, parameters).fetchall()
    connection.close()

    return [dict(row) for row in rows]


def main() -> None:
    parser = argparse.ArgumentParser(description="List orders, optionally by status.")
    parser.add_argument("--status", choices=["open", "shipped", "cancelled"])
    args = parser.parse_args()

    print(json.dumps(list_orders(status=args.status), indent=2))


if __name__ == "__main__":
    main()
