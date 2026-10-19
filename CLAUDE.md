# Campus Equipment Lending — project notes for Claude Code

DBMS mini-project (SY B.Tech IT). Flask + Psycopg 3 + PostgreSQL. See README.md for full details.
Two databases: local PostgreSQL 18 (`campus_equipment`, managed in pgAdmin 4, configured in `.env`)
and the live site's Neon database (DATABASE_URL in `.env.vercel`). Live site: https://campus-equipment.vercel.app
(deployed with the Vercel CLI, not from GitHub — pushing to GitHub does NOT redeploy). Never print or commit `.env*` files.

## State (2026-10-19)
- Local DB: schema + full `sql/sample_data.sql` (PART 1 and PART 2) loaded — 33 students, 16 equipment, 19 loans.
- `sql/sample_data.sql` PART 2 adds 30 students, 10 equipment, 16 loans. PART 2 is idempotent (matched by
  roll number / asset code / loan notes), so it is safe to run on a DB that already has PART 1.
- Overview page now has a "Visual Summary" with three charts (equipment by category, loans by status,
  loans by department), drawn in `static/app.js` `renderCharts()` from `/api/data` — no chart library.

- Live site: UPDATED (2026-10-19). PART 2 loaded into Neon — 33 students, 16 equipment, 20 loans
  (20, not 19, because one loan had already been issued through the live site before PART 2 was loaded).
  Redeployed with `vercel deploy --prod`; Visual Summary charts verified at https://campus-equipment.vercel.app.
  Commit pushed to GitHub (https://github.com/virajupadhyayfilms/campus-equipment).

## Updating the live site later
1. New sample data: run only the new SQL against DATABASE_URL_UNPOOLED from `.env.vercel` (venv's psycopg or psql).
2. Code changes: `vercel deploy --prod` from this folder (never from `~`), then check the live URL.
3. `git push` to keep GitHub in sync (it does not redeploy).
