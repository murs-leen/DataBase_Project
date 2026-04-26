-- =============================================================
-- HOSPITAL MANAGEMENT SYSTEM
-- SQL Queries Script
-- Covers: SELECT, Aggregate, JOIN, Subqueries, UPDATE, DELETE, DCL
-- =============================================================
USE hms_db;

-- =============================================================
-- SECTION 1: SELECT QUERIES (5 queries with WHERE conditions)
-- =============================================================

-- Q1: Get all active patients registered in 2026
SELECT
    patient_id,
    CONCAT(first_name, ' ', last_name) AS full_name,
    gender,
    blood_group,
    phone,
    registration_date
FROM PATIENT
WHERE status = 'Active'
  AND YEAR(registration_date) = 2026
ORDER BY registration_date DESC;

-- Q2: Get all scheduled appointments for a specific doctor (doctor_id = 1)
SELECT
    a.appointment_id,
    CONCAT(p.first_name, ' ', p.last_name) AS patient_name,
    a.appointment_date,
    a.appointment_time,
    a.reason,
    a.status
FROM APPOINTMENT a
JOIN PATIENT p ON p.patient_id = a.patient_id
WHERE a.doctor_id = 1
  AND a.status = 'Scheduled'
ORDER BY a.appointment_date, a.appointment_time;

-- Q3: Get all rooms that are currently available and not under maintenance
SELECT
    room_id,
    room_number,
    room_type,
    capacity,
    daily_charge,
    status
FROM ROOM
WHERE status = 'Available'
ORDER BY daily_charge ASC;

-- Q4: Get patients with partial or pending bills
SELECT
    b.bill_id,
    CONCAT(p.first_name, ' ', p.last_name) AS patient_name,
    b.total_amount,
    b.paid_amount,
    (b.total_amount - b.paid_amount)        AS balance_due,
    b.payment_status,
    b.bill_date
FROM BILLING b
JOIN PATIENT p ON p.patient_id = b.patient_id
WHERE b.payment_status IN ('Pending', 'Partial')
ORDER BY balance_due DESC;

-- Q5: Get doctors in Cardiology or Neurology departments
SELECT
    d.doctor_id,
    CONCAT(s.first_name, ' ', s.last_name) AS doctor_name,
    dep.dept_name,
    d.specialization,
    d.consultation_fee,
    d.available_days
FROM DOCTOR d
JOIN STAFF      s   ON s.staff_id  = d.staff_id
JOIN DEPARTMENT dep ON dep.dept_id = d.dept_id
WHERE dep.dept_name IN ('Cardiology', 'Neurology')
ORDER BY d.consultation_fee DESC;


-- =============================================================
-- SECTION 2: AGGREGATE QUERIES (3 with GROUP BY)
-- =============================================================

-- Q6: COUNT patients per gender and blood group
SELECT
    gender,
    blood_group,
    COUNT(*) AS total_patients
FROM PATIENT
WHERE status = 'Active'
GROUP BY gender, blood_group
ORDER BY total_patients DESC;

-- Q7: SUM and AVG billing per payment status
SELECT
    payment_status,
    COUNT(*)                    AS total_bills,
    SUM(total_amount)           AS total_revenue,
    SUM(paid_amount)            AS total_collected,
    SUM(total_amount - paid_amount) AS total_outstanding,
    ROUND(AVG(total_amount), 2) AS avg_bill,
    MAX(total_amount)           AS max_bill,
    MIN(total_amount)           AS min_bill
FROM BILLING
GROUP BY payment_status;

-- Q8: Total appointments per doctor with MIN/MAX date
SELECT
    d.doctor_id,
    CONCAT(s.first_name, ' ', s.last_name) AS doctor_name,
    dep.dept_name,
    COUNT(a.appointment_id)                AS total_appointments,
    MIN(a.appointment_date)                AS first_appointment,
    MAX(a.appointment_date)                AS last_appointment,
    AVG(d.consultation_fee)                AS avg_fee
FROM DOCTOR d
JOIN STAFF       s   ON s.staff_id   = d.staff_id
JOIN DEPARTMENT  dep ON dep.dept_id  = d.dept_id
LEFT JOIN APPOINTMENT a ON a.doctor_id = d.doctor_id
GROUP BY d.doctor_id, s.first_name, s.last_name, dep.dept_name
HAVING total_appointments > 0
ORDER BY total_appointments DESC;


-- =============================================================
-- SECTION 3: JOIN QUERIES (4 queries)
-- =============================================================

