"""
Loads northwind_complaints.csv into the `complaints` table on Tiger Cloud.

Usage:
    python import_csv.py path/to/northwind_complaints.csv

Requires the DATABASE_URL environment variable to be set to your Tiger Cloud
connection string, e.g.:
    export DATABASE_URL="postgres://user:password@host:port/dbname?sslmode=require"

Run schema.sql against the same database first.
"""

import csv
import os
import sys

import psycopg2


def to_bool(value):
    """CSV stores booleans as '0'/'1'/''; convert to Python bool or None."""
    if value in ("", None):
        return None
    return value == "1"


def to_int(value):
    if value in ("", None):
        return None
    return int(value)


def to_numeric(value):
    if value in ("", None):
        return None
    return float(value)


def to_date(value):
    if value in ("", None):
        return None
    return value  # 'YYYY-MM-DD' strings are accepted directly by psycopg2/Postgres


COLUMNS = [
    "complaint_id",
    "date_opened",
    "date_closed",
    "status",
    "channel",
    "category",
    "priority",
    "region",
    "source_system",
    "transferred_between_systems",
    "sla_days",
    "days_to_close",
    "sla_breach",
    "reopened",
    "resolution_action",
    "resolvable_by_information_only",
    "bill_correction_value",
    "account_id",
]

INSERT_SQL = f"""
    INSERT INTO complaints ({", ".join(COLUMNS)})
    VALUES ({", ".join(["%s"] * len(COLUMNS))})
    ON CONFLICT (complaint_id, date_opened) DO NOTHING
"""


def row_to_values(row):
    return (
        row["complaint_id"],
        to_date(row["date_opened"]),
        to_date(row["date_closed"]),
        row["status"],
        row["channel"],
        row["category"],
        row["priority"],
        row["region"],
        row["source_system"],
        to_bool(row["transferred_between_systems"]) or False,
        to_int(row["sla_days"]),
        to_int(row["days_to_close"]),
        to_bool(row["sla_breach"]) or False,
        to_bool(row["reopened"]) or False,
        row["resolution_action"] or None,
        to_bool(row["resolvable_by_information_only"]),
        to_numeric(row["bill_correction_value"]),
        row["account_id"],
    )


def main():
    if len(sys.argv) != 2:
        print("Usage: python import_csv.py path/to/northwind_complaints.csv")
        sys.exit(1)

    csv_path = sys.argv[1]
    database_url = os.environ.get("DATABASE_URL")
    if not database_url:
        print("Error: set the DATABASE_URL environment variable to your Tiger Cloud connection string.")
        sys.exit(1)

    conn = psycopg2.connect(database_url)
    cur = conn.cursor()

    batch = []
    batch_size = 1000
    total = 0

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            batch.append(row_to_values(row))
            if len(batch) >= batch_size:
                cur.executemany(INSERT_SQL, batch)
                conn.commit()
                total += len(batch)
                print(f"Inserted {total} rows...")
                batch = []

        if batch:
            cur.executemany(INSERT_SQL, batch)
            conn.commit()
            total += len(batch)

    print(f"Done. Inserted {total} rows total.")
    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
