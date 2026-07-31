import json


# Campos típicos donde puede venir el cuerpo del texto.
# Ajusten esta lista según lo que realmente traigan los JSON de ADL.
CAMPOS_TEXTO = ["title", "body_text", "body_paragraphs", "content", "text", "summary"]
CAMPOS_METADATA = ["url", "date", "authors", "tags", "source"]


def _extraer_valor_texto(valor) -> str:
    """Convierte listas de párrafos o strings sueltos en un solo texto."""
    if isinstance(valor, list):
        return "\n".join(str(v) for v in valor if v)
    if isinstance(valor, str):
        return valor
    return ""


def extract_json(path: str) -> str:
    """
    Extrae el texto de un archivo JSON, concatenando los campos de
    contenido en orden y dejando de lado los campos puramente
    descriptivos (url, fecha, autores, etc.).
    """
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        data = json.load(f)

    # Si el JSON es una lista de artículos, procesar cada uno y concatenar
    if isinstance(data, list):
        partes = []
        for item in data:
            partes.append(_extraer_de_objeto(item))
        return "\n\n".join(p for p in partes if p)

    return _extraer_de_objeto(data)


def _extraer_de_objeto(obj: dict) -> str:
    if not isinstance(obj, dict):
        return str(obj)

    partes = []
    for campo in CAMPOS_TEXTO:
        if campo in obj:
            valor = _extraer_valor_texto(obj[campo])
            if valor:
                partes.append(valor)

    return "\n\n".join(partes)