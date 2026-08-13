import osmium


class _HandlerAtributos(osmium.SimpleHandler):
    """
    Recorre un archivo PBF y extrae los atributos de cada elemento
    (nodos, ways, relaciones) como pares atributo:valor.
    Usa un set para no duplicar el mismo elemento en distintos niveles
    de zoom.
    """

    def __init__(self):
        super().__init__()
        self.vistos = set()
        self.textos = []

    def _procesar(self, obj, tipo):
        clave = (tipo, obj.id)
        if clave in self.vistos:
            return
        self.vistos.add(clave)

        pares = [f"tipo: {tipo}"]
        for tag in obj.tags:
            pares.append(f"{tag.k}: {tag.v}")

        if len(pares) > 1:  # solo guardar si tiene tags además del tipo
            self.textos.append(", ".join(pares))

    def node(self, n):
        self._procesar(n, "nodo")

    def way(self, w):
        self._procesar(w, "via")

    def relation(self, r):
        self._procesar(r, "relacion")


def extract_pbf(path: str) -> str:
    """
    Extrae texto de un archivo PBF (mapas), recorriendo sus capas y
    convirtiendo los atributos de cada elemento en texto plano.
    """
    handler = _HandlerAtributos()
    handler.apply_file(path)
    return "\n\n".join(handler.textos)