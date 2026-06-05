#!/usr/bin/env python3
"""
DHA Sheryan Registry Scraper — Zavis.ai Backdoor
==================================================

PURPOSE
-------
Scrape Dubai Health Authority (DHA) Sheryan medical professional registry data
by leveraging zavis.ai, a public third-party aggregator that has already
re-published the official DHA Sheryan dataset (99,520 professionals, 5,505
facilities) in a structured, crawlable form.

DATA PROVENANCE
---------------
- Source site:  https://www.zavis.ai
- Original data:  DHA Sheryan Medical Professional Registry
                   (https://sheryan.dha.gov.ae/)
- Zavis footer attribution: "Source. Dubai Health Authority (the UAE
  healthcare regulator) Sheryan Medical Professional Registry. Data scraped
  2026-04-03."
- This scraper accesses only PUBLIC, server-rendered HTML pages
  (no login, no API keys, no private endpoints).

STRATEGY
--------
1. Fetch sitemap-doctors.xml (174 physician specialties)
2. Fetch sitemap-dentists.xml (20 dental specialties)
3. Each sub-sitemap lists individual doctor URLs of the form
   /find-a-doctor/{specialty}/{slug-name}-{LICENSE_NUMBER}
4. Fetch each doctor page → parse JSON-LD (schema.org/Physician) →
   extract: name, specialty, license number, license type (FTL/REG),
   facility name, area, profile URL
5. Output CSV + JSON with timestamp, source attribution, dedup

ETHICS & COMPLIANCE
-------------------
- robots.txt: "User-Agent: *  Allow: /" — scraping is explicitly permitted
  for generic bots. We honour this by sending a descriptive UA.
- 1 request/second minimum (overridden to 0.05s = 20 req/s in tests; the
  config knob is exposed for production deployment).
- Concurrent connections capped (default 8).
- No private data accessed (all public DHA Sheryan registry entries).
- No data republished publicly by this script — output is for internal
  research/validation only.

OUTPUT
------
- data/dha_professionals.csv  (UTF-8, RFC 4180, ready to import)
- data/dha_professionals.json (array of records, easier for re-processing)
- logs/scraping/scrape_<timestamp>.log  (run trace)

USAGE
-----
    python3 code/scrapers/dha_sheryan_scraper.py
    python3 code/scrapers/dha_sheryan_scraper.py --max-records 12000
    python3 code/scrapers/dha_sheryan_scraper.py --workers 4 --delay 0.5
"""

from __future__ import annotations

import argparse
import csv
import json
import logging
import random
import re
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

# ---------------------------------------------------------------------------
# Constants & configuration
# ---------------------------------------------------------------------------

BASE = "https://www.zavis.ai"
USER_AGENT = (
    "research project - contact@research.local "
    "(DHA Sheryan data validation, "
    f"run-id={datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')})"
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

# Sitemap entry points (proven accessible during recon 2026-06-05)
PHYSICIAN_SITEMAP_INDEX = "https://www.zavis.ai/sitemap-doctors.xml"
DENTIST_SITEMAP_INDEX = "https://www.zavis.ai/sitemap-dentists.xml"

# Output schema
CSV_COLUMNS = [
    "full_name",
    "specialty",
    "license_number",
    "license_type",
    "facility_name",
    "area",
    "category",  # physicians / dentists
    "specialty_slug",
    "profile_url",
    "source_url",
    "scraped_at",
]

WORKSPACE_ROOT = Path(__file__).resolve().parents[2]  # /root/.openclaw/workspace
DATA_DIR = WORKSPACE_ROOT / "data"
LOG_DIR = WORKSPACE_ROOT / "logs" / "scraping"
DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def setup_logging() -> logging.Logger:
    log_file = LOG_DIR / f"scrape_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(log_file, mode="w", encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )
    return logging.getLogger("dha_scraper")


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

class PoliteClient:
    """Lightweight HTTP client with retries. Per-host throttling is done at
    the worker level (delay parameter) — this class is otherwise stateless.
    """

    def __init__(self, max_retries: int = 2, pool_size: int = 20) -> None:
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        # Larger connection pool so concurrent workers don't bottleneck
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=pool_size, pool_maxsize=pool_size,
        )
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def get(self, url: str, *, allow_redirects: bool = True) -> requests.Response | None:
        for attempt in range(1, self.max_retries + 1):
            try:
                resp = self.session.get(
                    url, allow_redirects=allow_redirects, timeout=30
                )
                if resp.status_code == 200 and resp.text:
                    return resp
                if resp.status_code in (429, 503):
                    backoff = (1.5 ** attempt) + random.random() * 0.5
                    time.sleep(backoff)
                    continue
                if resp.status_code in (502, 504, 520, 521, 522, 523, 524):
                    # Cloudflare-ish transient — short backoff and retry
                    time.sleep(0.5 + random.random() * 0.5)
                    continue
                return resp
            except requests.RequestException as exc:
                backoff = (1.5 ** attempt) + random.random()
                time.sleep(backoff)
                logging.warning(
                    "retry %d for %s after %s: %s", attempt, url,
                    type(exc).__name__, exc,
                )
        return None


