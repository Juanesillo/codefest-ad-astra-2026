# src/indexing/metadata_store.py
import json
from pathlib import Path


def write_metadata(path: str, registros: list[dict]) -> None:
    """Escribe la metadata en JSON Lines, un objeto por línea, en el mismo
    orden en que los vectores correspondientes se insertaron en FAISS (el
    id interno de FAISS = número de línea, 0-indexado)."""
    out_file = Path(path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        for registro in registros:
            f.write(json.dumps(registro, ensure_ascii=False) + "\n")


def load_metadata(path: str) -> list[dict]:
    """Carga metadata.jsonl como una lista; el índice de la lista coincide
    con el id interno de FAISS."""
    registros = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                registros.append(json.loads(line))
    return registros
