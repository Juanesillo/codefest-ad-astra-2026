# src/indexing/build_index.py
import json
from pathlib import Path

import faiss

from src.indexing.encoder import encode_texts
from src.indexing.metadata_store import write_metadata

OUT_DIR_DEFAULT = "entrega/base_vectorial/encoder_bge_m3"


def _read_chunks(chunks_path: str, limit: int | None = None):
    with open(chunks_path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if limit is not None and i >= limit:
                break
            line = line.strip()
            if line:
                yield json.loads(line)


def run(
    chunks_path: str = "data/chunks/chunks.jsonl",
    out_dir: str = OUT_DIR_DEFAULT,
    batch_size: int = 32,
    superbatch_size: int = 2000,
    limit: int | None = None,
) -> None:
    """Lee chunks.jsonl en streaming por superlotes (para no cargar todo el
    corpus en memoria), codifica cada superlote y va llenando un único
    IndexFlatIP. `limit` sirve para probar con un subconjunto chico."""
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    index = None
    todos_los_registros: list[dict] = []
    superbatch: list[dict] = []

    def flush(lote: list[dict]):
        nonlocal index
        if not lote:
            return
        textos = [r["texto"] for r in lote]
        embeddings = encode_texts(textos, batch_size=batch_size)
        if index is None:
            index = faiss.IndexFlatIP(embeddings.shape[1])
        index.add(embeddings)
        todos_los_registros.extend(lote)

    for registro in _read_chunks(chunks_path, limit=limit):
        superbatch.append(registro)
        if len(superbatch) >= superbatch_size:
            flush(superbatch)
            print(f"  ... {len(todos_los_registros)} chunks codificados")
            superbatch = []
    flush(superbatch)

    if index is None:
        print("No hay chunks para indexar (¿chunks_path vacío o limit=0?).")
        return

    faiss.write_index(index, str(out_path / "index.faiss"))
    write_metadata(str(out_path / "metadata.jsonl"), todos_los_registros)

    print(f"Índice FAISS con {index.ntotal} vectores guardado en {out_path}")


if __name__ == "__main__":
    run()
