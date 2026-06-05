#!/usr/bin/env python3
"""
Validate the DHA Sheryan dataset produced by dha_sheryan_scraper.py.

Checks:
- Row count
- Distinct license# count (no dupes expected)
- License# format
- Field fill rates
- Top specialties, facilities
- Spot-check 20 random records by printing them
- Compare counts against known totals (99,520 professionals, 24,186 physicians, etc.)
"""
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

DATA = Path(__file__).resolve().parents[2] / "data"
CSV_PATH = DATA / "dha_professionals.csv"
STATS_PATH = DATA / "dha_professionals_stats.json"

# Known universe (from zavis.ai + DHA Sheryan 2026-04-03 snapshot)
KNOWN = {
    "physicians": 24_186,
    "dentists": 7_713,
    "nurses": 34_733,
    "allied_health": 32_888,
    "total": 99_520,
}


def main() -> int:
    if not CSV_PATH.exists():
        print(f"❌ {CSV_PATH} missing")
        return 1
    records = list(csv.DictReader(CSV_PATH.open(encoding="utf-8")))
    print(f"📄 {len(records):,} records in {CSV_PATH.name}")

    # License# check
    lic = [r["license_number"] for r in records]
    bad = [l for l in lic if not re.fullmatch(r"\d{5,10}", l)]
    print(f"🔢 Distinct license#: {len(set(lic)):,} / {len(lic):,}")
    print(f"🔢 License# format OK: {len(bad) == 0} (bad: {len(bad)})")
    if bad:
        print(f"   Examples: {bad[:5]}")

    # Field fill
    cols = [
        "full_name", "specialty", "license_number", "license_type",
        "facility_name", "area", "category", "specialty_slug",
        "profile_url", "scraped_at",
    ]
    print("📊 Field fill rates:")
    for c in cols:
        n = sum(1 for r in records if r.get(c))
        print(f"   {c:18s} {n:>6,} / {len(records):,}  ({n/len(records)*100:5.1f}%)")

    # Categorical breakdowns
    cats = Counter(r["category"] for r in records)
    print(f"📂 Category breakdown: {dict(cats)}")

    types = Counter(r["license_type"] for r in records)
    print(f"🏷️  License type: {dict(types)}")

    specs = Counter(r["specialty"] for r in records)
    print(f"🩺 Distinct specialties: {len(specs)}")
    print("   Top 10:", specs.most_common(10))

    facs = Counter(r["facility_name"] for r in records if r["facility_name"])
    print(f"🏥 Distinct facilities: {len(facs)}")
    print("   Top 5:", facs.most_common(5))

    # Compare to known universe
    phys = cats.get("physicians", 0)
    dent = cats.get("dentists", 0)
    print("🌍 Coverage vs known DHA Sheryan universe:")
    print(f"   physicians:   {phys:>6,} / {KNOWN['physicians']:>6,}  "
          f"({phys/KNOWN['physicians']*100:5.1f}%)")
    print(f"   dentists:     {dent:>6,} / {KNOWN['dentists']:>6,}  "
          f"({dent/KNOWN['dentists']*100:5.1f}%)")
    print(f"   (Total target dataset is {KNOWN['total']:,}; this run captured "
          f"physicians + dentists = {phys+dent:,})")

    # 20 random samples
    import random
    random.seed(0)
    print("\n🎲 20 random records (visual sanity check):")
    for r in random.sample(records, min(20, len(records))):
        fac = r["facility_name"] or "(no facility)"
        print(f"   {r['license_number']:>8}  {r['license_type']:3}  "
              f"{r['full_name'][:30]:30s}  {r['specialty'][:25]:25s}  {fac[:40]}")

    # Quality gates
    if STATS_PATH.exists():
        stats = json.loads(STATS_PATH.read_text(encoding="utf-8"))
        print(f"\n✅ Stats file: {STATS_PATH}")
        print(f"   Scraped at:  {stats.get('scraped_at')}")
        print(f"   Source:      {stats['source']['aggregator']} → "
              f"{stats['source']['original_registry']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
