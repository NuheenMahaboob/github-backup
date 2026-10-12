@echo off
echo Installing dependencies...
pip install -r requirements.txt
echo.
echo Starting GitHub Backup...
py main.py
pause
