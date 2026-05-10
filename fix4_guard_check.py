import mysql.connector
import requests

BASE = "http://127.0.0.1:5000"

conn = mysql.connector.connect(host="localhost", user="root", password="password", database="hms_db")
cur = conn.cursor()
cur.execute("SELECT room_id FROM ROOM ORDER BY room_id LIMIT 1")
rid = cur.fetchone()[0]
cur.execute("UPDATE ROOM SET status='Occupied' WHERE room_id=%s", (rid,))
conn.commit()
cur.close()
conn.close()

s = requests.Session()
s.post(f"{BASE}/", data={"email": "admin_test", "password": "Admin@123"})
r = s.post(f"{BASE}/rooms/delete/{rid}", allow_redirects=False)

conn = mysql.connector.connect(host="localhost", user="root", password="password", database="hms_db")
cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM ROOM WHERE room_id=%s", (rid,))
count_after = cur.fetchone()[0]
cur.execute("UPDATE ROOM SET status='Available' WHERE room_id=%s", (rid,))
conn.commit()
cur.close()
conn.close()

with open("fix4_guard_out.txt", "w", encoding="utf-8") as f:
    f.write(f"delete_attempt_status={r.status_code}\n")
    f.write(f"room_exists_after_attempt={count_after}\n")
