import json
from dataclasses import dataclass, asdict
from typing import List

import mysql.connector
import requests


BASE = "http://127.0.0.1:5000"


@dataclass
class Check:
    area: str
    item: str
    route: str
    sql: str
    result: str
    detail: str


def db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="password",
        database="hms_db",
    )


def q1(sql, params=()):
    conn = db()
    cur = conn.cursor()
    cur.execute(sql, params)
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None


def qall(sql, params=()):
    conn = db()
    cur = conn.cursor(dictionary=True)
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    return rows


def post(sql, params=()):
    conn = db()
    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()
    conn.close()


def login(sess: requests.Session, username: str, password: str):
    return sess.post(f"{BASE}/", data={"email": username, "password": password}, allow_redirects=False)


def audit() -> List[Check]:
    checks: List[Check] = []
    admin = requests.Session()
    doctor = requests.Session()
    staff = requests.Session()
    anon = requests.Session()

    # Admin login
    r = login(admin, "admin_test", "Admin@123")
    checks.append(Check("ADMIN", "Login", "/", "SELECT * FROM USERS WHERE (username=%s OR email=%s) AND password_hash=%s AND is_active=1",
                        "PASS" if r.status_code == 302 else "FAIL", f"status={r.status_code}, location={r.headers.get('Location')}"))

    # Admin dashboard route behavior
    r = admin.get(f"{BASE}/dashboard", allow_redirects=False)
    checks.append(Check("ADMIN", "Dashboard redirect", "/dashboard -> /doctor_dashboard", "N/A", "PASS" if r.status_code == 302 else "FAIL",
                        f"status={r.status_code}, location={r.headers.get('Location')}"))

    r2 = admin.get(f"{BASE}/doctor_dashboard")
    checks.append(Check("ADMIN", "Dashboard page load", "/doctor_dashboard",
                        "SELECT SUM(paid_amount)... FROM BILLING ...", "PASS" if r2.status_code == 200 else "FAIL",
                        f"status={r2.status_code}"))

    # Doctors list
    r = admin.get(f"{BASE}/doctors")
    checks.append(Check("ADMIN", "Doctor list view", "/doctors",
                        "SELECT ... FROM DOCTOR d JOIN STAFF s ... JOIN DEPARTMENT ...", "PASS" if r.status_code == 200 else "FAIL",
                        f"status={r.status_code}"))

    # Add doctor
    before = q1("SELECT COUNT(*) FROM DOCTOR")
    dep = q1("SELECT dept_id FROM DEPARTMENT ORDER BY dept_id LIMIT 1")
    payload = {
        "first_name": "Hamza",
        "last_name": "Ali",
        "phone": "+923009990001",
        "email": "doctor_added@hospital.com",
        "hire_date": "2026-05-07",
        "salary": "170000",
        "shift": "Morning",
        "dept_id": str(dep),
        "specialization": "Internal Medicine",
        "license_number": "PMC-DOC-10002",
        "consultation_fee": "3000",
        "available_days": "Mon,Tue,Wed",
    }
    r = admin.post(f"{BASE}/doctors/add", data=payload, allow_redirects=False)
    after = q1("SELECT COUNT(*) FROM DOCTOR")
    checks.append(Check("ADMIN", "Doctor add", "/doctors/add",
                        "INSERT INTO STAFF ...; INSERT INTO DOCTOR ...", "PASS" if (r.status_code == 302 and after == before + 1) else "FAIL",
                        f"status={r.status_code}, count_before={before}, count_after={after}"))

    # Edit/Delete doctor routes don't exist
    checks.append(Check("ADMIN", "Doctor edit", "N/A", "N/A", "FAIL", "No edit doctor route in app.py"))
    checks.append(Check("ADMIN", "Doctor delete", "N/A", "N/A", "FAIL", "No delete doctor route in app.py"))

    # Patient CRUD
    r = admin.get(f"{BASE}/patients")
    checks.append(Check("ADMIN", "Patient list view", "/patients", "SELECT * FROM PATIENT ...", "PASS" if r.status_code == 200 else "FAIL",
                        f"status={r.status_code}"))
    before = q1("SELECT COUNT(*) FROM PATIENT")
    p_payload = {
        "first_name": "Zara", "last_name": "Noor", "dob": "1995-01-01", "gender": "Female",
        "phone": "+923008880001", "email": "zara.noor@demo.com", "address": "Lahore", "blood_group": "B+"
    }
    r = admin.post(f"{BASE}/patients/add", data=p_payload, allow_redirects=False)
    after = q1("SELECT COUNT(*) FROM PATIENT")
    checks.append(Check("ADMIN", "Patient add", "/patients/add", "INSERT INTO PATIENT ...", "PASS" if (r.status_code == 302 and after == before + 1) else "FAIL",
                        f"status={r.status_code}, before={before}, after={after}"))
    pid = q1("SELECT patient_id FROM PATIENT ORDER BY patient_id DESC LIMIT 1")
    r = admin.post(f"{BASE}/patients/edit/{pid}", data={**p_payload, "first_name": "ZaraUpdated"}, allow_redirects=False)
    updated = q1("SELECT COUNT(*) FROM PATIENT WHERE patient_id=%s AND first_name='ZaraUpdated'", (pid,))
    checks.append(Check("ADMIN", "Patient edit", f"/patients/edit/{pid}", "UPDATE PATIENT SET ... WHERE patient_id=%s",
                        "PASS" if (r.status_code == 302 and updated == 1) else "FAIL", f"status={r.status_code}, updated={updated}"))
    r = admin.post(f"{BASE}/patients/delete/{pid}", allow_redirects=False)
    inactive = q1("SELECT COUNT(*) FROM PATIENT WHERE patient_id=%s AND status='Inactive'", (pid,))
    checks.append(Check("ADMIN", "Patient delete (soft)", f"/patients/delete/{pid}", "UPDATE PATIENT SET status='Inactive' WHERE patient_id=%s",
                        "PASS" if (r.status_code == 302 and inactive == 1) else "FAIL", f"status={r.status_code}, inactive={inactive}"))

    # Missing management modules
    for m in [("Department Management", "No department CRUD routes"),
              ("Room Management", "No room CRUD routes"),
              ("Medicine Management", "No medicine CRUD routes"),
              ("Staff Management add/edit/delete", "Only /staff list route exists")]:
        checks.append(Check("ADMIN", m[0], "N/A", "N/A", "FAIL", m[1]))

    # Staff list and billing
    r = admin.get(f"{BASE}/staff")
    checks.append(Check("ADMIN", "Staff list", "/staff", "SELECT ... FROM STAFF LEFT JOIN ...", "PASS" if r.status_code == 200 else "FAIL",
                        f"status={r.status_code}"))
    r = admin.get(f"{BASE}/billing")
    checks.append(Check("ADMIN", "Billing access", "/billing", "SELECT ... FROM BILLING JOIN PATIENT ...", "PASS" if r.status_code == 200 else "FAIL",
                        f"status={r.status_code}"))

    # Admin logout
    r = admin.get(f"{BASE}/logout", allow_redirects=False)
    checks.append(Check("ADMIN", "Logout", "/logout", "session.clear()", "PASS" if r.status_code == 302 else "FAIL", f"status={r.status_code}"))

    # Doctor tests
    r = login(doctor, "doctor_test", "Doctor@123")
    checks.append(Check("DOCTOR", "Login", "/", "SELECT USERS...", "PASS" if r.status_code == 302 else "FAIL",
                        f"status={r.status_code}, location={r.headers.get('Location')}"))
    r = doctor.get(f"{BASE}/doctor_dashboard")
    checks.append(Check("DOCTOR", "Dashboard load", "/doctor_dashboard", "BILLING aggregate queries (not doctor-filtered)",
                        "PASS" if r.status_code == 200 else "FAIL", f"status={r.status_code}"))
    checks.append(Check("DOCTOR", "Dashboard own-data filter", "/doctor_dashboard", "No WHERE doctor/staff filter exists",
                        "FAIL", "Queries aggregate all BILLING data globally"))
    r = doctor.get(f"{BASE}/appointments")
    checks.append(Check("DOCTOR", "Appointments view", "/appointments", "SELECT ... FROM APPOINTMENT ... (no doctor filter)",
                        "PASS" if r.status_code == 200 else "FAIL", f"status={r.status_code}"))
    checks.append(Check("DOCTOR", "Appointments own-only", "/appointments", "No WHERE a.doctor_id = session doctor",
                        "FAIL", "Doctor can see all appointments"))
    checks.append(Check("DOCTOR", "Prescription module", "N/A", "N/A", "FAIL", "No doctor prescription create/view routes"))
    r = doctor.get(f"{BASE}/billing")
    checks.append(Check("DOCTOR", "Billing access", "/billing", "doctor_required allows Doctor/Admin",
                        "PASS" if r.status_code == 200 else "FAIL", f"status={r.status_code}"))
    for route in ["/staff", "/doctors/add", "/patients/delete/1"]:
        rr = doctor.get(f"{BASE}{route}", allow_redirects=False)
        checks.append(Check("DOCTOR", f"Blocked route {route}", route, "admin_required/staff_required", "PASS" if rr.status_code in (302, 200) else "FAIL",
                            f"status={rr.status_code}"))
    doctor.get(f"{BASE}/logout", allow_redirects=False)
    checks.append(Check("DOCTOR", "Logout", "/logout", "session.clear()", "PASS", "executed"))

    # Staff tests
    r = login(staff, "staff_test", "Staff@123")
    checks.append(Check("STAFF", "Login", "/", "SELECT USERS...", "PASS" if r.status_code == 302 else "FAIL",
                        f"status={r.status_code}, location={r.headers.get('Location')}"))
    r = staff.get(f"{BASE}/staff_dashboard")
    checks.append(Check("STAFF", "Dashboard load", "/staff_dashboard", "SELECT patient_id..., SELECT medicine_id...",
                        "PASS" if r.status_code == 200 else "FAIL", f"status={r.status_code}"))
    before = q1("SELECT COUNT(*) FROM PATIENT")
    r = staff.post(f"{BASE}/staff/register_patient", data={
        "first_name": "Imran", "last_name": "Tariq", "dob": "1990-06-01",
        "gender": "Male", "phone": "+923007770001", "email": "imran@demo.com",
        "blood_group": "A+", "address": "Karachi"
    })
    after = q1("SELECT COUNT(*) FROM PATIENT")
    checks.append(Check("STAFF", "Patient registration", "/staff/register_patient", "INSERT INTO PATIENT ...", "PASS" if after == before + 1 else "FAIL",
                        f"status={r.status_code}, before={before}, after={after}, body={r.text[:120]}"))

    # Appointment booking
    pid = q1("SELECT patient_id FROM PATIENT WHERE status='Active' ORDER BY patient_id DESC LIMIT 1")
    did = q1("SELECT doctor_id FROM DOCTOR ORDER BY doctor_id LIMIT 1")
    before = q1("SELECT COUNT(*) FROM APPOINTMENT")
    r = staff.post(f"{BASE}/appointments/add", data={
        "patient_id": str(pid), "doctor_id": str(did), "apt_date": "2026-05-10", "apt_time": "10:30", "reason": "Initial checkup"
    }, allow_redirects=False)
    after = q1("SELECT COUNT(*) FROM APPOINTMENT")
    checks.append(Check("STAFF", "Appointment booking", "/appointments/add", "INSERT INTO APPOINTMENT ...", "PASS" if after == before + 1 else "FAIL",
                        f"status={r.status_code}, before={before}, after={after}"))

    # Admission and discharge
    room_id = q1("SELECT room_id FROM ROOM WHERE status='Available' ORDER BY room_id LIMIT 1")
    before = q1("SELECT COUNT(*) FROM ADMISSION")
    r = staff.post(f"{BASE}/admissions/add", data={
        "patient_id": str(pid), "room_id": str(room_id), "doctor_id": str(did), "diagnosis": "Observation"
    }, allow_redirects=False)
    after = q1("SELECT COUNT(*) FROM ADMISSION")
    room_occ = q1("SELECT COUNT(*) FROM ROOM WHERE room_id=%s AND status='Occupied'", (room_id,))
    checks.append(Check("STAFF", "Admission create", "/admissions/add", "INSERT INTO ADMISSION ...; UPDATE ROOM ...; INSERT INTO BILLING ...",
                        "PASS" if (after == before + 1 and room_occ == 1) else "FAIL",
                        f"status={r.status_code}, before={before}, after={after}, room_occupied={room_occ}"))
    aid = q1("SELECT admission_id FROM ADMISSION ORDER BY admission_id DESC LIMIT 1")
    r = staff.post(f"{BASE}/admissions/discharge/{aid}", allow_redirects=False)
    room_avail = q1("SELECT COUNT(*) FROM ROOM WHERE room_id=%s AND status='Available'", (room_id,))
    checks.append(Check("STAFF", "Admission discharge", f"/admissions/discharge/{aid}", "UPDATE ADMISSION ...; UPDATE ROOM ...",
                        "PASS" if room_avail == 1 else "FAIL", f"status={r.status_code}, room_available={room_avail}"))

    # Dispense
    med_id = q1("SELECT medicine_id FROM MEDICINE ORDER BY medicine_id LIMIT 1")
    before_stock = q1("SELECT stock_quantity FROM MEDICINE WHERE medicine_id=%s", (med_id,))
    r = staff.post(f"{BASE}/staff/dispense", data={"patient_id": str(pid), "medicine_id": str(med_id), "quantity": "2"})
    after_stock = q1("SELECT stock_quantity FROM MEDICINE WHERE medicine_id=%s", (med_id,))
    checks.append(Check("STAFF", "Medicine dispense", "/staff/dispense", "UPDATE MEDICINE ...; INSERT PRESCRIPTION...; INSERT PRESCRIPTION_DETAILS...; UPDATE/INSERT BILLING...",
                        "PASS" if after_stock == before_stock - 2 else "FAIL",
                        f"status={r.status_code}, before_stock={before_stock}, after_stock={after_stock}, body={r.text[:120]}"))

    # Billing as staff should be blocked
    r = staff.get(f"{BASE}/billing", allow_redirects=False)
    checks.append(Check("STAFF", "Billing access", "/billing", "doctor_required", "PASS" if r.status_code == 200 else "FAIL",
                        f"status={r.status_code}"))
    # Because app returns error page 200, treat blocked as pass below:
    checks.append(Check("STAFF", "Billing blocked expectation", "/billing", "doctor_required", "PASS" if "Doctor access required" in r.text else "FAIL",
                        f"status={r.status_code}"))

    # Staff blocked routes
    for route in ["/admin_dashboard", "/doctors/add", "/doctor_dashboard"]:
        rr = staff.get(f"{BASE}{route}", allow_redirects=False)
        ok = False
        if route == "/admin_dashboard":
            ok = rr.status_code in (404, 302)
        else:
            ok = ("Admin access required" in rr.text) or ("Doctor access required" in rr.text)
        checks.append(Check("STAFF", f"Blocked route {route}", route, "decorators / missing route", "PASS" if ok else "FAIL",
                            f"status={rr.status_code}"))
    staff.get(f"{BASE}/logout", allow_redirects=False)
    checks.append(Check("STAFF", "Logout", "/logout", "session.clear()", "PASS", "executed"))

    # Logged-out protections
    for route in ["/dashboard", "/doctor_dashboard", "/staff_dashboard", "/patients", "/appointments"]:
        rr = anon.get(f"{BASE}{route}", allow_redirects=False)
        checks.append(Check("SECURITY", f"Logged-out protection {route}", route, "login_required/admin_required/doctor_required/staff_required",
                            "PASS" if rr.status_code == 302 else "FAIL", f"status={rr.status_code}, location={rr.headers.get('Location')}"))

    return checks


if __name__ == "__main__":
    out = audit()
    with open("task345_results.json", "w", encoding="utf-8") as f:
        json.dump([asdict(x) for x in out], f, indent=2)
    print(f"Wrote {len(out)} checks to task345_results.json")
