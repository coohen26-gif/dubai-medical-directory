# 📋 CAHIER DES CHARGES — Dubai Medical Directory

**Date** : 5 juin 2026
**Statut** : Document de travail — Phase de construction
**Auteur** : W (commanditaire) + Bonjour/Goku (assistant technique)

---

## 1. 🎯 VISION DU PROJET

**One-liner** : La première plateforme médicale trilingue FR/AR/EN des Émirats, listant tous les professionnels de santé DHA-licensés à Dubai.

**Mission** : Référencer les 99 520+ professionnels de santé DHA-licensés à Dubai, avec une fiche gratuite pour chaque (nom, spécialité, adresse, téléphone, langues parlées), puis proposer une version enrichie payante (200 AED/mois) aux praticiens qui veulent booster leur visibilité.

**Pourquoi ce projet** : Aucun acteur sur le marché UAE ne fait de trilingue FR/AR/EN. C'est un océan bleu identifié via analyse concurrentielle de 10 plateformes existantes (cf. `research/gap-analysis-opportunities.md`).

---

## 2. 📊 LE MARCHÉ (chiffres vérifiés 2026)

| Métrique | Valeur | Source |
|---|---|---|
| Population Dubai | 3,66 M | Dubai Statistics Center |
| Total pros DHA-licensés | **99 520** | DHA Sheryan Registry, 2026-04-03 |
| Médecins | 24 186 | DHA Sheryan |
| Dentistes | 7 713 | DHA Sheryan |
| Chirurgiens (toutes spé) | ~3 500-4 000 | Agrégation DHA Sheryan |
| Établissements de santé | 5 800 | Government of Dubai Media Office, 18-fév-2026 |
| Croissance YoY | +8,6 % établissements / +8,3 % effectif privé | DHA 2025 |
| CAGR marché UAE 2026-2030 | 7,5-9,5 % | Mordor, Grand View Research |

**Marché adressable (TAM)** : 87 500 pros DHA privé (88 % du total).
**Cible Year 1** : 11 800 médecins UAE × 5 % conversion = ~590 praticiens payants.
**ARR potentiel Y1** : 1,42 M AED abonnements + 1,42 M AED commissions booking = **~2,8 M AED (770K USD)**.

---

## 3. 🏗️ ARCHITECTURE TECHNIQUE

### 3.1. Stack proposée

| Composant | Technologie | Justification |
|---|---|---|
| **Backend** | Node.js + Express | Rapide à dev, écosystème riche, FR/AR/EN facile |
| **Base de données** | PostgreSQL | Robuste, full-text search FR/AR natif, géospatial |
| **Frontend** | Next.js + React | SSR pour SEO, multi-langue natif (next-intl) |
| **Hébergement** | Vercel + Supabase (MVP) puis AWS/DigitalOcean UAE | Latence UAE, RGPD-friendly |
| **Recherche** | PostgreSQL FTS + Meilisearch | Full-text search multilingue |
| **Stockage média** | Cloudflare R2 / S3 | Photos, vidéos praticiens |
| **Email** | Resend | Transactionnel (notifications, confirmations) |
| **Analytics** | Plausible (privacy-friendly) | RGPD, pas de cookie banner requis |

### 3.2. Structure de la base de données

