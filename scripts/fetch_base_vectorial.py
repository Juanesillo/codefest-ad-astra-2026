# scripts/fetch_base_vectorial.py
"""Descarga index.faiss y metadata.jsonl desde la carpeta de Drive
compartida (demasiado pesados para GitHub) y los deja en
entrega/base_vectorial/encoder_<nombre>/, donde generador.py los espera.

Uso:
    python scripts/fetch_base_vectorial.py
"""
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = REPO_ROOT / "entrega/base_vectorial/encoder_bge_m3"


# https://drive.google.com/drive/folders/1h1AdEjigBEWfruZlyr7VcYoIN9UTfGSa
DRIVE_FOLDER_ID = "1h1AdEjigBEWfruZlyr7VcYoIN9UTfGSa"


def main():
    try:
        import gdown
    except ImportError:
        sys.exit(
            "Falta gdown. Instala con: pip install gdown\n"
            "(ya está listado en requeriments.txt)"
        )

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    gdown.download_folder(
        id=DRIVE_FOLDER_ID,
        output=str(OUT_DIR),
        quiet=False,
        use_cookies=False,
    )

    faltantes = [
        nombre for nombre in ("index.faiss", "metadata.jsonl")
        if not (OUT_DIR / nombre).exists()
    ]
    if faltantes:
        sys.exit(
            f"Descarga incompleta, faltan: {faltantes}. "
            f"Verifica que la carpeta de Drive tenga permisos de lectura "
            f"para tu cuenta."
        )
    print(f"OK: index.faiss y metadata.jsonl listos en {OUT_DIR}")


if __name__ == "__main__":
    main()
