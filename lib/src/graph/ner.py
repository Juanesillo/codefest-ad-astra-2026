# src/graph/ner.py
import spacy

# xx_ent_wiki_sm es multilingue (cubre es/en/pt entre otros), licencia MIT
# explicita -- Babelscape/wikineural-multilingual-ner (usado antes) es CC
# BY-NC-SA 4.0, no permitida segun el FAQ de CODEFEST.
MODEL_NAME = "xx_ent_wiki_sm"

_NLP = None


def get_nlp():
    global _NLP
    if _NLP is None:
        _NLP = spacy.load(MODEL_NAME)
    return _NLP


def extraer_entidades(texto: str) -> list[dict]:
    """Devuelve las entidades (PER/ORG/LOC/MISC) encontradas en el texto,
    con su posición de caracter para poder emparejarlas con oraciones."""
    if not texto or not texto.strip():
        return []
    doc = get_nlp()(texto)
    return [
        {"texto": ent.text.strip(), "tipo": ent.label_, "start": ent.start_char, "end": ent.end_char}
        for ent in doc.ents
        if len(ent.text.strip()) > 1
    ]
