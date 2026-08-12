# src/graph/ner.py
import torch
from transformers import pipeline


MODEL_NAME = "Davlan/xlm-roberta-base-ner-hrl"

_NER = None


def get_ner():
    global _NER
    if _NER is None:
        device = 0 if torch.cuda.is_available() else -1
        _NER = pipeline("ner", model=MODEL_NAME, aggregation_strategy="simple", device=device)
    return _NER


# los chunks ya vienen presupuestados a ~450 tokens (Sección 3.3), pero se
# recorta por si acaso: el modelo (BERT) tiene limite de 512 tokens
MAX_CHARS = 1800
SCORE_MINIMO = 0.8


def extraer_entidades(texto: str) -> list[dict]:
    """Devuelve las entidades (PER/ORG/LOC/MISC) encontradas en el texto,
    con su posición de caracter para poder emparejarlas con oraciones.
    Filtra entidades de baja confianza o con fragmentos de wordpiece sin
    unir ("##..."): pasa sobre todo en listas densas de nombres (comités,
    agradecimientos) donde el PDF no deja separación clara entre entidades."""
    if not texto or not texto.strip():
        return []
    entidades = get_ner()(texto[:MAX_CHARS])
    return [
        {"texto": e["word"].strip(), "tipo": e["entity_group"], "start": e["start"], "end": e["end"]}
        for e in entidades
        if len(e["word"].strip()) > 1
        and e["score"] >= SCORE_MINIMO
        and "##" not in e["word"]
    ]
