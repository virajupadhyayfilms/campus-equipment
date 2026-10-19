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

## Pending: update the LIVE site
1. Load PART 2 into Neon (only that part — PART 1 is already there):
   `sed -n '/^-- PART 2/,$p' sql/sample_data.sql > /tmp/part2.sql`, then run /tmp/part2.sql against
   DATABASE_URL from `.env.vercel` (e.g. with the venv's psycopg, or psql). Verify counts: 33 / 16 / 19
   only if Neon started with the same 3 sample loans; otherwise check that 30 students and 10 items were added.
2. Redeploy: `vercel --prod`, then open https://campus-equipment.vercel.app and check the charts.
3. Push the commit to GitHub: `git push`.
