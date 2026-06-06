"""
DMD Dubai — Brand & mockup generator.
Produces 5 PNG mockups for the Dubai Medical Directory website.
"""
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os, math, random

# ---------- BRAND ----------
BRAND = {
    "name": "DMD Dubai",
    "tagline": "Dubai Medical Directory",
    "blue":       (0, 90, 156),     # primary — médical
    "blue_dark":  (0, 56, 102),
    "blue_light": (229, 240, 250),
    "green":      (40, 167, 95),    # confiance
    "green_dark": (28, 120, 66),
    "white":      (255, 255, 255),
    "offwhite":   (248, 250, 252),
    "ink":        (28, 33, 44),
    "ink_soft":   (90, 99, 112),
    "line":       (220, 226, 235),
    "warn":       (234, 88, 12),
    "gold":       (212, 175, 55),
    "shadow":     (0, 0, 0, 28),
}

# ---------- FONTS ----------
F = {}
def load_fonts():
    paths = {
        "regular": "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "bold":    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "serif":   "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        "serif_b": "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    }
    for k, p in paths.items():
        if os.path.exists(p):
            F[k] = p
load_fonts()

def font(key, size):
    return ImageFont.truetype(F[key], size)

# ---------- HELPERS ----------
def new_canvas(w, h, bg=BRAND["offwhite"]):
    img = Image.new("RGB", (w, h), bg)
    return img, ImageDraw.Draw(img)

def rounded(draw, xy, r, fill=None, outline=None, width=1):
    draw.rounded_rectangle(xy, radius=r, fill=fill, outline=outline, width=width)

def text_w(draw, txt, fnt):
    bbox = draw.textbbox((0, 0), txt, font=fnt)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]

def text(draw, xy, txt, fnt, fill=BRAND["ink"]):
    draw.text(xy, txt, font=fnt, fill=fill)

def hbar(draw, x, y, w, h, color):
    draw.rectangle([x, y, x + w, y + h], fill=color)

def vbar(draw, x, y, w, h, color):
    draw.rectangle([x, y, x + w, y + h], fill=color)

