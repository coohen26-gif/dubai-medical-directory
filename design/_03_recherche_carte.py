"""Recherche + carte mockup — 1440x1100."""
import sys, os, math, random
sys.path.insert(0, os.path.dirname(__file__))
from _dmd_brand import *

W, H = 1440, 1100
img, draw = new_canvas(W, H, BRAND["offwhite"])
header(draw, W, active_lang="FR")

# search bar at top below header
sy = 64 + 18
rounded(draw, [72, sy, W - 72, sy + 60], 30, fill=BRAND["white"], outline=BRAND["line"], width=2)
draw.text((92, sy + 18), "🔍", font=font("regular", 22), fill=BRAND["ink_soft"])
draw.text((130, sy + 20), "Dentiste francophone, Jumeirah, parle AR — 142 résultats", font=font("regular", 16), fill=BRAND["ink"])
# active filter chips
chips = ["📍 Jumeirah", "🇫🇷 Français", "🗣 العربية", "⭐ 4.5+", "✦ Premium"]
cx = 540
for c in chips:
    cw, _ = text_w(draw, c, font("bold", 12))
    rounded(draw, [cx, sy + 18, cx + cw + 24, sy + 44], 13, fill=BRAND["blue"], outline=BRAND["blue"])
    draw.text((cx + 12, sy + 22), c, font=font("bold", 12), fill=BRAND["white"])
    cx += cw + 32
# view toggle
rounded(draw, [W - 240, sy + 18, W - 156, sy + 44], 12, fill=BRAND["blue"], outline=BRAND["blue"])
draw.text((W - 224, sy + 22), "📋 Liste", font=font("bold", 12), fill=BRAND["white"])
rounded(draw, [W - 150, sy + 18, W - 72, sy + 44], 12, outline=BRAND["blue"], width=2)
draw.text((W - 134, sy + 22), "🗺 Carte", font=font("bold", 12), fill=BRAND["blue"])

# ===== Body: list (left) + map (right) =====
body_y = sy + 80
left_x, left_w = 72, 460
map_x, map_w = left_x + left_w + 24, W - 72 - (left_x + left_w + 24)
map_h = H - body_y - 24

# ---- map ----
# water (Persian Gulf)
draw.rectangle([map_x, body_y, map_x + map_w, body_y + map_h], fill=(196, 224, 240))
# land mass
rounded(draw, [map_x + 40, body_y + 20, map_x + map_w - 20, body_y + map_h - 20], 14, fill=(232, 244, 232))
# roads (fake grid)
random.seed(42)
for i in range(14):
    y_road = body_y + 60 + i * 60
    draw.line([(map_x + 40, y_road), (map_x + map_w - 20, y_road)], fill=(255, 255, 255), width=2)
for i in range(20):
    x_road = map_x + 80 + i * 50
    draw.line([(x_road, body_y + 20), (x_road, body_y + map_h - 20)], fill=(255, 255, 255), width=2)
# major roads (yellow)
for coords in [
    [(map_x + 100, body_y + 20), (map_x + 100, body_y + map_h - 20)],
    [(map_x + 40, body_y + 280), (map_x + map_w - 20, body_y + 280)],
    [(map_x + 40, body_y + 540), (map_x + map_w - 20, body_y + 540)],
]:
    draw.line(coords, fill=(245, 200, 80), width=4)
# district labels
labels = [("Jumeirah", map_x + 200, body_y + 380), ("Downtown", map_x + 480, body_y + 200),
          ("Deira", map_x + 800, body_y + 240), ("Marina", map_x + 250, body_y + 720),
          ("Bur Dubai", map_x + 600, body_y + 460)]
for name, lx, ly in labels:
    tw, _ = text_w(draw, name, font("bold", 13))
    draw.text((lx, ly), name, font=font("bold", 13), fill=(90, 99, 112))
# coastline
draw.line([(map_x + 40, body_y + 20), (map_x + 20, body_y + 100),
           (map_x + 30, body_y + 260), (map_x + 50, body_y + 420),
           (map_x + 20, body_y + 620), (map_x + 40, body_y + map_h - 20)],
          fill=(120, 170, 200), width=3)

# markers (positions chosen for visual spread)
markers = [
    (map_x + 220, body_y + 380, 1, "Dr. Layla M.", True),
    (map_x + 280, body_y + 420, 2, "Dr. Karim H.", True),
    (map_x + 460, body_y + 230, 3, "Dr. Sophie B.", True),
    (map_x + 480, body_y + 280, 4, "Dr. Omar S.", False),
    (map_x + 320, body_y + 720, 5, "Dr. Wei C.", True),
    (map_x + 580, body_y + 380, 6, "Dr. Youssef K.", True),
    (map_x + 700, body_y + 200, 7, "Dr. Lina F.", True),
    (map_x + 380, body_y + 540, 8, "Dr. Maria R.", False),
    (map_x + 750, body_y + 480, 9, "Dr. Hassan T.", True),
    (map_x + 180, body_y + 600, 10, "Dr. Anna P.", False),
    (map_x + 860, body_y + 600, 11, "Dr. Lina F.", True),
    (map_x + 90, body_y + 320, 12, "Dr. Layla M.", True),
]
for mx, my, idx, name, premium in markers:
    # pin
    color = BRAND["blue"] if premium else BRAND["ink_soft"]
    r = 14
    draw.ellipse([mx - r, my - r, mx + r, my + r], fill=color, outline=BRAND["white"], width=2)
    tw, th = text_w(draw, str(idx), font("bold", 11))
    draw.text((mx - tw / 2, my - th / 2 - 2), str(idx), font=font("bold", 11), fill=BRAND["white"])
    # shadow
    draw.ellipse([mx - 8, my + 12, mx + 8, my + 16], fill=(0, 0, 0, 30))

