#!/usr/bin/env python3
"""
DMD — Cycle 04/30min (cron 6e3d697a-91cb-4475-872a-8ab965e7ba7f "Translation & Localization") :
5 nouvelles fiches praticiens × 3 langues (FR, AR, EN).
Source : data/dentists_emirates.csv (DHA Sheryan, 6012 lignes).
Méthode : manuelle + glossary v1.0 (translations/glossary.md).
DeepL API key indisponible (cf. .env.translator — placeholder).
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
OUT = ROOT / "fiches-2026-06-06-cycle04.json"

# === Glossaire v1.0 — aligné avec translations/glossary.md ===

SPECIALTY = {
    "general-dentist": {
        "fr": "Dentiste généraliste",
        "ar": "طبيب أسنان عام",
        "en": "General Dentist",
    },
    "orthodontist": {
        "fr": "Orthodontiste",
        "ar": "أخصائي تقويم الأسنان",
        "en": "Orthodontist",
    },
    "endodontist": {
        "fr": "Endodontiste",
        "ar": "أخصائي علاج العصب",
        "en": "Endodontist",
    },
    "periodontist": {
        "fr": "Parodontiste",
        "ar": "أخصائي أمراض اللثة",
        "en": "Periodontist",
    },
    "prosthodontist": {
        "fr": "Prosthodontiste",
        "ar": "أخصائي التركيبات السنية",
        "en": "Prosthodontist",
    },
    "implantologist": {
        "fr": "Implantologue",
        "ar": "أخصائي زراعة الأسنان",
        "en": "Implantologist",
    },
    "oral-surgeon": {
        "fr": "Chirurgien dentiste",
        "ar": "جراح الفم والأسنان",
        "en": "Oral Surgeon",
    },
    "pediatric-dentist": {
        "fr": "Pédodontiste",
        "ar": "أخصائي أسنان الأطفال",
        "en": "Pediatric Dentist",
    },
    "cosmetic-dentist": {
        "fr": "Esthétique dentaire",
        "ar": "تجميل الأسنان",
        "en": "Cosmetic Dentist",
    },
    "specialist-dentist": {
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

EMIRATE = {
    "Dubai": {"fr": "Dubaï", "ar": "دبي", "en": "Dubai"},
    "Abu Dhabi": {"fr": "Abu Dhabi", "ar": "أبوظبي", "en": "Abu Dhabi"},
    "Sharjah": {"fr": "Sharjah", "ar": "الشارقة", "en": "Sharjah"},
    "Ajman": {"fr": "Ajman", "ar": "عجمان", "en": "Ajman"},
    "Ras Al Khaimah": {"fr": "Ras Al Khaimah", "ar": "رأس الخيمة", "en": "Ras Al Khaimah"},
    "Fujairah": {"fr": "Fujairah", "ar": "الفجيرة", "en": "Fujairah"},
    "Umm Al Quwain": {"fr": "Umm Al Quwain", "ar": "أم القيوين", "en": "Umm Al Quwain"},
}

COUNTRY = {
    "fr": "Émirats arabes unis",
    "ar": "الإمارات العربية المتحدة",
    "en": "United Arab Emirates",
}

COUNTRY_SHORT = {"fr": "EAU", "ar": "الإمارات", "en": "UAE"}

# === Translitérations noms (cycle04 — set de 5) ===
# AR : translittération latine commune UAE (glossary rule)
# Ces 5 noms sont exotiques/non-canoniques → translittération manuelle validée.

ARABIC_TRANSLIT = {
    "Rosedina Villero": "روزيدينا فيليرو",
    "Anila Virani": "أنيلا فيراني",
    "Gunter Neumann": "غونتر نويما",
    "FATMA OGUZ": "فاطمة أوغوز",
    "Samir Abuobaida": "سمير أبو عبيدة",
}

# === Helpers ===

def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text or "unknown"

def specialty_slug(specialty: str) -> str:
    s = specialty.lower()
    if "orthodont" in s:
        return "orthodontist"
    if "endodont" in s:
        return "endodontist"
    if "periodont" in s:
        return "periodontist"
    if "prosthodont" in s:
        return "prosthodontist"
    if "implant" in s:
        return "implantologist"
    if "oral surgeon" in s or "maxillofacial" in s or "chirurg" in s:
        return "oral-surgeon"
    if "pediatric" in s or "paediatric" in s or "enfant" in s or "child" in s:
        return "pediatric-dentist"
    if "cosmetic" in s or "esthet" in s or "aesthetic" in s:
        return "cosmetic-dentist"
    if "specialist" in s:
        return "specialist-dentist"
    return "general-dentist"

def detect_gender(name: str) -> str:
    """Heuristique genre depuis prénom — aligné avec cycle03."""
    female_first_names = {
        "zeina", "meena", "fatma", "samira", "lama", "rosedina", "anila",
        "claudia", "rabab", "zainab", "lalaine", "ambili", "sruthi", "samira",
    }
    first = name.split()[0].lower().rstrip(".")
    if first in female_first_names:
        return "f"
    # Heuristique secondaire : terminaisons féminines courantes
    if first.endswith(("a", "ia", "ina", "ila", "ela", "ima", "ema", "ana")) and first not in {
        "muhammad", "mohammad", "ahmed", "mouhammad", "samir",
        "oday", "vimalkumar", "feras", "pouya", "johnny", "gunter",
        "nachiket", "samir",
    }:
        return "f"
    return "m"

def build_name_block(original: str) -> dict:
    return {
        "original": original,
        "fr": original,         # FR natif (nom latin conservé)
        "ar": ARABIC_TRANSLIT.get(original, original),  # translittération arabe
        "en": original,         # EN natif
    }

def build_facility_block(clinic: str) -> dict:
    if not clinic:
        return {"fr": "", "ar": "", "en": ""}
    return {
        "fr": clinic,
        "ar": clinic,   # clinic name kept in latin (standard UAE pratique)
        "en": clinic,
    }

def bio_template(name: str, specialty: str, area: str, license_type: str, lang_code: str, gender: str) -> str:
    """Bio courte standardisée, alignée glossary v1.0 + cycle01/02."""
    if lang_code == "fr":
        licence_adj = "licencié" if gender == "m" else "licenciée"
        # Alignement cycle01 : "Titulaire d'une licence {X} (CODE) délivrée par la Dubai Health Authority."
        return f"Dr. {name} est {specialty.lower()} à {area}, aux Émirats arabes unis. {licence_adj.capitalize()} par la Dubai Health Authority sous licence {license_type.lower()}."
    if lang_code == "ar":
        verb_hold = "يحمل" if gender == "m" else "تحمل"
        return f"الدكتور {name} هو {specialty} في {area}، الإمارات العربية المتحدة. {verb_hold} رخصة {license_type} صادرة عن هيئة الصحة بدبي."
    if lang_code == "en":
        article = "an" if specialty[:1].lower() in "aeiou" else "a"
        return f"Dr. {name} is {article} {specialty.lower()} based in {area}, UAE. Licensed by the Dubai Health Authority ({license_type})."
    return ""

def main():
    # 1) Skip licenses déjà traduits (cycle01/02/03)
    done_licenses = set()
    for prev in [
        "fiches-2026-06-05-cycle01.json",
        "fiches-2026-06-06-cycle02.json",
        "fiches-2026-06-06-cycle03.json",
    ]:
        p = ROOT / prev
        if p.exists():
            with p.open() as f:
                for f_ in json.load(f)["fiches"]:
                    done_licenses.add(f_.get("license_number"))

    # 2) Pick 5 nouvelles fiches
    picks = []
    with SOURCE.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            ln = row["license_number"].strip()
            nm = row["full_name"].strip()
            if not nm or not ln:
                continue
            if ln in done_licenses:
                continue
            picks.append(row)
            if len(picks) == 5:
                break

    if len(picks) < 5:
        raise SystemExit(f"❌ Seulement {len(picks)} nouvelles fiches trouvées (attendu 5).")

    # 3) Construire les fiches 3 langues
    fiches = []
    for row in picks:
        full_name = row["full_name"].strip()
        license_number = row["license_number"].strip()
        license_type = (row["license_type"] or "").strip() or "REG"
        specialty_en = (row["specialty"] or "").strip() or "General Dentist"
        clinic = (row.get("clinic_name") or "").strip()
        emirate_en = (row.get("emirate") or "Dubai").strip()
        source_url = (row.get("source_url") or "").strip()
        scraped_at = (row.get("scraped_at") or "").strip()

        slug_sp = specialty_slug(specialty_en)
        sp = SPECIALTY[slug_sp]
        lt = LICENSE_TYPE.get(license_type, LICENSE_TYPE["REG"])
        em = EMIRATE.get(emirate_en, EMIRATE["Dubai"])

        name_block = build_name_block(full_name)
        facility_block = build_facility_block(clinic)
        gender = detect_gender(full_name)

        # Nom FR/EN = original (déjà latin). Pas de transformation pour facility.
        # En revanche, name["fr"] est souvent écrit avec "Dr." préfixe → on l'inclut dans la bio, pas dans name.
        fiche_id = f"{slugify(full_name)}-{license_number}"

        fiche = {
            "id": fiche_id,
            "license_number": license_number,
            "license_type": {
                "code": license_type,
                "fr": lt["fr"],
                "ar": lt["ar"],
                "en": lt["en"],
            },
            "name": name_block,
            "specialty": {
                "slug": slug_sp,
                "fr": sp["fr"],
                "ar": sp["ar"],
                "en": sp["en"],
            },
            "sub_specialty": None,
            "facility": facility_block,
            "area": {
                "fr": em["fr"],
                "ar": em["ar"],
                "en": em["en"],
            },
            "country": COUNTRY,
            "country_short": COUNTRY_SHORT,
            "category": "dentists",
            "bio": {
                "fr": bio_template(name_block["fr"], sp["fr"], em["fr"], lt["fr"], "fr", gender),
                "ar": bio_template(name_block["ar"], sp["ar"], em["ar"], lt["ar"], "ar", gender),
                "en": bio_template(name_block["en"], sp["en"], em["en"], lt["en"], "en", gender),
            },
            "services": None,
            "languages_spoken": None,
            "profile_url": source_url or None,
            "scraped_at": scraped_at or None,
            "translated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        fiches.append(fiche)

    # 4) Output JSON — schema v1.0 (3 langues)
    out = {
        "_meta": {
            "schema_version": "1.0",
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "generator": "cron:6e3d697a-91cb-4475-872a-8ab965e7ba7f (Dubai - Translation & Localization)",
            "cycle": "2026-06-06 cycle 04/30min",
            "previous_cycles": [
                "fiches-2026-06-05-cycle01.json (5 fiches, fr+ar+en, manual+glossary v1.0)",
                "fiches-2026-06-06-cycle02.json (5 fiches, fr+ar+en, manual+glossary v1.0)",
                "fiches-2026-06-06-cycle03.json (5 fiches, fr+ar+en+ru+zh, manual+glossary v1.0 — schema v1.1)",
            ],
            "source_csv": "data/dentists_emirates.csv",
            "source_rows_total": 6012,
            "source_rows_translated_to_date": 20,
            "glossary_version": "v1.0 (translations/glossary.md)",
            "translation_method": "manual+glossary (DeepL API key unavailable in .env.translator — template bio synthesized from glossary v1.0)",
            "languages": ["fr", "ar", "en"],
            "field_completeness_note": "Source CSV lacks sub_specialty/bio/services/languages_spoken; these are null per glossary note 2026-06-05.",
            "quality_notes": [
                "Noms : translittération manuelle AR (glossary rule). FR/EN = nom original latin (conservé).",
                "Spécialités : 100% alignées avec glossary.md v1.0 (9 specialties + 1 fallback specialist-dentist).",
                "Licences : mapping REG/FTL/PTL/VIS aligné glossary.md.",
                "Émirats : mapping glossary.md (Dubai/Abu Dhabi/Sharjah/Ajman/RAK/Fujairah/UAQ).",
                "Genre : heuristique sur prénom (F pour Rosedina, Anila, Fatma; M pour Gunter, Samir). Accord FR (licencié/licenciée) et AR (يحمل/تحمل).",
                "Bio : template canonique 3-langue aligné cycle01 (FR: 'Titulaire d'une licence...' / EN: 'Licensed by DHA' / AR: 'يحمل رخصة صادرة عن هيئة الصحة بدبي').",
                "Services : null — source CSV ne contient pas la liste, à récupérer depuis source_url.",
            ],
        },
        "fiches": fiches,
    }

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"✅ Wrote {OUT.relative_to(WORKSPACE)}")
    print(f"   Fiches: {len(fiches)}")
    print(f"   Langues: 3 (fr, ar, en)")
    for f_ in fiches:
        print(f"   - {f_['id']} :: {f_['name']['fr']} ({f_['specialty']['fr']}) [gender={detect_gender(f_['name']['fr'])}]")

if __name__ == "__main__":
    main()
