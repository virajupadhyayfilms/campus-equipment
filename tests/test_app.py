"""Integration tests. Set TEST_DATABASE_URL to a disposable PostgreSQL database."""
import os
import sys
import uuid
from pathlib import Path
from datetime import date, timedelta
import pytest
import psycopg
from psycopg import sql
from psycopg.rows import dict_row
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import app as module

@pytest.fixture
def client(monkeypatch):
    url = os.getenv('TEST_DATABASE_URL')
    if not url:
        pytest.skip('Set TEST_DATABASE_URL to run integration tests.')
    schema = 'equipment_test_' + uuid.uuid4().hex
    with psycopg.connect(url) as conn:
        conn.execute(sql.SQL('CREATE SCHEMA {}').format(sql.Identifier(schema)))
    shared = psycopg.connect(url,row_factory=dict_row,cursor_factory=psycopg.ClientCursor)
    shared.execute(sql.SQL('SET search_path TO {}').format(sql.Identifier(schema)))
    shared.execute("SET TIME ZONE 'Asia/Kolkata'")
    shared.commit()
    class TestConnection:
        # Reuse one connection while retaining real transaction commit/rollback.
        def __enter__(self):
            return shared
        def __exit__(self, exc_type, exc, traceback):
            shared.rollback() if exc_type else shared.commit()
    def connect_test():
        return TestConnection()
    monkeypatch.setattr(module, 'connect', connect_test)
    folder=Path(module.__file__).parent/'sql'
    with connect_test() as conn:
        conn.execute((folder/'schema.sql').read_text())
        conn.execute((folder/'sample_data.sql').read_text())
    module.app.config.update(TESTING=True)
    yield module.app.test_client()
    shared.close()
    with psycopg.connect(url) as conn:
        conn.execute(sql.SQL('DROP SCHEMA {} CASCADE').format(sql.Identifier(schema)))


def issue(client, equipment=2, **extra):
    payload=dict(student_id=1,equipment_id=equipment,due_date=(date.today()+timedelta(days=3)).isoformat())
    payload.update(extra)
    return client.post('/api/loans',json=payload)


def test_full_issue_return_and_history(client):
    assert client.get('/').status_code==200
    assert client.get('/static/app.js').status_code==200
    assert issue(client).status_code==201
    assert issue(client).status_code==409
    state=client.get('/api/data').get_json()
    loan=next(l for l in state['loans'] if l['equipment_id']==2)
    assert loan['status']=='Active'
    assert client.post(f"/api/loans/{loan['loan_id']}/return").status_code==200
    assert client.post(f"/api/loans/{loan['loan_id']}/return").status_code==409
    state=client.get('/api/data').get_json()
    assert next(e for e in state['equipment'] if e['equipment_id']==2)['status']=='Available'
    assert [e['event_type'] for e in reversed(state['events']) if e['loan_id']==loan['loan_id']]==['Issued','Returned']
    assert issue(client).status_code==201  # same item can be reissued after return


def test_reject_bad_issues_and_preserve_history(client):
    assert issue(client,equipment=6).status_code==409
    assert issue(client,due_date='2020-01-01').status_code==400
    assert issue(client,student_id=9999).status_code==409
    assert issue(client,equipment=9999).status_code==404
    assert client.delete('/api/students/1').status_code==409
    assert client.delete('/api/equipment/1').status_code==409
    assert client.patch('/api/equipment/1',json={'condition':'Maintenance'}).status_code==409
    assert client.post('/api/loans/9999/return').status_code==404
    state=client.get('/api/data').get_json()
    assert any(l['status']=='Overdue' for l in state['loans'])


def test_add_update_delete_and_validation(client):
    assert client.post('/api/students',json={'roll_number':'IT-X','student_name':"O'Neil <student>",'department':'IT','email':'oneil@example.com'}).status_code==201
    assert client.post('/api/students',json={'roll_number':'IT-X','student_name':'Duplicate','department':'IT','email':'different@example.com'}).status_code==409
    assert client.post('/api/students',json={'roll_number':'','student_name':'A','department':'IT','email':'bad'}).status_code==400
    assert client.post('/api/equipment',json={'asset_code':'TST-001','equipment_name':'Test Kit','category_id':2,'condition':'Good'}).status_code==201
    state=client.get('/api/data').get_json()
    equipment=next(e for e in state['equipment'] if e['asset_code']=='TST-001')
    student=next(s for s in state['students'] if s['roll_number']=='IT-X')
    assert client.patch(f"/api/equipment/{equipment['equipment_id']}",json={'condition':'Maintenance'}).status_code==200
    assert client.patch(f"/api/equipment/{equipment['equipment_id']}",json={'condition':'Broken'}).status_code==409
    assert client.delete(f"/api/equipment/{equipment['equipment_id']}").status_code==200
    assert client.delete(f"/api/students/{student['student_id']}").status_code==200
    assert client.post('/api/categories',json={'category_name':'Sports'}).status_code==201
    assert client.post('/api/loans',json=[]).status_code==400


def test_database_unique_and_date_constraints(client):
    # Bypass Flask to verify that SQL itself rejects duplicate open loans.
    with pytest.raises(psycopg.errors.UniqueViolation):
        with module.connect() as conn:
            conn.execute('INSERT INTO loans(student_id,equipment_id,due_date) VALUES (1,1,CURRENT_DATE+2)')
    with pytest.raises(psycopg.errors.CheckViolation):
        with module.connect() as conn:
            conn.execute('INSERT INTO loans(student_id,equipment_id,due_date) VALUES (1,2,CURRENT_DATE-1)')
    with module.connect() as conn:
        assert conn.execute('SELECT COUNT(*) AS n FROM loans').fetchone()['n']==3
