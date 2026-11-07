@echo off
chcp 65001 >nul
title TECNOSOL Mar del Plata - Tests
cd /d "%~dp0"

call "scripts\preparar_entorno.bat"
if errorlevel 1 (
  pause
  exit /b 1
)

".venv\Scripts\python.exe" -m pytest -v
pause
