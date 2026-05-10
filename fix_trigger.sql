DROP TRIGGER IF EXISTS trg_after_update_billing;

DELIMITER $$
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
DELIMITER ;
