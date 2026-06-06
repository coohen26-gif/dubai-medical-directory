# DMD Health Check #2 (1/30min) — 2026-06-06 11:04 UTC

**Cron:** 567b5bee Dubai - Health Check Scraping
**Time:** 2026-06-06 11:04 UTC
**Cycle:** 2/30min (suite check #1 08:33 UTC)

## Status Global

| Composant | État | Détail |
|---|---|---|
| DHA Sheryan | ⚠️ Saturated | 0 new (9537 dedup), scraping direct registry épuisé |
| Zavis | ✅ Healthy | 2000/2000 processed, +2 dentists (rebond marginal), elapsed 139.1s |
| Dataset dentists | ✅ 7,114 fiches | +4 vs 08:33 (7,110), 711% de l'objectif PG 1000 |
| DHA main CSV | ⚠️ Known bug | 35.1% exact dup rows (scraping bug documenté, non-régression) |
| Audit présence digitale | ✅ Stable | aucune régression sur la dernière heure |
| Git | ✅ Clean | Last commit 8283e10 (tech-build #17, 11:04 UTC) |

## Décision

- **Scraping** : non bloqué/captcha, Zavis fonctionne, basculer Dubai Pulse open data NON nécessaire.
- **PG insertion** : dataset 7,114 fiches (largement >1000), schema.sql + load_csv_to_pg.py prêts, **MAIS** loader en attente de `DMD_PG_DSN` :
  - Pas de `psql`/`pg_isready` dans le sandbox
  - Pas de service PostgreSQL démarré (port 5432 fermé)
  - `DMD_PG_DSN` non défini dans l'environnement
  - C'est un **blocker user (W)**, pas un blocker tech
- **Audit présence digitale** : stable, pas d'alerte.

## Prochaine action

- **11:04 UTC** : NO_REPLY (tout OK, pas d'action automatique possible)
- **En attente W** : fournir `DMD_PG_DSN` (postgresql://user:pwd@host:port/db) pour activer le loader PG
- **Prochain cycle health check** : 11:34 UTC (cron 1/30min)

## Pourquoi pas basculer sur Dubai Pulse / Zavis

- Zavis tourne déjà et fonctionne (7713 URLs dans le sitemap, 2000 traitées/cycle)
- DHA Sheryan saturated mais reste l'autorité de référence pour les IDs
- Dubai Pulse open data n'est pas activé car la bascule ne débloque pas le blocker PG (qui est ailleurs)
