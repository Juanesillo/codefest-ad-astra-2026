# src/extraction/clean_text.py
import re
import unicodedata
from langdetect import detect

def clean_text(texto: str) -> str:
    texto = unicodedata.normalize("NFC", texto)
    texto = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", texto)  # caracteres de control

    # boilerplate típico de reportes: "Página 4 de 30", números de página
    # sueltos, links de cabecera, fechas tipo "Enero 2018" al inicio/fin de línea
    texto = re.sub(r"(?i)\b(página|pág|page)\s+\d+(\s+(de|of)\s+\d+)?\b", "", texto)
    texto = re.sub(r"(?m)^\s*\d+\s*$", "", texto)
    texto = re.sub(r"https?://\S+|www\.\S+", "", texto)
    meses = r"(january|february|march|april|may|june|july|august|september|october|november|december|enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)"
    texto = re.sub(rf"(?i)\b{meses}\s+\d{{4}}\b", "", texto)

    texto = re.sub(r"[ \t]+", " ", texto)
    texto = re.sub(r"\n{3,}", "\n\n", texto)
    return texto.strip()


IDIOMAS_PERMITIDOS = {"es": "es", "en": "en", "pt": "pt", "spanish": "es", "english": "en", "portuguese": "pt"}

def detect_language(texto: str) -> str:
    if not texto or len(texto.strip()) < 20:
        return "es"
    try:
        lang = detect(texto[:1000]).lower()  # con 1000 caracteres alcanza
        return IDIOMAS_PERMITIDOS.get(lang, "es")
    except Exception:
        return "es"