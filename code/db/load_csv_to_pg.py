#!/usr/bin/env python3
"""
load_csv_to_pg.py — Bulk load dha_professionals_full.csv into PostgreSQL.

Uses COPY (fast path) via psycopg2. Designed to run on the workstation that
has PostgreSQL access (this sandbox has no psql). Idempotent: ON CONFLICT
DO NOTHING on dha_unique_id.

Usage:
    PGPASSWORD=... python3 code/db/load_csv_to_pg.py \
        --csv data/dha_professionals_full.csv \
        --dsn  "host=localhost dbname=dmd user=dmd_loader"

Generated: 2026-06-06 (cron 567b5bee)
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values

REPO = Path(__file__).resolve().parent.parent.parent
DEFAULT_CSV = REPO / "data" / "dha_professionals_full.csv"
DEFAULT_SCHEMA = REPO / "code" / "db" / "schema.sql"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    p.add_argument("--schema", type=Path, default=DEFAULT_SCHEMA)
    p.add_argument("--dsn", default=os.environ.get("DMD_PG_DSN", ""))
    p.add_argument("--batch", type=int, default=2000)
    p.add_argument("--skip-schema", action="store_true")
    return p.parse_args()


def apply_schema(conn, schema_path: Path) -> None:
    sql = schema_path.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
    print(f"[schema] applied from {schema_path.relative_to(REPO)}")


def stream_rows(csv_path: Path):
    with csv_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            yield (
                row["dhaUniqueId"].strip().zfill(8),
                row["full_name"].strip(),
                row["category"].strip(),
                row["specialty"].strip(),
                row["license_type"].strip(),
                (row.get("facility_name") or "").strip() or None,
                int(row.get("license_count") or 1),
                int(row.get("facility_count") or 0),
                (row.get("has_photo") or "no").lower() == "yes",
            )


def load(conn, csv_path: Path, batch: int) -> dict:
    started = time.time()
    log_id = None
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO dmd.ingestion_log(csv_path) VALUES (%s)
            RETURNING log_id
            """,
            (str(csv_path.relative_to(REPO)),),
        )
        log_id = cur.fetchone()[0]
    conn.commit()

    inserted = 0
    skipped = 0
    buffer: list[tuple] = []

    sql = """
        INSERT INTO dmd.professional (
            dha_unique_id, full_name, category, specialty, license_type,
            facility_name, license_count, facility_count, has_photo
        ) VALUES %s
        ON CONFLICT (dha_unique_id) DO NOTHING
    """

    with conn.cursor() as cur:
        for row in stream_rows(csv_path):
            buffer.append(row)
            if len(buffer) >= batch:
                execute_values(cur, sql, buffer, page_size=batch)
                inserted += cur.rowcount
                buffer.clear()
        if buffer:
            execute_values(cur, sql, buffer, page_size=len(buffer))
            inserted += cur.rowcount

        # refresh facility summary
        cur.execute(
            """
            TRUNCATE dmd.facility_summary;
            INSERT INTO dmd.facility_summary
            SELECT facility_name, COUNT(*),
                   COUNT(DISTINCT category), COUNT(DISTINCT specialty),
                   MIN(ingested_at)
              FROM dmd.professional
             WHERE facility_name IS NOT NULL
             GROUP BY facility_name;
            """
        )

        with conn.cursor() as cur2:
            cur2.execute(
                """
                UPDATE dmd.ingestion_log
                   SET finished_at = NOW(),
                       rows_inserted = %s,
                       rows_skipped  = %s,
                       status = 'ok'
                 WHERE log_id = %s
                """,
                (inserted, skipped, log_id),
            )
    conn.commit()

    return {
        "inserted": inserted,
        "skipped": skipped,
        "elapsed_sec": round(time.time() - started, 1),
        "log_id": log_id,
    }


def main() -> int:
    args = parse_args()
    if not args.dsn:
        print("ERROR: --dsn or DMD_PG_DSN env required", file=sys.stderr)
        return 2

    print(f"[load] csv   = {args.csv.relative_to(REPO)}")
    print(f"[load] schema= {args.schema.relative_to(REPO)}")
    print(f"[load] dsn   = {args.dsn}")

    conn = psycopg2.connect(args.dsn)
    conn.autocommit = False

    try:
        if not args.skip_schema:
            apply_schema(conn, args.schema)
        result = load(conn, args.csv, args.batch)
        print(json.dumps(result, indent=2))
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
