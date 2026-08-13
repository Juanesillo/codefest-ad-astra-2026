# scripts/patch_doc_ids.py
"""Repara entrega/base_vectorial/encoder_bge_m3/ para usar el DOC_ID
oficial de ADL (en vez del doc_id interno que asignamos nosotros al
procesar), SIN volver a codificar nada con el encoder: el vector de un
chunk depende solo de su texto, que no cambió para los documentos que
siguen en el corpus. Se reconstruyen los vectores ya calculados desde el
índice viejo y se emparejan con los chunks nuevos (data/chunks/chunks.jsonl,
ya generados con el DOC_ID oficial) por (fuente, posicion) -- clave estable
porque la fragmentación es determinista y el texto de origen no cambió.

Los chunks de documentos excluidos (sin DOC_ID oficial en el inventario de
ADL) simplemente no aparecen en el chunks.jsonl nuevo, así que sus vectores
viejos no se copian: quedan fuera del índice parchado.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import faiss
from src.indexing.metadata_store import load_metadata, write_metadata

INDEX_DIR = "../entrega/base_vectorial/encoder_bge_m3"
CHUNKS_NUEVOS = "data/chunks/chunks.jsonl"


def run():
    print("Cargando índice y metadata viejos...")
    old_index = faiss.read_index(f"{INDEX_DIR}/index.faiss")
    old_metadata = load_metadata(f"{INDEX_DIR}/metadata.jsonl")
    print(f"  {old_index.ntotal} vectores, {len(old_metadata)} registros de metadata")

    # (fuente, posicion) -> indice interno viejo de FAISS
    print("Construyendo índice de búsqueda (fuente, posicion) -> vector viejo...")
    mapa_viejo = {}
    for i, r in enumerate(old_metadata):
        mapa_viejo[(r["fuente"], r["posicion"])] = i

    chunks_nuevos = load_metadata(CHUNKS_NUEVOS)
    print(f"  {len(chunks_nuevos)} chunks nuevos (con DOC_ID oficial) a emparejar")

    d = old_index.d
    nuevo_index = faiss.IndexFlatIP(d)
    nuevos_metadata = []
    sin_match = 0

    for chunk in chunks_nuevos:
        clave = (chunk["fuente"], chunk["posicion"])
        i_viejo = mapa_viejo.get(clave)
        if i_viejo is None:
            sin_match += 1
            continue

        # chequeo de seguridad: el texto debe ser identico, si no, el vector
        # reciclado no corresponde a este chunk y hay que abortar.
        if old_metadata[i_viejo]["texto"] != chunk["texto"]:
            raise RuntimeError(
                f"Texto no coincide para {clave}: la fragmentación no dio "
                f"el mismo resultado, no se puede reciclar el vector."
            )

        vector = old_index.reconstruct(i_viejo).reshape(1, -1)
        nuevo_index.add(vector)
        nuevos_metadata.append(chunk)

    if sin_match:
        print(f"  ADVERTENCIA: {sin_match} chunks nuevos no encontraron vector viejo (deberían ser 0)")

    print(f"Índice parchado: {nuevo_index.ntotal} vectores (antes {old_index.ntotal})")

    faiss.write_index(nuevo_index, f"{INDEX_DIR}/index.faiss")
    write_metadata(f"{INDEX_DIR}/metadata.jsonl", nuevos_metadata)
    print(f"Guardado en {INDEX_DIR}/")


if __name__ == "__main__":
    run()
