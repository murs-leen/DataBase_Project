-- ClinicFlow / HMS full data reset script (MySQL)
-- Safe behavior:
-- 1) Keeps schema intact (no DROP TABLE)
-- 2) Skips non-existent tables silently
-- 3) Disables FK checks while truncating
-- 4) Resets AUTO_INCREMENT for existing tables
-- 5) Verifies row counts after reset

USE hms_db;

-- STEP 1: Detected project tables (from schema/code)
-- ADMISSION, APPOINTMENT, BILLING, DEPARTMENT, DOCTOR, MEDICINE, NURSE,
-- PATIENT, PRESCRIPTION, PRESCRIPTION_DETAILS, ROOM, STAFF, USERS

-- STEP 2: Disable FK checks
SET FOREIGN_KEY_CHECKS = 0;

DELIMITER $$

DROP PROCEDURE IF EXISTS truncate_if_exists $$
CREATE PROCEDURE truncate_if_exists(IN p_table_name VARCHAR(128))
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = DATABASE()
          AND table_name = p_table_name
    ) THEN
        SET @sql_stmt = CONCAT('TRUNCATE TABLE `', p_table_name, '`');
        PREPARE stmt FROM @sql_stmt;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
END $$

DROP PROCEDURE IF EXISTS reset_ai_if_exists $$
CREATE PROCEDURE reset_ai_if_exists(IN p_table_name VARCHAR(128))
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = DATABASE()
          AND table_name = p_table_name
    ) THEN
        SET @sql_stmt = CONCAT('ALTER TABLE `', p_table_name, '` AUTO_INCREMENT = 1');
        PREPARE stmt FROM @sql_stmt;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
END $$

DROP PROCEDURE IF EXISTS count_if_exists $$
CREATE PROCEDURE count_if_exists(IN p_table_name VARCHAR(128))
BEGIN
    IF EXISTS (
        SELECT 1
        FROM information_schema.tables
        WHERE table_schema = DATABASE()
          AND table_name = p_table_name
    ) THEN
        SET @sql_stmt = CONCAT('SELECT ''', p_table_name, ''' AS table_name, COUNT(*) AS total FROM `', p_table_name, '`');
    ELSE
        SET @sql_stmt = CONCAT('SELECT ''', p_table_name, ''' AS table_name, 0 AS total');
    END IF;
    PREPARE stmt FROM @sql_stmt;
    EXECUTE stmt;
    DEALLOCATE PREPARE stmt;
END $$

DELIMITER ;

-- STEP 3: TRUNCATE TABLES
-- Priority block from your request (auth/session first; skipped silently if missing)
CALL truncate_if_exists('login_history');
CALL truncate_if_exists('sessions');
CALL truncate_if_exists('personal_access_tokens');
CALL truncate_if_exists('password_reset_tokens');
CALL truncate_if_exists('remember_tokens');
CALL truncate_if_exists('oauth_access_tokens');
CALL truncate_if_exists('oauth_refresh_tokens');
CALL truncate_if_exists('failed_jobs');
CALL truncate_if_exists('activity_logs');
CALL truncate_if_exists('audit_logs');

-- Pivot / junction from your request (skipped silently if missing)
CALL truncate_if_exists('role_user');
CALL truncate_if_exists('permission_role');
CALL truncate_if_exists('model_has_roles');
CALL truncate_if_exists('model_has_permissions');
CALL truncate_if_exists('role_has_permissions');

-- Child/dependent tables in this project
CALL truncate_if_exists('PRESCRIPTION_DETAILS');
CALL truncate_if_exists('BILLING');
CALL truncate_if_exists('ADMISSION');
CALL truncate_if_exists('APPOINTMENT');
CALL truncate_if_exists('PRESCRIPTION');
CALL truncate_if_exists('USERS');
CALL truncate_if_exists('NURSE');
CALL truncate_if_exists('DOCTOR');
CALL truncate_if_exists('ROOM');

-- Parent tables in this project
CALL truncate_if_exists('PATIENT');
CALL truncate_if_exists('STAFF');
CALL truncate_if_exists('MEDICINE');
CALL truncate_if_exists('DEPARTMENT');

-- Also include your requested parent/auth tables (if present)
CALL truncate_if_exists('roles');
CALL truncate_if_exists('permissions');
CALL truncate_if_exists('users');

-- STEP 4: Reset AUTO_INCREMENT / sequences (MySQL)
-- Requested examples
CALL reset_ai_if_exists('users');
CALL reset_ai_if_exists('sessions');
CALL reset_ai_if_exists('login_history');
CALL reset_ai_if_exists('personal_access_tokens');
CALL reset_ai_if_exists('activity_logs');
CALL reset_ai_if_exists('roles');
CALL reset_ai_if_exists('permissions');

-- Actual project tables
CALL reset_ai_if_exists('DEPARTMENT');
CALL reset_ai_if_exists('STAFF');
CALL reset_ai_if_exists('DOCTOR');
CALL reset_ai_if_exists('NURSE');
CALL reset_ai_if_exists('PATIENT');
CALL reset_ai_if_exists('ROOM');
CALL reset_ai_if_exists('APPOINTMENT');
CALL reset_ai_if_exists('ADMISSION');
CALL reset_ai_if_exists('BILLING');
CALL reset_ai_if_exists('PRESCRIPTION');
CALL reset_ai_if_exists('MEDICINE');
CALL reset_ai_if_exists('PRESCRIPTION_DETAILS');
CALL reset_ai_if_exists('USERS');

-- STEP 5: Re-enable FK checks
SET FOREIGN_KEY_CHECKS = 1;

-- STEP 6: Verify everything is empty (0 rows expected)
CALL count_if_exists('users');
CALL count_if_exists('sessions');
CALL count_if_exists('login_history');
CALL count_if_exists('personal_access_tokens');
CALL count_if_exists('activity_logs');
CALL count_if_exists('ADMISSION');
CALL count_if_exists('APPOINTMENT');
CALL count_if_exists('BILLING');
CALL count_if_exists('DEPARTMENT');
CALL count_if_exists('DOCTOR');
CALL count_if_exists('MEDICINE');
CALL count_if_exists('NURSE');
CALL count_if_exists('PATIENT');
CALL count_if_exists('PRESCRIPTION');
CALL count_if_exists('PRESCRIPTION_DETAILS');
CALL count_if_exists('ROOM');
CALL count_if_exists('STAFF');
CALL count_if_exists('USERS');

-- Cleanup helper procedures
DROP PROCEDURE IF EXISTS truncate_if_exists;
DROP PROCEDURE IF EXISTS reset_ai_if_exists;
DROP PROCEDURE IF EXISTS count_if_exists;
