"""
ClinicFlow - Clinic Management System Backend
==========================================
Install requirements: pip install flask mysql-connector-python
Run: python app.py
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file, flash
import mysql.connector
import hashlib
import io
import csv
import os
from datetime import date, datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = "hms_secret_key_2026"

# Make enumerate available in all Jinja templates
app.jinja_env.globals['enumerate'] = enumerate

# Inject today's date fresh on every request (so it never goes stale)
@app.context_processor
def inject_globals():
    return {'today': str(date.today())}

# ─────────────────────────────────────────────
# DATABASE CONNECTION
# ─────────────────────────────────────────────
DB_CONFIG = {
    "host":     "localhost",
    "user":     "root",          # Change to your MySQL user
    "password": "password",      # MySQL password
    "database": "hms_db",
    "charset":  "utf8mb4"
}

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

def query_db(sql, params=(), fetchone=False):
    conn = get_db()
    cur  = conn.cursor(dictionary=True)
    cur.execute(sql, params)
    result = cur.fetchone() if fetchone else cur.fetchall()
    conn.close()
    return result

def execute_db(sql, params=()):
    conn = get_db()
    cur  = conn.cursor()
    cur.execute(sql, params)
    last_id = cur.lastrowid
    conn.commit()
    conn.close()
    return last_id

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()


def get_logged_in_doctor_id():
    """Resolve current doctor's doctor_id via session staff_id."""
    staff_id = session.get("staff_id")
    if not staff_id:
        return None
    row = query_db("SELECT doctor_id FROM DOCTOR WHERE staff_id=%s", (staff_id,), fetchone=True)
    return row["doctor_id"] if row else None

# ─────────────────────────────────────────────
# AUTH DECORATORS
# ─────────────────────────────────────────────
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        if session.get("role") != "Admin":
            return render_template("error.html", msg="Admin access required.")
        return f(*args, **kwargs)
    return decorated

def doctor_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        if session.get("role") not in ["Admin", "Doctor"]:
            return render_template("error.html", msg="Doctor access required.")
        return f(*args, **kwargs)
    return decorated

def staff_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        if session.get("role") not in ["Admin", "Staff"]:
            return render_template("error.html", msg="Staff access required.")
        return f(*args, **kwargs)
    return decorated


def doctor_or_staff_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        if session.get("role") not in ["Doctor", "Staff", "Admin"]:
            flash("Access denied.", "danger")
            return redirect(url_for("dashboard"))
        return f(*args, **kwargs)
    return decorated

