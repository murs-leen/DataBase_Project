-- =============================================================
-- HOSPITAL MANAGEMENT SYSTEM
-- Stored Programming: Procedures, Functions, Triggers, Cursors
-- MySQL 8.0+ equivalent of PL/SQL
-- =============================================================
USE hms_db;

-- Enable delimiter change for procedure/trigger definitions
DELIMITER $$

-- =============================================================
-- STORED PROCEDURE 1: sp_register_patient
-- Registers a new patient with IN/OUT parameters
-- OUT: the newly generated patient_id
-- =============================================================
CREATE PROCEDURE sp_register_patient(
    IN  p_first_name   VARCHAR(50),
    IN  p_last_name    VARCHAR(50),
    IN  p_dob          DATE,
    IN  p_gender       ENUM('Male','Female','Other'),
    IN  p_phone        VARCHAR(15),
    IN  p_email        VARCHAR(100),
    IN  p_address      TEXT,
    IN  p_blood_group  VARCHAR(5),
    OUT p_new_id       INT,
    OUT p_message      VARCHAR(200)
)
BEGIN
    -- Exception handler
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        SET p_new_id  = -1;
        SET p_message = 'ERROR: Failed to register patient. Duplicate phone/email or invalid data.';
        ROLLBACK;
    END;

    START TRANSACTION;

    -- Validate blood group
    IF p_blood_group NOT IN ('A+','A-','B+','B-','AB+','AB-','O+','O-') THEN
        SET p_new_id  = -1;
        SET p_message = 'ERROR: Invalid blood group provided.';
        ROLLBACK;
    ELSE
        INSERT INTO PATIENT
            (first_name, last_name, date_of_birth, gender, phone, email, address, blood_group)
        VALUES
            (p_first_name, p_last_name, p_dob, p_gender, p_phone, p_email, p_address, p_blood_group);

        SET p_new_id  = LAST_INSERT_ID();
        SET p_message = CONCAT('SUCCESS: Patient registered with ID = ', p_new_id);
        COMMIT;
    END IF;
END$$

-- =============================================================
-- STORED PROCEDURE 2: sp_generate_bill
-- Generates/updates bill for a patient after admission
-- Includes exception handling
-- =============================================================
CREATE PROCEDURE sp_generate_bill(
    IN p_patient_id   INT,
    IN p_admission_id INT,
    IN p_extra_charges DECIMAL(12,2),
    IN p_payment_method VARCHAR(30)
)
BEGIN
    DECLARE v_room_charge   DECIMAL(12,2) DEFAULT 0;
    DECLARE v_consult_fee   DECIMAL(12,2) DEFAULT 0;
    DECLARE v_med_cost      DECIMAL(12,2) DEFAULT 0;
    DECLARE v_stay_days     INT           DEFAULT 0;
    DECLARE v_daily_rate    DECIMAL(10,2) DEFAULT 0;
    DECLARE v_total         DECIMAL(12,2) DEFAULT 0;
    DECLARE v_doctor_id     INT;
    DECLARE v_existing_bill INT DEFAULT 0;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'ERROR: Bill generation failed due to database error.';
    END;

    START TRANSACTION;

    -- Calculate room charges (stay days × daily rate)
    SELECT
        DATEDIFF(COALESCE(a.discharge_date, CURDATE()), a.admit_date),
        r.daily_charge,
        a.attending_doctor
    INTO v_stay_days, v_daily_rate, v_doctor_id
    FROM ADMISSION a
    JOIN ROOM r ON r.room_id = a.room_id
    WHERE a.admission_id = p_admission_id
      AND a.patient_id   = p_patient_id;

    SET v_room_charge = v_stay_days * v_daily_rate;

    -- Get doctor consultation fee
    SELECT consultation_fee INTO v_consult_fee
    FROM DOCTOR WHERE doctor_id = v_doctor_id;

    -- Calculate total medicine cost from prescriptions
    SELECT COALESCE(SUM(pd.quantity * m.unit_price), 0)
    INTO v_med_cost
    FROM PRESCRIPTION pr
    JOIN PRESCRIPTION_DETAILS pd ON pd.prescription_id = pr.prescription_id
    JOIN MEDICINE m              ON m.medicine_id       = pd.medicine_id
    WHERE pr.patient_id = p_patient_id;

    -- Total
    SET v_total = v_room_charge + v_consult_fee + v_med_cost + COALESCE(p_extra_charges, 0);

    -- Check if bill already exists for this admission
    SELECT COUNT(*) INTO v_existing_bill
    FROM BILLING
    WHERE patient_id = p_patient_id AND admission_id = p_admission_id;

    IF v_existing_bill > 0 THEN
        -- Update existing bill
        UPDATE BILLING
        SET total_amount    = v_total,
            payment_method  = p_payment_method,
            bill_date       = CURDATE()
        WHERE patient_id = p_patient_id AND admission_id = p_admission_id;
    ELSE
        -- Insert new bill
        INSERT INTO BILLING
            (patient_id, admission_id, total_amount, paid_amount, bill_date, payment_status, payment_method)
        VALUES
            (p_patient_id, p_admission_id, v_total, 0.00, CURDATE(), 'Pending', p_payment_method);
    END IF;

    COMMIT;

    SELECT CONCAT('Bill generated: PKR ', v_total,
                  ' | Room: ', v_room_charge,
                  ' | Consult: ', v_consult_fee,
                  ' | Medicines: ', v_med_cost) AS bill_summary;
