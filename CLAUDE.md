# Campus Equipment Lending — project notes for Claude Code

DBMS mini-project (SY B.Tech IT). Flask + Psycopg 3 + PostgreSQL 18 (local, managed in pgAdmin 4). See README.md for full details.

## Current state (2026-10-19)
- Database `campus_equipment` exists on localhost:5432 (user `postgres`).
- `sql/schema.sql` and `sql/sample_data.sql` have ALREADY been run in pgAdmin. Tables, view, trigger and 3 sample loans exist.
- DO NOT run `flask --app app init-db` — tables exist, it will stop with "relation already exists".
- `sql/queries.sql` was run in pgAdmin; all queries succeed.
- `.env` was created from `.env.example`. The user must put their real PGPASSWORD in it — never print or commit `.env`.
- `.venv` has NOT been created yet; dependencies are not installed.

## Next step: get the website running
1. Confirm `.env` has a real PGPASSWORD (check it's not the placeholder; don't echo the value).
2. `python3 -m venv .venv && source .venv/bin/activate && python -m pip install -r requirements.txt`
3. `python app.py` (serves http://127.0.0.1:5001; keep it running).
4. Verify `curl -s http://127.0.0.1:5001/` and the API routes return data matching the DB (3 loans: 1 Returned, 1 Active, 1 Overdue).
