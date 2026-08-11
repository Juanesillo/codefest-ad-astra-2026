import sys
from pathlib import Path

# permite importar "src.xxx" al correr pytest desde cualquier carpeta
sys.path.insert(0, str(Path(__file__).resolve().parent))
