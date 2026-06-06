# DMD tech-build check #12 (2026-06-06 07:35 UTC)

State stable since check #11:

**Build artifacts**
- 120 static profiles (40 dentists × FR/AR/EN) — `code/web/profiles/{fr,ar,en}/`
- `sitemap.xml`: 121 URLs
- `index.json`: 40 profile records
- per-lang JSON fiches: 525 (105 unique dentists × 5 langs FR/AR/EN/RU/ZH)
- `code/web/index.html` + `profil-premium.html` static
- `design/`: 5 design mockups (homepage FR/AR, profil premium, recherche+carte, mobile)

**Data layer**
- `data/dha_professionals_full.csv` — 101,080 rows (35,464 known exact dups, scraping bug)
- `data/dentists_emirates.csv` — 6,753 dentists (last +4 from Zavis 07:07)
- `code/db/schema.sql` — full PG schema (7 tables, ready)
- `code/db/load_csv_to_pg.py` — psycopg2 COPY loader (idempotent), requires DMD_PG_DSN

**Pending W decision (unchanged since #6)**
- Provide `DMD_PG_DSN` env var to run the PG loader
- Approve Next.js scaffolding (package.json + next.config + pages/) to replace static HTML
- Activate `code/web/profiles/index.json` as the dynamic profile index once PG loaded

**No regressions, no new blockers. NO_REPLY.**