# ─────────────────────────────────────────────
# AUTH ROUTES
# ─────────────────────────────────────────────
@app.route("/", methods=["GET","POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("email","").strip()  # Form uses email now
        password = request.form.get("password","")
        # For simplicity, fallback to username if email fails, as DB uses username
        user = query_db(
            "SELECT * FROM USERS WHERE (username=%s OR email=%s) AND password_hash=%s AND is_active=1",
            (username, username, hash_pw(password)), fetchone=True
        )
        if user:
            session["user_id"]  = user["user_id"]
            session["username"] = user["username"]
            session["email"]    = user["email"]
            session["role"]     = user["role"]
            session["staff_id"] = user.get("staff_id")
            return redirect(url_for("dashboard"))
        error = "Invalid email or password."
    return render_template("login.html", error=error)

@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = None
    if request.method == "POST":
        role = request.form.get("role")
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        
        if not role or role not in ["Doctor", "Staff"]:
            error = "Please select a valid role."
        elif password != confirm:
            error = "Passwords do not match."
        else:
            try:
                execute_db(
                    "INSERT INTO USERS (username, email, password_hash, role) VALUES (%s, %s, %s, %s)",
                    (email.split('@')[0] + str(hash(email))[-4:], email, hash_pw(password), role)
                )
                user = query_db("SELECT * FROM USERS WHERE email=%s", (email,), fetchone=True)
                session["user_id"] = user["user_id"]
                session["username"] = user["username"]
                session["email"] = user["email"]
                session["role"] = user["role"]
                return redirect(url_for("dashboard"))
            except Exception as e:
                error = "Account already exists or database error."
                
    return render_template("signup.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# ─────────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────────
@app.route("/dashboard")
@login_required
def dashboard():
    role = session.get("role")
    if role in ["Admin", "Doctor"]:
        return redirect(url_for("doctor_dashboard"))
    elif role == "Staff":
        return redirect(url_for("staff_dashboard"))
    else:
        return render_template("error.html", msg="Invalid role.")

@app.route("/doctor_dashboard")
@doctor_required
def doctor_dashboard():
    if session.get("role") == "Doctor":
        doctor_id = get_logged_in_doctor_id()
        if not doctor_id:
            return render_template("error.html", msg="Doctor profile not linked to staff record.")

        # Scoped KPIs for the logged-in doctor only.
        today_rev = query_db(
            "SELECT COUNT(*) AS r FROM APPOINTMENT WHERE doctor_id=%s AND appointment_date = CURDATE()",
            (doctor_id,), fetchone=True)["r"]
        yesterday_rev = query_db(
            "SELECT COUNT(*) AS r FROM APPOINTMENT WHERE doctor_id=%s AND appointment_date = DATE_SUB(CURDATE(), INTERVAL 1 DAY)",
            (doctor_id,), fetchone=True)["r"]
        monthly_rev = query_db(
            "SELECT COUNT(DISTINCT patient_id) AS r FROM APPOINTMENT WHERE doctor_id=%s",
            (doctor_id,), fetchone=True)["r"]
        total_rev = query_db(
            "SELECT COUNT(*) AS r FROM PRESCRIPTION WHERE doctor_id=%s",
            (doctor_id,), fetchone=True)["r"]
        seven_day_rev = query_db("""
            SELECT DATE_FORMAT(appointment_date, '%b %d') as date_label,
                   COUNT(*) as daily_revenue
            FROM APPOINTMENT
            WHERE doctor_id=%s
              AND appointment_date >= DATE_SUB(CURDATE(), INTERVAL 6 DAY)
            GROUP BY appointment_date
            ORDER BY appointment_date ASC
        """, (doctor_id,))
    else:
        # Admin view remains global.
        today_rev = query_db(
            "SELECT COALESCE(SUM(paid_amount), 0) AS r FROM BILLING WHERE payment_date = CURDATE() AND payment_status IN ('Paid', 'Partial')",
            fetchone=True)["r"]
        yesterday_rev = query_db(
            "SELECT COALESCE(SUM(paid_amount), 0) AS r FROM BILLING WHERE payment_date = DATE_SUB(CURDATE(), INTERVAL 1 DAY) AND payment_status IN ('Paid', 'Partial')",
            fetchone=True)["r"]
        monthly_rev = query_db(
            "SELECT COALESCE(SUM(paid_amount), 0) AS r FROM BILLING WHERE MONTH(payment_date) = MONTH(CURDATE()) AND YEAR(payment_date) = YEAR(CURDATE()) AND payment_status IN ('Paid', 'Partial')",
            fetchone=True)["r"]
        total_rev = query_db(
            "SELECT COALESCE(SUM(paid_amount), 0) AS r FROM BILLING WHERE payment_status IN ('Paid', 'Partial')",
            fetchone=True)["r"]
        seven_day_rev = query_db("""
            SELECT DATE_FORMAT(payment_date, '%b %d') as date_label, COALESCE(SUM(paid_amount), 0) as daily_revenue
            FROM BILLING 
            WHERE payment_date >= DATE_SUB(CURDATE(), INTERVAL 6 DAY)
              AND payment_status IN ('Paid', 'Partial')
            GROUP BY payment_date
            ORDER BY payment_date ASC
        """)

    return render_template("doctor_dashboard.html",
        today_rev=today_rev,
        yesterday_rev=yesterday_rev,
        monthly_rev=monthly_rev,
        total_rev=total_rev,
        seven_day_rev=seven_day_rev
    )


@app.route("/doctor/prescriptions")
@doctor_required
def doctor_prescriptions():
    doctor_id = get_logged_in_doctor_id()
    if session.get("role") == "Doctor" and not doctor_id:
        return render_template("error.html", msg="Doctor profile not linked to staff record.")

    if session.get("role") == "Admin":
        rows = query_db("""
            SELECT pr.prescription_id, pr.patient_id, pr.doctor_id, pr.appointment_id,
                   pr.prescription_date, pr.notes,
                   CONCAT(p.first_name,' ',p.last_name) AS patient_name
            FROM PRESCRIPTION pr
            JOIN PATIENT p ON p.patient_id = pr.patient_id
            ORDER BY pr.prescription_date DESC, pr.prescription_id DESC
        """)
    else:
        rows = query_db("""
            SELECT pr.prescription_id, pr.patient_id, pr.doctor_id, pr.appointment_id,
                   pr.prescription_date, pr.notes,
                   CONCAT(p.first_name,' ',p.last_name) AS patient_name
            FROM PRESCRIPTION pr
            JOIN PATIENT p ON p.patient_id = pr.patient_id
            WHERE pr.doctor_id = %s
            ORDER BY pr.prescription_date DESC, pr.prescription_id DESC
        """, (doctor_id,))

    return render_template("doctor_prescriptions.html", prescriptions=rows)


@app.route("/doctor/prescriptions/new", methods=["GET", "POST"])
@doctor_required
def doctor_prescription_new():
    doctor_id = get_logged_in_doctor_id()
    if session.get("role") == "Doctor" and not doctor_id:
        return render_template("error.html", msg="Doctor profile not linked to staff record.")

    if session.get("role") == "Admin":
        patients = query_db("""
            SELECT DISTINCT p.patient_id, CONCAT(p.first_name,' ',p.last_name) AS name
            FROM PATIENT p
            WHERE p.status='Active'
            ORDER BY p.first_name, p.last_name
        """)
    else:
        patients = query_db("""
            SELECT DISTINCT p.patient_id, CONCAT(p.first_name,' ',p.last_name) AS name
            FROM PATIENT p
            JOIN APPOINTMENT a ON a.patient_id = p.patient_id
            WHERE p.status='Active'
              AND a.doctor_id = %s
            ORDER BY name
        """, (doctor_id,))

    error = None
    if request.method == "POST":
        patient_id = request.form.get("patient_id")
        diagnosis = request.form.get("diagnosis", "").strip()
        notes = request.form.get("notes", "").strip()

        if not patient_id:
            error = "Please select a patient."
        elif session.get("role") == "Doctor":
            allowed = query_db("""
                SELECT COUNT(*) AS c
                FROM APPOINTMENT
                WHERE doctor_id=%s AND patient_id=%s
            """, (doctor_id, patient_id), fetchone=True)["c"]
            if allowed == 0:
                error = "Selected patient is not assigned to this doctor."

        if not error:
            combined_notes = f"Diagnosis: {diagnosis}\nNotes: {notes}".strip()
            new_id = execute_db("""
                INSERT INTO PRESCRIPTION (patient_id, doctor_id, prescription_date, notes)
                VALUES (%s, %s, CURDATE(), %s)
            """, (patient_id, doctor_id if session.get("role") == "Doctor" else doctor_id or 1, combined_notes))
            return redirect(url_for("doctor_prescription_add_medicine", pid=new_id))

    return render_template("doctor_prescription_new.html", patients=patients, error=error)


@app.route("/doctor/prescriptions/<int:pid>/add_medicine", methods=["GET", "POST"])
@doctor_required
def doctor_prescription_add_medicine(pid):
    doctor_id = get_logged_in_doctor_id()
    rx = query_db("SELECT * FROM PRESCRIPTION WHERE prescription_id=%s", (pid,), fetchone=True)
    if not rx:
        return render_template("error.html", msg="Prescription not found.")

    if session.get("role") == "Doctor" and rx["doctor_id"] != doctor_id:
        return render_template("error.html", msg="Access denied for this prescription.")

    meds = query_db("SELECT medicine_id, medicine_name, stock_quantity FROM MEDICINE ORDER BY medicine_name")
    error = None
    if request.method == "POST":
        medicine_id = request.form.get("medicine_id")
        dosage = request.form.get("dosage", "").strip()
        frequency = request.form.get("frequency", "").strip()
        duration_days = request.form.get("duration", "").strip()
        quantity = request.form.get("quantity", "").strip()

        if not medicine_id or not dosage or not frequency or not duration_days or not quantity:
            error = "All medicine fields are required."
        else:
            dosage_with_frequency = f"{dosage} ({frequency})"
            execute_db("""
                INSERT INTO PRESCRIPTION_DETAILS (prescription_id, medicine_id, dosage, duration_days, quantity)
                VALUES (%s, %s, %s, %s, %s)
            """, (pid, medicine_id, dosage_with_frequency, duration_days, quantity))
            return redirect(url_for("doctor_prescription_view", pid=pid))

    return render_template("doctor_prescription_add_medicine.html", prescription=rx, medicines=meds, error=error)


@app.route("/doctor/prescriptions/<int:pid>/view")
@doctor_required
def doctor_prescription_view(pid):
    doctor_id = get_logged_in_doctor_id()
    rx = query_db("""
        SELECT pr.*, CONCAT(p.first_name,' ',p.last_name) AS patient_name
        FROM PRESCRIPTION pr
        JOIN PATIENT p ON p.patient_id = pr.patient_id
        WHERE pr.prescription_id=%s
    """, (pid,), fetchone=True)
    if not rx:
        return render_template("error.html", msg="Prescription not found.")

    if session.get("role") == "Doctor" and rx["doctor_id"] != doctor_id:
        return render_template("error.html", msg="Access denied for this prescription.")

    details = query_db("""
        SELECT pd.detail_id, pd.prescription_id, pd.medicine_id, pd.dosage,
               pd.duration_days, pd.quantity, m.medicine_name, m.unit_price
        FROM PRESCRIPTION_DETAILS pd
        JOIN MEDICINE m ON m.medicine_id = pd.medicine_id
        WHERE pd.prescription_id = %s
        ORDER BY pd.detail_id
    """, (pid,))
    return render_template("doctor_prescription_view.html", rx=rx, details=details)

@app.route("/staff_dashboard")
@staff_required
def staff_dashboard():
    patients_list = query_db("SELECT patient_id, CONCAT(first_name, ' ', last_name) AS name FROM PATIENT WHERE status='Active' ORDER BY first_name")
    medicines_list = query_db("SELECT medicine_id, medicine_name, stock_quantity FROM MEDICINE ORDER BY medicine_name")
    return render_template("staff_dashboard.html", patients=patients_list, medicines=medicines_list)

@app.route("/staff/dispense", methods=["POST"])
@staff_required
def staff_dispense():
    patient_id = request.form.get("patient_id")
    medicine_id = request.form.get("medicine_id")
    quantity = int(request.form.get("quantity", 0))
    
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    try:
        conn.start_transaction()
        cur.execute("SELECT stock_quantity, unit_price FROM MEDICINE WHERE medicine_id = %s FOR UPDATE", (medicine_id,))
        med = cur.fetchone()
        
        if not med:
            conn.rollback()
            return jsonify({"status": "error", "message": "Medicine not found."})
            
        if med["stock_quantity"] < quantity:
            conn.rollback()
            return jsonify({"status": "error", "message": f"Insufficient Stock. Only {med['stock_quantity']} units available."})
            
        cur.execute("UPDATE MEDICINE SET stock_quantity = stock_quantity - %s WHERE medicine_id = %s", (quantity, medicine_id))
        
        # We need to find a doctor to assign to the prescription. Let's get any active doctor for simplicity, or dummy it if allowed.
        # Actually, let's see if we can get doctor_id from session, or default to 1
        cur.execute("SELECT doctor_id FROM DOCTOR LIMIT 1")
        doc = cur.fetchone()
        doc_id = doc['doctor_id'] if doc else 1
        
        cur.execute("INSERT INTO PRESCRIPTION (patient_id, doctor_id, prescription_date, notes) VALUES (%s, %s, CURDATE(), 'Staff Dispensed')", (patient_id, doc_id))
        rx_id = cur.lastrowid
        cur.execute("INSERT INTO PRESCRIPTION_DETAILS (prescription_id, medicine_id, dosage, duration_days, quantity) VALUES (%s, %s, 'Dispensed', 1, %s)", (rx_id, medicine_id, quantity))
        
        # Add to patient's billing
        total_cost = med["unit_price"] * quantity
        cur.execute("SELECT bill_id FROM BILLING WHERE patient_id = %s AND payment_status != 'Paid' LIMIT 1", (patient_id,))
        bill = cur.fetchone()
        if bill:
            cur.execute("UPDATE BILLING SET total_amount = total_amount + %s, payment_status = 'Pending' WHERE bill_id = %s", (total_cost, bill['bill_id']))
        else:
            cur.execute("INSERT INTO BILLING (patient_id, total_amount, paid_amount, bill_date, payment_status) VALUES (%s, %s, 0, CURDATE(), 'Pending')", (patient_id, total_cost))
            
        conn.commit()
        return jsonify({"status": "success", "message": "Medicine dispensed successfully."})
    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)})
    finally:
        conn.close()

