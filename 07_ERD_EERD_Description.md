# ERD & EERD – Hospital Management System
## Textual Description (For Drawing in draw.io / Lucidchart / ERDPlus)

---

## 1. ENTITY LIST & PRIMARY KEYS

| Entity | PK | Notes |
|--------|----|-------|
| PATIENT | patient_id | Core entity |
| STAFF | staff_id | Superclass |
| DOCTOR | doctor_id | Subclass of STAFF |
| NURSE | nurse_id | Subclass of STAFF |
| DEPARTMENT | dept_id | Lookup entity |
| ROOM | room_id | Physical room |
| APPOINTMENT | appointment_id | Relationship entity |
| ADMISSION | admission_id | Inpatient record |
| BILLING | bill_id | Financial record |
| PRESCRIPTION | prescription_id | Medical orders |
| MEDICINE | medicine_id | Drug catalogue |
| PRESCRIPTION_DETAILS | detail_id | Weak Entity / Junction |
| USERS | user_id | Login accounts |

---

## 2. RELATIONSHIPS (ERD)

### One-to-Many (1:M)
```
PATIENT      ──<  APPOINTMENT      (1 patient → many appointments)
DOCTOR       ──<  APPOINTMENT      (1 doctor → many appointments)
PATIENT      ──<  ADMISSION        (1 patient → many admissions)
ROOM         ──<  ADMISSION        (1 room → many admissions over time)
PATIENT      ──<  PRESCRIPTION     (1 patient → many prescriptions)
DOCTOR       ──<  PRESCRIPTION     (1 doctor → many prescriptions)
DEPARTMENT   ──<  DOCTOR           (1 department → many doctors)
DEPARTMENT   ──<  ROOM             (1 department → many rooms)
```

### One-to-One (1:1)
```
PATIENT      ──── BILLING          (1 patient → 1 active bill per admission)
```
*(Enforced logically via admission_id linkage)*

### Many-to-Many (M:M) — via Junction Table
```
PRESCRIPTION  ><  MEDICINE
       resolved via: PRESCRIPTION_DETAILS (detail_id, prescription_id, medicine_id)
```

### EERD – Specialization (ISA Hierarchy)
```
        STAFF  (Superclass)
           |
    ┌──────┴──────┐
  DOCTOR        NURSE
(doctor_id)  (nurse_id)
   FK:staff_id  FK:staff_id

Constraint: Partial, Overlapping
(Not all staff are doctors/nurses; a staff member cannot be both)
```

### Weak Entity
```
PRESCRIPTION  ──{  PRESCRIPTION_DETAILS
                   (Existence-dependent on PRESCRIPTION)
                   Partial Key: (prescription_id, medicine_id)
```

### Aggregation / Composition
```
[ APPOINTMENT ] aggregated into ── PRESCRIPTION
An appointment is the context (aggregate) from which prescriptions emerge.
PRESCRIPTION references APPOINTMENT(appointment_id) with SET NULL on delete,
meaning the prescription persists even if the appointment record is removed.
```

---

## 3. ATTRIBUTE DETAILS PER ENTITY

### PATIENT
- patient_id (PK), first_name, last_name, date_of_birth, gender (multi-valued domain)
- phone (UNIQUE), email (UNIQUE), address, blood_group, registration_date, status

### STAFF
- staff_id (PK), first_name, last_name, staff_type (derived attribute for subclasses)
- phone (UNIQUE), email (UNIQUE), hire_date, salary, shift, status

### DOCTOR (Subclass of STAFF)
- doctor_id (PK), staff_id (FK), dept_id (FK)
- specialization, license_number (UNIQUE), consultation_fee, available_days

### NURSE (Subclass of STAFF)
- nurse_id (PK), staff_id (FK, UNIQUE), ward_assignment, certification

### DEPARTMENT
- dept_id (PK), dept_name (UNIQUE), location, phone_ext (UNIQUE), description

### ROOM
- room_id (PK), room_number (UNIQUE), room_type, dept_id (FK)
- capacity, daily_charge, status (derived: Available/Occupied/Maintenance)

### APPOINTMENT
- appointment_id (PK), patient_id (FK), doctor_id (FK)
- appointment_date, appointment_time, reason, status, notes

### ADMISSION
- admission_id (PK), patient_id (FK), room_id (FK), attending_doctor (FK)
- admit_date, discharge_date (nullable), diagnosis, status

### BILLING
- bill_id (PK), patient_id (FK), admission_id (FK)
- total_amount, paid_amount, bill_date, payment_status (derived), payment_method

### PRESCRIPTION
- prescription_id (PK), patient_id (FK), doctor_id (FK), appointment_id (FK nullable)
- prescription_date, notes

### MEDICINE
- medicine_id (PK), medicine_name (UNIQUE), generic_name, category
- unit_price, stock_quantity, manufacturer

### PRESCRIPTION_DETAILS (Weak Entity)
- detail_id (PK), prescription_id (FK — identifying relationship)
- medicine_id (FK), dosage, duration_days, quantity

---

## 4. EERD DIAGRAM ELEMENTS CHECKLIST

| EERD Feature | Implementation |
|-------------|----------------|
| ✅ Specialization (ISA) | STAFF → DOCTOR, NURSE |
| ✅ Weak Entity | PRESCRIPTION_DETAILS (depends on PRESCRIPTION) |
| ✅ One-to-One | PATIENT → BILLING (per admission) |
| ✅ One-to-Many (2+) | PATIENT→APPOINTMENT, DEPT→DOCTOR, ROOM→ADMISSION |
| ✅ Many-to-Many | PRESCRIPTION ↔ MEDICINE via PRESCRIPTION_DETAILS |
| ✅ Aggregation | APPOINTMENT aggregated into PRESCRIPTION |
| ✅ Partial participation | NURSE, DOCTOR partial subclasses of STAFF |
| ✅ Total participation | DOCTOR must belong to a DEPARTMENT |

---

## 5. NORMALIZATION JUSTIFICATION (3NF)

### 1NF (First Normal Form)
All tables satisfy 1NF:
- All attributes contain atomic values (no multi-valued or composite attributes stored)
- Each column has a single data type
- All rows are uniquely identified by a Primary Key

### 2NF (Second Normal Form)
All tables satisfy 2NF (no partial dependencies):
- All non-key attributes depend on the WHOLE primary key
- PRESCRIPTION_DETAILS: both `prescription_id` and `medicine_id` together determine
  dosage/duration — no partial dependency on either alone

### 3NF (Third Normal Form)
All tables satisfy 3NF (no transitive dependencies):
- BILLING: payment_status is functionally determined by (paid_amount, total_amount),
  not by a non-key attribute through another non-key — resolved by CASE in trigger/query
- DOCTOR: consultation_fee depends only on doctor_id (PK), not transitively via dept
- ADMISSION: diagnosis depends on admission_id, not transitively via patient or room
- ROOM: room attributes depend only on room_id, dept information in separate DEPARTMENT table
- No redundant data: doctor names not repeated in APPOINTMENT; room details not in ADMISSION

### BCNF check:
All determinants in each table are candidate keys — BCNF satisfied.

---

## 6. HOW TO DRAW IN draw.io

1. Open draw.io → New Diagram → Entity Relationship
2. Create rectangles for each entity with double border for weak entities
3. Add diamonds for relationships; double diamonds for identifying relationships
4. Use dashed lines with arrows for ISA hierarchies (STAFF → DOCTOR/NURSE)
5. Use "crow's foot" notation for cardinalities
6. Mark PK attributes with underline; derived attributes with dashed ellipse
7. Add "d" in ISA circle for disjoint, "o" for overlapping specializations
