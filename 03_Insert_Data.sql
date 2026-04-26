-- =============================================================
-- HOSPITAL MANAGEMENT SYSTEM
-- DML Script: Data Population (Realistic Data)
-- =============================================================
USE hms_db;

-- -------------------------------------------------------------
-- DEPARTMENT (10 rows)
-- -------------------------------------------------------------
INSERT INTO DEPARTMENT (dept_name, location, phone_ext, description) VALUES
('Cardiology',        'Block A – 2nd Floor', '1001', 'Heart and cardiovascular care'),
('Neurology',         'Block A – 3rd Floor', '1002', 'Brain and nervous system'),
('Orthopedics',       'Block B – 1st Floor', '1003', 'Bones, joints and muscles'),
('Pediatrics',        'Block B – 2nd Floor', '1004', 'Children healthcare (0-18 yrs)'),
('Oncology',          'Block C – 1st Floor', '1005', 'Cancer diagnosis and treatment'),
('Emergency',         'Ground Floor',        '1006', '24/7 emergency services'),
('Radiology',         'Block C – 2nd Floor', '1007', 'Imaging and diagnostics'),
('General Surgery',   'Block D – 1st Floor', '1008', 'Surgical procedures'),
('Gynecology',        'Block D – 2nd Floor', '1009', 'Women healthcare'),
('Dermatology',       'Block E – 1st Floor', '1010', 'Skin, hair and nails');

-- -------------------------------------------------------------
-- STAFF (20 rows — mix of Doctors, Nurses, etc.)
-- -------------------------------------------------------------
INSERT INTO STAFF (first_name, last_name, staff_type, phone, email, hire_date, salary, shift) VALUES
('Ahmed',    'Khan',      'Doctor',      '03001234501', 'ahmed.khan@hms.pk',      '2018-03-15', 250000.00, 'Morning'),
('Sara',     'Malik',     'Doctor',      '03001234502', 'sara.malik@hms.pk',      '2019-06-01', 230000.00, 'Morning'),
('Bilal',    'Hussain',   'Doctor',      '03001234503', 'bilal.hussain@hms.pk',   '2017-01-20', 270000.00, 'Morning'),
('Zara',     'Qureshi',   'Doctor',      '03001234504', 'zara.qureshi@hms.pk',    '2020-09-10', 220000.00, 'Evening'),
('Omar',     'Sheikh',    'Doctor',      '03001234505', 'omar.sheikh@hms.pk',     '2016-05-05', 300000.00, 'Morning'),
('Hina',     'Baig',      'Doctor',      '03001234506', 'hina.baig@hms.pk',       '2021-02-14', 210000.00, 'Evening'),
('Usman',    'Raza',      'Doctor',      '03001234507', 'usman.raza@hms.pk',      '2015-11-30', 320000.00, 'Morning'),
('Ayesha',   'Farooq',    'Doctor',      '03001234508', 'ayesha.farooq@hms.pk',   '2022-07-01', 200000.00, 'Morning'),
('Kamran',   'Iqbal',     'Doctor',      '03001234509', 'kamran.iqbal@hms.pk',    '2019-03-20', 240000.00, 'Night'),
('Fatima',   'Siddiqui',  'Doctor',      '03001234510', 'fatima.sid@hms.pk',      '2020-01-15', 225000.00, 'Morning'),
('Nadia',    'Ali',       'Nurse',       '03001234511', 'nadia.ali@hms.pk',       '2019-08-01', 80000.00,  'Morning'),
('Sana',     'Rehman',    'Nurse',       '03001234512', 'sana.rehman@hms.pk',     '2020-03-10', 75000.00,  'Evening'),
('Rabia',    'Javed',     'Nurse',       '03001234513', 'rabia.javed@hms.pk',     '2021-05-20', 78000.00,  'Night'),
('Asif',     'Nawaz',     'Nurse',       '03001234514', 'asif.nawaz@hms.pk',      '2018-12-01', 82000.00,  'Morning'),
('Maria',    'Akhtar',    'Nurse',       '03001234515', 'maria.akhtar@hms.pk',    '2022-01-10', 73000.00,  'Evening'),
('Tariq',    'Mehmood',   'Technician',  '03001234516', 'tariq.tech@hms.pk',      '2017-06-15', 65000.00,  'Morning'),
('Imran',    'Ghani',     'Technician',  '03001234517', 'imran.ghani@hms.pk',     '2020-09-01', 60000.00,  'Evening'),
('Zahid',    'Butt',      'Admin',       '03001234518', 'zahid.butt@hms.pk',      '2016-02-28', 90000.00,  'Morning'),
('Samina',   'Cheema',    'Admin',       '03001234519', 'samina.cheema@hms.pk',   '2018-07-01', 85000.00,  'Morning'),
('Adeel',    'Chaudhry',  'Technician',  '03001234520', 'adeel.ch@hms.pk',        '2021-11-15', 62000.00,  'Night');

