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


# ~3.7 caracteres/token medido a ojo sobre una muestra con el tokenizer de
# bge-m3. Es solo para presupuestar el corte sin llamar al tokenizer por
# cada oración; el num_tokens real de cada chunk se recalcula al final.
CHARS_PER_TOKEN_ESTIMATE = 3.7


def _wrap_oversized(unit: str, max_chars: int) -> list[str]:
    """Para cuando una oración/fila sola ya se pasa del presupuesto (listas
    de nombres sin puntuación, texto OCR roto, cid:123 de PDFs mal
    decodificados). Corta por palabra, y si ni eso alcanza (sin espacios),
    corta a lo bruto por caracteres. Prosa normal no debería llegar acá."""
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

    # texto anómalo tokeniza peor que prosa normal, por eso el wrap de
    # emergencia usa un presupuesto más conservador (mitad del normal)
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
        # csv/xlsx/pbf ya vienen separados por fila en "\n\n"; cada fila es
        # un registro independiente, no tiene sentido solaparlas
        unidades = [u.strip() for u in texto_completo.split("\n\n") if u.strip()]
        joiner = "\n\n"
        overlap = 0
    else:
        # prosa: cortamos por oración y solapamos para no perder contexto
        unidades = split_sentences(texto_completo, doc.get("idioma", "es"))
        joiner = " "
        overlap = overlap_sentences

    if not unidades:
        return []

    textos_chunk = _pack_units(unidades, joiner, max_tokens, overlap)
    num_tokens_list = count_tokens_batch(textos_chunk)

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
