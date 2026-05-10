import json
from pathlib import Path
import sqlite3


DATABASE_PATH = Path(__file__).resolve().parents[1] / "data" / "orders.db"


def customer_spend() -> list[dict]:
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

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    rows = connection.execute(sql).fetchall()
    connection.close()

    return [dict(row) for row in rows]


def main() -> None:
    print(json.dumps(customer_spend(), indent=2))


if __name__ == "__main__":
    main()
