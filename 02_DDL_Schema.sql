-- =============================================================
-- HOSPITAL MANAGEMENT SYSTEM (HMS)
-- DDL Script: Database Schema Creation
-- Database: MySQL 8.0+
-- Author: DB Systems Lab Project
-- Date: April 2026
-- =============================================================

-- Drop and recreate database
DROP DATABASE IF EXISTS hms_db;
CREATE DATABASE hms_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE hms_db;

-- =============================================================
-- TABLE 1: DEPARTMENT
-- (Created first — referenced by STAFF/DOCTOR/ROOM)
-- =============================================================
CREATE TABLE DEPARTMENT (
    dept_id     INT            NOT NULL AUTO_INCREMENT,
    dept_name   VARCHAR(100)   NOT NULL,
    location    VARCHAR(50)    NOT NULL,
    phone_ext   VARCHAR(10)    UNIQUE,
    description TEXT,
    CONSTRAINT PK_DEPARTMENT PRIMARY KEY (dept_id),
    CONSTRAINT UQ_DEPT_NAME  UNIQUE (dept_name)
);

-- =============================================================
-- TABLE 2: STAFF (Superclass — DOCTOR and NURSE are subclasses)
-- =============================================================
CREATE TABLE STAFF (
    staff_id   INT             NOT NULL AUTO_INCREMENT,
    first_name VARCHAR(50)     NOT NULL,
    last_name  VARCHAR(50)     NOT NULL,
    staff_type ENUM('Doctor','Nurse','Technician','Admin') NOT NULL,
    phone      VARCHAR(15)     NOT NULL,
    email      VARCHAR(100),
    hire_date  DATE            NOT NULL,
    salary     DECIMAL(10,2)   NOT NULL,
    shift      ENUM('Morning','Evening','Night') NOT NULL,
    status     ENUM('Active','Inactive') NOT NULL DEFAULT 'Active',
    CONSTRAINT PK_STAFF    PRIMARY KEY (staff_id),
    CONSTRAINT UQ_STAFF_PH UNIQUE (phone),
    CONSTRAINT UQ_STAFF_EM UNIQUE (email),
    CONSTRAINT CHK_SALARY  CHECK (salary > 0)
);

