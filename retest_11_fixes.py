import requests
import mysql.connector

BASE = "http://127.0.0.1:5000"


def q1(sql, params=()):
    conn = mysql.connector.connect(host="localhost", user="root", password="password", database="hms_db")
    cur = conn.cursor()
    cur.execute(sql, params)
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None


def login(username, password):
    s = requests.Session()
    r = s.post(f"{BASE}/", data={"email": username, "password": password}, allow_redirects=False)
    return s, r


results = []

# Fix1: doctor scoping (appointments)
s, r = login("doctor_test", "Doctor@123")
ap = s.get(f"{BASE}/appointments")
results.append(("Fix1 appointments scoped", r.status_code == 302 and "OTHERDOCONLY" not in ap.text))

# Fix2: doctor prescription module routes exist
lst = s.get(f"{BASE}/doctor/prescriptions")
new = s.get(f"{BASE}/doctor/prescriptions/new")
results.append(("Fix2 routes exist", lst.status_code == 200 and new.status_code == 200))

# Fix3: department list exists
sA, rA = login("admin_test", "Admin@123")
dep = sA.get(f"{BASE}/departments")
results.append(("Fix3 departments page", dep.status_code == 200))

# Fix4: rooms list exists
rooms = sA.get(f"{BASE}/rooms")
results.append(("Fix4 rooms page", rooms.status_code == 200))

# Fix5: medicines list exists
meds = sA.get(f"{BASE}/medicines")
results.append(("Fix5 medicines page", meds.status_code == 200))

# Fix6: doctor edit route exists
sid = q1("SELECT staff_id FROM DOCTOR ORDER BY doctor_id DESC LIMIT 1")
ed = sA.get(f"{BASE}/doctors/edit/{sid}")
results.append(("Fix6 doctor edit page", ed.status_code == 200))

# Fix7: staff add page exists
stadd = sA.get(f"{BASE}/staff/add")
results.append(("Fix7 staff add page", stadd.status_code == 200))

# Fix8: staff billing access + generate/view exist
sS, rS = login("staff_test", "Staff@123")
bill = sS.get(f"{BASE}/billing")
gen = sS.get(f"{BASE}/billing/generate")
results.append(("Fix8 staff billing access", bill.status_code == 200 and gen.status_code == 200))

with open("retest_11_fixes_out.txt", "w", encoding="utf-8") as f:
    for name, ok in results:
        f.write(f"{name}: {'PASS' if ok else 'FAIL'}\n")