# ─────────────────────────────────────────────
# STAFF PATIENT REGISTRATION
# ─────────────────────────────────────────────
@app.route("/staff/register_patient", methods=["POST"])
@staff_required
def staff_register_patient():
    f = request.form
    try:
        execute_db("""
            INSERT INTO PATIENT
                (first_name,last_name,date_of_birth,gender,phone,email,address,blood_group)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
        """, (f["first_name"], f["last_name"], f["dob"], f["gender"],
              f["phone"], f.get("email") or None, f["address"], f["blood_group"]))
        return jsonify({"status": "success", "message": "Patient registered successfully."})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# ─────────────────────────────────────────────
# PATIENT CRUD
# ─────────────────────────────────────────────
@app.route("/patients")
@login_required
def patients():
    search = request.args.get("q","").strip()
    if session.get("role") == "Doctor":
        doctor_id = get_logged_in_doctor_id()
        if not doctor_id:
            rows = []
        elif search:
            rows = query_db("""
                SELECT DISTINCT p.*
                FROM PATIENT p
                JOIN APPOINTMENT a ON p.patient_id = a.patient_id
                WHERE p.status='Active'
                  AND a.doctor_id=%s
                  AND (
                    p.first_name LIKE %s OR p.last_name LIKE %s
                    OR p.phone LIKE %s OR CAST(p.patient_id AS CHAR) LIKE %s
                  )
                ORDER BY p.patient_id DESC
            """, (doctor_id, f"%{search}%", f"%{search}%", f"%{search}%", f"%{search}%"))
        else:
            rows = query_db("""
                SELECT DISTINCT p.*
                FROM PATIENT p
                JOIN APPOINTMENT a ON p.patient_id = a.patient_id
                WHERE p.status='Active'
                  AND a.doctor_id=%s
                ORDER BY p.patient_id DESC
            """, (doctor_id,))
    elif search:
        rows = query_db("""
            SELECT * FROM PATIENT
            WHERE status='Active' AND (
                first_name LIKE %s OR last_name LIKE %s
                OR phone LIKE %s OR CAST(patient_id AS CHAR) LIKE %s
            ) ORDER BY patient_id DESC
        """, (f"%{search}%",)*4)
    else:
        rows = query_db("SELECT * FROM PATIENT WHERE status='Active' ORDER BY patient_id DESC")
    return render_template("patients.html", patients=rows, search=search)

