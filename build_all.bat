@echo off
echo ========================================
echo P4V AI Assistant - Full Build
echo ========================================

cd /d "%~dp0"

echo.
echo [1/3] Syncing version...
echo ----------------------------------------
call venv\Scripts\python build\sync_version.py

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: Version sync failed!
    pause
    exit /b 1
)

echo.
echo [2/3] Building executable...
echo ----------------------------------------
call venv\Scripts\pip install -r requirements.txt -q
call venv\Scripts\pyinstaller --clean build\p4v_ai_assistant.spec

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ERROR: PyInstaller build failed!
    pause
    exit /b 1
)

echo.
echo [3/3] Building installer...
echo ----------------------------------------
"C:\Program Files (x86)\NSIS\makensis.exe" installer\installer.nsi

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Build complete!
    echo EXE: dist\p4v_ai_assistant.exe
    echo Installer: dist\P4V-AI-Assistant-Setup.exe
    echo ========================================
) else (
    echo.
    echo ERROR: NSIS installer build failed!
)

pause
