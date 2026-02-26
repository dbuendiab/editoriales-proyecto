"""
Parser para extraer información de editoriales desde el documento Word
"""

import re
import mammoth


def parse_contacto(contacto_raw):
    """
    Parsea el campo contacto y extrae sus componentes
    
    Returns:
        dict con: email_principal, url_general, url_manuscritos, requiere_formulario
    """
    result = {
        'email_principal': None,
        'url_general': None,
        'url_manuscritos': None,
        'requiere_formulario': False
    }
    
    if not contacto_raw:
        return result
    
    # Extraer emails
    emails = re.findall(r'\S+@\S+', contacto_raw)
    if emails:
        result['email_principal'] = emails[0].strip()
    
    # Extraer URLs
    urls = re.findall(r'https?://[^\s]+', contacto_raw)
    
    # Identificar URLs específicas
    for url in urls:
        url_clean = url.strip()
        # Buscar si viene seguida de flag de manuscritos
        if '(envío de manuscritos)' in contacto_raw[contacto_raw.find(url_clean):contacto_raw.find(url_clean)+len(url_clean)+30]:
            result['url_manuscritos'] = url_clean
        elif result['url_general'] is None:
            result['url_general'] = url_clean
    
    # Detectar si requiere formulario
    if '(rellenar formulario)' in contacto_raw.lower():
        result['requiere_formulario'] = True
    
    return result


def parse_word_document(docx_path):
    """
    Parsea el documento Word y extrae todas las editoriales
    
    Returns:
        list de dicts con la información de cada editorial
    """
    # Leer el documento
    with open(docx_path, 'rb') as docx_file:
        result = mammoth.extract_raw_text(docx_file)
        text = result.value
    
    # Dividir por editoriales (separadas por dobles saltos de línea)
    editoriales_raw = re.split(r'\n\n\n+', text.strip())
    
    editoriales = []
    
    for ed_text in editoriales_raw:
        if not ed_text.strip():
            continue
        
        lines = [l.strip() for l in ed_text.strip().split('\n') if l.strip()]
        
        if len(lines) < 2:
            continue
        
        # Extraer información
        editorial = {}
        
        for line in lines:
            if line.startswith('Editorial:'):
                nombre_completo = line.replace('Editorial:', '').strip()
                
                # Separar nombre y grupo editorial
                if '(' in nombre_completo and ')' in nombre_completo:
                    nombre = nombre_completo[:nombre_completo.rfind('(')].strip()
                    grupo = nombre_completo[nombre_completo.rfind('(')+1:nombre_completo.rfind(')')].strip()
                else:
                    nombre = nombre_completo
                    grupo = None
                
                editorial['nombre'] = nombre
                editorial['grupo_editorial'] = grupo
            
            elif line.startswith('Contacto:'):
                contacto_raw = line.replace('Contacto:', '').strip()
                editorial['contacto_raw'] = contacto_raw
                
                # Parsear contacto
                contacto_parsed = parse_contacto(contacto_raw)
                editorial.update(contacto_parsed)
            
            elif line.startswith('Web:'):
                web = line.replace('Web:', '').strip()
                editorial['web'] = web
        
        if 'nombre' in editorial:
            editoriales.append(editorial)
    
    return editoriales


def populate_database(db_path, docx_path):
    """
    Parsea el Word y popula la base de datos
    """
    import sqlite3
    
    # Parsear documento
    print(f"📖 Parseando documento: {docx_path}")
    editoriales = parse_word_document(docx_path)
    print(f"✓ Encontradas {len(editoriales)} editoriales")
    
    # Conectar a BD
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Insertar editoriales
    inserted = 0
    for ed in editoriales:
        try:
            cursor.execute("""
                INSERT INTO editoriales (
                    nombre, grupo_editorial, email_principal, 
                    url_general, url_manuscritos, requiere_formulario,
                    web, contacto_raw
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ed.get('nombre'),
                ed.get('grupo_editorial'),
                ed.get('email_principal'),
                ed.get('url_general'),
                ed.get('url_manuscritos'),
                ed.get('requiere_formulario', False),
                ed.get('web'),
                ed.get('contacto_raw')
            ))
            
            editorial_id = cursor.lastrowid
            
            # Crear entrada en tabla seguimiento
            cursor.execute("""
                INSERT INTO seguimiento (editorial_id, bloque, estado)
                VALUES (?, 'D', 'pendiente')
            """, (editorial_id,))
            
            inserted += 1
            
        except Exception as e:
            print(f"✗ Error insertando {ed.get('nombre', 'desconocida')}: {e}")
    
    conn.commit()
    conn.close()
    
    print(f"✓ Insertadas {inserted} editoriales en la base de datos")
    return inserted


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Uso: python parser.py <db_path> <docx_path>")
        sys.exit(1)
    
    db_path = sys.argv[1]
    docx_path = sys.argv[2]
    
    populate_database(db_path, docx_path)
