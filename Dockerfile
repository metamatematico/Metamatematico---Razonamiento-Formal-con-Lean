FROM python:3.10-slim

# ── Sistema base ──────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl wget build-essential ca-certificates \
    libssl-dev pkg-config procps \
    && rm -rf /var/lib/apt/lists/*

# ── Lean 4 (elan) ────────────────────────────────────────────────────
RUN curl https://elan.lean-lang.org/elan-init.sh -sSf | sh -s -- -y --default-toolchain leanprover/lean4:stable
ENV PATH="/root/.elan/bin:${PATH}"

# ── App ───────────────────────────────────────────────────────────────
WORKDIR /app
COPY . .

# ── Python deps (CPU torch para imagen más pequeña) ──────────────────
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
        torch==2.2.0 --index-url https://download.pytorch.org/whl/cpu && \
    pip install --no-cache-dir \
        torch-geometric==2.4.0 \
        torch-scatter torch-sparse -f https://data.pyg.org/whl/torch-2.2.0+cpu.html && \
    pip install --no-cache-dir -r requirements.txt

# ── Pre-descargar Mathlib (build en tiempo de imagen) ────────────────
# Esto puede tomar 20-30 min pero solo se hace una vez al hacer docker build
RUN cd /app && lake update && lake exe cache get || true

# ── Streamlit config ──────────────────────────────────────────────────
RUN mkdir -p /root/.streamlit
COPY deploy/streamlit_config.toml /root/.streamlit/config.toml

ENV PYTHONIOENCODING=utf-8
ENV PYTHONUNBUFFERED=1
EXPOSE 8501

HEALTHCHECK CMD curl -f http://localhost:8501/_stcore/health || exit 1

CMD ["streamlit", "run", "app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--server.enableCORS=false", \
     "--server.enableXsrfProtection=false"]
