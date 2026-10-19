# Campus Equipment Lending and Return Management System

A DBMS mini-project for SY B.Tech IT, Semester III. The interface uses HTML, CSS, and JavaScript. Flask receives browser requests and executes SQL against PostgreSQL using Psycopg. Records are stored in PostgreSQL, not browser storage.

## Start Here — Mac

You need Python 3.10 or later and a running PostgreSQL installation. pgAdmin is a database management tool; the PostgreSQL server must also be running.

1. Extract this ZIP. Open the `equipment_project` folder in VS Code.
2. In pgAdmin, connect to your local PostgreSQL server. Right-click **Databases → Create → Database**. Name it `campus_equipment` and click Save. Use a new empty database.
3. Open **Terminal → New Terminal** in VS Code. Check that the terminal is inside `equipment_project`, then run:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

4. Open `.env` in VS Code. Enter the same PostgreSQL username, password, host, and port that work in pgAdmin. `postgres` and `5432` are common values, but your installation may use different ones. Keep `PGDATABASE=campus_equipment`. Do not share your completed `.env`.
5. Initialize the new database with fictional sample records:

```bash
python -m flask --app app init-db --sample
```

Run this once. If tables already exist, it intentionally stops rather than deleting your work. To start without fictional records, omit `--sample`. For an entirely separate fresh demonstration, create a different empty database and update `PGDATABASE`.

6. Start the application:

```bash
python app.py
```

7. Open **http://127.0.0.1:5001** in Chrome or Safari. Keep the terminal running while you use it. Press Control+C to stop.

On later runs, only activate `.venv` and run `python app.py`. Records remain in PostgreSQL after a restart. If port 5001 is busy, change `PORT` in `.env` to 5002 and use that port in the browser.

## What to Demonstrate

1. Overview displays inventory, availability, active loans, and overdue loans.
2. Equipment shows one row per physical item. Add a category, then add an item with its own asset code.
3. Students lets you add a borrower.
4. Issue Equipment connects a student to an available item and a due date. The item becomes On Loan.
5. A second issue for the same item is rejected by the backend and a database unique index.
6. Loans & Returns shows complete history. Record Return sets today's return date. The item becomes available again.
7. A second return is rejected. Items under maintenance cannot be issued.
8. Change a returned item's condition using Equipment → Condition. A student or item with loan history cannot be deleted; foreign keys preserve that history.
9. Reports show category totals and borrowing totals. Filters and searches help find records.
10. Open `sql/queries.sql` in pgAdmin's Query Tool to demonstrate joins, aggregates, subqueries, views, a transaction, and trigger records.

An item due today is Active. It becomes Overdue the following day if not returned. Overdue status is calculated when queried, so there is no manually maintained overdue flag.

## Files

- `app.py`: Flask routes, input checks, and SQL operations.
- `templates/index.html`: application page.
- `static/style.css`: styling and responsive layout.
- `static/app.js`: form submissions, table rendering, filtering, and fetch requests.
- `sql/schema.sql`: tables, keys, constraints, indexes, view, and trigger.
- `sql/sample_data.sql`: fictional sample records with dates relative to database today.
- `sql/queries.sql`: SQL queries to explain in the demonstration.
- `docs/ER_Diagram.svg`: ER diagram; open it in a browser.
- `docs/Database_Design.md`: problem statement, objectives, schema, and DBMS concepts.
- `tests/test_app.py`: optional integration tests for a disposable database.

## Connection Flow

Browser form → JavaScript fetch → Flask route → parameterized SQL → PostgreSQL → JSON response → updated table.

For example, the Issue Equipment form calls `POST /api/loans`. Flask locks the equipment row, checks availability and the due date, inserts the loan, and commits. The database trigger inserts an Issued event in the same transaction. If an insert fails, the transaction is rolled back.

## Common Problems

- **Cannot connect:** start PostgreSQL and check `.env` against pgAdmin's Connection settings. The database must already exist.
- **Password authentication failed:** correct `PGUSER` or `PGPASSWORD`; your Mac password may differ from the PostgreSQL password.
- **Relation does not exist:** run `init-db` once against the same database configured in `.env`.
- **Relation already exists:** the database was initialized. Start `python app.py`; do not initialize it again.
- **Record linked to history:** this is intentional. You can return a loan, but deleting its equipment/student would remove historical context.
- **Page says connecting:** open the page through Flask's URL, not by double-clicking `index.html`.

## Scope and Testing

This is a single local equipment-desk application. Login, payments, reservations, and email notifications are outside this version's scope. It binds to your own computer at `127.0.0.1`.

Source syntax and Flask routes are checked during development. Database/API integration checks were run against an embedded PostgreSQL test runtime; these are not a substitute for running the final demonstration against your installed PostgreSQL server. Full visual browser testing was not available in the build environment.

To run the optional tests on your Mac, create a **separate, empty, disposable** database (for example `campus_equipment_test`). The tests create their own schema and then remove it; they do not reset your app tables.

```bash
python -m pip install pytest
TEST_DATABASE_URL='postgresql://YOUR_USER:YOUR_PASSWORD@localhost:5432/campus_equipment_test' python -m pytest -q
```

Use URL-encoded credentials in this optional test URL if the password contains reserved characters. This URL is not needed for the normal `.env` setup.

## References

- Flask: https://flask.palletsprojects.com/en/stable/
- Psycopg: https://www.psycopg.org/psycopg3/docs/basic/usage.html
- PostgreSQL: https://www.postgresql.org/docs/current/