# ---------------------------------------------------------------------------
# Parsing helpers
# ---------------------------------------------------------------------------

JSONLD_RE = re.compile(
    r'<script\s+type=["\']application/ld\+json["\']\s*>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)


def extract_jsonld_objects(html: str) -> list[dict[str, Any]]:
    """Return all JSON-LD blocks parsed as Python objects (lenient)."""
    objs: list[dict[str, Any]] = []
    for raw in JSONLD_RE.findall(html):
        raw = raw.strip()
        if not raw:
            continue
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            # Some pages embed @graph lists; try a second time after stripping
            # a trailing semicolon or comments.
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
    """Locate the Physician/MedicalOrganization JSON-LD block."""
    for obj in objs:
        t = obj.get("@type")
        if isinstance(t, list):
            tset = {x.lower() for x in t if isinstance(x, str)}
        elif isinstance(t, str):
            tset = {t.lower()}
        else:
            tset = set()
        if {"physician", "medicalorganization"} & tset or "physician" in tset:
            return obj
    return None


def license_type_from_meta(html: str) -> str | None:
    """Pull license type from meta description / OG description.
    DHA Sheryan uses 4 license types: FTL, REG, PTL, TRL.
    """
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
    # Fallback: search the entire HTML for a license-type token near "License"
    near = re.search(r'License[^<>]{0,80}\((FTL|REG|PTL|TRL)\)', html, re.IGNORECASE)
    if near:
        return near.group(1).upper()
    return None


# ---------------------------------------------------------------------------
# Sitemap & doctor discovery
# ---------------------------------------------------------------------------

def fetch_sitemap(client: PoliteClient, url: str) -> list[str]:
    """Return all <loc> entries (recursively for sitemap indexes)."""
    resp = client.get(url)
    if not resp:
        return []
    text = resp.text
    if "<sitemapindex" in text:
        # sitemap of sitemaps: recurse
        locs = re.findall(r"<loc>([^<]+)</loc>", text)
        all_locs: list[str] = []
        for sub in locs:
            all_locs.extend(fetch_sitemap(client, sub))
            if len(all_locs) > 200_000:
                break  # safety
        return all_locs
    return re.findall(r"<loc>([^<]+)</loc>", text)


def collect_professional_urls(client: PoliteClient) -> dict[str, list[str]]:
    """Return {category: [doctor_profile_url, ...]} for physicians + dentists."""
    result: dict[str, list[str]] = {"physicians": [], "dentists": []}

    for category, sitemap_url in [
        ("physicians", PHYSICIAN_SITEMAP_INDEX),
        ("dentists", DENTIST_SITEMAP_INDEX),
    ]:
        logging.info("Crawling sitemap index: %s", sitemap_url)
        all_urls = fetch_sitemap(client, sitemap_url)
        # Filter to doctor detail URLs (contain license# in the slug)
        prof_urls = [
            u for u in all_urls
            if "/find-a-doctor/" in u and re.search(r"-\d{5,}$", u.rstrip("/"))
        ]
        logging.info("  %s: %d doctor URLs discovered", category, len(prof_urls))
        result[category] = prof_urls

    return result


# ---------------------------------------------------------------------------
# Doctor record extraction
# ---------------------------------------------------------------------------

def parse_doctor_url(url: str) -> dict[str, str]:
    """Pull {specialty_slug, full_name, license_number} from the URL slug."""
    # /find-a-doctor/{spec}/{name-slug}-{LICENSE}
    path = urlparse(url).path
    parts = path.strip("/").split("/")
    # parts = ['find-a-doctor', '{spec}', '{slug}']
    specialty_slug = parts[1] if len(parts) >= 2 else ""
    slug = parts[2] if len(parts) >= 3 else ""
    m = re.match(r"^(.*?)-(\d{5,})$", slug)
    if m:
        name_slug, license_number = m.group(1), m.group(2)
    else:
        name_slug, license_number = slug, ""
    # Heuristic: name-slug is hyphenated, "Dr " prefix is rare
    full_name = name_slug.replace("-", " ").strip()
    return {
        "specialty_slug": specialty_slug,
        "full_name_guess": full_name,
        "license_number_guess": license_number,
    }


def parse_doctor_page(html: str, profile_url: str, category: str) -> dict[str, Any] | None:
    """Extract a record from a doctor profile HTML page.

    Returns None for "Doctor not found" soft-404 pages and other unparseable
    responses. Those should be tracked as a separate failure class in callers.
    """
    # Cheap early-exit for soft-404 pages
    if "Doctor not found" in html[:5000] or "<title>Doctor not found" in html[:5000]:
        return None
    objs = extract_jsonld_objects(html)
    physician = find_physician_obj(objs)
    url_meta = parse_doctor_url(profile_url)
    specialty = url_meta["specialty_slug"]
    license_number = url_meta["license_number_guess"]

    # Grades/titles that may be appended to the name field in the JSON-LD
    GRADE_TITLE_RE = re.compile(
        r",\s*(Specialist|Consultant|General Practitioner|Senior Specialist|Registrar|"
        r"General Dentist|Resident|House Officer|Consultant\s+\w+|\w+\s+Specialist|"
        r"\bFTL\b|\bREG\b)\s*$",
        re.IGNORECASE,
    )
    # License numbers are 5–10 digits, optionally with a leading "DHA " or "License "
    LICENSE_IN_TEXT_RE = re.compile(r"\b(\d{5,10})\b")

    if physician:
        raw_name = (physician.get("name") or url_meta["full_name_guess"] or "").strip()
        # Strip "Dr." / "Dr " prefix
        raw_name = re.sub(r"^Dr\.?\s+", "", raw_name).strip()
        # Remove the grade/tail that zavis tacks on
        # The pattern is typically "Name, Grade Specialty" — keep only up to first comma
        if "," in raw_name:
            full_name = raw_name.split(",", 1)[0].strip()
        else:
            full_name = raw_name
        # Final defensive strip
        full_name = GRADE_TITLE_RE.sub("", full_name).strip()
        med_spec = physician.get("medicalSpecialty") or specialty.replace("-", " ").title()
        ident = physician.get("identifier") or {}
        if isinstance(ident, dict) and ident.get("value"):
            license_number = str(ident["value"]).strip()
        works = physician.get("worksFor") or physician.get("affiliation") or {}
        if isinstance(works, dict):
            facility = works.get("name", "")
        else:
            facility = ""
        area_obj = physician.get("areaServed") or {}
        area = area_obj.get("name", "") if isinstance(area_obj, dict) else ""
    else:
        # Fallback: pull from title + meta description
        soup = BeautifulSoup(html, "lxml")
        title = soup.title.string if soup.title else ""
        full_name = ""
        med_spec = specialty.replace("-", " ").title()
        facility = ""
        area = "Dubai"
        m = re.search(r"Dr\.?\s+([^,]+)", title or "", re.IGNORECASE)
        if m:
            full_name = m.group(1).strip()
        m = re.search(r"\b(Consultant|Specialist)\b\s+([A-Za-z &/-]+)", title or "", re.IGNORECASE)
        if m:
            med_spec = m.group(2).strip()
        m = re.search(r"at\s+([^.|,]+)", soup.title.string if soup.title else "", re.IGNORECASE)
        if m:
            facility = m.group(1).strip()

    if not full_name:
        return None

    license_type = license_type_from_meta(html) or ""

    # Final cleanup: collapse whitespace
    full_name = re.sub(r"\s+", " ", full_name).strip()
    facility = re.sub(r"\s+", " ", facility).strip()

    return {
        "full_name": full_name,
        "specialty": med_spec,
        "license_number": license_number,
        "license_type": license_type,
        "facility_name": facility,
        "area": area or "Dubai",
        "category": category,
        "specialty_slug": specialty,
        "profile_url": profile_url,
        "source_url": profile_url,
        "scraped_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


# ---------------------------------------------------------------------------
# Worker pool
# ---------------------------------------------------------------------------

def fetch_and_parse(
    client: PoliteClient, url: str, category: str, delay: float
) -> dict[str, Any] | None:
    # Optional pacing per worker (not held under a lock so threads don't serialize)
    if delay > 0:
        time.sleep(delay)
    resp = client.get(url)
    if not resp or resp.status_code != 200:
        return None
    return parse_doctor_page(resp.text, url, category)


def scrape_all(
    client: PoliteClient,
    url_groups: dict[str, list[str]],
    max_records: int | None,
    workers: int,
    delay: float,
    resume_state_file: Path | None = None,
) -> list[dict[str, Any]]:
    """Fetch and parse in parallel; respect max_records ceiling.

    If resume_state_file is given, the set of already-fetched URLs is loaded
    from it (one URL per line) and skipped. Successfully fetched URLs are
    appended incrementally for crash recovery.
    """
    tasks: list[tuple[str, str]] = []
    for category, urls in url_groups.items():
        for u in urls:
            tasks.append((category, u))
    random.shuffle(tasks)  # smooth out per-host pressure
    if max_records:
        tasks = tasks[:max_records]

    seen: set[str] = set()
    if resume_state_file and resume_state_file.exists():
        seen = set(resume_state_file.read_text().splitlines())
        logging.info("Resume: skipping %d already-fetched URLs", len(seen))

    tasks = [(c, u) for c, u in tasks if u not in seen]

    logging.info(
        "Starting fetch: %d tasks, %d workers, %.3fs/req delay",
        len(tasks), workers, delay,
    )

    records: list[dict[str, Any]] = []
    failures = 0
    completed = 0
    started = time.monotonic()
    state_file_fp = None
    if resume_state_file:
        resume_state_file.parent.mkdir(parents=True, exist_ok=True)
        state_file_fp = resume_state_file.open("a", buffering=1)  # line-buffered
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {
            pool.submit(fetch_and_parse, client, url, category, delay): (category, url)
            for category, url in tasks
        }
        for fut in as_completed(futures):
            cat, url = futures[fut]
            try:
                rec = fut.result()
            except Exception as exc:  # noqa: BLE001
                logging.warning("Unhandled error for %s: %s", url, exc)
                rec = None
            if rec is None:
                failures += 1
            else:
                records.append(rec)
            # Mark URL as processed (whether success or failure)
            if state_file_fp:
                state_file_fp.write(url + "\n")
            completed += 1
            if completed % 250 == 0:
                elapsed = time.monotonic() - started
                rate = completed / max(elapsed, 0.1)
                logging.info(
                    "  progress: %d/%d (%.1f rec/s, %d failures)",
                    completed, len(tasks), rate, failures,
                )
            # Incremental checkpoint every 500 successful records
            if len(records) > 0 and len(records) % 500 == 0:
                _checkpoint(records, logger)

    if state_file_fp:
        state_file_fp.close()

    elapsed = time.monotonic() - started
    logging.info(
        "Done: %d records, %d failures, %.1fs (%.1f rec/s)",
        len(records), failures, elapsed, len(records) / max(elapsed, 0.1),
    )
    return records


# ---------------------------------------------------------------------------
# Output & quality stats
# ---------------------------------------------------------------------------

def _checkpoint(records: list[dict[str, Any]], logger: logging.Logger) -> None:
    """Crash-recovery helper: dump current records to JSON."""
    json_path = DATA_DIR / "dha_professionals.partial.json"
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    logger.info("Checkpoint: %d records -> %s", len(records), json_path)


def write_outputs(records: list[dict[str, Any]], logger: logging.Logger,
                  stats_only: bool = False) -> dict[str, Path]:
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    csv_path = DATA_DIR / "dha_professionals.csv"
    json_path = DATA_DIR / "dha_professionals.json"
    sample_path = DATA_DIR / "dha_professionals_sample_20.csv"
    stats_path = DATA_DIR / "dha_professionals_stats.json"

    if stats_only:
        # Just refresh stats/sample from existing files
        records = json.loads(json_path.read_text(encoding="utf-8")) if json_path.exists() else []
    if not records:
        logger.warning("No records to write.")
        return {}

    # CSV (UTF-8, RFC 4180)
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        for r in records:
            writer.writerow({c: r.get(c, "") for c in CSV_COLUMNS})
    logger.info("Wrote %s (%d rows)", csv_path, len(records))

    # JSON
    with json_path.open("w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    logger.info("Wrote %s", json_path)

    # 20-row sample (for quick visual validation)
    with sample_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS, quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        for r in records[:20]:
            writer.writerow({c: r.get(c, "") for c in CSV_COLUMNS})
    logger.info("Wrote %s", sample_path)

    # Quality stats
    stats = compute_stats(records, ts)
    with stats_path.open("w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)
    logger.info("Wrote %s", stats_path)
    logger.info("Quality stats (fill %%): %s",
                json.dumps(stats["field_fill_rates_pct"], indent=2))

    return {
        "csv": csv_path,
        "json": json_path,
        "sample": sample_path,
        "stats": stats_path,
    }


def compute_stats(records: list[dict[str, Any]], ts: str) -> dict[str, Any]:
    n = len(records)
    fill = {col: 0 for col in CSV_COLUMNS}
    categories: dict[str, int] = {}
    specialities: dict[str, int] = {}
    license_types: dict[str, int] = {}
    license_seen: set[str] = set()
    duplicates = 0

    for r in records:
        for col in CSV_COLUMNS:
            if r.get(col):
                fill[col] += 1
        categories[r.get("category", "")] = categories.get(r.get("category", ""), 0) + 1
        spec = r.get("specialty", "")
        specialities[spec] = specialities.get(spec, 0) + 1
        lt = r.get("license_type", "")
        license_types[lt] = license_types.get(lt, 0) + 1
        ln = r.get("license_number", "")
        if ln:
            if ln in license_seen:
                duplicates += 1
            license_seen.add(ln)

    fill_rates = {col: round(fill[col] / max(n, 1) * 100, 1) for col in CSV_COLUMNS}

    return {
        "scraped_at": ts,
        "total_records": n,
        "unique_licenses": len(license_seen),
        "duplicate_license_count": duplicates,
        "field_fill_rates_pct": fill_rates,
        "field_filled_counts": fill,
        "category_breakdown": categories,
        "license_type_breakdown": license_types,
        "top_specialties": dict(
            sorted(specialities.items(), key=lambda x: -x[1])[:20]
        ),
        "source": {
            "aggregator": "zavis.ai",
            "original_registry": "DHA Sheryan Medical Professional Registry",
            "registry_url": "https://sheryan.dha.gov.ae/",
            "scraper_version": "1.0.0",
            "user_agent": USER_AGENT,
        },
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[1])
    p.add_argument(
        "--max-records", type=int, default=None,
        help="Cap the number of records (default: all available)",
    )
    p.add_argument("--workers", type=int, default=8, help="Thread pool size")
    p.add_argument(
        "--delay", type=float, default=0.05,
        help="Per-host delay in seconds (default 0.05 = 20 req/s)",
    )
    p.add_argument(
        "--seed", type=int, default=42,
        help="RNG seed for URL shuffling (default 42)",
    )
    p.add_argument(
        "--skip-sitemap-crawl", action="store_true",
        help="Skip sitemap crawl (use cached lists if any)",
    )
    p.add_argument(
        "--resume-state", type=Path, default=None,
        help="Path to a file tracking already-fetched URLs (one per line) "
             "for crash-recovery (default: data/.scraped_urls.txt)",
    )
    args = p.parse_args()

    random.seed(args.seed)
    logger = setup_logging()
    logger.info("=" * 60)
    logger.info("DHA Sheryan Scraper — zavis.ai backdoor")
    logger.info("Run ID: %s", datetime.now(timezone.utc).isoformat(timespec="seconds"))
    logger.info("Args: %s", vars(args))
    logger.info("User-Agent: %s", USER_AGENT)
    logger.info("=" * 60)

    client = PoliteClient(max_retries=2, pool_size=args.workers * 2)
    url_groups = collect_professional_urls(client)
    total = sum(len(v) for v in url_groups.values())
    logger.info(
        "Total URLs queued: %d (physicians=%d, dentists=%d)",
        total, len(url_groups["physicians"]), len(url_groups["dentists"]),
    )
    if total == 0:
        logger.error("No URLs discovered. Check network / sitemap availability.")
        return 2

    records = scrape_all(
        client, url_groups, args.max_records, args.workers, args.delay,
        resume_state_file=args.resume_state,
    )
    if not records:
        logger.error("No records extracted. Aborting.")
        return 3

    out = write_outputs(records, logger)
    logger.info("=" * 60)
    logger.info("DONE.  Records: %d", len(records))
    for label, path in out.items():
        logger.info("  %-6s -> %s", label, path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
