# SOFTWARE REQUIREMENTS SPECIFICATION (SRS)
## Hospital Management System (HMS)
### Database Systems Lab – Semester Project

**Version:** 1.0 | **Date:** April 2026

---

## 1. INTRODUCTION

### 1.1 Purpose
This SRS defines all requirements for the **Hospital Management System (HMS)** — a database-driven application managing patients, doctors, appointments, admissions, billing, and prescriptions.

### 1.2 Scope
HMS covers: Patient registration & discharge, doctor/staff management, appointment scheduling, room allocation, billing, prescription management, and a real-time analytics dashboard.

### 1.3 Acronyms
| Term | Definition |
|------|-----------|
| PK | Primary Key |
| FK | Foreign Key |
| 3NF | Third Normal Form |
| ERD | Entity-Relationship Diagram |
| EERD | Enhanced ERD |

---

## 2. OVERALL DESCRIPTION

### 2.1 User Classes
| User | Access Level |
|------|-------------|
| Admin | Full access — user management, all CRUD, reports |
| Doctor | View/update appointments, issue prescriptions |
| Staff/Nurse | Manage admissions, room assignments |
| Viewer | Read-only reports |

### 2.2 Operating Environment
- **RDBMS:** MySQL 8.0+
- **Backend:** Python 3.10+ (Flask)
- **Frontend:** HTML5 / CSS3 / JavaScript (Vanilla)
- **Browser:** Chrome 90+, Firefox 88+

---

## 3. FUNCTIONAL REQUIREMENTS

| ID | Requirement | Actor |
|----|-------------|-------|
| FR-01 | Register a new patient with auto-generated ID | Admin/Staff |
| FR-02 | Update patient details | Admin/Staff |
| FR-03 | Delete (deactivate) patient record | Admin |
| FR-04 | Search patient by name, phone, or ID | All |
| FR-05 | Register doctor with department & license | Admin |
| FR-06 | Schedule appointment — detect time conflicts | Admin/Staff |
| FR-07 | Admit patient to a room (check availability) | Admin/Staff |
| FR-08 | Assign/release rooms with auto status update | Admin/Staff |
| FR-09 | Generate bill from services and room charges | Admin |
| FR-10 | Issue prescription with multiple medicines | Doctor |
| FR-11 | View dashboard KPIs, charts, and reports | Admin |
| FR-12 | Manage staff (add, update, deactivate) | Admin |

---

## 4. NON-FUNCTIONAL REQUIREMENTS

| ID | Category | Requirement |
|----|----------|-------------|
| NFR-01 | Performance | Indexed queries return results < 2 sec for 100K rows |
| NFR-02 | Security | Role-based access, hashed passwords, GRANT/REVOKE |
| NFR-03 | Scalability | 3NF schema, designed for horizontal data growth |
| NFR-04 | Availability | Operational 8 AM–10 PM; daily mysqldump backups |
| NFR-05 | Usability | Validation feedback, dropdowns for FKs, responsive UI |
| NFR-06 | Maintainability | Modular SQL scripts, documented procedures/triggers |

---

## 5. DATA DICTIONARY

### PATIENT
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| patient_id | INT | PK, AUTO_INCREMENT | Unique patient ID |
| first_name | VARCHAR(50) | NOT NULL | First name |
| last_name | VARCHAR(50) | NOT NULL | Last name |
| date_of_birth | DATE | NOT NULL | DOB |
| gender | ENUM('Male','Female','Other') | NOT NULL | Gender |
| phone | VARCHAR(15) | NOT NULL, UNIQUE | Phone number |
| email | VARCHAR(100) | UNIQUE | Email |
| address | TEXT | NOT NULL | Address |
| blood_group | VARCHAR(5) | NOT NULL | Blood group |
| registration_date | DATE | NOT NULL, DEFAULT CURDATE() | Registration date |
| status | ENUM('Active','Inactive') | NOT NULL, DEFAULT 'Active' | Account status |