# selected card pop-up
pop_x, pop_y = map_x + 320, body_y + 280
rounded(draw, [pop_x, pop_y, pop_x + 240, pop_y + 90], 12, fill=BRAND["white"], outline=BRAND["blue"], width=2)
draw_avatar(draw, pop_x + 30, pop_y + 30, 16, "Dr. Layla Mansour")
draw.text((pop_x + 56, pop_y + 14), "Dr. Layla Mansour", font=font("bold", 13), fill=BRAND["ink"])
draw.text((pop_x + 56, pop_y + 32), "Orthodontie · 4.9 ★", font=font("regular", 11), fill=BRAND["ink_soft"])
rounded(draw, [pop_x + 56, pop_y + 52, pop_x + 180, pop_y + 74], 6, fill=BRAND["blue"])
ptw, _ = text_w(draw, "Voir la fiche →", font("bold", 11))
draw.text((pop_x + 56 + (124 - ptw) / 2, pop_y + 56), "Voir la fiche →", font=font("bold", 11), fill=BRAND["white"])

# map controls
ctrl_x = map_x + map_w - 60
rounded(draw, [ctrl_x, body_y + 20, ctrl_x + 44, body_y + 64], 8, fill=BRAND["white"], outline=BRAND["line"])
draw.text((ctrl_x + 18, body_y + 22), "+", font=font("bold", 18), fill=BRAND["ink"])
draw.line([(ctrl_x + 4, body_y + 44), (ctrl_x + 40, body_y + 44)], fill=BRAND["line"], width=1)
draw.text((ctrl_x + 17, body_y + 46), "−", font=font("bold", 18), fill=BRAND["ink"])
# search this area
rounded(draw, [ctrl_x, body_y + 80, ctrl_x + 44, body_y + 100], 6, fill=BRAND["blue"])
# zoom 4
draw.text((map_x + map_w - 80, body_y + map_h - 40), "© OpenStreetMap · DMD", font=font("regular", 10), fill=BRAND["ink_soft"])

# ---- LEFT list ----
# sort + count
draw.text((left_x, body_y), "142 dentistes à Dubai", font=font("bold", 18), fill=BRAND["ink"])
draw.text((left_x, body_y + 26), "Filtré par : Jumeirah · FR/AR/EN · 4.5+ ★", font=font("regular", 12), fill=BRAND["ink_soft"])
rounded(draw, [left_x + left_w - 130, body_y + 4, left_x + left_w, body_y + 30], 8, fill=BRAND["white"], outline=BRAND["line"])
draw.text((left_x + left_w - 120, body_y + 8), "Trier : Proximité ▼", font=font("regular", 12), fill=BRAND["ink"])

# list cards
list_y = body_y + 50
for i in range(5):
    d = DENTISTS[i]
    cy = list_y + i * 156
    rounded(draw, [left_x, cy, left_x + left_w, cy + 144], 12, fill=BRAND["white"], outline=BRAND["line"])
    if i == 0:
        rounded(draw, [left_x, cy, left_x + left_w, cy + 144], 12, outline=BRAND["blue"], width=2)
    draw_avatar(draw, left_x + 36, cy + 36, 22, d["name"])
    draw.text((left_x + 68, cy + 14), d["name"], font=font("bold", 14), fill=BRAND["ink"])
    draw.text((left_x + 68, cy + 32), d["spec"], font=font("regular", 11), fill=BRAND["ink_soft"])
    draw_rating(draw, left_x + 68, cy + 50, d["rating"], d["reviews"])
    # langs
    lx2 = left_x + 12
    ly2 = cy + 86
    for lg in d["langs"]:
        rounded(draw, [lx2, ly2, lx2 + 28, ly2 + 18], 9, fill=BRAND["blue_light"], outline=BRAND["blue"])
        cw, _ = text_w(draw, lg, font("bold", 9))
        draw.text((lx2 + (28 - cw) / 2, ly2 + 3), lg, font=font("bold", 9), fill=BRAND["blue"])
        lx2 += 34
    # distance
    draw.text((left_x + 68, cy + 110), "📍 1.2 km — Jumeirah Beach Rd", font=font("regular", 11), fill=BRAND["ink_soft"])
    # action
    rxa = left_x + left_w - 88
    rya = cy + 108
    rounded(draw, [rxa, rya, rxa + 76, rya + 28], 14, fill=BRAND["blue"])
    atw, _ = text_w(draw, "Réserver", font("bold", 11))
    draw.text((rxa + (76 - atw) / 2, rya + 7), "Réserver", font=font("bold", 11), fill=BRAND["white"])

# pagination
pg_y = list_y + 5 * 156 + 16
draw.text((left_x, pg_y), "‹", font=font("bold", 18), fill=BRAND["ink_soft"])
for i in range(5):
    px = left_x + 30 + i * 36
    active = i == 0
    rounded(draw, [px, pg_y - 2, px + 28, pg_y + 26], 6, fill=BRAND["blue"] if active else BRAND["white"], outline=BRAND["blue"] if active else BRAND["line"])
    pw, _ = text_w(draw, str(i + 1), font("bold", 12))
    draw.text((px + (28 - pw) / 2, pg_y + 4), str(i + 1), font=font("bold", 12), fill=BRAND["white"] if active else BRAND["ink"])
draw.text((left_x + 220, pg_y), "›", font=font("bold", 18), fill=BRAND["ink_soft"])

out = "/root/.openclaw/workspace/dubai-medical-directory/design/recherche_carte.png"
img.save(out, "PNG", optimize=True)
print(f"✅ {out}  ({os.path.getsize(out) // 1024} KB)")
