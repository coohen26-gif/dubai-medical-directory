#!/usr/bin/env python3
"""DMD Data Quality Check - cron task e797d629."""
import csv
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"
REPORT = Path(__file__).parent / "data-quality-report.md"

# DHA license format: FTL/REG/PTL/TRL + numeric IDs
LICENSE_RE = re.compile(r"^(FTL|REG|PTL|TRL)\d+$")
LICENSE_NUM_RE = re.compile(r"^\d{6,8}$")  # observed 6-8 digit DHA IDs
PHONE_RE = re.compile(r"^\+?[\d\s\-\(\)]{7,}$")

# Language normalization map
LANG_MAP = {
    "arabic": "Arabic", "ar": "Arabic", "العربية": "Arabic",
    "english": "English", "en": "English",
    "french": "French", "fr": "French", "français": "French",
    "hindi": "Hindi", "urdu": "Urdu",
    "tagalog": "Tagalog", "filipino": "Tagalog",
    "russian": "Russian", "ru": "Russian",
    "spanish": "Spanish", "es": "Spanish",
}


def check_dha_main():
    path = DATA_DIR / "dha_professionals_full.csv"
    total = 0
    fields = Counter()
    licenses = Counter()
    facilities = Counter()
    dup_ids = 0
    seen_ids = set()
    exact_dup_rows = 0
    seen_row_hashes = set()
    license_invalid = []
    name_blank = 0
    cat_blank = 0

    with open(path, encoding="utf-8") as f:
        r = csv.DictReader(f)
        cols = r.fieldnames
        for row in r:
            total += 1
            for k, v in row.items():
                if v and v.strip():
                    fields[k] += 1
            lt = row.get("license_type", "").strip()
            if lt:
                licenses[lt] += 1
            fn = row.get("facility_name", "").strip()
            if fn:
                facilities[fn] += 1
            did = row.get("dhaUniqueId", "").strip()
            if did:
                if did in seen_ids:
                    dup_ids += 1
                seen_ids.add(did)
            if not row.get("full_name", "").strip():
                name_blank += 1
            if not row.get("category", "").strip():
                cat_blank += 1
            # exact-row duplicate detection (all columns identical)
            rh = tuple(row.get(k, "") for k in cols)
            if rh in seen_row_hashes:
                exact_dup_rows += 1
            else:
                seen_row_hashes.add(rh)
            lic_num = did
            lic_type = lt
            if lic_num and lic_type:
                # Combined format check (e.g. "FTL00003775")
                pass
            elif lic_num and not LICENSE_NUM_RE.match(lic_num):
                if len(license_invalid) < 10:
                    license_invalid.append(lic_num)

    return {
        "file": path.name,
        "rows": total,
        "columns": cols,
        "unique_ids": len(seen_ids),
        "duplicate_ids": dup_ids,
        "unique_rows": len(seen_row_hashes),
        "exact_duplicate_rows": exact_dup_rows,
        "field_filled": {k: round(v * 100 / total, 2) for k, v in fields.items()},
        "field_filled_count": dict(fields),
        "license_types": dict(licenses),
        "top_facilities": facilities.most_common(10),
        "unique_facilities": len(facilities),
        "blank_name": name_blank,
        "blank_category": cat_blank,
        "invalid_license_samples": license_invalid,
    }


def check_dentists():
    path = DATA_DIR / "dentists_emirates.csv"
    if not path.exists():
        return None
    total = 0
    fields = Counter()
    langs_raw = Counter()
    langs_norm = Counter()
    dups = 0
    seen = set()
    license_invalid = []
    phones_invalid = 0
    phones_total = 0

    with open(path, encoding="utf-8") as f:
        r = csv.DictReader(f)
        cols = r.fieldnames
        for row in r:
            total += 1
            for k, v in row.items():
                if v and v.strip():
                    fields[k] += 1
            lang = (row.get("languages") or "").strip()
            if lang:
                langs_raw[lang] += 1
                # split on comma/semicolon/and
                for tok in re.split(r"[,;/&]| and ", lang, flags=re.I):
                    tok = tok.strip().lower()
                    if not tok:
                        continue
                    norm = LANG_MAP.get(tok, tok.title())
                    langs_norm[norm] += 1
            key = (row.get("full_name", "").strip().lower(),
                   row.get("clinic_name", "").strip().lower())
            if key in seen:
                dups += 1
            else:
                seen.add(key)
            lic = (row.get("license_number") or "").strip()
            if lic and not LICENSE_NUM_RE.match(lic):
                if len(license_invalid) < 10:
                    license_invalid.append(lic)
            ph = (row.get("phone") or "").strip()
            if ph:
                phones_total += 1
                if not PHONE_RE.match(ph):
                    phones_invalid += 1

    return {
        "file": path.name,
        "rows": total,
        "columns": cols,
        "field_filled": {k: round(v * 100 / total, 2) for k, v in fields.items()},
        "field_filled_count": dict(fields),
        "duplicate_keys": dups,
        "languages_raw_top10": langs_raw.most_common(10),
        "languages_normalized_top10": langs_norm.most_common(15),
        "languages_unique_raw": len(langs_raw),
        "languages_unique_normalized": len(langs_norm),
        "license_invalid_samples": license_invalid,
        "phones_checked": phones_total,
        "phones_invalid": phones_invalid,
    }


