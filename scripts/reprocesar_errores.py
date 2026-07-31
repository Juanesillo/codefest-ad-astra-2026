# scripts/reprocesar_errores.py
import pandas as pd
from src.extraction.dispatcher import run_all

errores = pd.read_csv("data/extraction_errors.csv")
registry = pd.read_csv("data/doc_registry.csv")

# quedarse solo con las filas del registro que fallaron
registry_fallidos = registry[registry["doc_id"].isin(errores["doc_id"])]
registry_fallidos.to_csv("data/doc_registry_reintentos.csv", index=False)

run_all(registry_csv="data/doc_registry_reintentos.csv", out_dir="data/processed")