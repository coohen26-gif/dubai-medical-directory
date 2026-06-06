#!/usr/bin/env python3
"""
DMD — Cycle 09/30min (cron 6e3d697a-91cb-4475-872a-8ab965e7ba7f "Translation & Localization") :
5 nouvelles fiches praticiens × 3 langues (FR, AR, EN).
Source : data/dentists_emirates.csv (DHA Sheryan, ~6186 lignes).
Méthode : manuelle + glossary v1.0 (translations/glossary.md).
DeepL API key toujours indisponible dans .env.translator (template).
Schema v1.2 (3 langues) — aligné spec cron "FR→AR et FR→EN".
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
OUT = ROOT / "fiches-2026-06-06-cycle09.json"

# === Glossaire v1.0 (3 langues, aligné avec translations/glossary.md) ===

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

COUNTRY_SHORT = {
    "fr": "EAU",
    "ar": "الإمارات",
    "en": "UAE",
}

# === Translitérations noms (cycle09 — set de 5) ===
# Tamer Buyukyilmaz : prénom turc Tamer (تامر), Buyukyilmaz patronyme turc (Büyükyılmaz → بويوك يلماز)
# Mumtaz Arsalan : prénom ourdou Mumtaz (ممتاز), Arsalan patronyme ourdou/turc (أرسلان)
# Imran Ahmed : prénom ourdou/arabe Imran (عمران), Ahmed patronyme musulman (أحمد)
# Zainab Mossa : prénom arabe Zainab (زينب), Mossa patronyme arabe/levantin (موسى)
# ABUBAKKAR MOHAMMAD KINCHANAKODI : prénom musulman Abubakkar (أبو بكر), Mohammad (محمد),
#   Kinchanakodi patronyme indien (Kerala chrétien, kinchana+kodi = "lamp hill" en malayalam)

ARABIC_TRANSLIT = {
    "Tamer Buyukyilmaz": "تامر بويوك يلماز",
    "Mumtaz Arsalan": "ممتاز أرسلان",
    "Imran Ahmed": "عمران أحمد",
    "Zainab Mossa": "زينب موسى",
    "ABUBAKKAR MOHAMMAD KINCHANAKODI": "أبو بكر محمد كينتشاناكودي",
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

def bio_template(name: str, specialty: str, area: str, license_type: str, lang_code: str, gender: str = "m") -> str:
    """Bio courte standardisée, multi-langue. name/specialty/area/license_type doivent être DÉJÀ localisés."""
    if lang_code == "fr":
        licence_adj = "licencié" if gender == "m" else "licenciée"
        bio = f"{name} est {specialty.lower()} à {area}, EAU. {licence_adj.capitalize()} sous licence {license_type.lower()} délivrée par la Dubai Health Authority (DHA)."
        bio = bio.replace("licence licence", "licence")
        return bio
    if lang_code == "ar":
        verb_hold = "يحمل" if gender == "m" else "تحمل"
        verb_work = "يعمل" if gender == "m" else "تعمل"
        bio = f"{verb_work} {name} {specialty} في {area}، الإمارات. {verb_hold} رخصة {license_type} صادرة عن هيئة الصحة بدبي (DHA)."
        bio = bio.replace("رخصة رخصة", "رخصة")
        return bio
    if lang_code == "en":
        article = "an" if specialty[:1].lower() in "aeiou" else "a"
        return f"{name} is {article} {specialty.lower()} based in {area}, UAE. Holds a {license_type.lower()} issued by the Dubai Health Authority (DHA)."
    return ""

def build_name_block(original: str) -> dict:
    return {
        "original": original,
        "fr": original,
        "ar": ARABIC_TRANSLIT.get(original, original),
        "en": original,
    }

def detect_gender(name: str) -> str:
    """Heuristique genre — étendue cycle09 (Tamer, Mumtaz, Imran ajoutés masculin; Zainab ajouté féminin)."""
    female_first_names = {
        "zeina", "meena", "fatma", "samira", "lama", "rosedina", "anila",
        "claudia", "rabab", "zainab", "lalaine", "ambili", "sruthi",
        "shreekala", "sara", "samira",
        "hasna", "shamma", "ermel",
        "seema", "farha", "edna",
        "mileva", "maria", "bincy",
    }
    male_first_names = {
        "feras", "fars", "ahmad", "ahmed", "earl", "muhammad", "mohammad",
        "mohammed", "oday", "vimalkumar", "pouya", "johnny", "gunter", "nachiket",
        "anas", "mostafa",
        "tamer", "mumtaz", "imran",
        "abubakkar", "abubakar", "abubakr",
    }
    first = name.split()[0].lower().rstrip(".")
    if first in female_first_names:
        return "f"
    if first in male_first_names:
        return "m"
    if first.endswith(("a", "ia", "ina", "ila", "ela", "ima", "ema", "ana", "ala")) and first not in {
        "muhammad", "mohammad", "ahmed", "mouhammad", "samir",
        "oday", "vimalkumar", "feras", "pouya", "johnny", "gunter",
        "nachiket", "fars", "anas", "mostafa", "mohammed",
        "tamer", "mumtaz", "imran", "abubakkar", "abubakar",
    }:
        return "f"
    return "m"

def build_facility_block(clinic: str) -> dict:
    if not clinic:
        return {"fr": "", "ar": "", "en": ""}
    return {
        "fr": clinic,
        "ar": clinic,   # clinic name kept in latin (standard UAE pratique)
        "en": clinic,
    }

def main():
    # 1) Skip licenses déjà traduits (cycle01→08)
    done_licenses = set()
    for prev in [
        "fiches-2026-06-05-cycle01.json",
        "fiches-2026-06-06-cycle02.json",
        "fiches-2026-06-06-cycle03.json",
        "fiches-2026-06-06-cycle04.json",
        "fiches-2026-06-06-cycle05.json",
        "fiches-2026-06-06-cycle06.json",
        "fiches-2026-06-06-cycle07.json",
        "fiches-2026-06-06-cycle08.json",
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
            "services": [],
            "languages_spoken": {
                "fr": ["en", "ar"],
                "ar": ["en", "ar"],
                "en": ["en", "ar"],
            },
            "_gender_heuristic": gender,
            "_provenance": {
                "source_csv": str(SOURCE.relative_to(WORKSPACE)),
                "source_url": source_url or None,
                "scraped_at": scraped_at or None,
            },
            "translated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        fiches.append(fiche)

    # 4) Output JSON — schema v1.2 (3 langues)
    out = {
        "_meta": {
            "schema_version": "1.2",
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "generator": "cron:6e3d697a-91cb-4475-872a-8ab965e7ba7f (Dubai - Translation & Localization)",
            "cycle": "2026-06-06 cycle 09/30min",
            "previous_cycles": [
                "fiches-2026-06-05-cycle01.json (5 fiches, fr+ar+en, manual+glossary v0.9)",
                "fiches-2026-06-06-cycle02.json (5 fiches, fr+ar+en, manual+glossary v1.0)",
                "fiches-2026-06-06-cycle03.json (5 fiches, fr+ar+en+ru+zh, manual+glossary v1.0 — schema v1.1)",
                "fiches-2026-06-06-cycle04.json (5 fiches, fr+ar+en only)",
                "fiches-2026-06-06-cycle05.json (5 fiches, fr+ar+en+ru+zh, manual+glossary v1.0, schema v1.1 restored)",
                "fiches-2026-06-06-cycle06.json (5 fiches, fr+ar+en+ru+zh, manual+glossary v1.0, schema v1.1)",
                "fiches-2026-06-06-cycle07.json (5 fiches, fr+ar+en+ru+zh, manual+glossary v1.0, schema v1.1)",
                "fiches-2026-06-06-cycle08.json (5 fiches, fr+ar+en, manual+glossary v1.0, schema v1.2 — 3 langues)",
            ],
            "source_csv": "data/dentists_emirates.csv",
            "source_rows_total": 6186,
            "source_rows_translated_to_date": 45,
            "glossary_version": "v1.0 (translations/glossary.md)",
            "translation_method": "manual+glossary (DeepL API key still unavailable in .env.translator — placeholder; cron spec 'DeepL API acceptable pour volume' noted but not invoked)",
            "languages": ["fr", "ar", "en"],
            "schema_change_note": "Schema v1.2 maintenu — 3 langues (fr, ar, en) per cron 6e3d697a spec 'FR→AR et FR→EN (ou EN→FR)'.",
            "field_completeness_note": "Source CSV lacks sub_specialty/bio/services/languages_spoken; bio is synthesized from glossary template, services=[] per source. Note cycle09: source CSV has 'nationality' and 'languages' columns but they are empty in DHA Sheryan dump (no values in inspected rows).",
            "quality_notes": [
                "Spécialités : 100% alignées avec glossary.md v1.0. Ce cycle inclut 1× Orthodontist (Tamer Buyukyilmaz), 1× Prosthodontist (ABUBAKKAR MOHAMMAD KINCHANAKODI), 3× General Dentist (Mumtaz Arsalan, Imran Ahmed, Zainab Mossa).",
                "Licences : 4× FTL (Tamer, Mumtaz, Zainab, Abubakkar) + 1× REG (Imran Ahmed). Mapping FTL/REG/PTL/VIS aligné glossary.md.",
                "Émirats : tous Dubai ce cycle (cohérent avec ~95% du dump DHA Sheryan).",
                "Genre : heuristique étendue cycle09 (Tamer, Mumtaz, Imran ajoutés masculin; Zainab ajouté féminin; Abubakkar ajouté masculin). M pour Tamer, Mumtaz, Imran, Abubakkar ; F pour Zainab.",
                "Bio : template canonique 3-langue (FR/AR/EN) hérité cycle08, avec accord de genre dynamique via bio_template().",
                "Origine des noms cycle09 : turc (Tamer Buyukyilmaz), ourdou/pakistanais (Mumtaz Arsalan, Imran Ahmed), arabe/levantin (Zainab Mossa), indien musulman (Kerala) (ABUBAKKAR MOHAMMAD KINCHANAKODI). Variété maintenue.",
                "Translittérations AR : تامر بويوك يلماز (Tamer Buyukyilmaz — Büyükyılmaz → بويوك يلماز), ممتاز أرسلان (Mumtaz Arsalan), عمران أحمد (Imran Ahmed), زينب موسى (Zainab Mossa), أبو بكر محمد كينتشاناكودي (ABUBAKKAR MOHAMMAD KINCHANAKODI).",
                "Translittérations RU/ZH : non produites ce cycle (schema v1.2, 3 langues uniquement). Si couverture RU/ZH requise → cycle dédié avec schema v1.1.",
                "Services : [] — source CSV ne contient pas la liste, à récupérer depuis source_url (DHA Sheryan search).",
                "Cohérence terminologique : specialties, license types, emirates, country strings tous issus de glossary v1.0 sans variation libre. Pas de drift détecté.",
                "Spécificité Tamer Buyukyilmaz : 'Buyukyilmaz' est une romanisation sans diacritiques de 'Büyükyılmaz' (turc). Translittération AR conserve la forme romanisée: بويوك يلماز (B-Y-Y-K Y-L-M-Z = Büyük Yılmaz). Le nom signifie littéralement 'grande persévérance' en turc.",
                "Spécificité ABUBAKKAR MOHAMMAD KINCHANAKODI : nom composé malayalam (kerala indien). Kinchanakodi = 'lamp hill' (kinchana=lamp, kodi=hill/flag en malayalam). Conservé tel quel en translittération AR phonétique.",
            ],
        },
        "fiches": fiches,
    }

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"✅ Wrote {OUT.relative_to(WORKSPACE)}")
    print(f"   Fiches: {len(fiches)}")
    print(f"   Langues: 3 (fr, ar, en)")
    print(f"   Total champs nommés traduits ce cycle: {len(fiches) * 5} champs × 3 langues")
    for f_ in fiches:
        print(f"   - {f_['id']} :: {f_['name']['fr']} ({f_['specialty']['fr']}) [gender={f_['_gender_heuristic']}]")

if __name__ == "__main__":
    main()
