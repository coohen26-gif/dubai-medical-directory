"""Homepage FR mockup — 1440x2400 (full long scroll)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from _dmd_brand import *

W, H = 1440, 2400
img, draw = new_canvas(W, H, BRAND["offwhite"])

# ===== Header =====
header_h = header(draw, W, langs=("FR","AR","EN","RU","ZH"), active_lang="FR")

# ===== HERO =====
hero_y = header_h
hero_h = 380
draw.rectangle([0, hero_y, W, hero_y + hero_h], fill=BRAND["white"])
# decorative shapes
draw.rectangle([0, hero_y + hero_h - 12, W, hero_y + hero_h], fill=BRAND["blue"])
# subtle medical cross pattern (light)
for i in range(0, W, 80):
    for j in range(hero_y, hero_y + hero_h, 80):
        if (i // 80 + j // 80) % 3 == 0:
            cx, cy = i + 40, j + 40
            cross_color = (235, 244, 251)
            vbar(draw, cx - 2, cy - 10, 4, 20, cross_color)
            hbar(draw, cx - 10, cy - 2, 20, 4, cross_color)
# title
f_h1 = font("serif_b", 44)
f_sub = font("regular", 18)
f_stat = font("bold", 32)
f_stat_l = font("regular", 12)
draw.text((72, hero_y + 60), "Trouvez votre praticien de santé à Dubai", font=f_h1, fill=BRAND["ink"])
draw.text((72, hero_y + 120), "L'annuaire trilingue FR/AR/EN des 99 520+ professionnels de santé", font=f_sub, fill=BRAND["ink_soft"])
draw.text((72, hero_y + 150), "DHA-licensés. Vérifiés. Réservables en ligne.", font=f_sub, fill=BRAND["ink_soft"])
# big search
sx, sy = 72, hero_y + 210
rounded(draw, [sx, sy, sx + 720, sy + 60], 30, fill=BRAND["white"], outline=BRAND["line"], width=2)
draw.text((sx + 24, sy + 18), "🔍", font=font("regular", 22), fill=BRAND["ink_soft"])
draw.text((sx + 60, sy + 20), "Spécialité, nom, zone, langue parlée…", font=font("regular", 16), fill=BRAND["ink_soft"])
# button inside search
btn_x = sx + 720 - 150
rounded(draw, [btn_x, sy + 6, btn_x + 140, sy + 54], 26, fill=BRAND["blue"])
btw, _ = text_w(draw, "Rechercher", font("bold", 16))
draw.text((btn_x + (140 - btw) / 2, sy + 17), "Rechercher", font=font("bold", 16), fill=BRAND["white"])
# quick tags
qtags = ["Dentiste francophone", "Pédiatre arabophone", "Gynécologue Jumeirah", "Cardiologue urgence"]
qtx = sx
qty = sy + 80
for t in qtags:
    tw, _ = text_w(draw, t, font("regular", 12))
    rounded(draw, [qtx, qty, qtx + tw + 20, qty + 26], 13, fill=BRAND["offwhite"], outline=BRAND["line"])
    draw.text((qtx + 10, qty + 6), t, font=font("regular", 12), fill=BRAND["ink_soft"])
    qtx += tw + 32
# right-side hero illustration block
hero_card_x = 920
hero_card_y = hero_y + 60
rounded(draw, [hero_card_x, hero_card_y, W - 72, hero_y + 320], 20, fill=BRAND["blue_light"], outline=BRAND["blue"])
draw.text((hero_card_x + 30, hero_card_y + 24), "📊 Le marché en chiffres", font=font("bold", 16), fill=BRAND["blue_dark"])
stats = [("99 520+", "Pros DHA-licensés"), ("7 713", "Dentistes"), ("5 800", "Établissements"), ("100%", "Vérifiés")]
sx2 = hero_card_x + 20
sy2 = hero_card_y + 70
for i, (n, l) in enumerate(stats):
    col = i % 2
    row = i // 2
    cx = sx2 + col * 220
    cy = sy2 + row * 80
    draw.text((cx, cy), n, font=f_stat, fill=BRAND["blue"])
    draw.text((cx, cy + 38), l, font=f_stat_l, fill=BRAND["ink_soft"])

# ===== TRUST BAR =====
trust_y = hero_y + hero_h + 30
trust_h = 70
rounded(draw, [72, trust_y, W - 72, trust_y + trust_h], 14, fill=BRAND["white"], outline=BRAND["line"])
draw.text((100, trust_y + 14), "PARTENAIRES DE CONFIANCE", font=font("bold", 11), fill=BRAND["ink_soft"])
logos = ["DHA", "Dubai Health", "Cleveland Clinic", "Mediclinic", "Aster", "NMC", "Emirates Hospital"]
lx = 100
ly = trust_y + 38
for L in logos:
    lw, _ = text_w(draw, L, font("bold", 16))
    draw.text((lx, ly), L, font=font("bold", 16), fill=BRAND["ink_soft"])
    lx += lw + 50

# ===== MAIN GRID =====
main_y = trust_y + trust_h + 30
left_w = 280
right_x = 72 + left_w + 24
right_w = W - right_x - 72

# Filter panel
filter_panel(draw, 72, main_y, left_w, 720)

# Right column
draw.text((right_x, main_y), "10 dentistes vedettes", font=font("bold", 22), fill=BRAND["ink"])
draw.text((right_x + 220, main_y + 8), "triés par proximité et note", font=font("regular", 13), fill=BRAND["ink_soft"])
# sort
sx3 = right_x + right_w - 200
rounded(draw, [sx3, main_y - 4, sx3 + 200, main_y + 30], 8, fill=BRAND["white"], outline=BRAND["line"])
draw.text((sx3 + 14, main_y + 6), "Trier : ⭐ Meilleures notes", font=font("regular", 12), fill=BRAND["ink"])

# 5 cols x 2 rows
col_n = 5
card_w = (right_w - (col_n - 1) * 16) // col_n  # = 211
card_h = 230
gap = 16
y_off = main_y + 56
for idx, d in enumerate(DENTISTS):
    col = idx % col_n
    row = idx // col_n
    cx = right_x + col * (card_w + gap)
    cy = y_off + row * (card_h + gap)
    draw_dentist_card(draw, cx, cy, card_w, card_h, d)
    # CTA at bottom
    cta_y = cy + card_h - 18
    cta_h = 30
    rounded(draw, [cx + 12, cta_y, cx + card_w - 12, cta_y + cta_h], 8, fill=BRAND["blue"] if d["premium"] else BRAND["offwhite"], outline=BRAND["blue"] if d["premium"] else BRAND["line"])
    cta_txt = "Voir la fiche →"
    cw, _ = text_w(draw, cta_txt, font("bold", 12))
    fc = BRAND["white"] if d["premium"] else BRAND["blue"]
    draw.text((cx + (card_w - cw) / 2, cta_y + 8), cta_txt, font=font("bold", 12), fill=fc)

# ===== CTA BANNER =====
banner_y = y_off + 2 * (card_h + gap) + 30
rounded(draw, [72, banner_y, W - 72, banner_y + 160], 18, fill=BRAND["blue"])
# decorative
draw.rectangle([W - 320, banner_y, W - 72, banner_y + 160], fill=BRAND["blue_dark"])
draw.text((110, banner_y + 36), "Vous êtes praticien de santé à Dubai ?", font=font("serif_b", 30), fill=BRAND["white"])
draw.text((110, banner_y + 78), "Boostez votre visibilité avec une fiche premium (200 AED/mois).", font=font("regular", 16), fill=BRAND["white"])
rounded(draw, [110, banner_y + 112, 360, banner_y + 144], 16, fill=BRAND["white"])
b1w, _ = text_w(draw, "Créer ma fiche premium →", font("bold", 14))
draw.text((110 + (250 - b1w) / 2, banner_y + 119), "Créer ma fiche premium →", font=font("bold", 14), fill=BRAND["blue"])
rounded(draw, [380, banner_y + 112, 560, banner_y + 144], 16, outline=BRAND["white"], width=2)
b2w, _ = text_w(draw, "En savoir plus", font("bold", 14))
draw.text((380 + (180 - b2w) / 2, banner_y + 119), "En savoir plus", font=font("bold", 14), fill=BRAND["white"])
# right side: mockup profile preview
draw.rectangle([W - 300, banner_y + 20, W - 92, banner_y + 140], fill=BRAND["white"])
rounded(draw, [W - 286, banner_y + 26, W - 286 + 36, banner_y + 26 + 36], 18, fill=BRAND["gold"])
draw.text((W - 280, banner_y + 70), "Dr. Layla Mansour", font=font("bold", 13), fill=BRAND["ink"])
draw.text((W - 280, banner_y + 88), "Orthodontie · Jumeirah", font=font("regular", 10), fill=BRAND["ink_soft"])
draw.text((W - 280, banner_y + 104), "⭐ 4.9 (312 avis)", font=font("regular", 10), fill=BRAND["ink_soft"])
rounded(draw, [W - 280, banner_y + 120, W - 130, banner_y + 134], 6, fill=BRAND["blue"])
b3w, _ = text_w(draw, "Réserver", font("bold", 10))
draw.text((W - 280 + (150 - b3w) / 2, banner_y + 122), "Réserver", font=font("bold", 10), fill=BRAND["white"])

# ===== FOOTER =====
foot_y = banner_y + 200
draw.rectangle([0, foot_y, W, H], fill=BRAND["ink"])
# 4 columns
cols = [
    ("DMD Dubai", ["À propos", "Notre mission", "Équipe", "Carrières", "Presse"]),
    ("Services",  ["Annuaire pro", "Fiche premium", "Booking", "API Pro", "Partenaires"]),
    ("Ressources",["Blog santé", "Glossaire médical", "FAQ", "Contact", "Statuts"]),
    ("Légal",     ["CGU", "CGV", "Confidentialité", "Cookies", "DHA Disclaimer"]),
]
cw = (W - 144) // 4
for i, (h, items) in enumerate(cols):
    cx = 72 + i * cw
    draw.text((cx, foot_y + 50), h, font=font("bold", 14), fill=BRAND["white"])
    iy = foot_y + 80
    for it in items:
        draw.text((cx, iy), it, font=font("regular", 12), fill=(180, 195, 215))
        iy += 22
# bottom bar
draw.line([(72, H - 60), (W - 72, H - 60)], fill=(60, 80, 100), width=1)
draw.text((72, H - 38), "© 2026 DMD Dubai — Dubai Medical Directory. Tous droits réservés.", font=font("regular", 11), fill=(140, 160, 185))
draw.text((W - 240, H - 38), "Fait avec ❤️ à Dubai · v0.1.0", font=font("regular", 11), fill=(140, 160, 185))

out = "/root/.openclaw/workspace/dubai-medical-directory/design/homepage_FR.png"
img.save(out, "PNG", optimize=True)
print(f"✅ {out}  ({os.path.getsize(out) // 1024} KB)")
