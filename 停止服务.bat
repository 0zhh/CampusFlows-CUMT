@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo Stopping backend and frontend (MySQL container is kept running)...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0stop-all.ps1"
echo.
pause
