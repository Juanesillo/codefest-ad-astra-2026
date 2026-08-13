## Fase de Extracción de Texto — Bitácora de decisiones

### Estado general
Se implementaron 7 extractores de texto (uno por formato de entrada) más un
dispatcher que orquesta todo el proceso según el `formato` registrado en
`data/doc_registry.csv`.

### Extractores implementados

| Archivo | Formato | Librería | Notas |
|---|---|---|---|
| `src/extraction/extract_pdf.py` | PDF | `pdfplumber` | Extrae texto por página, preserva orden de lectura |
| `src/extraction/extract_html.py` | HTML | `BeautifulSoup` | Elimina scripts/estilos/nav/footer, usa h1-h4/p/li como señales estructurales |
| `src/extraction/extract_json.py` | JSON | `json` (stdlib) | Ver sección "Formatos JSON detectados" abajo |
| `src/extraction/extract_tabular.py` | CSV/XLSX | `pandas` | Cada fila → texto tipo "columna: valor", una fila = una unidad de fragmentación |
| `src/extraction/extract_image_ocr.py` | PNG/JPG | `pytesseract` + `Pillow` | OCR multilingüe (spa+eng+por), devuelve vacío si falla en vez de romper el pipeline |
| `src/extraction/extract_pbf.py` | PBF (OpenStreetMap) | `osmium` | Recorre nodos/ways/relaciones, deduplica por (tipo, id) |
| `src/extraction/extract_mvt.py` | PBF (Vector Tiles) | `mapbox-vector-tile` | Ver sección "Problema: dos tipos de PBF" abajo |

### Dispatcher (`src/extraction/dispatcher.py`)
- Lee `data/doc_registry.csv`, aplica el extractor correspondiente por `doc_id`.
- Usa `tqdm` para barra de progreso (necesario, el OCR es lento y sin esto
  no se sabe si el proceso sigue vivo).
- Guarda cada resultado en `data/processed/{doc_id}.txt`.
- Los errores (extractor faltante, texto vacío, excepciones) se registran en
  `data/extraction_errors.csv` en vez de detener el proceso completo.
- Existe `scripts/reprocesar_errores.py` para reintentar solo los `doc_id`
  que fallaron, sin repetir todo el corpus.

### Problema resuelto: dos tipos de archivo `.pbf` en el corpus
El corpus contiene dos formatos distintos bajo la misma extensión `.pbf`:

1. **OSM-PBF real** (formato OpenStreetMap estándar) → `extract_pbf.py` con `osmium`.
2. **Mapbox Vector Tiles** servidos como tiles `{z}/{x}/{y}.pbf` (ej.
   `Amazon_Underworld/tiles/4/5/AMAZONUW_7.pbf`) → `extract_mvt.py`, formato
   de contenedor distinto, `osmium` no puede leerlos (error `invalid
   BlobHeader size`).

**Solución**: `dispatcher.py` usa `elegir_extractor_pbf(path)`, que decide
según si la ruta contiene `/tiles/` en su estructura de carpetas.

**Pendiente de decisión de equipo**: los tilesets de mapas generan muchos
archivos redundantes por nivel de zoom del mismo elemento geográfico. Falta
decidir si se procesan todos los niveles de zoom o solo uno representativo,
tal como sugiere la especificación del reto (Sección 2.1, PBF).

### Problema resuelto: JSON con estructuras heterogéneas
Se detectaron (al menos) dos formatos de JSON distintos en el corpus:

1. **Artículo simple** (ej. fuentes tipo Atlantic Council): campos directos
   `title`, `body_paragraphs`, `body_text`. Extracción directa concatenando
   esos campos.
2. **Reporte scrapeado de landing page** (ej. SWF Counterspace):
   estructura anidada `metadata` + `content.sections`, donde muchas
   secciones son en realidad menú de navegación del sitio (`About`,
   `Reports`, `Events`...) con muy pocos caracteres, y solo 1-2 secciones
   tienen contenido real y sustancial.

**Solución en `extract_json.py`**: detección automática del formato según
las keys presentes; para el formato 2, se filtran secciones por longitud
mínima (umbral configurable, actualmente 200 caracteres) para descartar
boilerplate de navegación.

### Hallazgo importante, aún en investigación: archivos duplicados por "documento lógico"
Se descubrió que al menos una carpeta del corpus (`SWF_Counterspace/
swf_counterspace_2026/`) contiene el mismo contenido representado en
múltiples archivos:

- `SWF_report-data.json` — landing page scrapeada, mayormente boilerplate
- `SWF_full-text.txt` — texto completo, aparentemente ya extraído del PDF
  original del reporte, más completo que el JSON
- `SWF_report-data.csv` — posibles datos tabulares estructurados
- `images/` — imágenes del reporte

**Pendiente de decisión de equipo (bloqueante antes de seguir con esta
carpeta y cualquier otra con el mismo patrón)**:
1. Confirmar si este patrón (json + txt + csv agrupados) se repite en más
   carpetas del corpus — revisar con un script sobre `data/inventory.csv`.
2. Decidir si cada archivo es un `doc_id` separado (según la definición
   literal del PDF: "un documento = un archivo"), o si se tratan como un
   solo documento lógico con el `.txt` como cuerpo principal y el `.json`
   como fuente de metadata adicional (`countries_covered`,
   `counterspace_categories`).
3. Si se tratan por separado, evaluar si el `.json` (mayormente navbar)
   debería excluirse de la indexación por aportar ruido más que señal.

### Checklist de estado actual
- [x] 7 extractores implementados y probados individualmente
- [x] Dispatcher con manejo de errores y barra de progreso
- [x] Corrida completa sobre el corpus (con algunos errores documentados)
- [x] Error de PBF (vector tiles) diagnosticado y resuelto
- [ ] Error de JSON (SWF Counterspace) — extractor ajustado, pendiente de
      confirmar si aplica usar `.txt` en vez del `.json` para este caso
- [ ] Decisión de equipo sobre documentos duplicados en múltiples formatos
- [ ] Limpieza y normalización (`clean_all.py`) — pendiente de correr sobre
      el corpus ya extraído
- [ ] Revisión manual de 5-10 archivos `.txt` extraídos