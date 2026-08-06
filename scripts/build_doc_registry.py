# scripts/build_doc_registry.py
import pandas as pd
from pathlib import Path
import hashlib

def make_doc_id(index):
    return f"DOC-{index:04d}"

def build_registry(inventory_csv="data/inventory.csv"):
    df = pd.read_csv(inventory_csv)
    df = df.sort_values("path").reset_index(drop=True)
    df["doc_id"] = [make_doc_id(i) for i in range(len(df))]
    df["formato"] = df["extension"].str.replace(".", "", regex=False)
    df["fuente"] = df["path"].astype(str).str.replace("\\", "/", regex=False)  # ruta original, sirve como referencia
    df.to_csv("data/doc_registry.csv", index=False)
    return df

if __name__ == "__main__":
    build_registry()