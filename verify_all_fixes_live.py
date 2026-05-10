import time
import mysql.connector
import requests

BASE = "http://127.0.0.1:5000"


def db():
    return mysql.connector.connect(host="localhost", user="root", password="password", database="hms_db")


def q1(sql, params=()):
    conn = db()
    cur = conn.cursor()
    cur.execute(sql, params)
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None


def qall(sql, params=()):
    conn = db()
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def login(user, pw):
    s = requests.Session()
    r = s.post(f"{BASE}/", data={"email": user, "password": pw}, allow_redirects=False)
    return s, r


lines = []

# ── VERIFY FIX 1 SQL bits ────────────────────────────────
staff_id = q1("SELECT staff_id FROM USERS WHERE username='doctor_test'")
doctor_id = q1("SELECT doctor_id FROM DOCTOR WHERE staff_id=%s", (staff_id,))
lines.append(f"FIX1 staff_id={staff_id} doctor_id={doctor_id}")
lines.append(f"FIX1 appt_count_scoped={q1('SELECT COUNT(*) FROM APPOINTMENT WHERE doctor_id=%s', (doctor_id,))}")

# ── Live doctor scoping proof ────────────────────────────
sD, rD = login("doctor_test", "Doctor@123")
appt_html = sD.get(f"{BASE}/appointments").text
lines.append(f"FIX1 doctor_login={rD.status_code} loc={rD.headers.get('Location')}")
lines.append(f"FIX1 other_doctor_token_visible={'OTHERDOCONLY' in appt_html}")

# ── VERIFY FIX 2 live inserts ────────────────────────────
before_rx = q1("SELECT COUNT(*) FROM PRESCRIPTION")
before_pd = q1("SELECT COUNT(*) FROM PRESCRIPTION_DETAILS")
my_patient = q1("""
    SELECT DISTINCT p.patient_id
    FROM PATIENT p JOIN APPOINTMENT a ON a.patient_id=p.patient_id
    WHERE a.doctor_id=%s
    ORDER BY p.patient_id LIMIT 1
""", (doctor_id,))
med_id = q1("SELECT medicine_id FROM MEDICINE ORDER BY medicine_id LIMIT 1")

new_rx = sD.post(
    f"{BASE}/doctor/prescriptions/new",
    data={"patient_id": my_patient, "diagnosis": "VerifyFix2", "notes": "note"},
    allow_redirects=False,
)
loc = new_rx.headers.get("Location", "")
rx_id = int(loc.split("/")[-2]) if "/add_medicine" in loc else None
sD.post(
    f"{BASE}/doctor/prescriptions/{rx_id}/add_medicine",
    data={"medicine_id": med_id, "dosage": "1 tab", "frequency": "Daily", "duration": "3", "quantity": "3"},
    allow_redirects=False,
)
after_rx = q1("SELECT COUNT(*) FROM PRESCRIPTION")
after_pd = q1("SELECT COUNT(*) FROM PRESCRIPTION_DETAILS")
lines.append(f"FIX2 rx_created_status={new_rx.status_code} rx_id={rx_id}")
lines.append(f"FIX2 PRESCRIPTION before={before_rx} after={after_rx}")
lines.append(f"FIX2 PRESCRIPTION_DETAILS before={before_pd} after={after_pd}")
lines.append(f"FIX2 PRESCRIPTION_last={qall('SELECT prescription_id,patient_id,doctor_id,prescription_date FROM PRESCRIPTION ORDER BY prescription_id DESC LIMIT 1')}")
lines.append(f"FIX2 PD_last={qall('SELECT detail_id,prescription_id,medicine_id,dosage,duration_days,quantity FROM PRESCRIPTION_DETAILS ORDER BY detail_id DESC LIMIT 1')}")

# ── VERIFY FIX 3 Department CRUD live ─────────────────────
sA, rA = login("admin_test", "Admin@123")
lines.append(f"FIX3 admin_login={rA.status_code}")
dept_before = q1("SELECT COUNT(*) FROM DEPARTMENT")
add_name = "Neurology"
existing = q1("SELECT COUNT(*) FROM DEPARTMENT WHERE dept_name=%s", (add_name,))
if existing:
    add_name = f"Neurology_{int(time.time())%100000}"
