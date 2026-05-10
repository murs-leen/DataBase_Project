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
view = s.get(f"{BASE}/staff")

suffix = int(time.time()) % 100000
email = f"staff_fix7_{suffix}@hospital.com"
phone = f"+92322{suffix:05d}"

before_staff = q1("SELECT COUNT(*) FROM STAFF")
before_users = q1("SELECT COUNT(*) FROM USERS")

add = s.post(
    f"{BASE}/staff/add",
    data={
        "first_name": "Fix7",
        "last_name": f"User{suffix}",
        "staff_type": "Technician",
        "phone": phone,
        "email": email,
        "hire_date": "2026-05-07",
        "salary": "75000",
        "shift": "Night",
    },
    allow_redirects=False,
)

staff_id = q1("SELECT staff_id FROM STAFF WHERE email=%s", (email,))
user_id = q1("SELECT user_id FROM USERS WHERE staff_id=%s", (staff_id,))
after_staff = q1("SELECT COUNT(*) FROM STAFF")
after_users = q1("SELECT COUNT(*) FROM USERS")

edit = s.post(
    f"{BASE}/staff/edit/{staff_id}",
    data={
        "first_name": "Fix7U",
        "last_name": f"User{suffix}U",
        "staff_type": "Admin",
        "phone": phone,
        "email": email,
        "hire_date": "2026-05-07",
        "salary": "80000",
        "shift": "Evening",
        "status": "Active",
    },
    allow_redirects=False,
)
edited_ok = q1("SELECT COUNT(*) FROM STAFF WHERE staff_id=%s AND first_name='Fix7U' AND shift='Evening' AND staff_type='Admin'", (staff_id,))

delete = s.post(f"{BASE}/staff/delete/{staff_id}", allow_redirects=False)
staff_after = q1("SELECT COUNT(*) FROM STAFF WHERE staff_id=%s", (staff_id,))
user_after = q1("SELECT COUNT(*) FROM USERS WHERE staff_id=%s", (staff_id,))

with open("fix7_verify_out.txt", "w", encoding="utf-8") as f:
    f.write(f"login={login.status_code}:{login.headers.get('Location')}\n")
    f.write(f"view={view.status_code}\n")
    f.write(f"add={add.status_code}, before_staff={before_staff}, after_staff={after_staff}, staff_id={staff_id}\n")
    f.write(f"users_linked=user_id={user_id}, before_users={before_users}, after_users={after_users}\n")
    f.write(f"edit={edit.status_code}, edited_ok={edited_ok}\n")
    f.write(f"delete={delete.status_code}, staff_after={staff_after}, user_after={user_after}\n")
