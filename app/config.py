"""
Configuración del proyecto
"""

import os
from pathlib import Path

# Cargar variables de entorno desde .env
try:
    from dotenv import load_dotenv
    # Buscar .env en el directorio raíz del proyecto
    env_path = Path(__file__).parent.parent / '.env'
    load_dotenv(dotenv_path=env_path)
except ImportError:
    print("⚠️  python-dotenv no instalado. Usando variables de entorno del sistema.")

# API Key de Anthropic
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY', '')

# Verificar configuración
def verificar_configuracion():
    """Verifica que la configuración está completa"""
    if not ANTHROPIC_API_KEY:
        print("=" * 60)
        print("⚠️  ADVERTENCIA: ANTHROPIC_API_KEY no configurada")
        print("=" * 60)
        print("Para usar el análisis IA, necesitas:")
        print("1. Obtener una API key en: https://console.anthropic.com/")
        print("2. Crear un archivo .env en la raíz del proyecto:")
        print("   ANTHROPIC_API_KEY=sk-ant-tu-key-aqui")
        print("=" * 60)
        return False
    return True

# Configuración del modelo
CLAUDE_MODEL = "claude-sonnet-4-20250514"
CLAUDE_MAX_TOKENS = 2000

if __name__ == "__main__":
    if verificar_configuracion():
        print("✓ Configuración correcta")
        print(f"✓ Modelo: {CLAUDE_MODEL}")
    else:
        print("✗ Configuración incompleta")
