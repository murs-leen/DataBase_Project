import mysql.connector
import requests

BASE = "http://127.0.0.1:5000"

s = requests.Session()
login = s.post(f"{BASE}/", data={"email": "doctor_test", "password": "Doctor@123"}, allow_redirects=False)

conn = mysql.connector.connect(host="localhost", user="root", password="password", database="hms_db")
cur = conn.cursor()
cur.execute("SELECT doctor_id FROM DOCTOR d JOIN STAFF s ON s.staff_id=d.staff_id WHERE s.email='doctor@hospital.com' LIMIT 1")
my_doc = cur.fetchone()[0]
cur.execute("""
    SELECT DISTINCT p.patient_id
    FROM PATIENT p JOIN APPOINTMENT a ON a.patient_id=p.patient_id
    WHERE a.doctor_id=%s
    ORDER BY p.patient_id LIMIT 1
""", (my_doc,))
patient_id = cur.fetchone()[0]
cur.execute("SELECT medicine_id FROM MEDICINE ORDER BY medicine_id LIMIT 1")
med_id = cur.fetchone()[0]
cur.close()
conn.close()

r_new = s.post(
    f"{BASE}/doctor/prescriptions/new",
    data={"patient_id": patient_id, "diagnosis": "Flu", "notes": "Hydration and rest"},
    allow_redirects=False,
)
new_loc = r_new.headers.get("Location", "")
new_pid = int(new_loc.split("/")[-2]) if "/add_medicine" in new_loc else None

r_add = s.post(
    f"{BASE}/doctor/prescriptions/{new_pid}/add_medicine",
    data={"medicine_id": med_id, "dosage": "1 tablet", "frequency": "Twice daily", "duration": "5", "quantity": "10"},
    allow_redirects=False,
)
v = s.get(f"{BASE}/doctor/prescriptions/{new_pid}/view")
lst = s.get(f"{BASE}/doctor/prescriptions")

# Create another-doctor prescription for ownership test
conn = mysql.connector.connect(host="localhost", user="root", password="password", database="hms_db")
cur = conn.cursor()
cur.execute("SELECT doctor_id FROM DOCTOR WHERE doctor_id<>%s ORDER BY doctor_id LIMIT 1", (my_doc,))
other_doc = cur.fetchone()[0]
cur.execute("INSERT INTO PRESCRIPTION (patient_id, doctor_id, prescription_date, notes) VALUES (%s,%s,CURDATE(),%s)", (patient_id, other_doc, "Other doctor rx"))
other_pid = cur.lastrowid
conn.commit()
cur.close()
conn.close()

blocked = s.get(f"{BASE}/doctor/prescriptions/{other_pid}/view")

with open("fix2_verify_out.txt", "w", encoding="utf-8") as f:
    f.write(f"login={login.status_code}:{login.headers.get('Location')}\n")
    f.write(f"new_rx_post={r_new.status_code}:{new_loc}\n")
    f.write(f"add_medicine_post={r_add.status_code}:{r_add.headers.get('Location')}\n")
    f.write(f"view_status={v.status_code}, contains_medicine={'Paracetamol' in v.text or 'Amoxicillin' in v.text or 'Ibuprofen' in v.text}\n")
    f.write(f"list_status={lst.status_code}, contains_new_id={str(new_pid) in lst.text}\n")
    f.write(f"ownership_block_status={blocked.status_code}, denied_text={'Access denied' in blocked.text}\n")