-- Q9: INNER JOIN — Appointments with patient and doctor names
SELECT
    a.appointment_id,
    CONCAT(p.first_name, ' ', p.last_name) AS patient_name,
    CONCAT(s.first_name, ' ', s.last_name) AS doctor_name,
    d.specialization,
    a.appointment_date,
    a.appointment_time,
    a.status
FROM APPOINTMENT a
INNER JOIN PATIENT p ON p.patient_id = a.patient_id
INNER JOIN DOCTOR  d ON d.doctor_id  = a.doctor_id
INNER JOIN STAFF   s ON s.staff_id   = d.staff_id
ORDER BY a.appointment_date DESC;

-- Q10: LEFT JOIN — All patients with their billing info (including unbilled)
SELECT
    p.patient_id,
    CONCAT(p.first_name, ' ', p.last_name) AS patient_name,
    p.phone,
    b.bill_id,
    COALESCE(b.total_amount, 0)            AS total_billed,
    COALESCE(b.payment_status, 'No Bill')  AS payment_status
FROM PATIENT p
LEFT JOIN BILLING b ON b.patient_id = p.patient_id
ORDER BY p.patient_id;

-- Q11: Multi-table JOIN (3+ tables) — Admission details with patient, room, doctor
SELECT
    adm.admission_id,
    CONCAT(p.first_name, ' ', p.last_name)  AS patient_name,
    r.room_number,
    r.room_type,
    dep.dept_name,
    CONCAT(s.first_name, ' ', s.last_name)  AS attending_doctor,
    adm.admit_date,
    adm.discharge_date,
    adm.diagnosis,
    adm.status,
    DATEDIFF(COALESCE(adm.discharge_date, CURDATE()), adm.admit_date) AS stay_days,
    DATEDIFF(COALESCE(adm.discharge_date, CURDATE()), adm.admit_date)
        * r.daily_charge AS room_charges
FROM ADMISSION adm
JOIN PATIENT    p   ON p.patient_id    = adm.patient_id
JOIN ROOM       r   ON r.room_id       = adm.room_id
JOIN DEPARTMENT dep ON dep.dept_id     = r.dept_id
JOIN DOCTOR     doc ON doc.doctor_id   = adm.attending_doctor
JOIN STAFF      s   ON s.staff_id      = doc.staff_id
ORDER BY adm.admit_date DESC;

-- Q12: JOIN — Prescription details with medicine names and costs
SELECT
    pr.prescription_id,
    pr.prescription_date,
    CONCAT(p.first_name, ' ', p.last_name)  AS patient_name,
    CONCAT(s.first_name, ' ', s.last_name)  AS doctor_name,
    m.medicine_name,
    m.category,
    pd.dosage,
    pd.duration_days,
    pd.quantity,
    (pd.quantity * m.unit_price)             AS medicine_cost
FROM PRESCRIPTION pr
JOIN PATIENT              p   ON p.patient_id       = pr.patient_id
JOIN DOCTOR               d   ON d.doctor_id        = pr.doctor_id
JOIN STAFF                s   ON s.staff_id         = d.staff_id
JOIN PRESCRIPTION_DETAILS pd  ON pd.prescription_id = pr.prescription_id
JOIN MEDICINE             m   ON m.medicine_id      = pd.medicine_id
ORDER BY pr.prescription_id, medicine_cost DESC;


-- =============================================================
-- SECTION 4: SUBQUERIES (3 queries)
-- =============================================================

-- Q13: Nested Subquery — Patients whose total billing > average billing
SELECT
    p.patient_id,
    CONCAT(p.first_name, ' ', p.last_name) AS patient_name,
    b.total_amount
FROM PATIENT p
JOIN BILLING b ON b.patient_id = p.patient_id
WHERE b.total_amount > (
    SELECT AVG(total_amount) FROM BILLING
)
ORDER BY b.total_amount DESC;

-- Q14: Subquery with IN — Doctors who have at least one completed appointment
SELECT
    d.doctor_id,
    CONCAT(s.first_name, ' ', s.last_name) AS doctor_name,
    d.specialization
FROM DOCTOR d
JOIN STAFF s ON s.staff_id = d.staff_id
WHERE d.doctor_id IN (
    SELECT DISTINCT doctor_id
    FROM APPOINTMENT
    WHERE status = 'Completed'
);

-- Q15: Correlated Subquery — Patients with more appointments than average
SELECT
    p.patient_id,
    CONCAT(p.first_name, ' ', p.last_name) AS patient_name,
    (
        SELECT COUNT(*)
        FROM APPOINTMENT a
        WHERE a.patient_id = p.patient_id
    ) AS appointment_count
