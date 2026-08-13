# scripts/test_pdf_crop.py
import pdfplumber
import os

def test_crop_pdf(pdf_path: str):
    """Compara texto extraído con y sin el recorte de márgenes, para
    verificar a ojo que el crop de extract_pdf.py saca el boilerplate
    (encabezado/pie) sin comerse contenido real."""
    if not os.path.exists(pdf_path):
        print(f"no se encontró el archivo: {pdf_path}")
        return

    print(f"probando en: {os.path.basename(pdf_path)}")

    with pdfplumber.open(pdf_path) as pdf:
        pagina = pdf.pages[0]

        texto_normal = pagina.extract_text() or ""

        alto = pagina.height
        ancho = pagina.width
        area_util = (0, alto * 0.08, ancho, alto * 0.92)
        texto_recortado = pagina.crop(area_util).extract_text() or ""

        print("\n--- sin recortar ---")
        print(texto_normal[:300] + "\n\n[...]\n\n" + texto_normal[-300:])

        print("\n--- recortado ---")
        print(texto_recortado[:300] + "\n\n[...]\n\n" + texto_recortado[-300:])

if __name__ == "__main__":
    # cambiar por cualquier PDF del corpus (ej. uno de F1 o F2 con encabezados)
    ruta_prueba = "data/raw/CODEFEST/F1_IA_y_Capacidades_Estrategicas/AI_Index_Stanford/pdfs/AIINDEX_ai-index-report-2017.pdf"
    test_crop_pdf(ruta_prueba)