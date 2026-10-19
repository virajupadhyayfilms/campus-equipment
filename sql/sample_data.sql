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

-- PART 2: 30 more students, 10 more equipment items and 16 more loans (fictional).
-- Safe to run on a database that already has PART 1: rows are matched by roll
-- number / asset code / notes, so running it twice does not duplicate anything.
BEGIN;
INSERT INTO students(roll_number,student_name,department,email) VALUES
('IT-104','Ishaan Kulkarni','Information Technology','ishaan.k@example.com'),
('IT-105','Ananya Iyer','Information Technology','ananya.i@example.com'),
('IT-106','Kabir Desai','Information Technology','kabir.d@example.com'),
('IT-107','Meera Nair','Information Technology','meera.n@example.com'),
('IT-108','Arjun Joshi','Information Technology','arjun.j@example.com'),
('IT-109','Saanvi Rao','Information Technology','saanvi.r@example.com'),
('IT-110','Vihaan Gupta','Information Technology','vihaan.g@example.com'),
('CE-201','Riya Kapoor','Computer Engineering','riya.k@example.com'),
('CE-202','Aditya Menon','Computer Engineering','aditya.m@example.com'),
('CE-203','Kavya Reddy','Computer Engineering','kavya.r@example.com'),
('CE-204','Neil Fernandes','Computer Engineering','neil.f@example.com'),
('CE-205','Tara Bhatt','Computer Engineering','tara.b@example.com'),
('CE-206','Yash Pawar','Computer Engineering','yash.p@example.com'),
('EXTC-301','Aisha Khan','Electronics & Telecommunication','aisha.k@example.com'),
('EXTC-302','Dev Malhotra','Electronics & Telecommunication','dev.m@example.com'),
('EXTC-303','Pooja Shetty','Electronics & Telecommunication','pooja.s@example.com'),
('EXTC-304','Rahul Verma','Electronics & Telecommunication','rahul.v@example.com'),
('EXTC-305','Nisha Pillai','Electronics & Telecommunication','nisha.p@example.com'),
('EXTC-306','Siddharth Jain','Electronics & Telecommunication','siddharth.j@example.com'),
('ME-401','Omkar Sawant','Mechanical Engineering','omkar.s@example.com'),
('ME-402','Sneha Chavan','Mechanical Engineering','sneha.c@example.com'),
('ME-403','Harsh Thakur','Mechanical Engineering','harsh.t@example.com'),
('ME-404','Priya Deshmukh','Mechanical Engineering','priya.d@example.com'),
('ME-405','Kunal Shinde','Mechanical Engineering','kunal.s@example.com'),
('AIDS-501','Zara Sheikh','AI & Data Science','zara.s@example.com'),
('AIDS-502','Aryan Mishra','AI & Data Science','aryan.m@example.com'),
('AIDS-503','Ira Banerjee','AI & Data Science','ira.b@example.com'),
('AIDS-504','Manav Sethi','AI & Data Science','manav.s@example.com'),
('AIDS-505','Diya Krishnan','AI & Data Science','diya.k@example.com'),
('AIDS-506','Rohan Agarwal','AI & Data Science','rohan.a@example.com')
ON CONFLICT DO NOTHING;
INSERT INTO equipment(asset_code,equipment_name,category_id,condition)
SELECT v.asset_code,v.equipment_name,c.category_id,v.condition FROM (VALUES
('CAM-002','DSLR Camera','Electronics','Good'),
('PRJ-002','Mini Projector','Electronics','Fair'),
('LAP-001','Laptop','Electronics','Good'),
('TAB-001','Graphics Tablet','Electronics','Good'),
('KIT-002','Raspberry Pi Kit','Lab Equipment','Good'),
('OSC-001','Digital Oscilloscope','Lab Equipment','Good'),
('SOL-001','Soldering Station','Lab Equipment','Maintenance'),
('TRI-002','Video Tripod','Accessories','Good'),
('LGT-001','LED Light Panel','Accessories','Good'),
('HDM-001','HDMI Adapter Kit','Accessories','Good')
) AS v(asset_code,equipment_name,category_name,condition)
JOIN categories c ON c.category_name=v.category_name
ON CONFLICT DO NOTHING;
-- Loans are inserted as open loans (the trigger logs "Issued"), then the
-- returned ones are updated (the trigger logs "Returned"). Day offsets are
-- relative to today: positive = days ago, negative = days ahead.
CREATE TEMP TABLE seed_loans(roll TEXT,asset TEXT,issued INT,due INT,returned INT,note TEXT) ON COMMIT DROP;
INSERT INTO seed_loans VALUES
('IT-104','PRJ-001',20,17,17,'Seminar presentation'),
('IT-105','CAM-002',15,10,11,'College fest coverage'),
('CE-201','LAP-001',12,5,6,'Hackathon'),
('CE-202','KIT-002',9,2,3,'IoT mini-project'),
('EXTC-301','OSC-001',14,7,7,'Signals lab'),
('ME-401','TRI-002',8,4,4,'Workshop recording'),
('AIDS-501','TAB-001',18,11,12,'UI design assignment'),
('IT-106','MIC-001',6,3,3,'Podcast club'),
('IT-107','CAM-002',4,-3,NULL,'Department photoshoot'),
('CE-203','LAP-001',5,-2,NULL,'Project demo'),
('EXTC-302','OSC-001',6,1,NULL,'Circuit testing'),
('ME-402','LGT-001',3,-4,NULL,'Video shoot lighting'),
('AIDS-502','KIT-002',2,1,NULL,'Sensor data project'),
('IT-108','PRJ-002',2,-5,NULL,'Club meeting'),
('CE-204','HDM-001',1,-6,NULL,'Lab presentation'),
('IT-104','TRI-002',3,1,NULL,'Photo walk');
-- Returned loans first, so each item is free before its next loan is issued.
INSERT INTO loans(student_id,equipment_id,issue_date,due_date,notes)
SELECT s.student_id,e.equipment_id,CURRENT_DATE-v.issued,CURRENT_DATE-v.due,v.note
FROM seed_loans v JOIN students s ON s.roll_number=v.roll
JOIN equipment e ON e.asset_code=v.asset
WHERE v.returned IS NOT NULL AND NOT EXISTS (SELECT 1 FROM loans l WHERE l.notes=v.note);
UPDATE loans l SET return_date=CURRENT_DATE-v.returned
FROM seed_loans v WHERE l.notes=v.note AND v.returned IS NOT NULL AND l.return_date IS NULL;
INSERT INTO loans(student_id,equipment_id,issue_date,due_date,notes)
SELECT s.student_id,e.equipment_id,CURRENT_DATE-v.issued,CURRENT_DATE-v.due,v.note
FROM seed_loans v JOIN students s ON s.roll_number=v.roll
JOIN equipment e ON e.asset_code=v.asset
WHERE v.returned IS NULL AND NOT EXISTS (SELECT 1 FROM loans l WHERE l.notes=v.note);
COMMIT;
