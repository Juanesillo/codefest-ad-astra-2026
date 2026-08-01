# scripts/inventory.py
import os
from pathlib import Path
import pandas as pd
from dotenv import load_dotenv

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Leer la variable de entorno para el directorio crudo, con un valor predeterminado si no está definida
ruta_env = os.getenv("DIRECTORIO_CRUDO", "data/raw/CODEFEST")
RAW_DIR = Path(ruta_env)

def build_inventory():
    rows = []
    for path in RAW_DIR.rglob("*"):
        if path.is_file():
            rows.append({
                "path": str(path),
                "extension": path.suffix.lower(),
                "size_kb": round(path.stat().st_size / 1024, 1),
                "fenomeno": path.parts[1] if len(path.parts) > 1 else None,
            })
    df = pd.DataFrame(rows)
    df.to_csv("data/inventory.csv", index=False)
    print(df.groupby(["fenomeno", "extension"]).size())
    print(f"\nTotal archivos: {len(df)}")
    return df

if __name__ == "__main__":
    build_inventory()