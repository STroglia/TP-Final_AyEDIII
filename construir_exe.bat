@echo off
chcp 65001 >nul
title TECNOSOL - Generar TECNOSOL.exe
rem ---------------------------------------------------------------
rem  Genera TECNOSOL.exe (en esta misma carpeta): la app completa en un solo archivo,
rem  sin necesidad de tener Python instalado para usarla.
rem  Volver a correrlo cada vez que se cambie el código.
rem ---------------------------------------------------------------
cd /d "%~dp0"

call "scripts\preparar_entorno.bat"
if errorlevel 1 (
  pause
  exit /b 1
)

echo  Instalando PyInstaller (solo la primera vez)...
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q pyinstaller
if errorlevel 1 (
  echo  [ERROR] No se pudo instalar PyInstaller. Verifica la conexion a internet.
  pause
  exit /b 1
)

echo  Generando TECNOSOL.exe. Tarda uno o dos minutos...
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean --onefile --name TECNOSOL ^
  --add-data "%~dp0app\templates;app\templates" ^
  --add-data "%~dp0app\static;app\static" ^
  --distpath "%~dp0." --workpath "%TEMP%\tecnosol_build" --specpath "%TEMP%\tecnosol_build" ^
  run.py
if errorlevel 1 (
  echo  [ERROR] No se pudo generar el ejecutable.
  pause
  exit /b 1
)

echo.
echo  Listo: TECNOSOL.exe
echo  Usa la misma base de datos que iniciar.bat (carpeta instancia).
pause
