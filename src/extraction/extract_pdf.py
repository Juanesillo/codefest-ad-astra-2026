import pdfplumber


def extract_pdf(path: str) -> str:
    """
    Extrae el texto de un PDF, preservando el orden de lectura por página.
    """
    texto_paginas = []

    with pdfplumber.open(path) as pdf:
        for pagina in pdf.pages:
            texto = pagina.extract_text()
            if texto:
                texto_paginas.append(texto)

    return "\n\n".join(texto_paginas)