#!/usr/bin/env python3
"""
DMD Profile Page Generator (5/30min build cycle)
Génère une page profil par dentiste depuis:
  - code/web/data/dentists_emirates.csv (FR source)
  - translations/fiches-*.json (FR/AR/EN)

Output:
  code/web/profiles/fr/<slug>.html
  code/web/profiles/ar/<slug>.html
  code/web/profiles/en/<slug>.html
  code/web/sitemap.xml
  code/web/profiles/index.json
"""
import csv
import json
import re
import sys
from pathlib import Path
from datetime import datetime, timezone
from html import escape

ROOT = Path(__file__).resolve().parent.parent.parent  # /dubai-medical-directory
WEB = ROOT / "code" / "web"
CSV_PATH = WEB / "data" / "dentists_emirates.csv"
TRANS_DIR = ROOT / "translations"
OUT = WEB / "profiles"
BASE_URL = "https://dmd-dubai.com"  # TODO: confirmer avec W

SPECIALTY_FR = {
    "General Dentist": "Dentiste généraliste",
    "Periodontics": "Parodontiste",
    "Endodontics": "Endodontiste",
    "Orthodontics": "Orthodontiste",
    "Implantology Privilege": "Implantologue",
    "Prosthodontics": "Prosthodontiste",
    "Pediatric Dentistry": "Pédodontiste",
    "Oral and Maxillofacial Surgery": "Chirurgien oral et maxillo-facial",
    "Oral Medicine": "Médecin oraliste",
}
SPECIALTY_AR = {
    "General Dentist": "طبيب أسنان عام",
    "Periodontics": "أخصائي أمراض اللثة",
    "Endodontics": "أخصائي علاج العصب",
    "Orthodontics": "أخصائي تقويم الأسنان",
    "Implantology Privilege": "أخصائي زراعة الأسنان",
    "Prosthodontics": "أخصائي التركيبات السنية",
    "Pediatric Dentistry": "طبيب أسنان الأطفال",
    "Oral and Maxillofacial Surgery": "جراح الفم والوجه والفكين",
    "Oral Medicine": "أخصائي طب الفم",
}
SPECIALTY_EN = {
    "General Dentist": "General Dentist",
    "Periodontics": "Periodontist",
    "Endodontics": "Endodontist",
    "Orthodontics": "Orthodontist",
    "Implantology Privilege": "Implantologist",
    "Prosthodontics": "Prosthodontist",
    "Pediatric Dentistry": "Pediatric Dentist",
    "Oral and Maxillofacial Surgery": "Oral & Maxillofacial Surgeon",
    "Oral Medicine": "Oral Medicine Specialist",
}
LICENSE_AR = {"REG": "ترخيص", "FTL": "كامل الترخيص"}


def slugify(name, license_no):
    base = re.sub(r"[^a-z0-9]+", "-", (name or "").lower()).strip("-")
    return f"{base}-{license_no}".strip("-")


