@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
 echo Run start.bat once to install dependencies, then close the server before training.
 pause
 exit /b 1
)
.venv\Scripts\python.exe train.py
pause
