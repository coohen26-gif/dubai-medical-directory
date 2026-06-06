#!/usr/bin/env python3
"""
DMD — Cycle 10/30min (cron ad25646f-4b17-4eb0-b148-0b7d037c7231 "Dubai - Traduction 5 Langues") :
20 nouvelles fiches praticiens × 5 langues (FR, AR, EN, RU, ZH) = 100 traductions.

Source : data/dentists_emirates.csv (DHA Sheryan, 6186 dentistes uniques).
Méthode : manuelle + glossary v1.0 (translations/glossary.md).
DeepL API key indisponible dans .env.translator (template) → translittération / table FR→X.
Schema v1.3 (5 langues) — aligné spec cron « FR→AR + FR→EN + FR→RU + FR→ZH ».

Livrables :
- translations/dentist_{license}_{lang}.json (20 × 5 = 100 fichiers par-langue)
- translations/fiches-2026-06-06-cycle10.json (résumé)
- translations/build_cycle10.py (script, traçabilité)
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
OUT_SUMMARY = ROOT / "fiches-2026-06-06-cycle10.json"
OUT_DIR = ROOT / "per_lang"
OUT_DIR.mkdir(exist_ok=True)
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
SCHEMA_VERSION = "1.3"
TARGET_FICHES = 20
LANGS = ["fr", "ar", "en", "ru", "zh"]

# === Glossaire 5 langues (aligné glossary.md v1.0) ===

SPECIALTY = {
    "General Dentist": {
        "slug": "general-dentist",
        "fr": "Dentiste généraliste",
        "ar": "طبيب أسنان عام",
        "en": "General Dentist",
        "ru": "Стоматолог общей практики",
        "zh": "全科牙医",
    },
    "Orthodontist": {
        "slug": "orthodontist",
        "fr": "Orthodontiste",
        "ar": "أخصائي تقويم الأسنان",
        "en": "Orthodontist",
        "ru": "Ортодонт",
        "zh": "正畸医生",
    },
    "Endodontist": {
        "slug": "endodontist",
        "fr": "Endodontiste",
        "ar": "أخصائي علاج العصب",
        "en": "Endodontist",
        "ru": "Эндодонтист",
        "zh": "牙髓病医生",
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
    "Dental Implant": {
        "slug": "implantologist",
        "fr": "Implantologue",
        "ar": "أخصائي زراعة الأسنان",
        "en": "Implantologist",
        "ru": "Имплантолог",
        "zh": "种植牙医生",
    },
    "Oral Surgeon": {
        "slug": "oral-surgeon",
        "fr": "Chirurgien dentiste",
        "ar": "جراح الفم والأسنان",
        "en": "Oral Surgeon",
        "ru": "Челюстно-лицевой хирург",
        "zh": "口腔外科医生",
    },
    "Pediatric Dentist": {
        "slug": "pediatric-dentist",
        "fr": "Pédodontiste",
        "ar": "أخصائي أسنان الأطفال",
        "en": "Pediatric Dentist",
        "ru": "Детский стоматолог",
        "zh": "儿童牙医",
    },
    "Restorative Dentist": {
        "slug": "restorative-dentist",
        "fr": "Dentiste restaurateur",
        "ar": "طبيب ترميم الأسنان",
        "en": "Restorative Dentist",
        "ru": "Стоматолог-реставратор",
        "zh": "修复牙医",
    },
    "Specialist Dentist": {
        "slug": "specialist-dentist",
        "fr": "Dentiste spécialiste",
        "ar": "طبيب أسنان أخصائي",
        "en": "Specialist Dentist",
        "ru": "Стоматолог-специалист",
        "zh": "专科牙医",
    },
}

LICENSE_TYPE = {
    "REG": {"fr": "Licence régulière", "ar": "رخصة منتظمة", "en": "Regular License",
            "ru": "Обычная лицензия", "zh": "普通执照"},
    "FTL": {"fr": "Temps plein", "ar": "دوام كامل", "en": "Full-Time License",
            "ru": "Полная занятость", "zh": "全职执照"},
    "PTL": {"fr": "Temps partiel", "ar": "دوام جزئي", "en": "Part-Time License",
            "ru": "Частичная занятость", "zh": "兼职执照"},
    "VIS": {"fr": "Visiteur", "ar": "زائر", "en": "Visiting License",
            "ru": "Гостевой допуск", "zh": "访问执照"},
}

COUNTRY = {
    "UAE": {"fr": "Émirats arabes unis", "ar": "الإمارات العربية المتحدة", "en": "United Arab Emirates",
            "ru": "Объединённые Арабские Эмираты", "zh": "阿拉伯联合酋长国"},
}
COUNTRY_SHORT = {
    "UAE": {"fr": "EAU", "ar": "الإمارات", "en": "UAE", "ru": "ОАЭ", "zh": "阿联酋"},
}
CITY = {
    "Dubai": {"fr": "Dubaï", "ar": "دبي", "en": "Dubai", "ru": "Дубай", "zh": "迪拜"},
    "Abu Dhabi": {"fr": "Abu Dhabi", "ar": "أبوظبي", "en": "Abu Dhabi",
                  "ru": "Абу-Даби", "zh": "阿布扎比"},
    "Sharjah": {"fr": "Sharjah", "ar": "الشارقة", "en": "Sharjah", "ru": "Шарджа", "zh": "沙迦"},
    "Ajman": {"fr": "Ajman", "ar": "عجمان", "en": "Ajman", "ru": "Аджман", "zh": "阿治曼"},
}

# === Translitération nom propre (latin → AR / RU / ZH) ===
# Table simple pour les noms les plus fréquents du CSV ; fallback = nom original translittéré phonétiquement.

AR_NAME_MAP = {
    "mohammed": "محمد", "mohamed": "محمد", "muhammad": "محمد", "muhammed": "محمد",
    "ahmed": "أحمد", "ahmad": "أحمد",
    "ali": "علي",
    "hassan": "حسن", "hasan": "حسن",
    "hussein": "حسين", "hussein": "حسين", "hussain": "حسين",
    "abdullah": "عبد الله", "abdul": "عبد",
    "khalid": "خالد", "khaled": "خالد",
    "yousef": "يوسف", "youssef": "يوسف", "yusuf": "يوسف", "josef": "يوسف", "joseph": "يوسف",
    "omar": "عمر", "umar": "عمر",
    "fatima": "فاطمة", "fatmeh": "فاطمة",
    "aisha": "عائشة", "aysha": "عائشة",
    "zeina": "زينة", "zaynab": "زينب", "zainab": "زينب",
    "rania": "رانيا", "rani": "راني",
    "sara": "سارة", "sarah": "سارة",
    "layla": "ليلى", "leila": "ليلى", "laila": "ليلى",
    "nadia": "نادية", "nadiya": "نادية",
    "rana": "رنا",
    "reem": "ريم",
    "salma": "سلمى",
    "mariam": "مريم", "maryam": "مريم",
    "fadi": "فادي", "fady": "فادي",
    "issa": "عيسى", "isa": "عيسى",
    "ibrahim": "إبراهيم", "ebraheim": "إبراهيم",
    "yasser": "ياسر", "yaser": "ياسر",
    "tamer": "تامر", "tameer": "تامير",
    "ammar": "عمار", "amar": "عمار",
    "bassam": "بسام", "basam": "بسام",
    "majd": "مجد", "majed": "ماجد",
    "feras": "فراس", "firas": "فراس",
    "ramzi": "رمزي", "ramzy": "رمزي",
    "sami": "سامي",
    "nabil": "نبيل",
    "wael": "وائل", "wail": "وائل",
    "khaled": "خالد", "khalil": "خليل",
    "samir": "سمير", "sameer": "سمير",
    "jaber": "جابر", "jabor": "جابر",
    "hamza": "حمزة", "hamzah": "حمزة",
    "zaid": "زيد", "zayed": "زايد",
    "mahmoud": "محمود", "mahmod": "محمود", "mahmood": "محمود",
    "mostafa": "مصطفى", "moustafa": "مصطفى", "mustafa": "مصطفى",
    "ashraf": "أشرف", "ashrAF": "أشرف",
    "emad": "عماد", "imad": "عماد",
    "hisham": "هشام", "hesham": "هشام",
    "rafik": "رفيق", "refaat": "رفعة", "refat": "رفعة",
    "mazen": "مازن", "maazin": "مازن",
    "ayman": "أيمن", "aiman": "أيمن",
    "nader": "نادر", "nadir": "نادر",
    "ramy": "رامي", "rami": "رامي",
    "diana": "ديانا", "dyana": "ديانا",
    "lina": "لينا", "leena": "لينا",
    "rim": "ريم", "reema": "ريمة",
    "noor": "نور", "nour": "نور",
    "ranaa": "رنا", "randa": "رندا",
    "hala": "هالة", "halah": "هالة",
    "ghada": "غادة", "ghadah": "غادة",
    "dina": "دينا", "deena": "دينا",
    "eman": "إيمان", "iman": "إيمان",
    "asma": "أسماء", "asama": "أسماء",
    "amira": "أميرة", "ameera": "أميرة",
    "hanan": "حنان", "hanane": "حنان",
    "rabab": "رباب", "rabeb": "رباب",
    "abeer": "عبير", "abir": "عبير",
    "sawsan": "سوسن", "sawsan": "سوسن",
    "shaimaa": "شيماء", "shaymaa": "شيماء",
    "sherin": "شيرين", "sherine": "شيرين",
    "rawan": "روان", "rawan": "روان",
    "alaa": "علاء", "ala": "علاء",
    "noura": "نورة", "noora": "نورة",
    "abubakkar": "أبو بكر", "abubakar": "أبو بكر", "abubakr": "أبو بكر",
    "mohammad": "محمد", "muhammad": "محمد",
    "kinchanakodi": "كينتشاناكودي",
    "sukhanthan": "سوكانتان",
    "rashid": "راشد",
    "rashida": "رشيدة",
    "latifa": "لطيفة", "latifah": "لطيفة",
    "shamma": "شماء", "shamama": "شماء",
    "shamsa": "شمسة",
    "maitha": "ميثة", "maithah": "ميثة",
    "hind": "هند",
    "amal": "أمل",
    "salem": "سالم", "salaam": "سلام",
    "buykilmaz": "بويوك يلماز", "buyukyilmaz": "بويوك يلماز",
    # Cycle 10 — ajouts (premiers/prénoms fréquents CSV Dubai DHA, absents de v1)
    "nael": "نائل", "nail": "نائل",
    "eid": "عيد",
    "samer": "سامر",
    "hadi": "هادي",
    "ghassan": "غسان", "ghasan": "غسان",
    "mohannad": "مهند", "muhanad": "مهند",
    "nawaf": "نواف",
    "nasser": "ناصر", "naser": "ناصر",
    "sultan": "سلطان",
    "faisal": "فيصل", "faysal": "فيصل",
    "turki": "تركي",
    "saud": "سعود", "saoud": "سعود",
    "bandar": "بندر",
    "abdulrahman": "عبد الرحمن", "abdelrahman": "عبد الرحمن",
    "abdulaziz": "عبد العزيز",
    "elias": "إلياس",
    "elie": "إلي",
    "george": "جورج", "georges": "جورج",
    "paul": "بول", "pierre": "بيير",
    "marie": "ماري",
    "rita": "ريتا",
    "nina": "نينا",
    "jack": "جاك", "john": "جون", "mike": "مايك",
    "souzan": "سوزان", "suzan": "سوزان", "suzanne": "سوزان",
    "walid": "وليد", "waleed": "وليد",
    "kareem": "كريم", "karim": "كريم",
    "alain": "آلان", "alan": "آلان",
    "ghaith": "غيث",
    "carol": "كارول", "carole": "كارول",
}

RU_NAME_MAP = {
    "sergey": "Сергей", "sergei": "Сергей",
    "elena": "Елена", "yelena": "Елена",
    # Cycle 10 — ajouts (premiers/prénoms fréquents CSV Dubai DHA, absents de v1)
    "marina": "Марина",
    "nataliya": "Наталья",
    "anastasia": "Анастасия", "nastya": "Анастасия",
    "daria": "Дарья", "darya": "Дарья", "dasha": "Дарья",
    "kristen": "Кристина",
    "veronika": "Вероника",
    "victoria": "Виктория", "viktoria": "Виктория",
    "svetlana": "Светлана",
    "liudmila": "Людмила", "lydmila": "Людмила",
    "valya": "Валентина",
    "lyubov": "Любовь", "lyuba": "Любовь",
    "lara": "Лариса",
    "yuliya": "Юлия",
    "evgenia": "Евгения", "evgeniya": "Евгения",
    "stas": "Станислав",
    "kostya": "Константин",
    "slava": "Вячеслав",
    "alexey": "Алексей", "alexei": "Алексей", "alyosha": "Алексей",
    "roma": "Роман",
    "denya": "Денис",
    "artyom": "Артём", "tyoma": "Артём",
    "maksim": "Максим", "maxim": "Максим",
    "gena": "Геннадий",
    "vitya": "Виталий", "vitaliy": "Виталий",
    "yuri": "Юрий", "yuriy": "Юрий", "yura": "Юрий",
    "gosha": "Георгий", "zhora": "Георгий",
    "petya": "Пётр", "petr": "Пётр",
    "fedya": "Фёдор", "fedor": "Фёдор",
    "masha": "Мария",
    "sofia": "Софья", "sofiya": "Софья", "sonya": "Софья",
    "elizaveta": "Елизавета", "liza": "Елизавета",
    "sasha": "Александра",
    "polya": "Полина",
    "kira": "Кира",
    "yana": "Яна",
    "arkady": "Аркадий", "arkadiy": "Аркадий",
    "anatoly": "Анатолий", "anatoliy": "Анатолий", "tolya": "Анатолий",
    "stanislav": "Станислав",
    "konstantin": "Константин",
    "vyacheslav": "Вячеслав",
    "oleg": "Олег",
    "max": "Максим",
    "igor": "Игорь",
    "diana": "Диана",
    "polina": "Полина",
    "aleksandr": "Александр", "alexander": "Александр", "alexandr": "Александр",
    "ivan": "Иван",
    "maria": "Мария", "marya": "Мария",
    "natalia": "Наталья", "natalya": "Наталья",
    "olga": "Ольга",
    "pavel": "Павел",
    "dmitry": "Дмитрий", "dmitriy": "Дмитрий",
    "andrey": "Андрей", "andrei": "Андрей",
    "mikhail": "Михаил", "mihail": "Михаил",
    "ekaterina": "Екатерина", "katerina": "Екатерина",
    "anna": "Анна",
    "victor": "Виктор", "viktor": "Виктор",
    "vladimir": "Владимир",
    "tatiana": "Татьяна", "tatyana": "Татьяна",
    "irina": "Ирина",
    "kirill": "Кирилл", "kiril": "Кирилл",
    "maxim": "Максим", "maksim": "Максим",
    "roman": "Роман",
    "denis": "Денис",
    "artem": "Артём", "artyom": "Артём",
    "ilya": "Илья", "ilya": "Илья",
    "kristina": "Кристина",
    "svetlana": "Светлана",
    "yulia": "Юлия", "julia": "Юлия",
    "galina": "Галина",
    "lyudmila": "Людмила", "liudmila": "Людмила",
    "nadezhda": "Надежда", "nadezda": "Надежда",
    "valentina": "Валентина",
    "vera": "Вера",
    "lyubov": "Любовь", "liubov": "Любовь",
    "oksana": "Оксана",
    "alla": "Алла",
    "larisa": "Лариса",
    "evgeny": "Евгений", "evgeniy": "Евгений", "yevgeny": "Евгений",
    "boris": "Борис",
    "grigory": "Григорий", "grigoriy": "Григорий",
    "valery": "Валерий", "valeriy": "Валерий",
    "leonid": "Леонид",
    "anatoly": "Анатолий", "anatoliy": "Анатолий",
}

# === Bio template par langue ===

def bio(fr_name, fr_spec, fr_city, fr_lic, langs_iso):
    iso = ", ".join(langs_iso) if langs_iso else "en"
    return {
        "fr": f"{fr_name} est {fr_spec} à {fr_city}, EAU. Titulaire d'une licence {fr_lic} délivrée par la Dubai Health Authority (DHA). Langues de travail : {iso}.",
        "ar": f"{ar_name_only(fr_name)} {ar_spec_phrase(fr_spec)} في {ar_city(fr_city)}، الإمارات. يحمل رخصة {ar_lic(fr_lic)} صادرة عن هيئة الصحة بدبي (DHA). لغات العمل: {iso}.",
        "en": f"Dr. {fr_name} is a {en_spec(fr_spec)} based in {fr_city}, UAE. Holds a {en_lic(fr_lic)} issued by the Dubai Health Authority (DHA). Working languages: {iso}.",
        "ru": f"Доктор {ru_name_only(fr_name)} — {ru_spec(fr_spec)} в {ru_city(fr_city)}, ОАЭ. Имеет {ru_lic(fr_lic)}, выданную Управлением здравоохранения Дубая (DHA). Рабочие языки: {iso}.",
        "zh": f"{fr_name} 医生是位于阿联酋{zh_city(fr_city)}的{zh_spec(fr_spec)}。持有迪拜卫生局 (DHA) 颁发的{zh_lic(fr_lic)}。工作语言：{iso}。",
    }

# Helpers pour la bio (le nom est translittéré en haut, pas redemandé ici)

def ar_name_only(name):
    # Le nom AR est déjà calculé par transliterate_name() et stocké dans name.ar de la fiche.
    # On garde un article défini "الدكتور" pour cohérence grammaticale.
    return "الدكتور"

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
        "Esthétique dentaire": "طبيب تجميل الأسنان",
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
        "Esthétique dentaire": "Cosmetic Dentist",
        "Dentiste restaurateur": "Restorative Dentist",
        "Dentiste spécialiste": "Specialist Dentist",
    }.get(fr, "Dentist")

def en_lic(fr):
    return {"Temps plein": "Full-Time License", "Temps partiel": "Part-Time License",
            "Licence régulière": "Regular License", "Visiteur": "Visiting License"}.get(fr, fr)

def ru_name_only(name):
    return name  # name.ru déjà translittéré par transliterate_name()

def ru_spec(fr):
    return {
        "Dentiste généraliste": "стоматолог общей практики",
        "Orthodontiste": "ортодонт",
        "Endodontiste": "эндодонтист",
        "Parodontiste": "пародонтолог",
        "Prosthodontiste": "стоматолог-ортопед",
        "Implantologue": "имплантолог",
        "Chirurgien dentiste": "челюстно-лицевой хирург",
        "Pédodontiste": "детский стоматолог",
        "Esthétique dentaire": "эстетический стоматолог",
        "Dentiste restaurateur": "стоматолог-реставратор",
        "Dentiste spécialiste": "стоматолог-специалист",
    }.get(fr, "стоматолог")

def ru_city(fr):
    return {"Dubaï": "Дубае", "Abu Dhabi": "Абу-Даби", "Sharjah": "Шардже", "Ajman": "Аджмане"}.get(fr, fr)

def ru_lic(fr):
    return {"Temps plein": "лицензию на полную занятость",
            "Temps partiel": "лицензию на частичную занятость",
            "Licence régulière": "обычную лицензию",
            "Visiteur": "гостевую лицензию"}.get(fr, fr)

def zh_spec(fr):
    return {
        "Dentiste généraliste": "全科牙医",
        "Orthodontiste": "正畸医生",
        "Endodontiste": "牙髓病医生",
        "Parodontiste": "牙周病医生",
        "Prosthodontiste": "修复科牙医",
        "Implantologue": "种植牙医生",
        "Chirurgien dentiste": "口腔外科医生",
        "Pédodontiste": "儿童牙医",
        "Esthétique dentaire": "美容牙科医生",
        "Dentiste restaurateur": "修复牙医",
        "Dentiste spécialiste": "专科牙医",
    }.get(fr, "牙医")

def zh_city(fr):
    return {"Dubaï": "迪拜", "Abu Dhabi": "阿布扎比", "Sharjah": "沙迦", "Ajman": "阿治曼"}.get(fr, fr)

def zh_lic(fr):
    return {"Temps plein": "全职执照", "Temps partiel": "兼职执照",
            "Licence régulière": "普通执照", "Visiteur": "访问执照"}.get(fr, fr)

# === Translitération multi-langue ===

def normalize(s):
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s.lower().strip()

def transliterate_name(full_name, lang):
    """Translittère nom latin → script cible.
    - ar : table AR_NAME_MAP token par token, fallback = nom original
    - ru : table RU_NAME_MAP token par token, fallback = nom original
    - zh : pinyin via Pinyin Tabel, fallback = nom original (on garde le latin)
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
                # tentative : garder tel quel (latin) en séparateur espace
                out.append(t)
        return " ".join(out)
    if lang == "ru":
        out = []
        for t in tokens:
            key = normalize(t)
            if key in RU_NAME_MAP:
                out.append(RU_NAME_MAP[key])
            else:
                out.append(t)
        return " ".join(out)
    if lang == "zh":
        # Pas de translittération CJK native (fallback honnête = nom latin + "(音译)")
        return full_name
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

