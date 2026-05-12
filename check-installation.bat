@echo off
REM Quick check script to verify installation

echo ========================================
echo Checking Splitter Installation
echo ========================================
echo.

REM Check Python
echo [1/4] Checking Python...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Python is in PATH
    python --version
) else (
    echo [WARN] Python not in PATH
    echo Checking common locations...
    
    if exist "C:\Python311\python.exe" (
        echo [OK] Found at C:\Python311\python.exe
        C:\Python311\python.exe --version
    ) else if exist "C:\Python312\python.exe" (
        echo [OK] Found at C:\Python312\python.exe
        C:\Python312\python.exe --version
    ) else (
        echo [ERROR] Python not found!
    )
)

echo.

REM Check requirements.txt
echo [2/4] Checking project files...
if exist "PythonProject2\requirements.txt" (
    echo [OK] requirements.txt found
) else (
    echo [ERROR] requirements.txt not found
)

if exist "PythonProject2\app.py" (
    echo [OK] app.py found
) else (
    echo [ERROR] app.py not found
)

if exist "web.config" (
    echo [OK] web.config found
) else (
    echo [ERROR] web.config not found
)

echo.

REM Check directories
echo [3/4] Checking directories...
if exist "logs" (
    echo [OK] logs directory exists
) else (
    echo [WARN] logs directory missing
)

if exist "PythonProject2\uploads" (
    echo [OK] uploads directory exists
) else (
    echo [WARN] uploads directory missing
)

if exist "PythonProject2\dist" (
    echo [OK] dist directory exists (frontend built)
) else (
    echo [WARN] dist directory missing (frontend not built)
)

echo.

REM Check Python packages
echo [4/4] Checking Python packages...
python -m pip show Flask >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Flask installed
) else (
    echo [ERROR] Flask not installed
)

python -m pip show flask-cors >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Flask-CORS installed
) else (
    echo [ERROR] Flask-CORS not installed
)

echo.
echo ========================================
echo Check Complete
echo ========================================
echo.

REM Check if IIS is installed
sc query w3svc >nul 2>&1
if %errorlevel% equ 0 (
    echo [INFO] IIS is installed and running
) else (
    echo [WARN] IIS may not be installed or running
)

echo.
pause

