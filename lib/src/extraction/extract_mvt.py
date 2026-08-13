# src/extraction/extract_mvt.py
import gzip
import mapbox_vector_tile


def extract_mvt(path: str) -> str:
    """
    Extrae texto de un Mapbox Vector Tile (.pbf servido como tile z/x/y).
    Recorre las capas y features, convirtiendo sus atributos en texto.
    """
    with open(path, "rb") as f:
        data = f.read()

    # algunos tiles vienen comprimidos con gzip
    try:
        data = gzip.decompress(data)
    except OSError:
        pass  # no estaba comprimido, seguir con los bytes originales

    try:
        tile = mapbox_vector_tile.decode(data)
    except Exception:
        return ""  # tile vacío o corrupto, no bloquear el pipeline

    partes = []
    for capa_nombre, capa in tile.items():
        for feature in capa.get("features", []):
            props = feature.get("properties", {})
            if not props:
                continue
            pares = [f"capa: {capa_nombre}"] + [f"{k}: {v}" for k, v in props.items()]
            partes.append(", ".join(pares))

    return "\n\n".join(partes)