-- -------------------------------------------------------------
-- DOCTOR (10 rows — staff_id 1–10)
-- -------------------------------------------------------------
INSERT INTO DOCTOR (staff_id, dept_id, specialization, license_number, consultation_fee, available_days) VALUES
(1,  1, 'Interventional Cardiology',  'PMDC-2018-001', 3000.00, 'Mon,Tue,Wed,Thu'),
(2,  2, 'Clinical Neurology',          'PMDC-2019-002', 2800.00, 'Mon,Wed,Fri'),
(3,  3, 'Orthopedic Surgery',          'PMDC-2017-003', 3200.00, 'Tue,Thu,Sat'),
(4,  4, 'Neonatology',                 'PMDC-2020-004', 2500.00, 'Mon,Tue,Thu,Fri'),
(5,  5, 'Medical Oncology',            'PMDC-2016-005', 4000.00, 'Mon,Wed,Fri'),
(6,  6, 'Emergency Medicine',          'PMDC-2021-006', 2000.00, 'Mon,Tue,Wed,Thu,Fri'),
(7,  8, 'General Surgery',             'PMDC-2015-007', 3500.00, 'Mon,Tue,Thu,Sat'),
(8,  9, 'Obstetrics & Gynecology',     'PMDC-2022-008', 2700.00, 'Mon,Wed,Fri'),
(9,  7, 'Interventional Radiology',    'PMDC-2019-009', 2200.00, 'Tue,Thu'),
(10, 10, 'Clinical Dermatology',       'PMDC-2020-010', 2300.00, 'Mon,Wed,Sat');

-- -------------------------------------------------------------
-- NURSE (5 rows — staff_id 11–15)
-- -------------------------------------------------------------
INSERT INTO NURSE (staff_id, ward_assignment, certification) VALUES
(11, 'Cardiology Ward',  'BScN – Punjab University 2018'),
(12, 'Neurology Ward',   'RN – Dow University 2019'),
(13, 'ICU',              'Critical Care Nurse – AKU 2021'),
(14, 'Pediatrics Ward',  'BScN – KEMU 2017'),
(15, 'Surgery Ward',     'RN – NUMS 2021');

