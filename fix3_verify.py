import time
import mysql.connector
import requests

BASE = "http://127.0.0.1:5000"

s = requests.Session()
login = s.post(f"{BASE}/", data={"email": "admin_test", "password": "Admin@123"}, allow_redirects=False)

def q1(sql, params=()):
    conn = mysql.connector.connect(host="localhost", user="root", password="password", database="hms_db")
    cur = conn.cursor()
    cur.execute(sql, params)
    row = cur.fetchone()
    cur.close()
    conn.close()
    return row[0] if row else None

# View
view = s.get(f"{BASE}/departments")

# Add
before = q1("SELECT COUNT(*) FROM DEPARTMENT")
suffix = int(time.time()) % 100000
name = f"Neurology Test {suffix}"
add = s.post(
    f"{BASE}/departments/add",
    data={
        "dept_name": name,
        "location": "Block C",
        "phone_ext": f"{suffix}",
        "description": "Neuro test department"
    },
    allow_redirects=False,
)
new_id = q1("SELECT dept_id FROM DEPARTMENT WHERE dept_name=%s LIMIT 1", (name,))
after_add = q1("SELECT COUNT(*) FROM DEPARTMENT")

# Edit
edit = s.post(
    f"{BASE}/departments/edit/{new_id}",
    data={
        "dept_name": "Neurology Test Updated",
        "location": "Block D",
        "phone_ext": "1098",
        "description": "Updated"
    },
    allow_redirects=False,
)
edited_ok = q1("SELECT COUNT(*) FROM DEPARTMENT WHERE dept_id=%s AND dept_name='Neurology Test Updated'", (new_id,))

# Delete blocked (department with doctors)
cardio_id = q1("SELECT dept_id FROM DEPARTMENT WHERE dept_name='Cardiology' LIMIT 1")
cardio_before = q1("SELECT COUNT(*) FROM DEPARTMENT WHERE dept_id=%s", (cardio_id,))
blocked = s.post(f"{BASE}/departments/delete/{cardio_id}", allow_redirects=False)
cardio_after = q1("SELECT COUNT(*) FROM DEPARTMENT WHERE dept_id=%s", (cardio_id,))

# Delete allowed (new dept)
delete_new = s.post(f"{BASE}/departments/delete/{new_id}", allow_redirects=False)
new_after_del = q1("SELECT COUNT(*) FROM DEPARTMENT WHERE dept_id=%s", (new_id,))

with open("fix3_verify_out.txt", "w", encoding="utf-8") as f:
    f.write(f"login={login.status_code}:{login.headers.get('Location')}\n")
    f.write(f"view={view.status_code}\n")
    f.write(f"add={add.status_code}, count_before={before}, count_after={after_add}, new_id={new_id}\n")
    f.write(f"edit={edit.status_code}, edited_ok={edited_ok}\n")
    f.write(f"delete_blocked={blocked.status_code}, cardio_before={cardio_before}, cardio_after={cardio_after}\n")
    f.write(f"delete_new={delete_new.status_code}, new_after_delete={new_after_del}\n")