def shadow_box(draw, xy, r, fill, shadow_offset=4, shadow_alpha=24):
    x1, y1, x2, y2 = xy
    sh = Image.new("RGBA", (x2 - x1 + shadow_offset * 4, y2 - y1 + shadow_offset * 4), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    sd.rounded_rectangle(
        [shadow_offset, shadow_offset, x2 - x1 + shadow_offset, y2 - y1 + shadow_offset],
        radius=r, fill=(0, 0, 0, shadow_alpha))
    sh = sh.filter(ImageFilter.GaussianBlur(6))
    return sh

# ---------- LOGO ----------
def draw_logo(draw, x, y, size=28, color=BRAND["blue"]):
    """Simple mark: rounded square 'D' with a medical cross accent."""
    s = size
    # tile
    rounded(draw, [x, y, x + s, y + s], 8, fill=color)
    # cross (small, white) — top-right
    cx, cy = x + s - s * 0.35, y + s * 0.25
    cw, ct = s * 0.18, s * 0.55
    rounded(draw, [cx - cw / 2, cy - ct / 2, cx + cw / 2, cy + ct / 2], 2, fill=BRAND["white"])
    rounded(draw, [cx - ct / 2, cy - cw / 2, cx + ct / 2, cy + cw / 2], 2, fill=BRAND["white"])
    # D letter
    fnt = font("serif_b", int(s * 0.62))
    w, h = text_w(draw, "D", fnt)
    draw.text((x + s * 0.18, y + s * 0.08), "D", font=fnt, fill=BRAND["white"])
    return x + s

def logo_wordmark(draw, x, y, color=BRAND["ink"], size=22, accent=BRAND["blue"]):
    draw_logo(draw, x, y, size=size, color=accent)
    fnt = font("bold", int(size * 0.85))
    text(draw, (x + size + 8, y + 2), "DMD Dubai", fnt, fill=color)
    return x + size + 8 + text_w(draw, "DMD Dubai", fnt)[0]

# ---------- DOCTOR CARDS (data) ----------
DENTISTS = [
    {"name":"Dr. Layla Mansour",  "spec":"Orthodontie",          "langs":["FR","AR","EN"], "zone":"Jumeirah",        "rating":4.9, "reviews":312, "premium":True,  "price":"Premium"},
    {"name":"Dr. Karim Haddad",   "spec":"Chirurgie orale",      "langs":["FR","AR","EN"], "zone":"Downtown",        "rating":4.8, "reviews":241, "premium":True,  "price":"Premium"},
    {"name":"Dr. Sophie Bernard", "spec":"Esthétique dentaire",  "langs":["FR","EN","RU"], "zone":"Marina",          "rating":4.9, "reviews":189, "premium":True,  "price":"Premium"},
    {"name":"Dr. Omar Al-Sayed",  "spec":"Implantologie",        "langs":["AR","EN"],      "zone":"Deira",           "rating":4.7, "reviews":158, "premium":False, "price":"Standard"},
    {"name":"Dr. Wei Chen",       "spec":"Pédodontie",           "langs":["EN","ZH"],      "zone":"Business Bay",    "rating":4.8, "reviews":142, "premium":True,  "price":"Premium"},
    {"name":"Dr. Maria Rossi",    "spec":"Parodontologie",       "langs":["FR","EN","IT"], "zone":"JLT",             "rating":4.6, "reviews":128, "premium":False, "price":"Standard"},
    {"name":"Dr. Youssef Khalil", "spec":"Endodontie",           "langs":["FR","AR","EN"], "zone":"Al Barsha",       "rating":4.9, "reviews":201, "premium":True,  "price":"Premium"},
    {"name":"Dr. Anna Petrov",    "spec":"Prothèses",            "langs":["EN","RU"],      "zone":"Dubai Hills",     "rating":4.7, "reviews":98,  "premium":False, "price":"Standard"},
    {"name":"Dr. Hassan Trabelsi","spec":"Chirurgie orale",      "langs":["FR","AR","EN"], "zone":"Al Wasl",         "rating":4.8, "reviews":167, "premium":True,  "price":"Premium"},
    {"name":"Dr. Lina Farouk",    "spec":"Orthodontie",          "langs":["AR","EN","RU"], "zone":"Mirdif",          "rating":4.9, "reviews":222, "premium":True,  "price":"Premium"},
]

def initials(name):
    parts = name.replace("Dr.", "").replace("Dr ", "").strip().split()
    return "".join([p[0] for p in parts[:2]]).upper()

def avatar_color(seed):
    h = sum(ord(c) for c in seed)
    return (60 + (h * 7) % 160, 80 + (h * 11) % 130, 130 + (h * 13) % 100)

def draw_avatar(draw, cx, cy, r, name):
    color = avatar_color(name)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color)
    fnt = font("bold", int(r * 0.85))
    w, h = text_w(draw, initials(name), fnt)
    draw.text((cx - w / 2, cy - h / 2 - 2), initials(name), font=fnt, fill=BRAND["white"])

def draw_rating(draw, x, y, rating, reviews, color=BRAND["ink"]):
    # star
    sx, sy = x, y
    pts = []
    for i in range(5):
        cx = sx + i * 14
        for j in range(5):
            angle = -math.pi / 2 + j * 2 * math.pi / 5
            r = 5
            px = cx + math.cos(angle) * r
            py = sy + math.sin(angle) * r
            if j == 0:
                pts = [(px, py)]
            else:
                pts.append((px, py))
    full = int(rating)
    for i in range(5):
        cx = sx + i * 14
        if i < full:
            draw.polygon([(cx, sy - 6), (cx + 2, sy - 2), (cx + 6, sy - 1),
                          (cx + 3, sy + 2), (cx + 4, sy + 6),
                          (cx, sy + 4), (cx - 4, sy + 6), (cx - 3, sy + 2),
                          (cx - 6, sy - 1), (cx - 2, sy - 2)], fill=(245, 175, 33))
        else:
            draw.polygon([(cx, sy - 6), (cx + 2, sy - 2), (cx + 6, sy - 1),
                          (cx + 3, sy + 2), (cx + 4, sy + 6),
                          (cx, sy + 4), (cx - 4, sy + 6), (cx - 3, sy + 2),
                          (cx - 6, sy - 1), (cx - 2, sy - 2)], fill=(220, 226, 235))
    fnt = font("bold", 11)
    draw.text((sx + 5 * 14 + 4, sy - 8), f"{rating:.1f}  ({reviews})", font=fnt, fill=color)

