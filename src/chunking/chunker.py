# src/chunking/chunker.py
import json
from pathlib import Path

from transformers import AutoTokenizer

from src.chunking.sentence_splitter import split_sentences

TABULAR_FORMATS = {"csv", "xlsx"}
GEO_FORMATS = {"pbf"}

_TOKENIZER = None


def get_tokenizer():
    global _TOKENIZER
    if _TOKENIZER is None:
        _TOKENIZER = AutoTokenizer.from_pretrained("BAAI/bge-m3")
    return _TOKENIZER


def count_tokens(texto: str) -> int:
    if not texto:
        return 0
    return len(get_tokenizer().encode(texto, add_special_tokens=False))


def count_tokens_batch(textos: list[str]) -> list[int]:
    if not textos:
        return []
    encoded = get_tokenizer()(textos, add_special_tokens=False)
    return [len(ids) for ids in encoded["input_ids"]]


# Estimado empírico (medido sobre una muestra del corpus con el tokenizer de
# bge-m3): ~3.7 caracteres por token en textos es/en/pt mixtos. Se usa solo
# como presupuesto para decidir dónde cortar (barato, sin llamar al
# tokenizer por cada oración); el num_tokens real de cada chunk final se
# mide después con el tokenizer, así que un error en esta estimación no
# afecta la metadata, solo el tamaño exacto del chunk.
CHARS_PER_TOKEN_ESTIMATE = 3.7


def _wrap_oversized(unit: str, max_chars: int) -> list[str]:
    """Corta una unidad (oración/fila) que por sí sola ya excede el
    presupuesto de caracteres. En la práctica esto solo ocurre con texto sin
    puntuación real que el segmentador de oraciones no pudo dividir (listas
    largas de nombres en agradecimientos, bloques OCR degradados, o texto
    corrupto tipo "(cid:123)" de PDFs con fuentes mal decodificadas). Se
    corta por límites de palabra cuando hay espacios; si una "palabra" en sí
    misma sigue excediendo el presupuesto (texto sin espacios en absoluto,
    como el caso "(cid:...)"), se corta directo por caracteres como último
    recurso. La prosa normal nunca pasa por esta rama."""
    max_chars = max(1, int(max_chars))
    if len(unit) <= max_chars:
        return [unit]

    palabras = unit.split(" ")
    if len(palabras) == 1:
        # Sin espacios: no hay forma de cortar por palabra, se corta por
        # caracteres en bloques fijos.
        return [unit[i:i + max_chars] for i in range(0, len(unit), max_chars)]

    piezas: list[str] = []
    actual: list[str] = []
    actual_len = 0
    for palabra in palabras:
        w_len = len(palabra) + 1
        if w_len > max_chars:
            if actual:
                piezas.append(" ".join(actual))
                actual, actual_len = [], 0
            piezas.extend(_wrap_oversized(palabra, max_chars))
            continue
        if actual and actual_len + w_len > max_chars:
            piezas.append(" ".join(actual))
            actual = []
            actual_len = 0
        actual.append(palabra)
        actual_len += w_len
    if actual:
        piezas.append(" ".join(actual))
    return piezas


def _pack_units(units: list[str], joiner: str, max_tokens: int, overlap: int) -> list[str]:
    """Empaqueta unidades (oraciones o filas/bloques) en chunks de hasta
    ~max_tokens (vía presupuesto de caracteres), sin partir ninguna unidad.
    `overlap` = número de unidades finales del chunk anterior que se repiten
    al inicio del siguiente."""
    max_chars = max_tokens * CHARS_PER_TOKEN_ESTIMATE

    # Margen de seguridad extra para el wrap de emergencia: texto anómalo
    # (glitches de extracción con caracteres duplicados, listas de nombres)
    # tokeniza mucho peor que prosa normal (~2 char/token en vez de ~3.7),
    # así que se usa un presupuesto más chico solo para esa rama.
    units_expandidas: list[str] = []
    for u in units:
        units_expandidas.extend(_wrap_oversized(u, max_chars * 0.5))
    units = units_expandidas

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for unit in units:
        u_len = len(unit)
        if current and current_len + u_len > max_chars:
            chunks.append(joiner.join(current))
            if overlap:
                current = current[-overlap:]
                current_len = sum(len(u) for u in current)
            else:
                current = []
                current_len = 0
        current.append(unit)
        current_len += u_len

    if current:
        chunks.append(joiner.join(current))

    return chunks


def chunk_document(doc: dict, max_tokens: int = 450, overlap_sentences: int = 1) -> list[dict]:
    """Fragmenta un documento del corpus (una línea de corpus_limpio.jsonl)
    en chunks con la metadata obligatoria de la Tabla 1 del spec."""
    formato = doc["formato"]
    texto_completo = doc["texto_completo"]

    if formato in TABULAR_FORMATS or formato in GEO_FORMATS:
        # Unidad natural = fila / elemento (ya separados por "\n\n" en
        # extract_tabular.py / extract_pbf.py / extract_mvt.py). No se
        # solapan: cada fila es un registro independiente.
        unidades = [u.strip() for u in texto_completo.split("\n\n") if u.strip()]
        joiner = "\n\n"
        overlap = 0
    else:
        # Prosa (pdf, html, json, txt, imágenes con OCR): segmentación
        # oracional + solape de oraciones completas entre chunks.
        unidades = split_sentences(texto_completo, doc.get("idioma", "es"))
        joiner = " "
        overlap = overlap_sentences

    if not unidades:
        return []

    textos_chunk = _pack_units(unidades, joiner, max_tokens, overlap)
    num_tokens_list = count_tokens_batch(textos_chunk)  # una sola llamada por documento

    chunks = []
    for posicion, (texto_chunk, num_tokens) in enumerate(zip(textos_chunk, num_tokens_list)):
        chunks.append({
            "doc_id": doc["doc_id"],
            "chunk_id": f"{doc['doc_id']}-chunk-{posicion:03d}",
            "fuente": doc["fuente"],
            "formato": formato,
            "fenomeno": doc["fenomeno"],
            "posicion": posicion,
            "num_tokens": num_tokens,
            "texto": texto_chunk,
            "idioma": doc.get("idioma", "es"),
        })
    return chunks


def run(
    corpus_jsonl: str = "data/corpus_limpio.jsonl",
    out_path: str = "data/chunks/chunks.jsonl",
    max_tokens: int = 450,
    overlap_sentences: int = 1,
) -> None:
    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)

    total_docs = 0
    total_chunks = 0

    with open(corpus_jsonl, encoding="utf-8") as f_in, open(out_file, "w", encoding="utf-8") as f_out:
        for line in f_in:
            line = line.strip()
            if not line:
                continue
            doc = json.loads(line)
            chunks = chunk_document(doc, max_tokens=max_tokens, overlap_sentences=overlap_sentences)
            for chunk in chunks:
                f_out.write(json.dumps(chunk, ensure_ascii=False) + "\n")
            total_docs += 1
            total_chunks += len(chunks)

    print(f"Chunking completo: {total_docs} documentos -> {total_chunks} chunks en {out_file}")


if __name__ == "__main__":
    run()
