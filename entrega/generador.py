# entrega/generador.py
"""Lee las 50 consultas (consultas.txt), busca en el índice FAISS
(base_vectorial/encoder_bge_m3/) y genera resultados.jsonl con el esquema
de la Sección 9 del spec: 

3 documentos 
10 fragmentos por consulta, cadafragmento con máximo 250 palabras.

No depende de nada fuera de esta carpeta, solo de faiss-cpu,
sentence-transformers y nltk (ver requeriments.txt)."""
import json
import re
from pathlib import Path

import faiss
import nltk
from nltk.tokenize import sent_tokenize
from sentence_transformers import SentenceTransformer

ENTREGA_DIR = Path(__file__).resolve().parent
INDEX_DIR = ENTREGA_DIR / "base_vectorial/encoder_bge_m3"
CONSULTAS_PATH = ENTREGA_DIR / "consultas.txt"
OUT_PATH = ENTREGA_DIR / "resultados.jsonl"

MODEL_NAME = "BAAI/bge-m3"  # encodermultilingue
K_RETRIEVE = 30  # pool de chunks para agregar a nivel documento
TOP_DOCS = 3
TOP_FRAGMENTS = 10
MAX_PALABRAS_FRAGMENTO = 250
_NLTK_LANG = {"es": "spanish", "en": "english", "pt": "portuguese"}

_MODEL = None
_INDEX = None
_METADATA = None
_PUNKT_READY = False


def get_model() -> SentenceTransformer:
    global _MODEL
    if _MODEL is None:
        _MODEL = SentenceTransformer(MODEL_NAME)
    return _MODEL


def load_index():
    """Carga el índice FAISS y su metadata una sola vez (cacheado en el
    módulo). El id interno de FAISS es la posición en la lista de metadata."""
    global _INDEX, _METADATA
    if _INDEX is None:
        _INDEX = faiss.read_index(str(INDEX_DIR / "index.faiss"))
        _METADATA = []
        with open(INDEX_DIR / "metadata.jsonl", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    _METADATA.append(json.loads(line))
    return _INDEX, _METADATA


def search(query: str, k: int = K_RETRIEVE) -> list[dict]:
    """Codifica la consulta con el mismo encoder del índice, busca el top-k
    por similitud coseno (producto interno con vectores normalizados) y
    devuelve la metadata de cada chunk con su score, de mayor a menor."""
    index, metadata = load_index()
    q = get_model().encode([query], normalize_embeddings=True, convert_to_numpy=True).astype("float32")
    scores, ids = index.search(q, k)

    hits = []
    for score, chunk_idx in zip(scores[0], ids[0]):
        if chunk_idx == -1:  # FAISS devuelve -1 si hay menos de k resultados
            continue
        hits.append({**metadata[chunk_idx], "score": float(score)})
    return hits


def aggregate_documents(hits: list[dict], top_docs: int = TOP_DOCS) -> list[dict]:
    """Agrega chunks a nivel de documento por max pooling (Sección 8.6): la
    relevancia de un documento es la de su mejor chunk."""
    mejor_por_doc: dict[str, dict] = {}
    for h in hits:
        doc_id = h["doc_id"]
        if doc_id not in mejor_por_doc or h["score"] > mejor_por_doc[doc_id]["score"]:
            mejor_por_doc[doc_id] = h

    ranked = sorted(mejor_por_doc.values(), key=lambda h: -h["score"])[:top_docs]
    return [{"rank": i + 1, "doc_id": h["doc_id"]} for i, h in enumerate(ranked)]


def _ensure_punkt():
    global _PUNKT_READY
    if _PUNKT_READY:
        return
    try:
        nltk.data.find("tokenizers/punkt_tab")
    except LookupError:
        nltk.download("punkt_tab", quiet=True)
    _PUNKT_READY = True


def split_sentences(texto: str, idioma: str = "es") -> list[str]:
    """Segmenta texto en oraciones completas, consciente del idioma (es/en/pt)."""
    if not texto or not texto.strip():
        return []
    _ensure_punkt()
    lang = _NLTK_LANG.get(idioma, "spanish")
    return [o.strip() for o in sent_tokenize(texto, language=lang) if o.strip()]


def _contar_palabras(texto: str) -> int:
    return len(texto.split())


def _dividir_fragmento(texto: str, idioma: str = "es") -> list[str]:
    """Divide un fragmento que supera las 250 palabras en sub-fragmentos que
    respeten el límite, cortando únicamente en límites de oración completa
    (Sección 9.2.1: requisito de completitud lingüística)."""
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


def build_fragments(hits: list[dict], top_fragments: int = TOP_FRAGMENTS) -> list[dict]:
    """Arma los top_fragments de salida (Sección 9.2/9.3): recorre los hits
    en orden, parte los que superen 250 palabras (mismo chunk_id de origen
    en todos los sub-fragmentos, para trazabilidad) y devuelve la lista."""
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


def parse_consultas(path: Path = CONSULTAS_PATH) -> dict[str, str]:
    """Parsea el banco de 50 preguntas (q001...q050), donde cada consulta
    puede estar envuelta en varias líneas y separada por líneas en blanco."""
    texto = path.read_text(encoding="utf-8")
    partes = re.split(r"(?m)^(q\d{3})\s+", texto)
    it = iter(partes[1:])
    consultas = {}
    for query_id, cuerpo in zip(it, it):
        consultas[query_id] = re.sub(r"\s+", " ", cuerpo).strip()
    return consultas


def responder_consulta(query_id: str, texto_consulta: str) -> dict:
    hits = search(texto_consulta, k=K_RETRIEVE)
    documents = aggregate_documents(hits, top_docs=TOP_DOCS)
    fragments = build_fragments(hits, top_fragments=TOP_FRAGMENTS)
    return {
        "query_id": query_id,
        "documents": documents,
        "fragments": fragments,
    }


def run(consultas_path: Path = CONSULTAS_PATH, out_path: Path = OUT_PATH) -> None:
    consultas = parse_consultas(consultas_path)
    query_ids = sorted(consultas.keys())  # q001, q002, ..., q050

    with open(out_path, "w", encoding="utf-8") as f_out:
        for i, query_id in enumerate(query_ids, 1):
            resultado = responder_consulta(query_id, consultas[query_id])
            f_out.write(json.dumps(resultado, ensure_ascii=False) + "\n")
            print(f"[{i}/{len(query_ids)}] {query_id} -> "
                  f"{len(resultado['documents'])} docs, {len(resultado['fragments'])} fragmentos")

    print(f"\n{len(query_ids)} consultas procesadas -> {out_path}")


if __name__ == "__main__":
    run()
