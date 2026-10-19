-- Run SELECT queries in pgAdmin after initialization.
-- 1. Join and view: full borrowing history.
SELECT loan_id, student_name, equipment_name, issue_date, due_date, return_date, status
FROM loan_details ORDER BY loan_id DESC;
-- 2. Overdue loans (unreturned, due before today).
SELECT * FROM loan_details WHERE status='Overdue';
-- 3. Aggregate with LEFT JOIN: include students who have never borrowed.
SELECT s.student_name, COUNT(l.loan_id) AS total_loans
FROM students s LEFT JOIN loans l USING(student_id)
GROUP BY s.student_id, s.student_name ORDER BY total_loans DESC;
-- 4. Subquery: equipment with no active loan and not under maintenance.
SELECT * FROM equipment e WHERE condition <> 'Maintenance'
AND NOT EXISTS (SELECT 1 FROM loans l WHERE l.equipment_id=e.equipment_id
                AND l.return_date IS NULL);
-- 5. Trigger output: issue and return audit records.
SELECT * FROM loan_events ORDER BY event_id;
-- 6. Grouping and HAVING.
SELECT student_id,COUNT(*) AS borrowed FROM loans
GROUP BY student_id HAVING COUNT(*) >= 1;
-- 7. Index inspection and query plan.
EXPLAIN SELECT * FROM loans WHERE equipment_id=1 AND return_date IS NULL;
-- 8. Transaction example (rolls back, leaving the data unchanged).
BEGIN;
UPDATE equipment SET condition='Fair' WHERE asset_code='MIC-001';
ROLLBACK;
-- Optional DCL demonstration, only after an existing role has been chosen:
-- GRANT SELECT ON loan_details TO your_existing_role;
-- REVOKE SELECT ON loan_details FROM your_existing_role;
