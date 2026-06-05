#!/bin/bash
set -e

echo ""
echo "========================================"
echo "   Camera Stream - Raspberry Pi Setup"
echo "========================================"
echo ""

# System packages (apt is more reliable than pip for opencv on RPi)
echo "[1/3] Installing system dependencies..."
sudo apt-get update -y -q
sudo apt-get install -y -q python3-pip python3-opencv libatlas-base-dev

# Only Flask is needed from pip since opencv comes from apt above
echo "[2/3] Installing Python packages..."
pip3 install flask==3.0.3 --break-system-packages 2>/dev/null || pip3 install flask==3.0.3

echo "[3/3] Starting camera stream..."
echo ""
python3 app.py