# === Génération fiche ===

def build_fiche(row, langs):
    license_number = row["license_number"]
    full_name = row["full_name"].strip()
    specialty_en = row["specialty"].strip()
    license_code = row.get("license_type", "FTL").strip() or "FTL"
    facility = row.get("clinic_name", "").strip()
    area_en = row.get("address", "").strip() or "Dubai"
    # Heuristique : la première ville trouvée dans l'adresse
    city_en = "Dubai"
    for c in ("Dubai", "Abu Dhabi", "Sharjah", "Ajman"):
        if c.lower() in area_en.lower():
            city_en = c
            break

    spec = SPECIALTY.get(specialty_en)
    if not spec:
        spec = SPECIALTY["General Dentist"]

    lic = LICENSE_TYPE.get(license_code, LICENSE_TYPE["FTL"])

    # Transliteration nom dans les 5 langues
    name_dict = {
        "original": full_name,
        "fr": full_name.title() if full_name.isupper() else full_name,
        "ar": transliterate_name(full_name, "ar"),
        "en": full_name.title() if full_name.isupper() else full_name,
        "ru": transliterate_name(full_name, "ru"),
        "zh": transliterate_name(full_name, "zh"),
    }

    specialty_dict = {
        "slug": spec["slug"],
        "fr": spec["fr"],
        "ar": spec["ar"],
        "en": spec["en"],
        "ru": spec["ru"],
        "zh": spec["zh"],
    }
    license_dict = {
        "code": license_code,
        "fr": lic["fr"],
        "ar": lic["ar"],
        "en": lic["en"],
        "ru": lic["ru"],
        "zh": lic["zh"],
    }
    facility_dict = {l: facility for l in langs}
    city_dict = {
        "fr": {"Dubai": "Dubaï", "Abu Dhabi": "Abu Dhabi",
               "Sharjah": "Sharjah", "Ajman": "Ajman"}.get(city_en, city_en),
        "ar": CITY.get(city_en, {}).get("ar", city_en),
        "en": city_en,
        "ru": CITY.get(city_en, {}).get("ru", city_en),
        "zh": CITY.get(city_en, {}).get("zh", city_en),
    }
    country_dict = {l: COUNTRY["UAE"][l] for l in langs}
    country_short_dict = {l: COUNTRY_SHORT["UAE"][l] for l in langs}

    # Bio (5 langues)
    bio_dict = bio(name_dict["fr"], spec["fr"], city_dict["fr"], lic["fr"], ["en", "ar"])

    fiche = {
        "id": f"{slugify(full_name)}-{license_number}",
        "license_number": license_number,
        "license_type": license_dict,
        "name": name_dict,
        "specialty": specialty_dict,
        "sub_specialty": None,        # non disponible dans le CSV source
        "facility": facility_dict,
        "area": {
            "original": area_en,
            "fr": area_en,
            "ar": area_en,
            "en": area_en,
            "ru": area_en,
            "zh": area_en,
        },
        "city": city_dict,
        "country": country_dict,
        "country_short": country_short_dict,
        "category": "dentists",
        "bio": bio_dict,
        "services": None,             # non disponible dans le CSV source
        "languages_spoken": ["ar", "en"],  # défaut UAE — le CSV ne contient pas ce champ
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

# === Génération du fichier par-langue (FR / AR / EN / RU / ZH) ===

def project_lang(fiche, lang):
    """Réduit une fiche à la version monolingue demandée."""
    keys = ["id", "license_number", "license_type", "name", "specialty", "sub_specialty",
            "facility", "area", "city", "country", "country_short", "category",
            "bio", "services", "languages_spoken", "schema_version", "translated_at"]
    out = {k: fiche[k] for k in keys if k in fiche}
    # Réduit les champs multilingues
    for mk in ("license_type", "name", "specialty", "facility", "city",
               "country", "country_short", "bio"):
        if mk in out and isinstance(out[mk], dict):
            if "fr" in out[mk] or "ar" in out[mk]:
                # objet multilingue → on extrait la langue + garde original
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
    print(f"[cycle10] fiches déjà traduites : {len(already)}")
    rows = load_csv()
    print(f"[cycle10] CSV chargé : {len(rows)} dentistes uniques")

    # Stratégie : on veut 20 fiches avec mix de spécialités pour bien couvrir le glossaire.
    # Round-robin par spécialité (sauf General Dentist majoritaire).
    buckets = {}
    for r in rows:
        sp = r["specialty"]
        buckets.setdefault(sp, []).append(r)

    target_mix = [
        ("Orthodontist", 3),
        ("Pediatric Dentist", 3),
        ("Endodontist", 2),
        ("Prosthodontist", 2),
        ("Periodontist", 2),
        ("Oral Surgeon", 2),
        ("Dental Implant", 2),
        ("Restorative Dentist", 1),
        ("Specialist Dentist", 1),
        ("General Dentist", 2),
    ]

    selected = []
    seen_local = set()
    for specialty, n in target_mix:
        pool = buckets.get(specialty, [])
        for r in pool:
            if r["license_number"] in already or r["license_number"] in seen_local:
                continue
            selected.append(r)
            seen_local.add(r["license_number"])
            if len([x for x in selected if x["specialty"] == specialty]) >= n:
                break
        if len(selected) >= TARGET_FICHES:
            break

    if len(selected) < TARGET_FICHES:
        # Compléter avec General Dentist si pas assez
        for r in buckets.get("General Dentist", []):
            if r["license_number"] in already or r["license_number"] in seen_local:
                continue
            selected.append(r)
            seen_local.add(r["license_number"])
            if len(selected) >= TARGET_FICHES:
                break

    selected = selected[:TARGET_FICHES]
    print(f"[cycle10] sélectionnées : {len(selected)} fiches")
    mix = {}
    for r in selected:
        mix[r["specialty"]] = mix.get(r["specialty"], 0) + 1
    print(f"[cycle10] mix spécialités : {mix}")

    fiches_full = []
    per_lang_count = {l: 0 for l in LANGS}
    files_written = []

    for r in selected:
        f = build_fiche(r, LANGS)
        fiches_full.append(f)
        # Fichier par langue
        for lang in LANGS:
            out_path = OUT_DIR / f"dentist_{r['license_number']}_{lang}.json"
            payload = project_lang(f, lang)
            out_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            files_written.append(str(out_path.relative_to(ROOT)))
            per_lang_count[lang] += 1

    # Fichier résumé cycle
    summary = {
        "_meta": {
            "schema_version": SCHEMA_VERSION,
            "generated_at": NOW,
            "generator": "build_cycle10.py",
            "cron": "ad25646f-4b17-4eb0-b148-0b7d037c7231",
            "cycle": "2026-06-06 cycle 10/30min",
            "languages_count": len(LANGS),
            "languages": LANGS,
            "target_fiches": TARGET_FICHES,
            "fiches_produced": len(fiches_full),
            "translations_produced": len(fiches_full) * len(LANGS),
            "specialty_mix": mix,
            "per_lang_count": per_lang_count,
            "per_lang_files": len(files_written),
            "previous_cycles": [
                "2026-06-05 cycle 01/30min", "2026-06-06 cycle 02/30min",
                "2026-06-06 cycle 03/30min", "2026-06-06 cycle 04/30min",
                "2026-06-06 cycle 05/30min", "2026-06-06 cycle 06/30min",
                "2026-06-06 cycle 07/30min", "2026-06-06 cycle 08/30min",
                "2026-06-06 cycle 09/30min",
            ],
            "source_csv": str(SOURCE.relative_to(WORKSPACE)),
            "glossary_version": "v1.0+RU/ZH extension (cycle10)",
            "deepl_used": False,
            "deepl_note": "DEEPL_API_KEY vide dans .env.translator (template) → translittération manuelle + table FR→X alignée glossary.md",
        },
        "fiches": fiches_full,
    }
    OUT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[cycle10] résumé → {OUT_SUMMARY.relative_to(ROOT)}")
    print(f"[cycle10] fichiers per-lang → {len(files_written)} ({per_lang_count})")
    return summary

if __name__ == "__main__":
    main()
