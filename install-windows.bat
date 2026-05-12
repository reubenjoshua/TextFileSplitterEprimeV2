@echo off
REM Installation script for Splitter on IIS
REM Run this in Command Prompt on your Windows Server

echo ========================================
echo Splitter Application Setup
echo ========================================
echo.

REM Try to find Python
echo [1/5] Looking for Python installation...
echo.

set PYTHON_EXE=

REM Check if python is in PATH
python --version >nul 2>&1
if %errorlevel% equ 0 (
    set PYTHON_EXE=python
    echo Found Python in PATH
    python --version
    goto :found_python
)

REM Check common installation locations
if exist "C:\Python311\python.exe" (
    set PYTHON_EXE=C:\Python311\python.exe
    echo Found Python at C:\Python311\python.exe
    goto :found_python
)

if exist "C:\Python312\python.exe" (
    set PYTHON_EXE=C:\Python312\python.exe
    echo Found Python at C:\Python312\python.exe
    goto :found_python
)

if exist "C:\Program Files\Python311\python.exe" (
    set PYTHON_EXE=C:\Program Files\Python311\python.exe
    echo Found Python at C:\Program Files\Python311\python.exe
    goto :found_python
)

if exist "C:\Program Files\Python312\python.exe" (
    set PYTHON_EXE=C:\Program Files\Python312\python.exe
    echo Found Python at C:\Program Files\Python312\python.exe
    goto :found_python
)

REM Python not found
echo.
echo ERROR: Python not found!
echo.
echo Please install Python from https://www.python.org/downloads/
echo Make sure to check "Add Python to PATH" during installation
echo.
pause
exit /b 1

:found_python
echo.
echo Python found: %PYTHON_EXE%
%PYTHON_EXE% --version
echo.

REM Update web.config with Python path
echo [2/5] Updating web.config with Python path...
echo Python path will be set to: %PYTHON_EXE%
echo (You may need to manually verify web.config)
echo.

REM Install Python dependencies
echo [3/5] Installing Python dependencies...
cd PythonProject2
%PYTHON_EXE% -m pip install --upgrade pip
%PYTHON_EXE% -m pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to install Python dependencies
    echo.
    pause
    exit /b 1
)

echo.
echo Dependencies installed successfully!
cd ..

REM Create necessary directories
echo.
echo [4/5] Creating necessary directories...
if not exist "logs" mkdir logs
if not exist "PythonProject2\uploads" mkdir PythonProject2\uploads
echo Directories created.

REM Set permissions (requires admin)
echo.
echo [5/5] Setting permissions...
icacls . /grant "IIS_IUSRS:(OI)(CI)F" /T >nul 2>&1
if %errorlevel% equ 0 (
    echo Permissions set successfully
) else (
    echo Warning: Could not set permissions automatically
    echo You may need to run this script as Administrator
    echo Or manually grant IIS_IUSRS full control to this folder
)

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Python location: %PYTHON_EXE%
echo.
echo Next steps:
echo 1. Open web.config and verify Python path is: %PYTHON_EXE%
echo 2. Open IIS Manager
echo 3. Create Application Pool (SplitterAppPool, No Managed Code)
echo 4. Create Website pointing to this folder
echo 5. Test: http://localhost/api/health
echo.
echo For detailed instructions, see DEPLOYMENT_GUIDE.md
echo.
pause

