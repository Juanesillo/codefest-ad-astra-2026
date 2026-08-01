import pdfplumber
import pytesseract

def extract_pdf(path: str, idioma_ocr: str = "spa+eng+por") -> str:
    """
    Extrae el texto de un PDF, preservando el orden de lectura por página.
    Adicionalmente, detecta imágenes dentro de la página y les aplica OCR
    para no perder información visual relevante (infografías, diagramas).
    """
    texto_paginas = []

    with pdfplumber.open(path) as pdf:
        for pagina in pdf.pages:
            # 1. Extraer texto nativo incrustado en el PDF
            texto_nativo = pagina.extract_text() or ""
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