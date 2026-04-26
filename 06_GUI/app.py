"""
Hospital Management System - Flask Backend
==========================================
Install requirements: pip install flask mysql-connector-python
Run: python app.py
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
import mysql.connector
import hashlib
import io
import csv
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

# ─────────────────────────────────────────────
# AUTH ROUTES
# ─────────────────────────────────────────────
@app.route("/", methods=["GET","POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username","").strip()
        password = request.form.get("password","")
        user = query_db(
            "SELECT * FROM USERS WHERE username=%s AND password_hash=%s AND is_active=1",
            (username, hash_pw(password)), fetchone=True
        )
        if user:
            session["user_id"]  = user["user_id"]
            session["username"] = user["username"]
            session["role"]     = user["role"]
            return redirect(url_for("dashboard"))
        error = "Invalid username or password."
    return render_template("login.html", error=error)

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
    total_patients   = query_db("SELECT COUNT(*) AS c FROM PATIENT WHERE status='Active'", fetchone=True)["c"]
    total_doctors    = query_db("SELECT COUNT(*) AS c FROM DOCTOR", fetchone=True)["c"]
    active_admissions= query_db("SELECT COUNT(*) AS c FROM ADMISSION WHERE status='Active'", fetchone=True)["c"]
    monthly_revenue  = query_db(
        "SELECT COALESCE(SUM(paid_amount),0) AS r FROM BILLING WHERE MONTH(bill_date)=MONTH(CURDATE()) AND YEAR(bill_date)=YEAR(CURDATE())",
        fetchone=True)["r"]

    # Chart data: patients per department
    dept_data = query_db("""
        SELECT dep.dept_name, COUNT(DISTINCT a.patient_id) AS cnt
        FROM DEPARTMENT dep
        LEFT JOIN DOCTOR d   ON d.dept_id   = dep.dept_id
        LEFT JOIN APPOINTMENT a ON a.doctor_id = d.doctor_id
        GROUP BY dep.dept_id, dep.dept_name
        ORDER BY cnt DESC LIMIT 10
    """)

    # Chart data: revenue per month (last 6 months)
    rev_data = query_db("""
        SELECT DATE_FORMAT(bill_date,'%b %Y') AS month_label,
               SUM(paid_amount) AS revenue
        FROM BILLING
        WHERE bill_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
        GROUP BY YEAR(bill_date), MONTH(bill_date), DATE_FORMAT(bill_date,'%b %Y')
        ORDER BY YEAR(bill_date), MONTH(bill_date)
    """)

    # Top 10 patients by billing
    top_patients = query_db("""
        SELECT CONCAT(p.first_name,' ',p.last_name) AS name,
               p.phone, p.blood_group,
               SUM(b.total_amount) AS total_billed,
               SUM(b.paid_amount)  AS total_paid,
               SUM(b.total_amount - b.paid_amount) AS balance
        FROM PATIENT p JOIN BILLING b ON b.patient_id=p.patient_id
        GROUP BY p.patient_id, p.first_name, p.last_name, p.phone, p.blood_group
        ORDER BY total_billed DESC LIMIT 10
    """)

    return render_template("dashboard.html",
        total_patients=total_patients,
        total_doctors=total_doctors,
        active_admissions=active_admissions,
        monthly_revenue=monthly_revenue,
        dept_data=dept_data,
        rev_data=rev_data,
        top_patients=top_patients
    )

# ─────────────────────────────────────────────
# PATIENT CRUD
# ─────────────────────────────────────────────
@app.route("/patients")
@login_required
def patients():
    search = request.args.get("q","").strip()
    if search:
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
        SELECT d.doctor_id, CONCAT(s.first_name,' ',s.last_name) AS name,
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

# ─────────────────────────────────────────────
# APPOINTMENT CRUD
# ─────────────────────────────────────────────
@app.route("/appointments")
@login_required
def appointments():
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
@login_required
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
@login_required
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
        SET paid_amount = paid_amount + %s,
            payment_method = %s,
            payment_status = CASE
                WHEN (paid_amount + %s) >= total_amount THEN 'Paid'
                WHEN (paid_amount + %s) > 0             THEN 'Partial'
                ELSE 'Pending'
            END
        WHERE bill_id = %s
    """, (amount, method, amount, amount, bid))
    return redirect(url_for("billing"))

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

# ─────────────────────────────────────────────
# REPORTS & EXPORT
# ─────────────────────────────────────────────
@app.route("/reports")
@login_required
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
@login_required
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
@login_required
def api_kpis():
    return jsonify({
        "total_patients":    query_db("SELECT COUNT(*) AS c FROM PATIENT WHERE status='Active'", fetchone=True)["c"],
        "total_doctors":     query_db("SELECT COUNT(*) AS c FROM DOCTOR", fetchone=True)["c"],
        "active_admissions": query_db("SELECT COUNT(*) AS c FROM ADMISSION WHERE status='Active'", fetchone=True)["c"],
        "monthly_revenue":   float(query_db(
            "SELECT COALESCE(SUM(paid_amount),0) AS r FROM BILLING WHERE MONTH(bill_date)=MONTH(CURDATE()) AND YEAR(bill_date)=YEAR(CURDATE())",
            fetchone=True)["r"])
    })

@app.route("/api/dept_chart")
@login_required
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
@login_required
def api_revenue_chart():
    rows = query_db("""
        SELECT DATE_FORMAT(bill_date,'%b %Y') AS label,
               ROUND(SUM(paid_amount),2) AS value
        FROM BILLING
        WHERE bill_date >= DATE_SUB(CURDATE(), INTERVAL 6 MONTH)
        GROUP BY YEAR(bill_date), MONTH(bill_date)
        ORDER BY YEAR(bill_date), MONTH(bill_date)
    """)
    return jsonify([dict(r) for r in rows])

if __name__ == "__main__":
    app.run(debug=True, port=5000)
