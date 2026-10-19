"""Campus Equipment Lending and Return Management System (local mini-project)."""
import os
from datetime import date
from pathlib import Path
import click
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

load_dotenv()
app = Flask(__name__)
app.json.sort_keys = False
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024


def connect():
    # Hosted deployments (Vercel + Neon) supply one DATABASE_URL instead of PG* settings.
    if os.getenv('DATABASE_URL'):
        return psycopg.connect(os.environ['DATABASE_URL'], row_factory=dict_row,
                               connect_timeout=5, options='-c timezone=Asia/Kolkata')
    return psycopg.connect(
        host=os.getenv('PGHOST', 'localhost'), port=os.getenv('PGPORT', '5432'),
        dbname=os.getenv('PGDATABASE', 'campus_equipment'),
        user=os.getenv('PGUSER', 'postgres'), password=os.getenv('PGPASSWORD', ''),
        row_factory=dict_row, connect_timeout=5,
        options='-c timezone=Asia/Kolkata')


def serialize(row):
    return {k: v.isoformat() if hasattr(v, 'isoformat') else v for k, v in row.items()}


def rows(sql, params=()):
    with connect() as conn:
        return [serialize(r) for r in conn.execute(sql, params).fetchall()]


def data():
    payload = request.get_json(silent=True)
    if not isinstance(payload, dict):
        raise ValueError('Send a JSON object.')
    return payload


def field(payload, name, length):
    value = payload.get(name, '')
    if not isinstance(value, str) or not value.strip() or len(value.strip()) > length:
        raise ValueError(f'{name.replace("_", " ").capitalize()} is required (maximum {length} characters).')
    return value.strip()


def positive_id(value):
    if isinstance(value, bool):
        raise ValueError('Select a valid record.')
    try:
        if str(int(value)) != str(value) or int(value) < 1:
            raise ValueError
        return int(value)
    except (TypeError, ValueError):
        raise ValueError('Select a valid record.')


@app.errorhandler(ValueError)
def bad_input(error):
    return jsonify(error=str(error)), 400


@app.errorhandler(psycopg.IntegrityError)
def integrity(error):
    if isinstance(error, psycopg.errors.UniqueViolation):
        message = 'That record already exists, or the equipment is already on loan.'
    elif isinstance(error, psycopg.errors.ForeignKeyViolation):
        message = 'This record is linked to loan history or the selected record does not exist.'
    else:
        message = 'The entry violates a database rule. Check the dates and required fields.'
    return jsonify(error=message), 409


@app.errorhandler(psycopg.OperationalError)
def unavailable(error):
    app.logger.error('PostgreSQL connection failed; check local database configuration.')
    return jsonify(error='Cannot connect to PostgreSQL. Check your .env settings and start PostgreSQL.'), 503


@app.errorhandler(psycopg.ProgrammingError)
def database_setup_error(error):
    if isinstance(error, psycopg.errors.UndefinedTable):
        return jsonify(error='Database tables are missing. Run the init-db command from README.md.'), 503
    app.logger.error('Database query failed; inspect the local database schema.')
    return jsonify(error='A database query failed. Check that the supplied schema was initialized.'), 500


@app.get('/')
def home():
    return render_template('index.html')


@app.get('/api/data')
def all_data():
    return jsonify(
        today=rows('SELECT CURRENT_DATE AS today')[0]['today'],
        students=rows('SELECT * FROM students ORDER BY student_name'),
        categories=rows('SELECT * FROM categories ORDER BY category_name'),
        equipment=rows('''SELECT e.*,c.category_name,
            CASE WHEN e.condition='Maintenance' THEN 'Maintenance'
                 WHEN EXISTS (SELECT 1 FROM loans l WHERE l.equipment_id=e.equipment_id
                              AND l.return_date IS NULL) THEN 'On Loan'
                 ELSE 'Available' END AS status
            FROM equipment e JOIN categories c USING(category_id) ORDER BY e.asset_code'''),
        loans=rows('SELECT * FROM loan_details ORDER BY loan_id DESC'),
        events=rows('SELECT * FROM loan_events ORDER BY event_id DESC'),
        borrower_report=rows('''SELECT s.student_id,s.student_name,s.roll_number,
            COUNT(l.loan_id) AS total_loans,
            COUNT(l.loan_id) FILTER (WHERE l.return_date IS NULL) AS open_loans
            FROM students s LEFT JOIN loans l USING(student_id)
            GROUP BY s.student_id,s.student_name,s.roll_number ORDER BY s.student_name'''),
        reports=rows('''SELECT c.category_name,COUNT(e.equipment_id) AS total_items,
            COUNT(e.equipment_id) FILTER (WHERE e.condition='Maintenance') AS maintenance_items,
            COUNT(e.equipment_id) FILTER (WHERE EXISTS (SELECT 1 FROM loans l
                WHERE l.equipment_id=e.equipment_id AND l.return_date IS NULL)) AS on_loan
            FROM categories c LEFT JOIN equipment e USING(category_id)
            GROUP BY c.category_id,c.category_name ORDER BY c.category_name'''))


