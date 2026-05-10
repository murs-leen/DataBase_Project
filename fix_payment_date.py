import mysql.connector

try:
    c = mysql.connector.connect(user='root', password='password', database='hms_db')
    cur = c.cursor()

    # 1. Add payment_date column if it doesn't exist
    cur.execute("""
        SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'hms_db' AND TABLE_NAME = 'BILLING' AND COLUMN_NAME = 'payment_date'
    """)
    if cur.fetchone()[0] == 0:
        cur.execute("ALTER TABLE BILLING ADD COLUMN payment_date DATE NULL DEFAULT NULL")
        print("Added payment_date column.")
    else:
        print("payment_date column already exists.")

    # 2. Backfill: for already-paid bills, set payment_date = bill_date
    cur.execute("""
        UPDATE BILLING 
        SET payment_date = bill_date 
        WHERE payment_status IN ('Paid', 'Partial') AND payment_date IS NULL
    """)
    print("Backfilled payment_date for existing paid records.")

    # 3. Drop and recreate trigger to also stamp payment_date
    cur.execute("DROP TRIGGER IF EXISTS trg_before_update_billing")
    cur.execute("""
    CREATE TRIGGER trg_before_update_billing
    BEFORE UPDATE ON BILLING
    FOR EACH ROW
    BEGIN
        IF NEW.paid_amount >= NEW.total_amount THEN
            SET NEW.payment_status = 'Paid';
            SET NEW.payment_date   = CURDATE();
        ELSEIF NEW.paid_amount > 0 AND NEW.paid_amount < NEW.total_amount THEN
            SET NEW.payment_status = 'Partial';
            SET NEW.payment_date   = CURDATE();
        ELSE
            SET NEW.payment_status = 'Pending';
        END IF;
    END
    """)
    print("Trigger updated to stamp payment_date on payment.")
    c.commit()

    # 4. Verify
    cur.execute("SHOW TRIGGERS WHERE `Trigger` LIKE '%billing%'")
    for t in cur.fetchall():
        print(f"  Trigger: {t[0]}, Event: {t[1]}, Timing: {t[4]}")

    cur.execute("SELECT bill_id, bill_date, payment_date, paid_amount, payment_status FROM BILLING ORDER BY bill_id DESC LIMIT 5")
    print("\nSample rows:")
    for r in cur.fetchall():
        print(f"  {r}")

except Exception as e:
    print(f"Error: {e}")
finally:
    try: c.close()
    except: pass
