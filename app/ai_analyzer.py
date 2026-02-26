"""
Analizador de editoriales usando Claude API - VERSIÓN CONSERVADORA
No inventa autores ni colecciones que no puede verificar
"""

import json
import re
from typing import Dict, Optional
import anthropic
from config import ANTHROPIC_API_KEY, CLAUDE_MODEL, CLAUDE_MAX_TOKENS


class AIAnalyzer:
    """Cliente para analizar editoriales usando Claude"""
    
    def __init__(self, api_key: str = None):
        """
        Inicializa el analizador
        
        Args:
            api_key: API key de Anthropic (usa config.ANTHROPIC_API_KEY si no se proporciona)
        """
        self.api_key = api_key or ANTHROPIC_API_KEY
        if not self.api_key:
            raise ValueError("API key de Anthropic no configurada")
        
        self.client = anthropic.Anthropic(api_key=self.api_key)
    
    def analizar_editorial(self, editorial_data: Dict, manuscrito_data: Dict = None) -> Optional[Dict]:
        """
        Analiza una editorial y genera puntuaciones
        
        Args:
            editorial_data: Dict con datos de la editorial (nombre, web, grupo, etc)
            manuscrito_data: Dict con descripción y archivos del manuscrito del usuario
        
        Returns:
            Dict con scores y análisis, o None si falla
        """
        try:
            # Construir prompt con datos del manuscrito
            prompt = self._construir_prompt(editorial_data, manuscrito_data)
            
            # Llamar a Claude API
            response = self.client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=CLAUDE_MAX_TOKENS,
                temperature=0.3,  # Más conservador que antes
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            # Extraer contenido
            content = response.content[0].text
            
            # Parsear respuesta JSON
            scores = self._parsear_respuesta(content)
            
            # Calcular prioridad global
            if scores:
                scores['prioridad_global'] = self._calcular_prioridad(scores)
            
            return scores
            
        except Exception as e:
            print(f"Error analizando editorial {editorial_data.get('nombre', 'desconocida')}: {e}")
            return None
    
    def _construir_prompt(self, editorial_data: Dict, manuscrito_data: Dict = None) -> str:
        """Construye el prompt conservador para el análisis"""
        
        nombre = editorial_data.get('nombre', 'Desconocida')
        web = editorial_data.get('web', '')
        grupo = editorial_data.get('grupo_editorial', 'Independiente')
        
        # Construir descripción del manuscrito
        manuscrito_texto = ""
        
        if manuscrito_data:
            # Descripción principal
            if manuscrito_data.get('descripcion'):
                manuscrito_texto += manuscrito_data['descripcion']
            
            # Texto de sinopsis si existe
            if manuscrito_data.get('sinopsis'):
                manuscrito_texto += "\n\nSINOPSIS/PRESENTACIÓN:\n" + manuscrito_data['sinopsis']
            
            # Texto de muestra si existe
            if manuscrito_data.get('muestra'):
                # Limitar muestra a primeros 2000 caracteres para no saturar
                muestra = manuscrito_data['muestra'][:2000]
                manuscrito_texto += "\n\nMUESTRA DE ESCRITURA:\n" + muestra + "\n[...]"
        
        if not manuscrito_texto:
            manuscrito_texto = "novela literaria contemporánea en español"
        
        prompt = f"""Analiza la compatibilidad entre esta editorial española y el manuscrito descrito.

**EDITORIAL A EVALUAR:**
Nombre: {nombre}
Web: {web}
Grupo: {grupo}

**MANUSCRITO DEL AUTOR:**
{manuscrito_texto}

---

**INSTRUCCIONES CRÍTICAS:**

1. **NO INVENTES AUTORES NI COLECCIONES** que no puedas verificar con certeza absoluta.
   - Si no estás 100% seguro de que un autor publica en esta editorial, NO lo menciones.
   - Si no conoces con certeza sus colecciones actuales, NO las nombres.
   - Es mejor ser genérico y preciso que específico y erróneo.

2. **SÍ puedes afirmar con seguridad:**
   - Tamaño y perfil general de la editorial (grande/mediana/pequeña/microeditorial)
   - Prestigio y reconocimiento en el sector (si es conocida)
   - Tipo de distribución aproximada (nacional/internacional/limitada)
   - Líneas editoriales generales (literaria/comercial/académica/experimental)
   - Probabilidad de aceptación para autores noveles (abierta/selectiva/muy selectiva)

3. **Tono del análisis:**
   - Profesional, analítico, sincero
   - Si dudas, reconócelo: "Parece que...", "Probablemente...", "Sin información detallada..."
   - Mejor decir "desconozco su catálogo actual" que inventar un autor

4. **Prioriza ANÁLISIS sobre DATOS:**
   - No necesito que me digas QUÉ autores publican
   - Necesito que me digas QUÉ TIPO de narrativa publican
   - No necesito nombres de colecciones
   - Necesito entender su LÍNEA EDITORIAL

---

**PUNTUACIONES REQUERIDAS (0-10):**

Evalúa los siguientes criterios:

1. **TAMAÑO (0-10)**: Tamaño de la editorial
   - 10 = Gran grupo editorial multinacional (Planeta, PRH, etc.)
   - 5 = Editorial mediana con varios títulos al año
   - 0 = Microeditorial o muy pequeña

2. **GÉNERO_AJUSTE (0-10)**: Ajuste del manuscrito con su línea editorial
   - 10 = Publican activamente este tipo de obra, línea perfectamente alineada
   - 5 = Publican el género pero no es su especialidad principal
   - 0 = No publican este tipo de obra
   IMPORTANTE: Evalúa específicamente para el manuscrito descrito, no de forma genérica

3. **PRESTIGIO (0-10)**: Reconocimiento y prestigio en el sector literario español
   - 10 = Editorial muy prestigiosa, premios importantes, autores reconocidos
   - 5 = Reconocida en círculos literarios
   - 0 = Desconocida o sin prestigio notable

4. **DISTRIBUCIÓN (0-10)**: Amplitud de distribución de sus libros
   - 10 = Distribución nacional amplia + internacional consolidada
   - 5 = Distribución nacional limitada o regional
   - 0 = Solo venta online o distribución muy limitada

5. **PROMOCIÓN (0-10)**: Inversión en marketing y promoción de autores
   - 10 = Gran presupuesto promocional, presencia mediática fuerte
   - 5 = Promoción moderada, redes sociales activas
   - 0 = Sin promoción o muy limitada

6. **PROBABILIDAD (0-10)**: Probabilidad de aceptar manuscrito no solicitado de autor novel
   - 10 = Muy abiertos a nuevos autores, responden activamente
   - 5 = Aceptan pero muy selectivos
   - 0 = Prácticamente cerrados a manuscritos no solicitados

---

**FORMATO DE RESPUESTA:**

Responde ÚNICAMENTE con un objeto JSON en este formato exacto (sin markdown, sin explicaciones adicionales):

{{
  "tamaño": X,
  "genero_ajuste": X,
  "prestigio": X,
  "distribucion": X,
  "promocion": X,
  "probabilidad": X,
  "razonamiento": "Explicación breve de 2-3 líneas sobre las puntuaciones específicas para este manuscrito. NO menciones autores concretos a menos que estés 100% seguro.",
  "analisis_texto": "Análisis de 3-4 párrafos (200-300 palabras) que evalúe:
    - Párrafo 1: Perfil de la editorial (tamaño, prestigio, distribución) - SIN nombres de autores
    - Párrafo 2: Línea editorial y tipo de narrativa que publican - EN TÉRMINOS GENERALES
    - Párrafo 3: Compatibilidad con este manuscrito específico - POR QUÉ sí o no encaja
    - Párrafo 4: Valoración final y recomendación estratégica
    Si desconoces información específica, indícalo con naturalidad."
}}

**RECUERDA:** Es mejor un análisis genérico pero preciso que uno específico pero falso. No inventes autores."""
        
        return prompt
    
    def _parsear_respuesta(self, content: str) -> Optional[Dict]:
        """Parsea la respuesta JSON de Claude"""
        try:
            # Limpiar markdown si existe
            content_clean = re.sub(r'```json\s*|\s*```', '', content).strip()
            
            # Parsear JSON
            data = json.loads(content_clean)
            
            # Validar campos requeridos
            required_fields = ['tamaño', 'genero_ajuste', 'prestigio', 
                             'distribucion', 'promocion', 'probabilidad',
                             'razonamiento', 'analisis_texto']
            
            for field in required_fields:
                if field not in data:
                    print(f"⚠️  Campo requerido '{field}' no encontrado en respuesta")
                    return None
            
            # Validar rangos (0-10) - solo campos numéricos
            numeric_fields = ['tamaño', 'genero_ajuste', 'prestigio', 
                            'distribucion', 'promocion', 'probabilidad']
            
            for field in numeric_fields:
                if not (0 <= data[field] <= 10):
                    print(f"⚠️  Campo '{field}' fuera de rango: {data[field]}")
                    return None
            
            # Mapear campos al esquema de BD
            # razonamiento -> notas_ia (texto breve)
            # analisis_texto -> analisis_ia (texto largo)
            # probabilidad -> probabilidad_ajuste (para compatibilidad BD)
            return {
                'tamaño': data['tamaño'],
                'genero_ajuste': data['genero_ajuste'],
                'prestigio': data['prestigio'],
                'distribucion': data['distribucion'],
                'promocion': data['promocion'],
                'probabilidad_ajuste': data['probabilidad'],  # Renombrar a probabilidad_ajuste
                'notas_ia': data['razonamiento'],
                'analisis_ia': data['analisis_texto']
            }
            
        except json.JSONDecodeError as e:
            print(f"Error parseando JSON: {e}")
            print(f"Contenido recibido: {content[:200]}...")
            return None
        except Exception as e:
            print(f"Error inesperado parseando respuesta: {e}")
            return None
    
    def _calcular_prioridad(self, scores: Dict) -> float:
        """
        Calcula la prioridad global basada en las puntuaciones
        
        Fórmula ponderada:
        - género_ajuste: 30% (lo más importante)
        - tamaño: 25% (grandes primero por tiempos)
        - distribución: 15%
        - promoción: 10%
        - prestigio: 10%
        - probabilidad: 10%
        """
        prioridad = (
            scores['genero_ajuste'] * 0.30 +
            scores['tamaño'] * 0.25 +
            scores['distribucion'] * 0.15 +
            scores['promocion'] * 0.10 +
            scores['prestigio'] * 0.10 +
            scores['probabilidad_ajuste'] * 0.10
        )
        
        return round(prioridad, 2)


# Función auxiliar para pruebas
if __name__ == "__main__":
    # Ejemplo de uso
    analyzer = AIAnalyzer()
    
    test_editorial = {
        'nombre': 'Periférica',
        'web': 'www.editorialperiferica.com',
        'grupo_editorial': 'Independiente'
    }
    
    test_manuscrito = {
        'descripcion': """Novela existencial de 132.000 palabras que explora el choque entre identidad 
y realidad. Articula dos relatos entrelazados: David Rubiños, un indigente que 
gana la lotería y ensaya identidades en distintos países; y Joaquín Esteban, 
el periodista que intenta convertir esa historia en novela. Narrativa densa, 
reflexiva, con ambición formal."""
    }
    
    print(f"Analizando: {test_editorial['nombre']}...")
    result = analyzer.analizar_editorial(test_editorial, test_manuscrito)
    
    if result:
        print("\n✓ Análisis completado:")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("\n✗ Análisis falló")
