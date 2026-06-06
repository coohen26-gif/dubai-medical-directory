"""Profil premium mockup — 1440x1500."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from _dmd_brand import *

W, H = 1440, 1500
img, draw = new_canvas(W, H, BRAND["offwhite"])
header(draw, W)

# ===== HERO PROFILE =====
y = 64
# cover photo
draw.rectangle([0, y, W, y + 280], fill=(40, 95, 145))  # blue gradient-ish solid
# photo strip
ph_y = y + 200
for i, label in enumerate(["Cabinet 1","Cabinet 2","Cabinet 3","Cabinet 4"]):
    px = 72 + i * 220
    rounded(draw, [px, ph_y, px + 200, ph_y + 64], 8, fill=(60, 115, 165), outline=BRAND["white"], width=2)
    # little stethoscope / chair icon
    draw.text((px + 8, ph_y + 22), "🦷", font=font("regular", 22), fill=BRAND["white"])
    draw.text((px + 38, ph_y + 24), label, font=font("bold", 12), fill=BRAND["white"])
# profile photo big avatar
av_x, av_y = 110, y + 130
rounded(draw, [av_x, av_y, av_x + 160, av_y + 160], 80, fill=BRAND["white"], outline=BRAND["white"], width=6)
draw_avatar(draw, av_x + 80, av_y + 80, 64, "Dr. Layla Mansour")
# premium badge
rounded(draw, [av_x + 100, av_y + 110, av_x + 220, av_y + 140], 14, fill=BRAND["gold"])
b1, _ = text_w(draw, "✦ PROFIL PREMIUM", font("bold", 12))
draw.text((av_x + 100 + (120 - b1) / 2, av_y + 117), "✦ PROFIL PREMIUM", font=font("bold", 12), fill=BRAND["white"])

# name + spec
nm_y = av_y + 180
draw.text((av_x + 180, nm_y), "Dr. Layla Mansour", font=font("serif_b", 36), fill=BRAND["white"])
draw.text((av_x + 180, nm_y + 44), "Orthodontiste — Invisalign Diamond Provider", font=font("regular", 18), fill=(220, 235, 250))
# mini stats inline
draw_rating(draw, av_x + 180, nm_y + 76, 4.9, 312, color=(255, 215, 100))
draw.text((av_x + 180, nm_y + 110), "📍 Jumeirah Beach Road, Dubai  ·  🕐 Lun-Sam 9h-19h", font=font("regular", 14), fill=(220, 235, 250))

# action buttons (top right)
abx = W - 72
# WhatsApp
abx -= 150
rounded(draw, [abx, nm_y + 8, abx + 150, nm_y + 50], 22, fill=(37, 211, 102))
wtw, _ = text_w(draw, "💬 WhatsApp", font("bold", 14))
draw.text((abx + (150 - wtw) / 2, nm_y + 18), "💬 WhatsApp", font=font("bold", 14), fill=BRAND["white"])
# Réserver
abx -= 170
rounded(draw, [abx, nm_y + 8, abx + 158, nm_y + 50], 22, fill=BRAND["white"])
rtw, _ = text_w(draw, "📅 Réserver", font("bold", 14))
draw.text((abx + (158 - rtw) / 2, nm_y + 18), "📅 Réserver", font=font("bold", 14), fill=BRAND["blue"])
# Partager
abx -= 130
rounded(draw, [abx, nm_y + 8, abx + 118, nm_y + 50], 22, outline=BRAND["white"], width=2)
stw, _ = text_w(draw, "↗ Partager", font("bold", 14))
draw.text((abx + (118 - stw) / 2, nm_y + 18), "↗ Partager", font=font("bold", 14), fill=BRAND["white"])

# ===== TABS =====
tabs_y = y + 280 + 24
tabs = ["Présentation", "Photos & Vidéo", "Services & Tarifs", "Avis (312)", "Localisation", "Contact"]
tx = 72
for t in tabs:
    active = t == "Présentation"
    tw, _ = text_w(draw, t, font("bold", 14))
    draw.text((tx, tabs_y), t, font=font("bold", 14), fill=BRAND["blue"] if active else BRAND["ink_soft"])
    if active:
        hbar(draw, tx, tabs_y + 26, tw, 3, BRAND["blue"])
    tx += tw + 32
draw.line([(72, tabs_y + 38), (W - 72, tabs_y + 38)], fill=BRAND["line"], width=1)

# ===== BODY 2 columns =====
body_y = tabs_y + 60

# left col: bio + video + gallery
left_x, left_w = 72, 860
# bio card
rounded(draw, [left_x, body_y, left_x + left_w, body_y + 180], 14, fill=BRAND["white"], outline=BRAND["line"])
draw.text((left_x + 24, body_y + 20), "À propos", font=font("bold", 18), fill=BRAND["ink"])
# trilingual flag
fx = left_x + left_w - 24 - 130
for code, color in [("FR", BRAND["blue"]), ("AR", BRAND["green"]), ("EN", BRAND["ink"])]:
    rounded(draw, [fx, body_y + 22, fx + 38, body_y + 44], 6, fill=color)
    cw, _ = text_w(draw, code, font("bold", 12))
    draw.text((fx + (38 - cw) / 2, body_y + 28), code, font=font("bold", 12), fill=BRAND["white"])
    fx += 44

# bio text
bio_lines = [
    "Dr. Layla Mansour est orthodontiste certifiée, spécialisée en orthodontie",
    "invisible (Invisalign) et en traitements esthétiques pour adultes et",
    "adolescents. Diplômée de l'Université Paris VII et formée au King's College",
    "de Londres, elle pratique à Dubai depuis 2012 et parle couramment français,",
    "arabe et anglais.",
]
by = body_y + 60
for line in bio_lines:
    draw.text((left_x + 24, by), line, font=font("regular", 13), fill=BRAND["ink"])
    by += 20
# languages chips
lx = left_x + 24
ly = by + 14
for code in ["Français", "العربية", "English", "Русский"]:
    rounded(draw, [lx, ly, lx + 90, ly + 26], 13, fill=BRAND["blue_light"], outline=BRAND["blue"])
    cw, _ = text_w(draw, code, font("bold", 11))
    draw.text((lx + (90 - cw) / 2, ly + 6), code, font=font("bold", 11), fill=BRAND["blue"])
    lx += 100

# video block
vid_y = body_y + 200
rounded(draw, [left_x, vid_y, left_x + left_w, vid_y + 360], 14, fill=BRAND["white"], outline=BRAND["line"])
draw.text((left_x + 24, vid_y + 20), "Présentation vidéo (FR / AR / EN)", font=font("bold", 18), fill=BRAND["ink"])
# big video frame
vf_x, vf_y = left_x + 24, vid_y + 56
vf_w, vf_h = left_w - 48, 220
draw.rectangle([vf_x, vf_y, vf_x + vf_w, vf_y + vf_h], fill=(30, 50, 80))
# play button
pbx, pby = vf_x + vf_w // 2, vf_y + vf_h // 2
rounded(draw, [pbx - 28, pby - 28, pbx + 28, pby + 28], 28, fill=BRAND["white"])
draw.polygon([(pbx - 8, pby - 14), (pbx + 14, pby), (pbx - 8, pby + 14)], fill=BRAND["blue"])
# duration
draw.text((vf_x + 12, vf_y + vf_h - 24), "▶  2:14", font=font("bold", 12), fill=BRAND["white"])
# thumbnail overlay text
draw.text((vf_x + 12, vf_y + 12), "Dr. Layla Mansour — Bienvenue au cabinet", font=font("bold", 14), fill=BRAND["white"])

# photo gallery thumbs
gx = left_x + 24
gy = vf_y + vf_h + 16
for i in range(5):
    rounded(draw, [gx, gy, gx + 150, gy + 60], 6, fill=(70, 130, 180), outline=BRAND["line"], width=1)
    gx += 160

# right col: booking widget + services
rx = left_x + left_w + 24
rw = W - rx - 72

# BOOKING widget (sticky style)
rounded(draw, [rx, body_y, rx + rw, body_y + 420], 14, fill=BRAND["white"], outline=BRAND["line"])
draw.text((rx + 24, body_y + 20), "📅 Prendre rendez-vous", font=font("bold", 18), fill=BRAND["ink"])
draw.text((rx + 24, body_y + 50), "Choisissez une prestation et un créneau", font=font("regular", 12), fill=BRAND["ink_soft"])
# service selector
draw.text((rx + 24, body_y + 86), "Prestation", font=font("bold", 12), fill=BRAND["ink"])
rounded(draw, [rx + 24, body_y + 108, rx + rw - 24, body_y + 138], 8, fill=BRAND["offwhite"], outline=BRAND["line"])
draw.text((rx + 36, body_y + 116), "Consultation orthodontie (60 min)", font=font("regular", 13), fill=BRAND["ink"])
draw.text((rx + rw - 60, body_y + 116), "▼", font=font("bold", 13), fill=BRAND["ink_soft"])

# calendar mini
cal_y = body_y + 158
draw.text((rx + 24, cal_y), "Juin 2026", font=font("bold", 13), fill=BRAND["ink"])
draw.text((rx + rw - 90, cal_y), "‹  ›", font=font("bold", 16), fill=BRAND["ink_soft"])
days = ["L","M","M","J","V","S","D"]
for i, d in enumerate(days):
    draw.text((rx + 24 + i * 50, cal_y + 28), d, font=font("bold", 11), fill=BRAND["ink_soft"])
# 3 weeks
for w in range(3):
    for d in range(7):
        cx = rx + 24 + d * 50
        cy = cal_y + 52 + w * 36
        day = w * 7 + d + 1
        if day > 30: break
        avail = (day + w) % 4 != 0
        selected = (day == 12 and w == 1)
        if selected:
            rounded(draw, [cx, cy, cx + 36, cy + 30], 6, fill=BRAND["blue"])
            tw, th = text_w(draw, str(day), font("bold", 13))
            draw.text((cx + (36 - tw) / 2, cy + (30 - th) / 2 - 1), str(day), font=font("bold", 13), fill=BRAND["white"])
        elif avail:
            rounded(draw, [cx, cy, cx + 36, cy + 30], 6, fill=BRAND["blue_light"])
            tw, th = text_w(draw, str(day), font("bold", 13))
            draw.text((cx + (36 - tw) / 2, cy + (30 - th) / 2 - 1), str(day), font=font("bold", 13), fill=BRAND["blue"])
        else:
            tw, th = text_w(draw, str(day), font("regular", 13))
            draw.text((cx + (36 - tw) / 2, cy + (30 - th) / 2 - 1), str(day), font=font("regular", 13), fill=BRAND["ink_soft"])

# time slots
ts_y = cal_y + 170
draw.text((rx + 24, ts_y), "Créneaux disponibles", font=font("bold", 12), fill=BRAND["ink"])
slots = ["09:00", "10:30", "14:00", "15:30", "17:00"]
for i, s in enumerate(slots):
    col = i % 3
    row = i // 3
    sx = rx + 24 + col * 100
    sy = ts_y + 22 + row * 36
    sel = s == "14:00"
    rounded(draw, [sx, sy, sx + 88, sy + 30], 6, fill=BRAND["blue"] if sel else BRAND["white"], outline=BRAND["blue"] if sel else BRAND["line"])
    sw, sh = text_w(draw, s, font("bold", 12)), 16
    fc = BRAND["white"] if sel else BRAND["ink"]
    sw2, sh2 = text_w(draw, s, font("bold", 12))
    draw.text((sx + (88 - sw2) / 2, sy + 6), s, font=font("bold", 12), fill=fc)

# CTA
cta_y = ts_y + 110
rounded(draw, [rx + 24, cta_y, rx + rw - 24, cta_y + 50], 25, fill=BRAND["blue"])
b1w, _ = text_w(draw, "Confirmer le RDV — 12 juin, 14:00", font("bold", 15))
draw.text((rx + 24 + ((rw - 48) - b1w) / 2, cta_y + 16), "Confirmer le RDV — 12 juin, 14:00", font=font("bold", 15), fill=BRAND["white"])

# small contact card
sc_y = body_y + 440
rounded(draw, [rx, sc_y, rx + rw, sc_y + 130], 14, fill=BRAND["offwhite"], outline=BRAND["line"])
draw.text((rx + 20, sc_y + 18), "📞 Contact direct", font=font("bold", 14), fill=BRAND["ink"])
draw.text((rx + 20, sc_y + 46), "+971 4 123 45 67", font=font("regular", 13), fill=BRAND["ink_soft"])
draw.text((rx + 20, sc_y + 70), "📧 contact@drlayla-dubai.ae", font=font("regular", 13), fill=BRAND["ink_soft"])
draw.text((rx + 20, sc_y + 94), "🌐 drlayla-mansour.ae", font=font("regular", 13), fill=BRAND["ink_soft"])

out = "/root/.openclaw/workspace/dubai-medical-directory/design/profil_premium.png"
img.save(out, "PNG", optimize=True)
print(f"✅ {out}  ({os.path.getsize(out) // 1024} KB)")