@app.post('/api/students')
def add_student():
    p = data()
    values = [field(p, k, n) for k, n in [('roll_number',30),('student_name',100),('department',60),('email',120)]]
    if '@' not in values[3] or '.' not in values[3].split('@')[-1]:
        raise ValueError('Enter a valid email address.')
    with connect() as conn:
        conn.execute('INSERT INTO students(roll_number,student_name,department,email) VALUES (%s,%s,%s,%s)', values)
    return jsonify(message='Student added.'), 201


@app.post('/api/categories')
def add_category():
    name = field(data(), 'category_name', 60)
    with connect() as conn:
        conn.execute('INSERT INTO categories(category_name) VALUES (%s)', (name,))
    return jsonify(message='Category added.'), 201


@app.post('/api/equipment')
def add_equipment():
    p = data()
    values = (field(p,'asset_code',30),field(p,'equipment_name',100),positive_id(p.get('category_id')),field(p,'condition',20))
    with connect() as conn:
        conn.execute('INSERT INTO equipment(asset_code,equipment_name,category_id,condition) VALUES (%s,%s,%s,%s)',values)
    return jsonify(message='Equipment added.'), 201


@app.patch('/api/equipment/<int:item_id>')
def update_equipment(item_id):
    condition = field(data(),'condition',20)
    with connect() as conn:
        item = conn.execute('SELECT equipment_id FROM equipment WHERE equipment_id=%s FOR UPDATE',(item_id,)).fetchone()
        if not item:
            return jsonify(error='Equipment not found.'),404
        active = conn.execute('SELECT 1 FROM loans WHERE equipment_id=%s AND return_date IS NULL',(item_id,)).fetchone()
        if active:
            return jsonify(error='Record the return before changing the equipment condition.'),409
        conn.execute('UPDATE equipment SET condition=%s WHERE equipment_id=%s',(condition,item_id))
    return jsonify(message='Equipment condition updated.')


@app.delete('/api/students/<int:student_id>')
def delete_student(student_id):
    with connect() as conn:
        row = conn.execute('DELETE FROM students WHERE student_id=%s RETURNING student_id',(student_id,)).fetchone()
        if not row:
            return jsonify(error='Student not found.'),404
    return jsonify(message='Student deleted.')


@app.delete('/api/equipment/<int:item_id>')
def delete_equipment(item_id):
    with connect() as conn:
        row = conn.execute('DELETE FROM equipment WHERE equipment_id=%s RETURNING equipment_id',(item_id,)).fetchone()
        if not row:
            return jsonify(error='Equipment not found.'),404
    return jsonify(message='Equipment deleted.')


@app.post('/api/loans')
def issue_item():
    p = data()
    student_id, item_id = positive_id(p.get('student_id')), positive_id(p.get('equipment_id'))
    try:
        due = date.fromisoformat(p.get('due_date',''))
    except (ValueError,TypeError):
        raise ValueError('Choose a valid due date.')
    notes = p.get('notes','')
    if not isinstance(notes,str) or len(notes) > 300:
        raise ValueError('Notes must be at most 300 characters.')
    with connect() as conn:
        today = conn.execute('SELECT CURRENT_DATE AS today').fetchone()['today']
        if due < today:
            raise ValueError('Due date cannot be before today.')
        item = conn.execute('SELECT * FROM equipment WHERE equipment_id=%s FOR UPDATE',(item_id,)).fetchone()
        if not item:
            return jsonify(error='Equipment not found.'),404
        if item['condition']=='Maintenance':
            return jsonify(error='This item is under maintenance.'),409
        if conn.execute('SELECT 1 FROM loans WHERE equipment_id=%s AND return_date IS NULL',(item_id,)).fetchone():
            return jsonify(error='This item is already on loan.'),409
        conn.execute('INSERT INTO loans(student_id,equipment_id,due_date,notes) VALUES (%s,%s,%s,%s)',(student_id,item_id,due,notes.strip()))
    return jsonify(message='Equipment issued.'),201


@app.post('/api/loans/<int:loan_id>/return')
def return_item(loan_id):
    with connect() as conn:
        loan = conn.execute('SELECT * FROM loans WHERE loan_id=%s FOR UPDATE',(loan_id,)).fetchone()
        if not loan:
            return jsonify(error='Loan not found.'),404
        if loan['return_date']:
            return jsonify(error='This loan has already been returned.'),409
        conn.execute('UPDATE loans SET return_date=CURRENT_DATE WHERE loan_id=%s',(loan_id,))
    return jsonify(message='Return recorded. Equipment is available again.')


@app.cli.command('init-db')
@click.option('--sample',is_flag=True,help='Also insert fictional sample data.')
def init_db(sample):
    """Create tables in an empty database; never drops existing tables."""
    folder = Path(__file__).parent / 'sql'
    with connect() as conn:
        conn.execute((folder/'schema.sql').read_text())
        if sample:
            conn.execute((folder/'sample_data.sql').read_text())
    click.echo('Database initialized.' + (' Sample data inserted.' if sample else ''))


if __name__ == '__main__':
    app.run(host='127.0.0.1',port=int(os.getenv('PORT','5001')),debug=False)
