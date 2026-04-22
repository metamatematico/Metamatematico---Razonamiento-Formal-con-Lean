#!/bin/bash
# ══════════════════════════════════════════════════════════════════════
# setup_vps.sh — Instalación completa de METAMATEMÁTICO en VPS Ubuntu
# Testeado en: Ubuntu 22.04 LTS (Hetzner CX31 / DigitalOcean 8GB)
#
# Uso: bash deploy/setup_vps.sh
# ══════════════════════════════════════════════════════════════════════
set -e

APP_DIR="/opt/metamat"
REPO="https://github.com/metamatematico/Metamatematico---Razonamiento-Formal-con-Lean.git"
VENV="$APP_DIR/.venv"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║   METAMATEMÁTICO — Setup VPS                 ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ── 1. Sistema ────────────────────────────────────────────────────────
echo "[1/7] Actualizando sistema..."
apt-get update -q && apt-get upgrade -y -q
apt-get install -y -q git curl wget build-essential ca-certificates \
    libssl-dev pkg-config python3.10 python3.10-venv python3-pip nginx

# ── 2. Clonar repo ───────────────────────────────────────────────────
echo "[2/7] Clonando repositorio..."
if [ -d "$APP_DIR" ]; then
    cd "$APP_DIR" && git pull
else
    git clone "$REPO" "$APP_DIR"
fi
cd "$APP_DIR"

# ── 3. Python virtualenv ──────────────────────────────────────────────
echo "[3/7] Creando entorno Python..."
python3.10 -m venv "$VENV"
source "$VENV/bin/activate"
pip install --upgrade pip -q

# PyTorch CPU (para VPS sin GPU)
pip install torch==2.2.0 --index-url https://download.pytorch.org/whl/cpu -q
pip install torch-geometric==2.4.0 -q
pip install torch-scatter torch-sparse \
    -f https://data.pyg.org/whl/torch-2.2.0+cpu.html -q

# Resto de dependencias
pip install -r requirements.txt -q
echo "  ✔ Python OK"

# ── 4. Lean 4 + elan ─────────────────────────────────────────────────
echo "[4/7] Instalando Lean 4..."
if ! command -v lake &> /dev/null; then
    curl https://elan.lean-lang.org/elan-init.sh -sSf | \
        sh -s -- -y --default-toolchain leanprover/lean4:stable
    echo 'export PATH="$HOME/.elan/bin:$PATH"' >> /root/.bashrc
    export PATH="$HOME/.elan/bin:$PATH"
fi
echo "  ✔ Lean OK: $(lean --version 2>/dev/null || echo 'instalado')"

# ── 5. Mathlib ───────────────────────────────────────────────────────
echo "[5/7] Descargando Mathlib (puede tomar 20-30 min)..."
cd "$APP_DIR"
lake update
lake exe cache get || echo "  (cache no disponible, compilando desde fuente)"
echo "  ✔ Mathlib OK"

# ── 6. Secrets / API keys ────────────────────────────────────────────
echo "[6/7] Configurando secretos..."
SECRETS_DIR="$APP_DIR/.streamlit"
mkdir -p "$SECRETS_DIR"
if [ ! -f "$SECRETS_DIR/secrets.toml" ]; then
    cat > "$SECRETS_DIR/secrets.toml" << 'SECRETS'
# Agrega tus API keys aquí (no subas este archivo a git)
ANTHROPIC_API_KEY = ""
GOOGLE_API_KEY    = ""
GROQ_API_KEY      = ""
SECRETS
    echo "  ⚠ Edita $SECRETS_DIR/secrets.toml con tus API keys"
fi

# Copiar config de Streamlit
cp "$APP_DIR/deploy/streamlit_config.toml" "$SECRETS_DIR/config.toml"

# ── 7. Servicio systemd ───────────────────────────────────────────────
echo "[7/7] Creando servicio systemd..."
cat > /etc/systemd/system/metamat.service << SERVICE
[Unit]
Description=METAMATEMÁTICO — Núcleo Lógico Evolutivo
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$APP_DIR
Environment="PATH=$VENV/bin:/root/.elan/bin:/usr/local/bin:/usr/bin:/bin"
Environment="PYTHONIOENCODING=utf-8"
ExecStart=$VENV/bin/streamlit run app.py --server.port=8501 --server.headless=true
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable metamat
systemctl start metamat

# ── Nginx reverse proxy ───────────────────────────────────────────────
cat > /etc/nginx/sites-available/metamat << NGINX
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_read_timeout 86400;
    }
}
NGINX

ln -sf /etc/nginx/sites-available/metamat /etc/nginx/sites-enabled/
nginx -t && systemctl restart nginx

echo ""
echo "════════════════════════════════════════════════"
echo "✔ Instalación completa"
echo ""
echo "  App corriendo en: http://$(curl -s ifconfig.me)"
echo ""
echo "  Comandos útiles:"
echo "    systemctl status metamat    # estado del servicio"
echo "    journalctl -u metamat -f    # logs en vivo"
echo "    systemctl restart metamat   # reiniciar"
echo ""
echo "  API keys: edita $SECRETS_DIR/secrets.toml"
echo "════════════════════════════════════════════════"