@app.route("/patients/add", methods=["GET","POST"])
@login_required
def add_patient():
    error = None
    if request.method == "POST":
        f = request.form
        try:
            pid = execute_db("""
                INSERT INTO PATIENT
                    (first_name,last_name,date_of_birth,gender,phone,email,address,blood_group)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, (f["first_name"], f["last_name"], f["dob"], f["gender"],
                  f["phone"], f.get("email") or None, f["address"], f["blood_group"]))
            return redirect(url_for("patients"))
        except Exception as e:
            error = f"Error: {e}"
    return render_template("patient_form.html", patient=None, error=error, action="Add")

@app.route("/patients/edit/<int:pid>", methods=["GET","POST"])
@login_required
def edit_patient(pid):
    error = None
    patient = query_db("SELECT * FROM PATIENT WHERE patient_id=%s", (pid,), fetchone=True)
    if request.method == "POST":
        f = request.form
        try:
            execute_db("""
                UPDATE PATIENT SET first_name=%s,last_name=%s,date_of_birth=%s,
                    gender=%s,phone=%s,email=%s,address=%s,blood_group=%s
                WHERE patient_id=%s
            """, (f["first_name"], f["last_name"], f["dob"], f["gender"],
                  f["phone"], f.get("email") or None, f["address"], f["blood_group"], pid))
            return redirect(url_for("patients"))
        except Exception as e:
            error = f"Error: {e}"
    return render_template("patient_form.html", patient=patient, error=error, action="Edit")

@app.route("/patients/delete/<int:pid>", methods=["POST"])
@admin_required
def delete_patient(pid):
    execute_db("UPDATE PATIENT SET status='Inactive' WHERE patient_id=%s", (pid,))
    return redirect(url_for("patients"))

# ─────────────────────────────────────────────
# DOCTOR CRUD
# ─────────────────────────────────────────────
@app.route("/doctors")
@login_required
def doctors():
    rows = query_db("""
        SELECT d.doctor_id, d.staff_id, CONCAT(s.first_name,' ',s.last_name) AS name,
               dep.dept_name, d.specialization, d.license_number,
               d.consultation_fee, d.available_days, s.status
        FROM DOCTOR d
        JOIN STAFF s ON s.staff_id=d.staff_id
        JOIN DEPARTMENT dep ON dep.dept_id=d.dept_id
        WHERE s.status='Active'
        ORDER BY d.doctor_id
    """)
    return render_template("doctors.html", doctors=rows)

@app.route("/doctors/add", methods=["GET","POST"])
@admin_required
def add_doctor():
    depts = query_db("SELECT * FROM DEPARTMENT ORDER BY dept_name")
    error = None
    if request.method == "POST":
        f = request.form
        try:
            # Insert staff first
            sid = execute_db("""
                INSERT INTO STAFF (first_name,last_name,staff_type,phone,email,hire_date,salary,shift)
                VALUES (%s,%s,'Doctor',%s,%s,%s,%s,%s)
            """, (f["first_name"], f["last_name"], f["phone"],
                  f.get("email") or None, f["hire_date"], f["salary"], f["shift"]))
            # Insert doctor
            execute_db("""
                INSERT INTO DOCTOR (staff_id,dept_id,specialization,license_number,consultation_fee,available_days)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, (sid, f["dept_id"], f["specialization"],
                  f["license_number"], f["consultation_fee"], f["available_days"]))
            return redirect(url_for("doctors"))
        except Exception as e:
            error = f"Error: {e}"
    return render_template("doctor_form.html", doctor=None, depts=depts, error=error, action="Add")


@app.route("/doctors/edit/<int:staff_id>", methods=["GET", "POST"])
@admin_required
def edit_doctor(staff_id):
    depts = query_db("SELECT * FROM DEPARTMENT ORDER BY dept_name")
    doctor = query_db("""
        SELECT s.staff_id, s.first_name, s.last_name, s.phone, s.email, s.hire_date, s.salary, s.shift, s.status,
               d.doctor_id, d.dept_id, d.specialization, d.license_number, d.consultation_fee, d.available_days
        FROM STAFF s
        JOIN DOCTOR d ON s.staff_id = d.staff_id
        WHERE s.staff_id=%s
    """, (staff_id,), fetchone=True)
    if not doctor:
        flash("Doctor not found.", "danger")
        return redirect(url_for("doctors"))

    error = None
    if request.method == "POST":
        f = request.form
        try:
            execute_db("""
                UPDATE STAFF
                SET first_name=%s, last_name=%s, phone=%s, salary=%s, shift=%s, status=%s
                WHERE staff_id=%s
            """, (
                f["first_name"], f["last_name"], f["phone"], f["salary"], f["shift"], f["status"], staff_id
            ))
            execute_db("""
                UPDATE DOCTOR
                SET dept_id=%s, specialization=%s, license_number=%s, consultation_fee=%s, available_days=%s
                WHERE staff_id=%s
            """, (
                f["dept_id"], f["specialization"], f["license_number"], f["consultation_fee"], f["available_days"], staff_id
            ))
            if f.get("email"):
                execute_db("UPDATE STAFF SET email=%s WHERE staff_id=%s", (f["email"], staff_id))
            return redirect(url_for("doctors"))
        except Exception as e:
            error = f"Error: {e}"
            doctor = {**doctor, **f}

    return render_template("doctor_form.html", doctor=doctor, depts=depts, error=error, action="Edit")


@app.route("/doctors/delete/<int:staff_id>", methods=["POST"])
@admin_required
def delete_doctor(staff_id):
    row = query_db("SELECT doctor_id FROM DOCTOR WHERE staff_id=%s", (staff_id,), fetchone=True)
    if not row:
        flash("Doctor not found.", "danger")
        return redirect(url_for("doctors"))
    doctor_id = row["doctor_id"]

    active_count = query_db("""
        SELECT COUNT(*) AS c
        FROM APPOINTMENT
        WHERE doctor_id=%s
          AND status NOT IN ('Completed','Cancelled')
    """, (doctor_id,), fetchone=True)["c"]
    if active_count > 0:
        flash("Cannot delete doctor: active appointments exist.", "danger")
        return redirect(url_for("doctors"))

    try:
        execute_db("DELETE FROM DOCTOR WHERE staff_id=%s", (staff_id,))
        execute_db("DELETE FROM USERS WHERE staff_id=%s", (staff_id,))
        execute_db("DELETE FROM STAFF WHERE staff_id=%s", (staff_id,))
    except Exception as e:
        flash(f"Doctor delete blocked by dependent records: {e}", "danger")
        return redirect(url_for("doctors"))

    return redirect(url_for("doctors"))


# ─────────────────────────────────────────────
# DEPARTMENT CRUD (ADMIN)
# ─────────────────────────────────────────────
@app.route("/departments")
@admin_required
def departments():
    rows = query_db("SELECT * FROM DEPARTMENT ORDER BY dept_name")
    return render_template("departments.html", departments=rows, form_mode="list", form_data=None, error=None)


@app.route("/departments/add", methods=["GET", "POST"])
@admin_required
def add_department():
    if request.method == "POST":
        f = request.form
        try:
            execute_db("""
                INSERT INTO DEPARTMENT (dept_name, location, phone_ext, description)
                VALUES (%s, %s, %s, %s)
            """, (
                f.get("dept_name", "").strip(),
                f.get("location", "").strip(),
                f.get("phone_ext", "").strip() or None,
                f.get("description", "").strip() or None
            ))
            return redirect(url_for("departments"))
        except Exception as e:
            rows = query_db("SELECT * FROM DEPARTMENT ORDER BY dept_name")
            return render_template("departments.html", departments=rows, form_mode="add", form_data=f, error=f"Error: {e}")

    rows = query_db("SELECT * FROM DEPARTMENT ORDER BY dept_name")
    return render_template("departments.html", departments=rows, form_mode="add", form_data=None, error=None)


