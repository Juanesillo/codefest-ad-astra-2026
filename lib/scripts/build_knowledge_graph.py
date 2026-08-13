# scripts/build_knowledge_graph.py
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.graph.build_graph import build_graph


def main():
    build_graph()


if __name__ == "__main__":
    main()
