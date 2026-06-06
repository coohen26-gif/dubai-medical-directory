#!/usr/bin/env python3
"""
DMD — Cycle 11/30min (cron 6e3d697a-91cb-4475-872a-8ab965e7ba7f "Dubai - Translation & Localization") :
5 nouvelles fiches praticiens × 2 langues (FR→AR, FR→EN) = 10 traductions.

Source : data/dentists_emirates.csv (DHA Sheryan, 6186 dentistes uniques).
Méthode : translittération manuelle + glossary v1.0 (translations/glossary.md).
DeepL API key indisponible dans .env.translator (template) → translittération / table FR→X.
Schema v1.4 (2 langues cibles : AR + EN) — aligné spec cron « FR→AR + FR→EN ».

Continuité : cycle précédent 6e3d697a ; cycles parallèles ad25646f (5 langues).
Sélection : 5 fiches NON couvertes par les 65 fiches déjà livrées (cycles 1-10).

Livrables :
- translations/per_lang/dentist_{license}_{ar|en}.json (5 × 2 = 10 fichiers)
- translations/fiches-2026-06-06-cycle11.json (résumé)
- translations/build_cycle11.py (script, traçabilité)
"""
import csv
import json
import re
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent
SOURCE = WORKSPACE / "data" / "dentists_emirates.csv"
OUT_SUMMARY = ROOT / "fiches-2026-06-06-cycle11.json"
OUT_DIR = ROOT / "per_lang"
OUT_DIR.mkdir(exist_ok=True)
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
SCHEMA_VERSION = "1.4"
TARGET_FICHES = 5
LANGS = ["ar", "en"]

# === Glossaire 2 langues (aligné glossary.md v1.0) ===

SPECIALTY = {
    "General Dentist": {
        "slug": "general-dentist",
        "fr": "Dentiste généraliste",
        "ar": "طبيب أسنان عام",
        "en": "General Dentist",
    },
    "Orthodontist": {
        "slug": "orthodontist",
        "fr": "Orthodontiste",
        "ar": "أخصائي تقويم الأسنان",
        "en": "Orthodontist",
    },
    "Endodontist": {
        "slug": "endodontist",
        "fr": "Endodontiste",
        "ar": "أخصائي علاج العصب",
        "en": "Endodontist",
    },
    "Periodontist": {
        "slug": "periodontist",
        "fr": "Parodontiste",
        "ar": "أخصائي أمراض اللثة",
        "en": "Periodontist",
    },
    "Prosthodontist": {
        "slug": "prosthodontist",
        "fr": "Prosthodontiste",
        "ar": "أخصائي التركيبات السنية",
        "en": "Prosthodontist",
    },
    "Dental Implant": {
        "slug": "implantologist",
        "fr": "Implantologue",
        "ar": "أخصائي زراعة الأسنان",
        "en": "Implantologist",
    },
    "Oral Surgeon": {
        "slug": "oral-surgeon",
        "fr": "Chirurgien dentiste",
        "ar": "جراح الفم والأسنان",
        "en": "Oral Surgeon",
    },
    "Pediatric Dentist": {
        "slug": "pediatric-dentist",
        "fr": "Pédodontiste",
        "ar": "أخصائي أسنان الأطفال",
        "en": "Pediatric Dentist",
    },
    "Restorative Dentist": {
        "slug": "restorative-dentist",
        "fr": "Dentiste restaurateur",
        "ar": "طبيب ترميم الأسنان",
        "en": "Restorative Dentist",
    },
    "Specialist Dentist": {
        "slug": "specialist-dentist",
        "fr": "Dentiste spécialiste",
        "ar": "طبيب أسنان أخصائي",
        "en": "Specialist Dentist",
    },
}

LICENSE_TYPE = {
    "REG": {"fr": "Licence régulière", "ar": "رخصة منتظمة", "en": "Regular License"},
    "FTL": {"fr": "Temps plein", "ar": "دوام كامل", "en": "Full-Time License"},
    "PTL": {"fr": "Temps partiel", "ar": "دوام جزئي", "en": "Part-Time License"},
    "VIS": {"fr": "Visiteur", "ar": "زائر", "en": "Visiting License"},
}

