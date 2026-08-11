# src/graph/relations.py
from src.chunking.sentence_splitter import split_sentences

MAX_PALABRAS_RELACION = 6
RELACION_GENERICA = "se_menciona_junto_a"


def _sentence_spans(texto: str, idioma: str) -> list[tuple[int, int, str]]:
    """split_sentences devuelve las oraciones ya recortadas, sin su
    posición original; se reconstruye buscándolas en orden desde el
    último punto encontrado."""
    spans = []
    cursor = 0
    for oracion in split_sentences(texto, idioma):
        idx = texto.find(oracion, cursor)
        if idx == -1:
            continue
        spans.append((idx, idx + len(oracion), oracion))
        cursor = idx + len(oracion)
    return spans


def _frase_relacion(texto: str, entidad_a: dict, entidad_b: dict) -> str:
    """Usa el texto entre dos entidades como relación (heurística de
    patrones, sin dependencias sintácticas). Si es muy largo, vacío o
    no parece una frase razonable, cae a una relación genérica."""
    fragmento = texto[entidad_a["end"]:entidad_b["start"]].strip(" ,.;:()-\n\"'")
    palabras = fragmento.split()
    if not palabras or len(palabras) > MAX_PALABRAS_RELACION:
        return RELACION_GENERICA
    return " ".join(palabras).lower()


def extraer_relaciones(texto: str, idioma: str, entidades: list[dict]) -> list[tuple[dict, dict, str]]:
    """Empareja entidades consecutivas dentro de la misma oración (no
    todos los pares posibles, para no inventar relaciones entre entidades
    lejanas) y arma triples (entidad_a, entidad_b, relación)."""
    triples = []
    for inicio, fin, _ in _sentence_spans(texto, idioma):
        en_oracion = sorted(
            (e for e in entidades if e["start"] >= inicio and e["end"] <= fin),
            key=lambda e: e["start"],
        )
        for a, b in zip(en_oracion, en_oracion[1:]):
            triples.append((a, b, _frase_relacion(texto, a, b)))
    return triples