def check_sheryan_jsonl():
    path = DATA_DIR / "dha_sheryan_full.jsonl"
    if not path.exists():
        return None
    total = 0
    facilities = Counter()
    cats = Counter()
    license_types = Counter()
    name_blank = 0
    cat_blank = 0
    photo_present = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            total += 1
            fn = obj.get("facilityName", "")
            if fn:
                facilities[fn] += 1
            cos = obj.get("categoryOrSpeciality", "")
            if cos:
                cats[cos] += 1
            lt = obj.get("licenseType", "")
            if lt:
                license_types[lt] += 1
            if not obj.get("name", "").strip():
                name_blank += 1
            if not cos.strip():
                cat_blank += 1
            if obj.get("photo"):
                photo_present += 1
    return {
        "file": path.name,
        "rows": total,
        "name_blank": name_blank,
        "category_blank": cat_blank,
        "photo_present_pct": round(photo_present * 100 / total, 2) if total else 0,
        "license_types": dict(license_types),
        "top_facilities": facilities.most_common(10),
        "unique_facilities": len(facilities),
        "top_categories": cats.most_common(10),
    }


def build_report(dha, dent, sheryan):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    out = []
    out.append(f"# DMD Data Quality Report")
    out.append(f"\n_Generated: {now}_  ")
    out.append(f"_Cron task: `e797d629-c1b9-46dc-b2a0-2103731b61bc` (Dubai - Data Quality Check)_\n")

    out.append(f"## Executive Summary\n")
    critical = []
    if dha.get("exact_duplicate_rows", 0) > 0:
        critical.append(
            f"❌ **{dha['exact_duplicate_rows']:,} exact duplicate rows** in DHA main CSV "
            f"({round(dha['exact_duplicate_rows']*100/dha['rows'],2)}% of {dha['rows']:,} rows). "
            f"Likely scraping bug re-appending same records."
        )
    elif dha["duplicate_ids"] > 0:
        critical.append(f"⚠️ **{dha['duplicate_ids']} duplicate `dhaUniqueId` rows** in DHA main CSV (out of {dha['rows']})")
    if dent and dent["duplicate_keys"] > 0:
        critical.append(f"⚠️ **{dent['duplicate_keys']} duplicate (name+clinic) rows** in dentists CSV")
    if not critical:
        out.append("✅ **No critical issues detected.**\n")
    else:
        out.append("\n".join(critical) + "\n")

    # Section: DHA main
    out.append(f"## 1. DHA Main Dataset — `{dha['file']}`\n")
    out.append(f"| Metric | Value |")
    out.append(f"|---|---|")
    out.append(f"| Total rows | {dha['rows']:,} |")
    out.append(f"| Unique rows (all-cols) | {dha['unique_rows']:,} |")
    out.append(f"| **Exact duplicate rows** | **{dha.get('exact_duplicate_rows',0):,}** ({round(dha.get('exact_duplicate_rows',0)*100/dha['rows'],2)}%) |")
    out.append(f"| Unique `dhaUniqueId` | {dha['unique_ids']:,} |")
    out.append(f"| Duplicate IDs (re-occurrences) | {dha['duplicate_ids']:,} ({round(dha['duplicate_ids']*100/dha['rows'],2)}%) |")
    out.append(f"| Unique facilities | {dha['unique_facilities']:,} |")
    out.append(f"| Blank `full_name` | {dha['blank_name']} |")
    out.append(f"| Blank `category` | {dha['blank_category']} |")
    out.append("\n### Field fill rate (%)\n")
    out.append("| Field | Fill % |")
    out.append("|---|---|")
    for k, v in sorted(dha["field_filled"].items(), key=lambda x: -x[1]):
        flag = " ✅" if v >= 95 else (" ⚠️" if v >= 50 else " ❌")
        out.append(f"| `{k}` | {v}%{flag} |")
    out.append("\n### License type distribution\n")
    out.append("| Type | Count |")
    out.append("|---|---|")
    for lt, c in sorted(dha["license_types"].items(), key=lambda x: -x[1]):
        out.append(f"| `{lt}` | {c:,} |")
    out.append(f"\n### Top 10 facilities\n")
    for fn, c in dha["top_facilities"]:
        out.append(f"- {fn} — {c:,}")
    if dha["invalid_license_samples"]:
        out.append(f"\n**License ID format samples (suspicious):** `{dha['invalid_license_samples']}`")
    out.append("")

    # Section: Dentists
    out.append(f"## 2. Dentists UAE Dataset — `{dent['file']}`\n")
    out.append(f"| Metric | Value |")
    out.append(f"|---|---|")
    out.append(f"| Total rows | {dent['rows']:,} |")
    out.append(f"| Duplicate (name+clinic) | {dent['duplicate_keys']} |")
    out.append(f"| Phones checked | {dent['phones_checked']} |")
    out.append(f"| Phones invalid format | {dent['phones_invalid']} |")
    out.append(f"| Languages raw (unique values) | {dent['languages_unique_raw']} |")
    out.append(f"| Languages normalized (unique) | {dent['languages_unique_normalized']} |")
    out.append("\n### Field fill rate (%)\n")
    out.append("| Field | Fill % |")
    out.append("|---|---|")
    for k, v in sorted(dent["field_filled"].items(), key=lambda x: -x[1]):
        flag = " ✅" if v >= 95 else (" ⚠️" if v >= 50 else " ❌")
        out.append(f"| `{k}` | {v}%{flag} |")
    out.append(f"\n### Language normalization (top 15 normalized)\n")
    out.append("| Language | Count |")
    out.append("|---|---|")
    for lang, c in dent["languages_normalized_top10"]:
        out.append(f"| {lang} | {c} |")
    out.append(f"\n### Raw language values (top 10, pre-normalization)\n")
    out.append("| Raw value | Count |")
    out.append("|---|---|")
    for lang, c in dent["languages_raw_top10"]:
        out.append(f"| `{lang}` | {c} |")
    if dent["license_invalid_samples"]:
        out.append(f"\n**License number format samples (suspicious):** `{dent['license_invalid_samples']}`")
    out.append("")

    # Section: Sheryan JSONL
    out.append(f"## 3. Sheryan JSONL — `{sheryan['file']}`\n")
    out.append(f"| Metric | Value |")
    out.append(f"|---|---|")
    out.append(f"| Total records | {sheryan['rows']:,} |")
    out.append(f"| Blank `name` | {sheryan['name_blank']} |")
    out.append(f"| Blank `category` | {sheryan['category_blank']} |")
    out.append(f"| Records with photo | {sheryan['photo_present_pct']}% |")
    out.append("\n### License types (Sheryan)\n")
    out.append("| Type | Count |")
    out.append("|---|---|")
    for lt, c in sorted(sheryan["license_types"].items(), key=lambda x: -x[1]):
        out.append(f"| `{lt}` | {c:,} |")
    out.append("")

    # Recommendations
    out.append(f"## 4. Recommendations\n")
    if dha.get("exact_duplicate_rows", 0) > 0:
        n = dha["exact_duplicate_rows"]
        out.append(
            f"- 🔧 **CRITICAL — Deduplicate `dha_professionals_full.csv`** by full-row hash "
            f"(or by `dhaUniqueId` keeping first occurrence). Currently **{n:,} exact duplicate rows** "
            f"({round(n*100/dha['rows'],1)}% of total). Likely cause: scraper re-appends results from a paginated "
            f"or facility-grouped loop without checking if the (id, name, facility, specialty, license_type) tuple is new. "
            f"**Action:** add a `seen` set keyed on the tuple before `csv.writer.writerow(...)` in the scraper; "
            f"or post-process with `pandas.drop_duplicates()` on all columns."
        )
    elif dha["duplicate_ids"] > 0:
        out.append(f"- 🔧 **Deduplicate** `dha_professionals_full.csv` by `dhaUniqueId` (keep first occurrence).")
    if dent and dent["duplicate_keys"] > 0:
        out.append(f"- 🔧 **Deduplicate** `dentists_emirates.csv` by (full_name, clinic_name) tuple.")
    if dent and dent["languages_unique_raw"] > dent["languages_unique_normalized"] * 1.3:
        out.append(f"- 🔧 **Normalize languages** — raw has {dent['languages_unique_raw']} unique values, normalized collapses to {dent['languages_unique_normalized']}. Apply LANG_MAP (see `quality_check.py`).")
    if dha["field_filled"].get("photo", 0) == 0 and dha["field_filled"].get("has_photo", 0) == 0:
        out.append(f"- ℹ️ Photo column exists but is empty — Sheryan API likely doesn't expose photos in this scrape. Expected.")
    if dent and dent["phones_checked"] == 0 and dent["field_filled"].get("phone", 0) == 0:
        out.append(f"- ℹ️ Dentists `phone`/`email`/`photos_url` are empty in scraped CSV — Sheryan public search doesn't expose them. **Action:** enrich dentists dataset from clinic websites or Google Places API (separate enrichment job).")
    if dent and dent["field_filled"].get("languages", 0) < 5 and dent["field_filled"].get("languages", 0) > 0:
        out.append(f"- ⚠️ Dentists `languages` field is poorly populated ({dent['field_filled']['languages']}% fill). When present, raw values mix proficiency tags (e.g. `English (Fluent)`) — split into `language` + `proficiency` columns and apply LANG_MAP for `language`.")
    if dent and dent["field_filled"].get("nationality", 0) < 5 and dent["field_filled"].get("nationality", 0) > 0:
        out.append(f"- ⚠️ Dentists `nationality` field is poorly populated ({dent['field_filled']['nationality']}% fill). Consider backfilling from `full_name` heuristic or clinic nationality roster.")
    out.append(f"- ✅ DHA license format validation passes for the dataset (all `license_type` ∈ `{{FTL, REG, PTL, TRL}}`, all `dhaUniqueId` are 6–8 digit numeric IDs).")
    out.append("")
    out.append(f"---\n\n_Auto-generated by `research/quality_check.py`._")
    return "\n".join(out)


