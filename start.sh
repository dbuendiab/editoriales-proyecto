#!/bin/bash
# Script de inicio rápido para Unix/Mac

echo "🚀 Iniciando servidor de Gestión de Editoriales..."
echo ""

# Verificar que existe el entorno virtual
if [ ! -d "venv" ]; then
    echo "⚠️  Entorno virtual no encontrado."
    echo "   Ejecuta primero: ./install.sh"
    exit 1
fi

# Activar entorno virtual
source venv/bin/activate

# Verificar que existe la BD
if [ ! -f "data/editoriales.db" ]; then
    echo "⚠️  Base de datos no encontrada. Inicializando..."
    python setup.py
    echo ""
fi

# Iniciar servidor
echo "🌐 Iniciando servidor en http://localhost:5000"
echo "   Presiona Ctrl+C para detener"
echo ""

cd app
python server.py