### STAFF
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| staff_id | INT | PK, AUTO_INCREMENT | Unique staff ID |
| first_name | VARCHAR(50) | NOT NULL | First name |
| last_name | VARCHAR(50) | NOT NULL | Last name |
| staff_type | ENUM('Doctor','Nurse','Technician','Admin') | NOT NULL | Staff type |
| phone | VARCHAR(15) | NOT NULL, UNIQUE | Phone |
| email | VARCHAR(100) | UNIQUE | Email |
| hire_date | DATE | NOT NULL | Hire date |
| salary | DECIMAL(10,2) | NOT NULL, CHECK(>0) | Monthly salary |
| shift | ENUM('Morning','Evening','Night') | NOT NULL | Work shift |
| status | ENUM('Active','Inactive') | NOT NULL, DEFAULT 'Active' | Status |

### DEPARTMENT
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| dept_id | INT | PK, AUTO_INCREMENT | Department ID |
| dept_name | VARCHAR(100) | NOT NULL, UNIQUE | Department name |
| location | VARCHAR(50) | NOT NULL | Physical location |
| phone_ext | VARCHAR(10) | UNIQUE | Extension number |
| description | TEXT | - | Description |

### DOCTOR
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| doctor_id | INT | PK, AUTO_INCREMENT | Doctor ID |
| staff_id | INT | FK→STAFF, NOT NULL | Linked staff record |
| dept_id | INT | FK→DEPARTMENT, NOT NULL | Department |
| specialization | VARCHAR(100) | NOT NULL | Specialization |
| license_number | VARCHAR(50) | NOT NULL, UNIQUE | License number |
| consultation_fee | DECIMAL(10,2) | NOT NULL, CHECK(>0) | Fee per visit |
| available_days | VARCHAR(100) | NOT NULL | Working days |

### APPOINTMENT
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| appointment_id | INT | PK, AUTO_INCREMENT | Appointment ID |
| patient_id | INT | FK→PATIENT, NOT NULL | Patient |
| doctor_id | INT | FK→DOCTOR, NOT NULL | Doctor |
| appointment_date | DATE | NOT NULL | Date |
| appointment_time | TIME | NOT NULL | Time |
| reason | VARCHAR(200) | NOT NULL | Visit reason |
| status | ENUM('Scheduled','Completed','Cancelled') | NOT NULL | Status |
| notes | TEXT | - | Doctor notes |

### ROOM
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| room_id | INT | PK, AUTO_INCREMENT | Room ID |
| room_number | VARCHAR(10) | NOT NULL, UNIQUE | Room number |
| room_type | ENUM('General','Private','ICU','Emergency') | NOT NULL | Type |
| dept_id | INT | FK→DEPARTMENT, NOT NULL | Department |
| capacity | INT | NOT NULL, CHECK(>0) | Bed capacity |
| daily_charge | DECIMAL(10,2) | NOT NULL, CHECK(>0) | Daily rate |
| status | ENUM('Available','Occupied','Maintenance') | NOT NULL | Status |

### ADMISSION
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| admission_id | INT | PK, AUTO_INCREMENT | Admission ID |
| patient_id | INT | FK→PATIENT, NOT NULL | Patient |
| room_id | INT | FK→ROOM, NOT NULL | Room |
| admit_date | DATE | NOT NULL | Admission date |
| discharge_date | DATE | NULL | Discharge date |
| diagnosis | TEXT | NOT NULL | Diagnosis |
| attending_doctor | INT | FK→DOCTOR, NOT NULL | Doctor |
| status | ENUM('Active','Discharged') | NOT NULL, DEFAULT 'Active' | Status |

