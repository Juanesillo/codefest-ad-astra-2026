# index.faiss y metadata.jsonl — no están en git

Estos dos archivos pesan demasiado para GitHub (635 MB el índice, 282 MB
la metadata; 162,569 chunks), así que viven en Drive en vez de en el repo:

https://drive.google.com/drive/folders/1h1AdEjigBEWfruZlyr7VcYoIN9UTfGSa

**⚠️ Pendiente / IMPORTANTE**: la carpeta de Drive de arriba todavía está
vacía. Los checksums de abajo corresponden a la versión CORREGIDA (doc_id
oficial de ADL, ver Sección "DOC_ID oficial" más abajo) que hay que subir
— **no** a una versión previa de 163,625 chunks que circuló antes con
doc_id inventados por nosotros (esa versión está mal, no la suban).

Los dos archivos corregidos están en esta ruta local ahora mismo:
`entrega/base_vectorial/encoder_bge_m3/`.

Para bajarlos a esta carpeta (una vez estén subidos):

```bash
python scripts/fetch_base_vectorial.py
```

O manualmente: descargar `index.faiss` y `metadata.jsonl` del link de
arriba y colocarlos en esta misma carpeta (`entrega/base_vectorial/encoder_bge_m3/`).

`generador.py` los busca en esta ruta exacta.

## DOC_ID oficial

El organizador confirmó en el FAQ que el emparejamiento contra el ground
truth se hace por el `DOC_ID` que asigna ADL en `Indice_Datos_Codefest.xlsx`
(ej. `F1-AIINDEX-015`), no por un doc_id inventado por el equipo. Este
índice ya usa esos DOC_ID oficiales (ver `scripts/build_corpus.py`). Los 8
archivos del corpus que no aparecen en ese inventario oficial (catálogos y
registros auxiliares de scraping que ADL no considera "documentos") se
excluyeron.

Checksums (para verificar que la subida/descarga a Drive no corrompió los
archivos — Drive a veces trunca archivos grandes):

- `index.faiss` (162,569 vectores): sha256 = `43c226f6b1fc0c38926afdf4299e453c9dd004fe5663e8a1fbcb9966e048c3c6`
- `metadata.jsonl` (162,569 líneas): sha256 = `a4e9f211494a210036b824cd1f9c764e5c22e972ee9d1d30bbb8b171b8338627`
