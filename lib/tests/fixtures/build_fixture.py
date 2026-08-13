# tests/fixtures/build_fixture.py
#
# Genera un corpus_limpio.jsonl de mentira, con el mismo esquema exacto
# que produce scripts/build_corpus.py, para poder desarrollar y probar
# el chunker y el encoder sin tener que esperar a que el equipo termine
# de procesar el corpus real. Cada documento cubre un caso puntual que
# el chunker tiene que manejar bien (ver la tabla en el plan).

import json

FIXTURE_JSONL_PATH = "tests/fixtures/corpus_fixture.jsonl"


def hacer_documentos_fixture() -> list[dict]:
    return [
        {
            "doc_id": "DOC-FIX-001",
            "fuente": "fixtures/f1_ia_defensa.pdf",
            "formato": "pdf",
            "fenomeno": 1,
            "idioma": "es",
            "texto_completo": (
                "El Sr. Gómez presentó el informe ante el comité el 3.5 de marzo. "
                "La inteligencia artificial se ha convertido en un factor central "
                "para la defensa nacional.\n\n"
                "El Dr. Ramírez explicó que EE.UU. y otros países han invertido "
                "fuertemente en sistemas autónomos. Sin embargo, persisten brechas "
                "importantes en la región.\n\n"
                "En conclusión, el uso de IA en entornos militares exige políticas "
                "claras. La colaboración entre universidades y el sector defensa "
                "resulta clave."
            ),
        },
        {
            "doc_id": "DOC-FIX-002",
            "fuente": "fixtures/f2_leo_debris.html",
            "formato": "html",
            "fenomeno": 2,
            "idioma": "en",
            "texto_completo": (
                "Low Earth Orbit congestion is a growing concern. Mr. Anderson "
                "noted that debris tracking has improved significantly.\n\n"
                "1. Satellite collisions increase orbital debris.\n"
                "2. Tracking systems need better funding.\n"
                "3. International cooperation remains limited.\n\n"
                "According to Dr. Lee, e.g. the Kessler syndrome illustrates the "
                "long-term risk. The U.S. and other spacefaring nations must "
                "coordinate closely."
            ),
        },
        {
            "doc_id": "DOC-FIX-003",
            "fuente": "fixtures/f3_dinamicas.json",
            "formato": "json",
            "fenomeno": 3,
            "idioma": "pt",
            "texto_completo": (
                "O Sr. Silva apresentou o relatório ontem. A reunião começou às "
                "15h.\n\n"
                "As dinâmicas territoriais na América Latina exigem atenção. "
                "O Dr. Costa destacou riscos de segurança na região."
            ),
        },
        {
            "doc_id": "DOC-FIX-004",
            "fuente": "fixtures/f1_equipo.csv",
            "formato": "csv",
            "fenomeno": 1,
            "idioma": "es",
            "texto_completo": (
                "nombre: Juan Pérez, edad: 34, cargo: analista\n\n"
                "nombre: Ana Torres, edad: 29, cargo: investigadora\n\n"
                "nombre: Luis Gómez, edad: 41, cargo: coordinador"
            ),
        },
        {
            "doc_id": "DOC-FIX-005",
            "fuente": "fixtures/f2_fila_gigante.xlsx",
            "formato": "xlsx",
            "fenomeno": 2,
            "idioma": "en",
            # una sola fila, sin puntuación, deliberadamente larga: debe
            # quedar como chunk "huérfano" en vez de partirse
            "texto_completo": "descripcion: " + ("orbital debris risk indicator " * 80),
        },
        {
            "doc_id": "DOC-FIX-006",
            "fuente": "fixtures/f1_fenomeno_roto.pdf",
            "formato": "pdf",
            "fenomeno": 0,  # simula el bug de inventory.py (ver README del plan)
            "idioma": "es",
            "texto_completo": (
                "Este documento simula un caso donde el campo fenómeno llegó mal "
                "calculado desde el registro. El chunker debe propagar el valor "
                "tal cual, sin intentar corregirlo."
            ),
        },
        {
            "doc_id": "DOC-FIX-007",
            "fuente": "fixtures/f1_una_oracion.html",
            "formato": "html",
            "fenomeno": 1,
            "idioma": "es",
            "texto_completo": "La inteligencia artificial transforma la defensa nacional.",
        },
        {
            "doc_id": "DOC-FIX-008",
            "fuente": "fixtures/f3_vacio.json",
            "formato": "json",
            "fenomeno": 3,
            "idioma": "en",
            "texto_completo": "",
        },
        {
            "doc_id": "DOC-FIX-009",
            "fuente": "fixtures/f2_ocr_ruidoso.png",
            "formato": "png",
            "fenomeno": 2,
            "idioma": "es",
            "texto_completo": (
                "[TEXTO DE IMAGEN/GRÁFICO]:\nSATELITE 2024 GRAFICO 1 datos de "
                "reentrada orbital fragmentos detectados 1200 aprox."
            ),
        },
        {
            "doc_id": "DOC-FIX-010",
            "fuente": "fixtures/f1_bloque_largo.pdf",
            "formato": "pdf",
            "fenomeno": 1,
            "idioma": "pt",
            "texto_completo": " ".join(
                f"A inteligência artificial avança no cenário {i} da defesa nacional."
                for i in range(1, 21)
            ),
        },
        {
            "doc_id": "DOC-FIX-011",
            "fuente": "fixtures/f2_mapa.pbf",
            "formato": "pbf",
            "fenomeno": 2,
            "idioma": "es",
            "texto_completo": (
                "tipo: node, name: Estacion Orbital, amenity: tracking_station\n\n"
                "tipo: way, name: Zona de Reentrada, landuse: restricted\n\n"
                "tipo: relation, name: Corredor Espacial, boundary: administrative"
            ),
        },
    ]


if __name__ == "__main__":
    documentos = hacer_documentos_fixture()
    with open(FIXTURE_JSONL_PATH, "w", encoding="utf-8") as f:
        for doc in documentos:
            f.write(json.dumps(doc, ensure_ascii=False) + "\n")
    print(f"Fixture generado: {len(documentos)} documentos en {FIXTURE_JSONL_PATH}")
