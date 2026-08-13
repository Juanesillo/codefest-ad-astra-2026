# scripts/clean_all.py
from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.extraction.clean_text import clean_text, detect_language

def run():
    registry = pd.read_csv("data/doc_registry.csv")
    idiomas = []
    for _, row in registry.iterrows():
        path = Path("data/processed") / f"{row['doc_id']}.txt"
        if not path.exists():
            continue
        texto = path.read_text(encoding="utf-8")
        texto_limpio = clean_text(texto)
        path.write_text(texto_limpio, encoding="utf-8")
        idiomas.append({"doc_id": row["doc_id"], "idioma": detect_language(texto_limpio)})

    pd.DataFrame(idiomas).to_csv("data/idiomas.csv", index=False)

if __name__ == "__main__":
    run()