@echo off
REM ===================================================
REM  One-click setup + run for Laptop Camera Stream
REM  Right-click this file -> Run as administrator
REM  (admin is needed only for the hotspot feature)
REM ===================================================

echo Installing dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

echo.
echo Starting camera stream server...
echo.
python app.py

pause
