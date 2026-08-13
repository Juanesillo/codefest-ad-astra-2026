import pandas as pd


def extract_tabular(path: str) -> str:
    """
    Extrae texto de archivos CSV o XLSX, convirtiendo cada fila en una
    unidad de texto tipo "columna1: valor1, columna2: valor2...".
    Cada fila queda separada por un salto de línea doble, lo que permite
    tratarla como unidad de fragmentación independiente en el chunking.
    """
    if path.lower().endswith(".xlsx"):
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path, encoding="utf-8", on_bad_lines="skip")

    filas_texto = []
    for _, fila in df.iterrows():
        pares = []
        for columna, valor in fila.items():
            if pd.isna(valor) or str(valor).strip() == "":
                continue
            pares.append(f"{columna}: {valor}")
        if pares:
            filas_texto.append(", ".join(pares))

    return "\n\n".join(filas_texto)