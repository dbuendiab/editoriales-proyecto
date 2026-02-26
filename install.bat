@echo off
REM Script de instalacion con entorno virtual para Windows

echo Instalacion del proyecto con entorno virtual
echo ================================================
echo.

REM Verificar que Python esta instalado
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python no esta instalado
    echo Instala Python desde https://www.python.org/
    pause
    exit /b 1
)

REM Crear entorno virtual si no existe
if not exist "venv" (
    echo Creando entorno virtual...
    python -m venv venv
    echo Entorno virtual creado
) else (
    echo Entorno virtual ya existe
)

REM Activar entorno virtual
echo.
echo Activando entorno virtual...
call venv\Scripts\activate.bat

REM Instalar dependencias
echo.
echo Instalando dependencias...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ================================================
echo Instalacion completada
echo ================================================
echo.
echo Para activar el entorno virtual en el futuro:
echo    venv\Scripts\activate.bat
echo.
echo Para iniciar el servidor:
echo    start.bat
echo.
pause
