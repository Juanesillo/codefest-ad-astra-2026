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
            # Ignorar el 8% superior (encabezados) y el 8% inferior (pie de
            # página). Los márgenes se calculan relativos al bbox real de la
            # página en vez de asumir que empieza en (0, 0): algunos PDFs
            # traen un MediaBox con origen distinto de cero (páginas con
            # marcas de corte, recortadas de un pliego mayor, etc.), y usar
            # coordenadas absolutas ahí produce un bbox fuera de la página.
            area_util = (x0, y0 + alto * 0.08, x1, y1 - alto * 0.08)
            pagina_recortada = pagina.crop(area_util)
            # 1. Extraer texto nativo incrustado en el PDF, ya sin encabezado/pie
            texto_nativo = pagina_recortada.extract_text() or ""
            texto_nativo = texto_nativo.strip()
            
            # 2. Extraer y procesar imágenes con OCR
            texto_imagenes = []
            for img in pagina.images:
                try:
                    # Obtener las coordenadas (bounding box) de la imagen en la página
                    bbox = (img["x0"], img["top"], img["x1"], img["bottom"])
                    
                    # Validar que las coordenadas formen un área válida
                    if bbox[0] < bbox[2] and bbox[1] < bbox[3]:
                        # Recortar esa región específica y convertirla en una imagen (PIL)
                        recorte = pagina.within_bbox(bbox)
                        pil_img = recorte.to_image(resolution=300).original
                        
                        # Extraer texto de la imagen usando el OCR ya configurado
                        texto_ocr = pytesseract.image_to_string(pil_img, lang=idioma_ocr)
                        if texto_ocr.strip():
                            texto_imagenes.append(texto_ocr.strip())
                except Exception:
                    # Si falla el recorte o el OCR de una imagen en particular, no rompemos el script
                    continue
            
            # 3. Concatenar texto nativo y texto de imágenes de la página actual
            texto_final_pagina = texto_nativo
            if texto_imagenes:
                if texto_final_pagina:
                    texto_final_pagina += "\n\n[TEXTO DE IMAGEN/GRÁFICO]:\n"
                else:
                    texto_final_pagina = "[TEXTO DE IMAGEN/GRÁFICO]:\n"
                    
                texto_final_pagina += "\n\n".join(texto_imagenes)
                
            if texto_final_pagina.strip():
                texto_paginas.append(texto_final_pagina.strip())

    return "\n\n".join(texto_paginas)