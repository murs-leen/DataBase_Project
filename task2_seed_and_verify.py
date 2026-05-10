import hashlib
import mysql.connector


def run():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="password",
        database="hms_db",
    )
    cur = conn.cursor(dictionary=True)

    # Step 4: Departments
    dept_rows = [
        ("Cardiology", "Block A", "1001", "Heart and cardiovascular care"),
        ("General Medicine", "Block B", "1002", "Primary and internal medicine"),
    ]
    for row in dept_rows:
        cur.execute("SELECT dept_id FROM DEPARTMENT WHERE dept_name=%s", (row[0],))
        found = cur.fetchone()
        if not found:
            cur.execute(
                "INSERT INTO DEPARTMENT (dept_name, location, phone_ext, description) VALUES (%s,%s,%s,%s)",
                row,
            )
    conn.commit()
    cur.execute("SELECT * FROM DEPARTMENT ORDER BY dept_id")
    print("DEPARTMENT:", cur.fetchall())

    # Step 5: Rooms (room_type must match enum: General/Private/ICU/Emergency)
    cur.execute("SELECT dept_id FROM DEPARTMENT WHERE dept_name='General Medicine'")
    gm = cur.fetchone()
    gm_id = gm["dept_id"]
    room_rows = [
        ("101", "General", gm_id, 8, 2500.00, "Available"),
        ("201", "Private", gm_id, 1, 7000.00, "Available"),
        ("301", "ICU", gm_id, 1, 15000.00, "Available"),
    ]
    for row in room_rows:
        cur.execute("SELECT room_id FROM ROOM WHERE room_number=%s", (row[0],))
        found = cur.fetchone()
        if not found:
            cur.execute(
                "INSERT INTO ROOM (room_number, room_type, dept_id, capacity, daily_charge, status) VALUES (%s,%s,%s,%s,%s,%s)",
                row,
            )
    conn.commit()
    cur.execute("SELECT * FROM ROOM ORDER BY room_id")
    print("ROOM:", cur.fetchall())

    # Step 6: Medicines
    medicine_rows = [
        ("Paracetamol", "Acetaminophen", "Analgesic", 15.00, 500, "PharmaCare"),
        ("Amoxicillin", "Amoxicillin Trihydrate", "Antibiotic", 45.00, 250, "MediLife"),
        ("Ibuprofen", "Ibuprofen", "NSAID", 25.00, 300, "HealthPlus"),
    ]
    for row in medicine_rows:
        cur.execute("SELECT medicine_id FROM MEDICINE WHERE medicine_name=%s", (row[0],))
        found = cur.fetchone()
        if not found:
            cur.execute(
                "INSERT INTO MEDICINE (medicine_name, generic_name, category, unit_price, stock_quantity, manufacturer) VALUES (%s,%s,%s,%s,%s,%s)",
                row,
            )
    conn.commit()
    cur.execute("SELECT * FROM MEDICINE ORDER BY medicine_id")
    print("MEDICINE:", cur.fetchall())

    # Password hashes
    admin_hash = hashlib.sha256("Admin@123".encode()).hexdigest()
    doctor_hash = hashlib.sha256("Doctor@123".encode()).hexdigest()
    staff_hash = hashlib.sha256("Staff@123".encode()).hexdigest()

    # Step 7: Admin user
    cur.execute("SELECT user_id FROM USERS WHERE username='admin_test' OR email='admin@hospital.com'")
    admin = cur.fetchone()
    if not admin:
        cur.execute(
            "INSERT INTO USERS (username, email, password_hash, role, staff_id, is_active) VALUES (%s,%s,%s,%s,%s,%s)",
            ("admin_test", "admin@hospital.com", admin_hash, "Admin", None, 1),
        )
    conn.commit()
    cur.execute("SELECT * FROM USERS WHERE role='Admin' ORDER BY user_id")
    print("USERS_ADMIN:", cur.fetchall())

    # Step 8: Doctor user + staff + doctor
    cur.execute("SELECT user_id FROM USERS WHERE username='doctor_test' OR email='doctor@hospital.com'")
    doctor_user = cur.fetchone()
    if not doctor_user:
        cur.execute(
            "INSERT INTO USERS (username, email, password_hash, role, staff_id, is_active) VALUES (%s,%s,%s,%s,%s,%s)",
            ("doctor_test", "doctor@hospital.com", doctor_hash, "Doctor", None, 1),
        )
    conn.commit()
    cur.execute("SELECT user_id FROM USERS WHERE username='doctor_test'")
    doctor_user = cur.fetchone()
    doctor_user_id = doctor_user["user_id"]

    cur.execute("SELECT staff_id FROM STAFF WHERE email='doctor@hospital.com'")
    doctor_staff = cur.fetchone()
    if not doctor_staff:
        cur.execute(
            "INSERT INTO STAFF (first_name,last_name,staff_type,phone,email,hire_date,salary,shift,status) VALUES (%s,%s,%s,%s,%s,CURDATE(),%s,%s,%s)",
            ("Ahsan", "Qureshi", "Doctor", "+923001110001", "doctor@hospital.com", 180000.00, "Morning", "Active"),
        )
    conn.commit()
    cur.execute("SELECT staff_id FROM STAFF WHERE email='doctor@hospital.com'")
    doctor_staff = cur.fetchone()
    doctor_staff_id = doctor_staff["staff_id"]

    cur.execute("SELECT dept_id FROM DEPARTMENT WHERE dept_name='Cardiology'")
    cardio_id = cur.fetchone()["dept_id"]

    cur.execute("SELECT doctor_id FROM DOCTOR WHERE staff_id=%s", (doctor_staff_id,))
    doctor_row = cur.fetchone()
    if not doctor_row:
        cur.execute(
            "INSERT INTO DOCTOR (staff_id, dept_id, specialization, license_number, consultation_fee, available_days) VALUES (%s,%s,%s,%s,%s,%s)",
            (doctor_staff_id, cardio_id, "Cardiologist", "PMC-DOC-10001", 3500.00, "Mon,Tue,Wed,Thu,Fri"),
        )
    conn.commit()

    cur.execute("UPDATE USERS SET staff_id=%s WHERE user_id=%s", (doctor_staff_id, doctor_user_id))
    conn.commit()

    cur.execute(
        "SELECT u.*, d.* FROM USERS u JOIN DOCTOR d ON u.staff_id = d.staff_id WHERE u.role='Doctor' ORDER BY u.user_id"
    )
    print("USERS_DOCTOR_JOIN:", cur.fetchall())

    # Step 9: Staff user + staff row
    cur.execute("SELECT user_id FROM USERS WHERE username='staff_test' OR email='staff@hospital.com'")
    staff_user = cur.fetchone()
    if not staff_user:
        cur.execute(
            "INSERT INTO USERS (username, email, password_hash, role, staff_id, is_active) VALUES (%s,%s,%s,%s,%s,%s)",
            ("staff_test", "staff@hospital.com", staff_hash, "Staff", None, 1),
        )
    conn.commit()
    cur.execute("SELECT user_id FROM USERS WHERE username='staff_test'")
    staff_user_id = cur.fetchone()["user_id"]

    cur.execute("SELECT staff_id FROM STAFF WHERE email='staff@hospital.com'")
    staff_staff = cur.fetchone()
    if not staff_staff:
        cur.execute(
            "INSERT INTO STAFF (first_name,last_name,staff_type,phone,email,hire_date,salary,shift,status) VALUES (%s,%s,%s,%s,%s,CURDATE(),%s,%s,%s)",
            ("Sana", "Khan", "Admin", "+923001110002", "staff@hospital.com", 65000.00, "Evening", "Active"),
        )
    conn.commit()
    cur.execute("SELECT staff_id FROM STAFF WHERE email='staff@hospital.com'")
    staff_staff_id = cur.fetchone()["staff_id"]

    cur.execute("UPDATE USERS SET staff_id=%s WHERE user_id=%s", (staff_staff_id, staff_user_id))
    conn.commit()

    cur.execute(
        "SELECT u.*, s.* FROM USERS u JOIN STAFF s ON u.staff_id = s.staff_id WHERE u.role='Staff' ORDER BY u.user_id"
    )
    print("USERS_STAFF_JOIN:", cur.fetchall())

    # Step 10 final verification
    for table in ["USERS", "DEPARTMENT", "DOCTOR", "STAFF", "ROOM", "MEDICINE"]:
        cur.execute(f"SELECT * FROM {table}")
        print(f"{table}:", cur.fetchall())

    cur.close()
    conn.close()


if __name__ == "__main__":
    run()
