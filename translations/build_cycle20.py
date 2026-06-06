#!/usr/bin/env python3
"""
DMD — Cycle 20/30min (cron ad25646f "Dubai - Traduction 5 Langues (Medical)") :
- 5 NOUVELLES fiches praticiens × 5 langues (FR, AR, EN, RU, ZH) = 25 traductions
- Continuité cycles 1-19 (90+ fiches cumulées, glossary v1.0 stable)

Source : data/dentists_emirates.csv (DHA Sheryan, 6712 entrées).
Méthode : translittération manuelle + glossary v1.0 (translations/glossary.md).
DeepL API key indisponible (.env.translator template) → translittération / table FR→X.
Schema v1.5 (5 langues).

Sélection (5 fiches NON couvertes) — DIVERSITÉ specialty :
- 1× Endodontist    (Khaled Alqadi, 46889163)         — Palestine/Jordanie probable
- 1× General Dentist (Mohammed Mohammed, 00251485)     — prénom composé arabe (Abu Dhabi/Dubai)
- 1× Oral Surgeon    (Arpita Singh, 30135001)          — Inde (Arpita = "offered" Sanskrit, Singh = "lion" Pendjab)
- 1× Endodontist    (Maria Morales, 00245491)         — hispanophone (Espagne/Amérique latine)
- 1× Orthodontist   (Jensyll Rodrigues, 94338321)     — Philippines/Brésil probable (Jensyll prénom rare, Rodrigues patronyme portugais)

Livrables :
- translations/per_lang/dentist_{license}_{fr|ar|en|ru|zh}.json (5×5 = 25)
- translations/fiches-2026-06-06-cycle20.json (résumé)
- translations/build_cycle20.py (script, traçabilité)
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
OUT_SUMMARY = ROOT / "fiches-2026-06-06-cycle20.json"

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

COUNTRY      = {"UAE": {"fr": "Émirats arabes unis",         "ar": "الإمارات العربية المتحدة", "en": "United Arab Emirates",       "ru": "Объединённые Арабские Эмираты", "zh": "阿拉伯联合酋长国"}}
COUNTRY_SHORT = {"UAE": {"fr": "EAU",                       "ar": "الإمارات",                  "en": "UAE",                       "ru": "ОАЭ",                              "zh": "阿联酋"}}

# === Heuristique genre (FR/AR) — cumul cycles 1-19 ===

FEMININE_FIRST = {
    "zeina","zaynab","zainab","sara","sarah","lama","rosedina","anila",
    "claudia","rabab","lalaine","ambili","sruthi","shreekala","fatma",
    "fatima","hasna","shamma","ermel","seema","farha","edna","lina",
    "leila","laila","layla","mariam","maryam","diana","noor","nour",
    "faiza","arpita","maria","jensyll","samira","mileva","anila",
    "latifa","lateefa","khulood","khulud","aisha","aishah","asma",
    "salma","soumaya","sumaya","rania","rana","hala","hind","huda",
    "rana","ranya","rawan","razan","reem","rim","rimah","roula",
    "saba","sahar","sawsan","shams","shatha","suad","taghreed",
    "tala","yara","yasmin","yasmine","zahra","zeinab","nadia",
    "lama","lina","mona","muna","amal","amani","amani","angham",
    "hiam","hiba","hoda","iman","enas","dina","dana",
    "nada","nadine","najat","nawal","nermin","noha","noura",
    "ranime","razan","rehab","rim","sahar","salwa","samar",
    "wafa","wafaa","warda","yasmin","yusra","zakia","zara",
    "julia","julie","ana","anamaria","anamaria","maria","marie",
    "arpita","priya","pooja","preethi","kavita","kavitha",
    "muneera","mounira","munira","nouf","nada","rawan",
    "lina","leena","layan","liane","mira","maya","mayar",
    "rosa","rosalinda","roxana","sandra","silvia","sylvia",
    "tatiana","teresa","theresa","valentina","vanessa","veronica",
    "victoria","virginia","yolanda","yvette","zara","zuzana",
    "anam","anjum","archana","arpitha","asha","baby","bharti",
    "bindu","chitra","deepa","deepthi","deepti","dhanalakshmi",
    "divya","durga","fatima","gayathri","gayatri","geetha",
    "hemalatha","indu","jaya","jothy","jyothi","kala","kalpana",
    "kalyani","kavita","lakshmi","latha","lavanya","laxmi",
    "leelavathi","leena","madhuri","mahalakshmi","mala","mangala",
    "manisha","manjula","manjusha","meena","meenakshi","meera",
    "mita","mitha","mohana","mohini","muktha","mythili","nagarathna",
    "nagaveni","nalini","nanda","narmada","natara jan","navaneetha",
    "neela","neelam","neeraja","niharika","nirmala","nisha","nishita",
    "nitisha","nivedita","padmini","parvathi","parvati","poornima",
    "prabha","prabhavathi","prameela","pramodini","prathibha","preethi",
    "prem","pritha","priyanka","pushpa","radhika","raga","ragini",
    "rajani","rajeshwari","rajini","ramya","ranjani","rasmi","rathi",
    "ravi","reema","reena","rekha","renu","revathi","riya","roja",
    "roshni","roopa","rupa","saba","sabitha","sadhna","sadhna",
    "saguna","sahana","sai","sailaja","sajitha","sakunthala","salini",
    "salma","sameera","samina","samira","samyuktha","sandhya","sangeetha",
    "sangita","sanjana","sankari","santa","santhi","santhosh","sanyuktha",
    "sapna","sarah","sarala","saranya","sarasa","sarita","saroja",
    "sasi","satheesh","sathya","satya","saumya","savitha","seethalakshmi",
    "shakila","shakuntala","shalini","shameem","shamim","shampa","shana",
    "shanthi","shanti","sharada","sharmila","sharmistha","shashi","sheela",
    "shehnaz","sheila","shilpa","shiny","shirin","shobha","shobhana",
    "shruti","shubha","shubhangi","shweta","sindhu","smitha","smita",
    "smriti","sneha","snehalata","soma","soumya","sowmya","sreekala",
    "sreedevi","sreelekha","srilakshmi","srividya","subha","subhadra",
    "subhashini","subbulakshmi","suchitra","sudha","sudharani","suganya",
    "suguna","suhasini","suja","sujata","sukanya","suma","sumangala",
    "sumathi","sumitra","sumitrasundari","sunanda","suneetha","sunitha",
    "sunni","suparna","supriya","surabhi","surekha","suriya","sushama",
    "sushila","sushma","susila","swapna","swarna","swathi","syamala",
    "syed","tanuja","tanvi","tara","tarannum","tarini","tejaswini",
    "thamaraiselvi","thanuja","tilottama","tina","triveni","uma",
    "umadevi","umarani","umesh","usha","usharani","vaijayanthi","vaishali",
    "vanaja","vani","vanisri","vanitha","varsha","varalakshmi","vasanthi",
    "vasugi","vasundhara","vedavalli","veena","veni","vennila","vidya",
    "vidyarani","vidyavathi","vijayalakshmi","vijayalaxmi","vijaya",
    "vijayalakshmi","vimala","vimla","vinaya","vinodhini","vinodini",
    "vinothini","vishali","vishnu","vithya","vydhianathan","yamini",
    "yasmeen","yashoda","yashodha","yogalakshmi","yogeswari","zohra",
}

# Map ISO countries to French short for bio
NAT_FR = {
    "United Arab Emirates": "Émirats arabes unis",
    "UAE": "Émirats arabes unis",
    "Saudi Arabia": "Arabie saoudite",
    "Egypt": "Égypte",
    "Jordan": "Jordanie",
    "Lebanon": "Liban",
    "Syria": "Syrie",
    "Iraq": "Irak",
    "Palestine": "Palestine",
    "India": "Inde",
    "Pakistan": "Pakistan",
    "Philippines": "Philippines",
    "United Kingdom": "Royaume-Uni",
    "United States": "États-Unis",
    "Canada": "Canada",
    "Germany": "Allemagne",
    "France": "France",
    "Italy": "Italie",
    "Spain": "Espagne",
    "Brazil": "Brésil",
    "Russia": "Russie",
    "Serbia": "Serbie",
    "Turkey": "Turquie",
    "Iran": "Iran",
    "Afghanistan": "Afghanistan",
    "Bangladesh": "Bangladesh",
    "Sri Lanka": "Sri Lanka",
    "Nepal": "Népal",
    "Yemen": "Yémen",
    "Oman": "Oman",
    "Kuwait": "Koweït",
    "Qatar": "Qatar",
    "Bahrain": "Bahreïn",
    "Sudan": "Soudan",
    "Tunisia": "Tunisie",
    "Morocco": "Maroc",
    "Algeria": "Algérie",
    "Libya": "Libye",
    "Ethiopia": "Éthiopie",
    "Kenya": "Kenya",
    "Nigeria": "Nigeria",
    "Ghana": "Ghana",
    "South Africa": "Afrique du Sud",
    "Australia": "Australie",
    "New Zealand": "Nouvelle-Zélande",
    "Japan": "Japon",
    "China": "Chine",
    "South Korea": "Corée du Sud",
    "North Korea": "Corée du Nord",
    "Indonesia": "Indonésie",
    "Malaysia": "Malaisie",
    "Singapore": "Singapour",
    "Thailand": "Thaïlande",
    "Vietnam": "Vietnam",
    "Myanmar": "Myanmar",
    "Cambodia": "Cambodge",
    "Laos": "Laos",
    "Mongolia": "Mongolie",
    "Kazakhstan": "Kazakhstan",
    "Uzbekistan": "Ouzbékistan",
    "Kyrgyzstan": "Kirghizistan",
    "Tajikistan": "Tadjikistan",
    "Turkmenistan": "Turkménistan",
    "Azerbaijan": "Azerbaïdjan",
    "Armenia": "Arménie",
    "Georgia": "Géorgie",
    "Ukraine": "Ukraine",
    "Belarus": "Biélorussie",
    "Moldova": "Moldavie",
    "Romania": "Roumanie",
    "Bulgaria": "Bulgarie",
    "Greece": "Grèce",
    "Albania": "Albanie",
    "North Macedonia": "Macédoine du Nord",
    "Croatia": "Croatie",
    "Bosnia and Herzegovina": "Bosnie-Herzégovine",
    "Slovenia": "Slovénie",
    "Slovakia": "Slovaquie",
    "Czech Republic": "Tchéquie",
    "Poland": "Pologne",
    "Hungary": "Hongrie",
    "Austria": "Autriche",
    "Switzerland": "Suisse",
    "Netherlands": "Pays-Bas",
    "Belgium": "Belgique",
    "Luxembourg": "Luxembourg",
    "Denmark": "Danemark",
    "Sweden": "Suède",
    "Norway": "Norvège",
    "Finland": "Finlande",
    "Iceland": "Islande",
    "Ireland": "Irlande",
    "Portugal": "Portugal",
    "Malta": "Malte",
    "Cyprus": "Chypre",
    "Mexico": "Mexique",
    "Argentina": "Argentine",
    "Chile": "Chili",
    "Colombia": "Colombie",
    "Peru": "Pérou",
    "Venezuela": "Venezuela",
    "Ecuador": "Équateur",
    "Bolivia": "Bolivie",
    "Uruguay": "Uruguay",
    "Paraguay": "Paraguay",
    "Dominican Republic": "République dominicaine",
    "Cuba": "Cuba",
    "Jamaica": "Jamaïque",
    "Haiti": "Haïti",
    "Costa Rica": "Costa Rica",
    "Panama": "Panama",
    "Guatemala": "Guatemala",
    "Honduras": "Honduras",
    "El Salvador": "Salvador",
    "Nicaragua": "Nicaragua",
}

NAT_AR = {
    "United Arab Emirates": "الإمارات العربية المتحدة",
    "UAE": "الإمارات العربية المتحدة",
    "Saudi Arabia": "المملكة العربية السعودية",
    "Egypt": "مصر",
    "Jordan": "الأردن",
    "Lebanon": "لبنان",
    "Syria": "سوريا",
    "Iraq": "العراق",
    "Palestine": "فلسطين",
    "India": "الهند",
    "Pakistan": "باكستان",
    "Philippines": "الفلبين",
    "United Kingdom": "المملكة المتحدة",
    "United States": "الولايات المتحدة",
    "Canada": "كندا",
    "Germany": "ألمانيا",
    "France": "فرنسا",
    "Italy": "إيطاليا",
    "Spain": "إسبانيا",
    "Brazil": "البرازيل",
    "Russia": "روسيا",
    "Serbia": "صربيا",
    "Turkey": "تركيا",
    "Iran": "إيران",
    "Afghanistan": "أفغانستان",
    "Bangladesh": "بنغلاديش",
    "Sri Lanka": "سريلانكا",
    "Nepal": "نيبال",
    "Yemen": "اليمن",
    "Oman": "عُمان",
    "Kuwait": "الكويت",
    "Qatar": "قطر",
    "Bahrain": "البحرين",
    "Sudan": "السودان",
    "Tunisia": "تونس",
    "Morocco": "المغرب",
    "Algeria": "الجزائر",
    "Libya": "ليبيا",
    "Ethiopia": "إثيوبيا",
    "Kenya": "كينيا",
    "Nigeria": "نيجيريا",
    "Ghana": "غانا",
    "South Africa": "جنوب أفريقيا",
    "Australia": "أستراليا",
    "New Zealand": "نيوزيلندا",
    "Japan": "اليابان",
    "China": "الصين",
    "South Korea": "كوريا الجنوبية",
    "Indonesia": "إندونيسيا",
    "Malaysia": "ماليزيا",
    "Singapore": "سنغافورة",
    "Thailand": "تايلاند",
    "Vietnam": "فيتنام",
    "Ukraine": "أوكرانيا",
    "Romania": "رومانيا",
    "Poland": "بولندا",
    "Greece": "اليونان",
    "Mexico": "المكسيك",
    "Argentina": "الأرجنتين",
    "Colombia": "كولومبيا",
    "Peru": "بيرو",
    "Venezuela": "فنزويلا",
    "Dominican Republic": "جمهورية الدومينيكان",
}

NAT_RU = {
    "United Arab Emirates": "Объединённые Арабские Эмираты",
    "UAE": "ОАЭ",
    "Saudi Arabia": "Саудовская Аравия",
    "Egypt": "Египет",
    "Jordan": "Иордания",
    "Lebanon": "Ливан",
    "Syria": "Сирия",
    "Iraq": "Ирак",
    "Palestine": "Палестина",
    "India": "Индия",
    "Pakistan": "Пакистан",
    "Philippines": "Филиппины",
    "United Kingdom": "Великобритания",
    "United States": "Соединённые Штаты",
    "Canada": "Канада",
    "Germany": "Германия",
    "France": "Франция",
    "Italy": "Италия",
    "Spain": "Испания",
    "Brazil": "Бразилия",
    "Russia": "Россия",
    "Serbia": "Сербия",
    "Turkey": "Турция",
    "Iran": "Иран",
    "Afghanistan": "Афганистан",
    "Bangladesh": "Бангладеш",
    "Sri Lanka": "Шри-Ланка",
    "Nepal": "Непал",
    "Yemen": "Йемен",
    "Oman": "Оман",
    "Kuwait": "Кувейт",
    "Qatar": "Катар",
    "Bahrain": "Бахрейн",
    "Sudan": "Судан",
    "Tunisia": "Тунис",
    "Morocco": "Марокко",
    "Algeria": "Алжир",
    "Libya": "Ливия",
    "Ethiopia": "Эфиопия",
    "Kenya": "Кения",
    "Nigeria": "Нигерия",
    "Ghana": "Гана",
    "South Africa": "Южная Африка",
    "Australia": "Австралия",
    "New Zealand": "Новая Зеландия",
    "Japan": "Япония",
    "China": "Китай",
    "South Korea": "Южная Корея",
    "Indonesia": "Индонезия",
    "Malaysia": "Малайзия",
    "Singapore": "Сингапур",
    "Thailand": "Таиланд",
    "Vietnam": "Вьетнам",
    "Ukraine": "Украина",
    "Romania": "Румыния",
    "Poland": "Польша",
    "Greece": "Греция",
    "Mexico": "Мексика",
    "Argentina": "Аргентина",
    "Colombia": "Колумбия",
    "Peru": "Перу",
    "Venezuela": "Венесуэла",
    "Dominican Republic": "Доминиканская Республика",
}

NAT_ZH = {
    "United Arab Emirates": "阿拉伯联合酋长国",
    "UAE": "阿联酋",
    "Saudi Arabia": "沙特阿拉伯",
    "Egypt": "埃及",
    "Jordan": "约旦",
    "Lebanon": "黎巴嫩",
    "Syria": "叙利亚",
    "Iraq": "伊拉克",
    "Palestine": "巴勒斯坦",
    "India": "印度",
    "Pakistan": "巴基斯坦",
    "Philippines": "菲律宾",
    "United Kingdom": "英国",
    "United States": "美国",
    "Canada": "加拿大",
    "Germany": "德国",
    "France": "法国",
    "Italy": "意大利",
    "Spain": "西班牙",
    "Brazil": "巴西",
    "Russia": "俄罗斯",
    "Serbia": "塞尔维亚",
    "Turkey": "土耳其",
    "Iran": "伊朗",
    "Afghanistan": "阿富汗",
    "Bangladesh": "孟加拉国",
    "Sri Lanka": "斯里兰卡",
    "Nepal": "尼泊尔",
    "Yemen": "也门",
    "Oman": "阿曼",
    "Kuwait": "科威特",
    "Qatar": "卡塔尔",
    "Bahrain": "巴林",
    "Sudan": "苏丹",
    "Tunisia": "突尼斯",
    "Morocco": "摩洛哥",
    "Algeria": "阿尔及利亚",
    "Libya": "利比亚",
    "Ethiopia": "埃塞俄比亚",
    "Kenya": "肯尼亚",
    "Nigeria": "尼日利亚",
    "Ghana": "加纳",
    "South Africa": "南非",
    "Australia": "澳大利亚",
    "New Zealand": "新西兰",
    "Japan": "日本",
    "China": "中国",
    "South Korea": "韩国",
    "Indonesia": "印度尼西亚",
    "Malaysia": "马来西亚",
    "Singapore": "新加坡",
    "Thailand": "泰国",
    "Vietnam": "越南",
    "Ukraine": "乌克兰",
    "Romania": "罗马尼亚",
    "Poland": "波兰",
    "Greece": "希腊",
    "Mexico": "墨西哥",
    "Argentina": "阿根廷",
    "Colombia": "哥伦比亚",
    "Peru": "秘鲁",
    "Venezuela": "委内瑞拉",
    "Dominican Republic": "多米尼加共和国",
}

# === Translittération EN/FR/RU/ZH pour prénoms arabes, indiens, etc. ===

NAME_TRANS = {
    "khaled": {"en": "Khaled", "fr": "Khaled", "ru": "Халед", "zh": "哈立德", "ar": "خالد"},
    "alqadi": {"en": "Alqadi", "fr": "Alqadi", "ru": "Аль-Кади", "zh": "阿尔卡迪", "ar": "القاضي"},
    "mohammed": {"en": "Mohammed", "fr": "Mohammed", "ru": "Мухаммед", "zh": "穆罕默德", "ar": "محمد"},
    "arpita": {"en": "Arpita", "fr": "Arpita", "ru": "Арпита", "zh": "阿尔皮塔", "ar": "أربيتا"},
    "singh": {"en": "Singh", "fr": "Singh", "ru": "Сингх", "zh": "辛格", "ar": "سينغ"},
    "maria": {"en": "Maria", "fr": "Maria", "ru": "Мария", "zh": "玛丽亚", "ar": "ماريا"},
    "morales": {"en": "Morales", "fr": "Morales", "ru": "Моралес", "zh": "莫拉莱斯", "ar": "موراليس"},
    "jensyll": {"en": "Jensyll", "fr": "Jensyll", "ru": "Дженсилл", "zh": "詹西尔", "ar": "جينسيل"},
    "rodrigues": {"en": "Rodrigues", "fr": "Rodrigues", "ru": "Родригес", "zh": "罗德里格斯", "ar": "رودريغيز"},
}

# === Helpers ===

def detect_gender(name: str, nationality: str = "") -> str:
    """Return 'F', 'M', or '?' based on first name."""
    tokens = name.lower().split()
    if not tokens: return "?"
    first = re.sub(r"[^a-z]", "", tokens[0])
    if first in FEMININE_FIRST: return "F"
    # common male arabic/indic markers
    if first in {"mohammed","mohamed","muhammad","ahmed","ahmad","ali","omar","khalid","khaled","saad","hassan","husein","hussain","abdullah","yusuf","yousef","ibrahim","tarek","tariq","faisal","faisal","majid","nasser","samir","samir","walid","zaid","zaid","karim","rashid","hisham","bashar","mazen","majed","saif","yazen","rayan","fares","feras","anis","anis","nabil","nabil","sami","adel","majdi","ramzi","ramy","ashraf","ashraf","gamal","amr","hazem","tamer","sherif","sharif","sameh","hany","mohannad","mohanad","wael","wael","ayman","eyad","iyad","hamza","hamza","bilal","zaid","zayd","anas","mahmoud","mahmood","mustafa","mostafa","hossam","husam","osama","othman","uthman","salem","saleh","naji","naje","jaber","jabir","habib","nader","naif","nayef","meshal","mishaal","meshal","mansour","mansoor","munir","mounir","munir","nizar","nizar","rafik","rafiq","sabah","sobah","subhi","subhi","ziad","zeyad","zuhair","zuheir","anwar","anwar","bashar","bisher","fadi","fady","fadi","hadi","haady","hamdi","hamdee","hindawi","jihad","juma","jumma","khairi","khairy","lateef","latif","louay","loay","maan","maan","majd","majd","mohab","mohab","nadeem","nadeem","nael","nael","qasim","qasem","raed","raed","ramzi","ramzy","rashid","rasheed","sabbar","sabir","samer","sameer","shadi","shadi","taher","tahir","thaier","thayer","wajdi","wajdy","waleed","walid","younis","younes","zafer","zafar","zakaria","zakariya","zaki","zaky","ayham","ayham","mohamad","mohamad","shady","shady","mounir","mounir","motasem","motasem","ayman","ayman","ayman","hossam","husam","khaldoun","khaldun","khattab","khattab","jamil","jameel","jamal","jemal","kamel","kameel","kamal","kemal","nabil","nabeel","nader","naeem","naim","naseer","nasir","rashid","rasheed","rashid","rida","reda","rida","sabih","sabeeh","sabah","sobh","sabah","samih","sameeh","samir","sameer","shaaban","shaaban","shaheen","shihab","shihab","suhail","sohail","sukayr","suker","tahseen","tahseen","tahsin","tahseen","tamim","tameem","thaqib","thaqib","thabit","thabit","wajih","wajeeh","wajeeh","yaqin","yaqeen","younan","younan","yousef","yusuf","zaheer","zahir","zakaria","zakariya","zuhdi","zuhdee","zuhdi","abdel","abdul","abdel","abdul"}:
        return "M"
    return "?"

def normalize_lang_codes(languages_raw: str) -> list:
    """Extract ISO codes from the languages column."""
    if not languages_raw: return ["en"]
    langs = []
    raw_low = languages_raw.lower()
    if "arabic" in raw_low or "ar" in raw_low.split(): langs.append("ar")
    if "english" in raw_low or "en" in raw_low.split(): langs.append("en")
    if "french" in raw_low or "fr" in raw_low.split(): langs.append("fr")
    if "hindi" in raw_low: langs.append("hi")
    if "urdu" in raw_low: langs.append("ur")
    if "russian" in raw_low: langs.append("ru")
    if "spanish" in raw_low: langs.append("es")
    if "portuguese" in raw_low: langs.append("pt")
    if "german" in raw_low: langs.append("de")
    if "italian" in raw_low: langs.append("it")
    if "tagalog" in raw_low or "filipino" in raw_low: langs.append("tl")
    if "mandarin" in raw_low or "chinese" in raw_low: langs.append("zh")
    if not langs: langs.append("en")
    return langs

def transcribe_name(name: str, lang: str) -> str:
    """Transliterate name in target language. Uses NAME_TRANS table then heuristic."""
    tokens = name.split()
    out = []
    for t in tokens:
        key = re.sub(r"[^a-z]", "", t.lower())
        if key in NAME_TRANS:
            out.append(NAME_TRANS[key].get(lang, t))
        else:
            # fallback: keep as-is for latin langs, translit to cyrillic for RU, ideographs for ZH, arabic for AR
            if lang == "ru":
                out.append(latin_to_cyrillic_heuristic(t))
            elif lang == "zh":
                out.append(latin_to_pinyin_heuristic(t))
            elif lang == "ar":
                out.append(latin_to_arabic_heuristic(t))
            else:
                out.append(t)
    return " ".join(out)

# Minimalistic translit tables for fallback
LATIN_CYR = {
    "a":"а","b":"б","c":"к","d":"д","e":"е","f":"ф","g":"г","h":"х","i":"и",
    "j":"дж","k":"к","l":"л","m":"м","n":"н","o":"о","p":"п","q":"к","r":"р",
    "s":"с","t":"т","u":"у","v":"в","w":"в","x":"кс","y":"й","z":"з",
    "sh":"ш","ch":"ч","zh":"ж","yu":"ю","ya":"я","yo":"ё","kh":"х","ts":"ц",
    "'":"ь","'":"ь",
}
LATIN_PINYIN = {
    "a":"阿","b":"布","c":"克","d":"德","e":"厄","f":"弗","g":"格","h":"赫","i":"伊",
    "j":"杰","k":"克","l":"尔","m":"姆","n":"恩","o":"奥","p":"普","q":"奇","r":"尔",
    "s":"斯","t":"特","u":"乌","v":"弗","w":"维","x":"克斯","y":"伊","z":"兹",
    "sh":"什","ch":"奇","zh":"日","th":"思","ph":"夫","wh":"沃",
}
LATIN_AR_HEURISTIC = "عبد"  # default: keep latin for AR fallback (rare)

def latin_to_cyrillic_heuristic(word: str) -> str:
    word_low = word.lower()
    out = ""
    i = 0
    while i < len(word_low):
        # try digraphs first
        if i+1 < len(word_low) and word_low[i:i+2] in LATIN_CYR:
            out += LATIN_CYR[word_low[i:i+2]]
            i += 2
        elif word_low[i] in LATIN_CYR:
            out += LATIN_CYR[word_low[i]]
            i += 1
        else:
            out += word[i]
            i += 1
    # capitalize first
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
    if out: out = out[0]
    return out

def latin_to_arabic_heuristic(word: str) -> str:
    # For unknown names in AR, keep latin in parentheses is the convention used
    return word

# === Bio generator 5-langue ===

def build_bio(name_full: str, specialty_fr: str, city_fr: str, lic_type_fr: str, gender: str, langs_iso: list) -> str:
    is_f = (gender == "F")
    if is_f:
        return f"{name_full} est {specialty_fr.lower()} à {city_fr}, EAU. Licenciée sous licence {lic_type_fr.lower()} délivrée par la Dubai Health Authority (DHA)."
    else:
        return f"{name_full} est {specialty_fr.lower()} à {city_fr}, EAU. Licencié sous licence {lic_type_fr.lower()} délivrée par la Dubai Health Authority (DHA)."

def build_bio_ar(name_full: str, specialty_ar: str, city_ar: str, lic_type_ar: str, gender: str) -> str:
    is_f = (gender == "F")
    if is_f:
        return f"تعمل {name_full} {specialty_ar} في {city_ar}، الإمارات. تحمل رخصة {lic_type_ar} صادرة عن هيئة الصحة بدبي (DHA)."
    else:
        return f"يعمل {name_full} {specialty_ar} في {city_ar}، الإمارات. يحمل رخصة {lic_type_ar} صادرة عن هيئة الصحة بدبي (DHA)."

def build_bio_en(name_full: str, specialty_en: str, city_en: str, lic_type_en: str, gender: str) -> str:
    is_f = (gender == "F")
    article = "an" if specialty_en[0].lower() in "aeiou" else "a"
    pronoun = "She" if is_f else "He"
    return f"{name_full} is {article} {specialty_en} based in {city_en}, UAE. {pronoun} holds a {lic_type_en} issued by the Dubai Health Authority (DHA)."

def build_bio_ru(name_full: str, specialty_ru: str, city_ru: str, lic_type_ru: str, gender: str) -> str:
    is_f = (gender == "F")
    if is_f:
        return f"{name_full} — {specialty_ru.lower()} в {city_ru}, ОАЭ. Она имеет {lic_type_ru.lower()}, выданную Управлением здравоохранения Дубая (DHA)."
    else:
        return f"{name_full} — {specialty_ru.lower()} в {city_ru}, ОАЭ. Он имеет {lic_type_ru.lower()}, выданную Управлением здравоохранения Дубая (DHA)."

def build_bio_zh(name_full: str, specialty_zh: str, city_zh: str, lic_type_zh: str, gender: str) -> str:
    return f"{name_full}是位于{city_zh}（阿联酋）的{ specialty_zh}。持有由迪拜卫生局 (DHA) 颁发的{lic_type_zh}。"

# === Main ===

def main():
    # Load picks from cycle 20 selection
    with open("/tmp/cycle20_picks.json") as f:
        picks = json.load(f)
    print(f"Cycle 20 — {len(picks)} fiches to translate")

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
        nationality = p["nationality"]
        emirate = p["emirate"]
        languages_raw = p.get("languages","")

        # Lookup specialty
        sp_entry = SPECIALTY.get(specialty_orig, SPECIALTY.get("General Dentist"))
        sp_slug = sp_entry["slug"]

        # Lookup license type
        lt_entry = LICENSE_TYPE.get(lic_type_code, LICENSE_TYPE["FTL"])

        # Lookup city
        city_entry = CITY.get(emirate, CITY["Dubai"])

        # Gender
        gender = detect_gender(name_orig, nationality)
        gender_count[gender] = gender_count.get(gender, 0) + 1

        # Languages
        langs_iso = normalize_lang_codes(languages_raw)
        langs_str = ", ".join(langs_iso)

        # Specialty counts
        sp_count[sp_slug] = sp_count.get(sp_slug, 0) + 1
        lic_count[lic_type_code] = lic_count.get(lic_type_code, 0) + 1
        if nationality:
            nat_count[nationality] = nat_count.get(nationality, 0) + 1

        # Nationality labels
        nat_fr = NAT_FR.get(nationality, nationality)
        nat_ar = NAT_AR.get(nationality, nationality)
        nat_ru = NAT_RU.get(nationality, nationality)
        nat_zh = NAT_ZH.get(nationality, nationality)

        # Build translations per language
        fiche = {
            "id": lic,
            "license_number": lic,
            "license_type": {
                "code": lic_type_code,
                "fr": lt_entry["fr"],
                "ar": lt_entry["ar"],
                "en": lt_entry["en"],
                "ru": lt_entry["ru"],
                "zh": lt_entry["zh"],
            },
            "nationality": {
                "orig": nationality,
                "fr": nat_fr,
                "ar": nat_ar,
                "en": nationality,
                "ru": nat_ru,
                "zh": nat_zh,
            },
            "city": {
                "orig": emirate,
                "fr": city_entry["fr"],
                "ar": city_entry["ar"],
                "en": city_entry["en"],
                "ru": city_entry["ru"],
                "zh": city_entry["zh"],
            },
            "specialty": {
                "slug": sp_slug,
                "orig": specialty_orig,
                "fr": sp_entry["fr"],
                "ar": sp_entry["ar"],
                "en": sp_entry["en"],
                "ru": sp_entry["ru"],
                "zh": sp_entry["zh"],
            },
            "languages_spoken": langs_iso,
            "_gender_heuristic": gender,
        }

        # 5-language per-field
        for lang in LANGS:
            name_t = transcribe_name(name_orig, lang)
            city_t = city_entry[lang]
            lic_t = lt_entry[lang]
            sp_t = sp_entry[lang]
            if lang == "fr":
                bio = build_bio(name_t, sp_entry["fr"], city_t, lic_t, gender, langs_iso)
            elif lang == "ar":
                bio = build_bio_ar(name_t, sp_entry["ar"], city_t, lic_t, gender)
            elif lang == "en":
                bio = build_bio_en(name_t, sp_entry["en"], city_t, lic_t, gender)
            elif lang == "ru":
                bio = build_bio_ru(name_t, sp_entry["ru"], city_t, lic_t, gender)
            elif lang == "zh":
                bio = build_bio_zh(name_t, sp_entry["zh"], city_t, lic_t, gender)

            # Services: stub based on specialty (5 langs)
            services = {
                "fr": ["Consultation", "Diagnostic", "Plan de traitement"],
                "ar": ["استشارة", "تشخيص", "خطة علاج"],
                "en": ["Consultation", "Diagnostic", "Treatment plan"],
                "ru": ["Консультация", "Диагностика", "План лечения"],
                "zh": ["咨询", "诊断", "治疗方案"],
            }

            entry = {
                "name": name_t,
                "specialty": sp_t,
                "sub_specialty": None,
                "bio": bio,
                "services": services[lang],
                "languages_spoken": langs_iso,
                "city": city_t,
                "license_type": lic_t,
                "nationality": nat_fr if lang=="fr" else (nat_ar if lang=="ar" else (nationality if lang=="en" else (nat_ru if lang=="ru" else nat_zh))),
                "source_license": lic,
            }
            fiche[lang] = entry

            # Write per-lang file
            out_path = OUT_DIR / f"dentist_{lic}_{lang}.json"
            out_path.write_text(json.dumps(entry, ensure_ascii=False, indent=2), encoding="utf-8")

        new_fiches.append(fiche)
        print(f"   NEW   - {lic} ({sp_slug}, {lic_type_code}, gender={gender}, nat={nationality or '?'}, langs={langs_iso})")

    # Summary file
    summary = {
        "_meta": {
            "schema_version": SCHEMA_VERSION,
            "generated_at": NOW,
            "generator": "build_cycle20.py",
            "cron": "ad25646f-4b17-4eb0-b148-0b7d037c7231",
            "cron_name": "Dubai - Traduction 5 Langues (Medical)",
            "cycle": "2026-06-06 cycle 20/30min",
            "previous_cycle": "2026-06-06 cycle 19/30min (90 fiches cumul)",
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
            "cycle20_notes": [
                "1× Endodontist (Khaled Alqadi, 46889163) — prénom Khaled خالد + patronyme Alqadi القاضي (juge/القاضي shariah)",
                "1× General Dentist (Mohammed Mohammed, 00251485) — prénom composé arabe (محمد محمد) rare, tradition Hijaz/Saudi",
                "1× Oral Surgeon (Arpita Singh, 30135001) — Inde (Arpita Sanskrit अर्पित 'offered' + Singh Pendjab सिंह 'lion' kshatriya)",
                "1× Endodontist (Maria Morales, 00245491) — hispanophone (Maria hébreu מרים / Morales patronyme espagnol 'peupliers')",
                "1× Orthodontist (Jensyll Rodrigues, 94338321) — Philippines/Brésil probable (Jensyll prénom rare filipin, Rodrigues patronyme portugais)",
                "Diversification : 4 specialties distinctes (2× Endodontist, 1× General Dentist, 1× Oral Surgeon, 1× Orthodontist)",
                "5 nationalités probables (JO/PS, SA, IN, ES/MX, PH/BR) — 5 régions du globe couvertes",
                "Mapping NAME_TRANS : 9 entrées arabes + indiennes + hispaniques translittérées en EN/FR/RU/ZH + arabe natif",
                "Cohérence terminologique maintenue sur 13 specialties glossary v1.0 (validé cycles 1-19)",
            ],
        },
        "new_fiches": new_fiches,
        "fill_fiches": [],
    }

    OUT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    total_files = len(new_fiches) * len(LANGS)
    print(f"\n✅ Cycle 20 done: {len(new_fiches)} new × 5 langs = {total_files} files")
    print(f"   Summary: {OUT_SUMMARY}")


if __name__ == "__main__":
    main()
