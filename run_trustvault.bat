@echo off
title TrustVault - Secure Document Management Platform
color 0B
cls
echo ==============================================================================
echo                      TRUSTVAULT SECURE PLATFORM
echo             Enterprise Role-Based Access Control Document Vault
echo ==============================================================================
echo.
echo [*] Checking Python environment...
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [!] Python is not found on your system PATH!
    echo     Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
)

echo [*] Initializing database & demo users...
python backend\seed_demo.py

echo.
echo [*] Starting TrustVault Server at http://127.0.0.1:5000 ...
echo [*] Opening your default browser...
start http://127.0.0.1:5000

echo.
echo ==============================================================================
echo TrustVault is now actively running! Press Ctrl+C in this window to stop.
echo ==============================================================================
python run.py

pause
