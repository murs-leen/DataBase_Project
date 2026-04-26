# FINAL PROJECT REPORT
## Hospital Management System (HMS)
### Database Systems Lab – Semester Project
**April 2026**

---

## EXECUTIVE SUMMARY

This report documents the complete design, development, and implementation of the **Hospital Management System (HMS)** — a full-stack database-driven application developed for the Database Systems Lab semester project. The system manages all core hospital operations including patient registration, doctor and staff management, appointment scheduling, room admission, billing, and prescription tracking, backed by a fully normalized MySQL database and a professional web-based GUI.

---

## 1. PROJECT OVERVIEW

| Attribute | Details |
|-----------|---------|
| Project Title | Hospital Management System |
| Database | MySQL 8.0 |
| Backend | Python 3.10 / Flask |
| Frontend | HTML5, CSS3 (Vanilla), JavaScript (ES6) |
| Charts | Chart.js v4 |
| Total Tables | 13 (10 core + 3 supporting) |
| Total SQL Files | 4 (DDL, DML, Queries, Stored Programming) |
| GUI Pages | 10 (Login, Dashboard, Patients, Doctors, Appointments, Admissions, Billing, Staff, Reports, Error) |

---

## 2. DATABASE SCHEMA SUMMARY

### 2.1 Tables Created

| # | Table | Type | Rows Inserted |
|---|-------|------|--------------|
| 1 | DEPARTMENT | Core Lookup | 10 |
| 2 | STAFF | Superclass | 20 |
| 3 | DOCTOR | Subclass (ISA) | 10 |
| 4 | NURSE | Subclass (ISA) | 5 |
| 5 | PATIENT | Core Entity | 20 |
| 6 | ROOM | Core Entity | 20 |
| 7 | APPOINTMENT | Relationship Entity | 20 |
| 8 | ADMISSION | Core Entity | 10 |
| 9 | BILLING | Core Entity | 10 |
| 10 | PRESCRIPTION | Core Entity | 10 |
| 11 | MEDICINE | Core Lookup | 20 |
| 12 | PRESCRIPTION_DETAILS | Weak Entity / Junction | 20 |
| 13 | USERS | Auth/Login | 7 |

### 2.2 Constraints Summary

| Constraint Type | Count |
|----------------|-------|
| Primary Keys | 13 |
| Foreign Keys | 16 |
| UNIQUE constraints | 12 |
| CHECK constraints | 10 |
| NOT NULL (all critical columns) | ✅ |
| ON DELETE CASCADE | 5 |
| ON DELETE SET NULL | 3 |
| ON DELETE RESTRICT | 4 |

### 2.3 Indexes
| Index | Table | Purpose |
|-------|-------|---------|
| IDX_PATIENT_NAME | PATIENT | Fast name searches |
| IDX_APPOINTMENT_DT | APPOINTMENT | Date-based filtering |
| IDX_BILLING_PATIENT | BILLING | Patient billing lookups |

### 2.4 Views
| View | Description |
|------|-------------|
| v_patient_full_info | Patient details with total billing summary |
| v_doctor_appointment_summary | Doctor performance with appointment counts |

---

## 3. STORED PROGRAMMING SUMMARY

### Stored Procedures

| Procedure | Purpose | Features |
|-----------|---------|---------|
| sp_register_patient | Register new patient | IN/OUT params, transaction, error handler |
| sp_generate_bill | Calculate and create bill | Exception handling, multi-table calculation |
| sp_admit_patient | Admit patient to room | Calls sp_generate_bill (procedure chaining) |

### Functions

| Function | Returns | Usage |
|----------|---------|-------|
| fn_calculate_age(dob) | INT (age in years) | Used inside SELECT queries |
| fn_get_patient_balance(patient_id) | DECIMAL (outstanding amount) | Reporting queries |

### Triggers

