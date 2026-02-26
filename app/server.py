"""
Servidor Flask - API REST para gestión de editoriales
"""

from flask import Flask, jsonify, request, render_template, Response
import os
import json
import time
from db_manager import DatabaseManager
from config import verificar_configuracion, ANTHROPIC_API_KEY, CLAUDE_MODEL
from ai_analyzer import AIAnalyzer
from bloque_assigner import asignar_bloque_automatico, get_estadisticas_bloques
from carta_generator import CartaGenerator
import anthropic

app = Flask(__name__, 
            template_folder='../templates',
            static_folder='../static')

# Configuración
DB_PATH = os.path.join(os.path.dirname(__file__), '../data/editoriales.db')
db = DatabaseManager(DB_PATH)

# Verificar configuración al inicio
AI_DISPONIBLE = verificar_configuracion()
if AI_DISPONIBLE:
    try:
        analyzer = AIAnalyzer()
        print("✓ Análisis IA: Disponible")
    except Exception as e:
        print(f"⚠️  Error inicializando analizador IA: {e}")
        AI_DISPONIBLE = False
else:
    analyzer = None
    print("⚠️  Análisis IA: No disponible (configura ANTHROPIC_API_KEY)")



@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')


@app.route('/api/editoriales', methods=['GET'])
def get_editoriales():
    """Obtiene todas las editoriales o filtradas por bloque"""
    bloque = request.args.get('bloque')
    editoriales = db.get_all_editoriales(bloque=bloque)
    return jsonify(editoriales)


@app.route('/api/editoriales/<int:editorial_id>', methods=['GET'])
def get_editorial(editorial_id):
    """Obtiene una editorial específica"""
    editorial = db.get_editorial_by_id(editorial_id)
    if editorial:
        return jsonify(editorial)
    return jsonify({'error': 'Editorial no encontrada'}), 404


@app.route('/api/editoriales', methods=['POST'])
def crear_editorial():
    """
    Crea una nueva editorial y opcionalmente la analiza con IA
    
    Body JSON:
    {
        "nombre": "Editorial Nueva",
        "web": "https://editorial.com",
        "grupo_editorial": "Independiente",
        "email_principal": "contacto@editorial.com",
        "analizar": true,  // opcional, por defecto true
        "api_key": "...",  // requerido si analizar=true
        "manuscrito": {...}  // requerido si analizar=true
    }
    """
    data = request.json
    
    # Validar campos obligatorios
    if not data.get('nombre'):
        return jsonify({'success': False, 'error': 'El nombre es obligatorio'}), 400
    
    # Crear editorial
    editorial_id = db.crear_editorial(data)
    
    if not editorial_id:
        return jsonify({'success': False, 'error': 'Error creando editorial'}), 500
    
    # Por defecto, analizar con IA
    analizar = data.get('analizar', True)
    
    if analizar:
        api_key = data.get('api_key', '')
        manuscrito_data = data.get('manuscrito', {})
        
        if not api_key:
            return jsonify({
                'success': True,
                'editorial_id': editorial_id,
                'warning': 'Editorial creada pero no analizada (falta API key)'
            })
        
        try:
            # Analizar con IA
            temp_analyzer = AIAnalyzer(api_key=api_key)
            editorial = db.get_editorial_by_id(editorial_id)
            
            scores = temp_analyzer.analizar_editorial(editorial, manuscrito_data)
            
            if scores:
                # Guardar análisis
                update_data = {
                    'tamaño': scores['tamaño'],
                    'genero_ajuste': scores['genero_ajuste'],
                    'prestigio': scores['prestigio'],
                    'distribucion': scores['distribucion'],
                    'promocion': scores['promocion'],
                    'probabilidad_ajuste': scores['probabilidad_ajuste'],
                    'prioridad_global': scores['prioridad_global'],
                    'analisis_ia': scores['analisis_ia'],
                    'notas_ia': scores.get('notas_ia', '')
                }
                db.update_seguimiento(editorial_id, update_data)
                
                # Asignar bloque automáticamente según prioridad
                prioridad = scores['prioridad_global']
                if prioridad >= 7.0:
                    nuevo_bloque = 'A'
                elif prioridad >= 5.0:
                    nuevo_bloque = 'B'
                elif prioridad >= 3.0:
                    nuevo_bloque = 'C'
                else:
                    nuevo_bloque = 'D'
                
                db.update_seguimiento(editorial_id, {'bloque': nuevo_bloque})
                
                return jsonify({
                    'success': True,
                    'editorial_id': editorial_id,
                    'prioridad': prioridad,
                    'bloque': nuevo_bloque,
                    'message': f'Editorial creada y analizada (Bloque {nuevo_bloque}, Prioridad {prioridad:.1f})'
                })
            else:
                return jsonify({
                    'success': True,
                    'editorial_id': editorial_id,
                    'warning': 'Editorial creada pero el análisis IA falló'
                })
                
        except Exception as e:
            return jsonify({
                'success': True,
                'editorial_id': editorial_id,
                'warning': f'Editorial creada pero error en análisis: {str(e)}'
            })
    
    # Sin análisis
    return jsonify({
        'success': True,
        'editorial_id': editorial_id,
        'message': 'Editorial creada exitosamente'
    })


