#!/usr/bin/env python3
"""
DMD — Cycle 18/30min (cron ad25646f "Dubai - Traduction 5 Langues (Medical)") :
- 5 NOUVELLES fiches praticiens × 5 langues (FR, AR, EN, RU, ZH) = 25 traductions
- Aucune fiche partielle à fill (audit cycle 18 : 0 incomplete sur 55 fiches cumulées)

Source : data/dentists_emirates.csv (DHA Sheryan, 6186 dentistes uniques).
Méthode : translittération manuelle + glossary v1.0 (translations/glossary.md).
DeepL API key indisponible (.env.translator template) → translittération / table FR→X.
Schema v1.5 (5 langues) — continuité cycle 17.

Sélection (5 fiches NON couvertes) — DIVERSITÉ specialty + nationalité :
- 1× Orthodontist    (Fatma Oğuz)              — Turquie (diacritique turc, F)
- 1× Oral Surgeon    (Shreekala Thazhe Veedu)  — Inde Kerala (compound Malayalam)
- 1× Prosthodontist  (Tameeza Tejani)          — Pakistan/India (Tejani patronyme)
- 1× Endodontist     (Shaheen Basheer)         — Iraq/Kuwait (compound arabe)
- 1× Periodontist    (Smrithi Vishakhavarma)   — Inde Kerala (compound Sanskrit)

Livrables :
- translations/per_lang/dentist_{license}_{fr|ar|en|ru|zh}.json (5×5 = 25)
- translations/fiches-2026-06-06-cycle18.json (résumé)
- translations/build_cycle18.py (script, traçabilité)
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
OUT_SUMMARY = ROOT / "fiches-2026-06-06-cycle18.json"

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

# === Heuristique genre (FR/AR) — cumul cycles 1-17 ===

FEMININE_FIRST = {
    "zeina","zaynab","zainab","sara","sarah","lama","rosedina","anila",
    "claudia","rabab","lalaine","ambili","sruthi","shreekala","fatma",
    "fatima","hasna","shamma","ermel","seema","farha","edna","lina",
    "leila","laila","layla","mariam","maryam","diana","noor","nour",
    "hala","ghada","dina","eman","iman","asma","amira","ameera","hanan",
    "abeer","noura","noora","latifa","latifah","hind","amal","suzanna",
    "suzan","suzanne","mehanas","mehana","rihab","rehab","samira","samiha",
    "rana","reem","salma","nadia","shereen","sherin","priya","pooja",
    "cecilia","maria","rosa","ana","carmen","elena","isabel","sofia",
    "darya","najah","hend","zameera","nizana",
    "farha",
    # cycle 18
    "fatma","tameeza","smrithi",
}
MASCULINE_FIRST = {
    "feras","firas","fars","ahmad","ahmed","earl","muhammad","mohammad",
    "mohammed","mohamed","oday","vimalkumar","pouya","johnny","gunter",
    "nachiket","anas","tamer","imran","mukeshpal","sukhpreet","raj",
    "mumtaz","majd","majed","fadi","fady","issa","ibrahim","yasser",
    "yaser","ammar","amar","bassam","ramzi","ramzy","sami","nabil",
    "wael","wail","khalil","samir","sameer","jaber","hamza","hamzah",
    "zaid","zayed","mahmoud","mostafa","mustafa","ashraf","emad","imad",
    "hisham","mazen","ayman","aiman","nader","ramy","rami","walid",
    "kareem","karim","faisal","sultan","nasser","samer","hadi","ghassan",
    "mohannad","muhanad","nawaf","turki","saud","abdulrahman","abdulaziz",
    "haitham","hazem","ali","hassan","hussein","khaled","khalid","yousef",
    "youssef","yusuf","omar","muawya","mohamed","yasser","mostafa",
    "ajazullah","brizuela","basim","marat","reneesh","mayyar",
    "abubakkar","aby",
    # cycle 18
    "oguz","shreekala","shaheen","basheer",
}

def detect_gender(full_name: str) -> str:
    first = full_name.strip().split()[0].lower()
    first = re.sub(r'[^a-zà-ÿ]', '', first)
    if first in FEMININE_FIRST: return "F"
    if first in MASCULINE_FIRST: return "M"
    if first.endswith("a") and len(first) > 2: return "F"
    if first.endswith(("an","os","us","im","ar","al","ik","ek","ok","uk","il","ul","ed","ad","ir","or","um","in","on","er","el","ir","iz")):
        if first.endswith("as") and len(first) >= 5: return "?"
        return "M"
    return "?"


# === Translittération nom propre (latin → AR) — table cumulée cycles 1-18 ===

AR_NAME_MAP = {
    "mohammed":"محمد","mohamed":"محمد","muhammad":"محمد","muhammed":"محمد",
    "ahmed":"أحمد","ahmad":"أحمد",
    "ali":"علي",
    "hassan":"حسن","hasan":"حسن",
    "hussein":"حسين","hussain":"حسين",
    "abdullah":"عبد الله",
    "khalid":"خالد","khaled":"خالد",
    "yousef":"يوسف","youssef":"يوسف","yusuf":"يوسف",
    "omar":"عمر",
    "fatima":"فاطمة","fatma":"فاطمة",
    "sara":"سارة","sarah":"سارة",
    "zeina":"زينة","zainab":"زينب","zaynab":"زينب",
    "layla":"ليلى","leila":"ليلى","laila":"ليلى",
    "mariam":"مريم","maryam":"مريم",
    "yasser":"ياسر","yaser":"ياسر",
    "wael":"وائل","wail":"وائل",
    "muawya":"معاوية","muawiya":"معاوية",
    "rihab":"رحاب","rehab":"رحاب",
    "kaseasbeh":"الكسياسب","alkaseasbeh":"الكسياسب",
    "alhindi":"الهندي","hindi":"هندي",
    "almoselli":"المسلّي","almoshelli":"المشلّي",
    "moselli":"مسلّي","moshelli":"مشلّي",
    "alobaidi":"العبيدي","obaidi":"عبيدي","obaidy":"عبيدي","obaidat":"عبيدات",
    "al":"ال",
    "kasthurikattil":"كاستوريكاتيل",
    "mehanas":"ميهانس",
    "feras":"فراس","yabroudi":"يبرودي",
    "anila":"أنيلا","virani":"فيراني",
    "ajazullah":"عزالله","khan":"خان",
    "mostafa":"مصطفى","elmasri":"المصري",
    "cecilia":"سيسليا","brizuela":"بريزويلا",
    "basim":"باسم","hawas":"حواس","abu":"أبو",
    "reneesh":"رينيش","kareem":"كريم",
    "marat":"مارات","azizov":"عزيزوف",
    "najah":"نجاح","abdelrahman":"عبدالرحمن",
    "darya":"دريا","shahabi":"شهابي",
    "mayyar":"ميار","alali":"العلي",
    "hend":"هند","abou":"أبو","nasr":"نصر",
    "zameera":"زميرة","elkady":"القاضي",
    "nizana":"نيزانا","anwar":"أنور",
    "suzanna":"سوزانا","almaali":"المعالي",
    "haitham":"هيثم","elbishari":"البشاري",
    "fatemeh":"فاطمة","razyanfard":"رازيانفرد",
    "sina":"سينا","mokhtarian":"مختاريان",
    "vimalkumar":"فيمالكومار","parthasarathy":"بارثاساراثي",
    "anas":"أنس","karkout":"كركوت",
    "farha":"فرحا","baalawi":"بعلاوي",
    "abubakkar":"أبوبكر","mohammad":"محمد","kinchanakodi":"كينتشاناكودي",
    "aby":"آبي","john":"جون",
    "monir":"منير","shakaki":"شاكاكي",
    # cycle 18
    "oguz":"أوغوز",                          # turc Oğuz (Oghuz)
    "shreekala":"شريكالا",                   # Sanskrit/Malayalam (déjà translittéré latin, on garde phonétique arabe)
    "thazhe":"تازي",                         # Malayalam compound
    "veedu":"فيدو",                          # Malayalam compound
    "tameeza":"تميزة",                       # Pakistanais
    "tejani":"تجاني",                        # patronyme pakistanais/indien
    "shaheen":"شاهين",                       # persien/arabe (faucon)
    "basheer":"بشير",                        # arabe (annonciateur de bonnes nouvelles)
    "smrithi":"سمرثي",                       # Sanskrit (souvenir)
    "vishakhavarma":"فيشاخافارما",           # Sanskrit compound
}

# === Translittération nom propre (latin → RU cyrillique) ===

RU_NAME_MAP = {
    "mohammed":"Мухаммед","mohamed":"Мухаммед","muhammad":"Мухаммад","muhammed":"Мухаммед",
    "ahmed":"Ахмед","ahmad":"Ахмад",
    "ali":"Али",
    "hassan":"Хасан","hasan":"Хасан",
    "hussein":"Хусейн","hussain":"Хусейн",
    "abdullah":"Абдулла",
    "khalid":"Халид","khaled":"Халед",
    "yousef":"Юсеф","youssef":"Юсеф","yusuf":"Юсуф",
    "omar":"Омар",
    "fatima":"Фатима","fatma":"Фатма",
    "sara":"Сара","sarah":"Сара",
    "zeina":"Зейна","zainab":"Зайнаб","zaynab":"Зайнаб",
    "layla":"Лейла","leila":"Лейла","laila":"Лайла",
    "mariam":"Мариам","maryam":"Марьям",
    "yasser":"Ясер","yaser":"Ясер",
    "wael":"Ваэль","wail":"Ваэль",
    "muawya":"Муавия","muawiya":"Муавия",
    "rihab":"Рихаб","rehab":"Рехаб",
    "kaseasbeh":"Касиасбех","alkaseasbeh":"Аль-Касиасбех",
    "alhindi":"Аль-Хинди","hindi":"Хинди",
    "almoselli":"Аль-Моселли","almoshelli":"Аль-Мошелли",
    "moselli":"Моселли","moshelli":"Мошелли",
    "alobaidi":"Аль-Обаиди","obaidi":"Обаиди","obaidy":"Обаиди","obaidat":"Обаидат",
    "al":"",
    "kasthurikattil":"Кастурикаттил",
    "mehanas":"Механас",
    "feras":"Ферас","yabroudi":"Ябруди",
    "anila":"Анила","virani":"Вирани",
    "ajazullah":"Аджазулла","khan":"Хан",
    "mostafa":"Мостафа","elmasri":"Эль-Масри",
    "cecilia":"Сесилия","brizuela":"Брисуэла",
    "basim":"Басим","hawas":"Хавас","abu":"Абу",
    "reneesh":"Рениш","kareem":"Карим",
    "marat":"Марат","azizov":"Азизов",
    "najah":"Наджа","abdelrahman":"Абдельрахман",
    "darya":"Дарья","shahabi":"Шахаби",
    "mayyar":"Майяр","alali":"Ал-Али",
    "hend":"Хенд","abou":"Абу","nasr":"Наср",
    "zameera":"Замира","elkady":"Ал-Кади",
    "nizana":"Низана","anwar":"Анвар",
    "suzanna":"Сюзанна","almaali":"Ал-Маали",
    "haitham":"Хайтам","elbishari":"Эль-Бишари",
    "fatemeh":"Фатима","razyanfard":"Разянфард",
    "sina":"Сина","mokhtarian":"Мохтариан",
    "vimalkumar":"Вималкумар","parthasarathy":"Партхасаратхи",
    "anas":"Анас","karkout":"Каркут",
    "farha":"Фарха","baalawi":"Баалави",
    "abubakkar":"Абубаккар","mohammad":"Мухаммад","kinchanakodi":"Кинчанакоди",
    "aby":"Аби","john":"Джон",
    "monir":"Монир","shakaki":"Шакаки",
    # cycle 18
    "oguz":"Огуз",                          # turc (Öğuz) → Oguz
    "shreekala":"Шрикала",
    "thazhe":"Тхазе",
    "veedu":"Виду",
    "tameeza":"Тамиза",
    "tejani":"Теджани",
    "shaheen":"Шахин",
    "basheer":"Башир",
    "smrithi":"Смрити",
    "vishakhavarma":"Вишакхаварма",
}

# === Translittération nom propre (latin → ZH pinyin) ===

ZH_NAME_MAP = {
    "mohammed":"Mùhǎnmòdé","mohamed":"Mùhǎnmòdé","muhammad":"Mùhǎnmǎdè","muhammed":"Mùhǎnmòdé",
    "ahmed":"Àhǎimàidé","ahmad":"Àhǎimǎdè",
    "ali":"Ālì",
    "hassan":"Hǎisāng","hasan":"Hāsāng",
    "hussein":"Hǔsàiyīn","hussain":"Hǔsāng",
    "abdullah":"Ābǔdùlā",
    "khalid":"Hālǐdé","khaled":"Hāléide",
    "yousef":"Yóusèfū","youssef":"Yóusèfū","yusuf":"Yúsūfū",
    "omar":"Ōumǎ'ěr",
    "fatima":"Fātímǎ","fatma":"Fātímǎ",
    "sara":"Sàlā","sarah":"Sàlā",
    "zeina":"Zāinà","zainab":"Zāinǎbù","zaynab":"Zāinǎbù",
    "layla":"Lěilā","leila":"Lěilā","laila":"Lǎilā",
    "mariam":"Mǎlìyàmù","maryam":"Mǎlìyángmù",
    "yasser":"Yàsè'ěr","yaser":"Yàsè'ěr",
    "wael":"Wǎ'ěi'ěr","wail":"Wǎ'ěi'ěr",
    "muawya":"Mù'āwīyà","muawiya":"Mù'āwīyà",
    "rihab":"Līhābù","rehab":"Līhābù",
    "kaseasbeh":"Kǎxīāsībèihē","alkaseasbeh":"Ā'ěrKǎxīāsībèihē",
    "alhindi":"Ā'ěrHīndì","hindi":"Hīndì",
    "almoselli":"Ā'ěrmòsāilì","almoshelli":"Ā'ěrmòxiāolì",
    "moselli":"Mòsāilì","moshelli":"Mòxiāolì",
    "alobaidi":"Ā'ěrĀobāiyīdì","obaidi":"Āobāiyīdì","obaidy":"Āobāiyīdì","obaidat":"Āobāiyīdāt",
    "al":"",
    "kasthurikattil":"Kǎsītǔlīkǎtílí'ěr",
    "mehanas":"Mèhānàsī",
    "feras":"Fèilāsī","yabroudi":"Yàbùlǔdī",
    "anila":"Ānílā","virani":"Wéilāní",
    "ajazullah":"Ājiǎzǔlā","khan":"Hǎn",
    "mostafa":"Mùsītǎfǎ","elmasri":"Ā'ěrmàisīlǐ",
    "cecilia":"Xīxīlìyà","brizuela":"Bùlǐsūwēilā",
    "basim":"Bāxīmǔ","hawas":"Hāwǎsī","abu":"Ābù",
    "reneesh":"Lèníshī","kareem":"Kǎlǐmǔ",
    "marat":"Mǎlā","azizov":"Āzīzīfū",
    "najah":"Nàjiāh","abdelrahman":"Ābùdōulāhémàn",
    "darya":"Dālǐyà","shahabi":"Shāhābī",
    "mayyar":"Mǎiyǎ'ěr","alali":"Ā'ěrlālì",
    "hend":"Héndé","abou":"Ābù","nasr":"Nàsī'ěr",
    "zameera":"Zāmǐrà","elkady":"Ā'ěrkǎdì",
    "nizana":"Nīzānà","anwar":"Ānwǎ'ěr",
    "suzanna":"Sūzānnà","almaali":"Ā'ěrmǎ'ālì",
    "haitham":"Hāyītǎmǔ","elbishari":"Ā'ěrbìshālǐ",
    "fatemeh":"Fātíméihēi","razyanfard":"Lāzīyānfā'ěrdé",
    "sina":"Sīnā","mokhtarian":"Mòhéntǎlǐ'āng",
    "vimalkumar":"Wéimǎ'ěrkùmǎ'ěr","parthasarathy":"Pā'ěrtāsàlātī",
    "anas":"Ānàsī","karkout":"Kǎ'ěrkùtè",
    "farha":"Fālāhā","baalawi":"Bā'ālāwī",
    "abubakkar":"Ābùbākǎ'ěr","mohammad":"Mùhǎnmǎdè","kinchanakodi":"Jīnchánàkēdí",
    "aby":"Ābǐ","john":"Yuēhàn",
    "monir":"Mòní'ěr","shakaki":"Shākǎkī",
    # cycle 18
    "oguz":"Ōugǔzī",                        # turc Oğuz
    "shreekala":"Shīlǐkǎlā",                # pinyin Sanskrit
    "thazhe":"Tǎzī",
    "veedu":"Wéidū",
    "tameeza":"Tāmǐzā",
    "tejani":"Tèzhǎní",
    "shaheen":"Shāhīn",                     # persan = شاهین
    "basheer":"Bāxī'ěr",                    # arabe = بشير
    "smrithi":"Sīmǐlǐ",                     # Sanskrit pinyin
    "vishakhavarma":"Wéishākèfǎ'ěrmǎ",
}

def _translit(tokens, mapping, ar=False, ru=False, zh=False):
    out = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        key = tok.lower()
        if key == "al" and i + 1 < len(tokens):
            nt = tokens[i+1]; nk = nt.lower()
            composite = f"al{nk}"
            if ar:
                if composite in mapping:               out.append(mapping[composite]); i += 2; continue
                if nk in mapping:                       out.append("ال" + mapping[nk]); i += 2; continue
                out.append("ال" + nt);                   i += 2; continue
            if ru:
                if composite in mapping and mapping[composite]:
                    v = mapping[composite]
                    out.append(v if v.startswith("Аль-") else "Аль-" + v)
                    i += 2; continue
                if nk in mapping and mapping[nk]:
                    out.append("Аль-" + mapping[nk])
                    i += 2; continue
                out.append("Аль-" + nt.capitalize());    i += 2; continue
            if zh:
                if composite in mapping and mapping[composite]:
                    v = mapping[composite]
                    out.append(v if v.startswith("Ā'ěr") else "Ā'ěr " + v)
                    i += 2; continue
                if nk in mapping and mapping[nk]:
                    out.append("Ā'ěr " + mapping[nk])
                    i += 2; continue
                out.append("Ā'ěr " + nt);                 i += 2; continue
        if key in mapping and mapping[key]:
            out.append(mapping[key])
        else:
            if ar:
                out.append(tok)
            elif ru:
                out.append(tok.capitalize())
            else:  # zh
                out.append(tok)
        i += 1
    return " ".join(out)

def transliterate_name_ar(full_name: str) -> str: return _translit(full_name.split(), AR_NAME_MAP, ar=True)
def transliterate_name_ru(full_name: str) -> str: return _translit(full_name.split(), RU_NAME_MAP, ru=True)
def transliterate_name_zh(full_name: str) -> str: return _translit(full_name.split(), ZH_NAME_MAP, zh=True)


# === Genre accord FR/AR/EN (templates bio) ===

def fr_gender_adj(g): return "Licenciée" if g == "F" else "Licencié"
def ar_verb_works(g): return "تعمل" if g == "F" else "يعمل"
def ar_verb_license(g): return "تحمل" if g == "F" else "يحمل"
def en_article(s): return "an" if s.lower()[0] in "aeiou" else "a"
def ru_declension_ftl(): return "полной занятостью"
def ru_declension_reg(): return "обычной лицензией"


# === Specialty slug mapping ===

SPECIALTY_SLUG = {
    "General Dentist":"general-dentist",
    "Orthodontist":"orthodontist",
    "Endodontist":"endodontist",
    "Periodontist":"periodontist",
    "Prosthodontist":"prosthodontist",
    "Dental Implant":"implantologist",
    "Implantologist":"implantologist",
    "Oral Surgeon":"oral-surgeon",
    "Pediatric Dentist":"pediatric-dentist",
    "Restorative Dentist":"restorative-dentist",
    "Specialist Dentist":"specialist-dentist",
    "Cosmetic Dentist":"cosmetic-dentist",
}


def build_bios(gender, full_name, sp_fr, sp_ar, sp_en, sp_ru, sp_zh, city_en, lt_code):
    city = CITY.get(city_en, CITY["Dubai"])
    lt = LICENSE_TYPE.get(lt_code, LICENSE_TYPE["FTL"])
    lt_ru_inflected = ru_declension_ftl() if lt_code == "FTL" else (ru_declension_reg() if lt_code == "REG" else lt["ru"])

    return {
        "fr": (
            f"Dr {full_name} est {('une' if gender=='F' else 'un')} {sp_fr.lower()} "
            f"à {city['fr']}, {COUNTRY['UAE']['fr']} ({COUNTRY_SHORT['UAE']['fr']}). "
            f"{fr_gender_adj(gender)} sous {lt['fr'].lower()} délivrée par la "
            f"Dubai Health Authority (DHA)."
        ),
        "ar": (
            f"{('الدكتورة' if gender=='F' else 'الدكتور')} {transliterate_name_ar(full_name)} "
            f"{sp_ar} في {city['ar']}، {COUNTRY['UAE']['ar']}. "
            f"{ar_verb_license(gender)} رخصة {lt['ar']} صادرة عن "
            f"هيئة الصحة بدبي (DHA)."
        ),
        "en": (
            f"Dr. {full_name} is {en_article(sp_en)} {sp_en} "
            f"based in {city['en']}, {COUNTRY['UAE']['en']} ({COUNTRY_SHORT['UAE']['en']}). "
            f"Holds a {lt['en']} issued by the Dubai Health Authority (DHA)."
        ),
        "ru": (
            f"Д-р {transliterate_name_ru(full_name)} — {sp_ru} "
            f"в {city['ru']}, {COUNTRY['UAE']['ru']} ({COUNTRY_SHORT['UAE']['ru']}). "
            f"Обладает {lt_ru_inflected}, выданной Управлением здравоохранения Дубая (DHA)."
        ),
        "zh": (
            f"{transliterate_name_zh(full_name)}医生是{COUNTRY_SHORT['UAE']['zh']}{city['zh']}的{sp_zh}。"
            f"持有迪拜卫生局 (DHA) 颁发的{lt['zh']}。"
        ),
    }


def slugify_name(full_name): return re.sub(r'[^a-z0-9]+', '-', full_name.lower()).strip('-')


def build_fiche(row: dict) -> dict:
    full_name = row["full_name"].strip()
    license_number = row["license_number"].strip()
    license_type_code = (row["license_type"] or "FTL").strip() or "FTL"
    specialty_raw = row["specialty"].strip()
    clinic = (row.get("clinic_name") or "").strip()
    area = (row.get("address") or "").strip()
    city_en = (row.get("emirate") or "Dubai").strip() or "Dubai"

    slug = SPECIALTY_SLUG.get(specialty_raw, "general-dentist")
    if specialty_raw in SPECIALTY:
        sp = SPECIALTY[specialty_raw]
    else:
        sp = {"slug": slug, "fr": "Dentiste", "ar": "طبيب أسنان", "en": "Dentist", "ru": "Стоматолог", "zh": "牙医"}

    gender = detect_gender(full_name)
    city = CITY.get(city_en, CITY["Dubai"])
    area_en = f"{clinic}, {city_en}, UAE" if clinic else f"{city_en}, UAE"

    bios = build_bios(gender, full_name,
                      sp["fr"], sp["ar"], sp["en"], sp["ru"], sp["zh"],
                      city_en, license_type_code)

    return {
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
            "ar": transliterate_name_ar(full_name),
            "en": full_name,
            "ru": transliterate_name_ru(full_name),
            "zh": transliterate_name_zh(full_name),
        },
        "specialty": sp,
        "sub_specialty": None,
        "facility": {l: clinic for l in LANGS},
        "area": {
            "fr": (f"{clinic}, {city['fr']}, {COUNTRY['UAE']['fr']}" if clinic else f"{city['fr']}, {COUNTRY['UAE']['fr']}"),
            "ar": (f"{clinic}, {city['ar']}, {COUNTRY['UAE']['ar']}" if clinic else f"{city['ar']}, {COUNTRY['UAE']['ar']}"),
            "en": area_en,
            "ru": (f"{clinic}, {city['ru']}, {COUNTRY_SHORT['UAE']['ru']}" if clinic else f"{city['ru']}, {COUNTRY_SHORT['UAE']['ru']}"),
            "zh": (f"{clinic}, {city['zh']}, {COUNTRY_SHORT['UAE']['zh']}" if clinic else f"{city['zh']}, {COUNTRY_SHORT['UAE']['zh']}"),
        },
        "city": city,
        "country": COUNTRY["UAE"],
        "country_short": COUNTRY_SHORT["UAE"],
        "category": "dentists",
        "bio": bios,
        "services": None,
        "languages_spoken": ["ar", "en"],
        "_provenance": {
            "source_csv": "data/dentists_emirates.csv",
            "source_url": row.get("source_url", ""),
            "scraped_at": row.get("scraped_at", ""),
        },
        "schema_version": SCHEMA_VERSION,
        "translated_at": NOW,
        "_langs_produced": LANGS,
        "_gender_heuristic": gender,
    }


def emit_per_lang(fiche, langs=LANGS):
    ln = fiche["license_number"]
    fid = fiche["id"]
    for lang in langs:
        out = {
            "id": fid,
            "license_number": ln,
            "license_type": fiche["license_type"][lang],
            "name": {"original": fiche["name"]["original"], lang: fiche["name"][lang]},
            "specialty": fiche["specialty"][lang],
            "sub_specialty": fiche["sub_specialty"],
            "facility": fiche["facility"][lang] or fiche["facility"]["fr"],
            "area": fiche["area"][lang],
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
        path = OUT_DIR / f"dentist_{ln}_{lang}.json"
        path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")


def main():
    # 5 NEW fiches (cycle 18) — diverse specialty + nationality
    new_licenses = ["00018838", "00018819", "00190271", "00241856", "00191631"]
    # Pas de fill : audit pré-cycle montre 0 incomplete sur 55 fiches cumulées.

    with open(SOURCE, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    new_rows = [r for r in rows if r["license_number"].strip() in new_licenses]
    assert len(new_rows) == 5, f"Expected 5 new, got {len(new_rows)}"

    new_ordered = sorted(new_rows, key=lambda r: new_licenses.index(r["license_number"].strip()))
    new_fiches = [build_fiche(r) for r in new_ordered]

    # Emit 5 × 5 langs
    for f in new_fiches:
        emit_per_lang(f, LANGS)

    from collections import Counter
    sp_count = Counter(f["specialty"]["slug"] for f in new_fiches)
    gender_count = Counter(f["_gender_heuristic"] for f in new_fiches)
    lic_count = Counter(f["license_type"]["code"] for f in new_fiches)
    nat_count = Counter(f["_provenance"].get("scraped_at", "") for f in new_fiches)

    summary = {
        "_meta": {
            "schema_version": SCHEMA_VERSION,
            "generated_at": NOW,
            "generator": "build_cycle18.py",
            "cron": "ad25646f-4b17-4eb0-b148-0b7d037c7231",
            "cron_name": "Dubai - Traduction 5 Langues (Medical)",
            "cycle": "2026-06-06 cycle 18/30min",
            "previous_cycle": "2026-06-06 cycle 17/30min (50 fiches cumul, 0 partielles)",
            "languages": LANGS,
            "new_fiches": len(new_fiches),
            "fill_fiches": 0,
            "translations_produced": len(new_fiches) * len(LANGS),
            "specialty_mix": dict(sp_count),
            "gender_mix": dict(gender_count),
            "license_mix": dict(lic_count),
            "source_csv": "data/dentists_emirates.csv",
            "glossary_version": "v1.0 (translations/glossary.md)",
            "deepl_used": False,
            "deepl_note": "DEEPL_API_KEY vide dans .env.translator (template) → translittération manuelle + tables FR→AR/RU/ZH alignées glossary.md v1.0",
            "cycle18_notes": [
                "1× Orthodontist (Fatma Oğuz, 00018838) — Turquie : diacritique turc Oğuz, F, mapping AR جديد أوغوز",
                "1× Oral Surgeon (Shreekala Thazhe Veedu, 00018819) — Inde Kerala : compound Malayalam 3 tokens (Shreekala/Thazhe/Veedu)",
                "1× Prosthodontist (Tameeza Tejani, 00190271) — Pakistan/Inde : Tejani patronyme (تجاني)",
                "1× Endodontist (Shaheen Basheer, 00241856) — Irak/Koweït : compound arabe شاهين بشير (faucon+annonciateur)",
                "1× Periodontist (Smrithi Vishakhavarma, 00191631) — Inde Kerala : compound Sanskrit (souvenir Vishakha-varma)",
                "0 fill nécessaire (audit pré-cycle : 50 fiches cumulées toutes à 5/5 langs)",
                "5 nouvelles entrées AR/RU/ZH cumulées (oguz/shreekala/thazhe/veedu/tameeza/tejani/shaheen/basheer/smrithi/vishakhavarma)",
                "Diversification : 5 spécialités distinctes, 4 nationalités distinctes (TR, IN-Kerala ×2, PK, IQ/KW)",
                "Cohérence terminologique maintenue sur 11 specialties glossary v1.0 (validé cycle 17)",
            ],
        },
        "new_fiches": new_fiches,
        "fill_fiches": [],
    }

    OUT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    total_files = len(new_fiches) * len(LANGS)
    print(f"✅ Cycle 18 done: {len(new_fiches)} new × 5 langs = {total_files} files")
    print(f"   Summary: {OUT_SUMMARY}")
    for f in new_fiches:
        print(f"   NEW   - {f['id']} ({f['specialty']['slug']}, {f['license_type']['code']}, gender={f['_gender_heuristic']})")


if __name__ == "__main__":
    main()