-- -------------------------------------------------------------
-- PATIENT (20 rows)
-- -------------------------------------------------------------
INSERT INTO PATIENT (first_name, last_name, date_of_birth, gender, phone, email, address, blood_group) VALUES
('Ali',        'Hassan',    '1985-03-12', 'Male',   '03101111001', 'ali.h@gmail.com',      'House 12 St 4 Lahore',     'B+'),
('Mariam',     'Tahir',     '1992-07-25', 'Female', '03101111002', 'mariam.t@gmail.com',   'Flat 5 DHA Phase 6 Karachi','A+'),
('Junaid',     'Mirza',     '1978-11-05', 'Male',   '03101111003', 'junaid.m@gmail.com',   '23 Garden Town Lahore',    'O+'),
('Sobia',      'Anwar',     '2001-01-18', 'Female', '03101111004', 'sobia.a@gmail.com',    '7 Satellite Town Rawalpindi','AB+'),
('Hamid',      'Chaudhry',  '1965-09-30', 'Male',   '03101111005', 'hamid.c@gmail.com',    '88 Gulberg III Lahore',    'O-'),
('Rida',       'Zafar',     '1998-04-14', 'Female', '03101111006', 'rida.z@gmail.com',     '45 F-11 Islamabad',        'B-'),
('Waqas',      'Aslam',     '1990-12-22', 'Male',   '03101111007', 'waqas.a@gmail.com',    'House 3 Johar Town Lahore','A-'),
('Uzma',       'Khalid',    '1975-06-08', 'Female', '03101111008', 'uzma.k@gmail.com',     '12 Clifton Karachi',       'AB-'),
('Faisal',     'Nawaz',     '2005-02-17', 'Male',   '03101111009', 'faisal.n@gmail.com',   '67 G-9 Islamabad',         'A+'),
('Noor',       'Bukhari',   '1988-08-03', 'Female', '03101111010', 'noor.b@gmail.com',     '2 Model Town Lahore',      'O+'),
('Shahzad',    'Abbasi',    '1972-05-20', 'Male',   '03101111011', 'shahzad.a@gmail.com',  '34 Hayatabad Peshawar',    'B+'),
('Huma',       'Rashid',    '1995-10-11', 'Female', '03101111012', 'huma.r@gmail.com',     '8 Cantt Rawalpindi',       'O-'),
('Nasir',      'Gillani',   '1960-03-07', 'Male',   '03101111013', 'nasir.g@gmail.com',    '100 Civil Lines Lahore',   'A+'),
('Amna',       'Sabir',     '2003-12-25', 'Female', '03101111014', 'amna.s@gmail.com',     '19 Askari 10 Lahore',      'B+'),
('Tariq',      'Lodhi',     '1982-07-14', 'Male',   '03101111015', 'tariq.l@gmail.com',    '55 PECHS Karachi',         'AB+'),
('Shabana',    'Parveen',   '1970-09-28', 'Female', '03101111016', 'shabana.p@gmail.com',  '3 Bahria Town Lahore',     'O+'),
('Danish',     'Umer',      '1999-04-04', 'Male',   '03101111017', 'danish.u@gmail.com',   '21 Cavalry Ground Lahore', 'A-'),
('Komal',      'Pervaiz',   '2008-06-19', 'Female', '03101111018', 'komal.p@gmail.com',    '6 DHA Phase 5 Lahore',     'B-'),
('Rehan',      'Saeed',     '1955-01-30', 'Male',   '03101111019', 'rehan.s@gmail.com',    '77 Saddar Karachi',        'O+'),
('Lubna',      'Arif',      '1987-11-09', 'Female', '03101111020', 'lubna.a@gmail.com',    '14 F-8 Islamabad',         'AB+');

-- -------------------------------------------------------------
-- ROOM (20 rows)
-- -------------------------------------------------------------
INSERT INTO ROOM (room_number, room_type, dept_id, capacity, daily_charge, status) VALUES
('A-101', 'General',    1, 4, 3000.00, 'Available'),
('A-102', 'Private',    1, 1, 8000.00, 'Available'),
('A-201', 'ICU',        2, 2, 15000.00,'Occupied'),
('A-202', 'General',    2, 4, 3000.00, 'Available'),
('B-101', 'General',    3, 4, 3000.00, 'Occupied'),
('B-102', 'Private',    3, 1, 8000.00, 'Available'),
('B-201', 'General',    4, 6, 2500.00, 'Available'),
('B-202', 'ICU',        4, 2, 15000.00,'Available'),
('C-101', 'General',    5, 4, 3000.00, 'Available'),
('C-102', 'Private',    5, 1, 8000.00, 'Occupied'),
('G-001', 'Emergency',  6, 8, 5000.00, 'Occupied'),
('G-002', 'Emergency',  6, 8, 5000.00, 'Available'),
('C-201', 'General',    7, 4, 3000.00, 'Available'),
('D-101', 'Private',    8, 1, 8000.00, 'Available'),
('D-102', 'ICU',        8, 2, 15000.00,'Available'),
('D-201', 'General',    9, 4, 3000.00, 'Available'),
('D-202', 'Private',    9, 1, 8000.00, 'Occupied'),
('E-101', 'General',   10, 4, 3000.00, 'Available'),
('A-301', 'General',      1, 2, 3000.00, 'Maintenance'),
('B-301', 'General',    3, 4, 3000.00, 'Available');

