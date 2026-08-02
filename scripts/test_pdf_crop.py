# scripts/test_pdf_crop.py
import pdfplumber
import os

def test_crop_pdf(pdf_path: str):
    if not os.path.exists(pdf_path):
        print(f"❌ Error: No se encontró el archivo en la ruta:\n{pdf_path}")
        return

    print(f"--- Probando extracción visual en: {os.path.basename(pdf_path)} ---")
    
    with pdfplumber.open(pdf_path) as pdf:
        # Tomar solo la primera página para la prueba
        pagina = pdf.pages[0]
        
        # 1. Extracción NORMAL (La que captura todo el ruido)
        texto_normal = pagina.extract_text() or ""
        
        # 2. Extracción RECORTADA (La mejora propuesta)
        alto = pagina.height
        ancho = pagina.width
        
        # Recortamos el 8% superior y el 8% inferior
        # Las coordenadas son: (izquierda, arriba, derecha, abajo)
        area_util = (0, alto * 0.08, ancho, alto * 0.92)
        pagina_recortada = pagina.crop(area_util)
        
        texto_recortado = pagina_recortada.extract_text() or ""
        
        # --- IMPRIMIR Y COMPARAR RESULTADOS ---
        print("\n" + "="*60)
        print("❌ RESULTADO ORIGINAL (Sin recortar)")
        print("="*60)
        # Imprimimos los primeros y últimos 300 caracteres para ver los márgenes
        print(texto_normal[:300] + "\n\n[... TEXTO INTERMEDIO ...]\n\n" + texto_normal[-300:])
        
        print("\n" + "="*60)
        print("✅ RESULTADO RECORTADO (Boilerplate eliminado)")
        print("="*60)
        print(texto_recortado[:300] + "\n\n[... TEXTO INTERMEDIO ...]\n\n" + texto_recortado[-300:])

if __name__ == "__main__":
    # AQUÍ DEBES PONER LA RUTA DE UN PDF REAL DE TU CORPUS
    # Por ejemplo, busca uno dentro de la carpeta F1 o F2 que sepas que tiene encabezados
    ruta_prueba = "data/raw/CODEFEST/F1_IA_y_Capacidades_Estrategicas/AI_Index_Stanford/pdfs/AIINDEX_ai-index-report-2017.pdf"
    
    test_crop_pdf(ruta_prueba)