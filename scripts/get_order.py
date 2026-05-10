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
            customers.segment AS customer_segment,
            customers.region AS customer_region,
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


def main() -> None:
    parser = argparse.ArgumentParser(description="Get one order by ID.")
    parser.add_argument("order_id", type=int)
    args = parser.parse_args()

    order = get_order(args.order_id)
    if order is None:
        raise SystemExit(f"Order {args.order_id} was not found.")

    print(json.dumps(order, indent=2))


if __name__ == "__main__":
    main()
