# entrega/generador.py
"""Lee las 50 consultas de evaluación, busca en el índice FAISS
(entrega/base_vectorial/encoder_bge_m3/) y genera entrega/resultados.jsonl
con el esquema exacto de la Sección 9 del spec (3 documentos + 10
fragmentos por consulta, cada fragmento con máximo 250 palabras)."""
import json
import re
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from src.retrieval.search import search
from src.retrieval.aggregation import aggregate_documents, build_fragments

CONSULTAS_PATH = REPO_ROOT / "data/processed/DOC-0000.txt"
OUT_PATH = REPO_ROOT / "entrega/resultados.jsonl"

K_RETRIEVE = 30  # pool de chunks para agregar a nivel documento
TOP_DOCS = 3
TOP_FRAGMENTS = 10


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
