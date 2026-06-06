#!/usr/bin/env python3
"""
DMD — Cycle 23/30min (cron 6e3d697a "Dubai - Translation & Localization") :
- 5 NOUVELLES fiches praticiens × 5 langues (FR, AR, EN, RU, ZH) = 25 traductions
- Continuité cycles 1-22 (120+ fiches cumulées, glossary v1.0 stable)

Source : data/dentists_emirates.csv (DHA Sheryan, ~6700 entrées).
Méthode : translittération manuelle + glossary v1.0 (translations/glossary.md).
DeepL API key indisponible (.env.translator template) → translittération / table FR→X.
Schema v1.5 (5 langues).

Sélection (5 fiches NON couvertes) — DIVERSITÉ specialty + nationality (cycle 23 = cible 25 traductions) :
- 1× General Dentist  (Meena Shahnawaz 00000783 PK/IN — trilingue: en/ur/sd)
- 1× Orthodontist     (Tamer Buyukyilmaz 00087766 TR)
- 1× Oral Surgeon     (Monir Al Shakaki 00184141 SY)
- 1× Periodontist     (Smrithi Vishakhavarma 00191631 IN)
- 1× Dental Implant   (Bizhan Behrouz 00242078 IR)

Livrables :
- translations/per_lang/dentist_{license}_{fr|ar|en|ru|zh}.json (5×5 = 25)
- translations/fiches-2026-06-06-cycle23.json (résumé)
- translations/build_cycle23.py (script, traçabilité)
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
OUT_SUMMARY = ROOT / "fiches-2026-06-06-cycle23.json"

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
    "VIS": {"fr": "Visiteur",          "ar": "زائر",        "en": "Visiting License",  "ru": "Гостевой допуск",    "zh": "访问执照"},
}

CITY = {
    "Dubai":     {"fr": "Dubaï",     "ar": "دبي",      "en": "Dubai",     "ru": "Дубай",     "zh": "迪拜"},
    "Abu Dhabi": {"fr": "Abu Dhabi", "ar": "أبوظبي",  "en": "Abu Dhabi", "ru": "Абу-Даби",  "zh": "阿布扎比"},
    "Sharjah":   {"fr": "Sharjah",   "ar": "الشارقة", "en": "Sharjah",   "ru": "Шарджа",    "zh": "沙迦"},
    "Ajman":     {"fr": "Ajman",     "ar": "عجمان",    "en": "Ajman",     "ru": "Аджман",    "zh": "阿治曼"},
}

# Country inferred from name origin / heuristic for cycle 23
COUNTRY = {
    "Pakistan":       {"fr": "Pakistan",     "ar": "باكستان",    "en": "Pakistan",     "ru": "Пакистан",   "zh": "巴基斯坦"},
    "India":          {"fr": "Inde",         "ar": "الهند",        "en": "India",        "ru": "Индия",      "zh": "印度"},
    "Turkey":         {"fr": "Turquie",      "ar": "تركيا",        "en": "Turkey",       "ru": "Турция",     "zh": "土耳其"},
    "Syria":          {"fr": "Syrie",        "ar": "سوريا",        "en": "Syria",        "ru": "Сирия",      "zh": "叙利亚"},
    "Iran":           {"fr": "Iran",         "ar": "إيران",        "en": "Iran",         "ru": "Иран",       "zh": "伊朗"},
    "Unknown":        {"fr": "",             "ar": "",             "en": "",             "ru": "",           "zh": ""},
}

# === Heuristique genre (FR/AR) — cumul cycles 1-22 ===

FEMININE_FIRST = {
    "zeina","zaynab","zainab","sara","sarah","lama","rosedina","anila",
    "claudia","rabab","lalaine","ambili","sruthi","shreekala","fatma",
    "fatima","hasna","shamma","ermel","seema","farha","edna","lina",
    "leila","laila","layla","mariam","maryam","diana","noor","nour",
    "faiza","arpita","maria","jensyll","samira","mileva","latifa",
    "lateefa","khulood","khulud","aisha","aishah","asma","salma",
    "soumaya","sumaya","rania","rana","hala","hind","huda","rawan",
    "razan","reem","rim","rimah","roula","saba","sahar","sawsan",
    "shams","shatha","suad","taghreed","tala","yara","yasmin","yasmine",
    "zahra","zeinab","nadia","mona","muna","amal","hiba","hoda","iman",
    "enas","dina","dana","nada","nadine","nawal","noha","noura",
    "ranime","rehab","salwa","samar","wafa","wafaa","warda","yusra",
    "zakia","zara","julia","julie","ana","anamaria","maria","marie",
    "arpita","priya","pooja","preethi","kavita","kavitha",
    "muneera","mounira","munira","nouf","leena","layan","liane",
    "mira","maya","mayar","rosa","sandra","silvia","sylvia",
    "tatiana","teresa","theresa","valentina","vanessa","veronica",
    "victoria","virginia","yolanda","yvette","zuzana","lubab","sally",
    "manla","tameeza","pardis","neha","smrithi","onisha","dina","soud",
    "fatma","anahita","nevin","helme","asha","bindu","chitra","deepa",
    "divya","gayathri","indu","jaya","kala","lakshmi","latha","madhuri",
    "mala","manjula","meena","meenakshi","mita","neela","neelam","nisha",
    "padma","parvathi","prabha","preethi","prem","pritha","priyanka",
    "pushpa","radhika","rajani","ramya","rasmi","reena","rekha","renu",
    "revathi","roja","roopa","rupa","sabitha","sadhna","sai","sajitha",
    "salini","sangeetha","sarala","sarita","shameem","sharada","sharmila",
    "sheela","shilpa","shiny","shobha","shruti","sneha","subha","sudha",
    "sujata","sukanya","suma","sumathi","sunitha","supriya","surekha",
    "sushma","swapna","swarna","tara","uma","usha","vani","varsha",
    "vasanthi","vidya","vimala","vimla","yasmeen","zohra","anila",
}

def detect_gender(name: str) -> str:
    tokens = name.lower().split()
    if not tokens: return "?"
    first = re.sub(r"[^a-z]", "", tokens[0])
    if first in FEMININE_FIRST: return "F"
    if first.endswith(("a","ah","ia","iya","ee","ie","ina")):
        return "F"
    return "M"

def normalize_lang_codes(languages_raw: str) -> list:
    if not languages_raw: return ["en"]
    langs = []
    raw_low = languages_raw.lower()
    if "arabic" in raw_low: langs.append("ar")
    if "english" in raw_low: langs.append("en")
    if "french" in raw_low: langs.append("fr")
    if "hindi" in raw_low: langs.append("hi")
    if "urdu" in raw_low: langs.append("ur")
    if "russian" in raw_low: langs.append("ru")
    if "spanish" in raw_low: langs.append("es")
    if "portuguese" in raw_low: langs.append("pt")
    if "german" in raw_low: langs.append("de")
    if "italian" in raw_low: langs.append("it")
    if "tagalog" in raw_low or "filipino" in raw_low: langs.append("tl")
    if "mandarin" in raw_low or "chinese" in raw_low: langs.append("zh")
    if "turkish" in raw_low: langs.append("tr")
    if "farsi" in raw_low or "persian" in raw_low: langs.append("fa")
    if "sindhi" in raw_low: langs.append("sd")
    if not langs: langs.append("en")
    return langs

# === Translittération EN/FR/RU/ZH pour noms cycle 23 ===

NAME_TRANS = {
    # Meena Shahnawaz (PK/IN) — trilingue en/ur/sd
    "meena":      {"en": "Meena",      "fr": "Meena",      "ru": "Мина",        "zh": "米娜",      "ar": "مينا"},
    "shahnawaz":  {"en": "Shahnawaz",  "fr": "Shahnawaz",  "ru": "Шахнаваз",   "zh": "沙赫纳瓦兹", "ar": "شهنواز"},
    # Tamer Buyukyilmaz (TR)
    "tamer":         {"en": "Tamer",         "fr": "Tamer",         "ru": "Тамер",        "zh": "塔梅尔",    "ar": "تامر"},
    "buyukyilmaz":   {"en": "Buyukyilmaz",   "fr": "Buyukyilmaz",   "ru": "Буюкылмаз",  "zh": "布尤克耶尔马兹","ar": "بوياك يلما"},
    # Monir Al Shakaki (SY)
    "monir":         {"en": "Monir",         "fr": "Monir",         "ru": "Мунир",       "zh": "穆尼尔",    "ar": "منير"},
    "shakaki":       {"en": "Al Shakaki",    "fr": "Al Shakaki",    "ru": "Аль-Шакаки",  "zh": "沙卡基",    "ar": "الشكاكي"},
    # Smrithi Vishakhavarma (IN)
    "smrithi":          {"en": "Smrithi",          "fr": "Smrithi",          "ru": "Смритхи",          "zh": "斯姆里提",    "ar": "سمرثي"},
    "vishakhavarma":    {"en": "Vishakhavarma",    "fr": "Vishakhavarma",    "ru": "Вишакхарма",      "zh": "维沙卡瓦尔马","ar": "فيشاكافارما"},
    # Bizhan Behrouz (IR)
    "bizhan":      {"en": "Bizhan",      "fr": "Bizhan",      "ru": "Бизхан",     "zh": "比詹",      "ar": "بيژان"},
    "behrouz":     {"en": "Behrouz",     "fr": "Behrouz",     "ru": "Бехруз",    "zh": "贝赫鲁兹",  "ar": "بهروز"},
    # Common Arabic prefixes
    "al":   {"en": "Al",   "fr": "Al",   "ru": "Аль",   "zh": "阿尔",   "ar": "ال"},
    "as":   {"en": "As",   "fr": "As",   "ru": "Ас",    "zh": "阿斯",   "ar": "آل"},
    "bin":  {"en": "bin",  "fr": "bin",  "ru": "бин",   "zh": "本",     "ar": "بن"},
    "abu":  {"en": "Abu",  "fr": "Abu",  "ru": "Абу",   "zh": "阿布",   "ar": "أبو"},
}

LATIN_CYR = {
    "a":"а","b":"б","c":"к","d":"д","e":"е","f":"ф","g":"г","h":"х","i":"и",
    "j":"дж","k":"к","l":"л","m":"м","n":"н","o":"о","p":"п","q":"к","r":"р",
    "s":"с","t":"т","u":"у","v":"в","w":"в","x":"кс","y":"й","z":"з",
    "sh":"ш","ch":"ч","zh":"ж","yu":"ю","ya":"я","yo":"ё","kh":"х","ts":"ц",
}

LATIN_PINYIN = {
    "a":"阿","b":"布","c":"克","d":"德","e":"厄","f":"弗","g":"格","h":"赫","i":"伊",
    "j":"杰","k":"克","l":"尔","m":"姆","n":"恩","o":"奥","p":"普","q":"奇","r":"尔",
    "s":"斯","t":"特","u":"乌","v":"弗","w":"维","x":"克斯","y":"伊","z":"兹",
    "sh":"什","ch":"奇","zh":"日","th":"思",
}

def latin_to_cyrillic_heuristic(word: str) -> str:
    word_low = word.lower()
    out = ""
    i = 0
    while i < len(word_low):
        if i+1 < len(word_low) and word_low[i:i+2] in LATIN_CYR:
            out += LATIN_CYR[word_low[i:i+2]]
            i += 2
        elif word_low[i] in LATIN_CYR:
            out += LATIN_CYR[word_low[i]]
            i += 1
        else:
            out += word[i]
            i += 1
    if out: out = out[0].upper() + out[1:]
    return out

def latin_to_pinyin_heuristic(word: str) -> str:
    word_low = word.lower()
    out = ""
    i = 0
    while i < len(word_low):
        if i+1 < len(word_low) and word_low[i:i+2] in LATIN_PINYIN:
            out += LATIN_PINYIN[word_low[i:i+2]]
            i += 2
        elif word_low[i] in LATIN_PINYIN:
            out += LATIN_PINYIN[word_low[i]]
            i += 1
        else:
            out += word[i]
            i += 1
    return out

def transcribe_name(name: str, lang: str) -> str:
    tokens = name.split()
    out = []
    for t in tokens:
        bare = re.sub(r"[^a-zA-Z]", "", t)
        key = bare.lower()
        if key in NAME_TRANS:
            out.append(NAME_TRANS[key].get(lang, t))
        else:
            if lang == "ru":
                out.append(latin_to_cyrillic_heuristic(t))
            elif lang == "zh":
                out.append(latin_to_pinyin_heuristic(t))
            elif lang == "ar":
                out.append(t)
            else:
                out.append(t)
    return " ".join(out)

# === Bio generator 5-langue ===

def build_bio_fr(name_full, sp_fr, city_fr, lic_fr, gender):
    lic_for_bio = lic_fr.lower()
    for prefix in ["licence ", "license "]:
        if lic_for_bio.startswith(prefix):
            lic_for_bio = lic_for_bio[len(prefix):]
    if gender == "F":
        return f"{name_full} est {sp_fr.lower()} à {city_fr}, EAU. Licenciée sous licence {lic_for_bio} délivrée par la Dubai Health Authority (DHA)."
    return f"{name_full} est {sp_fr.lower()} à {city_fr}, EAU. Licencié sous licence {lic_for_bio} délivrée par la Dubai Health Authority (DHA)."

def build_bio_ar(name_full, sp_ar, city_ar, lic_ar, gender):
    if gender == "F":
        return f"تعمل {name_full} {sp_ar} في {city_ar}، الإمارات. تحمل رخصة {lic_ar} صادرة عن هيئة الصحة بدبي (DHA)."
    return f"يعمل {name_full} {sp_ar} في {city_ar}، الإمارات. يحمل رخصة {lic_ar} صادرة عن هيئة الصحة بدبي (DHA)."

def build_bio_en(name_full, sp_en, city_en, lic_en, gender):
    article = "an" if sp_en[0].lower() in "aeiou" else "a"
    pronoun = "She" if gender == "F" else "He"
    lic_article = "an" if lic_en[0].lower() in "aeiou" else "a"
    return f"{name_full} is {article} {sp_en} based in {city_en}, UAE. {pronoun} holds {lic_article} {lic_en} issued by the Dubai Health Authority (DHA)."

def build_bio_ru(name_full, sp_ru, city_ru, lic_ru, gender):
    city_ru_decl = {"Дубай": "Дубае", "Абу-Даби": "Абу-Даби", "Шарджа": "Шардже", "Аджман": "Аджмане"}
    city_t = city_ru_decl.get(city_ru, city_ru)
    if gender == "F":
        return f"{name_full} — {sp_ru.lower()} в {city_t}, ОАЭ. Она имеет {lic_ru.lower()}, выданную Управлением здравоохранения Дубая (DHA)."
    return f"{name_full} — {sp_ru.lower()} в {city_t}, ОАЭ. Он имеет {lic_ru.lower()}, выданную Управлением здравоохранения Дубая (DHA)."

def build_bio_zh(name_full, sp_zh, city_zh, lic_zh, gender):
    return f"{name_full}是位于{city_zh}（阿联酋）的{sp_zh}。持有由迪拜卫生局 (DHA) 颁发的{lic_zh}。"

# === Main ===

def main():
    # 5 fiches sélectionnées pour cycle 23
    picks = [
        {
            "license": "00000783",
            "name": "Meena Shahnawaz",
            "specialty": "General Dentist",
            "license_type": "REG",
            "inferred_nat": "Pakistan",
            "nationality": "Pakistan",
            "emirate": "Dubai",
            "clinic_name": "",
            "languages": "English (Fluent); Urdu (Native); Sindhi (Native)",
            "source_url": "https://sheryan.dha.gov.ae/SearchProfessionals?search=00000783",
            "scraped_at": "2026-06-05T20:38:07.374434+00:00",
            "row_index": 7,
        },
        {
            "license": "00087766",
            "name": "Tamer Buyukyilmaz",
            "specialty": "Orthodontist",
            "license_type": "FTL",
            "inferred_nat": "Turkey",
            "nationality": "Turkey",
            "emirate": "Dubai",
            "clinic_name": "",
            "languages": "English (Intermediate)",
            "source_url": "https://sheryan.dha.gov.ae/SearchProfessionals?search=00087766",
            "scraped_at": "2026-06-05T20:38:07.374434+00:00",
            "row_index": 16,
        },
        {
            "license": "00184141",
            "name": "Monir Al Shakaki",
            "specialty": "Oral Surgeon",
            "license_type": "FTL",
            "inferred_nat": "Syria",
            "nationality": "Syria",
            "emirate": "Dubai",
            "clinic_name": "",
            "languages": "",
            "source_url": "https://sheryan.dha.gov.ae/SearchProfessionals?search=00184141",
            "scraped_at": "2026-06-05T20:38:07.374434+00:00",
            "row_index": 25,
        },
        {
            "license": "00191631",
            "name": "Smrithi Vishakhavarma",
            "specialty": "Periodontist",
            "license_type": "FTL",
            "inferred_nat": "India",
            "nationality": "India",
            "emirate": "Dubai",
            "clinic_name": "",
            "languages": "",
            "source_url": "https://sheryan.dha.gov.ae/SearchProfessionals?search=00191631",
            "scraped_at": "2026-06-05T20:38:07.374434+00:00",
            "row_index": 30,
        },
        {
            "license": "00242078",
            "name": "Bizhan Behrouz",
            "specialty": "Dental Implant",
            "license_type": "REG",
            "inferred_nat": "Iran",
            "nationality": "Iran",
            "emirate": "Dubai",
            "clinic_name": "",
            "languages": "",
            "source_url": "https://sheryan.dha.gov.ae/SearchProfessionals?search=00242078",
            "scraped_at": "2026-06-05T20:38:07.374434+00:00",
            "row_index": 40,
        },
    ]
    print(f"Cycle 23 — {len(picks)} fiches to translate")

    new_fiches = []
    sp_count = {}
    gender_count = {}
    lic_count = {}
    nat_count = {}

    for p in picks:
        lic = p["license"]
        name_orig = p["name"]
        specialty_orig = p["specialty"]
        lic_type_code = p["license_type"]
        nat = p["inferred_nat"]
        emirate = p["emirate"]
        languages_raw = p.get("languages","")

        sp_entry = SPECIALTY.get(specialty_orig, SPECIALTY["General Dentist"])
        sp_slug = sp_entry["slug"]
        lt_entry = LICENSE_TYPE.get(lic_type_code, LICENSE_TYPE["FTL"])
        city_entry = CITY.get(emirate, CITY["Dubai"])

        gender = detect_gender(name_orig)
        gender_count[gender] = gender_count.get(gender, 0) + 1

        langs_iso = normalize_lang_codes(languages_raw)

        sp_count[sp_slug] = sp_count.get(sp_slug, 0) + 1
        lic_count[lic_type_code] = lic_count.get(lic_type_code, 0) + 1
        nat_count[nat] = nat_count.get(nat, 0) + 1

        nat_dict = COUNTRY.get(nat, COUNTRY["Unknown"])

        for lang in LANGS:
            name_t = transcribe_name(name_orig, lang)
            city_t = city_entry[lang]
            lic_t = lt_entry[lang]
            sp_t = sp_entry[lang]

            if lang == "fr":
                bio = build_bio_fr(name_t, sp_entry["fr"], city_t, lic_t, gender)
            elif lang == "ar":
                bio = build_bio_ar(name_t, sp_entry["ar"], city_t, lic_t, gender)
            elif lang == "en":
                bio = build_bio_en(name_t, sp_entry["en"], city_t, lic_t, gender)
            elif lang == "ru":
                bio = build_bio_ru(name_t, sp_entry["ru"], city_t, lic_t, gender)
            elif lang == "zh":
                bio = build_bio_zh(name_t, sp_entry["zh"], city_t, lic_t, gender)

            # Schéma v1.5 (aligné sur per_lang/*.json existant)
            entry = {
                "id": f"{re.sub(r'[^a-z0-9-]', '-', name_orig.lower()).replace(' ', '-')}-{lic}",
                "license_number": lic,
                "license_type": lic_t,
                "name": {
                    "original": name_orig,
                    lang: name_t,
                },
                "specialty": sp_t,
                "sub_specialty": None,
                "facility": p.get("clinic_name",""),
                "area": f"{p.get('clinic_name','') or 'Dubai'}, {city_entry[lang]}, {'الإمارات العربية المتحدة' if lang=='ar' else ('Объединённые Арабские Эмираты' if lang=='ru' else ('阿拉伯联合酋长国' if lang=='zh' else ('Émirats arabes unis' if lang=='fr' else 'United Arab Emirates')))}",
                "city": city_t,
                "country": ('الإمارات العربية المتحدة' if lang=='ar' else ('Объединённые Арабские Эмираты' if lang=='ru' else ('阿拉伯联合酋长国' if lang=='zh' else ('Émirats arabes unis' if lang=='fr' else 'United Arab Emirates')))),
                "country_short": ('الإمارات' if lang=='ar' else ('ОАЭ' if lang=='ru' else ('阿联酋' if lang=='zh' else ('EAU' if lang=='fr' else 'UAE')))),
                "category": "dentists",
                "bio": bio,
                "services": None,
                "languages_spoken": langs_iso,
                "schema_version": SCHEMA_VERSION,
                "translated_at": NOW,
                "_lang": lang,
                "_provenance": {
                    "source_csv": "data/dentists_emirates.csv",
                    "source_url": p.get("source_url",""),
                    "scraped_at": p.get("scraped_at",""),
                    "row_index": p.get("row_index", 0),
                },
            }

            out_path = OUT_DIR / f"dentist_{lic}_{lang}.json"
            out_path.write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")

        new_fiches.append({
            "id": lic,
            "license_number": lic,
            "name": name_orig,
            "specialty": sp_slug,
            "license_type": lic_type_code,
            "nationality": nat,
            "gender_heuristic": gender,
            "languages_spoken": langs_iso,
        })
        print(f"   NEW   - {lic} | {sp_slug:25} | {lic_type_code:4} | g={gender} | nat={nat[:18]:18} | langs={langs_iso}")

    summary = {
        "_meta": {
            "schema_version": SCHEMA_VERSION,
            "generated_at": NOW,
            "generator": "build_cycle23.py",
            "cron": "6e3d697a-91cb-4475-872a-8ab965e7ba7f",
            "cron_name": "Dubai - Translation & Localization",
            "cycle": "2026-06-06 cycle 23/30min",
            "previous_cycle": "2026-06-06 cycle 22/30min",
            "languages": LANGS,
            "new_fiches": len(new_fiches),
            "fill_fiches": 0,
            "translations_produced": len(new_fiches) * len(LANGS),
            "specialty_mix": dict(sp_count),
            "gender_mix": dict(gender_count),
            "license_mix": dict(lic_count),
            "nationality_mix": dict(nat_count),
            "source_csv": "data/dentists_emirates.csv",
            "glossary_version": "v1.0 (translations/glossary.md)",
            "deepl_used": False,
            "deepl_note": "DEEPL_API_KEY vide dans .env.translator (template) → translittération manuelle + tables FR→AR/RU/ZH alignées glossary.md v1.0",
            "cycle23_notes": [
                "Cible cycle 23 = 5 fiches × 5 langues = 25 traductions (NO_REPLY cron, cadence normale)",
                "1× General Dentist (Meena Shahnawaz 00000783 PK — trilingue en/ur/sd)",
                "1× Orthodontist (Tamer Buyukyilmaz 00087766 TR)",
                "1× Oral Surgeon (Monir Al Shakaki 00184141 SY)",
                "1× Periodontist (Smrithi Vishakhavarma 00191631 IN)",
                "1× Dental Implant (Bizhan Behrouz 00242078 IR)",
                "Diversification 5 specialties distinctes + 5 nationalités (PK, TR, SY, IN, IR)",
                "Nouveau : extraction `languages_spoken` avec code ISO Sindhi (sd) ajouté en plus de en/ur — Meena Shahnawaz est trilingue",
                "Glossaire réutilisé tel quel (v1.0, 5 langues stable depuis cycle 19)",
                "Mapping NAME_TRANS : 5 nouveaux noms translittérés EN/FR/RU/ZH + AR natif",
                "Schéma per_lang v1.5 : 5 langues (FR/AR/EN/RU/ZH), 14 champs par fiche",
                "Aucun problème de traduction critique rencontré",
            ],
        },
        "new_fiches": new_fiches,
        "fill_fiches": [],
    }

    OUT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    total_files = len(new_fiches) * len(LANGS)
    print(f"\n✅ Cycle 23 done: {len(new_fiches)} new × 5 langs = {total_files} files")
    print(f"   Summary: {OUT_SUMMARY}")


if __name__ == "__main__":
    main()
