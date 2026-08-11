import numpy as np
import pytest

from src.indexing.encoder import encode_texts

pytestmark = pytest.mark.slow


def test_forma_y_tipo_de_los_vectores():
    textos = ["hola", "hello", "olá"]
    vectores = encode_texts(textos)
    assert vectores.shape == (3, 1024)
    assert vectores.dtype == np.float32


def test_vectores_normalizados():
    vectores = encode_texts(["cualquier texto de prueba"])
    norma = np.linalg.norm(vectores[0])
    assert norma == pytest.approx(1.0, abs=1e-3)


def test_lista_vacia_no_falla():
    vectores = encode_texts([])
    assert vectores.shape == (0, 1024)


def test_similitud_semantica_tiene_sentido():
    """Prueba de sanidad: un texto sobre IA en defensa debe parecerse más
    a otro sobre lo mismo que a uno sobre un tema aparte. No reemplaza un
    benchmark formal, pero detecta si el modelo quedó mal cableado."""
    consulta = encode_texts(
        ["¿Cómo se usa la inteligencia artificial en la defensa nacional?"]
    )[0]
    pasaje_relevante = encode_texts(
        ["La inteligencia artificial se ha convertido en un factor central "
         "para la defensa nacional."]
    )[0]
    pasaje_irrelevante = encode_texts(
        ["La receta lleva harina, huevos y azúcar horneados por media hora."]
    )[0]

    similitud_relevante = float(np.dot(consulta, pasaje_relevante))
    similitud_irrelevante = float(np.dot(consulta, pasaje_irrelevante))
    assert similitud_relevante > similitud_irrelevante
