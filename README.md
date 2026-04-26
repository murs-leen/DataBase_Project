# 🏥 Hospital Management System (HMS)
## Database Systems Lab – Semester Project

A complete, database-driven Hospital Management System built with **MySQL 8.0**, **Python Flask**, and **Vanilla HTML/CSS/JS**.

---

## 📁 Project Structure

```
DB_Project/
├── 01_SRS_Document.md              ← Software Requirements Specification
├── 02_DDL_Schema.sql               ← Database schema (13 tables, views, indexes)
├── 03_Insert_Data.sql              ← Seed data (170+ realistic rows)
├── 04_Queries.sql                  ← All SQL queries + DCL (GRANT/REVOKE)
├── 05_Stored_Programming.sql       ← Procedures, Functions, Triggers, Cursors
├── 06_GUI/
│   ├── app.py                      ← Flask web application (backend)
│   ├── requirements.txt            ← Python dependencies
│   ├── static/
│   │   └── style.css               ← Global dark-theme stylesheet
│   └── templates/
│       ├── base.html               ← Base layout with sidebar
│       ├── login.html              ← Login page (2 roles)
│       ├── dashboard.html          ← Analytics dashboard
│       ├── patients.html           ← Patient list + search
│       ├── patient_form.html       ← Add/Edit patient form
│       ├── doctors.html            ← Doctor list
│       ├── doctor_form.html        ← Add doctor form
│       ├── appointments.html       ← Appointments list
│       ├── appointment_form.html   ← Schedule appointment
│       ├── admissions.html         ← Admissions list
│       ├── admission_form.html     ← Admit patient form
│       ├── billing.html            ← Billing + payment modal
│       ├── staff.html              ← Staff management
│       ├── reports.html            ← Exportable reports
│       └── error.html              ← Error/403 page
├── 07_ERD_EERD_Description.md      ← ERD/EERD design + normalization
└── 08_Final_Report.md              ← Complete project report
```

---

## ⚡ Quick Setup

### Prerequisites
- MySQL 8.0+ installed and running
- Python 3.10+ installed
- `pip` available

### Step 1 – Create Database
Open MySQL shell or MySQL Workbench and run in order:
```sql
SOURCE path/to/02_DDL_Schema.sql;
SOURCE path/to/03_Insert_Data.sql;
SOURCE path/to/05_Stored_Programming.sql;
```
Or via command line:
```bash
mysql -u root -p < 02_DDL_Schema.sql
mysql -u root -p hms_db < 03_Insert_Data.sql
mysql -u root -p hms_db < 05_Stored_Programming.sql
```

### Step 2 – Configure Database Connection
Edit `06_GUI/app.py` around line 19:
```python
DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",          # ← your MySQL username
    "password": "yourpassword",  # ← your MySQL password
    "database": "hms_db"
}
```

### Step 3 – Install Python Dependencies
```bash
cd 06_GUI
pip install flask mysql-connector-python
```

### Step 4 – Run the Application
```bash
python app.py
```
Then open your browser at: **http://localhost:5000**

---

## 🔐 Login Credentials

| Role    | Username      | Password    | Access Level          |
|---------|---------------|-------------|----------------------|
| Admin   | `admin`       | `Admin@123` | Full access          |
| Doctor  | `dr_ahmed`    | `Doc@1234`  | Appointments, Rx     |
| Doctor  | `dr_sara`     | `Doc@1234`  | Appointments, Rx     |
| Staff   | `staff_zahid` | `Staff@123` | Patients, Admissions |
| Viewer  | `viewer`      | `View@123`  | Reports only         |

---

## 📊 Database Summary

| Category | Details |
|----------|---------|
| Tables | 13 (10 core + 3 supporting) |
| Foreign Keys | 16 |
| CHECK constraints | 10 |
| UNIQUE constraints | 12 |
| Views | 2 |
| Indexes | 3 |
| Stored Procedures | 3 |
| Functions | 2 |
| Triggers | 3 |
| Cursors | 2 |
| Data rows | 170+ |

---

## 🏗 Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| STAFF as superclass | DOCTOR and NURSE share staff attributes (ISA hierarchy / EERD specialization) |
| PRESCRIPTION_DETAILS as weak entity | Medicines in a prescription have no meaning without the parent prescription |
| Billing linked to admission | One bill per admission allows outpatient bills (no admission_id) to coexist |
| SHA2-256 password hashing | MySQL native hashing using `SHA2(password, 256)` |
| Views for reporting | `v_patient_full_info` and `v_doctor_appointment_summary` encapsulate joins |
| Soft-delete on patients | `status='Inactive'` preserves referential integrity in child tables |

---

## 📚 Academic Requirements Coverage

| Requirement | Status |
|-------------|--------|
| Minimum 8 entities | ✅ 10 core entities |
| ERD & EERD | ✅ Described in `07_ERD_EERD_Description.md` |
| 3NF Normalization | ✅ Justified in ERD file + Final Report |
| DDL with constraints | ✅ 13 tables, 10 CHECKs, 16 FKs |
| 20 rows major tables | ✅ PATIENT, STAFF, ROOM, APPOINTMENT, MEDICINE all have 20 rows |
| SELECT/JOIN/Aggregate | ✅ 15 queries in `04_Queries.sql` |
| Subqueries (nested + correlated) | ✅ 3 subqueries |
| UPDATE / DELETE | ✅ 2 each |
| GRANT / REVOKE | ✅ 4 users, full DCL section |
| Stored Procedures (3) | ✅ With IN/OUT, exception handling, chaining |
| Functions (2) | ✅ Used in SELECT queries |
| Triggers (3) | ✅ BEFORE INSERT, AFTER UPDATE, AFTER DELETE |
| Cursors (2) | ✅ Explicit + parameterized |
| GUI Login (2 roles) | ✅ Admin + Doctor/Staff/Viewer |
| CRUD Forms (3+) | ✅ Patient, Doctor, Appointment, Admission, Billing |
| Search + filter | ✅ Patient search by name/phone/ID |
| Dashboard KPI cards (4) | ✅ Patients, Doctors, Admissions, Revenue |
| Charts (2) | ✅ Dept bar chart + monthly revenue line chart |
| Top 10 patient table | ✅ On dashboard |
| CSV export | ✅ `/reports/export/csv` |
| Data from DB (no hardcoding) | ✅ All data via Flask+MySQL queries |
| Real-time refresh | ✅ KPI cards auto-refresh every 30 seconds |
