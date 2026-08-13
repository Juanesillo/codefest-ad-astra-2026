import numpy as np
import pytest
import faiss

from src.chunking.chunker import run as run_chunker
from src.indexing.build_index import run as run_build_index
from src.indexing.encoder import encode_texts
from src.indexing.metadata_store import load_metadata

FIXTURE_PATH = "tests/fixtures/corpus_fixture.jsonl"

pytestmark = pytest.mark.slow


def test_pipeline_completo_chunk_encode_faiss_query(tmp_path):
    chunks_path = tmp_path / "chunks.jsonl"
    run_chunker(corpus_jsonl=FIXTURE_PATH, out_path=str(chunks_path))

    out_dir = tmp_path / "encoder_bge_m3"
    run_build_index(chunks_path=str(chunks_path), out_dir=str(out_dir), batch_size=16)

    indice = faiss.read_index(str(out_dir / "index.faiss"))
    metadata = load_metadata(str(out_dir / "metadata.jsonl"))
    assert indice.ntotal == len(metadata)

    # la fila i de metadata debe corresponder exactamente al vector i que
    # FAISS le asignó como id interno -- la correspondencia es puramente
    # posicional, así que hay que verificarla explícitamente
    posicion_de_prueba = 0
    vector_reconstruido = indice.reconstruct(posicion_de_prueba)
    vector_esperado = encode_texts([metadata[posicion_de_prueba]["texto"]])[0]
    assert np.allclose(vector_reconstruido, vector_esperado, atol=1e-3)

    consulta = encode_texts(
        ["¿Qué papel juega la inteligencia artificial en la defensa nacional?"]
    )
    _, ids_resultado = indice.search(consulta, k=3)

    doc_ids_recuperados = [metadata[i]["doc_id"] for i in ids_resultado[0]]
    assert "DOC-FIX-001" in doc_ids_recuperados
