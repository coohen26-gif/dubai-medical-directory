# Brief Design — DMD Dubai Medical Directory

**Date** : 2026-06-06 (UTC)
**Cycle** : Design Studio (2/30min)
**Statut** : ✅ Livrables produits
**Auteur** : Cron autonome / DMD DESIGN

---

## 1. Objectif

Produire les **5 mockups PNG** (format haute résolution, branding cohérent)
servant de référence visuelle pour le site Dubai Medical Directory avant
intégration front-end (React/Next.js). Ces assets alimentent la maquette
client, la documentation produit, et la page de démo investisseur.

## 2. Branding

### Palette

| Token        | Hex       | Usage                              |
|--------------|-----------|------------------------------------|
| `--blue`     | `#005A9C` | Primary — médical, CTAs, header    |
| `--blue-dk`  | `#003866` | Textes bleu foncé, hover           |
| `--blue-lt`  | `#E5F0FA` | Background hero card, soft surfaces|
| `--green`    | `#28A75F` | Confiance, badges "vérifié"        |
| `--green-dk` | `#1C7842` | Hover, accents                     |
| `--ink`      | `#1C212C` | Texte principal                    |
| `--ink-soft` | `#5A6370` | Texte secondaire, méta            |
| `--line`     | `#DCE2EB` | Bordures, séparateurs              |
| `--warn`     | `#EA580C` | Alerte, urgence 24/7              |
| `--gold`     | `#D4AF37` | Premium tier                      |
| `--offwhite` | `#F8FAFC` | Background global                  |
| `--white`    | `#FFFFFF` | Cards, surfaces                    |

### Typographie

- **Titres** : serif (DejaVu Serif Bold) — évoque sérieux médical et Dubai premium
- **Corps** : sans-serif (DejaVu Sans Regular/Bold) — lisibilité élevée, trilingue
- **Note production** : remplacer en production par
  - Titres : *Cairo* (AR) / *Playfair Display* (FR/EN) / *Noto Serif SC* (ZH) / *PT Serif* (RU)
  - Corps : *Inter* ou *Noto Sans* (couvre 5 langues)

### Logo

