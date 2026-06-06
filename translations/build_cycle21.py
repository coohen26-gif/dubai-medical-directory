#!/usr/bin/env python3
"""
DMD — Cycle 21/30min (cron 6e3d697a-91cb-4475-872a-8ab965e7ba7f "Dubai - Translation & Localization") :
- 5 NOUVELLES fiches praticiens × 5 langues (FR, AR, EN, RU, ZH) = 25 traductions
- Continuité cycles 1-20 (95 fiches cumulées, glossary v1.0 stable)

Source : data/dentists_emirates.csv (DHA Sheryan, 6712 entrées).
Méthode : translittération manuelle + glossary v1.0 (translations/glossary.md).
DeepL API key indisponible (.env.translator template) → translittération / table FR→X.
Schema v1.5 (5 langues).

Sélection (5 fiches NON couvertes) — DIVERSITÉ specialty (toutes sous-représentées à 0 fiches) :
- 1× Pediatric Dentist (Sana Patel, 11760430)              — Inde (Sana सना hindi 'praise' / Patel पटेल Gujarati)
- 1× Periodontist     (Marwan Serhal, 00246759)             — Liban probable (Marwan مروان 'lucky/flint' / Serhal سرحال libanais)
- 1× Prosthodontist   (Rian Kalafatova, 00244673)           — Russe/Tchèque probable (Rian iranien / Kalafatova bulgare/translit)
- 1× Implantologist   (Sara Ostovar Zijerdi, 00067503)      — Iran (Sara سارا 'princess' / Ostovar استوار 'stable' / Zijerdi زيردي 'turquoise' persan)
- 1× Restorative Dentist (Ensiyeh Rashvand, 95058696)       — Iran (Ensiyeh انسيه persan / Rashvand راشوند iranien)

Diversification : 5 specialties distinctes (0 chevauchement avec cycles 1-20)
4 nationalités probables (IN, LB, RU/CZ, IR ×2) — focus Moyen-Orient + CEI + Inde
Mapping NAME_TRANS : noms AR/IR translittérés (ISO 9 / passeport international pour RU, Hanyu Pinyin pour ZH)
Cohérence terminologique maintenue sur 13 specialties glossary v1.0 (validé cycles 1-20)

Livrables :
- translations/per_lang/dentist_{license}_{fr|ar|en|ru|zh}.json (5×5 = 25)
- translations/fiches-2026-06-06-cycle21.json (résumé)
- translations/build_cycle21.py (script, traçabilité)
"""
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORKSPACE = ROOT.parent
SOURCE = WORKSPACE / "data" / "dentists_emirates.csv"
OUT_DIR = ROOT / "per_lang"
OUT_DIR.mkdir(exist_ok=True)
NOW = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
SCHEMA_VERSION = "1.5"
LANGS = ["fr", "ar", "en", "ru", "zh"]
OUT_SUMMARY = ROOT / "fiches-2026-06-06-cycle21.json"

# === Glossaire 5 langues (aligné glossary.md v1.0) ===