@app.route('/api/editoriales/<int:editorial_id>', methods=['PUT'])

def update_editorial(editorial_id):
    """Actualiza información de seguimiento de una editorial"""
    data = request.json
    success = db.update_seguimiento(editorial_id, data)
    if success:
        return jsonify({'success': True, 'message': 'Editorial actualizada'})
    return jsonify({'success': False, 'error': 'Error actualizando'}), 400


@app.route('/api/bloques/<bloque>', methods=['GET'])
def get_bloque(bloque):
    """Obtiene editoriales de un bloque específico"""
    if bloque not in ['A', 'B', 'C', 'D']:
        return jsonify({'error': 'Bloque inválido'}), 400
    
    order_by = request.args.get('order_by', 'orden')
    editoriales = db.get_editoriales_by_bloque(bloque, order_by)
    return jsonify(editoriales)


@app.route('/api/bloques/<bloque>/normalizar', methods=['POST'])
def normalizar_bloque(bloque):
    """Normaliza el orden de un bloque (100, 200, 300...)"""
    if bloque not in ['A', 'B', 'C', 'D']:
        return jsonify({'error': 'Bloque inválido'}), 400
    
    count = db.normalizar_orden_bloque(bloque)
    return jsonify({
        'success': True, 
        'message': f'{count} editoriales renumeradas',
        'count': count
    })


