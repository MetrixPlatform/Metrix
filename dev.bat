@echo off
rem Metrix dev launcher - starts backend and frontend for local testing.
rem Backend uses uvicorn auto-reload (METRIX_RELOAD=1); frontend uses Vite HMR.
rem Both reload automatically when you change code. Each runs in its own window.

setlocal
set "ROOT=%~dp0"
set "PYTHON=%ROOT%.venv\Scripts\python.exe"

if not exist "%PYTHON%" (
  echo [ERROR] Python venv not found: "%PYTHON%"
  echo Create it first, e.g.:
  echo   python -m venv .venv
  echo   .venv\Scripts\python -m pip install -r server\requirements.txt
  pause
  exit /b 1
)

echo Starting backend  -^> http://127.0.0.1:8000  (auto-reload)
start "Metrix Backend" cmd /k "cd /d "%ROOT%server" && set METRIX_RELOAD=1 && "%PYTHON%" main.py"

echo Starting frontend -^> http://127.0.0.1:5173  (hot reload)
start "Metrix Frontend" cmd /k "cd /d "%ROOT%web" && (if not exist node_modules npm install) && npm run dev"

echo.
echo Two windows opened. Edit code and it reloads automatically.
echo Close each window (or press Ctrl+C inside it) to stop a service.
endlocal
