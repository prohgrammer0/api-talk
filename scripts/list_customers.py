import json
from pathlib import Path
import sqlite3


DATABASE_PATH = Path(__file__).resolve().parents[1] / "data" / "orders.db"


def list_customers() -> list[dict]:
    sql = """
        SELECT
            customers.id,
            customers.name,
            customers.segment,
            customers.region
        FROM customers
        ORDER BY customers.name
    """

    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    rows = connection.execute(sql).fetchall()
    connection.close()

    return [dict(row) for row in rows]


def main() -> None:
    print(json.dumps(list_customers(), indent=2))


if __name__ == "__main__":
    main()