END$$

-- =============================================================
-- STORED PROCEDURE 3: sp_admit_patient
-- Admits patient and calls sp_generate_bill for billing setup
-- Demonstrates procedure calling another procedure
-- =============================================================
CREATE PROCEDURE sp_admit_patient(
    IN p_patient_id      INT,
    IN p_room_id         INT,
    IN p_doctor_id       INT,
    IN p_diagnosis       TEXT,
    OUT p_admission_id   INT,
    OUT p_status_msg     VARCHAR(200)
)
BEGIN
    DECLARE v_room_status VARCHAR(20);
    DECLARE v_room_dept   INT;

    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_admission_id = -1;
        SET p_status_msg   = 'ERROR: Admission failed.';
    END;

    START TRANSACTION;

    -- Check room availability
    SELECT status INTO v_room_status
    FROM ROOM WHERE room_id = p_room_id FOR UPDATE;

    IF v_room_status != 'Available' THEN
        SET p_admission_id = -1;
        SET p_status_msg   = CONCAT('ERROR: Room is currently ', v_room_status, '. Choose another room.');
        ROLLBACK;
    ELSE
        -- Create admission record
        INSERT INTO ADMISSION
            (patient_id, room_id, admit_date, diagnosis, attending_doctor, status)
        VALUES
            (p_patient_id, p_room_id, CURDATE(), p_diagnosis, p_doctor_id, 'Active');

        SET p_admission_id = LAST_INSERT_ID();

        -- Mark room as occupied
        UPDATE ROOM SET status = 'Occupied' WHERE room_id = p_room_id;

        COMMIT;

        SET p_status_msg = CONCAT('SUCCESS: Patient admitted. Admission ID = ', p_admission_id);

        -- Call billing procedure to create initial bill record
        CALL sp_generate_bill(p_patient_id, p_admission_id, 0, NULL);
    END IF;
END$$

-- =============================================================
-- FUNCTION 1: fn_calculate_age
-- Returns patient age in years from date_of_birth
-- Used inside SELECT queries
-- =============================================================
CREATE FUNCTION fn_calculate_age(p_dob DATE)
RETURNS INT
DETERMINISTIC
BEGIN
    RETURN TIMESTAMPDIFF(YEAR, p_dob, CURDATE());
END$$

