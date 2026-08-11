# index.faiss y metadata.jsonl — no están en git

Estos dos archivos pesan demasiado para GitHub (670 MB el índice, 296 MB
la metadata; 163,625 chunks), así que viven en Drive en vez de en el repo:

https://drive.google.com/drive/folders/1h1AdEjigBEWfruZlyr7VcYoIN9UTfGSa

**Pendiente**: la carpeta de Drive de arriba todavía está vacía. Falta que
alguien suba ahí los dos archivos generados (están en esta ruta local:
`entrega/base_vectorial/encoder_bge_m3/`).

Para bajarlos a esta carpeta (una vez estén subidos):

```bash
python scripts/fetch_base_vectorial.py
```

O manualmente: descargar `index.faiss` y `metadata.jsonl` del link de
arriba y colocarlos en esta misma carpeta (`entrega/base_vectorial/encoder_bge_m3/`).

`generador.py` los busca en esta ruta exacta.

Checksums (para verificar que la subida/descarga a Drive no corrompió los
archivos — Drive a veces trunca archivos grandes):

- `index.faiss`: sha256 = `bac47d34031332fb7e80c55f5fee0269b5ac7429560309324d9be313c7ee1375`
- `metadata.jsonl`: sha256 = `ae5bdaa675dbb8568cd2329c251ffc715aa8c23d00653979c3e7317b9a6ac188`