sA.post(f"{BASE}/departments/add", data={"dept_name": add_name, "location": "Block X", "phone_ext": "1111", "description": "Dept"}, allow_redirects=False)
dept_id = q1("SELECT dept_id FROM DEPARTMENT WHERE dept_name=%s", (add_name,))
sA.post(f"{BASE}/departments/edit/{dept_id}", data={"dept_name": add_name, "location": "Block Y", "phone_ext": "1112", "description": "Updated"}, allow_redirects=False)
loc = qall("SELECT dept_name,location FROM DEPARTMENT WHERE dept_id=%s", (dept_id,))
sA.post(f"{BASE}/departments/delete/{dept_id}", allow_redirects=False)
dept_after = q1("SELECT COUNT(*) FROM DEPARTMENT")
lines.append(f"FIX3 dept_count_before={dept_before} dept_count_after={dept_after}")
lines.append(f"FIX3 neurology_row_after_edit={loc}")

cardio_id = q1("SELECT dept_id FROM DEPARTMENT WHERE dept_name='Cardiology'")
before_cardio = q1("SELECT COUNT(*) FROM DEPARTMENT WHERE dept_id=%s", (cardio_id,))
sA.post(f"{BASE}/departments/delete/{cardio_id}", allow_redirects=False)
after_cardio = q1("SELECT COUNT(*) FROM DEPARTMENT WHERE dept_id=%s", (cardio_id,))
lines.append(f"FIX3 delete_cardiology_blocked={before_cardio==after_cardio}")

# ── VERIFY FIX 4 Room CRUD live ───────────────────────────
room_before = q1("SELECT COUNT(*) FROM ROOM")
sA.post(f"{BASE}/rooms/add", data={"room_number": "401", "room_type": "Emergency", "dept_id": cardio_id, "capacity": "2", "daily_charge": "14000"}, allow_redirects=False)
room_row = qall("SELECT room_id,room_number,room_type,daily_charge FROM ROOM WHERE room_number='401'")
room_id = room_row[0][0]
sA.post(f"{BASE}/rooms/edit/{room_id}", data={"room_number": "401", "room_type": "Emergency", "dept_id": cardio_id, "capacity": "2", "daily_charge": "15000"}, allow_redirects=False)
edited = qall("SELECT daily_charge FROM ROOM WHERE room_id=%s", (room_id,))
sA.post(f"{BASE}/rooms/delete/{room_id}", allow_redirects=False)
room_after = q1("SELECT COUNT(*) FROM ROOM")
lines.append(f"FIX4 room_count_before={room_before} room_count_after={room_after}")
lines.append(f"FIX4 room_401_inserted={room_row}")
lines.append(f"FIX4 room_401_charge_after_edit={edited}")

rid_occ = q1("SELECT room_id FROM ROOM ORDER BY room_id LIMIT 1")
conn = db()
cur = conn.cursor()
cur.execute("UPDATE ROOM SET status='Occupied' WHERE room_id=%s", (rid_occ,))
conn.commit()
cur.close()
conn.close()
sA.post(f"{BASE}/rooms/delete/{rid_occ}", allow_redirects=False)
exists = q1("SELECT COUNT(*) FROM ROOM WHERE room_id=%s", (rid_occ,))
conn = db()
cur = conn.cursor()
cur.execute("UPDATE ROOM SET status='Available' WHERE room_id=%s", (rid_occ,))
conn.commit()
cur.close()
conn.close()
lines.append(f"FIX4 occupied_delete_blocked={exists==1}")

