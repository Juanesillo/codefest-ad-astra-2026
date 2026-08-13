import pytest

from src.chunking.sentence_splitter import split_sentences


@pytest.mark.parametrize(
    "texto, idioma, esperado",
    [
        (
            "El Sr. Pérez llegó a las 3.14 pm. Luego se fue.",
            "es",
            ["El Sr. Pérez llegó a las 3.14 pm.", "Luego se fue."],
        ),
        (
            "EE.UU. anunció ayer un plan. La reunión fue en Bogotá.",
            "es",
            ["EE.UU. anunció ayer un plan.", "La reunión fue en Bogotá."],
        ),
        (
            "O Sr. Silva chegou. A reunião começou às 15h.",
            "pt",
            ["O Sr. Silva chegou.", "A reunião começou às 15h."],
        ),
        (
            "Mr. Anderson noted risks. The U.S. must act.",
            "en",
            ["Mr. Anderson noted risks.", "The U.S. must act."],
        ),
        (
            "J. K. Rowling escribió la saga. Fue un éxito mundial.",
            "es",
            ["J. K. Rowling escribió la saga.", "Fue un éxito mundial."],
        ),
        (
            "Texto con elipsis... sigue la misma idea. Nueva oración aquí.",
            "es",
            ["Texto con elipsis... sigue la misma idea.", "Nueva oración aquí."],
        ),
    ],
)
def test_casos_dificiles(texto, idioma, esperado):
    assert split_sentences(texto, idioma) == esperado


def test_bloque_vacio_no_lanza_excepcion():
    assert split_sentences("", "es") == []
    assert split_sentences("   ", "es") == []


def test_bloque_sin_puntuacion_se_devuelve_completo():
    assert split_sentences("Sin puntuacion final", "es") == ["Sin puntuacion final"]


def test_idioma_desconocido_no_falla():
    # cae al modelo de español en vez de lanzar una excepción
    resultado = split_sentences("El Sr. Pérez llegó. Se fue.", "fr")
    assert resultado == ["El Sr. Pérez llegó.", "Se fue."]


def test_limitacion_conocida_listas_numeradas_dentro_de_un_bloque():
    """NLTK no reconoce el numeral de una lista como marcador de ítem, así
    que "1." se trata como posible fin de oración. En la práctica esto
    produce fragmentos con el numeral suelto en vez de "1. Uno" como una
    sola unidad. No rompe el requisito de completitud lingüística (el
    numeral no es una oración cortada a la mitad), pero es una limitación
    conocida a tener en cuenta si el chunking se ve raro en documentos con
    listas numeradas dentro de un mismo bloque de texto."""
    texto = "1. Uno\n2. Dos\n3. Tres"
    resultado = split_sentences(texto, "es")
    assert resultado != ["1. Uno", "2. Dos", "3. Tres"]
    # ninguna palabra se pierde, solo queda mal agrupada
    assert " ".join(resultado).split() == texto.split()
