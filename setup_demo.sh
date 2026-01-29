#!/bin/bash
# Quick setup script for Production Report System demo
# This script initializes everything needed for the demo

echo ""
echo "========================================"
echo "Production Report System - Quick Setup"
echo "========================================"
echo ""

echo "[1/4] Creating data directory..."
mkdir -p data
echo "      Done!"

echo ""
echo "[2/4] Initializing database..."
python3 scripts/init_db.py
if [ $? -ne 0 ]; then
    echo "ERROR: Database initialization failed!"
    exit 1
fi

echo ""
echo "[3/4] Seeding master data..."
python3 scripts/seed_master_data.py
if [ $? -ne 0 ]; then
    echo "ERROR: Master data seeding failed!"
    exit 1
fi

echo ""
echo "[4/5] Creating sample Excel files..."
python3 scripts/create_sample_data.py
if [ $? -ne 0 ]; then
    echo "ERROR: Sample data creation failed!"
    exit 1
fi

echo ""
echo "[5/5] Simulating production events (MES)..."
python3 scripts/simulate_events.py
if [ $? -ne 0 ]; then
    echo "ERROR: Event simulation failed!"
    exit 1
fi

echo ""
echo "========================================"
echo "Setup completed successfully!"
echo "========================================"
echo ""
echo "You can now run the ETL pipeline:"
echo "  python3 scripts/run_pipeline.py"
echo ""
echo "Or inspect the database:"
echo "  python3 scripts/inspect_db.py"
echo ""
