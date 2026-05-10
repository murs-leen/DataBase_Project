import mysql.connector

conn = mysql.connector.connect(host="localhost", user="root", password="password", database="hms_db")
cur = conn.cursor()

cur.execute("SELECT dept_id FROM DEPARTMENT WHERE dept_name=%s", ("Neurology Test",))
row = cur.fetchone()
if row:
    dept_id = row[0]
    cur.execute("SELECT COUNT(*) FROM DOCTOR WHERE dept_id=%s", (dept_id,))
    cnt = cur.fetchone()[0]
    if cnt == 0:
        cur.execute("DELETE FROM DEPARTMENT WHERE dept_id=%s", (dept_id,))
        conn.commit()
        print("Deleted Neurology Test")
    else:
        print("Kept Neurology Test (doctors assigned)")
else:
    print("Neurology Test not found")

cur.close()
conn.close()

