@echo off
rem Metrix dev launcher - runs backend and frontend together in THIS window.
rem Backend uses uvicorn auto-reload; frontend uses Vite HMR. Press Ctrl+C to stop both.

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

"%PYTHON%" "%ROOT%dev.py" %*
endlocal
