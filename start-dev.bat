@echo off
echo Starting Splitter Development Environment...
echo.

echo Starting Backend (Flask)...
start "Backend" cmd /k "cd PythonProject2 && python app.py"

echo Waiting 3 seconds for backend to start...
timeout /t 3 /nobreak >nul

echo Starting Frontend (React)...
start "Frontend" cmd /k "cd splitter && npm start"

echo.
echo Both servers are starting up...
echo Backend: http://localhost:5000
echo Frontend: http://localhost:3000
echo.
echo Press any key to exit this window...
pause >nul
