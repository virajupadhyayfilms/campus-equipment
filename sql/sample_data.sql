-- Fictional demo records; run once after schema.sql.
BEGIN;
INSERT INTO categories(category_name) VALUES ('Electronics'),('Lab Equipment'),('Accessories');
INSERT INTO students(roll_number,student_name,department,email) VALUES
('IT-101','Aarav Shah','Information Technology','aarav@example.com'),
('IT-102','Diya Mehta','Information Technology','diya@example.com'),
('IT-103','Rohan Patil','Information Technology','rohan@example.com');
INSERT INTO equipment(asset_code,equipment_name,category_id,condition) VALUES
('CAM-001','Digital Camera',1,'Good'),('PRJ-001','Portable Projector',1,'Good'),
('KIT-001','Arduino Starter Kit',2,'Good'),('TRI-001','Camera Tripod',3,'Fair'),
('MIC-001','USB Microphone',1,'Good'),('MUL-001','Digital Multimeter',2,'Maintenance');
INSERT INTO loans(student_id,equipment_id,issue_date,due_date,notes) VALUES
(1,1,CURRENT_DATE-7,CURRENT_DATE-2,'Media workshop'),
(2,3,CURRENT_DATE-1,CURRENT_DATE+4,'Lab practice');
INSERT INTO loans(student_id,equipment_id,issue_date,due_date,notes) VALUES
(3,4,CURRENT_DATE-10,CURRENT_DATE-5,'Photography practice');
UPDATE loans SET return_date=CURRENT_DATE-6 WHERE loan_id=3;
COMMIT;
