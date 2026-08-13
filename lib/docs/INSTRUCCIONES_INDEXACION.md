# Instrucciones — Generar el índice FAISS (BAAI/bge-m3)

Este documento es para correr, en otra máquina, el paso que convierte los
163,625 chunks del corpus en un índice vectorial FAISS. No se corrió en la
máquina de desarrollo original porque no tiene GPU (4 núcleos CPU, sin
NVIDIA) y el encoder (`BAAI/bge-m3`, 568M parámetros) es demasiado pesado
para eso: medido en esa máquina, 10 chunks tardaron 196 segundos, lo que
proyecta a **~37 días** para el corpus completo en CPU puro.

**Plan A**: correr esto en el Mac (Apple Silicon M5, 16GB RAM) — tiene el
backend MPS de PyTorch, que acelera bastante frente a CPU puro. El código
ya lo detecta automáticamente.

**Plan B**: el notebook de Google Colab (`lib/notebooks/colab_build_faiss_index.ipynb`),
por si el Mac igual resulta lento o hay algún problema de dependencias —
Colab da GPU NVIDIA gratis y es totalmente autocontenido (no necesita
clonar el repo).

> Nota sobre rutas: el repo está organizado en `entrega/` (el paquete que se
> entrega tal cual, sin tocar) y `lib/` (todo el código y datos de trabajo del
> equipo). Los comandos de este documento asumen que ya hiciste `cd lib/`
> después de clonar/actualizar el repo — así las rutas relativas a `data/`
> coinciden con las que usa el código, y `entrega/` queda un nivel arriba
> (`../entrega/...`).

## 0. Qué vas a producir

Dos archivos:
- `entrega/base_vectorial/encoder_bge_m3/index.faiss` (~650-700 MB)
- `entrega/base_vectorial/encoder_bge_m3/metadata.jsonl` (~300 MB)

---

## Plan A — Correrlo en el Mac (M5)

### 1. Clonar / actualizar el repo

```bash
git clone git@github.com:Juanesillo/codefest-ad-astra-2026.git
cd codefest-ad-astra-2026
# o si ya lo tenías clonado:
git pull
# a partir de acá, todos los comandos de este documento se corren desde lib/:
cd lib
```

### 2. Conseguir `data/chunks/chunks.jsonl`

Este archivo **no viene en git** (pesa ~296 MB, está en `.gitignore`). Te lo
tienen que pasar por fuera (Drive, WeTransfer, USB, etc.) — comprime bien
con gzip antes de mandarlo:

```bash
# quien lo manda:
gzip -k data/chunks/chunks.jsonl   # genera chunks.jsonl.gz, mucho más chico

# quien lo recibe, después de bajarlo:
mkdir -p data/chunks
gunzip -c chunks.jsonl.gz > data/chunks/chunks.jsonl
```

Verifica que quedó completo (debe decir 163625):

```bash
wc -l data/chunks/chunks.jsonl
```

### 3. Preparar el entorno Python

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requeriments.txt
```

En Mac no hace falta nada especial para MPS — viene incluido en el `torch`
normal de PyPI para macOS.

### 4. Prueba rápida ANTES del corpus completo

```bash
python -c "from src.indexing.build_index import run; run(limit=20)"
```

Y confirma que está usando MPS (no CPU):

```bash
python -c "
import torch
print('MPS disponible:', torch.backends.mps.is_available())
"
```

Debe decir `True`. Si el paso anterior (`run(limit=20)`) tardó más de 1-2
minutos, algo no está usando MPS y hay que revisar antes de seguir — avísame.

### 5. Correr la indexación completa

```bash
python scripts/build_faiss_index.py
```

Esto:
1. Descarga el modelo `BAAI/bge-m3` la primera vez (~2.2 GB).
2. Lee los 163,625 chunks de `data/chunks/chunks.jsonl` en lotes.
3. Genera un embedding (vector de 1024 números) por cada chunk.
4. Los guarda en un índice FAISS y escribe la metadata correspondiente.

Con MPS en un M5 debería ser cuestión de minutos a un par de horas (no
tengo un número medido exacto para MPS — si el paso 4 dio un tiempo
razonable, esto escala proporcionalmente). Se puede dejar corriendo en
segundo plano: `nohup python scripts/build_faiss_index.py &`.

### 6. Verificar el resultado

```bash
python -c "
import faiss
idx = faiss.read_index('../entrega/base_vectorial/encoder_bge_m3/index.faiss')
print('vectores en el índice:', idx.ntotal)
"
wc -l ../entrega/base_vectorial/encoder_bge_m3/metadata.jsonl
```

Ambos números deben ser **163625**.

### 7. Devolver los resultados

```bash
cd ../entrega/base_vectorial
tar -czf encoder_bge_m3.tar.gz encoder_bge_m3/
```

Sube `encoder_bge_m3.tar.gz` a Drive/WeTransfer y comparte el link (no por
git, es demasiado grande).

---

## Plan B — Google Colab (si el Plan A no funciona bien)

1. Sube `data/chunks/chunks.jsonl` (o el `.gz`) a una carpeta en Google
   Drive, por ejemplo `MyDrive/codefest/chunks.jsonl`.
2. Abre `lib/notebooks/colab_build_faiss_index.ipynb` en Google Colab
   (Archivo → Subir notebook, o directo desde el repo si lo subes a Drive).
3. Entorno de ejecución → Cambiar tipo de entorno de ejecución → **GPU**
   (T4 gratis alcanza).
4. Corre las celdas en orden. El notebook monta Drive, instala lo
   necesario, lee `chunks.jsonl` desde Drive, genera el índice y **guarda
   el resultado de vuelta en Drive** (`MyDrive/codefest/entrega_bge_m3/`).
5. Baja esa carpeta de Drive y ubícala en `entrega/base_vectorial/encoder_bge_m3/`
   en el repo local, o mándamela directo comprimida.
