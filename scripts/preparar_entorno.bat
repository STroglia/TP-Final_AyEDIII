@echo off
rem ---------------------------------------------------------------
rem  Prepara el entorno de Python (.venv) con las dependencias.
rem  Lo usan iniciar.bat y correr_tests.bat. No hace falta abrirlo.
rem ---------------------------------------------------------------
cd /d "%~dp0.."

rem 1) Si el entorno ya existe y funciona, no hay nada que hacer.
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" -c "import flask, sqlalchemy, pytest" >nul 2>&1
  if not errorlevel 1 exit /b 0
  echo  El entorno de Python no funciona en esta computadora. Se va a volver a crear...
  rmdir /s /q ".venv"
)

rem 2) Buscar Python: lanzador "py", "python" en el PATH o carpetas de instalacion habituales.
set "PY="
py -3 --version >nul 2>&1 && set "PY=py -3"
if not defined PY python --version >nul 2>&1 && set "PY=python"
if not defined PY for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*" "%ProgramFiles%\Python3*") do (
  if exist "%%~D\python.exe" set "PY="%%~D\python.exe""
)
if not defined PY (
  echo.
  echo  [ERROR] No se encontro Python en esta computadora.
  echo  Instalalo desde https://www.python.org/downloads/
  echo  y marca la opcion "Add python.exe to PATH" durante la instalacion.
  echo.
  exit /b 1
)

rem 3) Crear el entorno e instalar las dependencias.
echo  Preparando el entorno por primera vez. Puede tardar un par de minutos...
%PY% -m venv .venv
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q -r requirements.txt
if errorlevel 1 (
  echo  [ERROR] No se pudieron instalar las dependencias. Verifica la conexion a internet.
  exit /b 1
)
echo  Entorno listo.
exit /b 0
