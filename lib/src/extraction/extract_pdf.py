import pdfplumber
import pytesseract

from extract_html import extract_html


def extract_pdf(path: str, idioma_ocr: str = "spa+eng+por") -> str:
    """
    Extrae el texto de un PDF, preservando el orden de lectura por página.
    Adicionalmente, detecta imágenes dentro de la página y les aplica OCR
    para no perder información visual relevante (infografías, diagramas).
    """
    # Algunas descargas del scraping quedaron mal identificadas: el archivo
    # tiene extensión .pdf pero el contenido real es una página de error o
    # de login en HTML (ej. SIPRI). pdfplumber/pikepdf fallan ahí con
    # "No /Root object!". En ese caso se recupera el texto como HTML en vez
    # de perder el documento por completo.
    with open(path, "rb") as f:
        cabecera = f.read(2048).lstrip()
    if not cabecera.startswith(b"%PDF"):
        if b"<html" in cabecera.lower() or b"<!doctype html" in cabecera.lower():
            return extract_html(path)
        raise ValueError(f"El archivo no es un PDF válido (no empieza con %PDF): {path}")

    texto_paginas = []

    with pdfplumber.open(path) as pdf:
        for pagina in pdf.pages:
            x0, y0, x1, y1 = pagina.bbox
            alto = y1 - y0
            # recorta 8% arriba/abajo para sacar encabezado y pie de página.
            # se calcula sobre el bbox real (no desde 0,0) porque algunos
            # PDFs traen el MediaBox desplazado (páginas recortadas de un
            # pliego más grande) y con coordenadas absolutas el crop queda mal
            area_util = (x0, y0 + alto * 0.08, x1, y1 - alto * 0.08)
            pagina_recortada = pagina.crop(area_util)
            texto_nativo = (pagina_recortada.extract_text() or "").strip()

            texto_imagenes = []
            for img in pagina.images:
                try:
                    bbox = (img["x0"], img["top"], img["x1"], img["bottom"])
                    if bbox[0] < bbox[2] and bbox[1] < bbox[3]:
                        pil_img = pagina.within_bbox(bbox).to_image(resolution=300).original
                        texto_ocr = pytesseract.image_to_string(pil_img, lang=idioma_ocr)
                        if texto_ocr.strip():
                            texto_imagenes.append(texto_ocr.strip())
                except Exception:
                    continue  # imagen individual rota, no tumba la página completa

            texto_final_pagina = texto_nativo
            if texto_imagenes:
                prefijo = "\n\n[TEXTO DE IMAGEN/GRÁFICO]:\n" if texto_final_pagina else "[TEXTO DE IMAGEN/GRÁFICO]:\n"
                texto_final_pagina += prefijo + "\n\n".join(texto_imagenes)

            if texto_final_pagina.strip():
                texto_paginas.append(texto_final_pagina.strip())

    return "\n\n".join(texto_paginas)