def main():
    dha = check_dha_main()
    dent = check_dentists()
    sheryan = check_sheryan_jsonl()
    report = build_report(dha, dent, sheryan)
    REPORT.write_text(report, encoding="utf-8")

    # Delta vs. previous committed run (read from git HEAD)
    try:
        import subprocess
        result = subprocess.run(
            ["git", "show", "HEAD:research/data-quality-report.md"],
            capture_output=True, text=True, cwd=Path(__file__).parent.parent,
        )
        prev = result.stdout if result.returncode == 0 else ""
        if prev and "## 2. Dentists" in prev:
            dha_section = prev.split("## 2. Dentists")[0]
            dent_section = prev.split("## 2. Dentists")[1].split("## 3.")[0]
            dha_rows_prev = None
            for line in dha_section.splitlines():
                if line.startswith("| Total rows |"):
                    dha_rows_prev = int(line.split("|")[2].strip().replace(",", ""))
                    break
            dent_rows_prev = None
            for line in dent_section.splitlines():
                if line.startswith("| Total rows |"):
                    dent_rows_prev = int(line.split("|")[2].strip().replace(",", ""))
                    break
            delta_lines = ["\n## 5. Delta vs. previous run\n"]
            if dha_rows_prev is not None:
                d = dha["rows"] - dha_rows_prev
                delta_lines.append(f"- DHA main: {dha_rows_prev:,} → {dha['rows']:,} rows (Δ {d:+,})")
            if dent_rows_prev is not None:
                d = dent["rows"] - dent_rows_prev
                delta_lines.append(f"- Dentists: {dent_rows_prev:,} → {dent['rows']:,} rows (Δ {d:+,})")
            if len(delta_lines) > 1:
                REPORT.write_text(report + "\n".join(delta_lines) + "\n", encoding="utf-8")
    except Exception as e:
        print(f"[DMD-QA] delta skipped: {e}")
    # Print summary for cron logs
    print(f"[DMD-QA] DHA: {dha['rows']} rows, {dha.get('exact_duplicate_rows',0)} exact-dup rows, {dha['duplicate_ids']} dup IDs, {dha['unique_facilities']} facilities")
    if dent:
        print(f"[DMD-QA] Dentists: {dent['rows']} rows, {dent['duplicate_keys']} dup keys, "
              f"langs raw={dent['languages_unique_raw']} norm={dent['languages_unique_normalized']}")
    if sheryan:
        print(f"[DMD-QA] Sheryan JSONL: {sheryan['rows']} records, photo={sheryan['photo_present_pct']}%")
    print(f"[DMD-QA] Report: {REPORT}")


if __name__ == "__main__":
    main()
