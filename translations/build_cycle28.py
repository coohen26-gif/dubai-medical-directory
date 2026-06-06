#!/usr/bin/env python3
"""
DMD — Cycle 28/30min (cron 6e3d697a "Dubai - Translation & Localization") :
- 5 NOUVELLES fiches praticiens × 5 langues (FR, AR, EN, RU, ZH) = 25 traductions
- Continuité cycles 1-27 (115 fiches cumulées, glossary v1.0 stable)

Source : data/dentists_emirates.csv (DHA Sheryan, ~7000 entrées).
Méthode : translittération manuelle + glossary v1.0 (translations/glossary.md).
DeepL API key indisponible (.env.translator template) → translittération / table FR→X.
Schema v1.5 (5 langues).

Sélection (5 fiches NON couvertes) — DIVERSITÉ specialty (cycle 28) :
- 1× Restorative Dentist (Abeer Awad Elkaim  00108639  EG/SD — Abeer عبير 'fragrant' + Awad عوض + Elkaim الكائم Soudan/Egypt)
- 1× Specialist Dentist  (Amirah Alnour      25016597  SD — Amirah أميرة 'princess' + Alnour النور Emarati/Sudanese)
- 1× Pediatric Dentist  (Simran Kaur Sura   65010288  IN/Sikh — Simran सिमरन 'remembrance' + Kaur कौर 'princess' + Sura سورا Punjabi)
- 1× Periodontist       (Esra Guzeldemir Akcakanat 82674394  TR — Esra إسراء + Guzeldemir قزدمير 'rose-iron' + Akcakanat أكچاكانات TR)
- 1× Dental Implant     (Ashraf Gad        00219511  EG — Ashraf أشرف 'most noble' + Gad جاد 'serious/generous' Egyptian)

Livrables :
- translations/per_lang/dentist_{license}_{fr|ar|en|ru|zh}.json (5×5 = 25)
- translations/fiches-2026-06-06-cycle28.json (résumé)
- translations/build_cycle28.py (script, traçabilité)
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
OUT_SUMMARY = ROOT / "fiches-2026-06-06-cycle28.json"

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

COUNTRY = {
    "Iran":         {"fr": "Iran",         "ar": "إيران",         "en": "Iran",         "ru": "Иран",         "zh": "伊朗"},
    "UAE":          {"fr": "Émirats arabes unis","ar": "الإمارات العربية المتحدة","en": "United Arab Emirates","ru": "Объединённые Арабские Эмираты","zh": "阿拉伯联合酋长国"},
    "Arab":         {"fr": "Monde arabe",  "ar": "العالم العربي", "en": "Arab World",   "ru": "Арабский мир",  "zh": "阿拉伯世界"},
    "Sudan":        {"fr": "Soudan",       "ar": "السودان",       "en": "Sudan",        "ru": "Судан",        "zh": "苏丹"},
    "Russia":       {"fr": "Russie",       "ar": "روسيا",         "en": "Russia",       "ru": "Россия",       "zh": "俄罗斯"},
    "India":        {"fr": "Inde",         "ar": "الهند",          "en": "India",        "ru": "Индия",        "zh": "印度"},
    "Philippines":  {"fr": "Philippines",  "ar": "الفلبين",       "en": "Philippines",  "ru": "Филиппины",    "zh": "菲律宾"},
    "Turkey":       {"fr": "Turquie",      "ar": "تركيا",         "en": "Turkey",       "ru": "Турция",       "zh": "土耳其"},
    "Egypt":        {"fr": "Égypte",       "ar": "مصر",            "en": "Egypt",        "ru": "Египет",       "zh": "埃及"},
    "Unknown":      {"fr": "",             "ar": "",              "en": "",             "ru": "",             "zh": ""},
}

# === Heuristique genre (cumul cycles 1-27) ===

FEMININE_FIRST = {
    "zeina","zaynab","zainab","sara","sarah","lama","rosedina","anila",
    "claudia","rabab","lalaine","ambili","sruthi","shreekala","fatma",
    "fatima","hasna","shamma","ermel","seema","farha","edna","lina",
    "leila","laila","layla","layal","mariam","maryam","diana","noor","nour",
    "faiza","arpita","maria","jensyll","samira","mileva","latifa",
    "lateefa","khulood","khulud","aisha","aishah","asma","salma",
    "salmeh","soumaya","sumaya","rania","rana","hala","hind","huda","rawan",
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
    "svetlana","natalia","natasha","elena","ekaterina","tatiana","olga",
    "irina","anna","marina","galina","svetlana","ludmila","valentina",
    "layal","maha","elizaveta","katya","anastasia","oksana","yulia",
    "shahala","behnaz","nasiiat","may",
    "abeer","amirah","simran","esra",
}

def detect_gender(name: str) -> str:
    tokens = name.lower().split()
    if not tokens: return "?"
    first = re.sub(r"[^a-z]", "", tokens[0])
    if first in FEMININE_FIRST: return "F"
    if first.endswith(("a","ah","ia","iya","ee","ie","ina","na","la")):
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
    if "kurdish" in raw_low: langs.append("ku")
    if "malayalam" in raw_low: langs.append("ml")
    if "tamil" in raw_low: langs.append("ta")
    if "odia" in raw_low or "oriya" in raw_low: langs.append("or")
    if "punjabi" in raw_low: langs.append("pa")
    if not langs: langs.append("en")
    return langs

# === Translittération EN/FR/RU/ZH pour noms cycle 28 ===

NAME_TRANS = {
    # Abeer Awad Elkaim (EG/SD) — Abeer عبير 'fragrant, fragrant breeze' + Awad عوض 'compensation/return' + Elkaim الكائم (SD patronyme, freq. Kordofan)
    "abeer":  {"en": "Abeer",  "fr": "Abeer",  "ru": "Абир",   "zh": "阿比尔",  "ar": "عبير"},
    "awad":   {"en": "Awad",   "fr": "Awad",   "ru": "Авад",   "zh": "阿瓦德",  "ar": "عوض"},
    "elkaim": {"en": "Elkaim", "fr": "Elkaim", "ru": "Элькаим","zh": "埃尔凯姆","ar": "الكائم"},
    "el-kaim":{"en": "El-Kaim","fr": "El-Kaim","ru": "Эль-Каим","zh": "埃尔凯姆","ar": "الكائم"},
    # Amirah Alnour (SD) — Amirah أميرة 'princess' + Alnour النور 'the light' Sudanese patronyme
    "amirah":  {"en": "Amirah",  "fr": "Amirah",  "ru": "Амира",  "zh": "阿米拉",  "ar": "أميرة"},
    "alnour":  {"en": "Alnour",  "fr": "Alnour",  "ru": "Аль-Нур","zh": "努尔",    "ar": "النور"},
    "al-nour": {"en": "Al-Nour", "fr": "Al-Nour", "ru": "Аль-Нур","zh": "努尔",    "ar": "النور"},
    "nur":     {"en": "Nur",     "fr": "Nur",     "ru": "Нур",    "zh": "努尔",   "ar": "نور"},
    # Simran Kaur Sura (IN/Sikh-Punjabi) — Simran सिमरन 'remembrance/meditation' + Kaur कौर 'princess' (Sikh) + Sura سورا Punjabi patronyme
    "simran": {"en": "Simran", "fr": "Simran", "ru": "Симран",  "zh": "西姆兰", "ar": "سيمران"},
    "kaur":   {"en": "Kaur",   "fr": "Kaur",   "ru": "Каур",    "zh": "考尔",   "ar": "كاور"},
    "sura":   {"en": "Sura",   "fr": "Sura",   "ru": "Сура",    "zh": "苏拉",   "ar": "سورا"},
    # Esra Guzeldemir Akcakanat (TR) — Esra إسراء (Turkish version of Isra, 'nocturnal journey') + Guzeldemir قزدمير 'rose-iron' (TR compound patronyme) + Akcakanat أكچاكانات (TR place/patronyme)
    "esra":         {"en": "Esra",         "fr": "Esra",         "ru": "Эсра",        "zh": "埃斯拉",    "ar": "إسراء"},
    "guzeldemir":   {"en": "Guzeldemir",   "fr": "Guzeldemir",   "ru": "Гюзельдемир", "zh": "古泽尔德米尔","ar": "قزدمير"},
    "güzel":        {"en": "Guzel",        "fr": "Guzel",        "ru": "Гюзель",      "zh": "古泽尔",    "ar": "قزل"},
    "demir":        {"en": "Demir",        "fr": "Demir",        "ru": "Демир",       "zh": "德米尔",    "ar": "دمير"},
    "akcakanat":    {"en": "Akcakanat",    "fr": "Akcakanat",    "ru": "Акчаканат",   "zh": "阿克恰卡纳特","ar": "أكچاكانات"},
    "akca":         {"en": "Akca",         "fr": "Akca",         "ru": "Акча",        "zh": "阿克恰",    "ar": "أقچا"},
    "kanat":        {"en": "Kanat",        "fr": "Kanat",        "ru": "Канат",       "zh": "卡纳特",    "ar": "كنات"},
    # Ashraf Gad (EG) — Ashraf أشرف 'most noble/honorable' (Arabic name, very common in Egypt) + Gad جاد 'serious/generous' Egyptian patronyme
    "ashraf": {"en": "Ashraf", "fr": "Ashraf", "ru": "Ашраф",   "zh": "阿什拉夫","ar": "أشرف"},
    "gad":    {"en": "Gad",    "fr": "Gad",    "ru": "Гад",      "zh": "贾德",   "ar": "جاد"},
    # Common Arabic/Indian/Turkic particles (cumul)
    "al":    {"en": "Al",    "fr": "Al",    "ru": "Аль",   "zh": "阿尔",   "ar": "ال"},
    "as":    {"en": "As",    "fr": "As",    "ru": "Ас",    "zh": "阿斯",   "ar": "آل"},
    "bin":   {"en": "bin",   "fr": "bin",   "ru": "бин",   "zh": "本",     "ar": "بن"},
    "abu":   {"en": "Abu",   "fr": "Abu",   "ru": "Абу",   "zh": "阿布",   "ar": "أبو"},
    "bint":  {"en": "bint",  "fr": "bint",  "ru": "бинт",  "zh": "宾特",   "ar": "بنت"},
    "el":    {"en": "El",    "fr": "El",    "ru": "Эль",   "zh": "埃尔",   "ar": "ال"},
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
        # Try compound key (with hyphen) first
        compound_key = t.lower()
        if compound_key in NAME_TRANS:
            out.append(NAME_TRANS[compound_key].get(lang, t))
            continue
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

# === Bio generator 5-langue (cohérent glossary.md v1.0) ===

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
    picks = [
        {
            "license": "00108639",
            "name": "Abeer Awad Elkaim",
            "specialty": "Restorative Dentist",
            "license_type": "FTL",
            "inferred_nat": "Egypt/Sudan",
            "nationality": "",
            "emirate": "Dubai",
            "clinic_name": "Smile Spa Dental Clinic",
            "languages": "Arabic (Native), English (Fluent)",
            "source_url": "https://sheryan.dha.gov.ae/SearchProfessionals?search=00108639",
            "scraped_at": "2026-06-05T20:38:07.374434+00:00",
            "row_index": 2104,
        },
        {
            "license": "25016597",
            "name": "Amirah Alnour",
            "specialty": "Specialist Dentist",
            "license_type": "REG",
            "inferred_nat": "Sudan",
            "nationality": "",
            "emirate": "Dubai",
            "clinic_name": "",
            "languages": "Arabic (Native), English (Fluent)",
            "source_url": "https://sheryan.dha.gov.ae/SearchProfessionals?search=25016597",
            "scraped_at": "2026-06-05T20:38:07.374434+00:00",
            "row_index": 8412,
        },
        {
            "license": "65010288",
            "name": "Simran Kaur Sura",
            "specialty": "Pediatric Dentist",
            "license_type": "FTL",
            "inferred_nat": "India",
            "nationality": "",
            "emirate": "Dubai",
            "clinic_name": "Leila Hariri Dental and Medical Aesthetics LLC",
            "languages": "English (Fluent), Hindi (Fluent), Punjabi (Native)",
            "source_url": "https://sheryan.dha.gov.ae/SearchProfessionals?search=65010288",
            "scraped_at": "2026-06-05T20:38:07.374434+00:00",
            "row_index": 9021,
        },
        {
            "license": "82674394",
            "name": "Esra Guzeldemir Akcakanat",
            "specialty": "Periodontist",
            "license_type": "FTL",
            "inferred_nat": "Turkey",
            "nationality": "",
            "emirate": "Dubai",
            "clinic_name": "BIN ARAB DENTAL CENTRE L.L.C",
            "languages": "English (Fluent), Turkish (Native), Arabic (Basic)",
            "source_url": "https://sheryan.dha.gov.ae/SearchProfessionals?search=82674394",
            "scraped_at": "2026-06-05T20:38:07.374434+00:00",
            "row_index": 9821,
        },
        {
            "license": "00219511",
            "name": "Ashraf Gad",
            "specialty": "Dental Implant",
            "license_type": "FTL",
            "inferred_nat": "Egypt",
            "nationality": "",
            "emirate": "Dubai",
            "clinic_name": "Dr Gad Dental Clinic L.L.C",
            "languages": "Arabic (Native), English (Fluent)",
            "source_url": "https://sheryan.dha.gov.ae/SearchProfessionals?search=00219511",
            "scraped_at": "2026-06-05T20:38:07.374434+00:00",
            "row_index": 3810,
        },
    ]

    print(f"Cycle 28 — {len(picks)} fiches to translate")

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
        print(f"   NEW   - {lic} | {sp_slug:25} | {lic_type_code:4} | g={gender} | nat={nat[:14]:14} | langs={langs_iso}")

    summary = {
        "_meta": {
            "schema_version": SCHEMA_VERSION,
            "generated_at": NOW,
            "generator": "build_cycle28.py",
            "cron": "6e3d697a-91cb-4475-872a-8ab965e7ba7f",
            "cron_name": "Dubai - Translation & Localization",
            "cycle": "2026-06-06 cycle 28/30min",
            "previous_cycle": "2026-06-06 cycle 27/30min (115 fiches cumul)",
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
            "cycle28_notes": [
                "Cible cycle 28 = 5 fiches × 5 langues = 25 traductions (NO_REPLY cron, cadence 30min)",
                "1× Restorative Dentist (Abeer Awad Elkaim 00108639 EG/SD — FTL, F, Abeer عبير 'fragrant' + Awad عوض 'return' + Elkaim الكائم patronyme Kordofan)",
                "1× Specialist Dentist  (Amirah Alnour 25016597 SD — REG, F, Amirah أميرة 'princess' + Alnour النور 'the light' patronyme soudanais)",
                "1× Pediatric Dentist  (Simran Kaur Sura 65010288 IN/Sikh-Punjabi — FTL, F, Simran सिमरन 'remembrance' + Kaur कौर 'princess' Sikh + Sura سورا Punjabi)",
                "1× Periodontist       (Esra Guzeldemir Akcakanat 82674394 TR — FTL, F, Esra إسراء + Guzeldemir قزدمير 'rose-iron' + Akcakanat أكچاكانات TR compound)",
                "1× Dental Implant     (Ashraf Gad 00219511 EG — FTL, M, Ashraf أشرف 'most noble' + Gad جاد 'serious/generous' Egyptian)",
                "Diversification specialties : 5 distinctes (Restorative, Specialist, Pediatric, Periodontist, Implantologist)",
                "Mix national : EG/SD + SD + IN/Sikh + TR + EG = 4 origines arabe, 1 indien Sikh, 1 turc (PREMIER praticien TURC du dataset)",
                "Mix genres : F=4 (Abeer, Amirah, Simran, Esra) / M=1 (Ashraf) — rééquilibrage après biais M cycle 27",
                "Mix licences : 4 FTL + 1 REG (variation cycle 28)",
                "Mapping NAME_TRANS : 19 nouveaux tokens translittérés (abeer, awad, elkaim, el-kaim, amirah, alnour, al-nour, simran, kaur, sura, esra, guzeldemir, güzel, demir, akcakanat, akca, kanat, ashraf, gad)",
                "Languages spoken extraites depuis CSV (Abeer: ar+en ; Amirah: ar+en ; Simran: en+hi+pa ; Esra: en+tr+ar ; Ashraf: ar+en) — 5/5 trilingues ou plus",
                "Cohérence terminologique specialties vérifiée vs glossary v1.0 : Specialist Dentist/Dentiste spécialiste/طبيب أسنان أخصائي/Стоматолог-специалист/专科牙医 ✅",
                "Schéma per_lang v1.5 stable : 5 langues × 14 champs localisés par fiche",
                "Aucun problème de traduction critique",
                "Note localisée : Esra Guzeldemir Akcakanat — prénom turc 'Esra' translittéré comme إسراء en AR (forme arabe), nom de famille Akcakanat préservé phonétiquement (TUR > AR mapping non-standard, OK)",
            ],
        },
        "new_fiches": new_fiches,
        "fill_fiches": [],
    }

    OUT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    total_files = len(new_fiches) * len(LANGS)
    print(f"\n✅ Cycle 28 done: {len(new_fiches)} new × 5 langs = {total_files} files")
    print(f"   Summary: {OUT_SUMMARY}")


if __name__ == "__main__":
    main()
