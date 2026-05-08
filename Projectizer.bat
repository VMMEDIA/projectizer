@echo off
REM Projectizer.bat — Windows native-window launcher.
REM Right-click → "Create shortcut" → drag the shortcut to Desktop or Start Menu.

cd /d "%~dp0"

if not exist ".venv\" (
    echo.
    echo Installing Projectizer dependencies, this may take 3-5 minutes...
    echo.
    python -m venv .venv || goto :error
    .venv\Scripts\python -m pip install --upgrade pip --quiet
    .venv\Scripts\pip install -r requirements.txt || goto :error
    echo.
    echo Setup complete.
    echo.
)

REM pythonw.exe = no console window. Use python.exe if you want to see logs.
start "" ".venv\Scripts\pythonw.exe" launcher.py
exit /b 0

:error
echo.
echo Setup failed. Make sure Python 3.10+ is installed and on PATH:
echo   https://www.python.org/downloads/
echo.
pause
exit /b 1
