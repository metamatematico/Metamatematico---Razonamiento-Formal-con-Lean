# METAMATEMÁTICO — Guía de Despliegue

## Comparación de opciones (con opciones LATAM)

| Plataforma | Lean 4 | GPU | Costo/mes | LATAM | Recomendado para |
|---|---|---|---|---|---|
| **Vultr — Guadalajara MX** | ✅ completo | ❌ CPU | ~$24 | ✅ México | **LATAM producción** |
| **Vultr — São Paulo BR** | ✅ completo | ❌ CPU | ~$24 | ✅ Brasil | LATAM producción |
| **DigitalOcean — São Paulo** | ✅ completo | ❌ CPU | ~$48 | ✅ Brasil | Alternativa |
| **Hetzner CX31** | ✅ completo | ❌ CPU | ~€10 | ❌ EU/US | Europa |
| **HuggingFace Spaces** | ❌ sin Lean | opcional T4 | $0–$50 | ❌ | Demo pública |
| **RunPod A4000** | ✅ completo | ✅ GPU | ~$0.44/h | ❌ | Máximo rendimiento |
| **Streamlit Cloud** | ❌ | ❌ | $0 | ❌ | ❌ No funciona (1GB RAM) |

> **Nota Hetzner**: No tiene data centers en México ni América Latina. Para usuarios
> en México, la mejor opción es **Vultr Guadalajara** (el único proveedor mayor
> con nodo en territorio mexicano).

---

## Opción A — Vultr Guadalajara (recomendada para México/LATAM)

### 1. Crear servidor

1. Registrarse en [vultr.com](https://www.vultr.com) (tienen opción de pago en MXN)
2. **Deploy New Server** → **Cloud Compute — Optimized**
3. Configuración:
   - **Server Location**: Guadalajara, Mexico 🇲🇽
   - **Server Image**: Ubuntu 22.04 LTS x64
   - **Plan**: 8 GB RAM / 4 vCPU / 160 GB SSD → ~$24/mes
     *(mínimo recomendado para Lean + Mathlib)*
   - **Additional features**: Enable IPv6, Backups (opcional)
4. Anotar la IP del servidor en el dashboard

### 2. Conectar e instalar

```bash
# Conectar al servidor
ssh root@<IP_DEL_SERVIDOR>

# Instalación automática (tarda ~40 min, principalmente Mathlib)
curl -sSL https://raw.githubusercontent.com/metamatematico/\
Metamatematico---Razonamiento-Formal-con-Lean/main/deploy/setup_vps.sh | bash
```

### 3. Configurar API keys

```bash
nano /opt/metamat/.streamlit/secrets.toml
```

```toml
ANTHROPIC_API_KEY = "sk-ant-..."   # console.anthropic.com
GOOGLE_API_KEY    = "AIza..."      # aistudio.google.com (gratis)
GROQ_API_KEY      = "gsk_..."      # console.groq.com (gratis)
```

```bash
systemctl restart metamat
```

### 4. Dominio propio + HTTPS (opcional pero recomendado)

```bash
# Apuntar tu dominio a la IP en tu registrador (A record)
apt install certbot python3-certbot-nginx -y
certbot --nginx -d tudominio.com
```

La app queda en `https://tudominio.com`.

### Comandos de administración

```bash
systemctl status metamat      # estado del servicio
journalctl -u metamat -f      # logs en tiempo real
systemctl restart metamat     # reiniciar app
cd /opt/metamat && git pull && systemctl restart metamat  # actualizar
```

---

## Opción B — DigitalOcean São Paulo (alternativa LATAM)

1. [digitalocean.com](https://www.digitalocean.com) → Create Droplet
2. **Region**: São Paulo (BRA1)
3. **Plan**: 8 GB / 4 vCPU → $48/mes
4. Mismo script de instalación:

```bash
curl -sSL https://raw.githubusercontent.com/metamatematico/\
Metamatematico---Razonamiento-Formal-con-Lean/main/deploy/setup_vps.sh | bash
```

---

## Opción C — HuggingFace Spaces (demo pública gratuita, sin Lean)

1. [huggingface.co/new-space](https://huggingface.co/new-space)
   - SDK: **Docker**, Hardware: CPU Basic (gratis) o T4 ($0.60/h)
2. Conectar repo:
   ```bash
   git remote add hf https://huggingface.co/spaces/TU_USUARIO/metamatematico
   git push hf main
   ```
3. Secrets en HF → Settings → Variables and secrets:
   `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `GROQ_API_KEY`

> Sin Lean: el sistema funciona con GNN+PPO + LLM + MES.
> La verificación formal queda en modo "formalización pendiente".

---

## Tamaños de componentes

| Componente | Tamaño |
|---|---|
| Código fuente | ~2 MB |
| Pesos GNN+PPO (`data/*.pt`) | ~2.2 MB |
| Dependencias Python (con torch) | ~4–6 GB |
| Lean 4 + elan | ~200 MB |
| **Mathlib compilado** | **~4–8 GB** |
| **Total disco mínimo** | **~15–20 GB** |
| RAM mínima en runtime | ~2–3 GB |
| RAM recomendada | 8 GB |
