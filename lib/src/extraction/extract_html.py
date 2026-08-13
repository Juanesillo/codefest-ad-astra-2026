from bs4 import BeautifulSoup


def extract_html(path: str) -> str:
    """
    Extrae el texto visible de un archivo HTML, eliminando scripts,
    estilos y marcado. Usa encabezados y párrafos como señales de
    estructura, insertando saltos de línea entre bloques.
    """
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        soup = BeautifulSoup(f, "html.parser")

    # eliminar elementos que no aportan contenido textual real
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript"]):
        tag.decompose()

    bloques = soup.find_all(["h1", "h2", "h3", "h4", "p", "li"])

    if bloques:
        texto = "\n\n".join(
            b.get_text(separator=" ", strip=True)
            for b in bloques
            if b.get_text(strip=True)
        )
    else:
        # fallback si el HTML no tiene esas etiquetas estructuradas
        texto = soup.get_text(separator="\n", strip=True)

    return texto