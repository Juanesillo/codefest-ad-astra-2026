# src/extraction/dispatcher.py
import pandas as pd
from pathlib import Path
from extract_pdf import extract_pdf
from extract_html import extract_html
from extract_json import extract_json
from extract_tabular import extract_tabular
from extract_image_ocr import extract_image
from extract_pbf import extract_pbf

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
    "pbf": extract_pbf,
}

def run_all(registry_csv="data/doc_registry.csv", out_dir="data/processed"):
    df = pd.read_csv(registry_csv)
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    errores = []

    for _, row in df.iterrows():
        extractor = EXTRACTORS.get(row["formato"])
        if extractor is None:
            errores.append((row["doc_id"], f"sin extractor para {row['formato']}"))
            continue
        try:
            texto = extractor(row["path"])
            out_path = Path(out_dir) / f"{row['doc_id']}.txt"
            out_path.write_text(texto, encoding="utf-8")
        except Exception as e:
            errores.append((row["doc_id"], str(e)))

    if errores:
        pd.DataFrame(errores, columns=["doc_id", "error"]).to_csv("data/extraction_errors.csv", index=False)
        print(f"{len(errores)} errores — ver data/extraction_errors.csv")

if __name__ == "__main__":
    run_all()