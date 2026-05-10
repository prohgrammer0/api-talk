import argparse
from pathlib import Path
import sqlite3


DATABASE_PATH = Path(__file__).resolve().parents[1] / "data" / "orders.db"


def delete_order(order_id: int) -> bool:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute("DELETE FROM order_items WHERE order_id = ?", (order_id,))
    cursor = connection.execute("DELETE FROM orders WHERE id = ?", (order_id,))
    connection.commit()
    connection.close()

    return cursor.rowcount > 0


def main() -> None:
    parser = argparse.ArgumentParser(description="Delete an order from the demo database.")
    parser.add_argument("order_id", type=int)
    args = parser.parse_args()

    deleted = delete_order(args.order_id)
    if not deleted:
        raise SystemExit(f"Order {args.order_id} was not found.")

    print(f"Deleted order {args.order_id}.")


if __name__ == "__main__":
    main()