-- =============================================================
-- FUNCTION 2: fn_get_patient_balance
-- Returns outstanding balance (total - paid) for a patient
-- =============================================================
CREATE FUNCTION fn_get_patient_balance(p_patient_id INT)
RETURNS DECIMAL(12,2)
READS SQL DATA
BEGIN
    DECLARE v_balance DECIMAL(12,2) DEFAULT 0.00;

    SELECT COALESCE(SUM(total_amount - paid_amount), 0.00)
    INTO v_balance
    FROM BILLING
    WHERE patient_id = p_patient_id
      AND payment_status IN ('Pending', 'Partial');

    RETURN v_balance;
END$$

-- Demo: Using fn_calculate_age inside SELECT
-- SELECT patient_id, CONCAT(first_name,' ',last_name) AS name,
--        fn_calculate_age(date_of_birth) AS age
-- FROM PATIENT WHERE status='Active';

-- =============================================================
-- TRIGGER 1: trg_before_insert_appointment (BEFORE INSERT)
-- Validates that appointment date is not in the past
-- and that no time conflict exists for the same doctor
-- =============================================================
CREATE TRIGGER trg_before_insert_appointment
BEFORE INSERT ON APPOINTMENT
FOR EACH ROW
BEGIN
    DECLARE v_conflict INT DEFAULT 0;

    -- Prevent backdated appointments
    IF NEW.appointment_date < CURDATE() THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'ERROR: Appointment date cannot be in the past.';
    END IF;

    -- Check doctor time conflict (same date + time)
    SELECT COUNT(*) INTO v_conflict
    FROM APPOINTMENT
    WHERE doctor_id        = NEW.doctor_id
      AND appointment_date = NEW.appointment_date
      AND appointment_time = NEW.appointment_time
      AND status           != 'Cancelled';

    IF v_conflict > 0 THEN
        SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'ERROR: Doctor already has an appointment at this date and time.';
    END IF;
END$$

-- =============================================================
-- TRIGGER 2: trg_before_update_billing (BEFORE UPDATE)
-- Automatically sets payment_status based on paid_amount
-- =============================================================
CREATE TRIGGER trg_before_update_billing
BEFORE UPDATE ON BILLING
FOR EACH ROW
BEGIN
    IF NEW.paid_amount >= NEW.total_amount THEN
        SET NEW.payment_status = 'Paid';
    ELSEIF NEW.paid_amount > 0 AND NEW.paid_amount < NEW.total_amount THEN
        SET NEW.payment_status = 'Partial';
    ELSE
        SET NEW.payment_status = 'Pending';
    END IF;
END$$

-- =============================================================
-- TRIGGER 3: trg_after_delete_admission (AFTER DELETE)
-- Releases room back to Available after admission is deleted
-- =============================================================
CREATE TRIGGER trg_after_delete_admission
AFTER DELETE ON ADMISSION
FOR EACH ROW
BEGIN
    -- Release the room only if no other active admission uses it
    IF NOT EXISTS (
        SELECT 1 FROM ADMISSION
        WHERE room_id = OLD.room_id AND status = 'Active'
    ) THEN
        UPDATE ROOM
        SET status = 'Available'
        WHERE room_id = OLD.room_id
          AND status  = 'Occupied';
    END IF;
END$$

