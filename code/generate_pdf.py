"""
Génération maquette PDF DMD Dubai - Direct, sans bullshit
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.colors import HexColor, white, black
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import os

# Couleurs DMD
PRIMARY = HexColor("#0A2540")
ACCENT = HexColor("#00D4A8")
ACCENT_2 = HexColor("#0066FF")
GOLD = HexColor("#FFB800")
MUTED = HexColor("#64748B")
BG = HexColor("#F7FAFC")
BORDER = HexColor("#E2E8F0")
GREEN_50 = HexColor("#10B981")

OUTPUT = "/root/.openclaw/workspace/dubai-medical-directory/docs/Maquette-DMD-Dubai-2026.pdf"
os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

c = canvas.Canvas(OUTPUT, pagesize=A4)
W, H = A4

def header(c, title, page_num):
    c.setFillColor(PRIMARY)
    c.rect(0, H-2*cm, W, 2*cm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(2*cm, H-1.3*cm, "DMD Dubai")
    c.setFont("Helvetica", 9)
    c.drawString(2*cm, H-1.7*cm, "Dubai Medical Directory • Trilingue FR/AR/EN")
    c.setFont("Helvetica-Bold", 11)
    c.drawRightString(W-2*cm, H-1.3*cm, title)
    c.setFont("Helvetica", 8)
    c.drawRightString(W-2*cm, H-1.7*cm, f"Page {page_num}")
    c.setFillColor(ACCENT)
    c.rect(0, H-2.05*cm, W, 0.05*cm, fill=1, stroke=0)

def footer(c, page_num):
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 7)
    c.drawString(2*cm, 1*cm, "© 2026 DMD Dubai • Données DHA Sheryan Registry (publiques) • Conforme PDPL UAE")
    c.drawRightString(W-2*cm, 1*cm, f"{page_num} / 12")

def title(c, text, y, size=24, color=PRIMARY):
    c.setFillColor(color)
    c.setFont("Helvetica-Bold", size)
    c.drawString(2*cm, y, text)
    return y - 1*cm

def text(c, txt, y, size=10, color=black, max_w=None):
    c.setFillColor(color)
    c.setFont("Helvetica", size)
    if max_w:
        from reportlab.lib.utils import simpleSplit
        lines = simpleSplit(txt, "Helvetica", size, max_w)
        for line in lines:
            c.drawString(2*cm, y, line)
            y -= size*1.3/10*cm + 0.1*cm
        return y
    c.drawString(2*cm, y, txt)
    return y - size*1.3/10*cm + 0.2*cm

def stat_card(c, x, y, number, label, w=5*cm, h=3*cm):
    c.setFillColor(white)
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.5)
    c.roundRect(x, y-h, w, h, 8, fill=1, stroke=1)
    c.setFillColor(ACCENT_2)
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(x+w/2, y-1.3*cm, number)
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 8)
    c.drawCentredString(x+w/2, y-2.1*cm, label)

def bar(c, x, y, w, h, pct, color=ACCENT):
    c.setFillColor(BG)
    c.roundRect(x, y, w, h, 3, fill=1, stroke=0)
    c.setFillColor(color)
    c.roundRect(x, y, w*pct/100, h, 3, fill=1, stroke=0)

# ========== PAGE 1: COUVERTURE ==========
c.setFillColor(PRIMARY)
c.rect(0, 0, W, H, fill=1, stroke=0)
# Bandeau accent
c.setFillColor(ACCENT)
c.rect(0, H-8*cm, W, 1*cm, fill=1, stroke=0)
c.setFillColor(GOLD)
c.rect(0, H-8.5*cm, W, 0.3*cm, fill=1, stroke=0)

# Logo
c.setFillColor(white)
c.setFont("Helvetica-Bold", 56)
c.drawString(2*cm, H-6*cm, "DMD")
c.setFillColor(ACCENT)
c.drawString(5.5*cm, H-6*cm, "Dubai")
c.setFillColor(GOLD)
c.setFont("Helvetica-Bold", 14)
c.drawString(2*cm, H-6.8*cm, "Dubai Medical Directory")

# Titre principal
c.setFillColor(white)
c.setFont("Helvetica-Bold", 28)
c.drawString(2*cm, H-12*cm, "La plateforme médicale")
c.drawString(2*cm, H-12.9*cm, "#1 aux Émirats")

# Sous-titre
c.setFillColor(ACCENT)
c.setFont("Helvetica-Bold", 14)
c.drawString(2*cm, H-14.5*cm, "Trilingue FR/AR/EN — Russe — Chinois")
c.setFont("Helvetica", 11)
c.setFillColor(white)
c.drawString(2*cm, H-15.5*cm, "99 520 professionnels DHA-licensés référencés")
c.drawString(2*cm, H-16.1*cm, "5 800 établissements de santé")
c.drawString(2*cm, H-16.7*cm, "Croissance +8,6% YoY")

# Footer
c.setFillColor(GOLD)
c.setFont("Helvetica-Bold", 12)
c.drawString(2*cm, 3*cm, "Maquette de présentation — Juin 2026")
c.setFillColor(white)
c.setFont("Helvetica", 9)
c.drawString(2*cm, 2.2*cm, "Document confidentiel — W / DMD Dubai")
c.drawString(2*cm, 1.6*cm, "Contact : w@dmd.ae")
c.showPage()

# ========== PAGE 2: LE MARCHÉ ==========
header(c, "Le marché", 2)
y = title(c, "Le marché de la santé à Dubai", H-4*cm, 22)

y -= 0.5*cm
y = text(c, "Le marché de la santé à Dubai est en forte croissance, validé par", y, 11, MUTED, W-4*cm)
y = text(c, "les données officielles du Dubai Health Authority (DHA).", y, 11, MUTED, W-4*cm)

# 4 stats cards
y -= 1*cm
stat_card(c, 2*cm, y, "99 520", "Pros DHA-licensés")
stat_card(c, 7.5*cm, y, "7 713", "Dentistes")
stat_card(c, 13*cm, y, "24 186", "Médecins")
y -= 4*cm

stat_card(c, 2*cm, y, "5 800", "Établissements santé")
stat_card(c, 7.5*cm, y, "+8,6%", "Croissance YoY")
stat_card(c, 13*cm, y, "5", "Langues cibles")

y -= 3*cm
y = text(c, "Chiffres clés :", y, 12, PRIMARY)
y -= 0.3*cm
y = text(c, "• Population Dubai : 3,66 millions d'habitants (200+ nationalités)", y, 10, MUTED, W-4*cm)
y = text(c, "• Croissance des établissements de santé : +8,6% YoY en 2025", y, 10, MUTED, W-4*cm)
y = text(c, "• Marché UAE total : 25-28 Md$ en 2024, projection 50 Md$ d'ici 2029", y, 10, MUTED, W-4*cm)
y = text(c, "• CAGR 2026-2030 : 7,5-9,5% (sources : Mordor, Grand View Research)", y, 10, MUTED, W-4*cm)
y = text(c, "• Ratio privé/public : 88% privé / 12% public", y, 10, MUTED, W-4*cm)

y -= 1*cm
c.setFillColor(BG)
c.roundRect(2*cm, y-2*cm, W-4*cm, 2.5*cm, 8, fill=1, stroke=0)
c.setFillColor(PRIMARY)
c.setFont("Helvetica-Bold", 12)
c.drawString(2.5*cm, y-0.8*cm, "Marché adressable (TAM)")
c.setFillColor(black)
c.setFont("Helvetica", 10)
c.drawString(2.5*cm, y-1.4*cm, "87 500 professionnels de santé privés DHA-licensés")
c.drawString(2.5*cm, y-1.9*cm, "= le marché que DMD Dubai peut monétiser")

footer(c, 2)
c.showPage()

# ========== PAGE 3: LE PROBLÈME ==========
header(c, "Le problème", 3)
y = title(c, "Le problème : 78,9% des praticiens", H-4*cm, 20)
y = text(c, "sont invisibles en ligne", y, 20, PRIMARY)
y -= 0.5*cm
y = text(c, "Audit indépendant réalisé sur 142 praticiens DHA à Dubai, juin 2026.", y, 10, MUTED, W-4*cm)

# Barres
y -= 1.5*cm
bars = [
    ("Aucun site web personnel", 78.9, ACCENT),
    ("Sur 0 annuaire digital (ni Practo, ni Zavis)", 40.1, ACCENT_2),
    ("Page clinique seule (pas de profil perso)", 28.2, GOLD),
    ("Prospects chauds (D+E+F)", 80.9, GREEN_50),
]
for label, pct, color in bars:
    c.setFillColor(black)
    c.setFont("Helvetica", 9)
    c.drawString(2*cm, y, label)
    c.setFont("Helvetica-Bold", 9)
    c.drawRightString(W-2*cm, y, f"{pct}%")
    bar(c, 2*cm, y-0.5*cm, W-4*cm, 0.3*cm, pct, color)
    y -= 1.2*cm

y -= 1*cm
c.setFillColor(PRIMARY)
c.setFont("Helvetica-Bold", 14)
c.drawString(2*cm, y, "Extrapolation à Dubai (99 520 praticiens)")
y -= 1*cm
c.setFillColor(ACCENT)
c.setFont("Helvetica-Bold", 28)
c.drawString(2*cm, y, "~78 500 praticiens")
c.setFillColor(black)
c.setFont("Helvetica", 11)
c.drawString(2*cm, y-0.8*cm, "n'ont pas de site web personnel")
c.drawString(2*cm, y-1.4*cm, "→ Océan bleu pour DMD Dubai")

y -= 3*cm
c.setFillColor(BG)
c.roundRect(2*cm, y-2*cm, W-4*cm, 2*cm, 8, fill=1, stroke=0)
c.setFillColor(PRIMARY)
c.setFont("Helvetica-Bold", 12)
c.drawString(2.5*cm, y-0.8*cm, "Conclusion")
c.setFillColor(black)
c.setFont("Helvetica", 10)
c.drawString(2.5*cm, y-1.4*cm, "78% des praticiens à Dubai n'ont aucune présence digitale structurée.")
c.drawString(2.5*cm, y-1.9*cm, "C'est un océan bleu non-addressé par les concurrents.")

footer(c, 3)
c.showPage()

# ========== PAGE 4: LA SOLUTION ==========
header(c, "La solution", 4)
y = title(c, "La solution : DMD Dubai", H-4*cm, 22)
y -= 0.3*cm
y = text(c, "La première plateforme médicale trilingue des Émirats", y, 12, ACCENT, W-4*cm)
y -= 1*cm

# 3 piliers
pillars = [
    ("🌍", "Trilingue FR/AR/EN", "0 concurrent ne fait de trilingue aux UAE.\nSeul angle défensif sur ce marché.\nSEO vacant en français."),
    ("⭐", "Profil enrichi premium", "Vidéo 60 sec + photos HD du cabinet\n+ bio multilingue + lien site externe\n+ WhatsApp direct (200 AED/mois)."),
    ("📅", "Booking Doctolib-like", "Prise de RDV 24/7, dispos en temps réel\n+ rappel SMS J-1 + pré-paiement\n+ commission 10% par RDV réservé."),
]
for emoji, title_, desc in pillars:
    c.setFillColor(PRIMARY)
    c.setFont("Helvetica-Bold", 32)
    c.drawString(2*cm, y, emoji)
    c.setFillColor(PRIMARY)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(4*cm, y, title_)
    c.setFillColor(black)
    c.setFont("Helvetica", 9)
    from reportlab.lib.utils import simpleSplit
    for line in simpleSplit(desc, "Helvetica", 9, W-6*cm):
        c.drawString(4*cm, y-0.7*cm, line)
        y -= 0.5*cm
    y -= 1*cm

footer(c, 4)
c.showPage()

# ========== PAGE 5: HOMEPAGE ==========
header(c, "Mockup homepage", 5)
y = title(c, "Mockup — Page d'accueil (FR)", H-4*cm, 18)
y = text(c, "Sélecteur 5 langues, recherche, filtres, stats, grille de fiches", y, 10, MUTED, W-4*cm)

# Mockup simplifié de la homepage
y -= 1*cm
# Hero simulation
c.setFillColor(ACCENT_2)
c.roundRect(2*cm, y-4*cm, W-4*cm, 4*cm, 10, fill=1, stroke=0)
c.setFillColor(white)
c.setFont("Helvetica-Bold", 18)
c.drawCentredString(W/2, y-1.2*cm, "Trouvez votre médecin à Dubai")
c.setFont("Helvetica", 10)
c.drawCentredString(W/2, y-1.9*cm, "99 520 professionnels DHA-licensés • 5 langues")
# Search bar
c.setFillColor(white)
c.roundRect(3*cm, y-3.2*cm, W-6*cm, 0.8*cm, 8, fill=1, stroke=0)
c.setFillColor(MUTED)
c.setFont("Helvetica", 10)
c.drawString(3.5*cm, y-2.9*cm, "🔍 Recherchez un médecin, dentiste, spécialité...")
c.setFillColor(ACCENT)
c.roundRect(W-5*cm, y-3.2*cm, 2*cm, 0.8*cm, 8, fill=1, stroke=0)
c.setFillColor(PRIMARY)
c.setFont("Helvetica-Bold", 10)
c.drawCentredString(W-4*cm, y-2.9*cm, "Rechercher")

y -= 5*cm

# Filtres
filters = ["🦷 Dentiste", "👨‍⚕️ Généraliste", "👶 Pédiatre", "🤰 Gynéco", "❤️ Cardio", "👁️ Ophtalmo", "🧴 Dermato"]
c.setFillColor(white)
c.setStrokeColor(BORDER)
x_pos = 2*cm
for f in filters:
    w = c.stringWidth(f, "Helvetica", 9) + 0.6*cm
    c.roundRect(x_pos, y-0.7*cm, w, 0.6*cm, 10, fill=1, stroke=1)
    c.setFillColor(black)
    c.setFont("Helvetica", 9)
    c.drawString(x_pos+0.3*cm, y-0.55*cm, f)
    x_pos += w + 0.3*cm

y -= 2*cm

# Stats
stat_card(c, 2*cm, y, "99 520", "Pros DHA")
stat_card(c, 5.7*cm, y, "7 713", "Dentistes")
stat_card(c, 9.4*cm, y, "24 186", "Médecins")
stat_card(c, 13.1*cm, y, "5", "Langues")

y -= 4*cm

# 2-3 fiche cards
c.setFillColor(PRIMARY)
c.setFont("Helvetica-Bold", 12)
c.drawString(2*cm, y, "🦷 Dentistes vedettes à Dubai")
y -= 1*cm
for i in range(3):
    c.setFillColor(white)
    c.setStrokeColor(BORDER)
    c.roundRect(2*cm+i*5.5*cm, y-3*cm, 5*cm, 3*cm, 8, fill=1, stroke=1)
    c.setFillColor(ACCENT)
    c.circle(2.5*cm+i*5.5*cm, y-1*cm, 0.5*cm, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 10)
    c.drawCentredString(2.5*cm+i*5.5*cm, y-1.1*cm, "👩‍⚕️")
    c.setFillColor(PRIMARY)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(3.2*cm+i*5.5*cm, y-1.5*cm, f"Dr. Test {i+1}")
    c.setFillColor(ACCENT)
    c.setFont("Helvetica", 8)
    c.drawString(3.2*cm+i*5.5*cm, y-2*cm, "General Dentist")
    c.setFillColor(MUTED)
    c.setFont("Helvetica", 7)
    c.drawString(3.2*cm+i*5.5*cm, y-2.4*cm, "✓ DHA-licensed")
    c.drawString(3.2*cm+i*5.5*cm, y-2.7*cm, "📍 Dubai")

footer(c, 5)
c.showPage()

# ========== PAGE 6: PROFIL PREMIUM ==========
header(c, "Mockup profil premium", 6)
y = title(c, "Mockup — Profil praticien premium", H-4*cm, 18)
y = text(c, "Comme Doctolib, mais multilingue et 100% Dubai", y, 10, MUTED, W-4*cm)

# Mockup profil
y -= 0.5*cm
c.setFillColor(PRIMARY)
c.roundRect(2*cm, y-5*cm, W-4*cm, 5*cm, 10, fill=1, stroke=0)
# Avatar
c.setFillColor(ACCENT)
c.circle(3.5*cm, y-2.5*cm, 1.2*cm, fill=1, stroke=0)
c.setFillColor(white)
c.setFont("Helvetica-Bold", 36)
c.drawCentredString(3.5*cm, y-2.7*cm, "👩‍⚕️")
# Nom
c.setFillColor(white)
c.setFont("Helvetica-Bold", 18)
c.drawString(5.5*cm, y-1.5*cm, "Dr. Lama Alamasi")
c.setFillColor(ACCENT)
c.setFont("Helvetica-Bold", 8)
c.drawString(5.5*cm, y-2*cm, "⭐ PROFIL PREMIUM")
c.setFillColor(white)
c.setFont("Helvetica", 10)
c.drawString(5.5*cm, y-2.5*cm, "General Dentist • Hadiya Dental Center")
c.drawString(5.5*cm, y-3*cm, "🗣️ AR, FR, EN • ⭐ 4.9/5 (127 avis)")

# CTA buttons
c.setFillColor(ACCENT)
c.roundRect(15*cm, y-2*cm, 3*cm, 0.8*cm, 8, fill=1, stroke=0)
c.setFillColor(PRIMARY)
c.setFont("Helvetica-Bold", 10)
c.drawCentredString(16.5*cm, y-1.7*cm, "📅 Prendre RDV")
c.setFillColor(white)
c.setStrokeColor(white)
c.roundRect(15*cm, y-3*cm, 3*cm, 0.7*cm, 8, fill=0, stroke=1)
c.setFillColor(white)
c.setFont("Helvetica", 9)
c.drawCentredString(16.5*cm, y-2.7*cm, "💬 WhatsApp")

y -= 6*cm

# Booking widget mockup
c.setFillColor(white)
c.setStrokeColor(BORDER)
c.roundRect(2*cm, y-7*cm, 8*cm, 7*cm, 10, fill=1, stroke=1)
c.setFillColor(PRIMARY)
c.setFont("Helvetica-Bold", 12)
c.drawString(2.5*cm, y-1*cm, "📅 Prendre rendez-vous")

# Calendar simulation
c.setFillColor(MUTED)
c.setFont("Helvetica", 7)
c.drawString(2.5*cm, y-1.7*cm, "JUIN 2026")
days = ["L8", "M9", "M10", "J11", "V12", "S13", "D14"]
for i, d in enumerate(days):
    c.setFillColor(PRIMARY if i == 3 else white)
    c.setStrokeColor(BORDER)
    c.roundRect(2.5*cm+i*1.05*cm, y-2.5*cm, 0.95*cm, 0.7*cm, 4, fill=1, stroke=1)
    c.setFillColor(white if i == 3 else black)
    c.setFont("Helvetica-Bold", 8)
    c.drawCentredString(2.97*cm+i*1.05*cm, y-2.2*cm, d)

# Slots
c.setFillColor(MUTED)
c.setFont("Helvetica", 7)
c.drawString(2.5*cm, y-3.2*cm, "CRÉNEAUX DISPONIBLES")
slots = ["09:00", "09:30", "10:30", "11:00", "11:30", "14:00", "14:30", "15:00", "16:00"]
for i, s in enumerate(slots):
    x = 2.5*cm + (i%3)*2.5*cm
    yy = y-3.6*cm - (i//3)*0.7*cm
    selected = (s == "11:00")
    c.setFillColor(ACCENT if selected else white)
    c.setStrokeColor(ACCENT if selected else BORDER)
    c.roundRect(x, yy-0.4*cm, 2*cm, 0.4*cm, 4, fill=1, stroke=1)
    c.setFillColor(PRIMARY if selected else black)
    c.setFont("Helvetica-Bold" if selected else "Helvetica", 8)
    c.drawCentredString(x+1*cm, yy-0.25*cm, s)

# Sidebar avec vidéo et services
c.setFillColor(white)
c.setStrokeColor(BORDER)
c.roundRect(11*cm, y-7*cm, 7*cm, 7*cm, 10, fill=1, stroke=1)
c.setFillColor(PRIMARY)
c.setFont("Helvetica-Bold", 12)
c.drawString(11.5*cm, y-1*cm, "🎬 Vidéo présentation")
c.setFillColor(PRIMARY)
c.roundRect(11.5*cm, y-4*cm, 6*cm, 2.5*cm, 6, fill=1, stroke=0)
c.setFillColor(white)
c.setFont("Helvetica-Bold", 10)
c.drawCentredString(14.5*cm, y-3*cm, "▶ Lire (0:58)")

c.setFillColor(PRIMARY)
c.setFont("Helvetica-Bold", 10)
c.drawString(11.5*cm, y-4.7*cm, "Services :")
c.setFillColor(black)
c.setFont("Helvetica", 8)
services_list = ["✓ Consultation gratuite", "✓ Détartrage & nettoyage", "✓ Implant dès 3 500 AED", "✓ Facettes céramique", "✓ Blanchiment", "✓ Invisalign", "✓ Urgence 24/7"]
for i, s in enumerate(services_list):
    c.drawString(11.5*cm, y-5.2*cm-i*0.4*cm, s)

footer(c, 6)
c.showPage()

# ========== PAGE 7: BUSINESS MODEL ==========
header(c, "Business model", 7)
y = title(c, "Business model & pricing", H-4*cm, 20)
y = text(c, "Freemium + commission = modèle Doctolib adapté Dubai", y, 10, MUTED, W-4*cm)

y -= 1*cm
c.setFillColor(PRIMARY)
c.setFont("Helvetica-Bold", 14)
c.drawString(2*cm, y, "Pricing praticien")
y -= 1*cm

# 3 tiers
tiers = [
    ("GRATUIT", "Claim de base", "✓ Nom, specialty, licence\n✓ Adresse, téléphone\n✓ Visible sur DMD Dubai\n✓ SEO basique", MUTED),
    ("PREMIUM", "200 AED/mois", "✓ Tout du gratuit\n✓ Vidéo présentation\n✓ Photos HD (x10)\n✓ Bio trilingue\n✓ WhatsApp button\n✓ Boost SEO", ACCENT),
    ("BUSINESS", "500 AED/mois", "✓ Tout du Premium\n✓ Position top résultats\n✓ Booking intégré\n✓ Téléconsult\n✓ Statistiques avancées", GOLD),
]
x_pos = 2*cm
for tier, price, desc, color in tiers:
    c.setFillColor(white)
    c.setStrokeColor(BORDER)
    c.roundRect(x_pos, y-5*cm, 5*cm, 5*cm, 10, fill=1, stroke=1)
    c.setFillColor(color)
    c.roundRect(x_pos, y-0.8*cm, 5*cm, 0.8*cm, 10, fill=1, stroke=0)
    c.setFillColor(white if color in [PRIMARY, ACCENT, GOLD] else white)
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(x_pos+2.5*cm, y-0.55*cm, tier)
    c.setFillColor(PRIMARY)
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(x_pos+2.5*cm, y-1.5*cm, price)
    c.setFillColor(black)
    c.setFont("Helvetica", 8)
    for i, line in enumerate(desc.split("\n")):
        c.drawString(x_pos+0.3*cm, y-2.3*cm-i*0.4*cm, line)
    x_pos += 5.3*cm

y -= 6*cm

# Projections
y = text(c, "Projections financières (année 1) :", y, 14, PRIMARY)
y -= 0.5*cm
y = text(c, "• 200 praticiens payants × 200 AED × 12 mois = 480 000 AED", y, 10, MUTED, W-4*cm)
y = text(c, "• Commission booking 10% × 100 RDV/mois × 200 praticiens × 100 AED × 12 = 2 400 000 AED", y, 10, MUTED, W-4*cm)
y = text(c, "• Setup onboarding × 200 × 500 AED = 100 000 AED", y, 10, MUTED, W-4*cm)
y = text(c, "TOTAL Y1 : 2 980 000 AED (~810 000 USD)", y, 12, ACCENT, W-4*cm)

footer(c, 7)
c.showPage()

# ========== PAGE 8: CONCURRENTS ==========
header(c, "Concurrents", 8)
y = title(c, "Analyse concurrentielle", H-4*cm, 20)
y = text(c, "10 plateformes actives à Dubai, 0 fait de trilingue FR/AR/EN", y, 10, MUTED, W-4*cm)

y -= 0.5*cm
competitors = [
    ("Practo", "Leader indien UAE", "31 000+ docs", "Pas FR", "Commission"),
    ("myAster", "Écosystème Aster", "5M users", "Pas FR", "Gratuit"),
    ("Zavis", "Miroir DHA Sheryan", "99 520 pros", "Pas FR", "Gratuit"),
    ("MediFinder", "Cosmetic + assurance", "11 800 docs", "Pas FR", "Gratuit"),
    ("Okadoc", "B2B premium", "Custom", "Pas solo", "$$$"),
    ("Doctify", "Reviews B2B", "B2B only", "Pas solo", "$$$"),
    ("HealthFinder", "Multi-émirat", "5 000+", "Pas FR", "Gratuit"),
    ("Daktoor", "Avis patients", "Faible", "Pas FR", "Gratuit"),
    ("Fidoc", "Directory simple", "Basique", "Pas FR", "Gratuit"),
    ("DoctorSoon", "Booking Dxb+Shj", "Limité", "Pas FR", "Gratuit"),
]
# Header table
c.setFillColor(PRIMARY)
c.roundRect(2*cm, y-0.7*cm, W-4*cm, 0.7*cm, 4, fill=1, stroke=0)
c.setFillColor(white)
c.setFont("Helvetica-Bold", 9)
c.drawString(2.2*cm, y-0.4*cm, "Plateforme")
c.drawString(6*cm, y-0.4*cm, "Positionnement")
c.drawString(10.5*cm, y-0.4*cm, "Couverture")
c.drawString(14*cm, y-0.4*cm, "UI FR?")
c.drawString(16.5*cm, y-0.4*cm, "Pricing")
y -= 0.7*cm

for i, (name, pos, cov, fr, price) in enumerate(competitors):
    bg = BG if i % 2 == 0 else white
    c.setFillColor(bg)
    c.rect(2*cm, y-0.6*cm, W-4*cm, 0.6*cm, fill=1, stroke=0)
    c.setFillColor(PRIMARY)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(2.2*cm, y-0.35*cm, name)
    c.setFillColor(black)
    c.setFont("Helvetica", 8)
    c.drawString(6*cm, y-0.35*cm, pos)
    c.drawString(10.5*cm, y-0.35*cm, cov)
    c.setFillColor(HexColor("#EF4444"))
    c.setFont("Helvetica-Bold", 8)
    c.drawString(14*cm, y-0.35*cm, fr)
    c.setFillColor(black)
    c.setFont("Helvetica", 8)
    c.drawString(16.5*cm, y-0.35*cm, price)
    y -= 0.6*cm

y -= 0.5*cm
c.setFillColor(ACCENT)
c.setFont("Helvetica-Bold", 14)
c.drawString(2*cm, y, "Notre avantage :")
y -= 0.8*cm
c.setFillColor(black)
c.setFont("Helvetica-Bold", 11)
c.drawString(2*cm, y, "0 concurrent ne fait de trilingue FR/AR/EN. C'est notre océan bleu.")

footer(c, 8)
c.showPage()

# ========== PAGE 9: FEATURE COMPARISON ==========
header(c, "Features", 9)
y = title(c, "Features Doctolib vs DMD Dubai", H-4*cm, 20)
y = text(c, "MVP vise 80% des features Doctolib, adaptées au marché UAE", y, 10, MUTED, W-4*cm)

y -= 0.5*cm
features = [
    ("Recherche par spécialité/zone", "✓", "✓"),
    ("Profil praticien enrichi", "✓", "✓"),
    ("Affichage disponibilités réelles", "✓", "✓"),
    ("Booking 1 clic 24/7", "✓", "✓"),
    ("Rappel SMS J-1", "✓", "✓"),
    ("Pré-paiement en ligne", "✓", "✓"),
    ("Multi-langue (5)", "FR/DE/IT/ES/NL", "FR/AR/EN/RU/ZH"),
    ("Avis patients vérifiés", "✓", "✓"),
    ("Synchronisation Google Cal", "✓", "✓"),
    ("Téléconsultation vidéo", "✓", "🟡 Phase 4"),
    ("App mobile native", "✓", "🟡 Phase 2"),
    ("Pricing", "135€/mois", "200 AED/mois"),
]
c.setFillColor(PRIMARY)
c.roundRect(2*cm, y-0.7*cm, W-4*cm, 0.7*cm, 4, fill=1, stroke=0)
c.setFillColor(white)
c.setFont("Helvetica-Bold", 9)
c.drawString(2.2*cm, y-0.4*cm, "Feature")
c.drawCentredString(10*cm, y-0.4*cm, "Doctolib France")
c.drawCentredString(15*cm, y-0.4*cm, "DMD Dubai")
y -= 0.7*cm

for i, (feat, dt, dmd) in enumerate(features):
    bg = BG if i % 2 == 0 else white
    c.setFillColor(bg)
    c.rect(2*cm, y-0.5*cm, W-4*cm, 0.5*cm, fill=1, stroke=0)
    c.setFillColor(black)
    c.setFont("Helvetica", 8)
    c.drawString(2.2*cm, y-0.3*cm, feat)
    c.drawCentredString(10*cm, y-0.3*cm, dt)
    c.drawCentredString(15*cm, y-0.3*cm, dmd)
    y -= 0.5*cm

footer(c, 9)
c.showPage()

# ========== PAGE 10: ROADMAP ==========
header(c, "Roadmap", 10)
y = title(c, "Roadmap 12 mois", H-4*cm, 20)

y -= 0.5*cm
roadmap = [
    ("M1-M2", "Infrastructure", "Scraping 99 520 fiches DHA\nSite web FR/AR/EN de base\nSEO foundation"),
    ("M3-M4", "MVP Premium", "Système de claim praticien\n200 fiches premium\nPremiers contacts terrain"),
    ("M5-M6", "Booking engine", "Prise de RDV Doctolib-like\nPré-paiement + commission\nCal.com self-hosted"),
    ("M7-M9", "Scale", "1 000 praticiens référencés\n50 praticiens payants\nSEO content 50 articles"),
    ("M10-M12", "Expansion", "2 000+ praticiens\n200 payants = 480K AED MRR\nAbu Dhabi + Sharjah"),
]
for phase, title_, desc in roadmap:
    c.setFillColor(ACCENT)
    c.roundRect(2*cm, y-1.8*cm, 2*cm, 1.8*cm, 8, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(3*cm, y-0.7*cm, phase)
    c.setFillColor(PRIMARY)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(4.5*cm, y-0.5*cm, title_)
    c.setFillColor(black)
    c.setFont("Helvetica", 8)
    from reportlab.lib.utils import simpleSplit
    for i, line in enumerate(simpleSplit(desc, "Helvetica", 8, W-7*cm)):
        c.drawString(4.5*cm, y-1*cm-i*0.4*cm, line)
    y -= 2.2*cm

footer(c, 10)
c.showPage()

# ========== PAGE 11: BUDGET ==========
header(c, "Budget", 11)
y = title(c, "Budget & utilisation des fonds", H-4*cm, 20)
y = text(c, "50 000 - 150 000 AED pour la première année", y, 11, MUTED, W-4*cm)

y -= 1*cm
budget_items = [
    ("Développement (Next.js + Cal.com + DB)", "60 000 AED", "40%"),
    ("Marketing & SEO (Google Ads, FB, content)", "60 000 AED", "40%"),
    ("Hébergement & outils (Vercel, Supabase, Twilio)", "15 000 AED", "10%"),
    ("Légal & admin (trade license, contrats)", "10 000 AED", "7%"),
    ("Divers & imprévus", "5 000 AED", "3%"),
]
for item, amount, pct in budget_items:
    c.setFillColor(black)
    c.setFont("Helvetica", 9)
    c.drawString(2*cm, y, item)
    c.drawRightString(W-4*cm, y, amount)
    bar(c, 2*cm, y-0.5*cm, W-4*cm, 0.3*cm, int(pct.rstrip("%")), ACCENT)
    y -= 1*cm

y -= 1*cm
c.setFillColor(PRIMARY)
c.setFont("Helvetica-Bold", 14)
c.drawString(2*cm, y, "TOTAL Y1 : ~150 000 AED (40 000 USD)")

y -= 1.5*cm
c.setFillColor(BG)
c.roundRect(2*cm, y-2*cm, W-4*cm, 2*cm, 8, fill=1, stroke=0)
c.setFillColor(PRIMARY)
c.setFont("Helvetica-Bold", 11)
c.drawString(2.5*cm, y-0.7*cm, "ROI attendu")
c.setFillColor(black)
c.setFont("Helvetica", 9)
c.drawString(2.5*cm, y-1.3*cm, "Investissement 150K AED → Revenu Y1 potentiel 2,98M AED")
c.drawString(2.5*cm, y-1.8*cm, "ROI = ~20x si objectif conversion atteint (5% des 4 000 prospects chauds)")

footer(c, 11)
c.showPage()

# ========== PAGE 12: CONTACT / NEXT STEPS ==========
c.setFillColor(PRIMARY)
c.rect(0, 0, W, H, fill=1, stroke=0)
c.setFillColor(ACCENT)
c.rect(0, H-3*cm, W, 3*cm, fill=1, stroke=0)
c.setFillColor(white)
c.setFont("Helvetica-Bold", 36)
c.drawCentredString(W/2, H-2*cm, "Construisons le Doctolib de Dubai")
y = H-6*cm
c.setFillColor(white)
c.setFont("Helvetica", 14)
c.drawCentredString(W/2, y, "Prochaines étapes :")
y -= 1*cm
steps = [
    "✓ Validation de la maquette par W",
    "→ Décision go/no-go pour développement",
    "→ Scraping 50K+ fiches DHA (en cours)",
    "→ Setup Cal.com self-hosted",
    "→ Lancement pilotes 5-10 dentistes Dubai",
    "→ Signature 50 praticiens payants à 200 AED/mois",
]
c.setFont("Helvetica", 12)
for s in steps:
    c.drawCentredString(W/2, y, s)
    y -= 0.8*cm

y -= 1*cm
c.setFillColor(GOLD)
c.setFont("Helvetica-Bold", 18)
c.drawCentredString(W/2, y, "W • w@dmd.ae")
y -= 1*cm
c.setFillColor(white)
c.setFont("Helvetica", 10)
c.drawCentredString(W/2, y, "Document confidentiel — Juin 2026")

c.showPage()
c.save()

print(f"✅ PDF généré : {OUTPUT}")
print(f"📦 Taille : {os.path.getsize(OUTPUT) / 1024:.1f} KB")
