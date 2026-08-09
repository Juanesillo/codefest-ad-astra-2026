# src/indexing/encoder.py
import numpy as np
import torch
from sentence_transformers import SentenceTransformer

MODEL_NAME = "BAAI/bge-m3"

_MODEL = None


def _pick_device() -> str:
    if torch.cuda.is_available():
        return "cuda"
    if torch.backends.mps.is_available():  # Apple Silicon (M1/M2/.../M5)
        return "mps"
    return "cpu"


def get_model() -> SentenceTransformer:
    """Carga el encoder una sola vez (cacheado en el módulo). Usa GPU
    (CUDA) o, en Mac Apple Silicon, el backend MPS si está disponible; si
    no, cae a CPU sin romperse — el mismo código sirve sin importar el
    hardware de quien lo corra."""
    global _MODEL
    if _MODEL is None:
        device = _pick_device()
        print(f"Cargando {MODEL_NAME} en device={device}...")
        _MODEL = SentenceTransformer(MODEL_NAME, device=device)
    return _MODEL


def encode_texts(textos: list[str], batch_size: int = 32) -> np.ndarray:
    """Codifica una lista de textos a embeddings normalizados a norma
    unitaria (para que la similitud coseno equivalga al producto interno,
    aprovechado por IndexFlatIP)."""
    if not textos:
        return np.empty((0, 1024), dtype="float32")
    model = get_model()
    embeddings = model.encode(
        textos,
        batch_size=batch_size,
        normalize_embeddings=True,
        show_progress_bar=True,
        convert_to_numpy=True,
    )
    return embeddings.astype("float32")
