@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ============================================
echo   CampusFlow - starting MySQL + backend + frontend
echo ============================================
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-all.ps1"
echo.
echo Done. Frontend: http://127.0.0.1:5173/
pause
