#!/usr/bin/env python3
"""
Script de inicialización del proyecto
Crea la base de datos y carga los datos del documento Word
"""

import os
import sys

# Añadir el directorio app al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from db_schema import create_database
from parser import populate_database

def init_project():
    """Inicializa el proyecto completo"""
    
    print("=" * 60)
    print("🚀 INICIALIZACIÓN DEL PROYECTO")
    print("=" * 60)
    
    # Paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, 'data', 'editoriales.db')
    docx_path = os.path.join(base_dir, 'data', 'editoriales01.docx')
    
    # Verificar que existe el Word
    if not os.path.exists(docx_path):
        print(f"❌ ERROR: No se encuentra el archivo {docx_path}")
        print("   Por favor, coloca el archivo editoriales01.docx en el directorio 'data/'")
        return False
    
    # Eliminar base de datos existente si existe
    if os.path.exists(db_path):
        print(f"⚠️  La base de datos ya existe en: {db_path}")
        respuesta = input("   ¿Deseas recrearla? (s/N): ")
        if respuesta.lower() != 's':
            print("   Operación cancelada")
            return False
        os.remove(db_path)
        print("   ✓ Base de datos anterior eliminada")
    
    # Paso 1: Crear base de datos
    print("\n📦 Paso 1: Creando base de datos...")
    try:
        create_database(db_path)
    except Exception as e:
        print(f"❌ ERROR creando base de datos: {e}")
        return False
    
    # Paso 2: Poblar con datos del Word
    print("\n📖 Paso 2: Cargando datos del documento Word...")
    try:
        count = populate_database(db_path, docx_path)
        if count == 0:
            print("⚠️  No se cargaron editoriales. Verifica el documento.")
            return False
    except Exception as e:
        print(f"❌ ERROR cargando datos: {e}")
        return False
    
    # Éxito
    print("\n" + "=" * 60)
    print("✅ INICIALIZACIÓN COMPLETADA")
    print("=" * 60)
    print(f"\n📂 Base de datos: {db_path}")
    print(f"📊 Editoriales cargadas: {count}")
    print("\n🚀 Para iniciar el servidor:")
    print("   cd app")
    print("   python server.py")
    print("\n🌐 Luego abre tu navegador en: http://localhost:5000")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = init_project()
    sys.exit(0 if success else 1)
