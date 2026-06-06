#!/usr/bin/env python3
"""
DMD Scraping Cycle — single 30-min cron run
===========================================

Mission (cron: DMD Scraping Dentistes Priorité)
- Extract dentists from ALL available sources and append to
  data/dentists_emirates.csv, deduped by license_number (DHA License).
- Sources, in priority order:
    1. DHA Sheryan full dump  (data/dha_sheryan_full.jsonl, 101k records)
       - broad filter: any record with "dent" or "maxillofacial" or "implant"
         in categoryOrSpeciality. Includes General Dentist, Specialist
         Orthodontist, Implantology, Dental Hygienist, Dental Assistant,
         etc. — anything a sales team would call a "dentist prospect".
    2. Zavis sitemap crawler  (https://www.zavis.ai/sitemap-dentists.xml)
       - 20 sub-sitemaps → 7,700+ profile URLs.
       - Each profile exposes JSON-LD (schema.org/Physician) with
         identifier.value (DHA License), medicalSpecialty, worksFor.name,
         areaServed.name (emirate).
       - Zavis covers DHA + (where applicable) non-DHA-licensed dentists
         advertising on their directory.
- Dedup key: license_number (DHA License, 5–10 digits).
  Zavis records without a resolvable DHA License are tagged with
  source_url as the dedup key instead (so they still surface).
- Output: data/dentists_emirates.csv (append mode, RFC 4180).
- Logs: logs/scraping/scrape_cycle_<ts>.log
- Idempotent: re-running produces zero new rows.

Usage
-----
    # Default: 30-min budget, 4 concurrent workers, polite (0.3s/req)
    python3 code/scrapers/scrape_cycle.py

    # Tunable
    python3 code/scrapers/scrape_cycle.py --max-zavis 1500 --workers 6 --delay 0.25
    python3 code/scrapers/scrape_cycle.py --skip-dha --skip-zavis
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import random
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Paths & logging
# ---------------------------------------------------------------------------

WORKSPACE = Path(__file__).resolve().parents[2]  # /root/.openclaw/workspace
DATA_DIR = WORKSPACE / "data"
LOG_DIR = WORKSPACE / "logs" / "scraping"
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
LOG_FILE = LOG_DIR / f"scrape_cycle_{ts}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, mode="w", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger("scrape_cycle")

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

USER_AGENT = (
    "research project - contact@research.local "
    "(DMD dentist directory build, "
    f"run-id={ts})"
)
HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.7,fr;q=0.3",
    "Accept-Encoding": "gzip, deflate",
    "DNT": "1",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

DENTIST_SITEMAP_INDEX = "https://www.zavis.ai/sitemap-dentists.xml"

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

UAE_EMIRATES = {
    "dubai": "Dubai",
    "abu dhabi": "Abu Dhabi",
    "sharjah": "Sharjah",
    "ajman": "Ajman",
    "umm al quwain": "Umm Al Quwain",
    "ras al khaimah": "Ras Al Khaimah",
    "fujairah": "Fujairah",
}

# Broader filter than the original extract_dentists.py: capture every dental
# professional category (incl. hygienist, assistant, lab tech). The sales
# team filters downstream for the specific specialty they want.
DENTIST_KEYWORDS = (
    "dentist", "dental", "maxillofacial", "endodont", "orthodont",
    "periodont", "prosthodont", "pediatric dent", "implantolog",
    "implant", "oral surgery", "oral medicine", "dental radiology",
    "dental pathology", "dental hygiene", "dental lab", "dental assistant",
)

# Specialty → normalized label (subset; fallback = "Dentist")
SPECIALTY_PATTERNS = [
    (r"orthodont", "Orthodontist"),
    (r"endodont", "Endodontist"),
    (r"periodont", "Periodontist"),
    (r"prosthodont", "Prosthodontist"),
    (r"pediatric\s*dent|paediatric\s*dent", "Pediatric Dentist"),
    (r"oral\s*and\s*maxillofacial|maxillofacial", "Oral Surgeon"),
    (r"oral\s*surg", "Oral Surgeon"),
    (r"implantolog|implant\s*privilege", "Dental Implant"),
    (r"cosmetic\s*dent|aesthetic\s*dent", "Cosmetic Dentist"),
    (r"restorat", "Restorative Dentist"),
    (r"general\s*dent|general\s*practitioner", "General Dentist"),
    (r"dental\s*hygien", "Dental Hygienist"),
    (r"dental\s*assistant", "Dental Assistant"),
    (r"dental\s*lab", "Dental Lab Technician"),
    (r"consultant.*dent", "Consultant Dentist"),
    (r"specialist.*dent", "Specialist Dentist"),
]

# JSON-LD helpers
JSONLD_RE = re.compile(
    r'<script\s+type=["\']application/ld\+json["\']\s*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)

GRADE_TITLE_RE = re.compile(
    r",\s*(Specialist|Consultant|General Practitioner|Senior Specialist|Registrar|"
    r"General Dentist|Resident|House Officer|Consultant\s+\w+|\w+\s+Specialist|"
    r"\bFTL\b|\bREG\b)\s*$",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# HTTP client
# ---------------------------------------------------------------------------

class PoliteClient:
    def __init__(self, max_retries: int = 2, pool_size: int = 20) -> None:
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=pool_size, pool_maxsize=pool_size,
        )
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def get(self, url: str, *, timeout: int = 25) -> requests.Response | None:
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.get(url, allow_redirects=True, timeout=timeout)
                if resp.status_code == 200 and resp.text:
                    return resp
                if resp.status_code in (429, 503):
                    time.sleep((1.5 ** attempt) + random.random() * 0.5)
                    continue
                if resp.status_code in (502, 504, 520, 521, 522, 523, 524):
                    time.sleep(0.5 + random.random() * 0.5)
                    continue
                if resp.status_code in (403, 404):
                    return None
                return resp
            except requests.RequestException as exc:
                time.sleep((1.5 ** attempt) + random.random())
                log.warning("retry %d for %s after %s: %s", attempt, url,
                            type(exc).__name__, exc)
        return None


# ---------------------------------------------------------------------------
# Specialty normalization
# ---------------------------------------------------------------------------

def normalize_specialty(raw: str) -> str:
    if not raw:
        return "Dentist"
    s = raw.lower().strip()
    for pattern, label in SPECIALTY_PATTERNS:
        if re.search(pattern, s):
            return label
    if "dentist" in s or "dental" in s:
        return "Dentist"
    return "Dentist"


def is_dental_record(raw: str) -> bool:
    s = (raw or "").lower()
    return any(kw in s for kw in DENTIST_KEYWORDS)


def extract_emirate(text: str) -> str:
    s = (text or "").lower()
    for key, emirate in UAE_EMIRATES.items():
        if key in s:
            return emirate
    return "Dubai"  # Zavis is DHA-centric, default


def build_source_url(dha_unique_id: str) -> str:
    return f"https://sheryan.dha.gov.ae/SearchProfessionals?search={dha_unique_id}"


# ---------------------------------------------------------------------------
# Dedup state
# ---------------------------------------------------------------------------

def load_existing_licenses(csv_path: Path) -> tuple[set[str], set[str]]:
    """Return (license_set, source_url_set) from existing CSV."""
    licenses: set[str] = set()
    sources: set[str] = set()
    if not csv_path.exists():
        return licenses, sources
    with csv_path.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            lic = (row.get("license_number") or "").strip()
            if lic:
                licenses.add(lic)
            src = (row.get("source_url") or "").strip()
            if src:
                sources.add(src)
    return licenses, sources


# ---------------------------------------------------------------------------
# Source 1: DHA Sheryan full dump
# ---------------------------------------------------------------------------

def iter_dha_dump(path: Path) -> Iterable[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError as e:
                log.warning("DHA dump bad JSON line %d: %s", line_no, e)


def extract_dha_source(
    jsonl_path: Path,
    existing_licenses: set[str],
    scraped_at: str,
) -> list[dict[str, str]]:
    """Yield dentist rows from DHA Sheryan full dump, skipping known dups."""
    log.info("[DHA] scanning %s", jsonl_path)
    scanned = matched = skipped = 0
    rows: list[dict[str, str]] = []
    for rec in iter_dha_dump(jsonl_path):
        scanned += 1
        cat = rec.get("categoryOrSpeciality", "")
        if not is_dental_record(cat):
            continue
        matched += 1
        license_number = str(rec.get("dhaUniqueId", "")).strip()
        if not license_number or license_number in existing_licenses:
            skipped += 1
            continue
        existing_licenses.add(license_number)
        full_name = (rec.get("name", "") or "").strip()
        # Strip leading "Dr."
        full_name = re.sub(r"^Dr\.?\s+", "", full_name).strip()
        clinic_name = (rec.get("facilityName", "") or "").strip()
        license_type = (rec.get("licenseType", "") or "").strip()
        photo = (rec.get("photo", "") or "").strip()
        source_url = build_source_url(license_number)
        emirate = extract_emirate(f"{clinic_name} {source_url}")
        address = clinic_name if clinic_name else f"{emirate}, UAE"
        if clinic_name:
            address = f"{clinic_name}, {emirate}, UAE"
        else:
            address = f"{emirate}, UAE"
        rows.append({
            "full_name": full_name,
            "specialty": normalize_specialty(cat),
            "license_number": license_number,
            "license_type": license_type,
            "nationality": "",
            "languages": "",
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
            "scraped_at": scraped_at,
        })
    log.info("[DHA] scanned=%d matched=%d new=%d skipped_dup=%d",
             scanned, matched, len(rows), skipped)
    return rows


# ---------------------------------------------------------------------------
# Source 2: Zavis sitemap + JSON-LD
# ---------------------------------------------------------------------------

def fetch_sitemap_urls(client: PoliteClient, sitemap_url: str) -> list[str]:
    """Recursively collect <loc> entries from a sitemap (handles indexes)."""
    resp = client.get(sitemap_url)
    if not resp:
        log.warning("sitemap fetch failed: %s", sitemap_url)
        return []
    text = resp.text
    if "<sitemapindex" in text:
        all_locs: list[str] = []
        for sub in re.findall(r"<loc>([^<]+)</loc>", text):
            all_locs.extend(fetch_sitemap_urls(client, sub))
            if len(all_locs) > 100_000:
                break
        return all_locs
    return re.findall(r"<loc>([^<]+)</loc>", text)


def collect_zavis_dentist_urls(client: PoliteClient) -> list[str]:
    log.info("[ZAVIS] fetching sitemap index %s", DENTIST_SITEMAP_INDEX)
    urls = fetch_sitemap_urls(client, DENTIST_SITEMAP_INDEX)
    profile_urls = [
        u for u in urls
        if "/find-a-doctor/" in u and re.search(r"-\d{5,}$", u.rstrip("/"))
    ]
    log.info("[ZAVIS] %d total URLs, %d profile URLs (after filter)",
             len(urls), len(profile_urls))
    return profile_urls


def extract_jsonld_objects(html: str) -> list[dict[str, Any]]:
    objs: list[dict[str, Any]] = []
    for raw in JSONLD_RE.findall(html):
        raw = raw.strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            try:
                data = json.loads(raw.rstrip(";"))
            except json.JSONDecodeError:
                continue
        if isinstance(data, list):
            objs.extend(x for x in data if isinstance(x, dict))
        elif isinstance(data, dict):
            objs.append(data)
    return objs


def find_physician_obj(objs: Iterable[dict[str, Any]]) -> dict[str, Any] | None:
    for obj in objs:
        t = obj.get("@type")
        if isinstance(t, list):
            tset = {x.lower() for x in t if isinstance(x, str)}
        elif isinstance(t, str):
            tset = {t.lower()}
        else:
            tset = set()
        if "physician" in tset or "medicalorganization" in tset:
            return obj
    return None


def parse_zavis_url(url: str) -> dict[str, str]:
    path = urlparse(url).path
    parts = path.strip("/").split("/")
    specialty_slug = parts[1] if len(parts) >= 2 else ""
    slug = parts[2] if len(parts) >= 3 else ""
    m = re.match(r"^(.*?)-(\d{5,})$", slug)
    if m:
        name_slug, license_number = m.group(1), m.group(2)
    else:
        name_slug, license_number = slug, ""
    full_name = name_slug.replace("-", " ").strip()
    return {
        "specialty_slug": specialty_slug,
        "full_name_guess": full_name,
        "license_number_guess": license_number,
    }


def license_type_from_meta(html: str) -> str:
    patterns = (
        r'License\s+[A-Z0-9]+\s+\((FTL|REG|PTL|TRL)\)',
        r'License\s+type[:\s]+(FTL|REG|PTL|TRL)',
        r'\((FTL|REG|PTL|TRL)\)',
    )
    for pat in patterns:
        m = re.search(pat, html, re.IGNORECASE)
        if m:
            for g in m.groups():
                if g:
                    return g.upper()
    near = re.search(r'License[^<>]{0,80}\((FTL|REG|PTL|TRL)\)', html, re.IGNORECASE)
    if near:
        return near.group(1).upper()
    return ""


def parse_zavis_profile(
    html: str,
    profile_url: str,
    existing_licenses: set[str],
    existing_sources: set[str],
    scraped_at: str,
) -> dict[str, str] | None:
    """Extract one dentist row from a Zavis profile page, or None to skip."""
    # Skip soft-404
    if "Doctor not found" in html[:5000]:
        return None
    # Skip already-known (by source_url)
    if profile_url in existing_sources:
        return None

    objs = extract_jsonld_objects(html)
    physician = find_physician_obj(objs)
    url_meta = parse_zavis_url(profile_url)
    specialty_slug = url_meta["specialty_slug"]
    license_number = url_meta["license_number_guess"]

    if physician:
        raw_name = (physician.get("name") or url_meta["full_name_guess"] or "").strip()
        raw_name = re.sub(r"^Dr\.?\s+", "", raw_name).strip()
        # "Name, Grade Specialty" — keep only up to first comma
        if "," in raw_name:
            full_name = raw_name.split(",", 1)[0].strip()
        else:
            full_name = raw_name
        full_name = GRADE_TITLE_RE.sub("", full_name).strip()
        med_spec = (physician.get("medicalSpecialty")
                    or specialty_slug.replace("-", " ").title())
        ident = physician.get("identifier") or {}
        if isinstance(ident, dict) and ident.get("value"):
            license_number = str(ident["value"]).strip()
        works = physician.get("worksFor") or physician.get("affiliation") or {}
        facility = works.get("name", "") if isinstance(works, dict) else ""
        area_obj = physician.get("areaServed") or {}
        area = area_obj.get("name", "") if isinstance(area_obj, dict) else ""
    else:
        soup = BeautifulSoup(html, "lxml")
        title = soup.title.string if soup.title else ""
        full_name = ""
        med_spec = specialty_slug.replace("-", " ").title()
        facility = ""
        area = "Dubai"
        m = re.search(r"Dr\.?\s+([^,]+)", title or "", re.IGNORECASE)
        if m:
            full_name = m.group(1).strip()
        m = re.search(r"\b(Consultant|Specialist)\b\s+([A-Za-z &/-]+)",
                      title or "", re.IGNORECASE)
        if m:
            med_spec = m.group(2).strip()
        m = re.search(r"at\s+([^.|,]+)",
                      soup.title.string if soup.title else "", re.IGNORECASE)
        if m:
            facility = m.group(1).strip()

    if not full_name:
        return None

    # Dedup by DHA license when resolvable
    if license_number and license_number in existing_licenses:
        return None

    license_type = license_type_from_meta(html)
    emirate = area or extract_emirate(f"{facility} {profile_url}")
    address = f"{facility}, {emirate}, UAE" if facility else f"{emirate}, UAE"
    specialty_norm = normalize_specialty(med_spec)

    return {
        "full_name": full_name,
        "specialty": specialty_norm,
        "license_number": license_number,
        "license_type": license_type,
        "nationality": "",
        "languages": "",
        "clinic_name": facility,
        "address": address,
        "emirate": emirate,
        "phone": "",
        "email": "",
        "latitude": "",
        "longitude": "",
        "working_hours": "",
        "accepted_insurance": "",
        "photos_url": "",
        "source_url": profile_url,
        "scraped_at": scraped_at,
    }


def fetch_and_parse_zavis(
    client: PoliteClient,
    url: str,
    existing_licenses: set[str],
    existing_sources: set[str],
    scraped_at: str,
    delay: float,
) -> dict[str, str] | None:
    time.sleep(delay * (0.5 + random.random()))  # jitter
    resp = client.get(url)
    if not resp:
        return None
    return parse_zavis_profile(
        resp.text, url, existing_licenses, existing_sources, scraped_at,
    )


def scrape_zavis(
    client: PoliteClient,
    urls: list[str],
    existing_licenses: set[str],
    existing_sources: set[str],
    scraped_at: str,
    workers: int,
    delay: float,
    max_records: int,
) -> list[dict[str, str]]:
    log.info("[ZAVIS] scraping up to %d URLs with %d workers (delay=%.2fs)",
             max_records, workers, delay)
    rows: list[dict[str, str]] = []
    seen_local: set[str] = set()
    total = min(len(urls), max_records)
    processed = 0
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(
                fetch_and_parse_zavis, client, url,
                existing_licenses, existing_sources, scraped_at, delay,
            ): url
            for url in urls[:total]
        }
        for fut in as_completed(futures):
            processed += 1
            try:
                row = fut.result()
            except Exception as e:
                log.warning("[ZAVIS] worker error: %s", e)
                continue
            if not row:
                continue
            lic = row["license_number"]
            src = row["source_url"]
            if lic in seen_local or src in seen_local:
                continue
            seen_local.add(lic or src)
            existing_licenses.add(lic) if lic else existing_sources.add(src)
            rows.append(row)
            if processed % 200 == 0:
                log.info("[ZAVIS] progress: %d/%d processed, %d new rows",
                         processed, total, len(rows))
    log.info("[ZAVIS] DONE: %d/%d processed, %d new rows",
             processed, total, len(rows))
    return rows


# ---------------------------------------------------------------------------
# CSV writer
# ---------------------------------------------------------------------------

def append_rows(csv_path: Path, rows: list[dict[str, str]]) -> int:
    if not rows:
        log.info("append: no new rows to write")
        return 0
    file_exists = csv_path.exists() and csv_path.stat().st_size > 0
    with csv_path.open("a" if file_exists else "w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=OUTPUT_FIELDS, quoting=csv.QUOTE_MINIMAL)
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)
    log.info("append: wrote %d new rows to %s", len(rows), csv_path)
    return len(rows)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="data/dentists_emirates.csv")
    parser.add_argument("--dha-jsonl", default="data/dha_sheryan_full.jsonl")
    parser.add_argument("--skip-dha", action="store_true")
    parser.add_argument("--skip-zavis", action="store_true")
    parser.add_argument("--max-zavis", type=int, default=2000,
                        help="Max Zavis profiles to scrape per cycle")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--delay", type=float, default=0.25,
                        help="Base delay between Zavis requests (seconds)")
    parser.add_argument("--scraped-at",
                        default=datetime.now(timezone.utc).isoformat())
    args = parser.parse_args()

    csv_path = WORKSPACE / args.csv
    dha_path = WORKSPACE / args.dha_jsonl

    log.info("=== DMD scrape cycle starting ===")
    log.info("csv=%s  dha=%s  workers=%d  delay=%.2fs  max_zavis=%d",
             csv_path, dha_path, args.workers, args.delay, args.max_zavis)
    log.info("skip_dha=%s  skip_zavis=%s  scraped_at=%s",
             args.skip_dha, args.skip_zavis, args.scraped_at)

    t0 = time.time()
    existing_licenses, existing_sources = load_existing_licenses(csv_path)
    log.info("loaded %d existing licenses, %d existing source_urls",
             len(existing_licenses), len(existing_sources))

    new_rows: list[dict[str, str]] = []

    # --- Source 1: DHA Sheryan full dump ---
    if not args.skip_dha and dha_path.exists():
        dha_rows = extract_dha_source(
            dha_path, existing_licenses, args.scraped_at,
        )
        new_rows.extend(dha_rows)
        log.info("[DHA] elapsed=%.1fs total_new=%d", time.time() - t0, len(new_rows))
    elif not args.skip_dha:
        log.warning("DHA jsonl not found: %s", dha_path)

    # --- Source 2: Zavis sitemap crawl ---
    if not args.skip_zavis:
        client = PoliteClient()
        try:
            urls = collect_zavis_dentist_urls(client)
            if urls:
                zavis_rows = scrape_zavis(
                    client, urls, existing_licenses, existing_sources,
                    args.scraped_at, args.workers, args.delay, args.max_zavis,
                )
                new_rows.extend(zavis_rows)
        except Exception as e:
            log.error("[ZAVIS] fatal: %s", e)
        log.info("[ZAVIS] elapsed=%.1fs total_new=%d", time.time() - t0, len(new_rows))

    # --- Persist ---
    written = append_rows(csv_path, new_rows)
    log.info("=== CYCLE DONE ===  new_rows=%d  written=%d  total_elapsed=%.1fs",
             len(new_rows), written, time.time() - t0)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
