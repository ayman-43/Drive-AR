@echo off
echo.
echo  Writing-Driven AutoResearch — Dashboard
echo  ========================================
echo.

REM Kill any process already using port 5500
for /f "tokens=5" %%a in ('netstat -aon ^| find ":5500"') do (
    taskkill /PID %%a /F >nul 2>&1
)

echo  Starting server at http://localhost:5500
echo  Opening dashboard in your browser...
echo.
echo  Press Ctrl+C to stop the server.
echo.

REM Start server in background and open browser
start "" "http://localhost:5500"
python -m http.server 5500 --directory dashboard
