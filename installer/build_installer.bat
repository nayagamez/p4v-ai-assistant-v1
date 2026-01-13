@echo off
echo ========================================
echo P4V AI Assistant - Installer Build
echo ========================================

cd /d "%~dp0"

echo.
echo Checking prerequisites...

if not exist "..\dist\p4v_ai_assistant.exe" (
    echo ERROR: p4v_ai_assistant.exe not found!
    echo Please run build.bat first.
    pause
    exit /b 1
)

echo.
echo Building NSIS installer...
"C:\Program Files (x86)\NSIS\makensis.exe" installer.nsi

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Build complete!
    echo Output: dist\P4V-AI-Assistant-Setup.exe
    echo ========================================
) else (
    echo.
    echo ========================================
    echo Build FAILED!
    echo ========================================
)

pause
