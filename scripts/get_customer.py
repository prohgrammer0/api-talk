import argparse
import json
from pathlib import Path
import sqlite3


DATABASE_PATH = Path(__file__).resolve().parents[1] / "data" / "orders.db"


def get_customer(customer_id: int) -> dict | None:
    sql = """
        SELECT
            customers.id,
            customers.name,
            customers.segment,
            customers.region
        FROM customers
        WHERE customers.id = ?
    """

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    row = connection.execute(sql, (customer_id,)).fetchone()
    connection.close()

    return dict(row) if row else None


def main() -> None:
    parser = argparse.ArgumentParser(description="Get one customer by ID.")
    parser.add_argument("customer_id", type=int)
    args = parser.parse_args()

    customer = get_customer(args.customer_id)
    if customer is None:
        raise SystemExit(f"Customer {args.customer_id} was not found.")

    print(json.dumps(customer, indent=2))


if __name__ == "__main__":
    main()
