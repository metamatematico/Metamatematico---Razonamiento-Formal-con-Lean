# METAMATEMÁTICO — Guía de Despliegue

## Comparación de opciones

| Plataforma | Lean 4 | GPU | Costo/mes | Dificultad | Recomendado para |
|---|---|---|---|---|---|
| **Hetzner CX31** (VPS) | ✅ completo | ❌ CPU | ~€10 | Media | Producción completa |
| **DigitalOcean 8GB** | ✅ completo | ❌ CPU | ~$48 | Media | Producción completa |
| **HuggingFace Spaces** | ❌ sin Lean | opcional T4 | $0–$50 | Baja | Demo pública |
| **RunPod A4000** | ✅ completo | ✅ GPU | ~$0.44/h | Media | Máximo rendimiento |
| **Streamlit Cloud** | ❌ | ❌ | $0 | Muy baja | ❌ No funciona (1GB RAM) |

## Opción A — VPS con Lean completo (recomendada)

### 1. Crear servidor en Hetzner

1. Registrarse en [hetzner.com/cloud](https://www.hetzner.com/cloud)
2. New Project → Add Server
3. Configuración:
   - **Imagen**: Ubuntu 22.04
   - **Tipo**: CX31 (4 vCPU, 8 GB RAM, 80 GB SSD) → €10.52/mes
   - **Ubicación**: Nuremberg o Helsinki (más rápido para Europa/LATAM)
   - **SSH key**: pegar tu clave pública

```bash
# Conectar al servidor
ssh root@<IP_DEL_SERVIDOR>

# Ejecutar script de instalación
curl -sSL https://raw.githubusercontent.com/metamatematico/Metamatematico---Razonamiento-Formal-con-Lean/main/deploy/setup_vps.sh | bash
```

### 2. Configurar API keys

```bash
nano /opt/metamat/.streamlit/secrets.toml
# Agregar:
# ANTHROPIC_API_KEY = "sk-ant-..."
# GOOGLE_API_KEY    = "AIza..."
# GROQ_API_KEY      = "gsk_..."
```

### 3. Dominio propio (opcional)

```bash
# Instalar certbot para HTTPS
apt install certbot python3-certbot-nginx -y
certbot --nginx -d tudominio.com
```

La app quedará en `http://<IP>` (o `https://tudominio.com` con HTTPS).

### Comandos de administración

```bash
systemctl status metamat      # estado
systemctl restart metamat     # reiniciar
journalctl -u metamat -f      # logs en vivo
cd /opt/metamat && git pull   # actualizar código
```

---

## Opción B — HuggingFace Spaces (demo gratuita, sin Lean)

### 1. Crear el Space

1. Ir a [huggingface.co/new-space](https://huggingface.co/new-space)
2. Configurar:
   - **Space name**: `metamatematico`
   - **SDK**: Docker
   - **Hardware**: CPU Basic (gratis) o T4 Small ($0.60/h)

### 2. Conectar repositorio

```bash
# En tu máquina local
git remote add hf https://huggingface.co/spaces/TU_USUARIO/metamatematico
git push hf main
```

### 3. Configurar secrets

En HuggingFace → Settings → Variables and secrets:
- `ANTHROPIC_API_KEY`
- `GOOGLE_API_KEY`
- `GROQ_API_KEY`

---

## Opción C — RunPod (GPU completa, pay-per-use)

1. Crear cuenta en [runpod.io](https://runpod.io)
2. Deploy → GPU Cloud
3. Template: PyTorch 2.2 + CUDA 12.1
4. GPU: RTX A4000 (~$0.44/h) o A10 (~$0.76/h)
5. En la terminal del pod:

```bash
git clone https://github.com/metamatematico/Metamatematico---Razonamiento-Formal-con-Lean.git
cd Metamatematico---Razonamiento-Formal-con-Lean
bash deploy/setup_vps.sh
```

Exponer el puerto 8501 en la configuración del pod.

---

## Tamaños de componentes a considerar

| Componente | Tamaño | Dónde |
|---|---|---|
| Código fuente | ~2 MB | GitHub (versionado) |
| Pesos GNN+PPO | ~2.2 MB | `data/neural_agent.json.pt` |
| Dependencias Python | ~4–6 GB | pip install |
| Lean 4 + elan | ~200 MB | elan install |
| **Mathlib compilado** | **~4–8 GB** | `lake update` |
| **Total disco mínimo** | **~15–20 GB** | — |
| RAM mínima (runtime) | ~2–3 GB | — |
| RAM recomendada | 8 GB | — |
