# CODEFEST · AD ASTRA 2026 — Etapa 1

Este repositorio está organizado en dos partes:

- **`entrega/`** — el paquete de entrega tal como lo exige la especificación
  técnica (Sección 1.4): `resultados.jsonl`, `generador.py`,
  `informe_tecnico.pdf` y `base_vectorial/` (índice FAISS, metadata y grafo
  de conocimiento). No depende de nada fuera de esta carpeta.
- **`lib/`** — todo el código y los datos de trabajo del equipo: extracción,
  limpieza, chunking, indexación, grafo, tests, notebooks y scripts
  auxiliares. Es donde se construyó todo lo que termina en `entrega/`.
  Ver [`lib/README.md`](lib/README.md) y [`lib/docs/`](lib/docs/) para la
  bitácora de decisiones y las instrucciones de indexación.
