import pandas as pd
import json
import re
from pathlib import Path

def extraer_numero_fenomeno(fuente) -> int:
    """
    Extrae el número de fenómeno (1, 2 o 3) a partir de la carpeta raíz del
    archivo original en `fuente` (ej. 'F1_IA_y_Capacidades_Estrategicas' -> 1).

    Nota: la columna `fenomeno` de doc_registry.csv NO sirve para esto (es
    siempre el string fijo "raw", asignado en la etapa de inventario). El
    número real de fenómeno solo vive en la ruta `fuente`.
    """
    if pd.isna(fuente):
        return 0

    coincidencia = re.search(r"[Ff](\d+)_", str(fuente))
    if coincidencia:
        return int(coincidencia.group(1))
    return 0

def build_corpus(registry_csv="data/doc_registry.csv",
                 idiomas_csv="data/idiomas.csv",
                 txt_dir="data/processed",
                 out_jsonl="data/corpus_limpio.jsonl"):

    df_registry = pd.read_csv(registry_csv)

    # idiomas.csv solo existe si ya se corrió clean_all.py antes
    try:
        df_idiomas = pd.read_csv(idiomas_csv)
        df_completo = pd.merge(df_registry, df_idiomas, on="doc_id", how="left")
    except FileNotFoundError:
        print("idiomas.csv no encontrado, se asigna 'unknown'")
        df_completo = df_registry.copy()
        df_completo["idioma"] = "unknown"

    textos_procesados = 0
    txt_path_base = Path(txt_dir)

    with open(out_jsonl, 'w', encoding='utf-8') as f_out:
        for _, row in df_completo.iterrows():
            doc_id = row["doc_id"]

            # filas sin formato (ej. .DS_Store) no deberían tener .txt real;
            # si lo tienen es basura de un doc_id reciclado en otra corrida
            if pd.isna(row.get("formato")):
                continue

            archivo_txt = txt_path_base / f"{doc_id}.txt"
            if not archivo_txt.exists():
                continue

            texto_completo = archivo_txt.read_text(encoding="utf-8")
            if not texto_completo.strip():
                continue

            fenomeno = extraer_numero_fenomeno(row.get("fuente"))
            if fenomeno not in (1, 2, 3):
                # archivos fuera de F1/F2/F3 (ej. el banco de preguntas o el
                # índice de datos, sueltos en la raíz del corpus)
                continue

            doc_obj = {
                "doc_id": doc_id,
                "fuente": str(row["fuente"]),
                "formato": str(row["formato"]),
                "fenomeno": fenomeno,
                "idioma": str(row["idioma"]),
                "texto_completo": texto_completo
            }

            f_out.write(json.dumps(doc_obj, ensure_ascii=False) + '\n')
            textos_procesados += 1

    print(f"Corpus consolidado: {textos_procesados} documentos en {out_jsonl}")

if __name__ == "__main__":
    build_corpus()