# src/extraction/clean_text.py
import re
import unicodedata
from langdetect import detect

def clean_text(texto: str) -> str:
    texto = unicodedata.normalize("NFC", texto)          # normaliza UTF-8
    texto = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", texto)  # caracteres de control
    texto = re.sub(r"[ \t]+", " ", texto)                 # espacios redundantes
    texto = re.sub(r"\n{3,}", "\n\n", texto)              # saltos de línea excesivos
    return texto.strip()

def detect_language(texto: str) -> str:
    try:
        return detect(texto[:1000])  # con los primeros 1000 caracteres basta
    except Exception:
        return "unknown"