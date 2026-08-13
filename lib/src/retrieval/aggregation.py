# src/retrieval/aggregation.py
from src.chunking.sentence_splitter import split_sentences

MAX_PALABRAS_FRAGMENTO = 250


def aggregate_documents(hits: list[dict], top_docs: int = 3) -> list[dict]:
    """Agrega chunks a nivel de documento por max pooling (Sección 8.6 del
    spec): la relevancia de un documento es la de su mejor chunk. Devuelve
    los `top_docs` documentos con mayor score, con su rank."""
    mejor_por_doc: dict[str, dict] = {}
    for h in hits:
        doc_id = h["doc_id"]
        if doc_id not in mejor_por_doc or h["score"] > mejor_por_doc[doc_id]["score"]:
            mejor_por_doc[doc_id] = h

    ranked = sorted(mejor_por_doc.values(), key=lambda h: -h["score"])[:top_docs]
    return [{"rank": i + 1, "doc_id": h["doc_id"]} for i, h in enumerate(ranked)]


def _contar_palabras(texto: str) -> int:
    return len(texto.split())


def _dividir_fragmento(texto: str, idioma: str = "es") -> list[str]:
    """Divide un fragmento que supera las 250 palabras en sub-fragmentos
    que respeten el límite, cortando únicamente en límites de oración
    completa (Sección 9.2.1 del spec: requisito de completitud lingüística
    también aplica aquí)."""
    if _contar_palabras(texto) <= MAX_PALABRAS_FRAGMENTO:
        return [texto]

    oraciones = split_sentences(texto, idioma)
    partes: list[str] = []
    actual: list[str] = []
    actual_palabras = 0

    for oracion in oraciones:
        n = _contar_palabras(oracion)
        if n > MAX_PALABRAS_FRAGMENTO:
            # oracion individual gigante (caso raro, texto sin puntuacion
            # real): corte de emergencia por palabras, ultimo recurso.
            if actual:
                partes.append(" ".join(actual))
                actual, actual_palabras = [], 0
            palabras = oracion.split()
            for i in range(0, len(palabras), MAX_PALABRAS_FRAGMENTO):
                partes.append(" ".join(palabras[i:i + MAX_PALABRAS_FRAGMENTO]))
            continue
        if actual and actual_palabras + n > MAX_PALABRAS_FRAGMENTO:
            partes.append(" ".join(actual))
            actual, actual_palabras = [], 0
        actual.append(oracion)
        actual_palabras += n

    if actual:
        partes.append(" ".join(actual))
    return partes


def build_fragments(hits: list[dict], top_fragments: int = 10) -> list[dict]:
    """Construye la lista de fragmentos de salida (Sección 9.2/9.3 del
    spec): recorre los chunks recuperados en orden de relevancia, divide
    los que superen las 250 palabras en sub-fragmentos (cada uno con su
    propio rank, pero el mismo chunk_id de origen para trazabilidad), y
    devuelve exactamente `top_fragments` entradas."""
    fragmentos: list[dict] = []
    for h in hits:
        piezas = _dividir_fragmento(h["texto"], h.get("idioma", "es"))
        for pieza in piezas:
            fragmentos.append({
                "chunk_id": h["chunk_id"],
                "doc_id": h["doc_id"],
                "text": pieza,
            })
        if len(fragmentos) >= top_fragments:
            break

    fragmentos = fragmentos[:top_fragments]
    for i, f in enumerate(fragmentos):
        f["rank"] = i + 1
    return fragmentos
