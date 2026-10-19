-- Run once in an empty campus_equipment database. No existing data is dropped.
BEGIN;
CREATE TABLE students (
    student_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    roll_number VARCHAR(30) NOT NULL UNIQUE CHECK (btrim(roll_number) <> ''),
    student_name VARCHAR(100) NOT NULL CHECK (btrim(student_name) <> ''),
    department VARCHAR(60) NOT NULL CHECK (btrim(department) <> ''),
    email VARCHAR(120) NOT NULL UNIQUE CHECK (position('@' in email) > 1)
);
CREATE TABLE categories (
    category_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    category_name VARCHAR(60) NOT NULL UNIQUE
);
CREATE TABLE equipment (
    equipment_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    asset_code VARCHAR(30) NOT NULL UNIQUE CHECK (btrim(asset_code) <> ''),
    equipment_name VARCHAR(100) NOT NULL CHECK (btrim(equipment_name) <> ''),
    category_id INTEGER NOT NULL REFERENCES categories(category_id),
    condition VARCHAR(20) NOT NULL DEFAULT 'Good'
        CHECK (condition IN ('Good','Fair','Maintenance'))
);
CREATE TABLE loans (
    loan_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(student_id),
    equipment_id INTEGER NOT NULL REFERENCES equipment(equipment_id),
    issue_date DATE NOT NULL DEFAULT CURRENT_DATE,
    due_date DATE NOT NULL CHECK (due_date >= issue_date),
    return_date DATE CHECK (return_date >= issue_date),
    notes VARCHAR(300) NOT NULL DEFAULT ''
);
-- One physical item can have only one open loan, even with concurrent requests.
CREATE UNIQUE INDEX one_open_loan_per_item ON loans(equipment_id)
    WHERE return_date IS NULL;
CREATE INDEX loans_student_idx ON loans(student_id);
CREATE TABLE loan_events (
    event_id INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    loan_id INTEGER NOT NULL REFERENCES loans(loan_id),
    event_type VARCHAR(10) NOT NULL CHECK (event_type IN ('Issued','Returned')),
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE FUNCTION log_loan_event() RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        INSERT INTO loan_events(loan_id,event_type) VALUES (NEW.loan_id,'Issued');
    ELSIF OLD.return_date IS NULL AND NEW.return_date IS NOT NULL THEN
        INSERT INTO loan_events(loan_id,event_type) VALUES (NEW.loan_id,'Returned');
    END IF;
    RETURN NEW;
END;
$$;
CREATE TRIGGER loan_event_trigger AFTER INSERT OR UPDATE ON loans
FOR EACH ROW EXECUTE FUNCTION log_loan_event();
CREATE VIEW loan_details AS
SELECT l.*, s.student_name,s.roll_number,e.asset_code,e.equipment_name,
    CASE WHEN l.return_date IS NOT NULL THEN 'Returned'
         WHEN l.due_date < CURRENT_DATE THEN 'Overdue'
         ELSE 'Active' END AS status
FROM loans l JOIN students s ON l.student_id=s.student_id
JOIN equipment e ON l.equipment_id=e.equipment_id;
COMMIT;
