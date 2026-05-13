# ── Lean 4 Verification Microservice ─────────────────────────────────
# Imagen Docker autocontenida con Lean 4 + Mathlib (cache precompilado).
# Deploy en Railway / Render / Fly.io; la app Streamlit lo llama via HTTP.
#
# Build time: ~15-25 min (primera vez; Railway cachea las capas).
# Imagen final: ~3-4 GB (Lean + Mathlib oleans + Python).
# ─────────────────────────────────────────────────────────────────────

FROM python:3.11-slim

# ── Sistema base ──────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git build-essential ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# ── elan + Lean 4 ─────────────────────────────────────────────────────
RUN curl -sSf https://elan.lean-lang.org/elan-init.sh \
    | sh -s -- -y --default-toolchain leanprover/lean4:stable
ENV PATH="/root/.elan/bin:${PATH}"

# ── Proyecto Lean mínimo con Mathlib ──────────────────────────────────
WORKDIR /lean_project
COPY lean_project/ .

# Descargar Mathlib (oleans precompilados via caché de Mathlib).
# lake update: resuelve versiones y clona mathlib4.
# lake exe cache get: descarga oleans precompilados (~500 MB) en vez de compilar.
# lake build: compila solo el proyecto propio (rápido con cache).
RUN lake update \
    && lake exe cache get \
    && echo "Mathlib cache downloaded" \
    || echo "cache get failed, lake build will compile from source (slow)"
RUN lake build || true

# ── FastAPI service ───────────────────────────────────────────────────
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY main.py .

ENV PYTHONIOENCODING=utf-8
ENV PYTHONUNBUFFERED=1
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