COUNTRY = {
    "UAE": {"fr": "Émirats arabes unis", "ar": "الإمارات العربية المتحدة", "en": "United Arab Emirates"},
}
COUNTRY_SHORT = {
    "UAE": {"fr": "EAU", "ar": "الإمارات", "en": "UAE"},
}
CITY = {
    "Dubai": {"fr": "Dubaï", "ar": "دبي", "en": "Dubai"},
    "Abu Dhabi": {"fr": "Abu Dhabi", "ar": "أبوظبي", "en": "Abu Dhabi"},
    "Sharjah": {"fr": "Sharjah", "ar": "الشارقة", "en": "Sharjah"},
    "Ajman": {"fr": "Ajman", "ar": "عجمان", "en": "Ajman"},
}

# === Translittération nom propre (latin → AR) — table enrichie cycle 11 ===

AR_NAME_MAP = {
    "mohammed": "محمد", "mohamed": "محمد", "muhammad": "محمد", "muhammed": "محمد",
    "ahmed": "أحمد", "ahmad": "أحمد",
    "ali": "علي",
    "hassan": "حسن", "hasan": "حسن",
    "hussein": "حسين", "hussain": "حسين",
    "abdullah": "عبد الله", "abdul": "عبد",
    "khalid": "خالد", "khaled": "خالد",
    "yousef": "يوسف", "youssef": "يوسف", "yusuf": "يوسف", "josef": "يوسف", "joseph": "يوسف",
    "omar": "عمر", "umar": "عمر",
    "fatima": "فاطمة", "fatmeh": "فاطمة",
    "aisha": "عائشة", "aysha": "عائشة",
    "zeina": "زينة", "zaynab": "زينب", "zainab": "زينب",
    "sara": "سارة", "sarah": "سارة",
    "layla": "ليلى", "leila": "ليلى", "laila": "ليلى",
    "rana": "رنا", "reem": "ريم", "salma": "سلمى",
    "mariam": "مريم", "maryam": "مريم",
    "fadi": "فادي", "fady": "فادي",
    "issa": "عيسى", "isa": "عيسى",
    "ibrahim": "إبراهيم", "ebraheim": "إبراهيم",
    "yasser": "ياسر", "yaser": "ياسر",
    "tamer": "تامر",
    "ammar": "عمار", "amar": "عمار",
    "bassam": "بسام",
    "majd": "مجد", "majed": "ماجد",
    "feras": "فراس", "firas": "فراس",
    "ramzi": "رمزي", "ramzy": "رمزي",
    "sami": "سامي", "nabil": "نبيل", "wael": "وائل", "wail": "وائل",
    "khaled": "خالد", "khalil": "خليل",
    "samir": "سمير", "sameer": "سمير",
    "jaber": "جابر",
    "hamza": "حمزة", "hamzah": "حمزة",
    "zaid": "زيد", "zayed": "زايد",
    "mahmoud": "محمود", "mahmod": "محمود", "mahmood": "محمود",
    "mostafa": "مصطفى", "moustafa": "مصطفى", "mustafa": "مصطفى",
    "ashraf": "أشرف",
    "emad": "عماد", "imad": "عماد",
    "hisham": "هشام", "hesham": "هشام",
    "mazen": "مازن",
    "ayman": "أيمن", "aiman": "أيمن",
    "nader": "نادر", "nadir": "نادر",
    "ramy": "رامي", "rami": "رامي",
    "diana": "ديانا",
    "lina": "لينا", "leena": "لينا",
    "noor": "نور", "nour": "نور",
    "hala": "هالة",
    "ghada": "غادة",
    "dina": "دينا",
    "eman": "إيمان", "iman": "إيمان",
    "asma": "أسماء",
    "amira": "أميرة", "ameera": "أميرة",
    "hanan": "حنان",
    "abeer": "عبير",
    "noura": "نورة", "noora": "نورة",
    "rashid": "راشد",
    "latifa": "لطيفة", "latifah": "لطيفة",
    "hind": "هند", "amal": "أمل", "salem": "سالم",
    "elias": "إلياس", "elie": "إلي",
    "george": "جورج", "georges": "جورج",
    "paul": "بول", "pierre": "بيير",
    "marie": "ماري", "rita": "ريتا", "nina": "نينا",
    "walid": "وليد", "waleed": "وليد",
    "kareem": "كريم", "karim": "كريم",
    "faisal": "فيصل", "faysal": "فيصل",
    "sultan": "سلطان", "nasser": "ناصر", "naser": "ناصر",
    "samer": "سامر", "hadi": "هادي",
    "ghassan": "غسان", "ghasan": "غسان",
    "mohannad": "مهند", "muhanad": "مهند",
    "nawaf": "نواف", "turki": "تركي", "saud": "سعود",
    "abdulrahman": "عبد الرحمن", "abdelrahman": "عبد الرحمن",
    "abdulaziz": "عبد العزيز",
    "haitham": "هيثم", "haitham": "هيثم",
    "hazem": "حازم",
    "suzanna": "سوزانا", "suzan": "سوزان", "suzanne": "سوزان",
    "sina": "سينا",
    "mokhtarian": "مختاریان", "razyanfard": "رازيانفارد",
    "elbishari": "البشيري",
    "almaali": "المعالي",
    "fatemeh": "فاطمة",
    "razyan": "رازيان",
    "sara": "سارة",
}