-- -------------------------------------------------------------
-- APPOINTMENT (20 rows)
-- -------------------------------------------------------------
INSERT INTO APPOINTMENT (patient_id, doctor_id, appointment_date, appointment_time, reason, status, notes) VALUES
(1,  1, '2026-04-01', '09:00:00', 'Chest pain evaluation',        'Completed', 'ECG normal; stress test ordered'),
(2,  2, '2026-04-02', '10:30:00', 'Frequent headaches',           'Completed', 'MRI recommended'),
(3,  3, '2026-04-03', '11:00:00', 'Knee pain',                    'Completed', 'X-ray shows early arthritis'),
(4,  4, '2026-04-05', '09:30:00', 'Child vaccination follow-up',  'Completed', 'All vaccines up to date'),
(5,  5, '2026-04-07', '14:00:00', 'Cancer screening',             'Completed', 'Biopsy ordered'),
(6,  6, '2026-04-08', '08:00:00', 'Acute abdominal pain',         'Completed', 'Appendix suspected — surgery scheduled'),
(7,  7, '2026-04-10', '11:30:00', 'Pre-surgical consultation',    'Completed', 'Surgery approved'),
(8,  8, '2026-04-12', '10:00:00', 'Prenatal check-up',            'Completed', '28 weeks — normal'),
(9,  9, '2026-04-14', '13:00:00', 'CT scan follow-up',            'Completed', 'Results reviewed'),
(10,10, '2026-04-15', '09:00:00', 'Skin rash examination',        'Completed', 'Eczema diagnosed'),
(11, 1, '2026-04-16', '10:00:00', 'Blood pressure check',         'Completed', 'Medication adjusted'),
(12, 2, '2026-04-17', '11:00:00', 'Migraine consultation',        'Scheduled', NULL),
(13, 5, '2026-04-18', '14:30:00', 'Chemotherapy follow-up',       'Scheduled', NULL),
(14, 3, '2026-04-19', '09:00:00', 'Fracture recovery check',      'Scheduled', NULL),
(15, 7, '2026-04-20', '10:30:00', 'Post-op follow-up',            'Scheduled', NULL),
(16, 8, '2026-04-21', '11:00:00', 'Gynecology annual exam',       'Scheduled', NULL),
(17, 4, '2026-04-22', '09:30:00', 'Child fever and cold',         'Scheduled', NULL),
(18,10, '2026-04-23', '10:00:00', 'Acne treatment follow-up',     'Scheduled', NULL),
(19, 1, '2026-04-24', '14:00:00', 'Hypertension management',      'Cancelled', 'Patient no-show'),
(20, 6, '2026-04-25', '08:30:00', 'Emergency consultation',       'Completed', 'Stabilised');

