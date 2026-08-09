import io

from PIL import Image
import pytesseract


def extract_image(path: str, idioma_ocr: str = "spa+eng+por") -> str:
    """
    Aplica OCR a una imagen para recuperar texto relevante (infografías,
    gráficos con texto). Usa los tres idiomas del corpus por defecto.
    """
    try:
        img = Image.open(path)
        # pytesseract solo reconoce el formato de la imagen a partir de
        # img.format, y no sabe guardar formatos como AVIF (usados por las
        # fuentes que scrapean imágenes web modernas) al escribir el
        # archivo temporal para el binario de tesseract. Normalizando
        # siempre a PNG en memoria evitamos ese "Unsupported image
        # format/type" sin depender de la extensión del archivo original.
        buffer = io.BytesIO()
        img.convert("RGB").save(buffer, format="PNG")
        buffer.seek(0)
        img_normalizada = Image.open(buffer)

        texto = pytesseract.image_to_string(img_normalizada, lang=idioma_ocr)
        return texto.strip()
    except Exception:
        # si la imagen no tiene texto útil o falla el OCR, devolver vacío
        # en vez de romper el pipeline completo
        return ""