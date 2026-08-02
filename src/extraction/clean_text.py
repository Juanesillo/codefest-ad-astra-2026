# src/extraction/clean_text.py
import re
import unicodedata
from langdetect import detect

def clean_text(texto: str) -> str:
    texto = unicodedata.normalize("NFC", texto)          # normaliza UTF-8
    texto = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", texto)  # caracteres de control

    # --- PATRONES GENÉRICOS DE BOILERPLATE ---
    
    # 1. Elimina variaciones de "Página X de Y", "Page 12 of 30", "Pág. 4"
    texto = re.sub(r"(?i)\b(página|pág|page)\s+\d+(\s+(de|of)\s+\d+)?\b", "", texto)
    
    # 2. Elimina números de página aislados en líneas independientes (ej. una línea que solo tiene "12")
    texto = re.sub(r"(?m)^\s*\d+\s*$", "", texto)
    
    # 3. Elimina URLs o links repetitivos de cabecera (http/https/www)
    texto = re.sub(r"https?://\S+|www\.\S+", "", texto)
    
    # 4. Elimina patrones genéricos de marcas de fecha/mes/año al inicio o fin de línea
    # Ej: "JANUARY 2020", "Noviembre 2018", "REPORT - 2021"
    meses = r"(january|february|march|april|may|june|july|august|september|october|november|december|enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)"
    texto = re.sub(rf"(?i)\b{meses}\s+\d{{4}}\b", "", texto)

    # ------------------------------------------

    texto = re.sub(r"[ \t]+", " ", texto)                 # espacios redundantes
    texto = re.sub(r"\n{3,}", "\n\n", texto)              # saltos de línea excesivos
    return texto.strip()

def detect_language(texto: str) -> str:
    try:
        return detect(texto[:1000])  # con los primeros 1000 caracteres basta
    except Exception:
        return "unknown"