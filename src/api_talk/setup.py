from pathlib import Path

from api_talk.db import DATABASE_PATH, SCHEMA_PATH, SEED_PATH, connect


def seed_database(db_path: Path = DATABASE_PATH) -> Path:
    db_path.parent.mkdir(parents=True, exist_ok=True)

    schema_sql = SCHEMA_PATH.read_text()
    seed_sql = SEED_PATH.read_text()

    with connect(db_path) as connection:
        connection.executescript(schema_sql)
        connection.executescript(seed_sql)
        connection.commit()

    return db_path


def main() -> None:
    db_path = seed_database()
    print(f"Seeded database: {db_path}")


if __name__ == "__main__":
    main()