```sql
-- Table principale : professionnels
CREATE TABLE professionals (
  id SERIAL PRIMARY KEY,
  full_name_ar VARCHAR(255),
  full_name_en VARCHAR(255),
  full_name_fr VARCHAR(255),
  specialty VARCHAR(100),        -- ex: "Dentist", "General Practitioner"
  sub_specialty VARCHAR(100),
  license_number VARCHAR(50) UNIQUE NOT NULL,
  gender VARCHAR(10),
  nationality VARCHAR(50),
  languages_spoken TEXT[],       -- ex: ['AR', 'EN', 'FR']
  facility_id INT REFERENCES facilities(id),
  area VARCHAR(100),             -- ex: "Dubai Marina"
  phone VARCHAR(50),
  email VARCHAR(255),
  source_url TEXT,
  scraped_at TIMESTAMP,
  is_claimed BOOLEAN DEFAULT FALSE,
  is_premium BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Table établissements
CREATE TABLE facilities (
  id SERIAL PRIMARY KEY,
  name VARCHAR(255) NOT NULL,
  license_number VARCHAR(50) UNIQUE,
  type VARCHAR(50),              -- 'Hospital', 'Clinic', 'Dental Center'
  address TEXT,
  area VARCHAR(100),
  city VARCHAR(50) DEFAULT 'Dubai',
  phone VARCHAR(50),
  latitude DECIMAL(10, 8),
  longitude DECIMAL(11, 8),
  scraped_at TIMESTAMP
);

-- Table reviews (à venir en M+6)
CREATE TABLE reviews (
  id SERIAL PRIMARY KEY,
  professional_id INT REFERENCES professionals(id),
  rating INT CHECK (rating BETWEEN 1 AND 5),
  comment TEXT,
  verified BOOLEAN DEFAULT FALSE,
  verification_method VARCHAR(20), -- 'SMS_OTP', 'QR_CODE'
  language VARCHAR(5),
  created_at TIMESTAMP DEFAULT NOW()
);
```

---

## 4. 🎨 FONCTIONNALITÉS

### 4.1. MVP — Phase 1 (mois 1-3) — GRATUIT

- ✅ **Liste des 99 520 pros** DHA-licensés (scraping)
- ✅ **Page profil public** par praticien (nom, spécialité, adresse, tél, langues)
- ✅ **Recherche multi-critères** : spécialité, langue, zone, genre, nationalité
- ✅ **Filtres géographiques** : Dubai Marina, Downtown, JBR, Business Bay, etc.
- ✅ **SEO local** : pages specialty × city × language
- ✅ **Multi-langue FR/AR/EN** avec sélecteur
- ✅ **Responsive mobile** (70% du traffic UAE est mobile)
- ✅ **Schema.org Physician** markup pour Google Rich Results
- ✅ **Sitemap XML** multilingue

### 4.2. Phase 2 — Premium 200 AED/mois (mois 3-6)

