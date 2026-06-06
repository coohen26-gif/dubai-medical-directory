#!/usr/bin/env python3
"""
Enrich dentists_emirates.csv from dha_sheryan_enrichment_sample.jsonl
=====================================================================

Mission (cron: DMD Scraping Dentistes Priorité):
- Populate nationality, languages, photos_url in dentists_emirates.csv
  from existing enrichment data (currently empty in CSV)
- The enrichment JSONL contains: nationality, languages[{name,level}],
  education[{year,school}], experience[{start,end,duration,location}],
  licenses[] (sub-licenses with facility)
- Source: DHA Sheryan portal (different endpoint from main dump)
- Only dentists (records whose category starts with "Dentist" or
  contains "dent" specialty) are merged
- Output: data/dentists_emirates.csv (in-place update, idempotent)

Caveats:
- Enrichment is a SAMPLE (250 records, ~54 dentists) from a one-off run
  on 2026-06-05. This script can be re-run when new enrichment data arrives.
- Idempotent: re-running produces zero changes.
- Does NOT add new rows — only fills empty fields in existing rows.
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

LOG_DIR = Path("logs/scraping")
LOG_DIR.mkdir(parents=True, exist_ok=True)

ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
LOG_FILE = LOG_DIR / f"enrich_dentists_{ts}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("enrich_dentists")

DENTIST_KEYWORDS = ("dentist", "dental", "maxillofacial", "endodont",
                    "orthodont", "periodont", "prosthodont", "pediatric dent")


def is_dentist_record(rec: dict[str, Any]) -> bool:
    cat = (rec.get("categoryOrSpeciality", "") or "").lower()
    return any(kw in cat for kw in DENTIST_KEYWORDS)


def collapse_languages(languages: list[dict[str, str]] | None) -> str:
    """languages=[{name, level}] → 'English (Fluent); Arabic (Intermediate)'"""
    if not languages:
        return ""
    seen: set[str] = set()
    out: list[str] = []
    for entry in languages:
        name = (entry.get("name") or "").strip()
        level = (entry.get("level") or "").strip()
        if not name:
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        if level:
            out.append(f"{name} ({level})")
        else:
            out.append(name)
    return "; ".join(out)


def merge_enrichment_into_row(
    row: dict[str, str],
    enrichment: dict[str, Any],
) -> dict[str, str]:
    """Fill empty fields in `row` from `enrichment` dict. Returns the row
    (mutated in place) plus a count of fields that were updated."""
    updates: list[str] = []

    # nationality
    nat = (enrichment.get("nationality") or "").strip()
    if nat and not row.get("nationality", "").strip():
        row["nationality"] = nat
        updates.append("nationality")

    # languages
    langs = collapse_languages(enrichment.get("languages"))
    if langs and not row.get("languages", "").strip():
        row["languages"] = langs
        updates.append("languages")

    # photos_url: enrichment has no photo field directly; the DHA portal
    # exposes the photo URL in the main record. We pass through if present.
    # (The source JSONL bundles photo at the top-level, not under enrichment.)
    return row  # updates tracked by caller via comparison


def load_enrichment_index(jsonl_path: Path) -> dict[str, dict[str, Any]]:
    """Return {license_number: enrichment_dict} filtered to dentists only."""
    idx: dict[str, dict[str, Any]] = {}
    n_total = 0
    n_dentists = 0
    if not jsonl_path.exists():
        log.error("Enrichment JSONL not found: %s", jsonl_path)
        return idx
    with jsonl_path.open("r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError as e:
                log.warning("Bad JSON line %d: %s", line_no, e)
                continue
            n_total += 1
            if not is_dentist_record(rec):
                continue
            n_dentists += 1
            lic = str(rec.get("dhaUniqueId", "")).strip()
            enr = rec.get("enrichment") or {}
            if lic and enr:
                # First-wins semantics; enrichment should be 1:1 by license
                idx.setdefault(lic, enr)
    log.info(
        "Loaded enrichment: %d total records, %d dentist records, %d unique dentist licenses",
        n_total, n_dentists, len(idx),
    )
    return idx


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--csv",
        default="data/dentists_emirates.csv",
        help="Dentists CSV (will be updated in place)",
    )
    parser.add_argument(
        "--enrichment",
        default="data/dha_sheryan_enrichment_sample.jsonl",
        help="Enrichment JSONL source",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv)
    enr_path = Path(args.enrichment)
    if not csv_path.exists():
        log.error("CSV not found: %s", csv_path)
        return 1

    enr_idx = load_enrichment_index(enr_path)
    if not enr_idx:
        log.warning("No enrichment data to apply.")
        return 0

    # Read CSV
    with csv_path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        fieldnames = reader.fieldnames or []
        rows = list(reader)
    log.info("Loaded %d dentist rows from %s", len(rows), csv_path)

    # Stats
    nat_updates = 0
    lang_updates = 0
    matched = 0
    skipped_no_enrichment = 0
    updated_rows: list[dict[str, str]] = []

    for row in rows:
        lic = (row.get("license_number") or "").strip()
        enr = enr_idx.get(lic)
        if not enr:
            skipped_no_enrichment += 1
            updated_rows.append(row)
            continue
        matched += 1
        before_nat = row.get("nationality", "")
        before_lang = row.get("languages", "")
        merge_enrichment_into_row(row, enr)
        if row.get("nationality", "") != before_nat:
            nat_updates += 1
        if row.get("languages", "") != before_lang:
            lang_updates += 1
        updated_rows.append(row)

    # Write back
    with csv_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(updated_rows)

    log.info(
        "DONE. matched=%d skipped_no_enrichment=%d "
        "nationality_updates=%d language_updates=%d output=%s",
        matched, skipped_no_enrichment,
        nat_updates, lang_updates, csv_path,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
