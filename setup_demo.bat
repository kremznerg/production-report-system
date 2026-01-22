@echo off
REM Quick setup script for Production Report System demo
REM This script initializes everything needed for the demo

echo.
echo ========================================
echo Production Report System - Quick Setup
echo ========================================
echo.

echo [1/4] Creating data directory...
if not exist data mkdir data
echo       Done!

echo.
echo [2/4] Initializing database...
python scripts\init_db.py
if errorlevel 1 (
    echo ERROR: Database initialization failed!
    pause
    exit /b 1
)

echo.
echo [3/4] Seeding master data...
python scripts\seed_master_data.py
if errorlevel 1 (
    echo ERROR: Master data seeding failed!
    pause
    exit /b 1
)

echo.
echo [4/4] Creating sample Excel files...
python scripts\create_sample_data.py
if errorlevel 1 (
    echo ERROR: Sample data creation failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Setup completed successfully!
echo ========================================
echo.
echo You can now run the ETL pipeline:
echo   python scripts\run_pipeline.py
echo.
echo Or inspect the database:
echo   python scripts\inspect_db.py
echo.
pause