-- -------------------------------------------------------------
-- ADMISSION (10 rows — active and discharged)
-- -------------------------------------------------------------
INSERT INTO ADMISSION (patient_id, room_id, admit_date, discharge_date, diagnosis, attending_doctor, status) VALUES
(5,  10, '2026-04-07', '2026-04-14', 'Lung carcinoma – Stage II',       5, 'Discharged'),
(6,  11, '2026-04-08', '2026-04-11', 'Acute appendicitis',              6, 'Discharged'),
(3,  5,  '2026-04-03', '2026-04-08', 'Severe knee injury',              3, 'Discharged'),
(1,  1,  '2026-04-10', NULL,         'Unstable angina',                 1, 'Active'),
(11, 3,  '2026-04-11', NULL,         'Hypertensive crisis',             1, 'Active'),
(13, 9,  '2026-04-12', NULL,         'Colon cancer – chemotherapy',     5, 'Active'),
(20, 11, '2026-04-25', NULL,         'Trauma – road accident',          6, 'Active'),
(8,  17, '2026-04-12', '2026-04-17', 'Labour and delivery',             8, 'Discharged'),
(7,  14, '2026-04-10', '2026-04-13', 'Hernia repair surgery',           7, 'Discharged'),
(15, 14, '2026-04-20', NULL,         'Post-op appendectomy care',       7, 'Active');

-- -------------------------------------------------------------
-- BILLING (10 rows)
-- -------------------------------------------------------------
INSERT INTO BILLING (patient_id, admission_id, total_amount, paid_amount, bill_date, payment_status, payment_method) VALUES
(5,  1, 155000.00, 155000.00, '2026-04-14', 'Paid',    'Insurance'),
(6,  2,  48000.00,  48000.00, '2026-04-11', 'Paid',    'Card'),
(3,  3,  39000.00,  20000.00, '2026-04-08', 'Partial', 'Cash'),
(8,  8,  62000.00,  62000.00, '2026-04-17', 'Paid',    'Card'),
(7,  9,  29000.00,  29000.00, '2026-04-13', 'Paid',    'Cash'),
(1,  4,  90000.00,  30000.00, '2026-04-26', 'Partial', 'Card'),
(11, 5,  75000.00,       0.00,'2026-04-26', 'Pending', NULL),
(13, 6, 120000.00,  50000.00, '2026-04-26', 'Partial', 'Insurance'),
(2,  NULL, 2800.00, 2800.00,  '2026-04-02', 'Paid',    'Cash'),
(4,  NULL, 2500.00, 2500.00,  '2026-04-05', 'Paid',    'Card');

-- -------------------------------------------------------------
-- MEDICINE (20 rows)
-- -------------------------------------------------------------
INSERT INTO MEDICINE (medicine_name, generic_name, category, unit_price, stock_quantity, manufacturer) VALUES
('Panadol',       'Paracetamol',          'Analgesic',      15.00, 5000, 'GSK Pakistan'),
('Augmentin',     'Amoxicillin/Clavulanate','Antibiotic',   85.00, 2000, 'GSK Pakistan'),
('Brufen',        'Ibuprofen',             'Anti-inflammatory',25.00,3000,'Abbott Pakistan'),
('Nexium',        'Esomeprazole',          'PPI',            95.00,1500, 'AstraZeneca'),
('Lipitor',       'Atorvastatin',          'Statin',         70.00,2500, 'Pfizer'),
('Norvasc',       'Amlodipine',            'Antihypertensive',60.00,2000,'Pfizer'),
('Glucophage',    'Metformin',             'Antidiabetic',   30.00,4000, 'Merck'),
('Ventolin',      'Salbutamol',            'Bronchodilator', 120.00,1000,'GSK Pakistan'),
('Flagyl',        'Metronidazole',         'Antiprotozoal',  20.00,3500, 'Sanofi'),
('Zithromax',     'Azithromycin',          'Antibiotic',    110.00,1800, 'Pfizer'),
('Crestor',       'Rosuvastatin',          'Statin',         90.00,1200, 'AstraZeneca'),
('Lantus',        'Insulin Glargine',      'Insulin',       350.00, 500, 'Sanofi'),
('Diamicron',     'Gliclazide',            'Antidiabetic',   45.00,2200, 'Servier'),
('Lasix',         'Furosemide',            'Diuretic',       18.00,3000, 'Sanofi'),
('Concor',        'Bisoprolol',            'Beta-blocker',   55.00,2800, 'Merck'),
('Omepral',       'Omeprazole',            'PPI',            35.00,3500, 'Barrett Hodgson'),
('Ciprofloxacin', 'Ciprofloxacin',         'Antibiotic',     45.00,2600, 'Bayer'),
('Prednisolone',  'Prednisolone',          'Corticosteroid', 25.00,2000, 'Ferozsons'),
('Morphine',      'Morphine Sulphate',     'Opioid Analgesic',200.00,300,'Reckitt'),
('Warfarin',      'Warfarin Sodium',       'Anticoagulant',  40.00,1500, 'Unilab');

