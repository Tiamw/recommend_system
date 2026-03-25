from __future__ import annotations

import argparse
import csv
import sqlite3
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Import anime_clean.csv into a SQLite database.")
    parser.add_argument(
        "--input-csv",
        default="training/data/processed/anime_clean.csv",
        help="Path to anime_clean.csv",
    )
    parser.add_argument(
        "--output-db",
        default="anime.db",
        help="Path to output SQLite database",
    )
    parser.add_argument(
        "--table",
        default="anime",
        help="Table name to create/populate",
    )
    return parser.parse_args()


def to_int(value: str) -> int | None:
    value = value.strip()
    if value == "":
        return None
    return int(float(value))


def to_float(value: str) -> float | None:
    value = value.strip()
    if value == "":
        return None
    return float(value)


def main() -> None:
    args = parse_args()
    input_csv = Path(args.input_csv)
    output_db = Path(args.output_db)

    if not input_csv.exists():
        raise FileNotFoundError(f"Input CSV not found: {input_csv}")

    output_db.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(output_db) as conn:
        cursor = conn.cursor()
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {args.table} (
                anime_id INTEGER PRIMARY KEY,
                name TEXT,
                genre TEXT,
                type TEXT,
                episodes INTEGER,
                rating REAL,
                members INTEGER
            )
            """
        )

        with input_csv.open("r", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            rows = []
            for row in reader:
                rows.append(
                    (
                        to_int(row.get("anime_id", "")),
                        row.get("name", "").strip() or None,
                        row.get("genre", "").strip() or None,
                        row.get("type", "").strip() or None,
                        to_int(row.get("episodes", "")),
                        to_float(row.get("rating", "")),
                        to_int(row.get("members", "")),
                    )
                )

        cursor.executemany(
            f"""
            INSERT OR REPLACE INTO {args.table}
            (anime_id, name, genre, type, episodes, rating, members)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()

    print(f"Imported {len(rows)} rows into {output_db} ({args.table}).")


if __name__ == "__main__":
    main()
