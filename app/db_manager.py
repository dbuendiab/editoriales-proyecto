"""
Gestor de base de datos - Operaciones CRUD
"""

import sqlite3
from typing import List, Dict, Optional
from datetime import datetime


class DatabaseManager:
    """Gestor de operaciones sobre la base de datos"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
    
    def _get_connection(self):
        """Obtiene una conexión a la base de datos"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Para acceder por nombre de columna
        return conn
    
    def get_all_editoriales(self, bloque: Optional[str] = None) -> List[Dict]:
        """
        Obtiene todas las editoriales con su información de seguimiento
        
        Args:
            bloque: Filtrar por bloque (A/B/C/D) o None para todas
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        query = """
            SELECT 
                e.*,
                s.bloque, s.orden, s.estado,
                s.tamaño, s.genero_ajuste, s.prestigio,
                s.distribucion, s.promocion, s.probabilidad_ajuste,
                s.prioridad_global,
                s.notas, s.analisis_manual, s.analisis_ia,
                s.fecha_envio, s.fecha_respuesta, s.resultado
            FROM editoriales e
            LEFT JOIN seguimiento s ON e.id = s.editorial_id
        """
        
        if bloque:
            query += " WHERE s.bloque = ?"
            query += " ORDER BY COALESCE(s.orden, 999999), e.nombre"
            cursor.execute(query, (bloque,))
        else:
            query += " ORDER BY COALESCE(s.orden, 999999), e.nombre"
            cursor.execute(query)
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_editorial_by_id(self, editorial_id: int) -> Optional[Dict]:
        """Obtiene una editorial por su ID"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                e.*,
                s.*
            FROM editoriales e
            LEFT JOIN seguimiento s ON e.id = s.editorial_id
            WHERE e.id = ?
        """, (editorial_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def update_seguimiento(self, editorial_id: int, data: Dict) -> bool:
        """
        Actualiza campos de seguimiento de una editorial
        
        Args:
            editorial_id: ID de la editorial
            data: Dict con campos a actualizar
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Construir query dinámicamente según campos presentes
        fields = []
        values = []
        
        allowed_fields = [
            'bloque', 'orden', 'estado',
            'tamaño', 'genero_ajuste', 'prestigio', 'distribucion', 
            'promocion', 'probabilidad_ajuste', 'prioridad_global',
            'notas', 'notas_ia', 'analisis_manual', 'analisis_ia',
            'feedback_editorial', 'aprendizajes',
            'fecha_confeccion', 'fecha_envio', 'fecha_respuesta', 'resultado'
        ]
        
        for field in allowed_fields:
            if field in data:
                fields.append(f"{field} = ?")
                values.append(data[field])
        
        if not fields:
            conn.close()
            return False
        
        values.append(editorial_id)
        
        query = f"UPDATE seguimiento SET {', '.join(fields)} WHERE editorial_id = ?"
        
        try:
            cursor.execute(query, values)
            conn.commit()
            success = cursor.rowcount > 0
        except Exception as e:
            print(f"Error actualizando seguimiento: {e}")
            success = False
        finally:
            conn.close()
        
        return success
    
    def get_editoriales_by_bloque(self, bloque: str, order_by: str = 'orden') -> List[Dict]:
        """
        Obtiene editoriales de un bloque específico, ordenadas
        
        Args:
            bloque: A, B, C, o D
            order_by: Campo por el que ordenar (orden, prioridad_global, nombre)
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        valid_order_fields = {
            'orden': 's.orden',
            'prioridad': 's.prioridad_global DESC',
            'nombre': 'e.nombre'
        }
        
        order_clause = valid_order_fields.get(order_by, 's.orden')
        
        cursor.execute(f"""
            SELECT 
                e.id, e.nombre, e.grupo_editorial, e.web,
                s.bloque, s.orden, s.estado, s.prioridad_global,
                s.fecha_envio, s.resultado
            FROM editoriales e
            LEFT JOIN seguimiento s ON e.id = s.editorial_id
            WHERE s.bloque = ?
            ORDER BY {order_clause}
        """, (bloque,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def cambiar_bloque(self, editorial_id: int, nuevo_bloque: str) -> bool:
        """Cambia una editorial de bloque"""
        if nuevo_bloque not in ['A', 'B', 'C', 'D']:
            return False
        
        return self.update_seguimiento(editorial_id, {'bloque': nuevo_bloque})
    
    def normalizar_orden_bloque(self, bloque: str, inicio: int = 100, incremento: int = 100) -> int:
        """
        Normaliza el orden de un bloque (100, 200, 300, ...)
        
        Returns:
            Número de editoriales renumeradas
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Obtener editoriales del bloque ordenadas por orden actual
        cursor.execute("""
            SELECT editorial_id FROM seguimiento
            WHERE bloque = ?
            ORDER BY COALESCE(orden, 999999), editorial_id
        """, (bloque,))
        
        editoriales = cursor.fetchall()
        
        # Renumerar
        for idx, row in enumerate(editoriales):
            nuevo_orden = inicio + (idx * incremento)
            cursor.execute("""
                UPDATE seguimiento 
                SET orden = ?
                WHERE editorial_id = ?
            """, (nuevo_orden, row['editorial_id']))
        
        conn.commit()
        count = len(editoriales)
        conn.close()
        
        return count
    
    def crear_editorial(self, data: Dict) -> Optional[int]:
        """
        Crea una nueva editorial con su registro de seguimiento
        
        Args:
            data: Dict con campos obligatorios: nombre, web
                  Campos opcionales: grupo_editorial, email_principal, etc.
        
        Returns:
            ID de la nueva editorial o None si falla
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # 1. Insertar en tabla editoriales
            cursor.execute("""
                INSERT INTO editoriales (
                    nombre, web, grupo_editorial, email_principal,
                    url_general, url_manuscritos, requiere_formulario
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get('nombre', ''),
                data.get('web', ''),
                data.get('grupo_editorial', 'Independiente'),
                data.get('email_principal', ''),
                data.get('url_general', data.get('web', '')),
                data.get('url_manuscritos', ''),
                data.get('requiere_formulario', 0)
            ))
            
            editorial_id = cursor.lastrowid
            
            # 2. Crear registro en seguimiento con valores por defecto
            cursor.execute("""
                INSERT INTO seguimiento (
                    editorial_id, bloque, orden, estado
                )
                VALUES (?, 'D', 9999, 'pendiente')
            """, (editorial_id,))
            
            conn.commit()
            print(f"✓ Editorial creada con ID: {editorial_id}")
            return editorial_id
            
        except Exception as e:
            print(f"Error creando editorial: {e}")
            conn.rollback()
            return None
        finally:
            conn.close()
    
    def get_stats(self) -> Dict:
        """Obtiene estadísticas generales"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        stats = {}
        
        # Total de editoriales
        cursor.execute("SELECT COUNT(*) as total FROM editoriales")
        stats['total'] = cursor.fetchone()['total']
        
        # Por bloque
        cursor.execute("""
            SELECT bloque, COUNT(*) as count 
            FROM seguimiento 
            GROUP BY bloque
        """)
        stats['por_bloque'] = {row['bloque']: row['count'] for row in cursor.fetchall()}
        
        # Por estado
        cursor.execute("""
            SELECT estado, COUNT(*) as count 
            FROM seguimiento 
            GROUP BY estado
        """)
        stats['por_estado'] = {row['estado']: row['count'] for row in cursor.fetchall()}
        
        # Con análisis IA
        cursor.execute("""
            SELECT COUNT(*) as count 
            FROM seguimiento 
            WHERE analisis_ia IS NOT NULL
        """)
        stats['con_analisis_ia'] = cursor.fetchone()['count']
        
        conn.close()
        return stats


if __name__ == "__main__":
    # Ejemplo de uso
    db = DatabaseManager("../data/editoriales.db")
    
    print("Estadísticas:")
    stats = db.get_stats()
    print(f"  Total: {stats['total']}")
    print(f"  Por bloque: {stats['por_bloque']}")
    print(f"  Por estado: {stats['por_estado']}")