-- -------------------------------------------------------------
-- PRESCRIPTION (10 rows)
-- -------------------------------------------------------------
INSERT INTO PRESCRIPTION (patient_id, doctor_id, appointment_id, prescription_date, notes) VALUES
(1,  1,  1,  '2026-04-01', 'Take with food; avoid alcohol'),
(2,  2,  2,  '2026-04-02', 'Avoid bright screens; rest in dark room'),
(3,  3,  3,  '2026-04-03', 'Apply ice pack; physiotherapy twice weekly'),
(5,  5,  5,  '2026-04-07', 'Chemo cycle 3; blood counts weekly'),
(6,  6,  6,  '2026-04-08', 'Post-op antibiotics; wound care daily'),
(10,10,  10, '2026-04-15', 'Apply cream twice daily; avoid triggers'),
(11, 1,  11, '2026-04-16', 'Reduce salt intake; BP monitoring at home'),
(7,  7,  7,  '2026-04-10', 'Post-hernia repair care; no heavy lifting'),
(8,  8,  8,  '2026-04-12', 'Prenatal vitamins; iron supplementation'),
(4,  4,  4,  '2026-04-05', 'ORS for hydration; fever syrup if needed');

-- -------------------------------------------------------------
-- PRESCRIPTION_DETAILS (20 rows — M:M junction)
-- -------------------------------------------------------------
INSERT INTO PRESCRIPTION_DETAILS (prescription_id, medicine_id, dosage, duration_days, quantity) VALUES
(1,  6,  '5mg once daily',              30, 30),
(1,  5,  '10mg at night',               30, 30),
(2,  1,  '500mg every 6 hours',          7, 28),
(2,  15, '5mg once daily at bedtime',   30, 30),
(3,  3,  '400mg three times daily',     10, 30),
(3,  1,  '500mg as needed for pain',     7, 20),
(4, 19,  '10mg IV every 6 hours',        3,  12),
(4, 18,  '40mg oral once daily',        10, 10),
(5,  2,  '1g twice daily',               7, 14),
(5,  1,  '500mg every 8 hours',          5, 15),
(6, 17,  'Apply thin layer twice daily', 14, 2),
(6, 16,  '20mg once daily before meal',  14,14),
(7,  6,  '10mg once daily morning',     30, 30),
(7,  14, '40mg once daily morning',     30, 30),
(8,  2,  '625mg three times daily',      7, 21),
(8,  1,  '1g every 8 hours',             5, 15),
(9,  12, '20 units subcutaneous nightly',90,90),
(9,  13, '30mg once daily with meal',   90, 90),
(10, 8,  '100mcg 2 puffs when needed',  30, 1),
(10, 16, '20mg once daily before meal', 30, 30);

-- -------------------------------------------------------------
-- USERS (login accounts)
-- Passwords are SHA2-256 hashed (plain: Admin@123, Staff@123)
-- -------------------------------------------------------------
INSERT INTO USERS (username, password_hash, role, staff_id) VALUES
('admin',        SHA2('Admin@123', 256), 'Admin',  18),
('dr_ahmed',     SHA2('Doc@1234',  256), 'Doctor',  1),
('dr_sara',      SHA2('Doc@1234',  256), 'Doctor',  2),
('dr_bilal',     SHA2('Doc@1234',  256), 'Doctor',  3),
('staff_zahid',  SHA2('Staff@123', 256), 'Staff',  18),
('staff_samina', SHA2('Staff@123', 256), 'Staff',  19),
('viewer',       SHA2('View@123',  256), 'Viewer', NULL);