# ── VERIFY FIX 5 Medicine CRUD live ───────────────────────
med_before = q1("SELECT COUNT(*) FROM MEDICINE")
sA.post(f"{BASE}/medicines/add", data={"medicine_name": "Metformin", "generic_name": "Metformin", "category": "Antidiabetic", "unit_price": "55", "stock_quantity": "80", "manufacturer": "DemoPharma"}, allow_redirects=False)
met = qall("SELECT medicine_id,unit_price FROM MEDICINE WHERE medicine_name='Metformin'")
met_id = met[0][0]
sA.post(f"{BASE}/medicines/edit/{met_id}", data={"medicine_name": "Metformin", "generic_name": "Metformin", "category": "Antidiabetic", "unit_price": "60", "stock_quantity": "80", "manufacturer": "DemoPharma"}, allow_redirects=False)
price = qall("SELECT unit_price FROM MEDICINE WHERE medicine_id=%s", (met_id,))
sA.post(f"{BASE}/medicines/delete/{met_id}", allow_redirects=False)
med_after = q1("SELECT COUNT(*) FROM MEDICINE")
lines.append(f"FIX5 med_count_before={med_before} med_count_after={med_after}")
lines.append(f"FIX5 metformin_row={met} price_after_edit={price}")

used_med = q1("SELECT medicine_id FROM PRESCRIPTION_DETAILS ORDER BY detail_id LIMIT 1")
before_used = q1("SELECT COUNT(*) FROM MEDICINE WHERE medicine_id=%s", (used_med,))
sA.post(f"{BASE}/medicines/delete/{used_med}", allow_redirects=False)
after_used = q1("SELECT COUNT(*) FROM MEDICINE WHERE medicine_id=%s", (used_med,))
lines.append(f"FIX5 used_med_delete_blocked={before_used==after_used}")

# ── VERIFY FIX 6 Edit doctor_test fee and delete guard ────
doc_staff = q1("SELECT staff_id FROM USERS WHERE username='doctor_test'")
sA.post(f"{BASE}/doctors/edit/{doc_staff}", data={
    "first_name": "Ahsan",
    "last_name": "Qureshi",
    "phone": "+923001110001",
    "email": "doctor@hospital.com",
    "hire_date": "2026-05-07",
    "salary": "180000",
    "shift": "Morning",
    "status": "Active",
    "dept_id": cardio_id,
    "specialization": "Cardiologist",
    "license_number": "PMC-DOC-10001",
    "consultation_fee": "5000",
    "available_days": "Mon,Tue,Wed,Thu,Fri",
}, allow_redirects=False)
fee = q1("SELECT consultation_fee FROM DOCTOR WHERE staff_id=%s", (doc_staff,))
lines.append(f"FIX6 doctor_test_fee={fee}")

# ensure active appointment exists for doctor_test doctor_id
conn = db()
cur = conn.cursor()
pid = q1("SELECT patient_id FROM PATIENT WHERE status='Active' ORDER BY patient_id LIMIT 1")
cur.execute(
    "INSERT INTO APPOINTMENT (patient_id,doctor_id,appointment_date,appointment_time,reason,status) "
    "VALUES (%s,%s,DATE_ADD(CURDATE(), INTERVAL 3 DAY),'09:15:00','GUARDTEST','Scheduled')",
    (pid, doctor_id),
)
conn.commit()
cur.close()
conn.close()
doc_count_before = q1("SELECT COUNT(*) FROM DOCTOR")
sA.post(f"{BASE}/doctors/delete/{doc_staff}", allow_redirects=False)
doc_count_after = q1("SELECT COUNT(*) FROM DOCTOR")
lines.append(f"FIX6 delete_guard_worked={doc_count_before==doc_count_after}")

# ── VERIFY FIX 7 add/edit/delete Test Nurse + linked USERS ─
staff_before = q1("SELECT COUNT(*) FROM STAFF")
users_before = q1("SELECT COUNT(*) FROM USERS")
suffix = int(time.time()) % 100000
email = f"test.nurse.{suffix}@hospital.com"
phone = f"+92333{suffix:05d}"
sA.post(f"{BASE}/staff/add", data={
    "first_name": "Test",
    "last_name": "Nurse",
    "staff_type": "Nurse",
    "phone": phone,
    "email": email,
    "hire_date": "2026-05-07",
    "salary": "70000",
    "shift": "Morning",
}, allow_redirects=False)
staff_row = qall("SELECT staff_id,first_name,last_name,shift FROM STAFF ORDER BY staff_id DESC LIMIT 1")
new_staff_id = staff_row[0][0]
user_row = qall("SELECT user_id,username,email,role,staff_id FROM USERS ORDER BY user_id DESC LIMIT 1")
staff_after_add = q1("SELECT COUNT(*) FROM STAFF")
users_after_add = q1("SELECT COUNT(*) FROM USERS")