FROM PATIENT p
WHERE (
    SELECT COUNT(*)
    FROM APPOINTMENT a
    WHERE a.patient_id = p.patient_id
) > (
    SELECT AVG(cnt) FROM (
        SELECT COUNT(*) AS cnt
        FROM APPOINTMENT
        GROUP BY patient_id
    ) subq
)
ORDER BY appointment_count DESC;


-- =============================================================
-- SECTION 5: UPDATE STATEMENTS (2)
-- =============================================================

-- U1: Update billing status to 'Paid' when paid_amount equals total_amount
UPDATE BILLING
SET payment_status = 'Paid'
WHERE paid_amount >= total_amount
  AND payment_status != 'Paid';

-- U2: Mark appointments as 'Cancelled' if they are older than 30 days
--     and still in 'Scheduled' status (no-show handling)
UPDATE APPOINTMENT
SET status = 'Cancelled'
WHERE status = 'Scheduled'
  AND appointment_date < DATE_SUB(CURDATE(), INTERVAL 30 DAY);


-- =============================================================
-- SECTION 6: DELETE STATEMENTS (2)
-- =============================================================

-- D1: Delete cancelled appointments older than 1 year
DELETE FROM APPOINTMENT
WHERE status = 'Cancelled'
  AND appointment_date < DATE_SUB(CURDATE(), INTERVAL 1 YEAR);

-- D2: Remove inactive patients who have no admissions, billing, or appointments
DELETE FROM PATIENT
WHERE status = 'Inactive'
  AND patient_id NOT IN (SELECT DISTINCT patient_id FROM ADMISSION)
  AND patient_id NOT IN (SELECT DISTINCT patient_id FROM BILLING)
  AND patient_id NOT IN (SELECT DISTINCT patient_id FROM APPOINTMENT);


-- =============================================================
-- SECTION 7: DCL — GRANT and REVOKE
-- =============================================================

-- Create application users
CREATE USER IF NOT EXISTS 'hms_admin'@'localhost'  IDENTIFIED BY 'Admin@123!';
CREATE USER IF NOT EXISTS 'hms_doctor'@'localhost' IDENTIFIED BY 'Doc@1234!';
CREATE USER IF NOT EXISTS 'hms_staff'@'localhost'  IDENTIFIED BY 'Staff@123!';
CREATE USER IF NOT EXISTS 'hms_viewer'@'localhost' IDENTIFIED BY 'View@123!';

-- Grant full access to admin
GRANT ALL PRIVILEGES ON hms_db.* TO 'hms_admin'@'localhost';

-- Grant limited access to doctors
GRANT SELECT, INSERT, UPDATE ON hms_db.APPOINTMENT         TO 'hms_doctor'@'localhost';
GRANT SELECT, INSERT, UPDATE ON hms_db.PRESCRIPTION        TO 'hms_doctor'@'localhost';
GRANT SELECT, INSERT, UPDATE ON hms_db.PRESCRIPTION_DETAILS TO 'hms_doctor'@'localhost';
GRANT SELECT ON hms_db.PATIENT                             TO 'hms_doctor'@'localhost';
GRANT SELECT ON hms_db.MEDICINE                            TO 'hms_doctor'@'localhost';

-- Grant staff permissions
GRANT SELECT, INSERT, UPDATE ON hms_db.PATIENT    TO 'hms_staff'@'localhost';
GRANT SELECT, INSERT, UPDATE ON hms_db.ADMISSION  TO 'hms_staff'@'localhost';
GRANT SELECT, INSERT, UPDATE ON hms_db.BILLING    TO 'hms_staff'@'localhost';
GRANT SELECT ON hms_db.ROOM                       TO 'hms_staff'@'localhost';
GRANT SELECT ON hms_db.DOCTOR                     TO 'hms_staff'@'localhost';

-- Grant view-only access to viewer
GRANT SELECT ON hms_db.v_patient_full_info            TO 'hms_viewer'@'localhost';
GRANT SELECT ON hms_db.v_doctor_appointment_summary   TO 'hms_viewer'@'localhost';

-- Revoke DELETE from staff and doctor (safety measure)
REVOKE DELETE ON hms_db.PATIENT     FROM 'hms_staff'@'localhost';
REVOKE DELETE ON hms_db.APPOINTMENT FROM 'hms_doctor'@'localhost';

FLUSH PRIVILEGES;
