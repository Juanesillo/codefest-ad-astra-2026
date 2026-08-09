# scripts/run_chunking.py
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.build_corpus import build_corpus
from src.chunking.chunker import run as run_chunker


def main():
    build_corpus()
    run_chunker()


if __name__ == "__main__":
    main()
