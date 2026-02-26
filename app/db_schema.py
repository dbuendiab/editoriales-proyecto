"""
Esquema de base de datos para el sistema de gestión de envío de manuscritos
"""

SCHEMA = """
-- Tabla principal de editoriales (datos estáticos)
CREATE TABLE IF NOT EXISTS editoriales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    grupo_editorial TEXT,
    email_principal TEXT,
    url_general TEXT,
    url_manuscritos TEXT,
    requiere_formulario BOOLEAN DEFAULT 0,
    web TEXT,
    contacto_raw TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tabla de seguimiento (datos operativos/modificables)
CREATE TABLE IF NOT EXISTS seguimiento (
    editorial_id INTEGER PRIMARY KEY,
    
    -- Ordenamiento y estado
    bloque TEXT DEFAULT 'D' CHECK(bloque IN ('A', 'B', 'C', 'D')),
    orden INTEGER,
    estado TEXT DEFAULT 'pendiente' CHECK(estado IN ('pendiente', 'en-proceso', 'finalizado')),
    
    -- Análisis IA (puntuaciones 0-10)
    tamaño INTEGER CHECK(tamaño IS NULL OR (tamaño >= 0 AND tamaño <= 10)),
    genero_ajuste INTEGER CHECK(genero_ajuste IS NULL OR (genero_ajuste >= 0 AND genero_ajuste <= 10)),
    prestigio INTEGER CHECK(prestigio IS NULL OR (prestigio >= 0 AND prestigio <= 10)),
    distribucion INTEGER CHECK(distribucion IS NULL OR (distribucion >= 0 AND distribucion <= 10)),
    promocion INTEGER CHECK(promocion IS NULL OR (promocion >= 0 AND promocion <= 10)),
    probabilidad_ajuste INTEGER CHECK(probabilidad_ajuste IS NULL OR (probabilidad_ajuste >= 0 AND probabilidad_ajuste <= 10)),
    prioridad_global REAL,
    
    -- Notas y análisis
    notas TEXT,
    notas_ia TEXT,
    analisis_manual TEXT,
    analisis_ia TEXT,
    
    -- Experiencia de envío
    feedback_editorial TEXT,
    aprendizajes TEXT,
    
    -- Fechas y resultado
    fecha_confeccion DATE,
    fecha_envio DATE,
    fecha_respuesta DATE,
    resultado TEXT CHECK(resultado IN ('aceptada', 'rechazada', NULL)),
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (editorial_id) REFERENCES editoriales(id) ON DELETE CASCADE
);

-- Índices para mejorar rendimiento
CREATE INDEX IF NOT EXISTS idx_editoriales_nombre ON editoriales(nombre);
CREATE INDEX IF NOT EXISTS idx_seguimiento_bloque ON seguimiento(bloque);
CREATE INDEX IF NOT EXISTS idx_seguimiento_orden ON seguimiento(bloque, orden);
CREATE INDEX IF NOT EXISTS idx_seguimiento_estado ON seguimiento(estado);

-- Trigger para actualizar updated_at
CREATE TRIGGER IF NOT EXISTS update_editoriales_timestamp 
AFTER UPDATE ON editoriales
BEGIN
    UPDATE editoriales SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS update_seguimiento_timestamp 
AFTER UPDATE ON seguimiento
BEGIN
    UPDATE seguimiento SET updated_at = CURRENT_TIMESTAMP WHERE editorial_id = NEW.editorial_id;
END;
"""

def create_database(db_path):
    """Crea la base de datos con el esquema definido"""
    import sqlite3
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Ejecutar el esquema
    cursor.executescript(SCHEMA)
    
    conn.commit()
    conn.close()
    
    print(f"✓ Base de datos creada en: {db_path}")

if __name__ == "__main__":
    import sys
    db_path = sys.argv[1] if len(sys.argv) > 1 else "../data/editoriales.db"
    create_database(db_path)
