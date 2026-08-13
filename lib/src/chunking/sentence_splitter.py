# src/chunking/sentence_splitter.py
import nltk
from nltk.tokenize import sent_tokenize

_NLTK_LANG = {"es": "spanish", "en": "english", "pt": "portuguese"}
_PUNKT_READY = False


def _ensure_punkt():
    global _PUNKT_READY
    if _PUNKT_READY:
        return
    try:
        nltk.data.find("tokenizers/punkt_tab")
    except LookupError:
        nltk.download("punkt_tab", quiet=True)
    _PUNKT_READY = True


def split_sentences(texto: str, idioma: str = "es") -> list[str]:
    """Segmenta texto en oraciones completas, consciente del idioma (es/en/pt)."""
    if not texto or not texto.strip():
        return []
    _ensure_punkt()
    lang = _NLTK_LANG.get(idioma, "spanish")
    oraciones = sent_tokenize(texto, language=lang)
    return [o.strip() for o in oraciones if o.strip()]
