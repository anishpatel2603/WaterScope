@echo off
title WATERSCOPE - Dev Environment
echo ==================================================================
echo   Starting WATERSCOPE Full-Stack Development Environment
echo ==================================================================
echo.

:: Check python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not found in PATH. Please ensure Python is installed.
    pause
    exit /b 1
)

:: 1. Launch FastAPI Backend in a new window
echo [1/2] Launching Python FastAPI Backend on http://127.0.0.1:8000 ...
start "WATERSCOPE Backend (FastAPI :8000)" cmd /k "python -m uvicorn api.app:app --host 127.0.0.1 --port 8000 --reload"

:: 2. Launch Vite Frontend in current window
echo [2/2] Launching Vite Frontend on http://localhost:5173 ...
cd frontend
npm run dev
