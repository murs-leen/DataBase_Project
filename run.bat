@echo off
:: ============================================================
:: HMS – Application Launcher
:: ============================================================
title HMS – Running on http://localhost:5000

echo.
echo  ============================================
echo    HOSPITAL MANAGEMENT SYSTEM
echo    Starting Flask server...
echo    Open: http://localhost:5000
echo    Press Ctrl+C to stop
echo  ============================================
echo.

cd 06_GUI
python app.py

pause