| Trigger | Event | Action |
|---------|-------|--------|
| trg_before_insert_appointment | BEFORE INSERT on APPOINTMENT | Prevent past dates, detect time conflicts |
| trg_after_update_billing | AFTER UPDATE on BILLING | Auto-update payment_status |
| trg_after_delete_admission | AFTER DELETE on ADMISSION | Release room to Available |

### Cursors

| Cursor / Procedure | Type | Description |
|-------------------|------|-------------|
| sp_overdue_bill_report | Explicit cursor | Iterates overdue bills into temp table |
| sp_dept_revenue_report(dept_id) | Parameterized cursor | Dept-wise revenue (0 = all depts) |

---

## 4. SQL QUERIES SUMMARY

| Category | Count | Topics Covered |
|----------|-------|----------------|
| SELECT with WHERE | 5 | Active patients, doctor filter, room availability, billing status, dept filter |
| Aggregate (GROUP BY) | 3 | COUNT/SUM/AVG/MIN/MAX on patients, billing, appointments |
| JOIN | 4 | INNER JOIN, LEFT JOIN, 3-table join, prescription details join |
| Subqueries | 3 | Nested avg comparison, IN subquery, correlated subquery |
| UPDATE | 2 | Auto-status fix, no-show cancellation |
| DELETE | 2 | Old cancelled records, inactive patients |
| DCL (GRANT/REVOKE) | Full set | 4 users: admin, doctor, staff, viewer |

---

## 5. GUI APPLICATION SUMMARY

### Login System
- SHA-256 hashed passwords stored in USERS table
- Role-based access: Admin / Doctor / Staff / Viewer
- Session management via Flask sessions
- Client-side input validation

### CRUD Modules

| Module | Add | View | Edit | Delete |
|--------|-----|------|------|--------|
| Patients | ✅ | ✅ | ✅ | ✅ (soft) |
| Doctors | ✅ | ✅ | — | — |
| Appointments | ✅ | ✅ | Status only | — |
| Admissions | ✅ | ✅ | Discharge | — |
| Billing | — | ✅ | Record payment | — |
| Staff | — | ✅ | — | — |

### Dashboard Features
- **KPI Cards:** Total Patients, Total Doctors, Active Admissions, Monthly Revenue
- **Chart 1:** Patients per Department (Bar chart – Chart.js)
- **Chart 2:** Revenue per Month – Last 6 months (Line chart – Chart.js)
- **Top 10 Table:** Patients ranked by billing amount
- **Auto-refresh:** KPI cards refresh every 30 seconds via `/api/kpis`

### Reports & Export
- Patient Billing Report – full table
- **CSV Export:** `/reports/export/csv` – downloadable UTF-8 CSV

---

## 6. NORMALIZATION JUSTIFICATION

### First Normal Form (1NF) ✅
- All attributes are atomic (single-valued)
- No repeating groups (medicines stored in separate PRESCRIPTION_DETAILS)
- Every table has a defined Primary Key

### Second Normal Form (2NF) ✅
- No partial dependencies exist (all composite PKs examined)
- PRESCRIPTION_DETAILS: dosage/duration depend on BOTH prescription_id + medicine_id
- All other tables have single-column PKs → 2NF automatically satisfied

### Third Normal Form (3NF) ✅
- No transitive dependencies:
  - Doctor's department info → in DEPARTMENT table (not in DOCTOR)
  - Room daily charge → in ROOM, not duplicated in ADMISSION
  - Staff name/salary → in STAFF, not duplicated in DOCTOR/NURSE
  - Patient name/phone → in PATIENT, not duplicated in APPOINTMENT/BILLING

**Conclusion:** All 13 tables satisfy 3NF. No redundancy, no partial or transitive dependencies.

---

## 7. SECURITY IMPLEMENTATION

| Feature | Implementation |
|---------|---------------|
| Password Hashing | SHA2-256 via MySQL SHA2() and Python hashlib |
| Role-Based Access | ENUM('Admin','Doctor','Staff','Viewer') in USERS |
| DB-Level Roles | MySQL GRANT/REVOKE per user role |
| Input Validation | Client-side JS + server-side try/except |
| SQL Injection Prevention | Parameterized queries (mysql-connector placeholders) |
| Session Security | Flask secret_key + server-side session management |

