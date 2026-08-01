import pandas as pd
import json
import re
from pathlib import Path

def extraer_numero_fenomeno(valor_fenomeno) -> int:
    """
    Convierte el string de la carpeta (ej. 'fenomeno_1', 'Fenomeno 2') 
    en un entero (1, 2 o 3) como exige la Tabla 1 de la Especificación.
    """
    if pd.isna(valor_fenomeno):
        return 0 # Valor por defecto si no se encuentra
    
    # Busca cualquier dígito en el string
    coincidencia = re.search(r'\d+', str(valor_fenomeno))
    if coincidencia:
        return int(coincidencia.group())
    return 0

def build_corpus(registry_csv="data/doc_registry.csv", 
                 idiomas_csv="data/idiomas.csv", 
                 txt_dir="data/processed", 
                 out_jsonl="data/corpus_limpio.jsonl"):
    
    print("Iniciando consolidación del corpus...")
    
    # 1. Cargar el registro base
    df_registry = pd.read_csv(registry_csv)
    
    # 2. Intentar cargar el archivo de idiomas (si ya se ejecutó clean_all.py)
    try:
        df_idiomas = pd.read_csv(idiomas_csv)
        df_completo = pd.merge(df_registry, df_idiomas, on="doc_id", how="left")
    except FileNotFoundError:
        print("Aviso: idiomas.csv no encontrado. Se asignará 'unknown'.")
        df_completo = df_registry.copy()
        df_completo["idioma"] = "unknown"

    # 3. Procesar e integrar los textos
    textos_procesados = 0
    txt_path_base = Path(txt_dir)
    
    with open(out_jsonl, 'w', encoding='utf-8') as f_out:
        for _, row in df_completo.iterrows():
            doc_id = row["doc_id"]
            archivo_txt = txt_path_base / f"{doc_id}.txt"
            
            # Verificar si la extracción de este documento fue exitosa
            if not archivo_txt.exists():
                continue
                
            texto_completo = archivo_txt.read_text(encoding="utf-8")
            
            # Construir el objeto con los metadatos obligatorios para la base vectorial
            doc_obj = {
                "doc_id": doc_id,
                "fuente": str(row["fuente"]),
                "formato": str(row["formato"]),
                "fenomeno": extraer_numero_fenomeno(row.get("fenomeno")),
                "idioma": str(row["idioma"]),
                "texto_completo": texto_completo
            }
            
            # Escribir la línea como JSON válido
            f_out.write(json.dumps(doc_obj, ensure_ascii=False) + '\n')
            textos_procesados += 1

    print(f"Corpus consolidado exitosamente. Se guardaron {textos_procesados} documentos en {out_jsonl}")

if __name__ == "__main__":
    build_corpus()