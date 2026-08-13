import json


# Campos típicos donde puede venir el cuerpo del texto. Incluye variantes en
# español porque varias fuentes del corpus (RutaN, CEEEP, MAPP OEA, RESDAL...)
# usan nombres de clave en español en vez de inglés.
CAMPOS_TEXTO = [
    "title", "titulo", "título",
    "body_text", "body_paragraphs",
    "content", "contenido",
    "text", "texto",
    "summary", "resumen",
    "description", "descripcion", "descripción",
    "cuerpo",
]
CAMPOS_METADATA = ["url", "date", "authors", "tags", "source"]

# Secciones scrapeadas (ej. content.sections de landing pages) con menos
# caracteres que esto suelen ser menús de navegación ("About", "Reports"...)
# en vez de contenido real, y se descartan.
UMBRAL_SECCION = 200


def _extraer_valor_texto(valor) -> str:
    """Convierte listas de párrafos, dicts de secciones o strings sueltos
    en un solo texto."""
    if isinstance(valor, list):
        partes = [_extraer_valor_texto(v) for v in valor if v]
        return "\n".join(p for p in partes if p)
    if isinstance(valor, dict):
        return _extraer_secciones(valor)
    if isinstance(valor, str):
        return valor
    if isinstance(valor, (int, float, bool)):
        return str(valor)
    return ""


def _extraer_secciones(d: dict) -> str:
    """Extrae texto de un dict de secciones (ej. reportes scrapeados con
    estructura content.sections), descartando entradas muy cortas que
    suelen ser boilerplate de navegación en vez de contenido real."""
    partes = []
    for clave, valor in d.items():
        texto = _extraer_valor_texto(valor).strip()
        if len(texto) >= UMBRAL_SECCION:
            partes.append(f"{clave}\n{texto}")
    return "\n\n".join(partes)


def _flatten_generico(obj, prefijo="") -> str:
    """Último recurso para catálogos/registros (listas de metadatos, mapas
    url->archivo, contadores de scraping...) que no tienen ningún campo de
    contenido reconocido: en vez de devolver texto vacío, aplana el objeto
    en pares 'clave: valor', igual que extract_tabular.py hace con CSV/XLSX.
    """
    partes = []
    if isinstance(obj, dict):
        for clave, valor in obj.items():
            if isinstance(valor, (dict, list)):
                sub = _flatten_generico(valor, f"{prefijo}{clave}.")
                if sub:
                    partes.append(sub)
            elif valor not in (None, "", []):
                partes.append(f"{prefijo}{clave}: {valor}")
    elif isinstance(obj, list):
        for item in obj:
            sub = _flatten_generico(item, prefijo)
            if sub:
                partes.append(sub)
    return "\n".join(partes)


def extract_json(path: str) -> str:
    """
    Extrae el texto de un archivo JSON, concatenando los campos de
    contenido en orden y dejando de lado los campos puramente
    descriptivos (url, fecha, autores, etc.). Si no hay ningún campo de
    contenido reconocible (catálogos, índices, registros de scraping),
    cae de vuelta a un aplanado genérico clave/valor.
    """
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        data = json.load(f)

    if isinstance(data, list):
        partes = [_extraer_de_objeto(item) for item in data]
        texto = "\n\n".join(p for p in partes if p)
    else:
        texto = _extraer_de_objeto(data)

    if texto.strip():
        return texto

    return _flatten_generico(data)


def _extraer_de_objeto(obj) -> str:
    if not isinstance(obj, dict):
        return str(obj) if obj not in (None, "", []) else ""

    partes = []

    metadata = obj.get("metadata")
    if isinstance(metadata, dict):
        titulo = metadata.get("title") or metadata.get("report_title") or metadata.get("page_title")
        if titulo:
            partes.append(str(titulo))

    for campo in CAMPOS_TEXTO:
        if campo in obj:
            valor = _extraer_valor_texto(obj[campo]).strip()
            if valor:
                partes.append(valor)

    return "\n\n".join(partes)
