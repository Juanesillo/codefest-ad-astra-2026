# src/retrieval/search.py
import faiss

from src.indexing.encoder import encode_texts
from src.indexing.metadata_store import load_metadata

INDEX_DIR_DEFAULT = "entrega/base_vectorial/encoder_bge_m3"

_INDEX = None
_METADATA = None
_INDEX_DIR = None


def load_index(index_dir: str = INDEX_DIR_DEFAULT):
    """Carga el índice FAISS y su metadata una sola vez (cacheado en el
    módulo). El id interno de FAISS es la posición en la lista de metadata."""
    global _INDEX, _METADATA, _INDEX_DIR
    if _INDEX is None or _INDEX_DIR != index_dir:
        _INDEX = faiss.read_index(f"{index_dir}/index.faiss")
        _METADATA = load_metadata(f"{index_dir}/metadata.jsonl")
        _INDEX_DIR = index_dir
    return _INDEX, _METADATA


def search(query: str, k: int = 10, index_dir: str = INDEX_DIR_DEFAULT) -> list[dict]:
    """Codifica la consulta con el mismo encoder del índice, busca el top-k
    por similitud coseno (producto interno con vectores normalizados) y
    devuelve la metadata de cada chunk con su score, ordenada de mayor a
    menor relevancia."""
    index, metadata = load_index(index_dir)
    q = encode_texts([query], batch_size=1)
    scores, ids = index.search(q, k)

    hits = []
    for score, chunk_idx in zip(scores[0], ids[0]):
        if chunk_idx == -1:  # FAISS devuelve -1 si hay menos de k resultados
            continue
        chunk = metadata[chunk_idx]
        hits.append({**chunk, "score": float(score)})
    return hits