def draw_dentist_card(draw, x, y, w, h, d):
    rounded(draw, [x, y, x + w, y + h], 14, fill=BRAND["white"], outline=BRAND["line"])
    # premium ribbon
    if d["premium"]:
        rb_w = 56
        rounded(draw, [x + w - rb_w - 8, y + 8, x + w - 8, y + 24], 6, fill=BRAND["gold"])
        f = font("bold", 10)
        t = "PREMIUM"
        tw, th = text_w(draw, t, f)
        draw.text((x + w - 8 - tw - 4, y + 11), t, font=f, fill=BRAND["white"])
    # avatar
    draw_avatar(draw, x + 36, y + 36, 26, d["name"])
    # name
    fnt = font("bold", 14)
    draw.text((x + 72, y + 24), d["name"], font=fnt, fill=BRAND["ink"])
    fnt2 = font("regular", 12)
    draw.text((x + 72, y + 44), d["spec"], font=fnt2, fill=BRAND["ink_soft"])
    # rating
    draw_rating(draw, x + 14, y + 78, d["rating"], d["reviews"])
    # chips
    cx = x + 14
    cy = y + 102
    for lang in d["langs"]:
        chip = lang
        cw, ch = text_w(draw, chip, font("bold", 10))
        rounded(draw, [cx, cy, cx + cw + 14, cy + 20], 10, fill=BRAND["blue_light"], outline=BRAND["blue"])
        draw.text((cx + 7, cy + 4), chip, font=font("bold", 10), fill=BRAND["blue"])
        cx += cw + 22
    # zone + price
    fnt3 = font("regular", 11)
    draw.text((x + 14, y + h - 26), f"📍 {d['zone']}", font=fnt3, fill=BRAND["ink_soft"])
    price_color = BRAND["gold"] if d["premium"] else BRAND["ink_soft"]
    pwt, _ = text_w(draw, d["price"], font("bold", 11))
    draw.text((x + w - 14 - pwt, y + h - 26), d["price"], font=font("bold", 11), fill=price_color)
    # CTA
    cta_y = y + h - 22
    return (x, y, w, h)

# ---------- HEADER / NAV ----------
def header(draw, w, langs=("FR","AR","EN","RU","ZH"), active_lang="FR", bg=BRAND["white"]):
    h = 64
    rounded(draw, [0, 0, w, h], 0, fill=bg)
    # bottom line
    draw.line([(0, h), (w, h)], fill=BRAND["line"], width=1)
    # logo
    logo_wordmark(draw, 28, 20, color=BRAND["ink"], size=26, accent=BRAND["blue"])
    # nav
    nav = ["Dentistes", "Médecins", "Spécialités", "Établissements", "À propos"]
    fnt = font("regular", 13)
    nx = 240
    for item in nav:
        tw, _ = text_w(draw, item, fnt)
        draw.text((nx, 24), item, font=fnt, fill=BRAND["ink_soft"])
        nx += tw + 28
    # right side: search icon + lang + login
    # search
    sx = w - 380
    rounded(draw, [sx, 18, sx + 200, 46], 14, fill=BRAND["offwhite"], outline=BRAND["line"])
    draw.text((sx + 12, 24), "🔍", font=font("regular", 13), fill=BRAND["ink_soft"])
    draw.text((sx + 32, 25), "Rechercher un praticien…", font=fnt, fill=BRAND["ink_soft"])
    # lang selector
    lx = w - 160
    rounded(draw, [lx, 18, lx + 110, 46], 14, fill=BRAND["white"], outline=BRAND["line"])
    for i, code in enumerate(langs):
        tx = lx + 8 + i * 21
        is_active = code == active_lang
        if is_active:
            rounded(draw, [tx - 4, 22, tx + 18, 42], 9, fill=BRAND["blue"])
            draw.text((tx, 27), code, font=font("bold", 10), fill=BRAND["white"])
        else:
            draw.text((tx, 28), code, font=font("bold", 10), fill=BRAND["ink_soft"])
    # login
    lx2 = w - 40
    rounded(draw, [lx2 - 60, 18, lx2, 46], 14, fill=BRAND["blue"])
    f2 = font("bold", 12)
    tw, _ = text_w(draw, "Connexion", f2)
    draw.text((lx2 - 60 + (60 - tw) / 2, 24), "Connexion", font=f2, fill=BRAND["white"])
    return h