- **Mark** : carré arrondi bleu (#005A9C) avec lettre "D" blanche + accent
  croix médicale discrète (vert #28A75F)
- **Wordmark** : "DMD Dubai" en serif bold, baseline "Dubai Medical
  Directory" en sans-serif regular
- **Variantes** : bleu sur blanc (principal), blanc sur bleu (header dark mode),
  monochrome ink (impression)

## 3. Livrables

| #  | Fichier             | Dimensions   | Contenu                                                                  |
|----|---------------------|--------------|--------------------------------------------------------------------------|
| 1  | `homepage_FR.png`   | 1440 × 2400  | Homepage FR long-scroll : sélecteur langue (FR/AR/EN/RU/ZH) header, hero avec recherche + stats, 10 fiches dentistes vedettes, sections spécialités/populaires, footer |
| 2  | `profil_premium.png`| 1440 × 1500  | Page profil dentiste premium : hero photos, player vidéo, bio trilingue, badges vérifications, WhatsApp button, booking link, avis patients, horaires |
| 3  | `recherche_carte.png`| 1440 × 1100 | Page recherche : barre filtres latéraux (spécialité, langue, zone, genre, prix), carte Dubai avec markers colorés, résultats liste, vue split |
| 4  | `homepage_AR.png`   | 1440 × 2400  | Identique à #1 mais en RTL (arabe) : layout mirroré, typographie Cairo-ready, menu à droite, alignements inversés |
| 5  | `mobile.png`        | 390 × 1800   | Version mobile responsive (iPhone 14) : header burger, sélecteur langue en sheet, recherche pleine largeur, filtres en bottom-sheet, fiche card stack, bottom nav |

## 4. Composants UI clés

### Header (desktop)
- Logo (gauche) · nav (Trouver un praticien / Spécialités / Établissements /
  Blog / À propos) · sélecteur langue (5 codes pays : 🇫🇷 FR / 🇦🇪 AR / 🇬🇧 EN /
  🇷🇺 RU / 🇨🇳 ZH) · bouton "Connexion" outlined · CTA "Inscription pro" filled bleu

### Hero search
- Input 720px, bouton "Rechercher" 140px intégré
- Quick-tags cliquables sous l'input (suggestions intelligentes)
- Card stats 4 KPIs à droite (99 520+ pros, 7 713 dentistes, 5 800 établissements, 100% vérifiés)

### Filtres latéraux (page recherche)
- Spécialité (multi-select avec icônes)
- Langue parlée (drapeaux + checkbox)
- Zone Dubai (Jumeirah / Marina / Downtown / Deira / Bur Dubai / Business Bay)
- Genre praticien (radio)
- Tranche de prix (range slider)
- Disponibilité (toggle : aujourd'hui / ce soir / week-end)
- Note minimum (★ 4+)
- Bouton "Réinitialiser" + "Appliquer (X résultats)"

### Fiche dentiste vedette
- Photo carrée 120×120 (placeholder gris)
- Nom + spécialité + zone
- Badges : "Vérifié DHA" (vert) · "FR/EN/AR" (drapeaux) · "Réponse <1h" (bleu)
- Note ★ 4.8 (127 avis)
- CTA "Voir profil" outlined + "WhatsApp" vert plein

### Profil premium
- Cover photo + logo établissement
- Galerie 6 photos + bouton "Vidéo de présentation" (player mocké)
- Bio trilingue (onglets FR / AR / EN)
- Bloc "Prendre rendez-vous" sticky à droite : calendrier + WhatsApp button
- Bloc "Tarifs" tabulaire
- Bloc "Avis" avec photos patients
- Bloc "Localisation" + carte embed

## 5. Responsive

### Breakpoints cibles
- **Mobile** : 390px (mockup livré)
- **Tablet** : 768px (mockup dérivé à produire en M2)
- **Desktop** : 1440px (mockups livrés)
- **Wide** : 1920px (auto-scaling)

### Adaptations mobile
- Header → burger menu + logo centré
- Sélecteur langue → bottom sheet avec drapeaux
- Filtres latéraux → bottom sheet plein écran
- Search → input pleine largeur + bouton icône
- Fiches → stack vertical, photo 64×64
- CTA WhatsApp → FAB (Floating Action Button) sticky bottom-right
- Bottom nav 4 items (Accueil / Recherche / Favoris / Compte)

## 6. RTL (Arabe)

- Direction : `dir="rtl"` sur `<html>` et containers principaux
- Layout : `flex-direction: row-reverse` global
- Typographie : basculement vers *Cairo* (Google Fonts, support natif AR)
- Icônes directionnelles : flèches inversées (←/→), mais icônes
  universelles conservées (🔍, ⭐, 📞, 💬)
- Numbers : garder chiffres occidentaux (standard Dubai)
- Wordmark : conserver "DMD Dubai" en latin (reconnaissance de marque)
- Hero copy : traduit via `translations/` (cycle 02+ déjà couvert)

## 7. Accessibilité

- Contraste texte/background : AA minimum (4.5:1) sur tout le body
- Cibles tactiles : 44×44px min (mobile)
- Focus rings : visibles (outline bleu 2px + offset 2px)
- Alt text : tous les visuels décoratifs `alt=""`, informatifs descriptifs
- Lang switcher : respecte `lang` attribute dynamique (`<html lang="ar">`)
- Motion : respecter `prefers-reduced-motion` (désactive animations hero)

## 8. Figma public link (à compléter)

> **Status** : ⚠️ Figma file non créé dans ce cycle (sandbox sans licence Figma,
> génération PNG via PIL). **Action** : importer les 5 PNG en frames Figma et
> publier le lien dans `docs/figma_link.txt` dès qu'un compte Figma est
> provisionné.
>
> **Procédure d'import** :
> 1. Créer un nouveau Figma file "DMD Dubai — Mockups v1"
> 2. Importer chaque PNG comme frame (File > Place Image > Set as Frame)
> 3. Organiser en page "Mockups v1" (5 frames 1440px + 1 frame 390px)
> 4. Ajouter une cover avec branding
> 5. Share > "Anyone with the link can view" > copier URL
> 6. Sauver dans `docs/figma_link.txt`

## 9. Métadonnées techniques

- **Format** : PNG, 8-bit RGB, non-interlaced
- **Résolution** : 1× (mockups web), production-ready pour Retina
- **Poids** : 67–172 KB / fichier (optimisé, <200 KB cible respectée)
- **Source** : `_0X_*.py` (PIL/Pillow) + `_dmd_brand.py` (tokens partagés)
- **Reproductibilité** : `cd design && python3 _01_homepage_fr.py` pour chaque
- **Déterminisme** : seeds `random.seed(42)` partout (mockups stables)

## 10. Roadmap

- [x] **Cycle 1** (00:43 UTC) : 5 PNG mockups + brand tokens — **livré**
- [ ] **M2** : Import Figma public + partage lien
- [ ] **M2** : Mockup tablet (768px) — 1 dérivé
- [ ] **M2** : Mockup page réservation (flow 3 étapes)
- [ ] **M2** : Mockup page établissement (DHA facility)
- [ ] **M3** : A/B variants CTA WhatsApp vs booking form
- [ ] **M3** : Dark mode AR (ramadan / soir)

## 11. Annexes

- Brand source : `design/_dmd_brand.py` (tokens, helpers, logo)
- Mockup sources : `design/_01_*.py` à `design/_05_*.py`
- Translations source : `translations/` (FR/AR/EN + RU/ZH cycles 04+)
- Référence : `dubai-medical-directory/CAHIER-DES-CHARGES.md`
