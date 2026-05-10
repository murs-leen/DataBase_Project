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

view = s.get(f"{BASE}/rooms")

before = q1("SELECT COUNT(*) FROM ROOM")
suffix = int(time.time()) % 100000
room_number = f"R{suffix}"
dept_id = q1("SELECT dept_id FROM DEPARTMENT ORDER BY dept_id LIMIT 1")
add = s.post(
    f"{BASE}/rooms/add",
    data={
        "room_number": room_number,
        "room_type": "Private",
        "dept_id": str(dept_id),
        "capacity": "1",
        "daily_charge": "9000"
    },
    allow_redirects=False,
)
room_id = q1("SELECT room_id FROM ROOM WHERE room_number=%s", (room_number,))
after_add = q1("SELECT COUNT(*) FROM ROOM")

edit = s.post(
    f"{BASE}/rooms/edit/{room_id}",
    data={
        "room_number": room_number + "X",
        "room_type": "ICU",
        "dept_id": str(dept_id),
        "capacity": "2",
        "daily_charge": "12000"
    },
    allow_redirects=False,
)
edited_ok = q1("SELECT COUNT(*) FROM ROOM WHERE room_id=%s AND room_type='ICU' AND capacity=2", (room_id,))

# occupied guard
occ_id = q1("SELECT room_id FROM ROOM WHERE status='Occupied' ORDER BY room_id LIMIT 1")
if occ_id:
    occ_before = q1("SELECT COUNT(*) FROM ROOM WHERE room_id=%s", (occ_id,))
    blocked = s.post(f"{BASE}/rooms/delete/{occ_id}", allow_redirects=False)
    occ_after = q1("SELECT COUNT(*) FROM ROOM WHERE room_id=%s", (occ_id,))
else:
    blocked = None
    occ_before = -1
    occ_after = -1

delete_new = s.post(f"{BASE}/rooms/delete/{room_id}", allow_redirects=False)
new_after_del = q1("SELECT COUNT(*) FROM ROOM WHERE room_id=%s", (room_id,))

with open("fix4_verify_out.txt", "w", encoding="utf-8") as f:
    f.write(f"login={login.status_code}:{login.headers.get('Location')}\n")
    f.write(f"view={view.status_code}\n")
    f.write(f"add={add.status_code}, count_before={before}, count_after={after_add}, room_id={room_id}\n")
    f.write(f"edit={edit.status_code}, edited_ok={edited_ok}\n")
    if blocked:
        f.write(f"delete_blocked={blocked.status_code}, occ_before={occ_before}, occ_after={occ_after}\n")
    else:
        f.write("delete_blocked=SKIPPED(no occupied room)\n")
    f.write(f"delete_new={delete_new.status_code}, new_after_delete={new_after_del}\n")
