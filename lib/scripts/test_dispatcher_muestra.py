# scripts/test_dispatcher_muestra.py
import pandas as pd
from src.extraction.dispatcher import run_all

df = pd.read_csv("data/doc_registry.csv")
df.sample(20, random_state=42).to_csv("data/doc_registry_muestra.csv", index=False)

run_all(registry_csv="data/doc_registry_muestra.csv", out_dir="data/processed_muestra")