@app.route("/departments/edit/<int:dept_id>", methods=["GET", "POST"])
@admin_required
def edit_department(dept_id):
    dept = query_db("SELECT * FROM DEPARTMENT WHERE dept_id=%s", (dept_id,), fetchone=True)
    if not dept:
        flash("Department not found.", "danger")
        return redirect(url_for("departments"))

    if request.method == "POST":
        f = request.form
        try:
            execute_db("""
                UPDATE DEPARTMENT
                SET dept_name=%s, location=%s, phone_ext=%s, description=%s
                WHERE dept_id=%s
            """, (
                f.get("dept_name", "").strip(),
                f.get("location", "").strip(),
                f.get("phone_ext", "").strip() or None,
                f.get("description", "").strip() or None,
                dept_id
            ))
            return redirect(url_for("departments"))
        except Exception as e:
            rows = query_db("SELECT * FROM DEPARTMENT ORDER BY dept_name")
            return render_template("departments.html", departments=rows, form_mode="edit", form_data={**dept, **f}, error=f"Error: {e}", edit_id=dept_id)

    rows = query_db("SELECT * FROM DEPARTMENT ORDER BY dept_name")
    return render_template("departments.html", departments=rows, form_mode="edit", form_data=dept, error=None, edit_id=dept_id)


@app.route("/departments/delete/<int:dept_id>", methods=["POST"])
@admin_required
def delete_department(dept_id):
    doc_count = query_db("SELECT COUNT(*) AS c FROM DOCTOR WHERE dept_id=%s", (dept_id,), fetchone=True)["c"]
    if doc_count > 0:
        flash("Cannot delete department: doctors are still assigned.", "danger")
        return redirect(url_for("departments"))
    execute_db("DELETE FROM DEPARTMENT WHERE dept_id=%s", (dept_id,))
    return redirect(url_for("departments"))


# ─────────────────────────────────────────────
# ROOM CRUD (ADMIN)
# ─────────────────────────────────────────────
@app.route("/rooms")
@admin_required
def rooms():
    rows = query_db("""
        SELECT r.*, d.dept_name
        FROM ROOM r
        JOIN DEPARTMENT d ON d.dept_id = r.dept_id
        ORDER BY r.room_number
    """)
    depts = query_db("SELECT dept_id, dept_name FROM DEPARTMENT ORDER BY dept_name")
    return render_template("rooms.html", rooms=rows, depts=depts, form_mode="list", form_data=None, error=None)


@app.route("/rooms/add", methods=["GET", "POST"])
@admin_required
def add_room():
    if request.method == "POST":
        f = request.form
        try:
            execute_db("""
                INSERT INTO ROOM (room_number, room_type, dept_id, capacity, daily_charge, status)
                VALUES (%s, %s, %s, %s, %s, 'Available')
            """, (
                f.get("room_number", "").strip(),
                f.get("room_type"),
                f.get("dept_id"),
                f.get("capacity"),
                f.get("daily_charge")
            ))
            return redirect(url_for("rooms"))
        except Exception as e:
            rows = query_db("""
                SELECT r.*, d.dept_name
                FROM ROOM r
                JOIN DEPARTMENT d ON d.dept_id = r.dept_id
                ORDER BY r.room_number
            """)
            depts = query_db("SELECT dept_id, dept_name FROM DEPARTMENT ORDER BY dept_name")
            return render_template("rooms.html", rooms=rows, depts=depts, form_mode="add", form_data=f, error=f"Error: {e}")

    rows = query_db("""
        SELECT r.*, d.dept_name
        FROM ROOM r
        JOIN DEPARTMENT d ON d.dept_id = r.dept_id
        ORDER BY r.room_number
    """)
    depts = query_db("SELECT dept_id, dept_name FROM DEPARTMENT ORDER BY dept_name")
    return render_template("rooms.html", rooms=rows, depts=depts, form_mode="add", form_data=None, error=None)


@app.route("/rooms/edit/<int:room_id>", methods=["GET", "POST"])
@admin_required
def edit_room(room_id):
    room = query_db("SELECT * FROM ROOM WHERE room_id=%s", (room_id,), fetchone=True)
    if not room:
        flash("Room not found.", "danger")
        return redirect(url_for("rooms"))

    if request.method == "POST":
        f = request.form
        try:
            execute_db("""
                UPDATE ROOM
                SET room_number=%s, room_type=%s, dept_id=%s, capacity=%s, daily_charge=%s
                WHERE room_id=%s
            """, (
                f.get("room_number", "").strip(),
                f.get("room_type"),
                f.get("dept_id"),
                f.get("capacity"),
                f.get("daily_charge"),
                room_id
            ))
            return redirect(url_for("rooms"))
        except Exception as e:
            rows = query_db("""
                SELECT r.*, d.dept_name
                FROM ROOM r
                JOIN DEPARTMENT d ON d.dept_id = r.dept_id
                ORDER BY r.room_number
            """)
            depts = query_db("SELECT dept_id, dept_name FROM DEPARTMENT ORDER BY dept_name")
            return render_template("rooms.html", rooms=rows, depts=depts, form_mode="edit", form_data={**room, **f}, error=f"Error: {e}", edit_id=room_id)

    rows = query_db("""
        SELECT r.*, d.dept_name
        FROM ROOM r
        JOIN DEPARTMENT d ON d.dept_id = r.dept_id
        ORDER BY r.room_number
    """)
    depts = query_db("SELECT dept_id, dept_name FROM DEPARTMENT ORDER BY dept_name")
    return render_template("rooms.html", rooms=rows, depts=depts, form_mode="edit", form_data=room, error=None, edit_id=room_id)


@app.route("/rooms/delete/<int:room_id>", methods=["POST"])
@admin_required
def delete_room(room_id):
    status_row = query_db("SELECT status FROM ROOM WHERE room_id=%s", (room_id,), fetchone=True)
    if not status_row:
        flash("Room not found.", "danger")
        return redirect(url_for("rooms"))
    if status_row["status"] == "Occupied":
        flash("Cannot delete room: room is currently occupied.", "danger")
        return redirect(url_for("rooms"))

    execute_db("DELETE FROM ROOM WHERE room_id=%s", (room_id,))
    return redirect(url_for("rooms"))


# ─────────────────────────────────────────────
# MEDICINE CRUD (ADMIN)
# ─────────────────────────────────────────────
@app.route("/medicines")
@admin_required
def medicines():
    rows = query_db("SELECT * FROM MEDICINE ORDER BY medicine_name")
    return render_template("medicines.html", medicines=rows, form_mode="list", form_data=None, error=None)


