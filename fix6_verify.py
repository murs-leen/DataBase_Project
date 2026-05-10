import time
import mysql.connector
import requests

BASE = "http://127.0.0.1:5000"

def q1(sql, params=()):
    conn = mysql.connector.connect(host="localhost", user="root", password="password", database="hms_db")
    cur = conn.cursor()
    cur.execute(sql, params)
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None

s = requests.Session()
login = s.post(f"{BASE}/", data={"email": "admin_test", "password": "Admin@123"}, allow_redirects=False)
view = s.get(f"{BASE}/doctors")

# Add a fresh doctor for edit/delete testing
suffix = int(time.time()) % 100000
dept_id = q1("SELECT dept_id FROM DEPARTMENT ORDER BY dept_id LIMIT 1")
add = s.post(
    f"{BASE}/doctors/add",
    data={
        "first_name": f"Fix6{suffix}",
        "last_name": "Doc",
        "phone": f"+92300{suffix:05d}",
        "email": f"fix6_{suffix}@hospital.com",
        "hire_date": "2026-05-07",
        "salary": "160000",
        "shift": "Morning",
        "dept_id": str(dept_id),
        "specialization": "General",
        "license_number": f"PMC-FIX6-{suffix}",
        "consultation_fee": "2800",
        "available_days": "Mon,Tue,Wed",
    },
    allow_redirects=False,
)
staff_id = q1("SELECT staff_id FROM STAFF WHERE email=%s", (f"fix6_{suffix}@hospital.com",))
doctor_id = q1("SELECT doctor_id FROM DOCTOR WHERE staff_id=%s", (staff_id,))

# Edit
edit = s.post(
    f"{BASE}/doctors/edit/{staff_id}",
    data={
        "first_name": f"Fix6{suffix}U",
        "last_name": "DocU",
        "phone": f"+92311{suffix:05d}",
        "email": f"fix6_{suffix}@hospital.com",
        "hire_date": "2026-05-07",
        "salary": "170000",
        "shift": "Evening",
        "status": "Active",
        "dept_id": str(dept_id),
        "specialization": "Updated Spec",
        "license_number": f"PMC-FIX6-{suffix}",
        "consultation_fee": "3000",
        "available_days": "Thu,Fri",
    },
    allow_redirects=False,
)
edited_ok = q1("SELECT COUNT(*) FROM DOCTOR d JOIN STAFF s ON s.staff_id=d.staff_id WHERE s.staff_id=%s AND d.specialization='Updated Spec' AND s.shift='Evening'", (staff_id,))

# Active appointment guard check: ensure at least one doctor has active scheduled appt
guard_doc = q1("""
    SELECT a.doctor_id
    FROM APPOINTMENT a
    WHERE a.status NOT IN ('Completed','Cancelled')
    ORDER BY a.appointment_id DESC
    LIMIT 1
""")
guard_staff_id = q1("SELECT staff_id FROM DOCTOR WHERE doctor_id=%s", (guard_doc,)) if guard_doc else None
if guard_staff_id:
    before_guard = q1("SELECT COUNT(*) FROM STAFF WHERE staff_id=%s", (guard_staff_id,))
    blocked = s.post(f"{BASE}/doctors/delete/{guard_staff_id}", allow_redirects=False)
    after_guard = q1("SELECT COUNT(*) FROM STAFF WHERE staff_id=%s", (guard_staff_id,))
else:
    blocked = None
    before_guard = -1
    after_guard = -1

# Delete fresh doctor (should pass)
del_ok = s.post(f"{BASE}/doctors/delete/{staff_id}", allow_redirects=False)
staff_after = q1("SELECT COUNT(*) FROM STAFF WHERE staff_id=%s", (staff_id,))
doctor_after = q1("SELECT COUNT(*) FROM DOCTOR WHERE staff_id=%s", (staff_id,))
user_after = q1("SELECT COUNT(*) FROM USERS WHERE staff_id=%s", (staff_id,))

with open("fix6_verify_out.txt", "w", encoding="utf-8") as f:
    f.write(f"login={login.status_code}:{login.headers.get('Location')}\n")
    f.write(f"view={view.status_code}\n")
    f.write(f"add={add.status_code}, staff_id={staff_id}, doctor_id={doctor_id}\n")
    f.write(f"edit={edit.status_code}, edited_ok={edited_ok}\n")
    if blocked:
        f.write(f"delete_blocked={blocked.status_code}, before_guard={before_guard}, after_guard={after_guard}\n")
    else:
        f.write("delete_blocked=SKIPPED(no active appointment doctor)\n")
    f.write(f"delete_ok={del_ok.status_code}, staff_after={staff_after}, doctor_after={doctor_after}, user_after={user_after}\n")
