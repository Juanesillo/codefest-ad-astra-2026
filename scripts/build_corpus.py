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


def _normaliza_ruta(fuente) -> str:
    """Normaliza una ruta 'fuente' (data\\raw\\CODEFEST\\...) al mismo
    formato relativo usado por Indice_Datos_Codefest.xlsx (Carpeta +
    Nombre estandarizado, con '/' y sin el prefijo data/raw/CODEFEST/)."""
    ruta = str(fuente).replace("\\", "/")
    prefijo = "data/raw/CODEFEST/"
    if ruta.startswith(prefijo):
        ruta = ruta[len(prefijo):]
    return ruta


def cargar_mapa_doc_id_oficial(
    xlsx_path="data/raw/CODEFEST/Indice_Datos_Codefest.xlsx",
) -> dict:
    """Carga el mapeo ruta -> DOC_ID oficial desde la hoja 'Inventario de
    Archivos' de Indice_Datos_Codefest.xlsx.

    Confirmado por los organizadores en el FAQ: el emparejamiento contra el
    ground truth se hace por el DOC_ID oficial que asigna ADL en este
    archivo, NO por un doc_id inventado por el equipo. Cualquier documento
    que no aparezca en este inventario (ej. catálogos/registros auxiliares
    de scraping que ADL no considera "documentos" del corpus) se excluye
    del corpus."""
    df = pd.read_excel(xlsx_path, sheet_name="Inventario de Archivos")
    df["ruta_oficial"] = df["Carpeta"] + "/" + df["Nombre estandarizado"]
    return dict(zip(df["ruta_oficial"], df["DOC_ID"]))


def build_corpus(registry_csv="data/doc_registry.csv",
                 idiomas_csv="data/idiomas.csv",
                 txt_dir="data/processed",
                 out_jsonl="data/corpus_limpio.jsonl",
                 indice_oficial_xlsx="data/raw/CODEFEST/Indice_Datos_Codefest.xlsx"):

    print("Iniciando consolidación del corpus...")

    mapa_doc_id = cargar_mapa_doc_id_oficial(indice_oficial_xlsx)
    print(f"Mapa de DOC_ID oficial cargado: {len(mapa_doc_id)} documentos en el inventario de ADL.")

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
    sin_doc_id_oficial = 0
    txt_path_base = Path(txt_dir)

    with open(out_jsonl, 'w', encoding='utf-8') as f_out:
        for _, row in df_completo.iterrows():
            doc_id_interno = row["doc_id"]

            # filas sin formato (ej. .DS_Store) no deberían tener .txt real;
            # si lo tienen es basura de un doc_id reciclado en otra corrida
            if pd.isna(row.get("formato")):
                continue

            archivo_txt = txt_path_base / f"{doc_id_interno}.txt"
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

            # El doc_id que va al corpus (y de ahí a chunks/índice/resultados)
            # es el DOC_ID OFICIAL de ADL, no el doc_id interno que asignamos
            # nosotros al procesar. Si un archivo no está en el inventario
            # oficial (ej. catálogos/registros auxiliares de scraping que
            # ADL no considera "documentos"), se excluye del corpus: no hay
            # forma de emparejarlo contra el ground truth.
            ruta_normalizada = _normaliza_ruta(row.get("fuente"))
            doc_id_oficial = mapa_doc_id.get(ruta_normalizada)
            if doc_id_oficial is None:
                sin_doc_id_oficial += 1
                continue

            doc_obj = {
                "doc_id": doc_id_oficial,
                "fuente": str(row["fuente"]),
                "formato": str(row["formato"]),
                "fenomeno": fenomeno,
                "idioma": str(row["idioma"]),
                "texto_completo": texto_completo
            }

            f_out.write(json.dumps(doc_obj, ensure_ascii=False) + '\n')
            textos_procesados += 1

    print(f"Corpus consolidado exitosamente. Se guardaron {textos_procesados} documentos en {out_jsonl}")
    print(f"Excluidos por no tener DOC_ID oficial en el inventario de ADL: {sin_doc_id_oficial}")

if __name__ == "__main__":
    build_corpus()