### BILLING
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| bill_id | INT | PK, AUTO_INCREMENT | Bill ID |
| patient_id | INT | FK→PATIENT, NOT NULL | Patient |
| admission_id | INT | FK→ADMISSION, NULL | Linked admission |
| total_amount | DECIMAL(12,2) | NOT NULL, CHECK(>=0) | Total bill |
| paid_amount | DECIMAL(12,2) | NOT NULL, DEFAULT 0 | Amount paid |
| bill_date | DATE | NOT NULL, DEFAULT CURDATE() | Bill date |
| payment_status | ENUM('Pending','Paid','Partial') | NOT NULL | Status |
| payment_method | VARCHAR(30) | - | Cash/Card/Insurance |

### PRESCRIPTION
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| prescription_id | INT | PK, AUTO_INCREMENT | Prescription ID |
| patient_id | INT | FK→PATIENT, NOT NULL | Patient |
| doctor_id | INT | FK→DOCTOR, NOT NULL | Doctor |
| appointment_id | INT | FK→APPOINTMENT, NULL | Linked appointment |
| prescription_date | DATE | NOT NULL, DEFAULT CURDATE() | Issue date |
| notes | TEXT | - | Instructions |

### MEDICINE
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| medicine_id | INT | PK, AUTO_INCREMENT | Medicine ID |
| medicine_name | VARCHAR(100) | NOT NULL, UNIQUE | Brand name |
| generic_name | VARCHAR(100) | NOT NULL | Generic name |
| category | VARCHAR(50) | NOT NULL | Category |
| unit_price | DECIMAL(8,2) | NOT NULL, CHECK(>=0) | Price per unit |
| stock_quantity | INT | NOT NULL, DEFAULT 0, CHECK(>=0) | Stock |
| manufacturer | VARCHAR(100) | NOT NULL | Manufacturer |

### PRESCRIPTION_DETAILS (Weak Entity / Junction)
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| detail_id | INT | PK, AUTO_INCREMENT | Detail ID |
| prescription_id | INT | FK→PRESCRIPTION, NOT NULL | Parent prescription |
| medicine_id | INT | FK→MEDICINE, NOT NULL | Medicine |
| dosage | VARCHAR(50) | NOT NULL | Dosage instruction |
| duration_days | INT | NOT NULL, CHECK(>0) | Duration in days |
| quantity | INT | NOT NULL, CHECK(>0) | Quantity prescribed |

### NURSE (Specialization of STAFF)
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| nurse_id | INT | PK, AUTO_INCREMENT | Nurse ID |
| staff_id | INT | FK→STAFF, NOT NULL, UNIQUE | Staff link |
| ward_assignment | VARCHAR(50) | NOT NULL | Ward |
| certification | VARCHAR(100) | NOT NULL | Certification |

### USERS (Login)
| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| user_id | INT | PK, AUTO_INCREMENT | User ID |
| username | VARCHAR(50) | NOT NULL, UNIQUE | Login name |
| password_hash | VARCHAR(255) | NOT NULL | Hashed password |
| role | ENUM('Admin','Doctor','Staff','Viewer') | NOT NULL | Role |
| staff_id | INT | FK→STAFF, NULL | Linked staff |
| is_active | TINYINT(1) | NOT NULL, DEFAULT 1 | Active flag |
| created_at | DATETIME | NOT NULL, DEFAULT NOW() | Created time |

---

## 6. USE CASES

| ID | Use Case | Actor | Priority |
|----|----------|-------|----------|
| UC-01 | Register Patient | Admin/Staff | High |
| UC-02 | Schedule Appointment | Admin/Staff | High |
| UC-03 | Admit Patient | Admin/Staff | High |
| UC-04 | Generate Bill | Admin | High |
| UC-05 | Issue Prescription | Doctor | High |
| UC-06 | View Dashboard | Admin | Medium |
| UC-07 | Manage Staff | Admin | Medium |
| UC-08 | Search Records | All | High |
| UC-09 | Export Reports | Admin | Medium |
| UC-10 | Login/Logout | All | High |

---
*End of SRS Document*