@app.route("/medicines/add", methods=["GET", "POST"])
@admin_required
def add_medicine():
    if request.method == "POST":
        f = request.form
        try:
            execute_db("""
                INSERT INTO MEDICINE (medicine_name, generic_name, category, unit_price, stock_quantity, manufacturer)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (
                f.get("medicine_name", "").strip(),
                f.get("generic_name", "").strip(),
                f.get("category", "").strip(),
                f.get("unit_price"),
                f.get("stock_quantity"),
                f.get("manufacturer", "").strip(),
            ))
            return redirect(url_for("medicines"))
        except Exception as e:
            rows = query_db("SELECT * FROM MEDICINE ORDER BY medicine_name")
            return render_template("medicines.html", medicines=rows, form_mode="add", form_data=f, error=f"Error: {e}")

    rows = query_db("SELECT * FROM MEDICINE ORDER BY medicine_name")
    return render_template("medicines.html", medicines=rows, form_mode="add", form_data=None, error=None)


@app.route("/medicines/edit/<int:medicine_id>", methods=["GET", "POST"])
@admin_required
def edit_medicine(medicine_id):
    med = query_db("SELECT * FROM MEDICINE WHERE medicine_id=%s", (medicine_id,), fetchone=True)
    if not med:
        flash("Medicine not found.", "danger")
        return redirect(url_for("medicines"))

    if request.method == "POST":
        f = request.form
        try:
            execute_db("""
                UPDATE MEDICINE
                SET medicine_name=%s, generic_name=%s, category=%s, unit_price=%s, stock_quantity=%s, manufacturer=%s
                WHERE medicine_id=%s
            """, (
                f.get("medicine_name", "").strip(),
                f.get("generic_name", "").strip(),
                f.get("category", "").strip(),
                f.get("unit_price"),
                f.get("stock_quantity"),
                f.get("manufacturer", "").strip(),
                medicine_id
            ))
            return redirect(url_for("medicines"))
        except Exception as e:
            rows = query_db("SELECT * FROM MEDICINE ORDER BY medicine_name")
            return render_template("medicines.html", medicines=rows, form_mode="edit", form_data={**med, **f}, error=f"Error: {e}", edit_id=medicine_id)

    rows = query_db("SELECT * FROM MEDICINE ORDER BY medicine_name")
    return render_template("medicines.html", medicines=rows, form_mode="edit", form_data=med, error=None, edit_id=medicine_id)


@app.route("/medicines/delete/<int:medicine_id>", methods=["POST"])
@admin_required
def delete_medicine(medicine_id):
    used = query_db("SELECT COUNT(*) AS c FROM PRESCRIPTION_DETAILS WHERE medicine_id=%s", (medicine_id,), fetchone=True)["c"]
    if used > 0:
        flash("Cannot delete medicine: used in prescription records.", "danger")
        return redirect(url_for("medicines"))
    execute_db("DELETE FROM MEDICINE WHERE medicine_id=%s", (medicine_id,))
    return redirect(url_for("medicines"))

# ─────────────────────────────────────────────
# APPOINTMENT CRUD
# ─────────────────────────────────────────────
@app.route("/appointments")
@login_required
def appointments():
    if session.get("role") == "Doctor":
        doctor_id = get_logged_in_doctor_id()
        rows = query_db("""
            SELECT a.appointment_id,
                   CONCAT(p.first_name,' ',p.last_name) AS patient_name,
                   CONCAT(s.first_name,' ',s.last_name) AS doctor_name,
                   d.specialization,
                   a.appointment_date, a.appointment_time,
                   a.reason, a.status
            FROM APPOINTMENT a
            JOIN PATIENT p ON p.patient_id=a.patient_id
            JOIN DOCTOR d  ON d.doctor_id=a.doctor_id
            JOIN STAFF s   ON s.staff_id=d.staff_id
            WHERE a.doctor_id=%s
            ORDER BY a.appointment_date DESC, a.appointment_time DESC
        """, (doctor_id,))
    else:
        rows = query_db("""
            SELECT a.appointment_id,
                   CONCAT(p.first_name,' ',p.last_name) AS patient_name,
                   CONCAT(s.first_name,' ',s.last_name) AS doctor_name,
                   d.specialization,
                   a.appointment_date, a.appointment_time,
                   a.reason, a.status
            FROM APPOINTMENT a
            JOIN PATIENT p ON p.patient_id=a.patient_id
            JOIN DOCTOR d  ON d.doctor_id=a.doctor_id
            JOIN STAFF s   ON s.staff_id=d.staff_id
            ORDER BY a.appointment_date DESC, a.appointment_time DESC
        """)
    return render_template("appointments.html", appointments=rows)

@app.route("/appointments/add", methods=["GET","POST"])
@login_required
def add_appointment():
    patients_list = query_db("SELECT patient_id, CONCAT(first_name,' ',last_name) AS name FROM PATIENT WHERE status='Active' ORDER BY first_name")
    doctors_list  = query_db("SELECT d.doctor_id, CONCAT(s.first_name,' ',s.last_name) AS name, d.specialization FROM DOCTOR d JOIN STAFF s ON s.staff_id=d.staff_id WHERE s.status='Active' ORDER BY s.first_name")
    error = None
    if request.method == "POST":
        f = request.form
        try:
            execute_db("""
                INSERT INTO APPOINTMENT (patient_id,doctor_id,appointment_date,appointment_time,reason,status)
                VALUES (%s,%s,%s,%s,%s,'Scheduled')
            """, (f["patient_id"], f["doctor_id"], f["apt_date"], f["apt_time"], f["reason"]))
            return redirect(url_for("appointments"))
        except Exception as e:
            error = f"Error: {str(e)}"
    return render_template("appointment_form.html",
        patients=patients_list, doctors=doctors_list, error=error,
        appointment=None, action="Schedule")

@app.route("/appointments/update_status/<int:aid>", methods=["POST"])
@login_required
def update_appointment_status(aid):
    new_status = request.form.get("status")
    execute_db("UPDATE APPOINTMENT SET status=%s WHERE appointment_id=%s", (new_status, aid))
    return redirect(url_for("appointments"))

# ─────────────────────────────────────────────
# ADMISSIONS
# ─────────────────────────────────────────────
@app.route("/admissions")
@login_required
def admissions():
    rows = query_db("""
        SELECT adm.admission_id,
               CONCAT(p.first_name,' ',p.last_name) AS patient_name,
               r.room_number, r.room_type,
               CONCAT(s.first_name,' ',s.last_name) AS doctor_name,
               adm.admit_date, adm.discharge_date,
               adm.diagnosis, adm.status
        FROM ADMISSION adm
        JOIN PATIENT p ON p.patient_id=adm.patient_id
        JOIN ROOM r    ON r.room_id=adm.room_id
        JOIN DOCTOR d  ON d.doctor_id=adm.attending_doctor
        JOIN STAFF s   ON s.staff_id=d.staff_id
        ORDER BY adm.admit_date DESC
    """)
    return render_template("admissions.html", admissions=rows)

@app.route("/admissions/add", methods=["GET","POST"])
@login_required
def add_admission():
    patients_list = query_db("SELECT patient_id, CONCAT(first_name,' ',last_name) AS name FROM PATIENT WHERE status='Active'")
    rooms_list    = query_db("SELECT room_id, room_number, room_type, daily_charge FROM ROOM WHERE status='Available'")
    doctors_list  = query_db("SELECT d.doctor_id, CONCAT(s.first_name,' ',s.last_name) AS name FROM DOCTOR d JOIN STAFF s ON s.staff_id=d.staff_id WHERE s.status='Active'")
    error = None
    if request.method == "POST":
        f = request.form
        try:
            # Check room availability
            room = query_db("SELECT status FROM ROOM WHERE room_id=%s", (f["room_id"],), fetchone=True)
            if not room or room["status"] != "Available":
                raise Exception("Selected room is not available.")
            # Create admission
            aid = execute_db("""
                INSERT INTO ADMISSION (patient_id, room_id, admit_date, diagnosis, attending_doctor, status)
                VALUES (%s, %s, CURDATE(), %s, %s, 'Active')
            """, (f["patient_id"], f["room_id"], f["diagnosis"], f["doctor_id"]))
            # Mark room occupied
            execute_db("UPDATE ROOM SET status='Occupied' WHERE room_id=%s", (f["room_id"],))
            # Create initial bill
            execute_db("""
                INSERT INTO BILLING (patient_id, admission_id, total_amount, paid_amount, bill_date, payment_status)
                VALUES (%s, %s, 0.00, 0.00, CURDATE(), 'Pending')
            """, (f["patient_id"], aid))
            return redirect(url_for("admissions"))
        except Exception as e:
            error = f"Error: {e}"
    return render_template("admission_form.html",
        patients=patients_list, rooms=rooms_list, doctors=doctors_list, error=error)

@app.route("/admissions/discharge/<int:aid>", methods=["POST"])
@login_required
def discharge_patient(aid):
    execute_db("UPDATE ADMISSION SET status='Discharged', discharge_date=CURDATE() WHERE admission_id=%s", (aid,))
    # Release room
    adm = query_db("SELECT room_id FROM ADMISSION WHERE admission_id=%s", (aid,), fetchone=True)
    if adm:
        execute_db("UPDATE ROOM SET status='Available' WHERE room_id=%s", (adm["room_id"],))
    return redirect(url_for("admissions"))

# ─────────────────────────────────────────────
# BILLING
# ─────────────────────────────────────────────
@app.route("/billing")
@doctor_or_staff_required
def billing():
    rows = query_db("""
        SELECT b.bill_id, CONCAT(p.first_name,' ',p.last_name) AS patient_name,
               b.total_amount, b.paid_amount,
               (b.total_amount - b.paid_amount) AS balance,
               b.bill_date, b.payment_status, b.payment_method
        FROM BILLING b
        JOIN PATIENT p ON p.patient_id=b.patient_id
        ORDER BY b.bill_date DESC
    """)
    return render_template("billing.html", bills=rows)

@app.route("/billing/pay/<int:bid>", methods=["POST"])
@doctor_or_staff_required
def record_payment(bid):
    # BUG FIX: form data is always a string — must convert to float before SQL arithmetic
    try:
        amount = float(request.form.get("amount", 0) or 0)
    except (ValueError, TypeError):
        amount = 0.0
    if amount <= 0:
        return redirect(url_for("billing"))

    method = request.form.get("method", "Cash") or "Cash"
    execute_db("""
        UPDATE BILLING
        SET paid_amount     = paid_amount + %s,
            payment_method  = %s
        WHERE bill_id = %s
    """, (amount, method, bid))
    # Update payment_status based on remaining balance
    execute_db("""
        UPDATE BILLING
        SET payment_status = CASE
            WHEN paid_amount >= total_amount THEN 'Paid'
            WHEN paid_amount > 0 THEN 'Partial'
            ELSE 'Pending'
        END
        WHERE bill_id = %s
    """, (bid,))
    return redirect(url_for("billing"))


@app.route("/billing/view/<int:bid>")
@doctor_or_staff_required
def billing_view(bid):
    row = query_db("""
        SELECT b.*, CONCAT(p.first_name,' ',p.last_name) AS patient_name
        FROM BILLING b
        JOIN PATIENT p ON p.patient_id=b.patient_id
        WHERE b.bill_id=%s
    """, (bid,), fetchone=True)
    if not row:
        return render_template("error.html", msg="Bill not found.")
    return render_template("billing_view.html", bill=row)


@app.route("/billing/generate", methods=["GET", "POST"])
@doctor_or_staff_required
def billing_generate():
    patients_list = query_db("""
        SELECT patient_id, CONCAT(first_name,' ',last_name) AS name
        FROM PATIENT
        WHERE status='Active'
        ORDER BY first_name
    """)
    admissions_list = query_db("""
        SELECT admission_id, patient_id
        FROM ADMISSION
        WHERE status='Active'
        ORDER BY admission_id DESC
    """)

    error = None
    if request.method == "POST":
        f = request.form
        try:
            patient_id = f.get("patient_id")
            admission_id = f.get("admission_id") or None
            total_amount = float(f.get("total_amount") or 0)
            if total_amount < 0:
                raise ValueError("Total amount must be non-negative.")
            execute_db("""
                INSERT INTO BILLING (patient_id, admission_id, total_amount, paid_amount, bill_date, payment_status)
                VALUES (%s, %s, %s, 0.00, CURDATE(), 'Pending')
            """, (patient_id, admission_id, total_amount))
            return redirect(url_for("billing"))
        except Exception as e:
            error = f"Error: {e}"

    return render_template("billing_generate.html", patients=patients_list, admissions=admissions_list, error=error)

# ─────────────────────────────────────────────
# STAFF MANAGEMENT
# ─────────────────────────────────────────────
@app.route("/staff")
@admin_required
def staff():
    rows = query_db("""
        SELECT s.staff_id, CONCAT(s.first_name,' ',s.last_name) AS name,
               s.staff_type, s.phone, s.email, s.hire_date, s.salary, s.shift, s.status,
               n.ward_assignment, n.certification,
               d.specialization, dep.dept_name
        FROM STAFF s
        LEFT JOIN NURSE n      ON n.staff_id = s.staff_id
        LEFT JOIN DOCTOR d     ON d.staff_id = s.staff_id
        LEFT JOIN DEPARTMENT dep ON dep.dept_id = d.dept_id
        ORDER BY s.staff_type, s.first_name
    """)
    return render_template("staff.html", staff=rows)


@app.route("/staff/add", methods=["GET", "POST"])
@admin_required
def add_staff():
    error = None
    if request.method == "POST":
        f = request.form
        try:
            sid = execute_db("""
                INSERT INTO STAFF
                    (first_name, last_name, staff_type, phone, email, hire_date, salary, shift, status)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,'Active')
            """, (
                f.get("first_name", "").strip(),
                f.get("last_name", "").strip(),
                f.get("staff_type"),
                f.get("phone", "").strip(),
                f.get("email", "").strip() or None,
                f.get("hire_date"),
                f.get("salary"),
                f.get("shift"),
            ))

            # Create USERS account (role Staff) linked via staff_id
            email = (f.get("email", "") or "").strip()
            username = (email.split("@")[0] if "@" in email and email else f"staff_{sid}")
            execute_db("""
                INSERT INTO USERS (username, email, password_hash, role, staff_id, is_active)
                VALUES (%s, %s, %s, 'Staff', %s, 1)
            """, (username, email or None, hash_pw("Staff@123"), sid))

            return redirect(url_for("staff"))
        except Exception as e:
            error = f"Error: {e}"

    return render_template("staff_form.html", staff_member=None, error=error, action="Add")


@app.route("/staff/edit/<int:staff_id>", methods=["GET", "POST"])
@admin_required
def edit_staff(staff_id):
    staff_member = query_db("SELECT * FROM STAFF WHERE staff_id=%s", (staff_id,), fetchone=True)
    if not staff_member:
        flash("Staff member not found.", "danger")
        return redirect(url_for("staff"))

    error = None
    if request.method == "POST":
        f = request.form
        try:
            execute_db("""
                UPDATE STAFF
                SET first_name=%s, last_name=%s, staff_type=%s, phone=%s, salary=%s, shift=%s, status=%s
                WHERE staff_id=%s
            """, (
                f.get("first_name", "").strip(),
                f.get("last_name", "").strip(),
                f.get("staff_type"),
                f.get("phone", "").strip(),
                f.get("salary"),
                f.get("shift"),
                f.get("status"),
                staff_id,
            ))
            # optional email update
            if f.get("email") is not None:
                execute_db("UPDATE STAFF SET email=%s WHERE staff_id=%s", (f.get("email") or None, staff_id))
                execute_db("UPDATE USERS SET email=%s WHERE staff_id=%s", (f.get("email") or None, staff_id))
            return redirect(url_for("staff"))
        except Exception as e:
            error = f"Error: {e}"
            staff_member = {**staff_member, **f}

    return render_template("staff_form.html", staff_member=staff_member, error=error, action="Edit")


@app.route("/staff/delete/<int:staff_id>", methods=["POST"])
@admin_required
def delete_staff(staff_id):
    try:
        execute_db("DELETE FROM USERS WHERE staff_id=%s", (staff_id,))
        execute_db("DELETE FROM STAFF WHERE staff_id=%s", (staff_id,))
    except Exception as e:
        flash(f"Staff delete blocked by dependent records: {e}", "danger")
        return redirect(url_for("staff"))
    return redirect(url_for("staff"))

# ─────────────────────────────────────────────
# REPORTS & EXPORT
# ─────────────────────────────────────────────
@app.route("/reports")
@doctor_required
def reports():
    patient_report = query_db("""
        SELECT p.patient_id,
               CONCAT(p.first_name,' ',p.last_name) AS patient_name,
               p.gender, p.blood_group, p.phone,
               COUNT(DISTINCT a.appointment_id)   AS appointments,
               COUNT(DISTINCT adm.admission_id)   AS admissions,
               COALESCE(SUM(b.total_amount), 0)   AS total_billed
        FROM PATIENT p
        LEFT JOIN APPOINTMENT a ON a.patient_id = p.patient_id
        LEFT JOIN ADMISSION adm ON adm.patient_id= p.patient_id
        LEFT JOIN BILLING b     ON b.patient_id  = p.patient_id
        WHERE p.status='Active'
        GROUP BY p.patient_id
        ORDER BY total_billed DESC
    """)
    return render_template("reports.html", patient_report=patient_report)

@app.route("/reports/export/csv")
@doctor_required
def export_csv():
    rows = query_db("""
        SELECT p.patient_id, CONCAT(p.first_name,' ',p.last_name) AS patient_name,
               p.gender, p.blood_group, p.phone, p.registration_date,
               COALESCE(SUM(b.total_amount),0) AS total_billed,
               COALESCE(SUM(b.paid_amount),0)  AS total_paid
        FROM PATIENT p
        LEFT JOIN BILLING b ON b.patient_id=p.patient_id
        GROUP BY p.patient_id ORDER BY total_billed DESC
    """)

    # BUG FIX: rows[0].keys() crashes on empty result — define fallback fieldnames
    fieldnames = list(rows[0].keys()) if rows else [
        'patient_id','patient_name','gender','blood_group',
        'phone','registration_date','total_billed','total_paid'
    ]

    si = io.StringIO()
    writer = csv.DictWriter(si, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    output = io.BytesIO()
    output.write(si.getvalue().encode("utf-8-sig"))
    output.seek(0)
    return send_file(output, mimetype="text/csv",
                     as_attachment=True, download_name="patient_billing_report.csv")

# ─────────────────────────────────────────────
# API ENDPOINTS (for dashboard JS charts)
# ─────────────────────────────────────────────
@app.route("/api/kpis")
@doctor_required
def api_kpis():
    return jsonify({
        "total_patients":    query_db("SELECT COUNT(*) AS c FROM PATIENT WHERE status='Active'", fetchone=True)["c"],
        "total_doctors":     query_db("SELECT COUNT(*) AS c FROM DOCTOR", fetchone=True)["c"],
        "active_admissions": query_db("SELECT COUNT(*) AS c FROM ADMISSION WHERE status='Active'", fetchone=True)["c"],
        "monthly_revenue":   float(query_db(
            "SELECT COALESCE(SUM(paid_amount),0) AS r FROM BILLING WHERE MONTH(payment_date)=MONTH(CURDATE()) AND YEAR(payment_date)=YEAR(CURDATE()) AND payment_status IN ('Paid','Partial')",
            fetchone=True)["r"])
    })

@app.route("/api/dept_chart")
@doctor_required
def api_dept_chart():
    rows = query_db("""
        SELECT dep.dept_name AS label, COUNT(DISTINCT a.patient_id) AS value
        FROM DEPARTMENT dep
        LEFT JOIN DOCTOR d    ON d.dept_id    = dep.dept_id
        LEFT JOIN APPOINTMENT a ON a.doctor_id = d.doctor_id
        GROUP BY dep.dept_id, dep.dept_name ORDER BY value DESC
    """)
    return jsonify([dict(r) for r in rows])

@app.route("/api/revenue_chart")
@doctor_required
def api_revenue_chart():
    rows = query_db("""
        SELECT DATE_FORMAT(payment_date,'%b %Y') AS label,
               ROUND(SUM(paid_amount),2) AS value
        FROM BILLING
        WHERE payment_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
          AND payment_status IN ('Paid','Partial')
        GROUP BY YEAR(payment_date), MONTH(payment_date)
        ORDER BY YEAR(payment_date), MONTH(payment_date)
    """)
    return jsonify([dict(r) for r in rows])

@app.route("/profile")
def profile():
    if "user_id" not in session: return redirect(url_for("login"))
    return render_template("placeholder.html", title="My Profile")

@app.route("/settings")
def settings():
    if "user_id" not in session: return redirect(url_for("login"))
    return render_template("placeholder.html", title="Settings")

@app.route("/change-password")
def change_password():
    if "user_id" not in session: return redirect(url_for("login"))
    return render_template("placeholder.html", title="Change Password")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