- ✅ Tout du MVP
- 🆕 **Claim de profil** : le praticien revendique sa fiche (vérif email + license DHA)
- 🆕 **Photos HD** du praticien et du cabinet (jusqu'à 10)
- 🆕 **Vidéo de présentation** 60 sec (hébergée sur plateforme)
- 🆕 **Bio enrichie trilingue** (FR, AR, EN)
- 🆕 **Lien vers site web** du praticien
- 🆕 **Bouton WhatsApp** direct
- 🆕 **Horaires d'ouverture** + jours fériés
- 🆕 **Assurances acceptées** (liste éditable)
- 🆕 **Boost SEO** : fiche en tête de liste pour sa zone/specialty
- 🆕 **Statistiques de vues** : nb visiteurs/mois sur la fiche

### 4.3. Phase 3 — Booking & Reviews (mois 6-12)

- 🆕 **Système de réservation** intégré (calendrier praticien)
- 🆕 **Pré-paiement** AED 50-200 par consultation
- 🆕 **Commission 10-15 %** sur chaque booking confirmé
- 🆕 **Reviews vérifiés** : QR code en cabinet + SMS-OTP post-visite
- 🆕 **Modération multilingue** (FR/AR/EN)
- 🆕 **Notifications email/SMS** au praticien (nouveau RDV, nouvel avis)

### 4.4. Phase 4 — Teleconsult (année 2)

- 🆕 **Téléconsultation vidéo** trilingue (WebRTC + Twilio)
- 🆕 **Prescription électronique** (compliance TRA + DHA)
- 🆕 **Paiement intégré** (Stripe / Tap / Telr)

---

## 5. 🌍 MULTILINGUISME

### 5.1. Stratégie de langues

- **Phase 1** : EN + AR (70% du marché UAE)
- **Phase 1.5** : + FR (océan bleu, 100-200K expats FR)
- **Phase 2** : + RU, ZH, HI (selon demande)

### 5.2. URLs et SEO

```
/en/dentists/dubai-marina          → version anglaise
/ar/اطباء-اسنان/دبي-مارينا          → version arabe
/fr/dentistes/dubai-marina          → version française
```

- Hreflang tags pour signaler à Google les variantes linguistiques
- `<html lang="ar" dir="rtl">` pour l'arabe (right-to-left)
- Traduction initiale : professionnel humain + DeepL API pour volume

---

## 6. 💰 MODÈLE ÉCONOMIQUE

### 6.1. Sources de revenus

| Source | Tarif | Volume cible Y1 | Revenu Y1 |
|---|---|---|---|
| Abonnement Premium praticien | 200 AED/mois | 590 praticiens | 1 420 000 AED |
| Commission booking | 10-15 % × AED 200/booking × 100/mois/praticien | 590 × 100 × 200 × 12 % | 1 420 000 AED |
| **Total Y1** | | | **~2 840 000 AED (770K USD)** |

### 6.2. Coûts prévisionnels Y1

| Poste | Coût mensuel | Coût annuel |
|---|---|---|
| Hosting (Vercel + Supabase + S3) | 500 AED | 6 000 AED |
| Nom de domaine (.ae + .com + .fr) | 50 AED | 600 AED |
| Traductions (DeepL API) | 200 AED | 2 400 AED |
| Marketing (Google Ads, FB Ads) | 5 000 AED | 60 000 AED |
| Freelance dev (si besoin) | 8 000 AED | 96 000 AED |
| **Total Y1** | | **~165 000 AED (45K USD)** |

**Marge Y1** : 2 840 000 - 165 000 = **2 675 000 AED (725K USD)** — si on atteint les objectifs de conversion.

---

## 7. 📅 ROADMAP DÉTAILLÉE

### Semaine 1-2 : Infrastructure data
- [ ] Finaliser le scraping DHA (10 000+ fiches)
- [ ] Nettoyer et dédupliquer
- [ ] Charger en PostgreSQL
- [ ] Backup complet

### Semaine 3-4 : MVP site web
- [ ] Setup Next.js + Supabase
- [ ] Page d'accueil FR/AR/EN
- [ ] Liste des praticiens avec filtres
- [ ] Page profil praticien
- [ ] Recherche full-text basique

### Semaine 5-6 : SEO Foundation
- [ ] 50 articles SEO long-tail (FR/AR/EN)
- [ ] Schema.org markup
- [ ] Sitemap multilingue
- [ ] Inscription Google Search Console + Bing Webmaster

### Semaine 7-8 : Lancement public
- [ ] Domaine .ae + .com + .fr
- [ ] SSL + hébergement prod
- [ ] Analytics (Plausible)
- [ ] Lancement silencieux (pas de pub, juste SEO)

### Mois 3-6 : Premium
- [ ] Système de claim praticien
- [ ] Paiement 200 AED/mois (Stripe / Tap)
- [ ] Profils enrichis (photos, vidéo, bio trilingue)
- [ ] Sales terrain : FBC, LinkedIn FR UAE, groupes FB

### Mois 6-12 : Booking + Reviews
- [ ] Système de réservation
- [ ] Pré-paiement
- [ ] Reviews vérifiés SMS-OTP + QR
- [ ] Expansion Abu Dhabi + Sharjah

### Année 2 : Teleconsult + Scale
- [ ] Téléconsultation vidéo trilingue
- [ ] Niche cosmetic / dental
- [ ] Partenariats assureurs (Daman, AXA)

---

## 8. ⚖️ ASPECTS LÉGAUX & ÉTHIQUES

### 8.1. Données personnelles (RGPD + UAE Data Law)

- Les données DHA Sheryan sont **publiques** (registre officiel accessible à tous)
- Affichage de : nom, spécialité, license #, langue, zone = OK
- ⚠️ **PAS d'affichage** : numéro de téléphone direct, email personnel (sauf si consent)
- Solution : bouton "Appeler le cabinet" qui passe par un proxy
- Conformité UAE Personal Data Protection Law (PDPL) — entrée en vigueur 2025

### 8.2. Accréditation DHA

- **Pas d'accréditation officielle nécessaire** pour afficher des data publiques
- Afficher "DHA-licensed - License #XXXXX" = information publique, pas une allégation
- Demande de partenariat formel DXH à faire en parallèle (6-12 mois)

### 8.3. Responsabilité

- Disclaimer : "Les informations proviennent du DHA Sheryan Registry. En cas d'erreur, contactez-nous."
- Vérification manuelle par échantillonnage des 10 000 premières fiches

---

## 9. 🎯 KPIs DE SUCCÈS

### Phase 1 (mois 1-3)
- 10 000+ fiches en base ✅
- Site en ligne FR/AR/EN ✅
- 100 visiteurs organiques/jour (objectif J+90)
- 50 praticiens qui ont claim leur profil

### Phase 2 (mois 3-6)
- 5 praticiens payants (pilote)
- Validation que le produit est utile
- 1 000 visiteurs organiques/jour

### Phase 3 (mois 6-12)
- 50 praticiens payants = 10 000 AED/mois MRR
- 100 bookings/mois via la plateforme
- 5 000 visiteurs organiques/jour

### Year 1
- 590 praticiens payants = 118 000 AED/mois MRR
- 240K AED (770K USD) ARR
- 10 000 visiteurs organiques/jour

---

## 10. 🚨 RISQUES IDENTIFIÉS

| Risque | Probabilité | Impact | Mitigation |
|---|---|---|---|
| DHA bloque le scraping | Moyenne | Élevé | Diversifier sources (Dubai Pulse, Zavis) + API officielle si proposée |
| Practo lance une UI FR | Faible (1 an sans) | Élevé | Accélérer le SEO et le premier-mover advantage |
| Praticiens ne paient pas 200 AED | Moyenne | Élevé | Tester avec 5-10 d'abord, ajuster le pricing |
| Problème légal sur affichage data | Faible | Élevé | Disclaimer + conformité PDPL UAE |
| Concurrence copie le modèle | Moyenne | Moyen | Verrouiller communauté FR (FBC, Alliance Française) |
| Coût acquisition client trop élevé | Moyenne | Élevé | SEO avant tout (canal gratuit) + sales direct |

---

## 11. 📁 STRUCTURE DU PROJET

```
dubai-medical-directory/
├── CAHIER-DES-CHARGES.md          ← ce document
├── code/
│   ├── scrapers/
│   │   └── dha_sheryan_scraper.py ← script de scraping
│   ├── web/
│   │   ├── app/                    ← Next.js
│   │   ├── components/
│   │   └── lib/
│   └── db/
│       └── schema.sql
├── data/
│   ├── dha_professionals.csv      ← dataset scrapé
│   └── dha_facilities.csv
├── research/
│   ├── dubai-medical-market-2026.md
│   ├── competitors-dubai-medical-2026.md
│   ├── competitors-pricing-model.md
│   └── gap-analysis-opportunities.md
├── marketing/
│   ├── pitch-praticien.md
│   ├── seo-keywords.md
│   └── sales-scripts.md
└── docs/
    ├── business-plan.md
    └── decision-framework.md
```

---

## 12. ✅ PROCHAINE ÉTAPE IMMÉDIATE

1. **Attendre le scraping** en cours (~10-30 min restantes)
2. **Valider le dataset** : combien de fiches réellement récupérées
3. **Créer la maquette PDF** une fois la data en main
4. **Présenter le résultat** pour go/no-go

**Status actuel** : scraping en cours, pas d'erreur, en attente des résultats.
