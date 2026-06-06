"""Mobile mockup — 390x1800 (single-column responsive)."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from _dmd_brand import *

W, H = 390, 1800
img, draw = new_canvas(W, H, BRAND["offwhite"])

# ===== Status bar (iOS style) =====
hbar(draw, 0, 0, W, 32, BRAND["ink"])
draw.text((20, 8), "9:41", font=font("bold", 13), fill=BRAND["white"])
draw.text((W - 80, 8), "📶  🔋", font=font("regular", 13), fill=BRAND["white"])

# ===== Mobile header (sticky) =====
mhy = 32
rounded(draw, [0, mhy, W, mhy + 64], 0, fill=BRAND["white"])
draw.line([(0, mhy + 64), (W, mhy + 64)], fill=BRAND["line"], width=1)
# hamburger
draw.line([(20, mhy + 22), (44, mhy + 22)], fill=BRAND["ink"], width=2)
draw.line([(20, mhy + 32), (44, mhy + 32)], fill=BRAND["ink"], width=2)
draw.line([(20, mhy + 42), (44, mhy + 42)], fill=BRAND["ink"], width=2)
# centered logo
lx, ly = W // 2 - 70, mhy + 18
logo_wordmark(draw, lx, ly, color=BRAND["ink"], size=22, accent=BRAND["blue"])
# lang icon (top right)
rounded(draw, [W - 56, mhy + 18, W - 20, mhy + 46], 14, fill=BRAND["offwhite"], outline=BRAND["line"])
draw.text((W - 48, mhy + 22), "FR", font=font("bold", 12), fill=BRAND["blue"])

# ===== Search bar =====
sy = mhy + 80
rounded(draw, [16, sy, W - 16, sy + 48], 24, fill=BRAND["white"], outline=BRAND["line"])
draw.text((28, sy + 14), "🔍", font=font("regular", 16), fill=BRAND["ink_soft"])
draw.text((54, sy + 16), "Dentiste, spécialité, zone…", font=font("regular", 13), fill=BRAND["ink_soft"])
# filter icon
rounded(draw, [W - 56, sy + 8, W - 24, sy + 40], 12, fill=BRAND["blue"])
draw.text((W - 48, sy + 12), "⚙", font=font("bold", 16), fill=BRAND["white"])

# ===== Filter chips horizontal scroll =====
chy = sy + 64
chips = ["📍 Jumeirah", "🇫🇷 FR", "🗣 AR", "⭐ 4.5+", "✦ Premium", "🚨 Urgence"]
cx = 16
for c in chips:
    cw, _ = text_w(draw, c, font("bold", 12))
    rounded(draw, [cx, chy, cx + cw + 24, chy + 30], 15, fill=BRAND["blue"] if c.startswith("📍") else BRAND["white"], outline=BRAND["blue"] if c.startswith("📍") else BRAND["line"])
    fc = BRAND["white"] if c.startswith("📍") else BRAND["ink"]
    draw.text((cx + 12, chy + 8), c, font=font("bold", 12), fill=fc)
    cx += cw + 32

# ===== Section title =====
ty = chy + 56
draw.text((16, ty), "10 dentistes vedettes", font=font("bold", 18), fill=BRAND["ink"])
draw.text((16, ty + 26), "Triés par proximité", font=font("regular", 12), fill=BRAND["ink_soft"])
# sort
rounded(draw, [W - 110, ty + 4, W - 16, ty + 32], 8, fill=BRAND["white"], outline=BRAND["line"])
draw.text((W - 100, ty + 10), "Trier : ⭐", font=font("regular", 11), fill=BRAND["ink"])

# ===== Cards (full width stacked) =====
ly2 = ty + 60
for i, d in enumerate(DENTISTS):
    cy = ly2 + i * 240
    rounded(draw, [16, cy, W - 16, cy + 220], 14, fill=BRAND["white"], outline=BRAND["line"])
    # premium ribbon
    if d["premium"]:
        rounded(draw, [W - 86, cy + 10, W - 24, cy + 30], 6, fill=BRAND["gold"])
        pwt, _ = text_w(draw, "PREMIUM", font("bold", 9))
        draw.text((W - 24 - pwt - 6, cy + 14), "PREMIUM", font=font("bold", 9), fill=BRAND["white"])
    # avatar
    draw_avatar(draw, 50, cy + 38, 24, d["name"])
    # name
    draw.text((86, cy + 22), d["name"], font=font("bold", 14), fill=BRAND["ink"])
    draw.text((86, cy + 42), d["spec"], font=font("regular", 12), fill=BRAND["ink_soft"])
    # rating
    draw_rating(draw, 86, cy + 62, d["rating"], d["reviews"])
    # divider
    draw.line([(28, cy + 96), (W - 28, cy + 96)], fill=BRAND["line"], width=1)
    # info row
    draw.text((28, cy + 108), f"📍 {d['zone']}", font=font("regular", 11), fill=BRAND["ink_soft"])
    # langs chips
    lx = 28
    ly3 = cy + 134
    for lg in d["langs"]:
        rounded(draw, [lx, ly3, lx + 32, ly3 + 22], 11, fill=BRAND["blue_light"], outline=BRAND["blue"])
        cw, _ = text_w(draw, lg, font("bold", 10))
        draw.text((lx + (32 - cw) / 2, ly3 + 5), lg, font=font("bold", 10), fill=BRAND["blue"])
        lx += 38
    # CTAs
    cta_y = cy + 168
    rounded(draw, [28, cta_y, (W - 28) // 2 - 4, cta_y + 38], 19, fill=BRAND["blue"])
    ctw, _ = text_w(draw, "📅 Réserver", font("bold", 12))
    draw.text((28 + (((W - 28) // 2 - 4) - 28 - ctw) / 2 + 28, cta_y + 11), "📅 Réserver", font=font("bold", 12), fill=BRAND["white"])
    rounded(draw, [(W - 28) // 2 + 4, cta_y, W - 28, cta_y + 38], 19, outline=BRAND["blue"], width=2)
    ctw2, _ = text_w(draw, "💬 WhatsApp", font("bold", 12))
    right_cx = (W - 28) // 2 + 4
    right_w = W - 28 - right_cx
    draw.text((right_cx + (right_w - ctw2) / 2, cta_y + 11), "💬 WhatsApp", font=font("bold", 12), fill=BRAND["blue"])

# ===== Bottom tab bar =====
tb_y = H - 72
draw.rectangle([0, tb_y, W, H], fill=BRAND["white"])
draw.line([(0, tb_y), (W, tb_y)], fill=BRAND["line"], width=1)
tabs = [("🏠", "Accueil", True), ("🔍", "Recherche", False),
        ("📅", "RDV", False), ("💬", "Messages", False), ("👤", "Profil", False)]
tw_each = W // 5
for i, (icon, lbl, active) in enumerate(tabs):
    tx = i * tw_each + tw_each // 2
    draw.text((tx - 9, tb_y + 10), icon, font=font("regular", 20), fill=BRAND["blue"] if active else BRAND["ink_soft"])
    draw.text((tx - text_w(draw, lbl, font("bold", 9))[0] // 2, tb_y + 42), lbl, font=font("bold", 9), fill=BRAND["blue"] if active else BRAND["ink_soft"])
# home indicator
hbar(draw, W // 2 - 60, H - 8, 120, 4, BRAND["ink"])

out = "/root/.openclaw/workspace/dubai-medical-directory/design/mobile.png"
img.save(out, "PNG", optimize=True)
print(f"✅ {out}  ({os.path.getsize(out) // 1024} KB)")
