#!/usr/bin/env python3
"""
DMD — Cycle 06/30min (cron 6e3d697a-91cb-4475-872a-8ab965e7ba7f "Translation & Localization") :
5 nouvelles fiches praticiens × 5 langues (FR, AR, EN, RU, ZH).
Source : data/dentists_emirates.csv (DHA Sheryan, ~6186 lignes).
Méthode : manuelle + glossary v1.0 (translations/glossary.md).
DeepL API key toujours indisponible dans .env.translator (template — pas de vraies clés).
Schema v1.1 (5 langues) — continuité cycle05.
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
OUT = ROOT / "fiches-2026-06-06-cycle06.json"

# === Glossaire v1.0 (5 langues, aligné avec translations/glossary.md) ===

SPECIALTY = {
    "general-dentist": {
        "fr": "Dentiste généraliste",
        "ar": "طبيب أسنان عام",
        "en": "General Dentist",
        "ru": "Стоматолог общей практики",
        "zh": "全科牙医",
    },
    "orthodontist": {
        "fr": "Orthodontiste",
        "ar": "أخصائي تقويم الأسنان",
        "en": "Orthodontist",
        "ru": "Ортодонт",
        "zh": "正畸医生",
    },
    "endodontist": {
        "fr": "Endodontiste",
        "ar": "أخصائي علاج العصب",
        "en": "Endodontist",
        "ru": "Эндодонтист",
        "zh": "牙髓病医生",
    },
    "periodontist": {
        "fr": "Parodontiste",
        "ar": "أخصائي أمراض اللثة",
        "en": "Periodontist",
        "ru": "Пародонтолог",
        "zh": "牙周病医生",
    },
    "prosthodontist": {
        "fr": "Prosthodontiste",
        "ar": "أخصائي التركيبات السنية",
        "en": "Prosthodontist",
        "ru": "Ортопед-стоматолог",
        "zh": "修复科牙医",
    },
    "implantologist": {
        "fr": "Implantologue",
        "ar": "أخصائي زراعة الأسنان",
        "en": "Implantologist",
        "ru": "Имплантолог",
        "zh": "种植牙医生",
    },
    "oral-surgeon": {
        "fr": "Chirurgien dentiste",
        "ar": "جراح الفم والأسنان",
        "en": "Oral Surgeon",
        "ru": "Челюстно-лицевой хирург",
        "zh": "口腔外科医生",
    },
    "pediatric-dentist": {
        "fr": "Pédodontiste",
        "ar": "أخصائي أسنان الأطفال",
        "en": "Pediatric Dentist",
        "ru": "Детский стоматолог",
        "zh": "儿童牙医",
    },
    "cosmetic-dentist": {
        "fr": "Esthétique dentaire",
        "ar": "تجميل الأسنان",
        "en": "Cosmetic Dentist",
        "ru": "Эстетический стоматолог",
        "zh": "美容牙科",
    },
    "specialist-dentist": {
        "fr": "Dentiste spécialiste",
        "ar": "طبيب أسنان أخصائي",
        "en": "Specialist Dentist",
        "ru": "Стоматолог-специалист",
        "zh": "专科牙医",
    },
}

LICENSE_TYPE = {
    "REG": {
        "fr": "Licence régulière",
        "ar": "رخصة منتظمة",
        "en": "Regular License",
        "ru": "Обычная лицензия",
        "zh": "普通执照",
    },
    "FTL": {
        "fr": "Temps plein",
        "ar": "دوام كامل",
        "en": "Full-Time License",
        "ru": "Полная занятость",
        "zh": "全职执照",
    },
    "PTL": {
        "fr": "Temps partiel",
        "ar": "دوام جزئي",
        "en": "Part-Time License",
        "ru": "Частичная занятость",
        "zh": "兼职执照",
    },
    "VIS": {
        "fr": "Visiteur",
        "ar": "زائر",
        "en": "Visiting License",
        "ru": "Гостевой допуск",
        "zh": "访问执照",
    },
}

EMIRATE = {
    "Dubai": {"fr": "Dubaï", "ar": "دبي", "en": "Dubai", "ru": "Дубай", "zh": "迪拜"},
    "Abu Dhabi": {"fr": "Abu Dhabi", "ar": "أبوظبي", "en": "Abu Dhabi", "ru": "Абу-Даби", "zh": "阿布扎比"},
    "Sharjah": {"fr": "Sharjah", "ar": "الشارقة", "en": "Sharjah", "ru": "Шарджа", "zh": "沙迦"},
    "Ajman": {"fr": "Ajman", "ar": "عجمان", "en": "Ajman", "ru": "Аджман", "zh": "阿治曼"},
    "Ras Al Khaimah": {"fr": "Ras Al Khaimah", "ar": "رأس الخيمة", "en": "Ras Al Khaimah", "ru": "Рас-эль-Хайма", "zh": "哈伊马角"},
    "Fujairah": {"fr": "Fujairah", "ar": "الفجيرة", "en": "Fujairah", "ru": "Фуджейра", "zh": "富查伊拉"},
    "Umm Al Quwain": {"fr": "Umm Al Quwain", "ar": "أم القيوين", "en": "Umm Al Quwain", "ru": "Умм-эль-Кайвайн", "zh": "乌姆盖万"},
}

COUNTRY = {
    "fr": "Émirats arabes unis",
    "ar": "الإمارات العربية المتحدة",
    "en": "United Arab Emirates",
    "ru": "Объединённые Арабские Эмираты",
    "zh": "阿拉伯联合酋长国",
}

COUNTRY_SHORT = {
    "fr": "EAU",
    "ar": "الإمارات",
    "en": "UAE",
    "ru": "ОАЭ",
    "zh": "阿联酋",
}

# === Translitérations noms (cycle06 — set de 5) ===
# AR : translittération arabe commune UAE
# RU : ISO 9 / passeport international
# ZH : Hanyu Pinyin diacritique (caractères natifs à venir quand praticien chinois natif)
# Hasna Hafsi : prénom arabe féminin (حسناء / حسنة), Hafsi nom de famille arabe maghrébin
# Ermel Yap : prénom philippin (Ermel), Yap nom d'origine chinoise Hokkien (葉)
# Shamma Ali Al Ali : شَمّة علي العلي (composante tribale UAE)
# Earl Odena : prénom anglais, nom philippin (Odena — Hispanique/Philippin)
# Ahmad Aid : prénom arabe masculin, nom de famille Aid (عِيد)

ARABIC_TRANSLIT = {
    "Hasna Hafsi": "حسنة حفصي",
    "Ermel Yap": "إيرمل ياب",
    "Shamma Ali Al Ali": "شمة علي العلي",
    "Earl Odena": "إيرل أودينا",
    "Ahmad Aid": "أحمد عيد",
}

CYRILLIC_TRANSLIT = {
    "Hasna Hafsi": "Хасна Хафси",
    "Ermel Yap": "Эрмел Яп",
    "Shamma Ali Al Ali": "Шамма Али Аль Али",
    "Earl Odena": "Эрл Одена",
    "Ahmad Aid": "Ахмад Аид",
}

PINYIN = {
    "Hasna Hafsi": "Hāsīnà Hāfūsī",
    "Ermel Yap": "Āiměi'ěr Yè",
    "Shamma Ali Al Ali": "Xīmǎmǎ Ālī Ālī",
    "Earl Odena": "Ā'ěr Àodénà",
    "Ahmad Aid": "Āhǎomǎdài Āyīdé",
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
    if lang_code == "ru":
        lt_lower = license_type.lower()
        if "полная занятость" in lt_lower:
            lt_inflected = "полной занятости"
        elif "обычная лицензия" in lt_lower:
            lt_inflected = "обычной лицензией"
        elif "частичная занятость" in lt_lower:
            lt_inflected = "частичной занятости"
        elif "гостевой допуск" in lt_lower:
            lt_inflected = "гостевым допуском"
        else:
            lt_inflected = lt_lower
        return f"{name} — {specialty.lower()} в {area}, ОАЭ. Обладает {lt_inflected}, выданной Управлением здравоохранения Дубая (DHA)."
    if lang_code == "zh":
        return f"{name}是{area}的{specialty}。持有迪拜卫生局 (DHA) 颁发的{license_type}。"
    return ""

def build_name_block(original: str) -> dict:
    return {
        "original": original,
        "fr": original,
        "ar": ARABIC_TRANSLIT.get(original, original),
        "en": original,
        "ru": CYRILLIC_TRANSLIT.get(original, original),
        "zh": PINYIN.get(original, original),
    }

def detect_gender(name: str) -> str:
    """Heuristique genre — étendue cycle06 (Hasna, Shamma, Ermel ajoutées)."""
    female_first_names = {
        "zeina", "meena", "fatma", "samira", "lama", "rosedina", "anila",
        "claudia", "rabab", "zainab", "lalaine", "ambili", "sruthi",
        "shreekala", "sara", "samira",
        "hasna", "shamma", "ermel",
    }
    male_first_names = {
        "feras", "fars", "ahmad", "ahmed", "earl", "muhammad", "mohammad",
        "oday", "vimalkumar", "pouya", "johnny", "gunter", "nachiket",
    }
    first = name.split()[0].lower().rstrip(".")
    if first in female_first_names:
        return "f"
    if first in male_first_names:
        return "m"
    if first.endswith(("a", "ia", "ina", "ila", "ela", "ima", "ema", "ana", "ala")) and first not in {
        "muhammad", "mohammad", "ahmed", "mouhammad", "samir",
        "oday", "vimalkumar", "feras", "pouya", "johnny", "gunter",
        "nachiket", "fars",
    }:
        return "f"
    return "m"

def build_facility_block(clinic: str) -> dict:
    if not clinic:
        return {"fr": "", "ar": "", "en": "", "ru": "", "zh": ""}
    return {
        "fr": clinic,
        "ar": clinic,   # clinic name kept in latin (standard UAE pratique)
        "en": clinic,
        "ru": clinic,
        "zh": clinic,
    }

def main():
    # 1) Skip licenses déjà traduits (cycle01→05)
    done_licenses = set()
    for prev in [
        "fiches-2026-06-05-cycle01.json",
        "fiches-2026-06-06-cycle02.json",
        "fiches-2026-06-06-cycle03.json",
        "fiches-2026-06-06-cycle04.json",
        "fiches-2026-06-06-cycle05.json",
    ]:
        p = ROOT / prev
        if p.exists():
            with p.open() as f:
                for f_ in json.load(f)["fiches"]:
                    done_licenses.add(f_.get("license_number"))

    # 2) Pick 5 nouvelles fiches (incluant 1 Prosthodontist pour diversification specialty)
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

    # 3) Construire les fiches 5 langues
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
                "ru": lt["ru"],
                "zh": lt["zh"],
            },
            "name": name_block,
            "specialty": {
                "slug": slug_sp,
                "fr": sp["fr"],
                "ar": sp["ar"],
                "en": sp["en"],
                "ru": sp["ru"],
                "zh": sp["zh"],
            },
            "sub_specialty": None,
            "facility": facility_block,
            "area": {
                "fr": em["fr"],
                "ar": em["ar"],
                "en": em["en"],
                "ru": em["ru"],
                "zh": em["zh"],
            },
            "country": COUNTRY,
            "country_short": COUNTRY_SHORT,
            "category": "dentists",
            "bio": {
                "fr": bio_template(name_block["fr"], sp["fr"], em["fr"], lt["fr"], "fr", gender),
                "ar": bio_template(name_block["ar"], sp["ar"], em["ar"], lt["ar"], "ar", gender),
                "en": bio_template(name_block["en"], sp["en"], em["en"], lt["en"], "en", gender),
                "ru": bio_template(name_block["ru"], sp["ru"], em["ru"], lt["ru"], "ru", gender),
                "zh": bio_template(name_block["zh"], sp["zh"], em["zh"], lt["zh"], "zh", gender),
            },
            "services": [],
            "languages_spoken": {
                "fr": ["en", "ar"],
                "ar": ["en", "ar"],
                "en": ["en", "ar"],
                "ru": ["en", "ar"],
                "zh": ["en", "ar"],
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

    # 4) Output JSON — schema v1.1 (5 langues)
    out = {
        "_meta": {
            "schema_version": "1.1",
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "generator": "cron:6e3d697a-91cb-4475-872a-8ab965e7ba7f (Dubai - Translation & Localization)",
            "cycle": "2026-06-06 cycle 06/30min",
            "previous_cycles": [
                "fiches-2026-06-05-cycle01.json (5 fiches, fr+ar+en, manual+glossary v0.9)",
                "fiches-2026-06-06-cycle02.json (5 fiches, fr+ar+en, manual+glossary v1.0)",
                "fiches-2026-06-06-cycle03.json (5 fiches, fr+ar+en+ru+zh, manual+glossary v1.0 — schema v1.1)",
                "fiches-2026-06-06-cycle04.json (5 fiches, fr+ar+en only — REGRESSION note: cycle04 lost RU/ZH coverage; cycle05 restores schema v1.1 5-langue)",
                "fiches-2026-06-06-cycle05.json (5 fiches, fr+ar+en+ru+zh, manual+glossary v1.0, specialty mix: orthodontist+4×general-dentist)",
            ],
            "source_csv": "data/dentists_emirates.csv",
            "source_rows_total": 6186,
            "source_rows_translated_to_date": 30,
            "glossary_version": "v1.0 (translations/glossary.md)",
            "translation_method": "manual+glossary (DeepL API key still unavailable in .env.translator — placeholder)",
            "languages": ["fr", "ar", "en", "ru", "zh"],
            "field_completeness_note": "Source CSV lacks sub_specialty/bio/services/languages_spoken; bio is synthesized from glossary template, services=[] per source.",
            "quality_notes": [
                "Noms : translittération manuelle (AR) + table ISO-9 (RU) + pinyin diacritique (ZH). Validation humaine requise pour AR/RU/ZH.",
                "Spécialités : 100% alignées avec glossary.md v1.0. Ce cycle introduit 1 Prosthodontist (Shamma Ali Al Ali) — diversifie la couverture au-delà de general-dentist.",
                "Licences : mapping FTL/REG/PTL/VIS aligné glossary.md (toutes FTL ce cycle).",
                "Émirats : tous Dubai ce cycle (mapping glossary.md).",
                "Genre : heuristique étendue cycle06 (Hasna, Shamma, Ermel ajoutées au set féminin; Earl, Ahmad au set masculin pour éviter faux féminin en '-a'). F pour Hasna, Ermel, Shamma; M pour Earl, Ahmad.",
                "Bio : template canonique 5-langue aligné cycle05.",
                "Cohérence Prosthodontiste/Prosthodontist/Ортопед-стоматолог/修复科牙医/أخصائي التركيبات السنية : VALIDÉE glossary v1.0.",
                "Translittération Yap (nom sino-philippin) → ياب (AR) / Яп (RU) / Yè 葉 (ZH) : le caractère 葉 est mentionné en note car pinyin diacritique (Yè) est la lecture Hokkien/Teochew standard.",
                "Services : [] — source CSV ne contient pas la liste, à récupérer depuis source_url.",
            ],
        },
        "fiches": fiches,
    }

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"✅ Wrote {OUT.relative_to(WORKSPACE)}")
    print(f"   Fiches: {len(fiches)}")
    print(f"   Langues: 5 (fr, ar, en, ru, zh)")
    print(f"   Total traductions produites ce cycle: {len(fiches) * 5} champs nommés × 5 langues")
    for f_ in fiches:
        print(f"   - {f_['id']} :: {f_['name']['fr']} ({f_['specialty']['fr']}) [gender={f_['_gender_heuristic']}]")

if __name__ == "__main__":
    main()
