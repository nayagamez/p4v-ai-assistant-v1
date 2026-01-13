@echo off
echo ========================================
echo P4V AI Assistant - Build
echo ========================================

cd /d "%~dp0"

echo Installing dependencies...
call venv\Scripts\pip install -r requirements.txt -q

echo.
echo Running PyInstaller build...
call venv\Scripts\python build\build.py

echo.
echo ========================================
echo Build complete!
echo Output: dist\p4v_ai_assistant.exe
echo ========================================
pause