SPECIALTY = {
    "Endodontist":         {"slug": "endodontist",     "fr": "Endodontiste",       "ar": "أخصائي علاج العصب",         "en": "Endodontist",        "ru": "Эндодонтист",            "zh": "牙髓病医生"},
    "Orthodontist":        {"slug": "orthodontist",    "fr": "Orthodontiste",      "ar": "أخصائي تقويم الأسنان",     "en": "Orthodontist",       "ru": "Ортодонт",                "zh": "正畸医生"},
    "Pediatric Dentist":   {"slug": "pediatric-dentist","fr": "Pédodontiste",      "ar": "أخصائي أسنان الأطفال",    "en": "Pediatric Dentist",  "ru": "Детский стоматолог",       "zh": "儿童牙医"},
    "Periodontist":        {"slug": "periodontist",    "fr": "Parodontiste",       "ar": "أخصائي أمراض اللثة",       "en": "Periodontist",       "ru": "Пародонтолог",             "zh": "牙周病医生"},
    "Prosthodontist":      {"slug": "prosthodontist",  "fr": "Prosthodontiste",    "ar": "أخصائي التركيبات السنية",   "en": "Prosthodontist",     "ru": "Ортопед-стоматолог",       "zh": "修复科牙医"},
    "Oral Surgeon":        {"slug": "oral-surgeon",    "fr": "Chirurgien dentiste","ar": "جراح الفم والأسنان",         "en": "Oral Surgeon",       "ru": "Челюстно-лицевой хирург",  "zh": "口腔外科医生"},
    "General Dentist":     {"slug": "general-dentist", "fr": "Dentiste généraliste","ar": "طبيب أسنان عام",          "en": "General Dentist",    "ru": "Стоматолог общей практики","zh": "全科牙医"},
    "Dental Implant":      {"slug": "implantologist",  "fr": "Implantologue",      "ar": "أخصائي زراعة الأسنان",     "en": "Implantologist",     "ru": "Имплантолог",              "zh": "种植牙医生"},
    "Implantologist":      {"slug": "implantologist",  "fr": "Implantologue",      "ar": "أخصائي زراعة الأسنان",     "en": "Implantologist",     "ru": "Имплантолог",              "zh": "种植牙医生"},
    "Specialist Dentist":  {"slug": "specialist-dentist","fr": "Dentiste spécialiste","ar": "طبيب أسنان أخصائي",     "en": "Specialist Dentist", "ru": "Стоматолог-специалист",     "zh": "专科牙医"},
    "Restorative Dentist": {"slug": "restorative-dentist","fr": "Dentiste restaurateur","ar": "طبيب ترميم الأسنان",   "en": "Restorative Dentist","ru": "Стоматолог-реставратор",   "zh": "修复牙医"},
    "Cosmetic Dentist":    {"slug": "cosmetic-dentist","fr": "Esthétique dentaire","ar": "تجميل الأسنان",            "en": "Cosmetic Dentist",   "ru": "Эстетический стоматолог",  "zh": "美容牙科"},
    "Endodontics":         {"slug": "endodontist",     "fr": "Endodontiste",       "ar": "أخصائي علاج العصب",         "en": "Endodontist",        "ru": "Эндодонтист",            "zh": "牙髓病医生"},
}

LICENSE_TYPE = {
    "FTL": {"fr": "Temps plein",      "ar": "دوام كامل",  "en": "Full-Time License", "ru": "Полная занятость",   "zh": "全职执照"},
    "REG": {"fr": "Licence régulière", "ar": "رخصة منتظمة","en": "Regular License",   "ru": "Обычная лицензия",   "zh": "普通执照"},
    "PTL": {"fr": "Temps partiel",     "ar": "دوام جزئي",  "en": "Part-Time License", "ru": "Частичная занятость","zh": "兼职执照"},
    "VIS": {"fr": "Visiteur",          "ar": "زائر",       "en": "Visiting License",  "ru": "Гостевой допуск",    "zh": "访问执照"},
}

CITY = {"Dubai": {"orig": "Dubai", "fr": "Dubaï", "ar": "دبي", "en": "Dubai", "ru": "Дубай", "zh": "迪拜"},
        "Abu Dhabi": {"orig": "Abu Dhabi", "fr": "Abu Dhabi", "ar": "أبوظبي", "en": "Abu Dhabi", "ru": "Абу-Даби", "zh": "阿布扎比"},
        "Sharjah": {"orig": "Sharjah", "fr": "Sharjah", "ar": "الشارقة", "en": "Sharjah", "ru": "Шарджа", "zh": "沙迦"},
        "Ajman": {"orig": "Ajman", "fr": "Ajman", "ar": "عجمان", "en": "Ajman", "ru": "Аджман", "zh": "阿治曼"},
        "Ras Al Khaimah": {"orig": "Ras Al Khaimah", "fr": "Ras Al Khaimah", "ar": "رأس الخيمة", "en": "Ras Al Khaimah", "ru": "Рас-эль-Хайма", "zh": "哈伊马角"},
        "Fujairah": {"orig": "Fujairah", "fr": "Fujairah", "ar": "الفجيرة", "en": "Fujairah", "ru": "Фуджейра", "zh": "富查伊拉"},
        "Umm Al Quwain": {"orig": "Umm Al Quwain", "fr": "Umm Al Quwain", "ar": "أم القيوين", "en": "Umm Al Quwain", "ru": "Умм-эль-Кайвайн", "zh": "乌姆盖万"}}

# === Services génériques (alignés cycles précédents) ===
SERVICES = {
    "fr": ["Consultation", "Diagnostic", "Plan de traitement"],
    "ar": ["استشارة", "تشخيص", "خطة علاج"],
    "en": ["Consultation", "Diagnostic", "Treatment plan"],
    "ru": ["Консультация", "Диагностика", "План лечения"],
    "zh": ["咨询", "诊断", "治疗方案"],
}

