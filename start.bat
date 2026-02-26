@echo off
REM Script de inicio rapido para Windows

echo Iniciando servidor de Gestion de Editoriales...
echo.

REM Verificar que existe el entorno virtual
if not exist "venv" (
    echo Entorno virtual no encontrado.
    echo Ejecuta primero: install.bat
    pause
    exit /b 1
)

REM Activar entorno virtual
call venv\Scripts\activate.bat

REM Verificar que existe la BD
if not exist "data\editoriales.db" (
    echo Base de datos no encontrada. Inicializando...
    python setup.py
    echo.
)

REM Iniciar servidor
echo Iniciando servidor en http://localhost:5000
echo Presiona Ctrl+C para detener
echo.

cd app
python server.py
