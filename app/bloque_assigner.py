"""
Módulo para asignación automática de bloques basada en análisis IA
"""

def asignar_bloque_automatico(puntuaciones):
    """
    Asigna un bloque (A, B, C, D) basándose en las puntuaciones IA
    
    Args:
        puntuaciones: Dict con las puntuaciones IA de la editorial
        
    Returns:
        str: 'A', 'B', 'C', o 'D'
    """
    if not puntuaciones:
        return 'D'
    
    # Convertir None a 0 para evitar errores con comparaciones
    prioridad = float(puntuaciones.get('prioridad_global') or 0)
    genero = float(puntuaciones.get('genero_ajuste') or 0)
    tamaño = float(puntuaciones.get('tamaño') or 0)
    probabilidad = float(puntuaciones.get('probabilidad') or 0)
    
    # BLOQUE A: Editoriales prioritarias
    # - Muy buen ajuste de género
    # - Alta prioridad global
    # - Tamaño suficiente para dar visibilidad
    if genero >= 8 and prioridad >= 7 and tamaño >= 6:
        return 'A'
    
    # BLOQUE B: Buenas opciones
    # - Buen ajuste de género
    # - Prioridad media-alta
    if genero >= 7 and prioridad >= 5:
        return 'B'
    
    # BLOQUE C: Opciones de backup
    # - Ajuste de género aceptable
    # - Prioridad baja-media
    if genero >= 5 and prioridad >= 3.5:
        return 'C'
    
    # BLOQUE D: Descartadas
    # - Ajuste bajo
    # - No son adecuadas para el manuscrito
    return 'D'


def get_estadisticas_bloques(editoriales):
    """
    Calcula estadísticas de la distribución de bloques
    
    Args:
        editoriales: Lista de editoriales
        
    Returns:
        dict: Estadísticas por bloque
    """
    stats = {
        'A': {'count': 0, 'prioridad_media': 0, 'editoriales': []},
        'B': {'count': 0, 'prioridad_media': 0, 'editoriales': []},
        'C': {'count': 0, 'prioridad_media': 0, 'editoriales': []},
        'D': {'count': 0, 'prioridad_media': 0, 'editoriales': []}
    }
    
    for ed in editoriales:
        bloque = ed.get('bloque', 'D')
        prioridad = ed.get('prioridad_global', 0)
        
        stats[bloque]['count'] += 1
        stats[bloque]['editoriales'].append({
            'nombre': ed.get('nombre'),
            'prioridad': prioridad
        })
    
    # Calcular prioridades medias
    for bloque in stats:
        if stats[bloque]['count'] > 0:
            total_prioridad = sum(e['prioridad'] for e in stats[bloque]['editoriales'])
            stats[bloque]['prioridad_media'] = round(total_prioridad / stats[bloque]['count'], 2)
    
    return stats


def get_explicacion_bloque(bloque):
    """
    Devuelve una explicación del significado de cada bloque
    
    Args:
        bloque: 'A', 'B', 'C', o 'D'
        
    Returns:
        str: Explicación del bloque
    """
    explicaciones = {
        'A': 'Prioridad máxima: Excelente ajuste de género, alta prioridad, buena visibilidad',
        'B': 'Buenas opciones: Buen ajuste, prioridad media-alta',
        'C': 'Opciones de backup: Ajuste aceptable, menor prioridad',
        'D': 'Descartadas: Bajo ajuste o no adecuadas para el manuscrito'
    }
    return explicaciones.get(bloque, 'Sin clasificar')
