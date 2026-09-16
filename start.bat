@echo off
setlocal enabledelayedexpansion

echo =========================================================
echo Starting QueryCraft AI - Enterprise NLP to SQL Generator
echo =========================================================

REM Detect Python
set PYTHON_EXE=python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
        set PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe
    ) else if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" (
        set PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python310\python.exe
    ) else if exist "C:\Python311\python.exe" (
        set PYTHON_EXE=C:\Python311\python.exe
    ) else if exist "C:\Python310\python.exe" (
        set PYTHON_EXE=C:\Python310\python.exe
    ) else (
        echo [ERROR] Python not found. Please install Python 3.10+ and add it to PATH.
        pause
        exit /b 1
    )
)

echo [Found Python] Using: "%PYTHON_EXE%"

echo.
echo [1/3] Setting up Backend...
cd backend
"!PYTHON_EXE!" -m pip install -r requirements.txt
echo Initializing database seed...
"!PYTHON_EXE!" -m app.db.seed

echo.
echo [2/3] Setting up Frontend...
cd ..\frontend
if not exist node_modules (
    echo Installing frontend dependencies...
    call npm install
)

echo.
echo [3/3] Launching Development Servers...
echo Starting Backend API at http://localhost:8000 (Swagger: http://localhost:8000/docs)
start "QueryCraft Backend" cmd /k "cd ..\backend && ""!PYTHON_EXE!"" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

echo Starting Frontend UI at http://localhost:5173
start "QueryCraft Frontend" cmd /k "npm run dev"

echo.
echo =========================================================
echo Servers successfully launched!
echo Open http://localhost:5173 in your browser.
echo =========================================================
pause
