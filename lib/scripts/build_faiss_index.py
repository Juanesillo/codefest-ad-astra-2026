# scripts/build_faiss_index.py
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.indexing.build_index import run


def main():
    run()


if __name__ == "__main__":
    main()