---

## 8. PERFORMANCE FEATURES

| Feature | Implementation |
|---------|---------------|
| Indexes | 3 composite/single-column indexes on hot columns |
| Views | 2 views pre-join expensive multi-table queries |
| Connection pooling | Single connection per request (suitable for lab scale) |
| Efficient queries | GROUP BY with aggregates; LEFT JOINs over subqueries where possible |

---

## 9. FILE DELIVERABLES INDEX

| # | File | Description |
|---|------|-------------|
| 1 | `01_SRS_Document.md` | Software Requirements Specification |
| 2 | `02_DDL_Schema.sql` | Database schema (13 tables, indexes, views, DCL) |
| 3 | `03_Insert_Data.sql` | Realistic seed data (170+ rows) |
| 4 | `04_Queries.sql` | All SQL query types + DCL |
| 5 | `05_Stored_Programming.sql` | 3 procedures, 2 functions, 3 triggers, 2 cursors |
| 6 | `06_GUI/app.py` | Flask backend application |
| 7 | `06_GUI/static/style.css` | Global dark-theme stylesheet |
| 8 | `06_GUI/templates/` | 10 Jinja2 HTML templates |
| 9 | `07_ERD_EERD_Description.md` | ERD/EERD textual description + normalization |
| 10 | `08_Final_Report.md` | This document |

---

## 10. HOW TO RUN THE PROJECT

### Step 1: Setup MySQL Database
```bash
mysql -u root -p < 02_DDL_Schema.sql
mysql -u root -p hms_db < 03_Insert_Data.sql
mysql -u root -p hms_db < 05_Stored_Programming.sql
```

### Step 2: Install Python Dependencies
```bash
cd 06_GUI
pip install flask mysql-connector-python
```

### Step 3: Configure Database Connection
Edit `06_GUI/app.py` lines 18-23:
```python
DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",        # ← your MySQL username
    "password": "yourpassword",# ← your MySQL password
    "database": "hms_db"
}
```

### Step 4: Run the Application
```bash
python app.py
```
Open browser: **http://localhost:5000**

### Default Login
| Role | Username | Password |
|------|----------|----------|
| Admin | `admin` | `Admin@123` |
| Doctor | `dr_ahmed` | `Doc@1234` |
| Staff | `staff_zahid` | `Staff@123` |
| Viewer | `viewer` | `View@123` |

---

## 11. VIVA PREPARATION NOTES

### Key Concepts to Explain:
1. **ERD vs EERD:** ERD shows basic entities/relationships; EERD adds specialization (ISA), weak entities, aggregation
2. **3NF:** No transitive dependencies — explain using BILLING vs PATIENT separation
3. **Triggers vs Procedures:** Triggers fire automatically on DML events; procedures are called explicitly
4. **Cursors:** Row-by-row iteration when set-based operations are insufficient
5. **GRANT/REVOKE:** DCL controls database-level access per user role
6. **Views:** Virtual tables — v_patient_full_info joins PATIENT+BILLING for reuse
7. **ON DELETE CASCADE vs SET NULL:** CASCADE removes child records; SET NULL nullifies FK reference

### Likely Viva Questions:
- "Why is PRESCRIPTION_DETAILS a weak entity?" → It has no meaning without PRESCRIPTION
- "How is billing normalized?" → Total amount computed from services, not stored redundantly
- "What is the ISA hierarchy?" → STAFF is superclass; DOCTOR and NURSE inherit staff attributes
- "How does the room trigger work?" → trg_after_delete_admission releases room on discharge
- "Difference between correlated and nested subquery?" → Correlated references outer query per row

---

*End of Final Report*
*Hospital Management System – Database Systems Lab Semester Project*
