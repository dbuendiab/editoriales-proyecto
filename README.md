# Sistema de Gestión de Envíos Editoriales

Sistema web local para gestionar el envío de manuscritos a editoriales con análisis IA personalizado y generación automática de contenido.

Desarrollado por **Diego Buendía** para la gestión de envíos de *La miseria como placebo*.

## Características

- Importación de editoriales desde un documento Word con formato estructurado
- Análisis IA de cada editorial en 6 dimensiones (tamaño, género, prestigio, distribución, promoción, probabilidad de aceptación)
- Asignación automática a bloques de prioridad (A/B/C/D)
- Generación de párrafos personalizados para cartas de presentación
- Refinamiento iterativo de los párrafos con feedback
- Seguimiento completo: fechas de envío y respuesta, estados y resultados
- Creación manual de nuevas editoriales con análisis IA opcional
- Interfaz web de página única (SPA), sin dependencias de frontend

## Requisitos

- Python 3.10 o superior
- API Key de [Anthropic](https://console.anthropic.com/) (Claude)

## Instalación

```bash
# 1. Clona el repositorio
git clone https://github.com/tu-usuario/editoriales-proyecto.git
cd editoriales-proyecto

# 2. Prepara tu documento de editoriales
#    El repo incluye data/editoriales.docx con 10 editoriales de ejemplo.
#    Edítalo o sustitúyelo con tus propias editoriales antes de continuar.
#    (ver sección "Formato del documento" más abajo)

# 3. Copia el archivo de configuración y añade tu API key
cp .env.example .env
# Edita .env y rellena ANTHROPIC_API_KEY

# 4. Ejecuta el instalador
./install.sh        # Linux / Mac
install.bat         # Windows

# El instalador crea el entorno virtual, instala dependencias
# e importa las editoriales del documento a la base de datos.
```

## Uso

```bash
./start.sh      # Linux / Mac
start.bat       # Windows
```

Abre http://localhost:5000 en tu navegador.

### Primer arranque

1. Ve a **⚙️ Configuración** e introduce tu API Key de Anthropic
2. Escribe la descripción de tu manuscrito (título, género, temática)
3. Pulsa **Analizar Todas** para puntuar todas las editoriales con IA
4. Pulsa **Asignar Bloques** para distribuirlas en A/B/C/D según prioridad

### Flujo de trabajo habitual

1. Filtra por **Bloque A** (mayor prioridad)
2. Abre el detalle de una editorial (👁️)
3. Genera un párrafo personalizado para la carta (✏️ Generar Párrafo)
4. Refina el párrafo con instrucciones adicionales si lo necesitas
5. Envía el manuscrito
6. Edita la editorial para registrar la fecha de envío y cambiar el estado
7. Cuando llegue respuesta, registra la fecha de respuesta y el resultado

## Formato del documento de editoriales

El archivo `data/editoriales.docx` incluye 10 editoriales ficticias que ilustran el formato esperado. Edítalo o sustitúyelo con tus propias editoriales **antes de ejecutar el instalador** (`setup.py`). El instalador busca exactamente ese nombre — si tu documento tiene otro nombre, renómbralo a `editoriales.docx`.

Cada editorial ocupa un bloque de texto separado por al menos dos líneas en blanco, con estas etiquetas:

```
Editorial: Nombre de la Editorial (Grupo Editorial Opcional)
Contacto: email@editorial.com https://www.editorial.com https://www.editorial.com/envios (envío de manuscritos)
Web: https://www.editorial.com
```

Notas sobre el campo `Contacto`:
- El email se detecta automáticamente por su formato
- La URL marcada con `(envío de manuscritos)` se guarda como URL específica de envíos
- Si el proceso requiere rellenar un formulario web, añade `(rellenar formulario)`

## Bloques de prioridad

| Bloque | Prioridad global | Significado |
|--------|-----------------|-------------|
| A | ≥ 7.0 | Envío inmediato — alta compatibilidad |
| B | 5.0 – 6.99 | Segunda ronda — compatibilidad media |
| C | 3.0 – 4.99 | Reserva — compatibilidad baja |
| D | < 3.0 | Descartada |

## Stack tecnológico

| Capa | Tecnología |
|------|-----------|
| Backend | Python 3.10+, Flask 3.0 |
| Base de datos | SQLite (portable, sin servidor) |
| IA | Anthropic Claude API |
| Frontend | HTML, CSS y JavaScript vanilla |

## Backup

La base de datos no se versiona en git. Haz copias manuales del archivo `data/editoriales.db` cuando quieras conservar un estado concreto.

```bash
cp data/editoriales.db data/editoriales.db.bak-$(date +%Y%m%d)
```

## Licencia

MIT License — consulta el archivo [LICENSE](LICENSE) para más detalles.
