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
view = s.get(f"{BASE}/medicines")

before = q1("SELECT COUNT(*) FROM MEDICINE")
suffix = int(time.time()) % 100000
name = f"TestMed{suffix}"
add = s.post(
    f"{BASE}/medicines/add",
    data={
        "medicine_name": name,
        "generic_name": f"Generic{suffix}",
        "category": "TestCat",
        "unit_price": "99.99",
        "stock_quantity": "50",
        "manufacturer": "TestPharma",
    },
    allow_redirects=False,
)
med_id = q1("SELECT medicine_id FROM MEDICINE WHERE medicine_name=%s", (name,))
after_add = q1("SELECT COUNT(*) FROM MEDICINE")

edit = s.post(
    f"{BASE}/medicines/edit/{med_id}",
    data={
        "medicine_name": name + "U",
        "generic_name": f"Generic{suffix}U",
        "category": "UpdatedCat",
        "unit_price": "120",
        "stock_quantity": "45",
        "manufacturer": "UpdatedPharma",
    },
    allow_redirects=False,
)
edited_ok = q1("SELECT COUNT(*) FROM MEDICINE WHERE medicine_id=%s AND category='UpdatedCat' AND stock_quantity=45", (med_id,))

# Guard test: pick medicine used in prescription_details
used_med = q1("SELECT medicine_id FROM PRESCRIPTION_DETAILS ORDER BY detail_id LIMIT 1")
if used_med:
    used_before = q1("SELECT COUNT(*) FROM MEDICINE WHERE medicine_id=%s", (used_med,))
    blocked = s.post(f"{BASE}/medicines/delete/{used_med}", allow_redirects=False)
    used_after = q1("SELECT COUNT(*) FROM MEDICINE WHERE medicine_id=%s", (used_med,))
else:
    blocked = None
    used_before = -1
    used_after = -1

delete_new = s.post(f"{BASE}/medicines/delete/{med_id}", allow_redirects=False)
new_after_del = q1("SELECT COUNT(*) FROM MEDICINE WHERE medicine_id=%s", (med_id,))

with open("fix5_verify_out.txt", "w", encoding="utf-8") as f:
    f.write(f"login={login.status_code}:{login.headers.get('Location')}\n")
    f.write(f"view={view.status_code}\n")
    f.write(f"add={add.status_code}, count_before={before}, count_after={after_add}, med_id={med_id}\n")
    f.write(f"edit={edit.status_code}, edited_ok={edited_ok}\n")
    if blocked:
        f.write(f"delete_blocked={blocked.status_code}, used_before={used_before}, used_after={used_after}\n")
    else:
        f.write("delete_blocked=SKIPPED(no used medicine)\n")
    f.write(f"delete_new={delete_new.status_code}, new_after_delete={new_after_del}\n")
