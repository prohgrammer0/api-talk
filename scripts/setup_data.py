from pathlib import Path
import sqlite3


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
DATABASE_PATH = DATA_DIR / "orders.db"
SCHEMA_PATH = DATA_DIR / "schema.sql"
SEED_PATH = DATA_DIR / "seed.sql"


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    schema_sql = SCHEMA_PATH.read_text()
    seed_sql = SEED_PATH.read_text()

    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(schema_sql)
        connection.executescript(seed_sql)
        connection.commit()

    print(f"Seeded database: {DATABASE_PATH}")


if __name__ == "__main__":
    main()
