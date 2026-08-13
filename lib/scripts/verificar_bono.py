# scripts/verificar_bono.py
"""Corre una consulta con y sin el grafo para ver la diferencia. Uso:

    python scripts/verificar_bono.py
    python scripts/verificar_bono.py q028
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "entrega"))
import generador

CONSULTA_DEFECTO = "q028"


def main():
    query_id = sys.argv[1] if len(sys.argv) > 1 else CONSULTA_DEFECTO
    consultas = generador.parse_consultas()
    texto = consultas[query_id]

    print(f"{query_id}: {texto}\n")

    grafo = generador.get_grafo()
    print(f"grafo cargado: {grafo.number_of_nodes()} entidades, {grafo.number_of_edges()} relaciones\n")

    entidades = generador.entidades_de_consulta(texto)
    print(f"entidades detectadas en la consulta: {entidades}\n")

    hits_amplios = generador.search(texto, k=generador.K_VALIDACION_GRAFO)
    hits_faiss = hits_amplios[:generador.K_RETRIEVE]
    chunk_ids_faiss = {h["chunk_id"] for h in hits_amplios}
    conteo_grafo = generador.candidatos_grafo(texto, chunk_ids_permitidos=chunk_ids_faiss)
    print(f"candidatos que aporta el grafo (ya validados contra FAISS): {len(conteo_grafo)}\n")

    docs_sin_grafo = generador.aggregate_documents(hits_faiss, top_docs=3)
    hits_fusionados = generador.fusionar_rrf(hits_faiss, conteo_grafo) if conteo_grafo else hits_faiss
    docs_con_grafo = generador.aggregate_documents(hits_fusionados, top_docs=3)

    print("documentos SOLO FAISS:      ", [d["doc_id"] for d in docs_sin_grafo])
    print("documentos FAISS + grafo:   ", [d["doc_id"] for d in docs_con_grafo])

    if [d["doc_id"] for d in docs_sin_grafo] == [d["doc_id"] for d in docs_con_grafo]:
        print("\n(para esta consulta el grafo no cambió el resultado -- probá con otra)")
    else:
        print("\nEl grafo SÍ cambió el resultado para esta consulta.")


if __name__ == "__main__":
    main()