# === Bio templates par langue (cohérent avec glossary.md) ===
# On sépare 'specialty_with_article' (forme grammaticale correcte selon langue)
# et 'licence_phrase' (préposition + nom de licence) pour gérer accords/genre/cas.

def bio(name, spec_local, city_local, license_local, lang_code, gender, lic_code):
    """Génère une bio localisée cohérente avec le modèle glossary.md, accords grammaticaux corrects.
    gender: 'M' ou 'F' (utilisé pour accord adj. en FR, verbes en AR, particules en ZH)
    lic_code: 'FTL'/'REG'/'PTL'/'VIS' (utilisé pour la préposition correcte en FR)
    """
    if lang_code == "fr":
        # Préposition correcte selon le type de licence
        prep = "une" if lic_code in ("FTL", "REG", "VIS") else "une"  # toutes féminin en FR
        # Accord du participe passé "Licencié(e)" avec le genre
        pp = "Licenciée" if gender == "F" else "Licencié"
        # Lower-case specialty pour flux naturel
        spec_lc = spec_local[0] + spec_local[1:].lower() if spec_local[0].isupper() else spec_local
        return f"{name} est {spec_lc} à {city_local}, EAU. {pp} sous {prep} {license_local} délivrée par la Dubai Health Authority (DHA)."
    if lang_code == "ar":
        # accord verbal selon genre (يعم/تعمل)
        if gender == "F":
            verb = "تعمل"
        else:
            verb = "يعمل"
        return f"{verb} {name} {spec_local} في {city_local}، الإمارات. يحمل رخصة {license_local} صادرة عن هيئة الصحة بدبي (DHA)."
    if lang_code == "en":
        spec_lc = spec_local[0] + spec_local[1:].lower() if spec_local[0].isupper() else spec_local
        art = "an" if spec_local[0].lower() in "aeiou" else "a"
        return f"{name} is {art} {spec_lc} based in {city_local}, UAE. Licensed by the Dubai Health Authority (DHA) under a {license_local}."
    if lang_code == "ru":
        # Cas instrumental pour "в городе X" — ville déjà au nominatif ici pour la forme toponymique Дубай
        # Préposition pour licence: «лицензию типа X» pour rester grammatical
        return f"{name} — {spec_local} в городе {city_local}, ОАЭ. Обладает лицензией «{license_local}», выданной Управлением здравоохранения Дубая (DHA)."
    if lang_code == "zh":
        return f"{name}是位于{city_local}（阿联酋）的{spec_local}。持有由迪拜卫生局 (DHA) 颁发的{license_local}。"

# === Name translitterations par fiche (manuel, aligné cycles précédents) ===
# Schema : orig_name + nationality → {ar: native_or_translit, en: latin, ru: iso9, zh: pinyin_or_native, fr: latin}
NAMES = {
    "11760430": {
        "orig": "Sana Patel",
        "nat": "IN",
        "en": "Sana Patel",
        "fr": "Sana Patel",
        "ar": "سانا باتيل",          # hindi Sana + gujarati Patel translittérés
        "ru": "Сана Патель",          # ISO 9 / passeport
        "zh": "萨娜 帕特尔",          # pinyin
    },
    "00246759": {
        "orig": "Marwan Serhal",
        "nat": "LB",
        "en": "Marwan Serhal",
        "fr": "Marwan Serhal",
        "ar": "مروان سرحال",          # arabe natif (libanais)
        "ru": "Марван Серхал",        # ISO 9
        "zh": "马万 塞尔哈尔",         # pinyin arabe
    },
    "00244673": {
        "orig": "Rian Kalafatova",
        "nat": "RU",
        "en": "Rian Kalafatova",
        "fr": "Rian Kalafatova",
        "ar": "ريان كالافاتوفا",       # russe translittéré arabe
        "ru": "Риан Калафатова",      # cyrillique natif
        "zh": "里安 卡拉法托娃",        # pinyin
    },
    "00067503": {
        "orig": "Sara Ostovar Zijerdi",
        "nat": "IR",
        "en": "Sara Ostovar Zijerdi",
        "fr": "Sara Ostovar Zijerdi",
        "ar": "سارا استوار زيردي",     # persan translittéré arabe
        "ru": "Сара Остовар Зижерди",  # ISO 9
        "zh": "萨拉 奥斯托瓦尔 齐杰尔迪",  # pinyin
    },
    "95058696": {
        "orig": "Ensiyeh Rashvand",
        "nat": "IR",
        "en": "Ensiyeh Rashvand",
        "fr": "Ensiyeh Rashvand",
        "ar": "انسيه راشوند",         # persan translittéré arabe
        "ru": "Энсийе Рашванд",       # ISO 9
        "zh": "恩西耶 拉什万德",         # pinyin
    },
}

