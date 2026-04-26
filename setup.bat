@echo off
:: ============================================================
:: HMS – Windows Setup Script
:: Run this ONCE to configure the database and install packages
:: ============================================================
title HMS – Hospital Management System Setup

echo.
echo  ============================================
echo    HOSPITAL MANAGEMENT SYSTEM – SETUP
echo  ============================================
echo.

:: ── Step 1: MySQL Setup ──────────────────────
echo [1/3] Setting up MySQL database...
echo.
set /p MYSQL_USER=Enter MySQL username (default: root): 
if "%MYSQL_USER%"=="" set MYSQL_USER=root

set /p MYSQL_PASS=Enter MySQL password (leave blank if none): 

echo.
echo Running DDL script...
if "%MYSQL_PASS%"=="" (
    mysql -u %MYSQL_USER% < 02_DDL_Schema.sql
) else (
    mysql -u %MYSQL_USER% -p%MYSQL_PASS% < 02_DDL_Schema.sql
)

echo Running Insert data script...
if "%MYSQL_PASS%"=="" (
    mysql -u %MYSQL_USER% hms_db < 03_Insert_Data.sql
) else (
    mysql -u %MYSQL_USER% -p%MYSQL_PASS% hms_db < 03_Insert_Data.sql
)

echo Running Stored programming script...
if "%MYSQL_PASS%"=="" (
    mysql -u %MYSQL_USER% hms_db < 05_Stored_Programming.sql
) else (
    mysql -u %MYSQL_USER% -p%MYSQL_PASS% hms_db < 05_Stored_Programming.sql
)

echo.
echo [OK] Database setup complete.

:: ── Step 2: Update DB config in app.py ───────
echo.
echo [2/3] Updating database credentials in app.py...

:: Use PowerShell to patch the password in app.py
powershell -Command ^
  "(Get-Content '06_GUI\app.py') ^
   -replace '\"password\":.*,', '\"password\":     \"%MYSQL_PASS%\",' ^
   -replace '\"user\":.*,',     '\"user\":     \"%MYSQL_USER%\",' ^
   | Set-Content '06_GUI\app.py'"

echo [OK] Credentials updated.

:: ── Step 3: Install Python packages ──────────
echo.
echo [3/3] Installing Python dependencies...
pip install flask mysql-connector-python
echo [OK] Dependencies installed.

echo.
echo  ============================================
echo    SETUP COMPLETE!
echo    Run: run.bat  to start the application
echo    URL: http://localhost:5000
echo  ============================================
echo.
pause
