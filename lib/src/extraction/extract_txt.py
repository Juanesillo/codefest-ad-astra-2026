def extract_txt(path: str) -> str:
    """
    Extrae el texto de archivos .txt planos (ej. transcripciones o
    extracciones ya hechas por la fuente original, como SWF_full-text.txt).
    """
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.read().strip()
