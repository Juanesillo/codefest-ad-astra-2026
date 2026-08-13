# src/extraction/base.py
from dataclasses import dataclass

@dataclass
class ExtractedDoc:
    doc_id: str
    fuente: str
    formato: str
    texto: str          # texto plano, limpio de marcado
    idioma: str = None  # se llena en la fase de limpieza