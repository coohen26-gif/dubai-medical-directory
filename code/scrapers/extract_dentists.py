#!/usr/bin/env python3
"""
Extract dentists from DHA Sheryan full dump → dentists_emirates.csv
===================================================================

Mission (cron: DMD Scraping Dentistes Priorité):
- Extraire TOUS les dentistes + chirurgiens-dentistes du dataset DHA Sheryan
- Dédupliquer par license_number (dhaUniqueId)
- Mapper les spécialités vers la taxonomie cible:
  Dentist / Oral Surgeon / Orthodontist / Endodontist / Periodontist /
  Prosthodontist / Pediatric Dentist / Dental Implant
- Output: data/dentists_emirates.csv (append mode)
- Champs: full_name, specialty, license_number, nationality, languages,
          clinic_name, address, phone, email, latitude, longitude,
          working_hours, accepted_insurance, photos_url, source_url,
          scraped_at
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

LOG_DIR = Path("logs/scraping")
LOG_DIR.mkdir(parents=True, exist_ok=True)

ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
LOG_FILE = LOG_DIR / f"extract_dentists_{ts}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("extract_dentists")

# ---------------------------------------------------------------------------
# Specialty mapping (DHA → DMD taxonomy)
# ---------------------------------------------------------------------------

SPECIALTY_PATTERNS = [
    # (regex, normalized specialty)
    (r"orthodont", "Orthodontist"),
    (r"endodont", "Endodontist"),
    (r"periodont", "Periodontist"),
    (r"prosthodont", "Prosthodontist"),
    (r"pediatric\s*dent|paediatric\s*dent", "Pediatric Dentist"),
    (r"oral\s*and\s*maxillofacial|maxillofacial", "Oral Surgeon"),
    (r"oral\s*surg", "Oral Surgeon"),
    (r"implant", "Dental Implant"),
    (r"cosmetic\s*dent|aesthetic\s*dent", "Cosmetic Dentist"),
    (r"restorat", "Restorative Dentist"),
    (r"general\s*dent|general\s*practitioner.*dent|GP\s*dent", "General Dentist"),
    (r"consultant.*dent|consultant.*dental", "Consultant Dentist"),
    (r"specialist.*dent|specialist.*dental", "Specialist Dentist"),
]

# Country → nationality inference (from license source / facility heuristics)
UAE_EMIRATES = {
    "dubai": "Dubai",
    "abu dhabi": "Abu Dhabi",
    "sharjah": "Sharjah",
    "ajman": "Ajman",
    "umm al quwain": "Umm Al Quwain",
    "ras al khaimah": "Ras Al Khaimah",
    "fujairah": "Fujairah",
}


def normalize_specialty(raw: str) -> str:
    """Map DHA specialty string to DMD taxonomy."""
    if not raw:
        return "Dentist"
    s = raw.lower().strip()
    if "dentist" not in s and "dental" not in s and "maxillofacial" not in s:
        return ""  # not a dentist
    for pattern, label in SPECIALTY_PATTERNS:
        if re.search(pattern, s):
            return label
    # default for any dentist line without specific match
    if "consultant" in s:
        return "Consultant Dentist"
    if "specialist" in s:
        return "Specialist Dentist"
    return "General Dentist"


def extract_emirate(facility_name: str, source_url: str = "") -> str:
    """Best-effort inference of UAE emirate from facility name."""
    text = f"{facility_name} {source_url}".lower()
    for key, emirate in UAE_EMIRATES.items():
        if key in text:
            return emirate
    return "Dubai"  # DHA Sheryan is Dubai-centric, default


def build_address(facility_name: str, emirate: str) -> str:
    if not facility_name or facility_name.strip() in ("", "N/A", "null"):
        return f"{emirate}, UAE"
    return f"{facility_name}, {emirate}, UAE"


def build_source_url(dha_unique_id: str) -> str:
    return f"https://sheryan.dha.gov.ae/SearchProfessionals?search={dha_unique_id}"


# ---------------------------------------------------------------------------
# Main extraction
# ---------------------------------------------------------------------------

OUTPUT_FIELDS = [
    "full_name",
    "specialty",
    "license_number",
    "license_type",
    "nationality",
    "languages",
    "clinic_name",
    "address",
    "emirate",
    "phone",
    "email",
    "latitude",
    "longitude",
    "working_hours",
    "accepted_insurance",
    "photos_url",
    "source_url",
    "scraped_at",
]


def iter_jsonl(path: Path) -> Iterable[dict]:
    with path.open("r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                log.warning("Bad JSON line %d in %s: %s", line_no, path, e)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        default="data/dha_sheryan_full.jsonl",
        help="Input JSONL file (DHA Sheryan full dump)",
    )
    parser.add_argument(
        "--output",
        default="data/dentists_emirates.csv",
        help="Output CSV file (append mode)",
    )
    parser.add_argument(
        "--append",
        action="store_true",
        default=True,
        help="Append to output (default true; dedup by license_number)",
    )
    parser.add_argument(
        "--scraped-at",
        default=datetime.now(timezone.utc).isoformat(),
        help="ISO timestamp for scraped_at field",
    )
    args = parser.parse_args()

    in_path = Path(args.input)
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not in_path.exists():
        log.error("Input not found: %s", in_path)
        return 1

    # Load existing license_numbers for dedup
    existing_licenses: set[str] = set()
    if args.append and out_path.exists():
        with out_path.open("r", encoding="utf-8", newline="") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                lic = row.get("license_number", "").strip()
                if lic:
                    existing_licenses.add(lic)
        log.info("Loaded %d existing license_numbers from %s", len(existing_licenses), out_path)

    # Determine file mode
    file_exists = out_path.exists() and out_path.stat().st_size > 0
    write_header = not (args.append and file_exists)
    mode = "a" if (args.append and file_exists) else "w"

    scanned = 0
    matched = 0
    written = 0
    skipped_dup = 0
    seen_this_run: set[str] = set()

    log.info("Scanning %s for Dentist* records…", in_path)

    with out_path.open(mode, encoding="utf-8", newline="") as out_fh:
        writer = csv.DictWriter(out_fh, fieldnames=OUTPUT_FIELDS)
        if write_header:
            writer.writeheader()
            out_fh.flush()

        for rec in iter_jsonl(in_path):
            scanned += 1
            specialty_raw = rec.get("categoryOrSpeciality", "")
            specialty = normalize_specialty(specialty_raw)
            if not specialty:
                continue
            matched += 1

            license_number = str(rec.get("dhaUniqueId", "")).strip()
            if not license_number:
                continue

            # Dedup: in-file + this-run
            if license_number in existing_licenses or license_number in seen_this_run:
                skipped_dup += 1
                continue
            seen_this_run.add(license_number)

            full_name = rec.get("name", "").strip()
            clinic_name = rec.get("facilityName", "").strip()
            license_type = rec.get("licenseType", "").strip()
            photo = rec.get("photo", "").strip()
            source_url = build_source_url(license_number)
            emirate = extract_emirate(clinic_name, source_url)
            address = build_address(clinic_name, emirate)

            row = {
                "full_name": full_name,
                "specialty": specialty,
                "license_number": license_number,
                "license_type": license_type,
                "nationality": "",  # not in DHA public dump; needs Zavis enrichment
                "languages": "",    # not in DHA public dump; needs Zavis enrichment
                "clinic_name": clinic_name,
                "address": address,
                "emirate": emirate,
                "phone": "",
                "email": "",
                "latitude": "",
                "longitude": "",
                "working_hours": "",
                "accepted_insurance": "",
                "photos_url": photo,
                "source_url": source_url,
                "scraped_at": args.scraped_at,
            }
            writer.writerow(row)
            written += 1
            if written % 500 == 0:
                out_fh.flush()
                log.info("scanned=%d matched=%d written=%d dup_skip=%d",
                         scanned, matched, written, skipped_dup)

    out_fh_close = out_path  # noqa: F841 (file is closed by context manager)
    log.info("DONE. scanned=%d matched=%d written=%d dup_skip=%d output=%s",
             scanned, matched, written, skipped_dup, out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