-- =============================================================
-- CURSOR 1: cur_overdue_bills
-- Iterates over all overdue bills and prints summary report
-- Uses explicit cursor
-- =============================================================
CREATE PROCEDURE sp_overdue_bill_report()
BEGIN
    DECLARE v_done         INT DEFAULT 0;
    DECLARE v_bill_id      INT;
    DECLARE v_patient_name VARCHAR(101);
    DECLARE v_balance      DECIMAL(12,2);
    DECLARE v_days_overdue INT;

    -- Explicit cursor declaration
    DECLARE cur_overdue CURSOR FOR
        SELECT
            b.bill_id,
            CONCAT(p.first_name, ' ', p.last_name),
            (b.total_amount - b.paid_amount),
            DATEDIFF(CURDATE(), b.bill_date)
        FROM BILLING b
        JOIN PATIENT p ON p.patient_id = b.patient_id
        WHERE b.payment_status IN ('Pending','Partial')
          AND b.bill_date < DATE_SUB(CURDATE(), INTERVAL 7 DAY)
        ORDER BY b.bill_date ASC;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_done = 1;

    -- Temporary result table
    DROP TEMPORARY TABLE IF EXISTS tmp_overdue_report;
    CREATE TEMPORARY TABLE tmp_overdue_report (
        bill_id      INT,
        patient_name VARCHAR(101),
        balance      DECIMAL(12,2),
        days_overdue INT
    );

    OPEN cur_overdue;
    fetch_loop: LOOP
        FETCH cur_overdue INTO v_bill_id, v_patient_name, v_balance, v_days_overdue;
        IF v_done = 1 THEN
            LEAVE fetch_loop;
        END IF;

        INSERT INTO tmp_overdue_report VALUES
            (v_bill_id, v_patient_name, v_balance, v_days_overdue);
    END LOOP;
    CLOSE cur_overdue;

    -- Return result
    SELECT * FROM tmp_overdue_report ORDER BY days_overdue DESC;
    DROP TEMPORARY TABLE IF EXISTS tmp_overdue_report;
END$$

-- =============================================================
-- CURSOR 2: cur_dept_revenue (Parameterized Cursor equivalent)
-- Calculates total revenue per department using cursor
-- p_dept_id = 0 means ALL departments
-- =============================================================
CREATE PROCEDURE sp_dept_revenue_report(IN p_dept_id INT)
BEGIN
    DECLARE v_done      INT DEFAULT 0;
    DECLARE v_dept_name VARCHAR(100);
    DECLARE v_revenue   DECIMAL(12,2);
    DECLARE v_dept_id   INT;

    DECLARE cur_dept CURSOR FOR
        SELECT
            dep.dept_id,
            dep.dept_name,
            COALESCE(SUM(b.total_amount), 0) AS dept_revenue
        FROM DEPARTMENT dep
        LEFT JOIN ROOM r     ON r.dept_id     = dep.dept_id
        LEFT JOIN ADMISSION a ON a.room_id    = r.room_id
        LEFT JOIN BILLING b   ON b.admission_id = a.admission_id
        WHERE (p_dept_id = 0 OR dep.dept_id = p_dept_id)
        GROUP BY dep.dept_id, dep.dept_name;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET v_done = 1;

    DROP TEMPORARY TABLE IF EXISTS tmp_dept_revenue;
    CREATE TEMPORARY TABLE tmp_dept_revenue (
        dept_id   INT,
        dept_name VARCHAR(100),
        revenue   DECIMAL(12,2)
    );

    OPEN cur_dept;
    read_loop: LOOP
        FETCH cur_dept INTO v_dept_id, v_dept_name, v_revenue;
        IF v_done = 1 THEN LEAVE read_loop; END IF;
        INSERT INTO tmp_dept_revenue VALUES (v_dept_id, v_dept_name, v_revenue);
    END LOOP;
    CLOSE cur_dept;

    SELECT * FROM tmp_dept_revenue ORDER BY revenue DESC;
    DROP TEMPORARY TABLE IF EXISTS tmp_dept_revenue;
END$$

DELIMITER ;

-- =============================================================
-- QUICK TESTS (uncomment to run)
-- =============================================================
-- CALL sp_register_patient('Test','User','1990-01-01','Male','03009999999',NULL,'Test Address','O+',@id,@msg);
-- SELECT @id, @msg;

-- CALL sp_admit_patient(2, 2, 1, 'Observation', @adm_id, @msg);
-- SELECT @adm_id, @msg;

-- CALL sp_overdue_bill_report();
-- CALL sp_dept_revenue_report(0);
-- SELECT fn_calculate_age('1985-03-12') AS age;
-- SELECT fn_get_patient_balance(3) AS balance_due;