-- =============================================================
-- TABLE 3: DOCTOR (Subclass/Specialization of STAFF)
-- =============================================================
CREATE TABLE DOCTOR (
    doctor_id        INT           NOT NULL AUTO_INCREMENT,
    staff_id         INT           NOT NULL,
    dept_id          INT           NOT NULL,
    specialization   VARCHAR(100)  NOT NULL,
    license_number   VARCHAR(50)   NOT NULL,
    consultation_fee DECIMAL(10,2) NOT NULL,
    available_days   VARCHAR(100)  NOT NULL,
    CONSTRAINT PK_DOCTOR        PRIMARY KEY (doctor_id),
    CONSTRAINT UQ_LICENSE       UNIQUE (license_number),
    CONSTRAINT FK_DOC_STAFF     FOREIGN KEY (staff_id)
        REFERENCES STAFF(staff_id)   ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT FK_DOC_DEPT      FOREIGN KEY (dept_id)
        REFERENCES DEPARTMENT(dept_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT CHK_CONSULT_FEE  CHECK (consultation_fee > 0)
);

-- =============================================================
-- TABLE 4: NURSE (Subclass/Specialization of STAFF)
-- =============================================================
CREATE TABLE NURSE (
    nurse_id        INT          NOT NULL AUTO_INCREMENT,
    staff_id        INT          NOT NULL,
    ward_assignment VARCHAR(50)  NOT NULL,
    certification   VARCHAR(100) NOT NULL,
    CONSTRAINT PK_NURSE      PRIMARY KEY (nurse_id),
    CONSTRAINT UQ_NURSE_STF  UNIQUE (staff_id),
    CONSTRAINT FK_NURSE_STAFF FOREIGN KEY (staff_id)
        REFERENCES STAFF(staff_id) ON DELETE CASCADE ON UPDATE CASCADE
);

-- =============================================================
-- TABLE 5: PATIENT
-- =============================================================
CREATE TABLE PATIENT (
    patient_id        INT          NOT NULL AUTO_INCREMENT,
    first_name        VARCHAR(50)  NOT NULL,
    last_name         VARCHAR(50)  NOT NULL,
    date_of_birth     DATE         NOT NULL,
    gender            ENUM('Male','Female','Other') NOT NULL,
    phone             VARCHAR(15)  NOT NULL,
    email             VARCHAR(100),
    address           TEXT         NOT NULL,
    blood_group       VARCHAR(5)   NOT NULL,
    registration_date DATE         NOT NULL DEFAULT (CURDATE()),
    status            ENUM('Active','Inactive') NOT NULL DEFAULT 'Active',
    CONSTRAINT PK_PATIENT    PRIMARY KEY (patient_id),
    CONSTRAINT UQ_PAT_PHONE  UNIQUE (phone),
    CONSTRAINT CHK_PAT_BGRP  CHECK (blood_group IN ('A+','A-','B+','B-','AB+','AB-','O+','O-'))
);

-- =============================================================
-- TABLE 6: ROOM
-- =============================================================
CREATE TABLE ROOM (
    room_id      INT           NOT NULL AUTO_INCREMENT,
    room_number  VARCHAR(10)   NOT NULL,
    room_type    ENUM('General','Private','ICU','Emergency') NOT NULL,
    dept_id      INT           NOT NULL,
    capacity     INT           NOT NULL,
    daily_charge DECIMAL(10,2) NOT NULL,
    status       ENUM('Available','Occupied','Maintenance') NOT NULL DEFAULT 'Available',
    CONSTRAINT PK_ROOM         PRIMARY KEY (room_id),
    CONSTRAINT UQ_ROOM_NUM     UNIQUE (room_number),
    CONSTRAINT FK_ROOM_DEPT    FOREIGN KEY (dept_id)
        REFERENCES DEPARTMENT(dept_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT CHK_ROOM_CAP    CHECK (capacity > 0),
    CONSTRAINT CHK_DAILY_CHG   CHECK (daily_charge > 0)
);

-- =============================================================
-- TABLE 7: APPOINTMENT
-- =============================================================
CREATE TABLE APPOINTMENT (
    appointment_id   INT          NOT NULL AUTO_INCREMENT,
    patient_id       INT          NOT NULL,
    doctor_id        INT          NOT NULL,
    appointment_date DATE         NOT NULL,
    appointment_time TIME         NOT NULL,
    reason           VARCHAR(200) NOT NULL,
    status           ENUM('Scheduled','Completed','Cancelled') NOT NULL DEFAULT 'Scheduled',
    notes            TEXT,
    CONSTRAINT PK_APPOINTMENT  PRIMARY KEY (appointment_id),
    CONSTRAINT FK_APT_PATIENT  FOREIGN KEY (patient_id)
        REFERENCES PATIENT(patient_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT FK_APT_DOCTOR   FOREIGN KEY (doctor_id)
        REFERENCES DOCTOR(doctor_id)  ON DELETE RESTRICT ON UPDATE CASCADE
);

-- =============================================================
-- TABLE 8: ADMISSION
-- =============================================================
CREATE TABLE ADMISSION (
    admission_id      INT  NOT NULL AUTO_INCREMENT,
    patient_id        INT  NOT NULL,
    room_id           INT  NOT NULL,
    admit_date        DATE NOT NULL,
    discharge_date    DATE DEFAULT NULL,
    diagnosis         TEXT NOT NULL,
    attending_doctor  INT  NOT NULL,
    status            ENUM('Active','Discharged') NOT NULL DEFAULT 'Active',
    CONSTRAINT PK_ADMISSION    PRIMARY KEY (admission_id),
    CONSTRAINT FK_ADM_PATIENT  FOREIGN KEY (patient_id)
        REFERENCES PATIENT(patient_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT FK_ADM_ROOM     FOREIGN KEY (room_id)
        REFERENCES ROOM(room_id)      ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT FK_ADM_DOCTOR   FOREIGN KEY (attending_doctor)
        REFERENCES DOCTOR(doctor_id)  ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT CHK_DISCHARGE   CHECK (discharge_date IS NULL OR discharge_date >= admit_date)
);

-- =============================================================
-- TABLE 9: BILLING (1:1 with PATIENT per visit via admission_id)
-- =============================================================
CREATE TABLE BILLING (
    bill_id        INT           NOT NULL AUTO_INCREMENT,
    patient_id     INT           NOT NULL,
    admission_id   INT           DEFAULT NULL,
    total_amount   DECIMAL(12,2) NOT NULL,
    paid_amount    DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    bill_date      DATE          NOT NULL DEFAULT (CURDATE()),
    payment_status ENUM('Pending','Paid','Partial') NOT NULL DEFAULT 'Pending',
    payment_method VARCHAR(30)   DEFAULT NULL,
    CONSTRAINT PK_BILLING      PRIMARY KEY (bill_id),
    CONSTRAINT FK_BILL_PATIENT FOREIGN KEY (patient_id)
        REFERENCES PATIENT(patient_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT FK_BILL_ADM     FOREIGN KEY (admission_id)
        REFERENCES ADMISSION(admission_id) ON DELETE SET NULL ON UPDATE CASCADE,
    CONSTRAINT CHK_TOTAL_AMT   CHECK (total_amount >= 0),
    CONSTRAINT CHK_PAID_AMT    CHECK (paid_amount >= 0)
);

-- =============================================================
-- TABLE 10: PRESCRIPTION
-- =============================================================
CREATE TABLE PRESCRIPTION (
    prescription_id   INT  NOT NULL AUTO_INCREMENT,
    patient_id        INT  NOT NULL,
    doctor_id         INT  NOT NULL,
    appointment_id    INT  DEFAULT NULL,
    prescription_date DATE NOT NULL DEFAULT (CURDATE()),
    notes             TEXT,
    CONSTRAINT PK_PRESCRIPTION   PRIMARY KEY (prescription_id),
    CONSTRAINT FK_PRE_PATIENT    FOREIGN KEY (patient_id)
        REFERENCES PATIENT(patient_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT FK_PRE_DOCTOR     FOREIGN KEY (doctor_id)
        REFERENCES DOCTOR(doctor_id)  ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT FK_PRE_APT        FOREIGN KEY (appointment_id)
        REFERENCES APPOINTMENT(appointment_id) ON DELETE SET NULL ON UPDATE CASCADE
);

-- =============================================================
-- TABLE 11: MEDICINE
-- =============================================================
CREATE TABLE MEDICINE (
    medicine_id    INT           NOT NULL AUTO_INCREMENT,
    medicine_name  VARCHAR(100)  NOT NULL,
    generic_name   VARCHAR(100)  NOT NULL,
    category       VARCHAR(50)   NOT NULL,
    unit_price     DECIMAL(8,2)  NOT NULL,
    stock_quantity INT           NOT NULL DEFAULT 0,
    manufacturer   VARCHAR(100)  NOT NULL,
    CONSTRAINT PK_MEDICINE     PRIMARY KEY (medicine_id),
    CONSTRAINT UQ_MED_NAME     UNIQUE (medicine_name),
    CONSTRAINT CHK_MED_PRICE   CHECK (unit_price >= 0),
    CONSTRAINT CHK_MED_STOCK   CHECK (stock_quantity >= 0)
);

-- =============================================================
-- TABLE 12: PRESCRIPTION_DETAILS (Weak Entity + Junction M:M)
-- =============================================================
CREATE TABLE PRESCRIPTION_DETAILS (
    detail_id       INT          NOT NULL AUTO_INCREMENT,
    prescription_id INT          NOT NULL,
    medicine_id     INT          NOT NULL,
    dosage          VARCHAR(50)  NOT NULL,
    duration_days   INT          NOT NULL,
    quantity        INT          NOT NULL,
    CONSTRAINT PK_PRESC_DET      PRIMARY KEY (detail_id),
    CONSTRAINT FK_PRDET_PRESC    FOREIGN KEY (prescription_id)
        REFERENCES PRESCRIPTION(prescription_id) ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT FK_PRDET_MED      FOREIGN KEY (medicine_id)
        REFERENCES MEDICINE(medicine_id) ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT CHK_DURATION      CHECK (duration_days > 0),
    CONSTRAINT CHK_QUANTITY      CHECK (quantity > 0)
);

-- =============================================================
-- TABLE 13: USERS (Login / Authentication)
-- =============================================================
CREATE TABLE USERS (
    user_id       INT           NOT NULL AUTO_INCREMENT,
    username      VARCHAR(50)   NOT NULL,
    password_hash VARCHAR(255)  NOT NULL,
    role          ENUM('Admin','Doctor','Staff','Viewer') NOT NULL,
    staff_id      INT           DEFAULT NULL,
    is_active     TINYINT(1)    NOT NULL DEFAULT 1,
    created_at    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT PK_USERS      PRIMARY KEY (user_id),
    CONSTRAINT UQ_USERNAME   UNIQUE (username),
    CONSTRAINT FK_USR_STAFF  FOREIGN KEY (staff_id)
        REFERENCES STAFF(staff_id) ON DELETE SET NULL ON UPDATE CASCADE
);

-- =============================================================
-- INDEXES (Performance Optimization)
-- =============================================================
CREATE INDEX IDX_PATIENT_NAME   ON PATIENT(last_name, first_name);
CREATE INDEX IDX_APPOINTMENT_DT ON APPOINTMENT(appointment_date, doctor_id);
CREATE INDEX IDX_BILLING_PATIENT ON BILLING(patient_id);

-- =============================================================
-- VIEW 1: v_patient_full_info
-- Shows complete patient info with total billing
-- =============================================================
CREATE OR REPLACE VIEW v_patient_full_info AS
SELECT
    p.patient_id,
    CONCAT(p.first_name, ' ', p.last_name)  AS full_name,
    p.gender,
    p.blood_group,
    p.phone,
    p.registration_date,
    p.status,
    COALESCE(SUM(b.total_amount), 0)         AS total_billed,
    COALESCE(SUM(b.paid_amount), 0)          AS total_paid
FROM PATIENT p
LEFT JOIN BILLING b ON b.patient_id = p.patient_id
GROUP BY p.patient_id, p.first_name, p.last_name, p.gender,
         p.blood_group, p.phone, p.registration_date, p.status;

-- =============================================================
-- VIEW 2: v_doctor_appointment_summary
-- Doctor name, department, and count of appointments
-- =============================================================
CREATE OR REPLACE VIEW v_doctor_appointment_summary AS
SELECT
    d.doctor_id,
    CONCAT(s.first_name, ' ', s.last_name) AS doctor_name,
    dep.dept_name,
    d.specialization,
    d.consultation_fee,
    COUNT(a.appointment_id)                 AS total_appointments
FROM DOCTOR d
JOIN STAFF      s   ON s.staff_id  = d.staff_id
JOIN DEPARTMENT dep ON dep.dept_id = d.dept_id
LEFT JOIN APPOINTMENT a ON a.doctor_id = d.doctor_id
GROUP BY d.doctor_id, s.first_name, s.last_name,
         dep.dept_name, d.specialization, d.consultation_fee;

-- =============================================================
-- DCL: Grant/Revoke (run as root after creation)
-- =============================================================
-- Create application roles
-- CREATE USER IF NOT EXISTS 'hms_admin'@'localhost' IDENTIFIED BY 'Admin@123!';
-- CREATE USER IF NOT EXISTS 'hms_staff'@'localhost' IDENTIFIED BY 'Staff@123!';
-- GRANT ALL PRIVILEGES ON hms_db.* TO 'hms_admin'@'localhost';
-- GRANT SELECT, INSERT, UPDATE ON hms_db.PATIENT      TO 'hms_staff'@'localhost';
-- GRANT SELECT, INSERT, UPDATE ON hms_db.APPOINTMENT  TO 'hms_staff'@'localhost';
-- GRANT SELECT, INSERT, UPDATE ON hms_db.ADMISSION    TO 'hms_staff'@'localhost';
-- GRANT SELECT ON hms_db.v_patient_full_info           TO 'hms_staff'@'localhost';
-- REVOKE DELETE ON hms_db.*                            FROM 'hms_staff'@'localhost';
-- FLUSH PRIVILEGES;
