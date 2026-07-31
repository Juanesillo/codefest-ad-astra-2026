from PIL import Image
import pytesseract


def extract_image(path: str, idioma_ocr: str = "spa+eng+por") -> str:
    """
    Aplica OCR a una imagen para recuperar texto relevante (infografías,
    gráficos con texto). Usa los tres idiomas del corpus por defecto.
    """
    try:
        img = Image.open(path)
        texto = pytesseract.image_to_string(img, lang=idioma_ocr)
        return texto.strip()
    except Exception as e:
        # si la imagen no tiene texto útil o falla el OCR, devolver vacío
        # en vez de romper el pipeline completo
        return ""