# === Bio template par langue (2 langues cibles) ===

def bio(fr_name, fr_spec, fr_city, fr_lic, langs_iso, lang):
    iso = ", ".join(langs_iso) if langs_iso else "en"
    if lang == "ar":
        # Structure : "{ar_name} {ar_spec_phrase} في {ar_city}، الإمارات. ..."
        # "الدكتور" est le préfixe honorifique, placé devant le nom translittéré.
        return f"الدكتور {ar_name_only(fr_name)} {ar_spec_phrase(fr_spec)} في {ar_city(fr_city)}، الإمارات. يحمل رخصة {ar_lic(fr_lic)} صادرة عن هيئة الصحة بدبي (DHA). لغات العمل: {iso}."
    if lang == "en":
        # Règle a/an : voyelle initiale phonétique → "an" ; sinon "a".
        spec_en = en_spec(fr_spec)
        article = "an" if spec_en[:1].lower() in ("a", "e", "i", "o", "u") else "a"
        return f"Dr. {fr_name} is {article} {spec_en} based in {fr_city}, UAE. Holds a {en_lic(fr_lic)} issued by the Dubai Health Authority (DHA). Working languages: {iso}."

# === Helpers bio ===

def ar_name_only(name):
    # Renvoie le nom translittéré en arabe (le titre "الدكتور" est ajouté en amont dans bio()).
    return name

def ar_spec_phrase(fr):
    return {
        "Dentiste généraliste": "طبيب أسنان عام",
        "Orthodontiste": "أخصائي تقويم الأسنان",
        "Endodontiste": "أخصائي علاج العصب",
        "Parodontiste": "أخصائي أمراض اللثة",
        "Prosthodontiste": "أخصائي التركيبات السنية",
        "Implantologue": "أخصائي زراعة الأسنان",
        "Chirurgien dentiste": "جراح الفم والأسنان",
        "Pédodontiste": "أخصائي أسنان الأطفال",
        "Dentiste restaurateur": "طبيب ترميم الأسنان",
        "Dentiste spécialiste": "طبيب أسنان أخصائي",
    }.get(fr, "طبيب أسنان")

def ar_city(fr):
    return {"Dubaï": "دبي", "Abu Dhabi": "أبوظبي", "Sharjah": "الشارقة", "Ajman": "عجمان"}.get(fr, fr)

def ar_lic(fr):
    return {"Temps plein": "دوام كامل", "Temps partiel": "دوام جزئي",
            "Licence régulière": "رخصة منتظمة", "Visiteur": "زائر"}.get(fr, fr)

def en_spec(fr):
    return {
        "Dentiste généraliste": "General Dentist",
        "Orthodontiste": "Orthodontist",
        "Endodontiste": "Endodontist",
        "Parodontiste": "Periodontist",
        "Prosthodontiste": "Prosthodontist",
        "Implantologue": "Implantologist",
        "Chirurgien dentiste": "Oral Surgeon",
        "Pédodontiste": "Pediatric Dentist",
        "Dentiste restaurateur": "Restorative Dentist",
        "Dentiste spécialiste": "Specialist Dentist",
    }.get(fr, "Dentist")

def en_lic(fr):
    return {"Temps plein": "Full-Time License", "Temps partiel": "Part-Time License",
            "Licence régulière": "Regular License", "Visiteur": "Visiting License"}.get(fr, fr)

# === Translittération multi-langue ===

