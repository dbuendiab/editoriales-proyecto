#!/bin/bash
# Script de instalación con entorno virtual para Unix/Mac

echo "📦 Instalación del proyecto con entorno virtual"
echo "================================================"
echo ""

# Verificar que Python3 está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: Python 3 no está instalado"
    echo "   Instala Python 3 desde https://www.python.org/"
    exit 1
fi

# Crear entorno virtual si no existe
if [ ! -d "venv" ]; then
    echo "🔧 Creando entorno virtual..."
    python3 -m venv venv
    echo "✓ Entorno virtual creado"
else
    echo "✓ Entorno virtual ya existe"
fi

# Activar entorno virtual
echo ""
echo "🔌 Activando entorno virtual..."
source venv/bin/activate

# Instalar dependencias
echo ""
echo "📚 Instalando dependencias..."
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "================================================"
echo "✅ Instalación completada"
echo "================================================"
echo ""
echo "Para activar el entorno virtual en el futuro:"
echo "   source venv/bin/activate"
echo ""
echo "Para iniciar el servidor:"
echo "   ./start.sh"
echo ""
