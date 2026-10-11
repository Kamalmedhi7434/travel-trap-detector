@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo First run: creating an isolated Python environment...
  py -3 -m venv .venv
  if errorlevel 1 goto error
)
if not exist ".venv\travel-ready.txt" (
  echo Installing dependencies. Internet is needed for this first setup only.
  .venv\Scripts\python.exe -m pip install -r requirements.txt
  if errorlevel 1 goto error
  echo installed > .venv\travel-ready.txt
)
echo Open http://127.0.0.1:5000 in your browser. Keep this window open.
.venv\Scripts\python.exe app.py
pause
exit /b
:error
echo Setup failed. Install 64-bit Python 3.10-3.13 and check your internet connection for the first install.
pause
exit /b 1