def normalize(s):
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower().strip()

def transliterate_name(full_name, lang):
    """Translittère nom latin → script cible.
    - ar : table AR_NAME_MAP token par token, fallback = nom original
    """
    if not full_name:
        return ""
    tokens = re.split(r"\s+", full_name.strip())
    if lang == "ar":
        out = []
        for t in tokens:
            key = normalize(t)
            if key in AR_NAME_MAP:
                out.append(AR_NAME_MAP[key])
            else:
                out.append(t)
        return " ".join(out)
    return full_name

# === Slug ID ===

def slugify(name):
    s = normalize(name)
    s = re.sub(r"[^a-z0-9]+", "-", s).strip("-")
    return s or "unknown"

# === Charge les fiches déjà traduites (skip) ===

def load_already_done():
    done = set()
    for f in (ROOT.glob("fiches-*.json")):
        try:
            d = json.load(open(f))
            for x in d.get("fiches", []):
                done.add(x["license_number"])
        except Exception:
            pass
    return done

# === Lecture CSV + dédup ===

def load_csv():
    rows = []
    seen = set()
    with open(SOURCE, newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            k = row["license_number"]
            if k in seen:
                continue
            seen.add(k)
            rows.append(row)
    return rows

# === Sélection des 5 fiches ===

def select_fiches(rows, already, n=5):
    """Mix 5 fiches : 1 Orthodontist + 1 Endodontist + 1 Prosthodontist + 2 Dental Implant."""
    target_mix = [
        ("Orthodontist", 1),
        ("Endodontist", 1),
        ("Prosthodontist", 1),
        ("Dental Implant", 2),
    ]
    buckets = {}
    for r in rows:
        sp = r["specialty"]
        buckets.setdefault(sp, []).append(r)

    selected = []
    seen_local = set()
    for specialty, count in target_mix:
        pool = buckets.get(specialty, [])
        for r in pool:
            if r["license_number"] in already or r["license_number"] in seen_local:
                continue
            selected.append(r)
            seen_local.add(r["license_number"])
            if len([x for x in selected if x["specialty"] == specialty]) >= count:
                break
    return selected[:n]

# === Génération fiche ===

def build_fiche(row, langs):
    license_number = row["license_number"]
    full_name = row["full_name"].strip()
    specialty_en = row["specialty"].strip()
    license_code = row.get("license_type", "FTL").strip() or "FTL"
    facility = row.get("clinic_name", "").strip()
    area_en = row.get("address", "").strip() or "Dubai"
    city_en = "Dubai"
    for c in ("Dubai", "Abu Dhabi", "Sharjah", "Ajman"):
        if c.lower() in area_en.lower():
            city_en = c
            break

    spec = SPECIALTY.get(specialty_en)
    if not spec:
        spec = SPECIALTY["General Dentist"]

    lic = LICENSE_TYPE.get(license_code, LICENSE_TYPE["FTL"])

    name_dict = {
        "original": full_name,
        "fr": full_name.title() if full_name.isupper() else full_name,
        "ar": transliterate_name(full_name, "ar"),
        "en": full_name.title() if full_name.isupper() else full_name,
    }

    specialty_dict = {
        "slug": spec["slug"],
        "fr": spec["fr"],
        "ar": spec["ar"],
        "en": spec["en"],
    }
    license_dict = {
        "code": license_code,
        "fr": lic["fr"],
        "ar": lic["ar"],
        "en": lic["en"],
    }
    facility_dict = {l: facility for l in langs}
    city_dict = {
        "fr": {"Dubai": "Dubaï", "Abu Dhabi": "Abu Dhabi",
               "Sharjah": "Sharjah", "Ajman": "Ajman"}.get(city_en, city_en),
        "ar": CITY.get(city_en, {}).get("ar", city_en),
        "en": city_en,
    }
    country_dict = {l: COUNTRY["UAE"][l] for l in langs}
    country_short_dict = {l: COUNTRY_SHORT["UAE"][l] for l in langs}

    bio_dict = {
        lang: bio(
            name_dict["fr"] if lang == "en" else name_dict["ar"],
            spec["fr"], city_dict["fr"], lic["fr"], ["en", "ar"], lang
        )
        for lang in langs
    }

    fiche = {
        "id": f"{slugify(full_name)}-{license_number}",
        "license_number": license_number,
        "license_type": license_dict,
        "name": name_dict,
        "specialty": specialty_dict,
        "sub_specialty": None,
        "facility": facility_dict,
        "area": {
            "original": area_en,
            "fr": area_en,
            "ar": area_en,
            "en": area_en,
        },
        "city": city_dict,
        "country": country_dict,
        "country_short": country_short_dict,
        "category": "dentists",
        "bio": bio_dict,
        "services": None,
        "languages_spoken": ["ar", "en"],
        "_provenance": {
            "source_csv": "data/dentists_emirates.csv",
            "source_url": row.get("source_url", ""),
            "scraped_at": row.get("scraped_at", ""),
        },
        "_gender_heuristic": "unknown",
        "translated_at": NOW,
        "schema_version": SCHEMA_VERSION,
    }
    return fiche

# === Génération du fichier par-langue (AR / EN) ===

def project_lang(fiche, lang):
    """Réduit une fiche à la version monolingue demandée (AR ou EN)."""
    keys = ["id", "license_number", "license_type", "name", "specialty", "sub_specialty",
            "facility", "area", "city", "country", "country_short", "category",
            "bio", "services", "languages_spoken", "schema_version", "translated_at"]
    out = {k: fiche[k] for k in keys if k in fiche}
    for mk in ("license_type", "name", "specialty", "facility", "city",
               "country", "country_short", "bio"):
        if mk in out and isinstance(out[mk], dict):
            if "ar" in out[mk] or "en" in out[mk]:
                if "original" in out[mk]:
                    out[mk] = {"original": out[mk]["original"], lang: out[mk].get(lang, "")}
                else:
                    out[mk] = out[mk].get(lang, "")
    if "area" in out and isinstance(out["area"], dict):
        out["area"] = out["area"].get(lang) or out["area"].get("original", "")
    out["_lang"] = lang
    out["_provenance"] = fiche.get("_provenance", {})
    return out

# === Main ===

def main():
    already = load_already_done()
    print(f"[cycle11] fiches déjà traduites : {len(already)}")
    rows = load_csv()
    print(f"[cycle11] CSV chargé : {len(rows)} dentistes uniques")

    selected = select_fiches(rows, already, n=TARGET_FICHES)
    print(f"[cycle11] sélectionnées : {len(selected)} fiches")
    mix = {}
    for r in selected:
        mix[r["specialty"]] = mix.get(r["specialty"], 0) + 1
    print(f"[cycle11] mix spécialités : {mix}")

    fiches_full = []
    per_lang_count = {l: 0 for l in LANGS}
    files_written = []

    for r in selected:
        f = build_fiche(r, LANGS)
        fiches_full.append(f)
        for lang in LANGS:
            out_path = OUT_DIR / f"dentist_{r['license_number']}_{lang}.json"
            payload = project_lang(f, lang)
            out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            files_written.append(str(out_path.relative_to(ROOT)))
            per_lang_count[lang] += 1

    summary = {
        "_meta": {
            "schema_version": SCHEMA_VERSION,
            "generated_at": NOW,
            "generator": "build_cycle11.py",
            "cron": "6e3d697a-91cb-4475-872a-8ab965e7ba7f",
            "cron_name": "Dubai - Translation & Localization",
            "cycle": "2026-06-06 cycle 11/30min",
            "languages_count": len(LANGS),
            "languages": LANGS,
            "translation_direction": "FR→AR + FR→EN",
            "target_fiches": TARGET_FICHES,
            "fiches_produced": len(fiches_full),
            "translations_produced": len(fiches_full) * len(LANGS),
            "specialty_mix": mix,
            "per_lang_count": per_lang_count,
            "per_lang_files": len(files_written),
            "source_csv": str(SOURCE.relative_to(WORKSPACE)),
            "glossary_version": "v1.0 (cycle11 subset AR+EN)",
            "deepl_used": False,
            "deepl_note": "DEEPL_API_KEY vide dans .env.translator (template) → translittération manuelle + table FR→X alignée glossary.md",
        },
        "fiches": fiches_full,
    }
    OUT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[cycle11] résumé → {OUT_SUMMARY.relative_to(ROOT)}")
    print(f"[cycle11] fichiers per-lang → {len(files_written)} ({per_lang_count})")
    return summary

if __name__ == "__main__":
    main()