def load_translations():
    """Load all fiches from all translation cycles into one map keyed by (name, license_no) and also by name.
    Supports both flat (old cycle01) and nested (cycle02+) schemas.
    """
    out = {}
    for p in sorted(TRANS_DIR.glob("fiches-*.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            for f in d.get("fiches", []):
                if "name" in f and isinstance(f["name"], dict):
                    orig = f["name"].get("original", "")
                    name = {
                        "ar": f["name"].get("ar", orig),
                        "en": f["name"].get("en", orig),
                        "fr": f["name"].get("fr", orig),
                    }
                    spec = f.get("specialty") or {}
                    license_obj = f.get("license_type") or {}
                    entry = {
                        "ar": name["ar"],
                        "en": name["en"],
                        "fr": name["fr"],
                        "specialty_ar": spec.get("ar"),
                        "specialty_en": spec.get("en"),
                        "specialty_fr": spec.get("fr"),
                        "license_ar": license_obj.get("ar"),
                        "license_en": license_obj.get("en"),
                        "license_fr": license_obj.get("fr"),
                        "bio": f.get("bio") or {},
                        "facility": f.get("facility") or {},
                        "area": f.get("area") or {},
                    }
                else:
                    # Old flat schema
                    orig = f.get("original") or f.get("name") or ""
                    entry = {
                        "ar": f.get("ar", orig),
                        "en": f.get("en", orig),
                        "fr": f.get("fr", orig),
                        "specialty_ar": f.get("specialty_ar"),
                        "specialty_en": f.get("specialty_en"),
                        "specialty_fr": f.get("specialty_fr"),
                    }
                out[orig] = entry
                # Also key by license_no for cross-reference
                lic = f.get("license_number") or ""
                if lic:
                    out[f"{orig}|{lic}"] = entry
        except Exception as e:
            print(f"[WARN] {p}: {e}", file=sys.stderr)
    return out


def initials(name):
    parts = [p for p in (name or "").split() if p]
    if not parts:
        return "DR"
    return (parts[0][0] + (parts[-1][0] if len(parts) > 1 else "")).upper()


def render_profile(row, tr, lang):
    """Render a profile page in given lang ('fr' | 'ar' | 'en')."""
    name_orig = row["full_name"]
    specialty_en = row["specialty"]
    facility = row.get("facility_name") or ""
    license_no = row["license_number"]
    license_type = row["license_type"]
    area = row.get("area") or "Dubai"
    profile_url = row.get("profile_url") or ""
    source_url = row.get("source_url") or ""

    # Localized name + specialty
    if lang == "ar":
        name = (tr.get(name_orig) or {}).get("ar", name_orig)
        specialty = (tr.get(name_orig) or {}).get("specialty_ar") or SPECIALTY_AR.get(specialty_en, specialty_en)
        dir_attr = "rtl"
        lang_label = "ar"
        other_langs = [("fr", "🇫🇷 Français"), ("en", "🇬🇧 English")]
        title = f"د. {name} — {specialty} في {area} | DMD Dubai"
        description = f"د. {name}، {specialty} في {area}. احجز موعدك أونلاين 24/7. ملف DHA-موثق."
    else:
        if lang == "fr":
            name = (tr.get(name_orig) or {}).get("fr", name_orig)
            specialty = SPECIALTY_FR.get(specialty_en, specialty_en)
            other_langs = [("ar", "🇸🇦 العربية"), ("en", "🇬🇧 English")]
        else:  # en
            name = (tr.get(name_orig) or {}).get("en", name_orig)
            specialty = SPECIALTY_EN.get(specialty_en, specialty_en)
            other_langs = [("fr", "🇫🇷 Français"), ("ar", "🇸🇦 العربية")]
        dir_attr = "ltr"
        lang_label = lang
        title = f"Dr. {name} — {specialty} in {area} | DMD Dubai"
        description = f"Dr. {name}, {specialty} in {area}. Book online 24/7. DHA-licensed verified profile."

    avatar = initials(name)
    facility_disp = facility or ("—" if lang == "ar" else ("Dubai, UAE" if not facility else "Dubai, UAE"))
    license_disp = {
        "fr": f"DHA-licensé #{license_no} • {license_type}",
        "ar": f"مرخص من DHA رقم {license_no} • {'كامل الترخيص' if license_type == 'FTL' else 'ترخيص'}",
        "en": f"DHA-licensed #{license_no} • {license_type}",
    }[lang]
    cta_text = {
        "fr": "Prendre rendez-vous",
        "ar": "احجز موعدك",
        "en": "Book appointment",
    }[lang]
    verified_text = {
        "fr": "Profil vérifié DHA",
        "ar": "ملف موثق من هيئة الصحة بدبي",
        "en": "DHA-verified profile",
    }[lang]
    about_label = {
        "fr": "À propos",
        "ar": "نبذة",
        "en": "About",
    }[lang]
    specialty_label = {
        "fr": "Spécialité",
        "ar": "التخصص",
        "en": "Specialty",
    }[lang]
    facility_label = {
        "fr": "Établissement",
        "ar": "المنشأة",
        "en": "Facility",
    }[lang]
    license_label = {
        "fr": "Licence DHA",
        "ar": "الترخيص",
        "en": "DHA License",
    }[lang]
    location_label = {
        "fr": "Localisation",
        "ar": "الموقع",
        "en": "Location",
    }[lang]
    back_text = {
        "fr": "← Retour à l'annuaire",
        "ar": "→ العودة إلى الدليل",
        "en": "← Back to directory",
    }[lang]
    source_text = {
        "fr": "Source officielle",
        "ar": "المصدر الرسمي",
        "en": "Official source",
    }[lang]

    # Use base template from profil-premium.html style
    slug = slugify(name_orig, license_no)
    url = f"{BASE_URL}/profiles/{lang}/{slug}.html"
    hreflangs = "".join(
        f'<link rel="alternate" hreflang="{ol}" href="{BASE_URL}/profiles/{ol}/{slug}.html" />'
        for ol, _ in other_langs + [("fr" if lang != "fr" else "en", None)]
    )
    # Simpler: emit x-default + current
    alt_links = []
    for ol, label in other_langs:
        alt_links.append(f'<link rel="alternate" hreflang="{ol}" href="{BASE_URL}/profiles/{ol}/{slug}.html" />')
    alt_links.append(f'<link rel="alternate" hreflang="x-default" href="{BASE_URL}/profiles/fr/{slug}.html" />')

    html = f"""<!DOCTYPE html>
<html lang="{lang_label}" dir="{dir_attr}">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{escape(title)}</title>
  <meta name="description" content="{escape(description)}" />
  <link rel="canonical" href="{url}" />
  {''.join(alt_links)}
  <meta property="og:title" content="{escape(title)}" />
  <meta property="og:description" content="{escape(description)}" />
  <meta property="og:type" content="profile" />
  <meta property="og:url" content="{url}" />
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ font-family: -apple-system, "Inter", "Segoe UI", Roboto, sans-serif; color: #1a202c; background: #f7fafc; line-height: 1.6; }}
    header {{ background: linear-gradient(135deg, #0A2540 0%, #0066FF 100%); color: white; padding: 1rem 1.5rem; position: sticky; top: 0; z-index: 100; }}
    .header-inner {{ max-width: 1100px; margin: 0 auto; display: flex; justify-content: space-between; align-items: center; gap: 1rem; flex-wrap: wrap; }}
    .logo {{ font-size: 1.3rem; font-weight: 800; }}
    .logo span {{ color: #00D4A8; }}
    .lang-switcher {{ display: flex; gap: 0.4rem; }}
    .lang-switcher a {{ color: white; text-decoration: none; padding: 0.4rem 0.7rem; border-radius: 0.4rem; background: rgba(255,255,255,0.15); font-size: 0.85rem; font-weight: 500; }}
    .lang-switcher a.active {{ background: white; color: #0A2540; }}
    main {{ max-width: 900px; margin: 2rem auto; padding: 0 1.5rem; }}
    .breadcrumb {{ color: #64748b; font-size: 0.9rem; margin-bottom: 1.5rem; }}
    .breadcrumb a {{ color: #0066FF; text-decoration: none; }}
    .profile-card {{ background: white; border-radius: 1.2rem; padding: 2.5rem 2rem; box-shadow: 0 4px 24px rgba(0,0,0,0.06); border: 1px solid #e2e8f0; }}
    .profile-head {{ display: flex; gap: 1.5rem; align-items: center; margin-bottom: 2rem; flex-wrap: wrap; }}
    .avatar {{ width: 96px; height: 96px; border-radius: 50%; background: linear-gradient(135deg, #00D4A8 0%, #0066FF 100%); color: white; display: flex; align-items: center; justify-content: center; font-size: 2.2rem; font-weight: 800; flex-shrink: 0; }}
    .name {{ font-size: 1.9rem; font-weight: 800; color: #0A2540; margin-bottom: 0.3rem; }}
    .spec {{ color: #00D4A8; font-size: 1.1rem; font-weight: 600; }}
    .verified {{ display: inline-block; background: #d1fae5; color: #065f46; padding: 0.3rem 0.8rem; border-radius: 2rem; font-size: 0.8rem; font-weight: 600; margin-top: 0.5rem; }}
    .details {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; margin: 1.5rem 0; padding: 1.5rem; background: #f7fafc; border-radius: 0.8rem; }}
    .detail-item {{ }}
    .detail-label {{ font-size: 0.8rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.3rem; font-weight: 600; }}
    .detail-value {{ font-weight: 600; color: #0A2540; }}
    .cta {{ display: block; background: linear-gradient(135deg, #0A2540 0%, #0066FF 100%); color: white; text-align: center; padding: 1.1rem; border-radius: 0.8rem; text-decoration: none; font-weight: 700; font-size: 1.05rem; margin: 1.5rem 0; transition: transform 0.2s; }}
    .cta:hover {{ transform: translateY(-2px); }}
    .about {{ margin-top: 2rem; padding-top: 2rem; border-top: 1px solid #e2e8f0; }}
    .about h2 {{ font-size: 1.3rem; margin-bottom: 0.8rem; color: #0A2540; }}
    .source {{ margin-top: 1rem; font-size: 0.85rem; color: #64748b; }}
    .source a {{ color: #0066FF; text-decoration: none; }}
    footer {{ text-align: center; color: #64748b; font-size: 0.85rem; padding: 2rem 1rem; }}
  </style>
</head>
<body>
  <header>
    <div class="header-inner">
      <a href="/" style="color:white;text-decoration:none;" class="logo">DMD <span>Dubai</span></a>
      <nav class="lang-switcher">
        {"".join(f'<a href="{BASE_URL}/profiles/{ol}/{slug}.html"{" class=\"active\"" if ol==lang else ""}>{label}</a>' for ol, label in (other_langs if lang == "ar" else [("fr", "🇫🇷 FR"), ("ar", "🇸🇦 AR"), ("en", "🇬🇧 EN")]))}
      </nav>
    </div>
  </header>
  <main>
    <div class="breadcrumb"><a href="/">{back_text}</a></div>
    <article class="profile-card">
      <div class="profile-head">
        <div class="avatar">{avatar}</div>
        <div>
          <h1 class="name">Dr. {escape(name)}</h1>
          <div class="spec">{escape(specialty)}</div>
          <div class="verified">✓ {verified_text}</div>
        </div>
      </div>
      <div class="details">
        <div class="detail-item">
          <div class="detail-label">{specialty_label}</div>
          <div class="detail-value">{escape(specialty)}</div>
        </div>
        <div class="detail-item">
          <div class="detail-label">{facility_label}</div>
          <div class="detail-value">{escape(facility_disp)}</div>
        </div>
        <div class="detail-item">
          <div class="detail-label">{license_label}</div>
          <div class="detail-value">{escape(license_disp)}</div>
        </div>
        <div class="detail-item">
          <div class="detail-label">{location_label}</div>
          <div class="detail-value">{escape(area)}, UAE</div>
        </div>
      </div>
      <a href="#book" class="cta">📅 {cta_text}</a>
      <section class="about">
        <h2>{about_label}</h2>
        <p>Dr. {escape(name)} {{
          "fr": f"exerce en tant que {specialty} à {area}. Profil vérifié DHA — license #{license_no} ({license_type}).",
          "ar": f"يعمل {specialty} في {area}. ملف موثق من هيئة الصحة بدبي — ترخيص رقم {license_no} ({'كامل' if license_type=='FTL' else 'عام'}).",
          "en": f"practices as a {specialty} in {area}. DHA-verified profile — license #{license_no} ({license_type}).",
        }}[lang]</p>
        <div class="source">{source_text}: <a href="{escape(source_url, quote=True)}" rel="noopener" target="_blank">Zavis Directory</a></div>
      </section>
    </article>
  </main>
  <footer>© 2026 DMD Dubai — Dubai Medical Directory</footer</body>
</html>
"""
    # fix the bad closing tag
    html = html.replace("</footer</body>", "</footer></body>")
    return html, slug, name


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "fr").mkdir(exist_ok=True)
    (OUT / "ar").mkdir(exist_ok=True)
    (OUT / "en").mkdir(exist_ok=True)

    if not CSV_PATH.exists():
        print(f"[ERR] missing {CSV_PATH}", file=sys.stderr)
        return 1

    translations = load_translations()
    print(f"[INFO] Loaded translations for {len(translations)} names")

    with CSV_PATH.open(encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    print(f"[INFO] Read {len(rows)} dentists from CSV")

    index = []
    for row in rows:
        for lang in ("fr", "ar", "en"):
            html, slug, name = render_profile(row, translations, lang)
            out_path = OUT / lang / f"{slug}.html"
            out_path.write_text(html, encoding="utf-8")
        index.append({
            "slug": slugify(row["full_name"], row["license_number"]),
            "name": row["full_name"],
            "specialty": row["specialty"],
            "license": row["license_number"],
            "facility": row.get("facility_name") or "",
            "profile_url": row.get("profile_url") or "",
        })
        print(f"[OK] Generated 3 pages for Dr. {row['full_name']}")

    (OUT / "index.json").write_text(
        json.dumps({"generated_at": datetime.now(timezone.utc).isoformat(), "count": len(index), "profiles": index}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"[OK] Wrote {OUT / 'index.json'} ({len(index)} profiles)")

    # Sitemap
    sitemap = ['<?xml version="1.0" encoding="UTF-8"?>']
    sitemap.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    sitemap.append('  <url><loc>{0}/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>'.format(BASE_URL))
    for p in index:
        for lang in ("fr", "ar", "en"):
            sitemap.append(f'  <url><loc>{BASE_URL}/profiles/{lang}/{p["slug"]}.html</loc><changefreq>weekly</changefreq><priority>0.8</priority></url>')
    sitemap.append('</urlset>')
    sitemap_path = WEB / "sitemap.xml"
    sitemap_path.write_text("\n".join(sitemap), encoding="utf-8")
    print(f"[OK] Wrote {sitemap_path}")

    # robots.txt
    robots = WEB / "robots.txt"
    robots.write_text(
        f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n",
        encoding="utf-8",
    )
    print(f"[OK] Wrote {robots}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
