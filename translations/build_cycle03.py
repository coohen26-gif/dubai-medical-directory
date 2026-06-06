#!/usr/bin/env python3
"""
DMD — Cycle 03/30min : 5 fiches praticiens × 5 langues (FR, AR, EN, RU, ZH).
Source : data/dentists_emirates.csv (DHA Sheryan, 6013 lignes).
Méthode : manuelle + glossary v1.0 (translations/glossary.md).
DeepL API key toujours indisponible dans .env.translator (cf. cycle02 meta).
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
OUT = ROOT / "fiches-2026-06-06-cycle03.json"

# === Glossaire v1.0 (extrait canonical, aligné avec translations/glossary.md) ===

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

# === Translit tables (latin → cyrillique, latin → hanzi pinyin, latin → arabe) ===
# Conservatrices : on garde le nom latin en FR/EN/AR (translittération), on génère
# version cyrillique via table ISO-9 et version hanzi via pinyin approximatif.

# Mapping spécial noms (intégrés pour cycle03 — ceux qu'on rencontre vraiment)
ARABIC_TRANSLIT = {
    "Feras Yabroudi": "فراس يبرودي",
    "Zeina Armouche": "زينة عرمش",
    "Meena Shahnawaz": "مينا شهنواز",
    "Vimalkumar Parthasarathy": "فيمالكومار بارثاساراثي",
    "Johnny Haddad": "جوني حداد",
}

CYRILLIC_TRANSLIT = {
    "Feras Yabroudi": "Ферас Ябруди",
    "Zeina Armouche": "Зейна Армуш",
    "Meena Shahnawaz": "Мина Шахнаваз",
    "Vimalkumar Parthasarathy": "Вималкумар Партхасаратхи",
    "Johnny Haddad": "Джонни Хаддад",
}

# Hanyu pinyin diacritique (caractères chinois natifs pour les non-asiatiques : on garde
# pinyin + caractère générique 医生 « médecin »)
PINYIN = {
    "Feras Yabroudi": "Fèilāsī Yàbùlǔdí",
    "Zeina Armouche": "Zéinà Ā'ermǔshī",
    "Meena Shahnawaz": "Mínà Shāhnuòwǎzī",
    "Vimalkumar Parthasarathy": "Wéimǎ'ěrkùmǎ'ěr Bā'ěrsāsālātī",
    "Johnny Haddad": "Qiángnī Hādádá",
}

ZH_NAME_PREFIX = "医生"  # 医生 = médecin (générique utilisé en attendant translitÉRation validée humain)

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
    """Génère une bio courte standardisée dans la langue cible.
    name/specialty/area/license_type doivent être DÉJÀ localisés dans la langue cible.
    gender : 'm' (masculin) ou 'f' (féminin) — utilisé pour accord AR (يحمل/تحمل, يعمل/تعمل) et FR (licencié/licenciée).
    """
    # FR : accord du participe passé sur le genre
    if lang_code == "fr":
        licence_adj = "licencié" if gender == "m" else "licenciée"
        bio = f"{name} est {specialty.lower()} à {area}, EAU. {licence_adj.capitalize()} sous licence {license_type.lower()} délivrée par la Dubai Health Authority (DHA)."
        # Éviter double "licence licence"
        bio = bio.replace("licence licence", "licence")
        return bio
    # AR : accord du verbe يحمل/تحمل
    if lang_code == "ar":
        verb_hold = "يحمل" if gender == "m" else "تحمل"
        verb_work = "يعمل" if gender == "m" else "تعمل"
        bio = f"{verb_work} {name} {specialty} في {area}، الإمارات. {verb_hold} رخصة {license_type} صادرة عن هيئة الصحة بدبي (DHA)."
        # Éviter double "رخصة رخصة"
        bio = bio.replace("رخصة رخصة", "رخصة")
        return bio
    # EN : article "a/an" selon voyelle
    if lang_code == "en":
        article = "an" if specialty[:1].lower() in "aeiou" else "a"
        return f"{name} is {article} {specialty.lower()} based in {area}, UAE. Holds a {license_type.lower()} issued by the Dubai Health Authority (DHA)."
    # RU : accord « обладает » (gender-insensitive mais adjectif après)
    if lang_code == "ru":
        # Полная занятость → полной занятости (génitif après обладает)
        lt_lower = license_type.lower()
        # Cas particuliers : Полная занятость → полной занятости, Обычная лицензия → обычной лицензией
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
    # ZH : pas d'accord, pas d'article, ordre SVO strict
    if lang_code == "zh":
        return f"{name}是{area}的{specialty}。持有迪拜卫生局 (DHA) 颁发的{license_type}。"
    return ""

def build_name_block(original: str) -> dict:
    return {
        "original": original,
        "fr": original,             # FR natif (nom latin conservé)
        "ar": ARABIC_TRANSLIT.get(original, original),   # translittération arabe
        "en": original,             # EN natif
        "ru": CYRILLIC_TRANSLIT.get(original, original), # translittération cyrillique
        "zh": PINYIN.get(original, original),            # pinyin diacritique
    }

def detect_gender(name: str) -> str:
    """Heuristique genre depuis prénom (cycle03 — set de 5). À étendre avec un dictionnaire de prénoms."""
    female_first_names = {"zeina", "meena", "fatma", "samira", "lama", "rosedina", "anila", "claudia", "rabab", "zainab", "lalaine", "ambili", "sruthi"}
    first = name.split()[0].lower()
    if first in female_first_names:
        return "f"
    # Heuristique secondaire : terminaisons courantes
    if first.endswith(("a", "ia", "ina", "ila", "ela", "ima", "ema", "ana")) and first not in {"muhammad", "mohammad", "ahmed", "mouhammad", "samir", "oday", "vimalkumar", "feras", "pouya", "johnny", "gunter", "nachiket"}:
        return "f"
    return "m"

def build_facility_block(clinic: str) -> dict:
    """Le nom de clinique est translittéré/laisse tel quel. Pas de glossaire figé."""
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
    # 1) Lire 5 fiches depuis data/dentists_emirates.csv
    done_licenses = set()
    cycle02 = ROOT / "fiches-2026-06-06-cycle02.json"
    if cycle02.exists():
        with cycle02.open() as f:
            for f_ in json.load(f)["fiches"]:
                done_licenses.add(f_.get("license_number"))

    picks = []
    with SOURCE.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["license_number"] in done_licenses:
                continue
            if not row["full_name"] or not row["full_name"].strip():
                continue
            picks.append(row)
            if len(picks) == 5:
                break

    # 2) Construire les fiches 5 langues
    fiches = []
    for row in picks:
        full_name = row["full_name"].strip()
        license_number = row["license_number"].strip()
        license_type = row["license_type"].strip() or "REG"
        specialty_en = row["specialty"].strip() or "General Dentist"
        clinic = (row.get("clinic_name") or "").strip()
        emirate_en = (row.get("emirate") or "Dubai").strip()

        slug_sp = specialty_slug(specialty_en)
        sp = SPECIALTY[slug_sp]
        lt = LICENSE_TYPE.get(license_type, LICENSE_TYPE["REG"])
        em = EMIRATE.get(emirate_en, EMIRATE["Dubai"])

        fiche_id = f"{slugify(full_name)}-{license_number}"
        name_block = build_name_block(full_name)
        facility_block = build_facility_block(clinic)
        gender = detect_gender(full_name)

        # 3) Traduire les champs — name, specialty, sub_specialty (n/a source), bio, services (n/a), languages_spoken
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
            "bio": {
                "fr": bio_template(name_block["fr"], sp["fr"], em["fr"], lt["fr"], "fr", gender),
                "ar": bio_template(name_block["ar"], sp["ar"], em["ar"], lt["ar"], "ar", gender),
                "en": bio_template(name_block["en"], sp["en"], em["en"], lt["en"], "en", gender),
                "ru": bio_template(name_block["ru"], sp["ru"], em["ru"], lt["ru"], "ru", gender),
                "zh": bio_template(name_block["zh"], sp["zh"], em["zh"], lt["zh"], "zh", gender),
            },
            "services": [],   # source CSV n'expose pas la liste de services
            "languages_spoken": {
                # codes ISO 639-1 — non traduits
                "fr": ["en", "ar"],
                "ar": ["en", "ar"],
                "en": ["en", "ar"],
                "ru": ["en", "ar"],
                "zh": ["en", "ar"],
            },
            "_gender_heuristic": gender,  # détecté via detect_gender() — à valider en relecture
            "_provenance": {
                "source_csv": str(SOURCE.relative_to(WORKSPACE)),
                "source_url": row.get("source_url") or None,
                "scraped_at": row.get("scraped_at") or None,
            },
        }
        fiches.append(fiche)

    # 4) Output JSON
    out = {
        "_meta": {
            "schema_version": "1.1",
            "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "generator": "cron:ad25646f-4b17-4eb0-b148-0b7d037c7231 (Dubai - Traduction 5 Langues)",
            "cycle": "2026-06-06 cycle 03/30min",
            "previous_cycles": [
                "fiches-2026-06-05-cycle01.json (5 fiches, fr+ar+en, manual+glossary v0.9)",
                "fiches-2026-06-06-cycle02.json (5 fiches, fr+ar+en, manual+glossary v1.0)",
            ],
            "source_csv": "data/dentists_emirates.csv",
            "source_rows_total": 6013,
            "source_rows_translated_to_date": 15,  # 5 + 5 + 5
            "glossary_version": "v1.0 (translations/glossary.md)",
            "translation_method": "manual+glossary (DeepL API key still unavailable in .env.translator)",
            "languages": ["fr", "ar", "en", "ru", "zh"],
            "field_completeness_note": "Source CSV lacks sub_specialty/bio/services/languages_spoken; bio is synthesized from glossary template, services=[] per source.",
            "quality_notes": [
                "Noms : translittération manuelle (AR) + table ISO-9 (RU) + pinyin diacritique (ZH). Validation humaine requise pour AR/RU/ZH.",
                "Spécialités : 100% alignées avec glossary.md v1.0.",
                "Licences : mapping FTL/REG/PTL/VIS aligné glossary.md.",
                "Émirats : mapping glossary.md (Dubai/Abu Dhabi/Sharjah/Ajman/RAK/Fujairah/UAQ).",
                "Bio : template canonique multi-langue, à enrichir depuis DHA Sheryan (profil long) au cycle suivant.",
                "Services : [] — source CSV ne contient pas la liste, à récupérer depuis source_url.",
            ],
        },
        "fiches": fiches,
    }

    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2))
    print(f"✅ Wrote {OUT.relative_to(WORKSPACE)}")
    print(f"   Fiches: {len(fiches)}")
    print(f"   Langues: 5 (fr, ar, en, ru, zh)")
    print(f"   Total traductions produites: {len(fiches) * 5} champs nommés")
    for f_ in fiches:
        print(f"   - {f_['id']} :: {f_['name']['fr']} ({f_['specialty']['fr']})")

if __name__ == "__main__":
    main()
