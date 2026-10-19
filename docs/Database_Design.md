# Database Design

## Problem Definition

Colleges need to track equipment borrowed by students, availability, due dates, and returns. Manual records can lead to duplicate issuing and difficulty identifying overdue items. The system stores student, equipment, and loan records in a centralized relational database and provides a connected interface for issuing equipment, recording returns, and viewing history.

## Objectives

- Maintain student and physical equipment records.
- Prevent the same item from being issued while already on loan.
- Track issue dates, due dates, returns, and overdue items.
- Preserve borrowing history and provide summary reports.

## Tables and Relationships

| Table | Primary Key | Foreign Keys | Other Attributes |
| --- | --- | --- | --- |
| students | student_id | — | roll_number (unique), student_name, department, email (unique) |
| categories | category_id | — | category_name (unique) |
| equipment | equipment_id | category_id → categories | asset_code (unique), equipment_name, condition |
| loans | loan_id | student_id → students; equipment_id → equipment | issue_date, due_date, return_date, notes |
| loan_events | event_id | loan_id → loans | event_type, recorded_at |

A category has many equipment items. A student can have many loans. An item can have many historical loans, but at most one open loan. Each loan has an Issued event and, once returned, a Returned event.

## Design and Normalization

Each row represents one entity or transaction, and each field stores one value (1NF). Primary keys are single attributes, so no partial dependency on part of a composite key occurs (2NF). Names and category descriptions are stored in their own tables rather than repeated in loan records, avoiding transitive dependencies (3NF). This is based on the stated business rules, not a claim that every possible dependency has been discovered.

Availability is derived from condition and whether an open loan exists. Loan status is derived from the due date and return date. These values are not redundantly stored in multiple tables.

## DBMS Concepts Demonstrated

- Primary and foreign keys; NOT NULL, UNIQUE, and CHECK constraints.
- INSERT, SELECT, UPDATE, and DELETE.
- INNER JOIN, LEFT JOIN, aggregate functions, GROUP BY, HAVING, and EXISTS subqueries.
- `loan_details` view combines loan, student, and equipment data.
- `log_loan_event()` PL/pgSQL trigger function records issuing and returns.
- Indexes on student references and open equipment loans.
- Transactions commit valid changes and roll back failures.
- `SELECT ... FOR UPDATE` serializes issuing requests for the same equipment. A partial unique index is the final database-level safeguard against two open loans for one item.

The application does not claim to implement recovery algorithms itself. PostgreSQL provides transaction and recovery mechanisms. DCL examples in `queries.sql` are optional demonstrations against an existing role; the UI does not implement user accounts.

## Required Operations

The app inserts borrowers and equipment, reads inventory and loan history, updates conditions and return dates, and deletes records that have no loan history. Foreign keys reject deletion of referenced records.

Dates are calendar dates. A due date must be on or after the issue date. A return date cannot precede the issue date. The app records returns using the database's current date.

## Conclusion

The system connects a simple interface to a relational database and demonstrates how constraints, joins, transactions, and triggers help keep equipment lending records consistent.
