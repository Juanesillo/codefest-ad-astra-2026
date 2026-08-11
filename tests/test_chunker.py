import json

import pytest

from src.chunking.chunker import chunk_document
from src.chunking.chunker import run as run_chunker
from src.chunking.sentence_splitter import split_sentences

FIXTURE_PATH = "tests/fixtures/corpus_fixture.jsonl"

CAMPOS_OBLIGATORIOS = {
    "doc_id": str,
    "chunk_id": str,
    "fuente": str,
    "formato": str,
    "fenomeno": int,
    "posicion": int,
    "num_tokens": int,
    "texto": str,
}


@pytest.fixture(scope="module")
def documentos_fixture():
    with open(FIXTURE_PATH, encoding="utf-8") as f:
        return {json.loads(linea)["doc_id"]: json.loads(linea) for linea in f}


def _doc(documentos_fixture, doc_id):
    return documentos_fixture[doc_id]


def test_campos_obligatorios_de_la_tabla_1(documentos_fixture):
    for doc in documentos_fixture.values():
        for chunk in chunk_document(doc):
            for campo, tipo in CAMPOS_OBLIGATORIOS.items():
                assert campo in chunk, f"falta el campo {campo} en {chunk.get('chunk_id')}"
                assert isinstance(chunk[campo], tipo), f"{campo} no es {tipo} en {chunk['chunk_id']}"
            assert chunk["texto"].strip() != ""


def test_posicion_empieza_en_cero_y_es_consecutiva(documentos_fixture):
    doc = _doc(documentos_fixture, "DOC-FIX-001")
    posiciones = [c["posicion"] for c in chunk_document(doc)]
    assert posiciones == list(range(len(posiciones)))


def test_chunks_de_prosa_no_terminan_a_mitad_de_oracion(documentos_fixture):
    doc = _doc(documentos_fixture, "DOC-FIX-001")
    for chunk in chunk_document(doc):
        assert chunk["texto"][-1] in ".!?…"


def test_fenomeno_se_propaga_sin_corregirse(documentos_fixture):
    doc = _doc(documentos_fixture, "DOC-FIX-006")
    assert doc["fenomeno"] == 0
    for chunk in chunk_document(doc):
        assert chunk["fenomeno"] == 0


def test_documento_vacio_no_genera_chunks(documentos_fixture):
    doc = _doc(documentos_fixture, "DOC-FIX-008")
    assert chunk_document(doc) == []


def test_documento_de_una_sola_oracion_da_un_solo_chunk(documentos_fixture):
    doc = _doc(documentos_fixture, "DOC-FIX-007")
    chunks = chunk_document(doc)
    assert len(chunks) == 1
    assert chunks[0]["posicion"] == 0
    assert chunks[0]["texto"] == doc["texto_completo"]


def test_fila_csv_nunca_queda_partida_entre_chunks(documentos_fixture):
    doc = _doc(documentos_fixture, "DOC-FIX-004")
    filas_originales = [f.strip() for f in doc["texto_completo"].split("\n\n")]
    chunks = chunk_document(doc)
    texto_completo_chunks = "\n\n".join(c["texto"] for c in chunks)
    for fila in filas_originales:
        assert fila in texto_completo_chunks


def test_formato_pbf_se_trata_como_geo_no_como_prosa(documentos_fixture):
    doc = _doc(documentos_fixture, "DOC-FIX-011")
    elementos_originales = [e.strip() for e in doc["texto_completo"].split("\n\n")]
    chunks = chunk_document(doc)
    texto_completo_chunks = "\n\n".join(c["texto"] for c in chunks)
    for elemento in elementos_originales:
        assert elemento in texto_completo_chunks


def test_unidad_gigante_sin_puntuacion_se_corta_por_palabras_como_ultimo_recurso(documentos_fixture):
    # a diferencia de una oracion (que nunca se corta), una fila/valor sin
    # ningun signo de puntuacion que por si sola supera el presupuesto de
    # tokens SI se corta por palabras como ultimo recurso -- ninguna palabra
    # se pierde en el proceso, solo se redistribuye entre varios chunks
    doc = _doc(documentos_fixture, "DOC-FIX-005")
    chunks = chunk_document(doc)
    assert len(chunks) > 1

    palabras_originales = doc["texto_completo"].split()
    palabras_en_chunks = " ".join(c["texto"] for c in chunks).split()
    assert palabras_en_chunks == palabras_originales


def test_overlap_entre_chunks_consecutivos(documentos_fixture):
    doc = _doc(documentos_fixture, "DOC-FIX-010")
    # max_tokens chico a proposito, para forzar varios chunks con este
    # documento de 20 oraciones cortas
    chunks = chunk_document(doc, max_tokens=40, overlap_sentences=1)
    assert len(chunks) > 1

    oraciones_originales = split_sentences(doc["texto_completo"], doc["idioma"])
    for anterior, siguiente in zip(chunks, chunks[1:]):
        ultima_oracion_anterior = split_sentences(anterior["texto"], doc["idioma"])[-1]
        primera_oracion_siguiente = split_sentences(siguiente["texto"], doc["idioma"])[0]
        assert ultima_oracion_anterior == primera_oracion_siguiente

    # ninguna oracion original se perdio en el proceso
    todas_las_oraciones_en_chunks = " ".join(c["texto"] for c in chunks)
    for oracion in oraciones_originales:
        assert oracion in todas_las_oraciones_en_chunks


def test_es_determinista(documentos_fixture):
    doc = _doc(documentos_fixture, "DOC-FIX-002")
    primera_corrida = chunk_document(doc)
    segunda_corrida = chunk_document(doc)
    assert primera_corrida == segunda_corrida


def test_run_sobre_el_corpus_completo_no_falla(tmp_path):
    salida = tmp_path / "chunks_fixture.jsonl"
    run_chunker(corpus_jsonl=FIXTURE_PATH, out_path=str(salida))
    assert salida.exists()

    lineas = salida.read_text(encoding="utf-8").strip().split("\n")
    assert len(lineas) > 0
    for linea in lineas:
        chunk = json.loads(linea)
        for campo in CAMPOS_OBLIGATORIOS:
            assert campo in chunk
