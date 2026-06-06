#!/usr/bin/env python3
"""
DMD — Cycle 14/30min (cron ad25646f-4b17-4eb0-b148-0b7d037c7231 "Traduction 5 Langues") :
5 nouvelles fiches praticiens × 5 langues (FR, AR, EN, RU, ZH) = 25 traductions.

Source : data/dentists_emirates.csv (DHA Sheryan, 6186 dentistes uniques).
Méthode : translittération manuelle + glossary v1.0 (translations/glossary.md).
DeepL API key indisponible dans .env.translator (template) → translittération / table FR→X.
Schema v1.5 (5 langues) — continuité cycle13.

Continuité :
- cycle 13 (5 fiches Endo/Ortho/Pedo/Perio/Prostho) → cumul 80 fiches / 35 per_lang complètes
- ce cycle 14 couvre 5 NOUVELLES fiches, variety specialty + 1 license REG (Mohammed Ajazullah Khan)
- après ce cycle : cumul 85 fiches / 40 per_lang complètes

Sélection : 5 fiches NON couvertes, variety specialty-driven :
- 1× Oral Surgeon        (Feras Yabroudi)         — nouveau
- 1× Pediatric Dentist   (Anila Virani)           — couverture (8 déjà)
- 1× Orthodontist        (Mohammed Ajazullah Khan) — REG license (variant vs FTL)
- 1× Prosthodontist      (Mostafa Elmasri)         — couverture (8 déjà)
- 1× General Dentist     (Cecilia Brizuela)        — espagnol/italien (test translittération)

Livrables :
- translations/per_lang/dentist_{license}_{fr|ar|en|ru|zh}.json (5 × 5 = 25 fichiers)
- translations/fiches-2026-06-06-cycle14.json (résumé)
- translations/build_cycle14.py (script, traçabilité)
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
OUT_SUMMARY = ROOT / "fiches-2026-06-06-cycle14.json"
OUT_DIR = ROOT / "per_lang"
OUT_DIR.mkdir(exist_ok=True)
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
SCHEMA_VERSION = "1.5"
TARGET_FICHES = 5
LANGS = ["fr", "ar", "en", "ru", "zh"]

# === Glossaire 5 langues (aligné glossary.md v1.0) ===

SPECIALTY = {
    "Endodontist": {
        "slug": "endodontist",
        "fr": "Endodontiste",
        "ar": "أخصائي علاج العصب",
        "en": "Endodontist",
        "ru": "Эндодонтист",
        "zh": "牙髓病医生",
    },
    "Orthodontist": {
        "slug": "orthodontist",
        "fr": "Orthodontiste",
        "ar": "أخصائي تقويم الأسنان",
        "en": "Orthodontist",
        "ru": "Ортодонт",
        "zh": "正畸医生",
    },
    "Pediatric Dentist": {
        "slug": "pediatric-dentist",
        "fr": "Pédodontiste",
        "ar": "أخصائي أسنان الأطفال",
        "en": "Pediatric Dentist",
        "ru": "Детский стоматолог",
        "zh": "儿童牙医",
    },
    "Periodontist": {
        "slug": "periodontist",
        "fr": "Parodontiste",
        "ar": "أخصائي أمراض اللثة",
        "en": "Periodontist",
        "ru": "Пародонтолог",
        "zh": "牙周病医生",
    },
    "Prosthodontist": {
        "slug": "prosthodontist",
        "fr": "Prosthodontiste",
        "ar": "أخصائي التركيبات السنية",
        "en": "Prosthodontist",
        "ru": "Ортопед-стоматолог",
        "zh": "修复科牙医",
    },
    "Oral Surgeon": {
        "slug": "oral-surgeon",
        "fr": "Chirurgien dentiste",
        "ar": "جراح الفم والأسنان",
        "en": "Oral Surgeon",
        "ru": "Челюстно-лицевой хирург",
        "zh": "口腔外科医生",
    },
    "General Dentist": {
        "slug": "general-dentist",
        "fr": "Dentiste généraliste",
        "ar": "طبيب أسنان عام",
        "en": "General Dentist",
        "ru": "Стоматолог общей практики",
        "zh": "全科牙医",
    },
}

LICENSE_TYPE = {
    "FTL": {"fr": "Temps plein", "ar": "دوام كامل", "en": "Full-Time License", "ru": "Полная занятость", "zh": "全职执照"},
    "REG": {"fr": "Licence régulière", "ar": "رخصة منتظمة", "en": "Regular License", "ru": "Обычная лицензия", "zh": "普通执照"},
    "PTL": {"fr": "Temps partiel", "ar": "دوام جزئي", "en": "Part-Time License", "ru": "Частичная занятость", "zh": "兼职执照"},
    "VIS": {"fr": "Visiteur", "ar": "زائر", "en": "Visiting License", "ru": "Гостевой допуск", "zh": "访问执照"},
}

CITY = {
    "Dubai": {"fr": "Dubaï", "ar": "دبي", "en": "Dubai", "ru": "Дубай", "zh": "迪拜"},
    "Abu Dhabi": {"fr": "Abu Dhabi", "ar": "أبوظبي", "en": "Abu Dhabi", "ru": "Абу-Даби", "zh": "阿布扎比"},
    "Sharjah": {"fr": "Sharjah", "ar": "الشارقة", "en": "Sharjah", "ru": "Шарджа", "zh": "沙迦"},
    "Ajman": {"fr": "Ajman", "ar": "عجمان", "en": "Ajman", "ru": "Аджман", "zh": "阿治曼"},
}

COUNTRY = {"UAE": {"fr": "Émirats arabes unis", "ar": "الإمارات العربية المتحدة", "en": "United Arab Emirates", "ru": "Объединённые Арабские Эмираты", "zh": "阿拉伯联合酋长国"}}
COUNTRY_SHORT = {"UAE": {"fr": "EAU", "ar": "الإمارات", "en": "UAE", "ru": "ОАЭ", "zh": "阿联酋"}}

# === Heuristique genre (FR/AR) — set cumulé cycles 1-13 + cycle 14 ===

FEMININE_FIRST = {
    "zeina", "zaynab", "zainab", "sara", "sarah", "lama", "rosedina", "anila",
    "claudia", "rabab", "lalaine", "ambili", "sruthi", "shreekala", "fatma",
    "fatima", "hasna", "shamma", "ermel", "seema", "farha", "edna", "lina",
    "leila", "laila", "layla", "mariam", "maryam", "diana", "noor", "nour",
    "hala", "ghada", "dina", "eman", "iman", "asma", "amira", "ameera", "hanan",
    "abeer", "noura", "noora", "latifa", "latifah", "hind", "amal", "suzanna",
    "suzan", "suzanne", "mehanas", "mehana", "rihab", "rehab", "samira", "samiha",
    "rana", "reem", "salma", "nadia", "shereen", "sherin", "priya", "pooja",
    "cecilia", "maria", "rosa", "ana", "carmen", "elena", "isabel", "sofia",
}
MASCULINE_FIRST = {
    "feras", "firas", "fars", "ahmad", "ahmed", "earl", "muhammad", "mohammad",
    "mohammed", "mohamed", "oday", "vimalkumar", "pouya", "johnny", "gunter",
    "nachiket", "anas", "tamer", "imran", "mukeshpal", "sukhpreet", "raj",
    "mumtaz", "majd", "majed", "fadi", "fady", "issa", "ibrahim", "yasser",
    "yaser", "ammar", "amar", "bassam", "ramzi", "ramzy", "sami", "nabil",
    "wael", "wail", "khalil", "samir", "sameer", "jaber", "hamza", "hamzah",
    "zaid", "zayed", "mahmoud", "mostafa", "mustafa", "ashraf", "emad", "imad",
    "hisham", "mazen", "ayman", "aiman", "nader", "ramy", "rami", "walid",
    "kareem", "karim", "faisal", "sultan", "nasser", "samer", "hadi", "ghassan",
    "mohannad", "muhanad", "nawaf", "turki", "saud", "abdulrahman", "abdulaziz",
    "haitham", "hazem", "ali", "hassan", "hussein", "khaled", "khalid", "yousef",
    "youssef", "yusuf", "omar", "muawya", "mohamed", "yasser", "mostafa",
    "ajazullah", "brizuela",
}

def detect_gender(full_name: str) -> str:
    """Returns 'F', 'M', or '?' based on first-name heuristics."""
    first = full_name.strip().split()[0].lower()
    first = re.sub(r'[^a-zà-ÿ]', '', first)
    if first in FEMININE_FIRST:
        return "F"
    if first in MASCULINE_FIRST:
        return "M"
    if first.endswith("a") and len(first) > 2:
        return "F"
    if first.endswith(("an", "os", "us", "im", "ar", "al", "ik", "ek", "ok", "uk", "il", "ul", "ed", "ad", "ir", "or", "um", "in", "on", "er", "el", "as", "ir", "iz")):
        if first.endswith("as") and len(first) >= 5:
            return "?"
        return "M"
    return "?"


# === Translittération nom propre (latin → AR) — table enrichie cycle 14 ===

AR_NAME_MAP = {
    "mohammed": "محمد", "mohamed": "محمد", "muhammad": "محمد", "muhammed": "محمد",
    "ahmed": "أحمد", "ahmad": "أحمد",
    "ali": "علي",
    "hassan": "حسن", "hasan": "حسن",
    "hussein": "حسين", "hussain": "حسين",
    "abdullah": "عبد الله",
    "khalid": "خالد", "khaled": "خالد",
    "yousef": "يوسف", "youssef": "يوسف", "yusuf": "يوسف",
    "omar": "عمر",
    "fatima": "فاطمة", "fatma": "فاطمة",
    "sara": "سارة", "sarah": "سارة",
    "zeina": "زينة", "zainab": "زينب", "zaynab": "زينب",
    "layla": "ليلى", "leila": "ليلى", "laila": "ليلى",
    "mariam": "مريم", "maryam": "مريم",
    "yasser": "ياسر", "yaser": "ياسر",
    "wael": "وائل", "wail": "وائل",
    "muawya": "معاوية", "muawiya": "معاوية",
    "rihab": "رحاب", "rehab": "رحاب",
    "mohamed": "محمد",
    "kaseasbeh": "الكسياسب", "alkaseasbeh": "الكسياسب",
    "alhindi": "الهندي", "hindi": "هندي",
    "almoselli": "المسلّي", "almoshelli": "المشلّي",
    "moselli": "مسلّي", "moshelli": "مشلّي",
    "alobaidi": "العبيدي", "obaidi": "عبيدي", "obaidy": "عبيدي",
    "obaidat": "عبيدات",
    "al": "ال",
    "kasthurikattil": "كاستوريكاتيل",
    "mehanas": "ميهانس",
    # cycle 14 additions
    "feras": "فراس", "yabroudi": "يبرودي",
    "anila": "أنيلا", "virani": "فيراني",
    "ajazullah": "عزالله", "khan": "خان",
    "mostafa": "مصطفى", "elmasri": "المصري",
    "cecilia": "سيسليا", "brizuela": "بريزويلا",
}

def transliterate_name_ar(full_name: str) -> str:
    """Tokenize and transliterate. Merges 'Al' prefix with the next token."""
    tokens = full_name.split()
    out_tokens = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        key = tok.lower()
        if key == "al" and i + 1 < len(tokens):
            next_tok = tokens[i + 1]
            next_key = next_tok.lower()
            if f"al{next_key}" in AR_NAME_MAP:
                out_tokens.append(AR_NAME_MAP[f"al{next_key}"])
            elif next_key in AR_NAME_MAP:
                out_tokens.append("ال" + AR_NAME_MAP[next_key])
            else:
                out_tokens.append("ال" + next_tok)
            i += 2
            continue
        if key in AR_NAME_MAP:
            out_tokens.append(AR_NAME_MAP[key])
        else:
            out_tokens.append(tok)
        i += 1
    return " ".join(out_tokens)


# === Translittération nom propre (latin → RU cyrillique) — table enrichie cycle 14 ===

RU_NAME_MAP = {
    "mohammed": "Мухаммед", "mohamed": "Мухаммед", "muhammad": "Мухаммад", "muhammed": "Мухаммед",
    "ahmed": "Ахмед", "ahmad": "Ахмад",
    "ali": "Али",
    "hassan": "Хасан", "hasan": "Хасан",
    "hussein": "Хусейн", "hussain": "Хусейн",
    "abdullah": "Абдулла",
    "khalid": "Халид", "khaled": "Халед",
    "yousef": "Юсеф", "youssef": "Юсеф", "yusuf": "Юсуф",
    "omar": "Омар",
    "fatima": "Фатима", "fatma": "Фатма",
    "sara": "Сара", "sarah": "Сара",
    "zeina": "Зейна", "zainab": "Зайнаб", "zaynab": "Зайнаб",
    "layla": "Лейла", "leila": "Лейла", "laila": "Лайла",
    "mariam": "Мариам", "maryam": "Марьям",
    "yasser": "Ясер", "yaser": "Ясер",
    "wael": "Ваэль", "wail": "Ваэль",
    "muawya": "Муавия", "muawiya": "Муавия",
    "rihab": "Рихаб", "rehab": "Рехаб",
    "mohamed": "Мухаммед",
    "kaseasbeh": "Касиасбех", "alkaseasbeh": "Аль-Касиасбех",
    "alhindi": "Аль-Хинди", "hindi": "Хинди",
    "almoselli": "Аль-Моселли", "almoshelli": "Аль-Мошелли",
    "moselli": "Моселли", "moshelli": "Мошелли",
    "alobaidi": "Аль-Обаиди", "obaidi": "Обаиди", "obaidy": "Обаиди",
    "obaidat": "Обаидат",
    "al": "",
    "kasthurikattil": "Кастурикаттил",
    "mehanas": "Механас",
    # cycle 14 additions
    "feras": "Ферас", "yabroudi": "Ябруди",
    "anila": "Анила", "virani": "Вирани",
    "ajazullah": "Аджазулла", "khan": "Хан",
    "mostafa": "Мостафа", "elmasri": "Эль-Масри",
    "cecilia": "Сесилия", "brizuela": "Брисуэла",
}

def transliterate_name_ru(full_name: str) -> str:
    """Tokenize and transliterate to Russian cyrillic."""
    tokens = full_name.split()
    out_tokens = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        key = tok.lower()
        if key == "al" and i + 1 < len(tokens):
            next_tok = tokens[i + 1]
            next_key = next_tok.lower()
            if f"al{next_key}" in RU_NAME_MAP and RU_NAME_MAP[f"al{next_key}"]:
                val = RU_NAME_MAP[f"al{next_key}"]
                if val.startswith("Аль-"):
                    out_tokens.append(val)
                else:
                    out_tokens.append("Аль-" + val)
            elif next_key in RU_NAME_MAP and RU_NAME_MAP[next_key]:
                out_tokens.append("Аль-" + RU_NAME_MAP[next_key])
            else:
                out_tokens.append("Аль-" + next_tok.capitalize())
            i += 2
            continue
        if key in RU_NAME_MAP and RU_NAME_MAP[key]:
            out_tokens.append(RU_NAME_MAP[key])
        else:
            out_tokens.append(tok.capitalize())
        i += 1
    return " ".join(out_tokens)


# === Translittération nom propre (latin → ZH pinyin) — table enrichie cycle 14 ===

ZH_NAME_MAP = {
    "mohammed": "Mùhǎnmòdé", "mohamed": "Mùhǎnmòdé", "muhammad": "Mùhǎnmǎdè", "muhammed": "Mùhǎnmòdé",
    "ahmed": "Àhǎimàidé", "ahmad": "Àhǎimǎdè",
    "ali": "Ālì",
    "hassan": "Hǎisāng", "hasan": "Hāsāng",
    "hussein": "Hǔsàiyīn", "hussain": "Hǔsāng",
    "abdullah": "Ābǔdùlā",
    "khalid": "Hālǐdé", "khaled": "Hāléide",
    "yousef": "Yóusèfū", "youssef": "Yóusèfū", "yusuf": "Yúsūfū",
    "omar": "Ōumǎ'ěr",
    "fatima": "Fātímǎ", "fatma": "Fātímǎ",
    "sara": "Sàlā", "sarah": "Sàlā",
    "zeina": "Zāinà", "zainab": "Zāinǎbù", "zaynab": "Zāinǎbù",
    "layla": "Lěilā", "leila": "Lěilā", "laila": "Lǎilā",
    "mariam": "Mǎlìyàmù", "maryam": "Mǎlìyángmù",
    "yasser": "Yàsè'ěr", "yaser": "Yàsè'ěr",
    "wael": "Wǎ'ěi'ěr", "wail": "Wǎ'ěi'ěr",
    "muawya": "Mù'āwīyà", "muawiya": "Mù'āwīyà",
    "rihab": "Līhābù", "rehab": "Līhābù",
    "mohamed": "Mùhǎnmòdé",
    "kaseasbeh": "Kǎxīāsībèihē", "alkaseasbeh": "Ā'ěrKǎxīāsībèihē",
    "alhindi": "Ā'ěrHīndì", "hindi": "Hīndì",
    "almoselli": "Ā'ěrmòsāilì", "almoshelli": "Ā'ěrmòxiāolì",
    "moselli": "Mòsāilì", "moshelli": "Mòxiāolì",
    "alobaidi": "Ā'ěrĀobāiyīdì", "obaidi": "Āobāiyīdì", "obaidy": "Āobāiyīdì",
    "obaidat": "Āobāiyīdāt",
    "al": "",
    "kasthurikattil": "Kǎsītǔlīkǎtílí'ěr",
    "mehanas": "Mèhānàsī",
    # cycle 14 additions
    "feras": "Fèilāsī", "yabroudi": "Yàbùlǔdī",
    "anila": "Ānílā", "virani": "Wéilāní",
    "ajazullah": "Ājiǎzǔlā", "khan": "Hǎn",
    "mostafa": "Mùsītǎfǎ", "elmasri": "Ā'ěrmàisīlǐ",
    "cecilia": "Xīxīlìyà", "brizuela": "Bùlǐsūwēilā",
}

def transliterate_name_zh(full_name: str) -> str:
    """Tokenize and transliterate to Hanyu Pinyin diacritique."""
    tokens = full_name.split()
    out_tokens = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        key = tok.lower()
        if key == "al" and i + 1 < len(tokens):
            next_tok = tokens[i + 1]
            next_key = next_tok.lower()
            if f"al{next_key}" in ZH_NAME_MAP and ZH_NAME_MAP[f"al{next_key}"]:
                val = ZH_NAME_MAP[f"al{next_key}"]
                if val.startswith("Ā'ěr"):
                    out_tokens.append(val)
                else:
                    out_tokens.append("Ā'ěr " + val)
            elif next_key in ZH_NAME_MAP and ZH_NAME_MAP[next_key]:
                out_tokens.append("Ā'ěr " + ZH_NAME_MAP[next_key])
            else:
                out_tokens.append("Ā'ěr " + next_tok)
            i += 2
            continue
        if key in ZH_NAME_MAP and ZH_NAME_MAP[key]:
            out_tokens.append(ZH_NAME_MAP[key])
        else:
            out_tokens.append(tok)
        i += 1
    return " ".join(out_tokens)


# === Genre accord FR/AR/EN (templates bio) ===

def fr_gender_adj(gender: str) -> str:
    return "Licenciée" if gender == "F" else "Licencié"


def ar_verb_works(gender: str) -> str:
    return "تعمل" if gender == "F" else "يعمل"


def ar_verb_license(gender: str) -> str:
    return "تحمل" if gender == "F" else "يحمل"


def en_article(specialty_en: str) -> str:
    return "an" if specialty_en.lower()[0] in "aeiou" else "a"


def ru_declension_ftl() -> str:
    return "полной занятостью"


def ru_declension_reg() -> str:
    return "обычной лицензией"


# === Specialty slug mapping (CSV "specialty" string → slug) ===

SPECIALTY_SLUG = {
    "General Dentist": "general-dentist",
    "Orthodontist": "orthodontist",
    "Endodontist": "endodontist",
    "Periodontist": "periodontist",
    "Prosthodontist": "prosthodontist",
    "Dental Implant": "implantologist",
    "Implantologist": "implantologist",
    "Oral Surgeon": "oral-surgeon",
    "Pediatric Dentist": "pediatric-dentist",
    "Restorative Dentist": "restorative-dentist",
    "Specialist Dentist": "specialist-dentist",
    "Cosmetic Dentist": "cosmetic-dentist",
}

# === Génération de la bio (5 langues) ===

def build_bios(gender: str, full_name: str, specialty_fr: str, specialty_ar: str,
               specialty_en: str, specialty_ru: str, specialty_zh: str,
               city_en: str, license_type_code: str):
    city = CITY.get(city_en, CITY["Dubai"])
    lt = LICENSE_TYPE.get(license_type_code, LICENSE_TYPE["FTL"])
    lt_ru_inflected = ru_declension_ftl() if license_type_code == "FTL" else (
        ru_declension_reg() if license_type_code == "REG" else lt["ru"]
    )
    lt_zh = lt["zh"]
    lt_en = lt["en"]
    lt_fr = lt["fr"]

    bios = {}

    bios["fr"] = (
        f"Dr {full_name} est {('une' if gender == 'F' else 'un')} {specialty_fr.lower()} "
        f"à {city['fr']}, {COUNTRY['UAE']['fr']} ({COUNTRY_SHORT['UAE']['fr']}). "
        f"{fr_gender_adj(gender)} sous {lt_fr.lower()} délivrée par la "
        f"Dubai Health Authority (DHA)."
    )

    if gender == "F":
        dr_prefix = "الدكتورة"
    else:
        dr_prefix = "الدكتور"
    bios["ar"] = (
        f"{dr_prefix} {transliterate_name_ar(full_name)} "
        f"{specialty_ar} في {city['ar']}، {COUNTRY['UAE']['ar']}. "
        f"{ar_verb_license(gender)} رخصة {lt['ar']} صادرة عن "
        f"هيئة الصحة بدبي (DHA)."
    )

    bios["en"] = (
        f"Dr. {full_name} is {en_article(specialty_en)} {specialty_en} "
        f"based in {city['en']}, {COUNTRY['UAE']['en']} ({COUNTRY_SHORT['UAE']['en']}). "
        f"Holds a {lt_en} issued by the Dubai Health Authority (DHA)."
    )

    bios["ru"] = (
        f"Д-р {transliterate_name_ru(full_name)} — {specialty_ru} "
        f"в {city['ru']}, {COUNTRY['UAE']['ru']} ({COUNTRY_SHORT['UAE']['ru']}). "
        f"Обладает {lt_ru_inflected}, выданной Управлением здравоохранения Дубая (DHA)."
    )

    bios["zh"] = (
        f"{transliterate_name_zh(full_name)}医生是{COUNTRY_SHORT['UAE']['zh']}{city['zh']}的{specialty_zh}。"
        f"持有迪拜卫生局 (DHA) 颁发的{lt_zh}。"
    )

    return bios


# === Main build loop ===

def slugify_name(full_name: str) -> str:
    return re.sub(r'[^a-z0-9]+', '-', full_name.lower()).strip('-')


def build_one_fiche(row: dict) -> dict:
    full_name = row["full_name"].strip()
    license_number = row["license_number"].strip()
    license_type_code = row["license_type"].strip() or "FTL"
    specialty_raw = row["specialty"].strip()
    clinic = row.get("clinic_name", "").strip()
    area = row.get("address", "").strip()
    city_en = row.get("emirate", "Dubai").strip() or "Dubai"

    slug = SPECIALTY_SLUG.get(specialty_raw, "general-dentist")
    if specialty_raw in SPECIALTY:
        sp_data = SPECIALTY[specialty_raw]
    else:
        sp_data = {
            "slug": slug,
            "fr": "Dentiste",
            "ar": "طبيب أسنان",
            "en": "Dentist",
            "ru": "Стоматолог",
            "zh": "牙医",
        }

    gender = detect_gender(full_name)
    fr_lic = "Licenciée" if gender == "F" else "Licencié"

    name_ar = transliterate_name_ar(full_name)
    name_ru = transliterate_name_ru(full_name)
    name_zh = transliterate_name_zh(full_name)

    city = CITY.get(city_en, CITY["Dubai"])
    area_full_en = f"{clinic}, {city_en}, UAE" if clinic else f"{city_en}, UAE"
    area_full_fr = f"{clinic}, {city['fr']}, {COUNTRY['UAE']['fr']}" if clinic else f"{city['fr']}, {COUNTRY['UAE']['fr']}"
    area_full_ar = f"{clinic}, {city['ar']}, {COUNTRY['UAE']['ar']}" if clinic else f"{city['ar']}, {COUNTRY['UAE']['ar']}"

    bios = build_bios(
        gender, full_name,
        sp_data["fr"], sp_data["ar"], sp_data["en"], sp_data["ru"], sp_data["zh"],
        city_en, license_type_code,
    )

    fiche = {
        "id": f"{slugify_name(full_name)}-{license_number}",
        "license_number": license_number,
        "license_type": {
            "code": license_type_code,
            "fr": LICENSE_TYPE.get(license_type_code, LICENSE_TYPE["FTL"])["fr"],
            "ar": LICENSE_TYPE.get(license_type_code, LICENSE_TYPE["FTL"])["ar"],
            "en": LICENSE_TYPE.get(license_type_code, LICENSE_TYPE["FTL"])["en"],
            "ru": LICENSE_TYPE.get(license_type_code, LICENSE_TYPE["FTL"])["ru"],
            "zh": LICENSE_TYPE.get(license_type_code, LICENSE_TYPE["FTL"])["zh"],
        },
        "name": {
            "original": full_name,
            "fr": full_name,
            "ar": name_ar,
            "en": full_name,
            "ru": name_ru,
            "zh": name_zh,
        },
        "specialty": {
            "slug": slug,
            "fr": sp_data["fr"],
            "ar": sp_data["ar"],
            "en": sp_data["en"],
            "ru": sp_data["ru"],
            "zh": sp_data["zh"],
        },
        "sub_specialty": None,
        "facility": {
            "original": clinic,
            "fr": clinic,
            "ar": clinic,
            "en": clinic,
            "ru": clinic,
            "zh": clinic,
        },
        "area": {
            "original": area,
            "fr": area_full_fr,
            "ar": area_full_ar,
            "en": area_full_en,
            "ru": f"{clinic}, {city['ru']}, {COUNTRY_SHORT['UAE']['ru']}" if clinic else f"{city['ru']}, {COUNTRY_SHORT['UAE']['ru']}",
            "zh": f"{clinic}, {city['zh']}, {COUNTRY_SHORT['UAE']['zh']}" if clinic else f"{city['zh']}, {COUNTRY_SHORT['UAE']['zh']}",
        },
        "city": {
            "fr": city["fr"],
            "ar": city["ar"],
            "en": city["en"],
            "ru": city["ru"],
            "zh": city["zh"],
        },
        "country": {
            "fr": COUNTRY["UAE"]["fr"],
            "ar": COUNTRY["UAE"]["ar"],
            "en": COUNTRY["UAE"]["en"],
            "ru": COUNTRY["UAE"]["ru"],
            "zh": COUNTRY["UAE"]["zh"],
        },
        "country_short": {
            "fr": COUNTRY_SHORT["UAE"]["fr"],
            "ar": COUNTRY_SHORT["UAE"]["ar"],
            "en": COUNTRY_SHORT["UAE"]["en"],
            "ru": COUNTRY_SHORT["UAE"]["ru"],
            "zh": COUNTRY_SHORT["UAE"]["zh"],
        },
        "category": "dentists",
        "bio": bios,
        "services": None,
        "languages_spoken": ["ar", "en"],
        "_provenance": {
            "source_csv": "data/dentists_emirates.csv",
            "source_url": row.get("source_url", ""),
            "scraped_at": row.get("scraped_at", ""),
            "row_index": row.get("_row_index", None),
        },
        "schema_version": SCHEMA_VERSION,
        "translated_at": NOW,
        "_langs_produced": LANGS,
        "_gender_heuristic": gender,
    }
    return fiche


def emit_per_lang(fiche: dict):
    ln = fiche["license_number"]
    fiche_id = fiche["id"]
    for lang in LANGS:
        out = {
            "id": fiche_id,
            "license_number": ln,
            "license_type": fiche["license_type"][lang],
            "name": {
                "original": fiche["name"]["original"],
                lang: fiche["name"][lang],
            },
            "specialty": fiche["specialty"][lang],
            "sub_specialty": fiche["sub_specialty"],
            "facility": fiche["facility"][lang] or fiche["facility"]["original"],
            "area": fiche["area"][lang] or fiche["area"]["original"],
            "city": fiche["city"][lang],
            "country": fiche["country"][lang],
            "country_short": fiche["country_short"][lang],
            "category": fiche["category"],
            "bio": fiche["bio"][lang],
            "services": fiche["services"],
            "languages_spoken": fiche["languages_spoken"],
            "schema_version": SCHEMA_VERSION,
            "translated_at": NOW,
            "_lang": lang,
            "_provenance": fiche["_provenance"],
        }
        outpath = OUT_DIR / f"dentist_{ln}_{lang}.json"
        outpath.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    # 5 selected dentists for cycle 14 (1 with REG license for variety)
    selected_licenses = ["00005038", "00018395", "00073857", "00070602", "00123367"]

    with open(SOURCE, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    for i, r in enumerate(rows):
        r["_row_index"] = i

    sel = [r for r in rows if r["license_number"].strip() in selected_licenses]
    assert len(sel) == 5, f"Expected 5 selected, got {len(sel)}"

    sel_ordered = sorted(sel, key=lambda r: selected_licenses.index(r["license_number"].strip()))

    fiches = [build_one_fiche(r) for r in sel_ordered]

    for fiche in fiches:
        emit_per_lang(fiche)

    from collections import Counter
    sp_count = Counter(f["specialty"]["slug"] for f in fiches)
    gender_count = Counter(f["_gender_heuristic"] for f in fiches)
    lic_count = Counter(f["license_type"]["code"] for f in fiches)

    summary = {
        "_meta": {
            "schema_version": SCHEMA_VERSION,
            "generated_at": NOW,
            "generator": "build_cycle14.py",
            "cron": "ad25646f-4b17-4eb0-b148-0b7d037c7231",
            "cron_name": "Dubai - Traduction 5 Langues (Medical)",
            "cycle": "2026-06-06 cycle 14/30min",
            "previous_cycle": "2026-06-06 cycle 13/30min (80 fiches cumul, 35 in per_lang)",
            "languages": LANGS,
            "target_fiches": TARGET_FICHES,
            "fiches_produced": len(fiches),
            "translations_produced": len(fiches) * len(LANGS),
            "specialty_mix": dict(sp_count),
            "gender_mix": dict(gender_count),
            "license_mix": dict(lic_count),
            "per_lang_count": {lang: len(fiches) for lang in LANGS},
            "per_lang_files": len(fiches) * len(LANGS),
            "source_csv": "data/dentists_emirates.csv",
            "glossary_version": "v1.0 (translations/glossary.md)",
            "deepl_used": False,
            "deepl_note": "DEEPL_API_KEY vide dans .env.translator (template) → translittération manuelle + tables FR→AR/RU/ZH alignées glossary.md v1.0",
            "cycle14_notes": [
                "1× Oral Surgeon (Feras Yabroudi) — nouveau, pas couvert cycles 1-13",
                "1× REG license (Mohammed Ajazullah Khan Orthodontist) — variant FTL pour test pipeline",
                "1× nom espagnol (Cecilia Brizuela) — test translittération hors zone arabe/indienne",
            ],
        },
        "fiches": fiches,
    }

    OUT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ Cycle 14 done: {len(fiches)} fiches × {len(LANGS)} langs = {len(fiches)*len(LANGS)} traductions")
    print(f"   Summary: {OUT_SUMMARY}")
    print(f"   Per-lang files: {len(fiches)*len(LANGS)}")
    print(f"   Specialty mix: {dict(sp_count)}")
    print(f"   Gender mix: {dict(gender_count)}")
    print(f"   License mix: {dict(lic_count)}")
    for f in fiches:
        print(f"   - {f['id']} ({f['specialty']['slug']}, {f['license_type']['code']}, gender={f['_gender_heuristic']})")


if __name__ == "__main__":
    main()
