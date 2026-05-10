import mysql.connector

try:
    c = mysql.connector.connect(user='root', password='password', database='hms_db')
    cur = c.cursor()

    # Drop BOTH triggers (old broken one + new one if already created)
    cur.execute("DROP TRIGGER IF EXISTS trg_after_update_billing")
    print("Dropped trg_after_update_billing")
    cur.execute("DROP TRIGGER IF EXISTS trg_before_update_billing")
    print("Dropped trg_before_update_billing")

    # Re-create the correct BEFORE UPDATE trigger (uses SET NEW.field, no recursive UPDATE)
    cur.execute("""
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
    END
    """)
    c.commit()
    print("SUCCESS: trg_before_update_billing created correctly.")

    # Verify
    cur.execute("SHOW TRIGGERS WHERE `Trigger` LIKE '%billing%'")
    for t in cur.fetchall():
        print(f"  Trigger: {t[0]}, Event: {t[1]}, Timing: {t[4]}")

except Exception as e:
    print(f"Error: {e}")
finally:
    try:
        c.close()
    except:
        pass
