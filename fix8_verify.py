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

def qdict(sql, params=()):
    conn = mysql.connector.connect(host="localhost", user="root", password="password", database="hms_db")
    cur = conn.cursor(dictionary=True)
    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows

s = requests.Session()
login = s.post(f"{BASE}/", data={"email": "staff_test", "password": "Staff@123"}, allow_redirects=False)

billing_page = s.get(f"{BASE}/billing")
gen_page = s.get(f"{BASE}/billing/generate")

pid = q1("SELECT patient_id FROM PATIENT WHERE status='Active' ORDER BY patient_id DESC LIMIT 1")
count_before = q1("SELECT COUNT(*) FROM BILLING")
suffix = int(time.time()) % 100000
gen = s.post(f"{BASE}/billing/generate", data={"patient_id": pid, "admission_id": "", "total_amount": "1234.00"}, allow_redirects=False)
count_after = q1("SELECT COUNT(*) FROM BILLING")
bid = q1("SELECT bill_id FROM BILLING ORDER BY bill_id DESC LIMIT 1")

view = s.get(f"{BASE}/billing/view/{bid}")

# pay partial then full
pay1 = s.post(f"{BASE}/billing/pay/{bid}", data={"amount": "200.00", "method": "Cash"}, allow_redirects=False)
status1 = q1("SELECT payment_status FROM BILLING WHERE bill_id=%s", (bid,))
pay2 = s.post(f"{BASE}/billing/pay/{bid}", data={"amount": "2000.00", "method": "Cash"}, allow_redirects=False)
status2 = q1("SELECT payment_status FROM BILLING WHERE bill_id=%s", (bid,))

with open("fix8_verify_out.txt", "w", encoding="utf-8") as f:
    f.write(f"login={login.status_code}:{login.headers.get('Location')}\n")
    f.write(f"billing_page={billing_page.status_code}\n")
    f.write(f"generate_page={gen_page.status_code}\n")
    f.write(f"generate_post={gen.status_code}, count_before={count_before}, count_after={count_after}, bid={bid}\n")
    f.write(f"view_bill={view.status_code}\n")
    f.write(f"pay1={pay1.status_code}, status_after_pay1={status1}\n")
    f.write(f"pay2={pay2.status_code}, status_after_pay2={status2}\n")
