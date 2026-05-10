import mysql.connector
import requests

conn = mysql.connector.connect(host="localhost", user="root", password="password", database="hms_db")
cur = conn.cursor()
cur.execute("SELECT doctor_id FROM DOCTOR d JOIN STAFF s ON s.staff_id=d.staff_id WHERE s.email='doctor@hospital.com' LIMIT 1")
d1 = cur.fetchone()[0]
cur.execute("SELECT doctor_id FROM DOCTOR WHERE doctor_id<>%s ORDER BY doctor_id LIMIT 1", (d1,))
row = cur.fetchone()
if row:
    d2 = row[0]
    cur.execute("SELECT patient_id FROM PATIENT WHERE status='Active' ORDER BY patient_id LIMIT 1")
    p = cur.fetchone()[0]
    cur.execute(
        "INSERT INTO APPOINTMENT (patient_id,doctor_id,appointment_date,appointment_time,reason,status) "
        "VALUES (%s,%s,CURDATE(),'12:37:00','OTHERDOCONLY','Scheduled')",
        (p, d2),
    )
    conn.commit()
cur.close()
conn.close()

s = requests.Session()
r = s.post("http://127.0.0.1:5000/", data={"email": "doctor_test", "password": "Doctor@123"}, allow_redirects=False)
lines = [f"login {r.status_code} {r.headers.get('Location')}"]

app = s.get("http://127.0.0.1:5000/appointments")
lines.append(f"appointments {app.status_code} OTHERDOCONLY_visible {'OTHERDOCONLY' in app.text}")

pat = s.get("http://127.0.0.1:5000/patients")
lines.append(f"patients {pat.status_code}")

dash = s.get("http://127.0.0.1:5000/doctor_dashboard")
lines.append(f"dashboard {dash.status_code}")

with open("fix1_verify_out.txt", "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
