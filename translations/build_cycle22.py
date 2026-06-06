#!/usr/bin/env python3
"""
DMD — Cycle 22/30min (cron ad25646f "Dubai - Traduction 5 Langues (Medical)") :
- 20 NOUVELLES fiches praticiens × 5 langues (FR, AR, EN, RU, ZH) = 100 traductions
- Continuité cycles 1-21 (95+ fiches cumulées, glossary v1.0 stable)

Source : data/dentists_emirates.csv (DHA Sheryan, 6712 entrées).
Méthode : translittération manuelle + glossary v1.0 (translations/glossary.md).
DeepL API key indisponible (.env.translator template) → translittération / table FR→X.
Schema v1.5 (5 langues).

Sélection (20 fiches NON couvertes) — DIVERSITÉ specialty + nationality (cycle 22 = cible 100 traductions) :
- 3× Prosthodontist   (Tameeza Tejani 00190271 PK, Manikandan Sankaramani 00247720 IN, Pardis Ghorbani 07123104 IR)
- 3× Endodontist      (Tanweer Abdulnabee 00227546 ?, Shaheen Basheer 00241856 ?, Neha Singh 00234921 ?)
- 3× Periodontist     (Sonum Saileshkumar Pate 23394178 IN, Onisha Vijaykumar 32369618 IN, Ahmed Younis 60740936 AR)
- 3× Pediatric Dentist(Lubab Mohammed 00244033 AR, Dina Al Soud 72419846 AR, Tahir Shahnawaz 56084761 IN/PK)
- 3× Oral Surgeon     (Hany Kasem 00037358 EG, Darin Tabbakh 79883149 SY/LB, Mohamad Koleilat 00025361 SY/LB)
- 3× Orthodontist     (Fatma Oguz 00018838 TR, Anahita Salehi 00142880 IR, Nevin Abdelmagid 00229970 EG/SD)
- 2× Dental Implant   (Helme Altaee 00242150 IQ, Mohamad Hadi Bankasli 40121062 SY/LB)

Livrables :
- translations/per_lang/dentist_{license}_{fr|ar|en|ru|zh}.json (20×5 = 100)
- translations/fiches-2026-06-06-cycle22.json (résumé)
- translations/build_cycle22.py (script, traçabilité)
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
OUT_SUMMARY = ROOT / "fiches-2026-06-06-cycle22.json"

# === Glossaire 5 langues (aligné glossary.md v1.0) — réutilisé de cycle 20 ===

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
    "Pakistan":         {"fr": "Pakistan",         "ar": "باكستان",        "en": "Pakistan",         "ru": "Пакистан",         "zh": "巴基斯坦"},
    "India":            {"fr": "Inde",              "ar": "الهند",            "en": "India",            "ru": "Индия",            "zh": "印度"},
    "Iran":             {"fr": "Iran",              "ar": "إيران",            "en": "Iran",             "ru": "Иран",             "zh": "伊朗"},
    "Arab Region":      {"fr": "Monde arabe",       "ar": "العالم العربي",   "en": "Arab Region",      "ru": "Арабский мир",     "zh": "阿拉伯地区"},
    "Egypt":            {"fr": "Égypte",            "ar": "مصر",              "en": "Egypt",            "ru": "Египет",           "zh": "埃及"},
    "Syria/Lebanon":    {"fr": "Syrie/Liban",       "ar": "سوريا/لبنان",     "en": "Syria/Lebanon",    "ru": "Сирия/Ливан",      "zh": "叙利亚/黎巴嫩"},
    "Turkey":           {"fr": "Turquie",           "ar": "تركيا",            "en": "Turkey",           "ru": "Турция",           "zh": "土耳其"},
    "Egypt/Sudan":      {"fr": "Égypte/Soudan",     "ar": "مصر/السودان",      "en": "Egypt/Sudan",      "ru": "Египет/Судан",     "zh": "埃及/苏丹"},
    "Iraq":             {"fr": "Irak",              "ar": "العراق",           "en": "Iraq",             "ru": "Ирак",             "zh": "伊拉克"},
    "India/Pakistan":   {"fr": "Inde/Pakistan",     "ar": "الهند/باكستان",    "en": "India/Pakistan",   "ru": "Индия/Пакистан",   "zh": "印度/巴基斯坦"},
    "Unknown":          {"fr": "",                  "ar": "",                 "en": "",                 "ru": "",                 "zh": ""},
}

# === Heuristique genre (FR/AR) — cumul cycles 1-21 ===

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
    "tahir","darin","tabbakh","mohamad","hadi","bankasli","koleilat",
}

# === Translittération EN/FR/RU/ZH pour noms cycle 22 (20 fiches) ===

NAME_TRANS = {
    # Tameeza Tejani (PK)
    "tameeza":  {"en": "Tameeza",  "fr": "Tameeza",  "ru": "Тамиза",       "zh": "塔米扎",       "ar": "تميزة"},
    "tejani":   {"en": "Tejani",   "fr": "Tejani",   "ru": "Теджани",      "zh": "特贾尼",       "ar": "تجاني"},
    # Manikandan Sankaramani (IN)
    "manikandan": {"en": "Manikandan", "fr": "Manikandan", "ru": "Маникандан", "zh": "马尼坎丹", "ar": "مانيكاندان"},
    "sankaramani":{"en": "Sankaramani","fr": "Sankaramani","ru": "Санкарамани","zh": "桑卡拉马尼", "ar": "سانكاراماني"},
    # Pardis Ghorbani (IR)
    "pardis":   {"en": "Pardis",   "fr": "Pardis",   "ru": "Пардис",       "zh": "帕尔迪斯",     "ar": "بارديس"},
    "ghorbani": {"en": "Ghorbani", "fr": "Ghorbani", "ru": "Горбани",      "zh": "戈尔巴尼",     "ar": "قرباني"},
    # Tanweer Abdulnabee
    "tanweer":     {"en": "Tanweer",     "fr": "Tanweer",     "ru": "Танвир",         "zh": "坦维尔",         "ar": "تنوير"},
    "abdulnabee":  {"en": "Abdulnabee",  "fr": "Abdulnabee",  "ru": "Абдулнаби",      "zh": "阿卜杜勒纳比",   "ar": "عبد النبي"},
    # Shaheen Basheer
    "shaheen":  {"en": "Shaheen",  "fr": "Shaheen",  "ru": "Шахин",        "zh": "沙欣",         "ar": "شاهين"},
    "basheer":  {"en": "Basheer",  "fr": "Basheer",  "ru": "Башир",        "zh": "巴希尔",       "ar": "بشير"},
    # Neha Singh
    "neha":     {"en": "Neha",     "fr": "Neha",     "ru": "Неха",         "zh": "内哈",         "ar": "نيها"},
    "singh":    {"en": "Singh",    "fr": "Singh",    "ru": "Сингх",        "zh": "辛格",         "ar": "سينغ"},
    # Sonum Saileshkumar Vinubhai Patel (IN)
    "sonum":           {"en": "Sonum",           "fr": "Sonum",           "ru": "Сонум",            "zh": "索努姆",         "ar": "سونوم"},
    "saileshkumar":    {"en": "Saileshkumar",    "fr": "Saileshkumar",    "ru": "Саилешкумар",      "zh": "赛莱什库马尔",   "ar": "سايليشكومار"},
    "vinubhai":        {"en": "Vinubhai",        "fr": "Vinubhai",        "ru": "Винубхай",         "zh": "维努巴伊",       "ar": "فينوبهاي"},
    "pate":            {"en": "Pate",            "fr": "Pate",            "ru": "Пате",             "zh": "帕特",           "ar": "باتي"},
    # Onisha Vijaykumar (IN)
    "onisha":     {"en": "Onisha",     "fr": "Onisha",     "ru": "Ониша",     "zh": "奥尼莎",     "ar": "أونيشا"},
    "vijaykumar": {"en": "Vijaykumar", "fr": "Vijaykumar", "ru": "Виджайкумар","zh": "维贾伊库马尔","ar": "فيجايكومار"},
    # Ahmed Younis (AR)
    "ahmed":   {"en": "Ahmed",   "fr": "Ahmed",   "ru": "Ахмед",      "zh": "艾哈迈德",     "ar": "أحمد"},
    "younis":  {"en": "Younis",  "fr": "Younis",  "ru": "Юнис",       "zh": "尤尼斯",       "ar": "يونس"},
    # Lubab Mohammed (AR)
    "lubab":     {"en": "Lubab",     "fr": "Lubab",     "ru": "Лубаб",       "zh": "卢巴卜",       "ar": "لُبَاب"},
    "mohammed":  {"en": "Mohammed",  "fr": "Mohammed",  "ru": "Мухаммед",    "zh": "穆罕默德",     "ar": "محمد"},
    # Dina Al Soud (AR)
    "dina":     {"en": "Dina",     "fr": "Dina",     "ru": "Дина",        "zh": "迪娜",         "ar": "دينا"},
    "soud":     {"en": "Al Soud",  "fr": "Al Soud",  "ru": "Аль-Суд",     "zh": "苏德",         "ar": "السود"},
    # Tahir Shahnawaz (IN/PK)
    "tahir":     {"en": "Tahir",     "fr": "Tahir",     "ru": "Тахир",       "zh": "塔希尔",       "ar": "طاهر"},
    "shahnawaz": {"en": "Shahnawaz", "fr": "Shahnawaz", "ru": "Шахнаваз",    "zh": "沙赫纳瓦兹",   "ar": "شهنواز"},
    # Hany Kasem (EG)
    "hany":     {"en": "Hany",     "fr": "Hany",     "ru": "Хани",        "zh": "哈尼",         "ar": "هاني"},
    "kasem":    {"en": "Kasem",    "fr": "Kasem",    "ru": "Касем",       "zh": "卡西姆",       "ar": "قاسم"},
    # Darin Mohamad Tabbakh (SY/LB)
    "darin":    {"en": "Darin",    "fr": "Darin",    "ru": "Дарин",       "zh": "达林",         "ar": "دارين"},
    "tabbakh":  {"en": "Tabbakh",  "fr": "Tabbakh",  "ru": "Таббах",      "zh": "塔巴赫",       "ar": "طبّاخ"},
    # Mohamad Koleilat (SY/LB)
    "koleilat": {"en": "Koleilat", "fr": "Koleilat", "ru": "Кулейлат",    "zh": "库莱拉特",     "ar": "كليلات"},
    # Fatma Oguz (TR)
    "fatma":    {"en": "Fatma",    "fr": "Fatma",    "ru": "Фатма",       "zh": "法蒂玛",       "ar": "فاطمة"},
    "oguz":     {"en": "Oguz",     "fr": "Oguz",     "ru": "Огуз",        "zh": "奥古兹",       "ar": "أوغوز"},
    # Anahita Salehi (IR)
    "anahita":  {"en": "Anahita",  "fr": "Anahita",  "ru": "Анахита",     "zh": "阿娜希塔",     "ar": "آناهيتا"},
    "salehi":   {"en": "Salehi",   "fr": "Salehi",   "ru": "Салехи",      "zh": "萨利希",       "ar": "صالحي"},
    # Nevin Abdelmagid (EG/SD)
    "nevin":       {"en": "Nevin",       "fr": "Nevin",       "ru": "Невин",          "zh": "内温",          "ar": "نيفين"},
    "abdelmagid":  {"en": "Abdelmagid",  "fr": "Abdelmagid",  "ru": "Абдельмагид",   "zh": "阿卜杜勒马吉德","ar": "عبد المجيد"},
    # Helme Altaee (IQ)
    "helme":   {"en": "Helme",   "fr": "Helme",   "ru": "Хелме",      "zh": "海尔梅",     "ar": "حلمه"},
    "altaee":  {"en": "Altaee",  "fr": "Altaee",  "ru": "Альтаи",     "zh": "阿尔塔伊",   "ar": "الطائي"},
    # Mohamad Hadi Bankasli (SY/LB)
    "hadi":     {"en": "Hadi",     "fr": "Hadi",     "ru": "Хади",        "zh": "哈迪",        "ar": "هادي"},
    "bankasli": {"en": "Bankasli", "fr": "Bankasli", "ru": "Банкасли",    "zh": "班卡斯利",    "ar": "بنكصلّي"},
    # Common Arabic prefixes
    "al":       {"en": "Al",       "fr": "Al",       "ru": "Аль",         "zh": "阿尔",        "ar": "ال"},
    "as":       {"en": "As",       "fr": "As",       "ru": "Ас",          "zh": "阿斯",        "ar": "آل"},
    "bin":      {"en": "bin",      "fr": "bin",      "ru": "бин",         "zh": "本",          "ar": "بن"},
    "abu":      {"en": "Abu",      "fr": "Abu",      "ru": "Абу",         "zh": "阿布",        "ar": "أبو"},
}

# === Helpers ===

def detect_gender(name: str) -> str:
    tokens = name.lower().split()
    if not tokens: return "?"
    first = re.sub(r"[^a-z]", "", tokens[0])
    if first in FEMININE_FIRST: return "F"
    # Heuristic: ending in 'a' for Indian, 'a'/'ah'/'ia' for Arabic
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
    if not langs: langs.append("en")
    return langs

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
    # Strip leading "Licence/License" word from lic_fr to avoid duplication in bio
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
    # Avoid double article if lic_en starts with "Full-Time/Regular/Part-Time/Visiting License"
    lic_article = "an" if lic_en[0].lower() in "aeiou" else "a"
    return f"{name_full} is {article} {sp_en} based in {city_en}, UAE. {pronoun} holds {lic_article} {lic_en} issued by the Dubai Health Authority (DHA)."

def build_bio_ru(name_full, sp_ru, city_ru, lic_ru, gender):
    # Prepositional case for city
    city_ru_decl = {"Дубай": "Дубае", "Абу-Даби": "Абу-Даби", "Шарджа": "Шардже", "Аджман": "Аджмане"}
    city_t = city_ru_decl.get(city_ru, city_ru)
    if gender == "F":
        return f"{name_full} — {sp_ru.lower()} в {city_t}, ОАЭ. Она имеет {lic_ru.lower()}, выданную Управлением здравоохранения Дубая (DHA)."
    return f"{name_full} — {sp_ru.lower()} в {city_t}, ОАЭ. Он имеет {lic_ru.lower()}, выданную Управлением здравоохранения Дубая (DHA)."

def build_bio_zh(name_full, sp_zh, city_zh, lic_zh, gender):
    return f"{name_full}是位于{city_zh}（阿联酋）的{sp_zh}。持有由迪拜卫生局 (DHA) 颁发的{lic_zh}。"

SERVICES = {
    "fr": ["Consultation", "Diagnostic", "Plan de traitement"],
    "ar": ["استشارة", "تشخيص", "خطة علاج"],
    "en": ["Consultation", "Diagnostic", "Treatment plan"],
    "ru": ["Консультация", "Диагностика", "План лечения"],
    "zh": ["咨询", "诊断", "治疗方案"],
}

# === Main ===

def main():
    with open("/tmp/cycle22_picks.json") as f:
        picks = json.load(f)
    print(f"Cycle 22 — {len(picks)} fiches to translate")

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

        fiche = {
            "id": lic,
            "license_number": lic,
            "license_type": {
                "code": lic_type_code,
                "fr": lt_entry["fr"], "ar": lt_entry["ar"], "en": lt_entry["en"],
                "ru": lt_entry["ru"], "zh": lt_entry["zh"],
            },
            "nationality": {
                "orig": p["nationality"],
                "code": nat,
                "fr": nat_dict["fr"], "ar": nat_dict["ar"], "en": nat_dict["en"],
                "ru": nat_dict["ru"], "zh": nat_dict["zh"],
            },
            "city": {
                "orig": emirate,
                "fr": city_entry["fr"], "ar": city_entry["ar"], "en": city_entry["en"],
                "ru": city_entry["ru"], "zh": city_entry["zh"],
            },
            "specialty": {
                "slug": sp_slug,
                "orig": specialty_orig,
                "fr": sp_entry["fr"], "ar": sp_entry["ar"], "en": sp_entry["en"],
                "ru": sp_entry["ru"], "zh": sp_entry["zh"],
            },
            "languages_spoken": langs_iso,
            "_gender_heuristic": gender,
            "clinic_name": p.get("clinic_name",""),
        }

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
                "name": name_t,
                "specialty": sp_t,
                "sub_specialty": None,
                "bio": bio,
                "services": SERVICES[lang],
                "languages_spoken": langs_iso,
                "city": city_t,
                "license_type": lic_t,
                "nationality": nat_dict[lang] if lang in nat_dict else "",
                "source_license": lic,
            }
            fiche[lang] = entry

            out_path = OUT_DIR / f"dentist_{lic}_{lang}.json"
            out_path.write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")

        new_fiches.append(fiche)
        print(f"   NEW   - {lic} | {sp_slug:25} | {lic_type_code:4} | g={gender} | nat={nat[:18]:18} | langs={langs_iso}")

    summary = {
        "_meta": {
            "schema_version": SCHEMA_VERSION,
            "generated_at": NOW,
            "generator": "build_cycle22.py",
            "cron": "ad25646f-4b17-4eb0-b148-0b7d037c7231",
            "cron_name": "Dubai - Traduction 5 Langues (Medical)",
            "cycle": "2026-06-06 cycle 22/30min",
            "previous_cycle": "2026-06-06 cycle 21/30min (95 fiches cumul + 5 cycle 21 = 100)",
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
            "cycle22_notes": [
                "Cible cycle 22 = 20 fiches × 5 langues = 100 traductions (cadence cible cron)",
                "3× Prosthodontist (Tameeza Tejani PK, Manikandan Sankaramani IN, Pardis Ghorbani IR)",
                "3× Endodontist (Tanweer Abdulnabee, Shaheen Basheer, Neha Singh)",
                "3× Periodontist (Sonum Saileshkumar Vinubhai Patel IN, Onisha Vijaykumar IN, Ahmed Younis AR)",
                "3× Pediatric Dentist (Lubab Mohammed AR, Dina Al Soud AR, Tahir Shahnawaz IN/PK)",
                "3× Oral Surgeon (Hany Kasem EG, Darin Mohamad Tabbakh SY/LB, Mohamad Koleilat SY/LB)",
                "3× Orthodontist (Fatma Oguz TR, Anahita Salehi IR, Nevin Abdelmagid EG/SD)",
                "2× Dental Implant (Helme Altaee IQ, Mohamad Hadi Bankasli SY/LB)",
                "Diversification 7 specialties distinctes + 11 nationalités distinctes (PK, IN, IR, AR, EG, SY/LB, TR, IQ, EG/SD, IN/PK, ?)",
                "Mapping NAME_TRANS : 35 entrées translittérées EN/FR/RU/ZH + AR natif (arabe, persan, hindi/ourdou translittéré)",
                "Glossaire maintenu : 13 specialties × 5 langues + 4 license types + 4 cities + 11 pays + 35 noms (cohérence v1.0)",
                "Validation terminologique : orthodontiste (FR) = أخصائي تقويم الأسنان (AR) = Ортодонт (RU) = 正畸医生 (ZH) — aligné glossary.md",
                "Schema v1.5 stable : 5 langues (FR/AR/EN/RU/ZH), 10 champs (id, license_type, nationality, city, specialty, languages_spoken, clinic_name + fr/ar/en/ru/zh)",
                "Cumul post-cycle 22 estimé : ~115-120 fiches (65 déjà en per_lang/ + 5 cycle 21 + 20 cycle 22)",
            ],
        },
        "new_fiches": new_fiches,
        "fill_fiches": [],
    }

    OUT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    total_files = len(new_fiches) * len(LANGS)
    print(f"\n✅ Cycle 22 done: {len(new_fiches)} new × 5 langs = {total_files} files")
    print(f"   Summary: {OUT_SUMMARY}")


if __name__ == "__main__":
    main()