sA.post(f"{BASE}/staff/edit/{new_staff_id}", data={
    "first_name": "Test",
    "last_name": "Nurse",
    "staff_type": "Nurse",
    "phone": phone,
    "email": email,
    "hire_date": "2026-05-07",
    "salary": "70000",
    "shift": "Night",
    "status": "Active",
}, allow_redirects=False)
shift = q1("SELECT shift FROM STAFF WHERE staff_id=%s", (new_staff_id,))

sA.post(f"{BASE}/staff/delete/{new_staff_id}", allow_redirects=False)
staff_after_del = q1("SELECT COUNT(*) FROM STAFF")
users_after_del = q1("SELECT COUNT(*) FROM USERS")
lines.append(f"FIX7 staff_counts_before={staff_before} after_add={staff_after_add} after_del={staff_after_del}")
lines.append(f"FIX7 users_counts_before={users_before} after_add={users_after_add} after_del={users_after_del}")
lines.append(f"FIX7 staff_last_insert={staff_row}")
lines.append(f"FIX7 users_last_insert={user_row}")
lines.append(f"FIX7 nurse_shift_after_edit={shift}")

# ── VERIFY FIX 8 staff billing access + paid status ───────
sS, rS = login("staff_test", "Staff@123")
b = sS.get(f"{BASE}/billing")
g = sS.get(f"{BASE}/billing/generate")
count_b_before = q1("SELECT COUNT(*) FROM BILLING")
sS.post(f"{BASE}/billing/generate", data={"patient_id": pid, "admission_id": "", "total_amount": "999.00"}, allow_redirects=False)
bid = q1("SELECT bill_id FROM BILLING ORDER BY bill_id DESC LIMIT 1")
bill_last = qall("SELECT bill_id,patient_id,total_amount,paid_amount,payment_status FROM BILLING ORDER BY bill_id DESC LIMIT 1")
sS.post(f"{BASE}/billing/pay/{bid}", data={"amount": "999.00", "method": "Cash"}, allow_redirects=False)
status = q1("SELECT payment_status FROM BILLING ORDER BY bill_id DESC LIMIT 1")
lines.append(f"FIX8 staff_billing_pages={b.status_code},{g.status_code}")
lines.append(f"FIX8 bill_last={bill_last}")
lines.append(f"FIX8 status_after_pay={status}")

# ── Final count query ─────────────────────────────────────
final_counts = qall(
    """
SELECT 'USERS' as T, COUNT(*) FROM USERS
UNION ALL SELECT 'PATIENT', COUNT(*) FROM PATIENT
UNION ALL SELECT 'DOCTOR', COUNT(*) FROM DOCTOR
UNION ALL SELECT 'STAFF', COUNT(*) FROM STAFF
UNION ALL SELECT 'APPOINTMENT', COUNT(*) FROM APPOINTMENT
UNION ALL SELECT 'ADMISSION', COUNT(*) FROM ADMISSION
UNION ALL SELECT 'PRESCRIPTION', COUNT(*) FROM PRESCRIPTION
UNION ALL SELECT 'PRESCRIPTION_DETAILS', COUNT(*) FROM PRESCRIPTION_DETAILS
UNION ALL SELECT 'BILLING', COUNT(*) FROM BILLING
UNION ALL SELECT 'ROOM', COUNT(*) FROM ROOM
UNION ALL SELECT 'MEDICINE', COUNT(*) FROM MEDICINE
UNION ALL SELECT 'DEPARTMENT', COUNT(*) FROM DEPARTMENT
"""
)
lines.append(f"FINAL_COUNTS={final_counts}")

with open("verify_all_fixes_live_out.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

