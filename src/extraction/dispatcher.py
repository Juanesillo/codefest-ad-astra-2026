# src/extraction/dispatcher.py
import pandas as pd
from pathlib import Path
from tqdm import tqdm

from extract_pdf import extract_pdf
from extract_html import extract_html
from extract_json import extract_json
from extract_tabular import extract_tabular
from extract_image_ocr import extract_image
from extract_pbf import extract_pbf
from extract_mvt import extract_mvt


EXTRACTORS = {
    "pdf": extract_pdf,
    "html": extract_html,
    "htm": extract_html,
    "json": extract_json,
    "csv": extract_tabular,
    "xlsx": extract_tabular,
    "png": extract_image,
    "jpg": extract_image,
    "jpeg": extract_image,
    "avif": extract_image
    # "pbf" se maneja aparte con elegir_extractor_pbf(), no va aquí
}


def elegir_extractor_pbf(path: str):
    """
    Distingue entre PBF de OpenStreetMap (osmium) y Mapbox Vector Tiles
    (mvt), que comparten extensión pero tienen estructura interna distinta.
    Los vector tiles siguen el patrón de carpetas tiles/{z}/{x}/{y}.pbf.
    """
    if "/tiles/" in path.replace("\\", "/"):
        return extract_mvt
    return extract_pbf


def run_all(registry_csv="data/doc_registry.csv", out_dir="data/processed"):
    df = pd.read_csv(registry_csv)
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    errores = []
    exitosos = 0

    for _, row in tqdm(df.iterrows(), total=len(df), desc="Extrayendo"):
        formato = str(row["formato"]).lower()
        path = row["path"]

        if formato == "pbf":
            extractor = elegir_extractor_pbf(path)
        else:
            extractor = EXTRACTORS.get(formato)

        if extractor is None:
            errores.append((row["doc_id"], path, f"sin extractor para formato '{formato}'"))
            continue

        try:
            texto = extractor(path)
            if not texto or len(texto.strip()) == 0:
                errores.append((row["doc_id"], path, "texto vacío tras extracción"))
                continue

            out_path = Path(out_dir) / f"{row['doc_id']}.txt"
            out_path.write_text(texto, encoding="utf-8")
            exitosos += 1

        except Exception as e:
            errores.append((row["doc_id"], path, str(e)))

    print(f"\nExtraídos exitosamente: {exitosos}/{len(df)}")

    if errores:
        errores_df = pd.DataFrame(errores, columns=["doc_id", "path", "error"])
        errores_df.to_csv("data/extraction_errors.csv", index=False)
        print(f"Errores: {len(errores)} — ver data/extraction_errors.csv")


if __name__ == "__main__":
    run_all()