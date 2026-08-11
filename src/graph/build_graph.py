# src/graph/build_graph.py
import json
from pathlib import Path

import networkx as nx

from src.graph.ner import extraer_entidades
from src.graph.relations import extraer_relaciones

OUT_PATH_DEFAULT = "entrega/base_vectorial/grafo/grafo.graphml"


def _clave(texto: str) -> str:
    return texto.strip().lower()


def build_graph(
    chunks_path: str = "data/chunks/chunks.jsonl",
    out_path: str = OUT_PATH_DEFAULT,
    limit: int | None = 6000,
    every_n: int = 32,
) -> nx.MultiDiGraph:
    """Recorre chunks.jsonl, extrae entidades y relaciones por heurística
    de co-ocurrencia dentro de la oración, y arma un grafo dirigido donde
    cada arista guarda su doc_id/chunk_id de origen (trazabilidad, Sección
    7.2).

    NER sobre el corpus completo (163k chunks, ~85ms/chunk en GPU) tomaría
    unas 4 horas, mucho más de lo que amerita un componente bonus; en vez
    de eso se toma 1 de cada `every_n` chunks (`limit` acota el total). Los
    chunks están agrupados por fenómeno en bloques dentro del archivo
    (F1: 0-99252, F2: 99253-131996, F3: 131997-163624), así que un límite
    simple sin stride solo vería F1 — el muestreo por stride sí cubre los 3."""
    G = nx.MultiDiGraph()
    procesados = 0

    with open(chunks_path, encoding="utf-8") as f:
        for i, line in enumerate(f):
            if i % every_n != 0:
                continue
            if limit is not None and procesados >= limit:
                break
            procesados += 1
            line = line.strip()
            if not line:
                continue
            chunk = json.loads(line)
            texto = chunk["texto"]
            idioma = chunk.get("idioma", "es")

            entidades = extraer_entidades(texto)
            if len(entidades) < 2:
                continue

            for entidad_a, entidad_b, relacion in extraer_relaciones(texto, idioma, entidades):
                clave_a, clave_b = _clave(entidad_a["texto"]), _clave(entidad_b["texto"])
                if not clave_a or not clave_b or clave_a == clave_b:
                    continue
                if clave_a not in G:
                    G.add_node(clave_a, label=entidad_a["texto"], tipo=entidad_a["tipo"])
                if clave_b not in G:
                    G.add_node(clave_b, label=entidad_b["texto"], tipo=entidad_b["tipo"])
                G.add_edge(
                    clave_a, clave_b,
                    relacion=relacion,
                    doc_id=chunk["doc_id"],
                    chunk_id=chunk["chunk_id"],
                    fenomeno=chunk["fenomeno"],
                )

            if procesados % 500 == 0:
                print(f"  ... {procesados} chunks procesados (linea {i}), {G.number_of_nodes()} entidades, {G.number_of_edges()} relaciones")

    out_file = Path(out_path)
    out_file.parent.mkdir(parents=True, exist_ok=True)
    nx.write_graphml(G, out_file)
    print(f"Grafo guardado en {out_file}: {G.number_of_nodes()} entidades, {G.number_of_edges()} relaciones")
    return G


if __name__ == "__main__":
    build_graph()
