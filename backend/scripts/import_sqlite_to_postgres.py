import argparse
import json
import os
import sqlite3
import sys
from typing import Any

import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_batch

TABLES = ["tournament", "playerresult", "match"]
JSON_LIKE_COLUMNS = {
    "tournament": {"location"},
    "playerresult": {"list_json"},
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Copy data from a SQLite DB into PostgreSQL (dev)."
    )
    parser.add_argument(
        "--sqlite-path",
        default="test_absoute.db",
        help="Path to SQLite source DB. Default: test_absoute.db",
    )
    parser.add_argument(
        "--postgres-url",
        default=os.getenv("DATABASE_URL", ""),
        help="PostgreSQL connection URL. Falls back to DATABASE_URL env.",
    )
    parser.add_argument(
        "--skip-truncate",
        action="store_true",
        help="Do not truncate target tables before insert.",
    )
    return parser.parse_args()


def load_rows(conn: sqlite3.Connection, table_name: str) -> tuple[list[str], list[sqlite3.Row]]:
    cursor = conn.execute(f'SELECT * FROM "{table_name}"')
    rows = cursor.fetchall()
    columns = [desc[0] for desc in cursor.description]
    return columns, rows


def normalize_value(table_name: str, column_name: str, value: Any) -> Any:
    if value is None:
        return None

    if (
        table_name in JSON_LIKE_COLUMNS
        and column_name in JSON_LIKE_COLUMNS[table_name]
        and isinstance(value, str)
    ):
        try:
            return json.loads(value)
        except Exception:
            return value

    return value


def main() -> int:
    args = parse_args()

    if not args.postgres_url:
        print("ERROR: missing --postgres-url and DATABASE_URL is not set.")
        return 2

    if not os.path.exists(args.sqlite_path):
        print(f"ERROR: SQLite file not found: {args.sqlite_path}")
        return 2

    sqlite_conn = sqlite3.connect(args.sqlite_path)
    sqlite_conn.row_factory = sqlite3.Row

    pg_conn = psycopg2.connect(args.postgres_url)
    pg_conn.autocommit = False

    try:
        with pg_conn.cursor() as cur:
            for table_name in TABLES:
                columns, rows = load_rows(sqlite_conn, table_name)

                if not args.skip_truncate:
                    cur.execute(sql.SQL("TRUNCATE TABLE {} RESTART IDENTITY CASCADE").format(sql.Identifier(table_name)))

                if not rows:
                    print(f"{table_name}: 0 rows")
                    continue

                tuples = []
                for row in rows:
                    tuples.append(
                        tuple(normalize_value(table_name, col, row[col]) for col in columns)
                    )

                insert_query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                    sql.Identifier(table_name),
                    sql.SQL(", ").join(sql.Identifier(c) for c in columns),
                    sql.SQL(", ").join(sql.Placeholder() for _ in columns),
                )

                execute_batch(cur, insert_query.as_string(pg_conn), tuples, page_size=500)
                print(f"{table_name}: imported {len(tuples)} rows")

        pg_conn.commit()
        print("Import completed successfully.")
        return 0

    except Exception as exc:
        pg_conn.rollback()
        print(f"ERROR: import failed: {exc}")
        return 1

    finally:
        sqlite_conn.close()
        pg_conn.close()


if __name__ == "__main__":
    sys.exit(main())
