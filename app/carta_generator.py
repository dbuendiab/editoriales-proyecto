"""
Generador de párrafos personalizados para cartas de presentación
"""
import anthropic
from config import CLAUDE_MODEL, CLAUDE_MAX_TOKENS


class CartaGenerator:
    def __init__(self, api_key):
        self.client = anthropic.Anthropic(api_key=api_key)
    
    def generar_parrafo(self, editorial_data, manuscrito_data, analisis_ia, notas_usuario=''):
        """
        Genera un párrafo personalizado para la carta de presentación
        
        Args:
            editorial_data: Dict con datos de la editorial
            manuscrito_data: Dict con descripción y archivos del manuscrito
            analisis_ia: Texto del análisis IA previo de esta editorial
            notas_usuario: Notas personales del usuario sobre esta editorial
        
        Returns:
            str: Párrafo generado
        """
        try:
            prompt = self._construir_prompt(editorial_data, manuscrito_data, analisis_ia, notas_usuario)
            
            response = self.client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=1000,  # Párrafo corto
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            print(f"Error generando párrafo: {e}")
            return None
    
    def refinar_parrafo(self, parrafo_anterior, instrucciones_usuario, editorial_data, manuscrito_data, analisis_ia, notas_usuario=''):
        """
        Refina un párrafo existente según las instrucciones del usuario
        
        Args:
            parrafo_anterior: El párrafo generado previamente
            instrucciones_usuario: Feedback/instrucciones del usuario
            editorial_data: Dict con datos de la editorial
            manuscrito_data: Dict con descripción del manuscrito
            analisis_ia: Texto del análisis IA previo
            notas_usuario: Notas personales sobre esta editorial
        
        Returns:
            str: Párrafo refinado
        """
        try:
            prompt = self._construir_prompt_refinamiento(
                parrafo_anterior, 
                instrucciones_usuario,
                editorial_data, 
                manuscrito_data, 
                analisis_ia, 
                notas_usuario
            )
            
            response = self.client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=1000,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            print(f"Error refinando párrafo: {e}")
            return None
    
    def _construir_prompt_refinamiento(self, parrafo_anterior, instrucciones_usuario, editorial_data, manuscrito_data, analisis_ia, notas_usuario=''):
        """Construye el prompt para refinar el párrafo"""
        
        nombre = editorial_data.get('nombre', 'la editorial')
        manuscrito_desc = manuscrito_data.get('descripcion', 'novela contemporánea')
        analisis_snippet = analisis_ia[:800] if analisis_ia else "Editorial adecuada"
        
        notas_section = ""
        if notas_usuario and notas_usuario.strip():
            notas_section = f"""
Notas del autor sobre {nombre}:
{notas_usuario}
"""
        
        prompt = f"""Eres un experto en redacción de cartas de presentación editoriales.

Generaste este párrafo previamente:

"{parrafo_anterior}"

El autor solicita los siguientes ajustes:

"{instrucciones_usuario}"

CONTEXTO ORIGINAL:

Editorial: {nombre}

Descripción del manuscrito (va ANTES del párrafo en la carta):
"{manuscrito_desc}"

Análisis de la editorial:
{analisis_snippet}
{notas_section}

INSTRUCCIONES PARA EL REFINAMIENTO:

1. Aplica los cambios solicitados por el autor
2. Si el autor corrige información (ej: "El autor X SÍ publica aquí"), acéptalo como correcto y úsalo
3. Si pide más corto/largo, ajusta la longitud apropiadamente
4. Si pide cambio de tono, ajústalo
5. Mantén el objetivo: explicar POR QUÉ enviar a esta editorial específicamente
6. El párrafo debe conectar naturalmente tras la descripción del manuscrito
7. NO repitas información de la descripción del manuscrito
8. Longitud objetivo: 50-70 palabras (pero ajusta si el autor lo pide)

REGLAS:
- Las correcciones del usuario son siempre correctas
- Si menciona autores/colecciones, úsalos con confianza
- Mantén tono profesional pero cercano
- Genera el párrafo refinado COMPLETO (no expliques los cambios, solo genera el nuevo párrafo)

Genera el párrafo refinado:"""
        
        return prompt
    
    def _construir_prompt(self, editorial_data, manuscrito_data, analisis_ia, notas_usuario=''):
        """Construye el prompt para generar el párrafo"""
        
        nombre = editorial_data.get('nombre', 'la editorial')
        grupo = editorial_data.get('grupo_editorial', '')
        
        # Descripción del manuscrito
        manuscrito_desc = manuscrito_data.get('descripcion', 'novela contemporánea')
        
        # Extracto del análisis IA (razones por las que es buena opción)
        analisis_snippet = analisis_ia[:800] if analisis_ia else "Editorial adecuada para el manuscrito"
        
        # Construir sección de notas si existen
        notas_section = ""
        if notas_usuario and notas_usuario.strip():
            notas_section = f"""
Notas adicionales del autor sobre {nombre}:
{notas_usuario}
"""
        
        prompt = f"""Eres un experto en el panorama editorial español contemporáneo con conocimiento específico de catálogos y colecciones.

Necesitas generar un párrafo de 2-3 líneas (50-70 palabras) para una carta de presentación editorial.

CONTEXTO DE INTEGRACIÓN:

Este párrafo se insertará en una carta donde el autor YA HA PRESENTADO su obra brevemente.
El autor describe su manuscrito así:

"{manuscrito_desc}"

Tu párrafo irá DESPUÉS de esa presentación, por lo que debes:
- Conectar naturalmente (empezar con "Esta obra...", "Mi manuscrito...", "La novela...", etc.)
- NO repetir información ya mencionada en la descripción
- Centrarte en POR QUÉ esta editorial específicamente

INFORMACIÓN SOBRE {nombre}:

Análisis de la editorial:
{analisis_snippet}
{notas_section}
Grupo editorial: {grupo}

INSTRUCCIONES CRÍTICAS:

1. Tu objetivo: Encontrar la CONEXIÓN MÁS ESPECÍFICA Y VERIFICABLE posible
2. Si el autor proporcionó NOTAS sobre esta editorial: Úsalas como información privilegiada (autores, colecciones, detalles del catálogo)
3. PRIORIDAD 1: Si conoces autores que publican en {nombre} y se relacionan con mi manuscrito, MENCIÓNALOS
4. PRIORIDAD 2: Si conoces colecciones específicas de {nombre}, MENCIÓNALAS
5. PRIORIDAD 3: Si conoces el tipo de narrativa que caracteriza su catálogo, DESCRÍBELO
6. NUNCA inventes autores o colecciones - es mejor ser menos específico que mentir
7. Longitud: 50-70 palabras (2-3 líneas)
8. Tono: Profesional, directo, sin florituras

REGLAS ABSOLUTAS:
- Si mencionas un autor: Debes estar 100% seguro de que publica en {nombre} (o aparece en las notas del usuario)
- Si mencionas una colección: Debe existir realmente (o aparecer en las notas del usuario)
- Si dudas: Habla del tipo/estilo de narrativa, no de nombres concretos
- Conecta características CONCRETAS de su catálogo con aspectos ESPECÍFICOS de mi manuscrito
- Las notas del usuario son información verificada: ÚSALAS si están presentes
- NO repitas lo que ya está en la descripción del manuscrito

ESTRUCTURA OBJETIVO (en orden de preferencia):

MEJOR (si estás seguro):
"Esta obra podría encajar en [colección específica] de {nombre}, que ha publicado autores como [X] y [Y] cuyas obras comparten [similitud muy específica con mi manuscrito]. Su [característica concreta del catálogo] conecta con mi propuesta de [aspecto específico de mi obra]."

MUY BUENO (si conoces colecciones):
"Mi manuscrito conecta con la colección [nombre real] de {nombre}, que reúne obras que [característica específica]. La apuesta de {nombre} por [aspecto editorial verificable] hace que considere que mi propuesta podría ser de interés para su catálogo."

BUENO (si conoces el estilo):
"Esta obra podría encajar en {nombre}, editorial que se caracteriza por publicar [tipo muy específico de narrativa] que [característica distintiva]. Mi manuscrito comparte ese enfoque al [aspecto concreto de mi obra]."

EJEMPLOS DE ESPECIFICIDAD:

✗ MAL: "narrativa contemporánea de calidad"
✓ BIEN: "narrativa que explora la identidad a través de estructuras fragmentadas"

✗ MAL: "propuestas experimentales"
✓ BIEN: "obras que combinan realismo y metaficción"

✗ MAL: "exploran la condición humana"
✓ BIEN: "indagan en el choque entre identidad construida y realidad"

Genera el párrafo (recuerda: busca la conexión MÁS ESPECÍFICA posible sin inventar, y que conecte naturalmente tras la descripción del manuscrito):"""
        
        return prompt