# ---------- FILTERS PANEL ----------
def filter_panel(draw, x, y, w, h):
    rounded(draw, [x, y, x + w, y + h], 14, fill=BRAND["white"], outline=BRAND["line"])
    f_t = font("bold", 14)
    draw.text((x + 18, y + 18), "Filtres", font=f_t, fill=BRAND["ink"])
    f_r = font("regular", 11)
    draw.text((x + w - 50, y + 22), "Réinitialiser", font=f_r, fill=BRAND["blue"])
    y2 = y + 52
    # Specialties
    draw.text((x + 18, y2), "Spécialité", font=font("bold", 12), fill=BRAND["ink"])
    specs = ["Orthodontie", "Chirurgie orale", "Implantologie", "Esthétique", "Endodontie", "Pédodontie", "Parodontologie"]
    y2 += 24
    for s in specs[:6]:
        rounded(draw, [x + 18, y2, x + 18 + 12, y2 + 12], 3, outline=BRAND["line"], width=1, fill=BRAND["white"])
        draw.text((x + 36, y2 - 1), s, font=f_r, fill=BRAND["ink"])
        y2 += 22
    # Langues
    y2 += 12
    draw.text((x + 18, y2), "Langue parlée", font=font("bold", 12), fill=BRAND["ink"])
    y2 += 24
    langs = ["FR", "AR", "EN", "RU", "ZH", "ES", "HI"]
    for i, code in enumerate(langs):
        col = i % 3
        row = i // 3
        cx = x + 18 + col * 70
        cy = y2 + row * 28
        active = code in ("FR", "AR", "EN")
        bg = BRAND["blue"] if active else BRAND["white"]
        fg = BRAND["white"] if active else BRAND["ink"]
        out = BRAND["blue"] if active else BRAND["line"]
        rounded(draw, [cx, cy, cx + 52, cy + 22], 11, fill=bg, outline=out)
        cw, ch = text_w(draw, code, font("bold", 10))
        draw.text((cx + (52 - cw) / 2, cy + 5), code, font=font("bold", 10), fill=fg)
    y2 += 70
    # Zone
    draw.text((x + 18, y2), "Zone", font=font("bold", 12), fill=BRAND["ink"])
    y2 += 24
    zones = ["Jumeirah", "Downtown", "Marina", "Deira", "Al Barsha", "JLT"]
    for z in zones:
        rounded(draw, [x + 18, y2, x + 18 + 12, y2 + 12], 3, outline=BRAND["line"], width=1, fill=BRAND["white"])
        draw.text((x + 36, y2 - 1), z, font=f_r, fill=BRAND["ink"])
        y2 += 22
    # Genre
    y2 += 12
    draw.text((x + 18, y2), "Genre", font=font("bold", 12), fill=BRAND["ink"])
    y2 += 24
    genres = ["Femme", "Homme", "Tous"]
    gx = x + 18
    for g in genres:
        active = g == "Tous"
        bg = BRAND["blue_light"] if active else BRAND["white"]
        out = BRAND["blue"] if active else BRAND["line"]
        fg = BRAND["blue"] if active else BRAND["ink_soft"]
        rounded(draw, [gx, y2, gx + 56, y2 + 24], 12, fill=bg, outline=out)
        cw, _ = text_w(draw, g, font("bold", 11))
        draw.text((gx + (56 - cw) / 2, y2 + 5), g, font=font("bold", 11), fill=fg)
        gx += 64
    # apply button
    y2 += 44
    rounded(draw, [x + 18, y2, x + w - 18, y2 + 38], 10, fill=BRAND["blue"])
    aw, _ = text_w(draw, "Appliquer les filtres", font("bold", 13))
    draw.text((x + 18 + ((w - 36) - aw) / 2, y2 + 11), "Appliquer les filtres", font=font("bold", 13), fill=BRAND["white"])