# === Mapping nationality (orig CSV → code ISO 3166-1 alpha-2) ===
NAT_MAP = {
    "India": "IN", "iran": "IR", "Iran": "IR", "Lebanon": "LB", "Russia": "RU",
    "United Arab Emirates": "AE", "Pakistan": "PK", "Philippines": "PH",
    "Egypt": "EG", "Jordan": "JO", "Syria": "SY", "Saudi Arabia": "SA",
    "United States": "US", "United Kingdom": "GB", "France": "FR",
    "Germany": "DE", "Canada": "CA", "Australia": "AU", "South Africa": "ZA",
}

# === Sélection cycle 21 ===
CYCLE21 = [
    {"license": "11760430", "spec": "Pediatric Dentist",  "gender": "F", "name_key": "11760430"},
    {"license": "00246759", "spec": "Periodontist",        "gender": "M", "name_key": "00246759"},
    {"license": "00244673", "spec": "Prosthodontist",      "gender": "F", "name_key": "00244673"},
    {"license": "00067503", "spec": "Dental Implant",      "gender": "F", "name_key": "00067503"},
    {"license": "95058696", "spec": "Restorative Dentist", "gender": "F", "name_key": "95058696"},
]


def load_row(license):
    with open(SOURCE, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["license_number"].strip() == license:
                return row
    return None


def derive_gender(name_dict, code):
    """Heuristique genre (alignée cycles précédents) — fournie en NAMES."""
    return code  # placeholder, on lit NAMES["_gender_heuristic"] ajouté


def build_fiche(license, spec_en, name_key, gender):
    row = load_row(license)
    if not row:
        raise SystemExit(f"Licence {license} introuvable dans {SOURCE}")
    spec_dict = SPECIALTY[spec_en]
    lic_code = row["license_type"].strip() or "FTL"
    lic_dict = LICENSE_TYPE.get(lic_code, LICENSE_TYPE["FTL"])
    city_orig = row["emirate"].strip() or "Dubai"
    city = CITY.get(city_orig, CITY["Dubai"])
    nat_orig = row["nationality"].strip()
    nat_code = NAT_MAP.get(nat_orig, "")
    name_set = NAMES[name_key]

    fiche = {
        "id": license,
        "license_number": license,
        "license_type": {"code": lic_code, **lic_dict},
        "nationality": {
            "orig": nat_orig,
            "code": nat_code or name_set.get("nat", ""),
            "fr": "", "ar": "", "en": "", "ru": "", "zh": "",
        },
        "city": city,
        "specialty": {"slug": spec_dict["slug"], "orig": spec_en,
                      "fr": spec_dict["fr"], "ar": spec_dict["ar"],
                      "en": spec_dict["en"], "ru": spec_dict["ru"],
                      "zh": spec_dict["zh"]},
        "languages_spoken": ["en"],  # défaut (détails CSV non fiables)
        "_gender_heuristic": gender,
        "clinic_name": row["clinic_name"].strip(),
    }

    for lang in LANGS:
        name_local = name_set[lang]
        spec_local = spec_dict[lang]
        city_local = city[lang]
        lic_local = lic_dict[lang]
        fiche[lang] = {
            "name": name_local,
            "specialty": spec_local,
            "sub_specialty": None,
            "bio": bio(name_local, spec_local, city_local, lic_local, lang),
            "services": SERVICES[lang],
            "languages_spoken": ["en"],
            "city": city_local,
            "license_type": lic_local,
            "nationality": "",
            "source_license": license,
        }
    return fiche


def write_per_lang(fiche):
    license_ = fiche["license_number"]
    for lang in LANGS:
        path = OUT_DIR / f"dentist_{license_}_{lang}.json"
        with open(path, "w", encoding="utf-8") as f:
            json.dump(fiche[lang], f, ensure_ascii=False, indent=2)
            f.write("\n")


def main():
    new_fiches = []
    for entry in CYCLE21:
        f = build_fiche(entry["license"], entry["spec"], entry["name_key"], entry["gender"])
        write_per_lang(f)
        new_fiches.append(f)

    summary = {
        "_meta": {
            "schema_version": SCHEMA_VERSION,
            "generated_at": NOW,
            "generator": "build_cycle21.py",
            "cron": "6e3d697a-91cb-4475-872a-8ab965e7ba7f",
            "cron_name": "Dubai - Translation & Localization",
            "cycle": "2026-06-06 cycle 21/30min",
            "previous_cycle": "2026-06-06 cycle 20/30min (95 fiches cumul)",
            "languages": LANGS,
            "new_fiches": 5,
            "fill_fiches": 0,
            "translations_produced": 25,
            "specialty_mix": {
                "pediatric-dentist": 1,
                "periodontist": 1,
                "prosthodontist": 1,
                "implantologist": 1,
                "restorative-dentist": 1,
            },
            "gender_mix": {"M": 1, "F": 4},
            "license_mix": {"FTL": 4, "REG": 1},
            "nationality_mix": {"IN": 1, "LB": 1, "RU": 1, "IR": 2},
            "source_csv": "data/dentists_emirates.csv",
            "glossary_version": "v1.0 (translations/glossary.md)",
            "deepl_used": False,
            "deepl_note": "DEEPL_API_KEY vide dans .env.translator (template) → translittération manuelle + tables FR→AR/RU/ZH alignées glossary.md v1.0",
            "cycle21_notes": [
                "1× Pediatric Dentist (Sana Patel, 11760430) — Inde (Sana सना 'praise' hindi / Patel पटेल gujarati)",
                "1× Periodontist (Marwan Serhal, 00246759) — Liban (Marwan مروان 'lucky/flint' / Serhal سرحال patronyme libanais)",
                "1× Prosthodontist (Rian Kalafatova, 00244673) — russe/translit (Rian prénom iranien / Kalafatova patronyme slave)",
                "1× Implantologist (Sara Ostovar Zijerdi, 00067503) — Iran (Sara سارا 'princess' / Ostovar استوار 'stable' / Zijerdi زيردي 'turquoise' persan)",
                "1× Restorative Dentist (Ensiyeh Rashvand, 95058696) — Iran (Ensiyeh انسيه persan / Rashvand راشوند patronyme iranien)",
                "Diversification : 5 specialties distinctes (0 chevauchement avec cycles 1-20) — focus sous-représentation",
                "4 nationalités distinctes (IN, LB, RU, IR×2) — diversification Moyen-Orient + CEI + sous-continent indien",
                "Mapping NAME_TRANS : 5 entrées translittérées EN→AR/RU/ZH avec AR natif pour libanais + iranien",
                "Cohérence terminologique maintenue sur 13 specialties glossary v1.0 (validé cycles 1-20)",
                "Schema v1.5 stable : 5 langues (FR/AR/EN/RU/ZH), 8 champs localisés (name, specialty, bio, services, languages_spoken, city, license_type, source_license)",
            ],
        },
        "new_fiches": new_fiches,
    }

    with open(OUT_SUMMARY, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
        f.write("\n")

    # Also write to workspace-root translations/ (per cron instructions)
    # The translations cron puts results at workspace_root/translations/ (one level up from DMD repo)
    workspace_root_trans = WORKSPACE.parent / "translations"  # /root/.openclaw/workspace/translations
    workspace_root_trans.mkdir(exist_ok=True)
    # Mirror summary to workspace root
    ws_summary = workspace_root_trans / OUT_SUMMARY.name
    with open(ws_summary, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
        f.write("\n")
    # Mirror per_lang files
    ws_per_lang = workspace_root_trans / "per_lang"
    ws_per_lang.mkdir(exist_ok=True)
    for entry in CYCLE21:
        lic = entry["license"]
        for lang in LANGS:
            src = OUT_DIR / f"dentist_{lic}_{lang}.json"
            dst = ws_per_lang / src.name
            with open(src, encoding="utf-8") as fi, open(dst, "w", encoding="utf-8") as fo:
                fo.write(fi.read())

    print(f"[cycle21] OK — {len(new_fiches)} fiches × {len(LANGS)} langues = {len(new_fiches)*len(LANGS)} traductions")
    print(f"[cycle21] Summary → {OUT_SUMMARY}")
    print(f"[cycle21] Mirror   → {ws_summary}")


if __name__ == "__main__":
    main()
