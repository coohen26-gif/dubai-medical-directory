## DMD tech-build check #17 — 2026-06-06 11:04 UTC

**État : STABLE** (6ème check identique consécutive)

### ✅ Ce qui avance / est OK
- **Pages profil** : 40 fiches × 3 langues (FR/AR/EN) = **120 HTML** générés (+ index.json)
- **sitemap.xml** : 121 URLs valides, inchangé
- **Traductions** : 115 fiches × 5 langues (fr/en/ar/ru/zh) = **575 JSON** dans translations/per_lang/
- **Données** : CSV stable (DHA saturated, Zavis marginal)
- **Robots.txt** : OK, pointe vers sitemap
- **Scraping** : saturé mais pipeline stable

### ⏸️ Bloqué (en attente décision/données W)
- **PostgreSQL** : schema.sql + load_csv_to_pg.py prêts, mais **DB non connectée** — attend `DMD_PG_DSN`
- **Next.js** : non démarré — attend décision W (statique fonctionne en attendant)
- **Recherche full-text** : pas implémentée (PG FTS dépend du point précédent)

### 📊 Métriques
- Profils publiés : 120/99 520 (0,12 % — phase MVP statique assumée)
- Croissance nette : **0** depuis check #16 (~30min)
- Dernier commit précédent : 0ac35ad (check #16)
- Cycles cron : #1-#17, état stable

### 🎯 Action
- **Commit minimal** (état stable log uniquement)
- W doit fournir : (a) DSN PostgreSQL ou (b) décision Go Next.js
- En attendant : continuer SEO cycles + scraping marginal

NO_REPLY.