@app.route('/api/editoriales/<int:editorial_id>/cambiar-bloque', methods=['POST'])
def cambiar_bloque(editorial_id):
    """Cambia una editorial de bloque"""
    data = request.json
    nuevo_bloque = data.get('bloque')
    
    if not nuevo_bloque or nuevo_bloque not in ['A', 'B', 'C', 'D']:
        return jsonify({'error': 'Bloque inválido'}), 400
    
    success = db.cambiar_bloque(editorial_id, nuevo_bloque)
    if success:
        return jsonify({'success': True, 'message': f'Movida a bloque {nuevo_bloque}'})
    return jsonify({'success': False, 'error': 'Error cambiando bloque'}), 400


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Obtiene estadísticas generales"""
    stats = db.get_stats()
    return jsonify(stats)


@app.route('/api/ia/disponible', methods=['POST'])
def ia_disponible():
    """Verifica si el análisis IA está disponible con la API key proporcionada"""
    data = request.json or {}
    api_key = data.get('api_key', '')
    
    if not api_key:
        return jsonify({
            'disponible': False,
            'mensaje': 'API key no proporcionada'
        })
    
    try:
        # Intentar crear cliente con la key
        test_analyzer = AIAnalyzer(api_key=api_key)
        return jsonify({
            'disponible': True,
            'mensaje': 'API key válida'
        })
    except Exception as e:
        return jsonify({
            'disponible': False,
            'mensaje': f'API key inválida: {str(e)}'
        })


@app.route('/api/test-api-key', methods=['POST'])
def test_api_key():
    """Prueba una API key haciendo una llamada mínima"""
    data = request.json
    api_key = data.get('api_key', '')
    
    if not api_key:
        return jsonify({
            'success': False,
            'error': 'API key no proporcionada'
        }), 400
    
    try:
        # Crear cliente y hacer llamada de prueba
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        
        # Llamada mínima para verificar
        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=10,
            messages=[{"role": "user", "content": "Hi"}]
        )
        
        return jsonify({
            'success': True,
            'mensaje': 'API key válida y funcional'
        })
        
    except anthropic.AuthenticationError:
        return jsonify({
            'success': False,
            'error': 'API key inválida o sin permisos'
        }), 401
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Error: {str(e)}'
        }), 500


@app.route('/api/analizar/<int:editorial_id>', methods=['POST'])
def analizar_editorial(editorial_id):
    """Analiza una editorial específica con IA"""
    data = request.json or {}
    api_key = data.get('api_key', '')
    manuscrito_data = data.get('manuscrito', {})
    
    if not api_key:
        return jsonify({
            'success': False, 
            'error': 'API key no proporcionada'
        }), 400
    
    try:
        # Obtener datos de la editorial
        editorial = db.get_editorial_by_id(editorial_id)
        if not editorial:
            return jsonify({'success': False, 'error': 'Editorial no encontrada'}), 404
        
        # Analizar con IA usando la API key proporcionada
        print(f"Analizando: {editorial['nombre']}...")
        temp_analyzer = AIAnalyzer(api_key=api_key)
        scores = temp_analyzer.analizar_editorial(editorial, manuscrito_data)
        
        if not scores:
            return jsonify({
                'success': False, 
                'error': 'Error analizando editorial'
            }), 500
        
        # Guardar resultados en BD
        update_data = {
            'tamaño': scores['tamaño'],
            'genero_ajuste': scores['genero_ajuste'],
            'prestigio': scores['prestigio'],
            'distribucion': scores['distribucion'],
            'promocion': scores['promocion'],
            'probabilidad_ajuste': scores['probabilidad_ajuste'],  # YA viene renombrado del parser
            'prioridad_global': scores['prioridad_global'],
            'analisis_ia': scores['analisis_ia'],  # YA viene formateado del parser
            'notas_ia': scores.get('notas_ia', '')  # Añadir notas_ia si existe
        }
        
        success = db.update_seguimiento(editorial_id, update_data)
        
        if success:
            return jsonify({
                'success': True,
                'message': f'Editorial {editorial["nombre"]} analizada correctamente',
                'scores': scores
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Error guardando análisis en base de datos'
            }), 500
            
    except Exception as e:
        print(f"Error en análisis: {e}")
        return jsonify({
            'success': False,
            'error': f'Error inesperado: {str(e)}'
        }), 500


@app.route('/api/analizar-todas', methods=['POST'])
def analizar_todas():
    """
    Analiza todas las editoriales sin análisis IA
    Retorna progreso vía streaming
    """
    data = request.json or {}
    api_key = data.get('api_key', '')
    manuscrito_data = data.get('manuscrito', {})
    
    if not api_key:
        return jsonify({
            'success': False,
            'error': 'API key no proporcionada'
        }), 400
    
    def generar():
        """Generador para streaming"""
        try:
            # Crear analizador con la API key proporcionada
            temp_analyzer = AIAnalyzer(api_key=api_key)
            
            # Obtener editoriales sin análisis
            editoriales = db.get_all_editoriales()
            sin_analisis = [e for e in editoriales if not e.get('analisis_ia')]
            
            total = len(sin_analisis)
            
            if total == 0:
                yield f"data: {json.dumps({'type': 'complete', 'message': 'Todas las editoriales ya están analizadas'})}\n\n"
                return
            
            yield f"data: {json.dumps({'type': 'start', 'total': total})}\n\n"
            
            for idx, editorial in enumerate(sin_analisis, 1):
                # Enviar progreso
                yield f"data: {json.dumps({'type': 'progress', 'current': idx, 'total': total, 'nombre': editorial['nombre']})}\n\n"
                
                # Analizar con datos del manuscrito
                scores = temp_analyzer.analizar_editorial(editorial, manuscrito_data)
                
                if scores:
                    # Guardar
                    update_data = {
                        'tamaño': scores['tamaño'],
                        'genero_ajuste': scores['genero_ajuste'],
                        'prestigio': scores['prestigio'],
                        'distribucion': scores['distribucion'],
                        'promocion': scores['promocion'],
                        'probabilidad_ajuste': scores['probabilidad_ajuste'],  # YA viene renombrado
                        'prioridad_global': scores['prioridad_global'],
                        'analisis_ia': scores['analisis_ia'],  # YA viene formateado
                        'notas_ia': scores.get('notas_ia', '')  # Añadir notas_ia
                    }
                    db.update_seguimiento(editorial['id'], update_data)
                    
                    yield f"data: {json.dumps({'type': 'success', 'nombre': editorial['nombre'], 'prioridad': scores['prioridad_global']})}\n\n"
                else:
                    yield f"data: {json.dumps({'type': 'error', 'nombre': editorial['nombre']})}\n\n"
                
                # Rate limiting (evitar sobrecarga de API)
                time.sleep(1)
            
            yield f"data: {json.dumps({'type': 'complete', 'message': f'{total} editoriales analizadas'})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
    response = Response(generar(), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'
    return response


@app.route('/api/asignar-bloques', methods=['POST'])
def asignar_bloques_automaticamente():
    """
    Asigna bloques automáticamente a todas las editoriales con análisis IA
    """
    try:
        print("\n=== INICIANDO ASIGNACIÓN DE BLOQUES ===")
        editoriales = db.get_all_editoriales()
        print(f"Total editoriales en BD: {len(editoriales)}")
        
        # Filtrar solo las que tienen análisis IA
        con_analisis = [e for e in editoriales if e.get('analisis_ia')]
        print(f"Editoriales con análisis IA: {len(con_analisis)}")
        
        if not con_analisis:
            return jsonify({
                'success': False,
                'error': 'No hay editoriales con análisis IA'
            }), 400
        
        # Asignar bloques
        actualizadas = 0
        errores = []
        
        for editorial in con_analisis:
            try:
                # Preparar puntuaciones
                puntuaciones = {
                    'prioridad_global': editorial.get('prioridad_global', 0),
                    'genero_ajuste': editorial.get('genero_ajuste', 0),
                    'tamaño': editorial.get('tamaño', 0),
                    'probabilidad': editorial.get('probabilidad_ajuste', 0)
                }
                
                print(f"\nEditorial: {editorial['nombre']}")
                print(f"  Puntuaciones: {puntuaciones}")
                
                # Calcular bloque
                bloque = asignar_bloque_automatico(puntuaciones)
                print(f"  Bloque asignado: {bloque}")
                
                # Actualizar en BD
                success = db.update_seguimiento(editorial['id'], {'bloque': bloque})
                if success:
                    actualizadas += 1
                else:
                    errores.append(f"{editorial['nombre']}: Error actualizando BD")
                    
            except Exception as e:
                error_msg = f"{editorial['nombre']}: {str(e)}"
                print(f"  ERROR: {error_msg}")
                errores.append(error_msg)
        
        print(f"\n=== RESUMEN ===")
        print(f"Actualizadas: {actualizadas}/{len(con_analisis)}")
        if errores:
            print(f"Errores: {len(errores)}")
            for err in errores:
                print(f"  - {err}")
        
        # Obtener estadísticas
        editoriales_actualizadas = db.get_all_editoriales()
        stats = get_estadisticas_bloques(editoriales_actualizadas)
        
        print(f"\nEstadísticas por bloque:")
        for bloque in ['A', 'B', 'C', 'D']:
            print(f"  Bloque {bloque}: {stats[bloque]['count']} editoriales (prioridad media: {stats[bloque]['prioridad_media']})")
        
        return jsonify({
            'success': True,
            'message': f'{actualizadas} editoriales reorganizadas',
            'actualizadas': actualizadas,
            'total': len(con_analisis),
            'errores': errores,
            'estadisticas': stats
        })
        
    except Exception as e:
        print(f"\n!!! ERROR GENERAL: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/ordenar-por-prioridad', methods=['POST'])
def ordenar_por_prioridad():
    """
    Ordena las editoriales por prioridad IA (mayor a menor)
    Actualiza el campo 'orden' en seguimiento
    """
    try:
        print("\n=== ORDENANDO POR PRIORIDAD IA ===")
        editoriales = db.get_all_editoriales()
        
        # Filtrar solo las que tienen prioridad_global
        con_prioridad = [e for e in editoriales if e.get('prioridad_global') is not None]
        sin_prioridad = [e for e in editoriales if e.get('prioridad_global') is None]
        
        print(f"Con prioridad: {len(con_prioridad)}")
        print(f"Sin prioridad: {len(sin_prioridad)}")
        
        # Ordenar por prioridad descendente
        con_prioridad_sorted = sorted(con_prioridad, key=lambda x: float(x.get('prioridad_global', 0)), reverse=True)
        
        # Actualizar orden
        actualizadas = 0
        orden = 100  # Empezar en 100 con saltos de 100
        
        # Primero las que tienen prioridad (ordenadas)
        for editorial in con_prioridad_sorted:
            success = db.update_seguimiento(editorial['id'], {'orden': orden})
            if success:
                actualizadas += 1
                print(f"{orden}. {editorial['nombre']} - Prioridad: {editorial.get('prioridad_global')}")
            orden += 100  # Saltos de 100
        
        # Luego las que no tienen prioridad (mantienen orden original)
        for editorial in sin_prioridad:
            success = db.update_seguimiento(editorial['id'], {'orden': orden})
            if success:
                actualizadas += 1
            orden += 100  # Saltos de 100
        
        print(f"\n=== RESUMEN ===")
        print(f"Actualizadas: {actualizadas}/{len(editoriales)}")
        
        return jsonify({
            'success': True,
            'message': f'{len(con_prioridad)} editoriales ordenadas por prioridad',
            'actualizadas': actualizadas,
            'total': len(editoriales)
        })
        
    except Exception as e:
        print(f"\n!!! ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/ordenar-por-probabilidad', methods=['POST'])
def ordenar_por_probabilidad():
    """
    Ordena las editoriales por probabilidad de aceptación (mayor a menor)
    Actualiza el campo 'orden' en seguimiento
    """
    try:
        print("\n=== ORDENANDO POR PROBABILIDAD ===")
        editoriales = db.get_all_editoriales()
        
        # Filtrar solo las que tienen probabilidad_ajuste
        con_probabilidad = [e for e in editoriales if e.get('probabilidad_ajuste') is not None]
        sin_probabilidad = [e for e in editoriales if e.get('probabilidad_ajuste') is None]
        
        print(f"Con probabilidad: {len(con_probabilidad)}")
        print(f"Sin probabilidad: {len(sin_probabilidad)}")
        
        # Ordenar por probabilidad descendente
        con_probabilidad_sorted = sorted(con_probabilidad, key=lambda x: float(x.get('probabilidad_ajuste', 0)), reverse=True)
        
        # Actualizar orden
        actualizadas = 0
        orden = 100  # Empezar en 100 con saltos de 100
        
        # Primero las que tienen probabilidad (ordenadas)
        for editorial in con_probabilidad_sorted:
            success = db.update_seguimiento(editorial['id'], {'orden': orden})
            if success:
                actualizadas += 1
                print(f"{orden}. {editorial['nombre']} - Probabilidad: {editorial.get('probabilidad_ajuste')}")
            orden += 100  # Saltos de 100
        
        # Luego las que no tienen probabilidad (mantienen orden original)
        for editorial in sin_probabilidad:
            success = db.update_seguimiento(editorial['id'], {'orden': orden})
            if success:
                actualizadas += 1
            orden += 100  # Saltos de 100
        
        print(f"\n=== RESUMEN ===")
        print(f"Actualizadas: {actualizadas}/{len(editoriales)}")
        
        return jsonify({
            'success': True,
            'message': f'{len(con_probabilidad)} editoriales ordenadas por probabilidad',
            'actualizadas': actualizadas,
            'total': len(editoriales)
        })
        
    except Exception as e:
        print(f"\n!!! ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/generar-parrafo/<int:editorial_id>', methods=['POST'])
def generar_parrafo_carta(editorial_id):
    """
    Genera un párrafo personalizado para la carta de presentación a una editorial
    """
    data = request.json or {}
    api_key = data.get('api_key', '')
    manuscrito_data = data.get('manuscrito', {})
    
    if not api_key:
        return jsonify({
            'success': False,
            'error': 'API key no proporcionada'
        }), 400
    
    try:
        # Obtener datos de la editorial
        editorial = db.get_editorial_by_id(editorial_id)
        if not editorial:
            return jsonify({'success': False, 'error': 'Editorial no encontrada'}), 404
        
        # Obtener análisis IA previo y notas
        analisis_ia = editorial.get('analisis_ia', '')
        notas = editorial.get('notas', '')
        
        if not analisis_ia:
            return jsonify({
                'success': False,
                'error': 'Esta editorial no tiene análisis IA. Analízala primero.'
            }), 400
        
        # Generar párrafo
        print(f"Generando párrafo para: {editorial['nombre']}...")
        generator = CartaGenerator(api_key=api_key)
        parrafo = generator.generar_parrafo(editorial, manuscrito_data, analisis_ia, notas)
        
        if not parrafo:
            return jsonify({
                'success': False,
                'error': 'Error generando párrafo'
            }), 500
        
        return jsonify({
            'success': True,
            'parrafo': parrafo,
            'editorial': editorial['nombre']
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/refinar-parrafo/<int:editorial_id>', methods=['POST'])
def refinar_parrafo_carta(editorial_id):
    """
    Refina un párrafo existente según instrucciones del usuario
    """
    data = request.json or {}
    api_key = data.get('api_key', '')
    manuscrito_data = data.get('manuscrito', {})
    parrafo_anterior = data.get('parrafo_anterior', '')
    instrucciones = data.get('instrucciones', '')
    
    if not api_key:
        return jsonify({
            'success': False,
            'error': 'API key no proporcionada'
        }), 400
    
    if not parrafo_anterior:
        return jsonify({
            'success': False,
            'error': 'No hay párrafo anterior para refinar'
        }), 400
    
    if not instrucciones or not instrucciones.strip():
        return jsonify({
            'success': False,
            'error': 'Por favor proporciona instrucciones de refinamiento'
        }), 400
    
    try:
        # Obtener datos de la editorial
        editorial = db.get_editorial_by_id(editorial_id)
        if not editorial:
            return jsonify({'success': False, 'error': 'Editorial no encontrada'}), 404
        
        # Obtener análisis IA y notas
        analisis_ia = editorial.get('analisis_ia', '')
        notas = editorial.get('notas', '')
        
        if not analisis_ia:
            return jsonify({
                'success': False,
                'error': 'Esta editorial no tiene análisis IA'
            }), 400
        
        # Refinar párrafo
        print(f"Refinando párrafo para: {editorial['nombre']}...")
        print(f"Instrucciones: {instrucciones}")
        
        generator = CartaGenerator(api_key=api_key)
        parrafo_refinado = generator.refinar_parrafo(
            parrafo_anterior,
            instrucciones,
            editorial, 
            manuscrito_data, 
            analisis_ia, 
            notas
        )
        
        if not parrafo_refinado:
            return jsonify({
                'success': False,
                'error': 'Error refinando párrafo'
            }), 500
        
        return jsonify({
            'success': True,
            'parrafo': parrafo_refinado,
            'editorial': editorial['nombre']
        })
        
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/editoriales/<int:editorial_id>/guardar-parrafo', methods=['POST'])
def guardar_parrafo(editorial_id):
    """
    Guarda el párrafo generado en el campo analisis_manual
    """
    data = request.json or {}
    parrafo = data.get('parrafo', '')
    
    if not parrafo:
        return jsonify({
            'success': False,
            'error': 'No hay párrafo para guardar'
        }), 400
    
    try:
        # Guardar en analisis_manual
        success = db.update_seguimiento(editorial_id, {'analisis_manual': parrafo})
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Párrafo guardado correctamente'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Error guardando el párrafo'
            }), 500
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint no encontrado'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Error interno del servidor'}), 500


if __name__ == '__main__':
    print("=" * 60)
    print("🚀 Servidor Flask iniciado")
    print("=" * 60)
    print(f"📂 Base de datos: {DB_PATH}")
    print(f"🌐 Abre tu navegador en: http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, host='0.0.0.0', port=5000)
