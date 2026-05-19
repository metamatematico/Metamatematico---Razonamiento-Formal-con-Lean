# ── METAMATEMÁTICO — Streamlit + Lean 4 completo ─────────────────────
# Imagen autocontenida: Python + Lean 4 + Mathlib + app Streamlit.
# Deploy en Railway / Render / Fly.io.
#
# Capas optimizadas para cache de Docker:
#   1. Sistema base  (raramente cambia)
#   2. elan + Lean   (cambia solo con lean-toolchain)
#   3. Mathlib cache (cambia solo con lake-manifest.json)
#   4. Python deps   (cambia solo con requirements.txt)
#   5. Código app    (cambia frecuentemente)
# ─────────────────────────────────────────────────────────────────────

FROM python:3.11-slim

# ── 1. Sistema base ───────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl wget build-essential ca-certificates \
    libssl-dev pkg-config procps \
    && rm -rf /var/lib/apt/lists/*

# ── 2. elan + Lean 4 ──────────────────────────────────────────────────
RUN curl -sSf https://elan.lean-lang.org/elan-init.sh \
    | sh -s -- -y --default-toolchain leanprover/lean4:stable
ENV PATH="/root/.elan/bin:${PATH}"

# ── 3. Mathlib: descarga oleans precompilados ─────────────────────────
# Copiar solo los archivos de proyecto Lean para que esta capa se
# invalide SOLO cuando cambia lakefile.toml o lake-manifest.json.
WORKDIR /app
COPY lakefile.toml lean-toolchain lake-manifest.json ./

# lake update: resuelve versiones, clona mathlib4 fuente
# lake exe cache get: descarga oleans precompilados (~500 MB comprimidos)
# lake build: compila solo los archivos del proyecto (rápido con cache)
RUN lake update \
    && (lake exe cache get && echo "Mathlib cache OK" \
        || echo "Sin cache — lake build compilará desde fuente (lento)") \
    && lake build || true

# ── 4. Python deps ────────────────────────────────────────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── 5. Código de la aplicación ────────────────────────────────────────
COPY . .

# Archivos Lean del proyecto (compilar si hay cambios)
RUN lake build || true

# ── Streamlit config ──────────────────────────────────────────────────
RUN mkdir -p /root/.streamlit
COPY deploy/streamlit_config.toml /root/.streamlit/config.toml

ENV PYTHONIOENCODING=utf-8
ENV PYTHONUNBUFFERED=1
EXPOSE 8501

HEALTHCHECK --interval=30s --timeout=10s --start-period=120s \
    CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--server.enableCORS=false", \
     "--server.enableXsrfProtection=false"]
