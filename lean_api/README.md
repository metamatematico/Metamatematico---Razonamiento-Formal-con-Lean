# Lean Verification Microservice

FastAPI service that runs Lean 4 + Mathlib and exposes a `/verify` endpoint.
The main Streamlit app calls it when Lean is not installed locally (e.g. Streamlit Cloud).

## Deploy en Railway (recomendado, gratis)

1. Ve a [railway.app](https://railway.app) → **New Project → Deploy from GitHub repo**
2. Selecciona este repositorio.
3. En **Settings → Source**, cambia **Root Directory** a `lean_api`.
4. Railway detecta el `Dockerfile` automáticamente.
5. El primer build tarda ~15-25 min (descarga Mathlib cache). Las builds siguientes son rápidas.
6. Copia la URL pública del servicio (ej: `https://lean-api-xxx.railway.app`).

## Configurar Streamlit Cloud

En tu app de Streamlit Cloud → **Settings → Secrets**, añade:

```toml
LEAN_VERIFY_URL = "https://lean-api-xxx.railway.app"
```

Eso es todo. La app detecta automáticamente que Lean no está instalado localmente
y llama al microservicio para verificar el código.

## Endpoints

| Método | Ruta      | Descripción                          |
|--------|-----------|--------------------------------------|
| GET    | /health   | Liveness probe                       |
| POST   | /verify   | Verifica código Lean 4               |

### POST /verify

```json
{
  "code": "import Mathlib.Tactic.Ring\ntheorem add_comm (a b : Nat) : a + b = b + a := by ring",
  "timeout": 60
}
```

Respuesta:
```json
{
  "stdout": "{\"severity\":\"information\",...}",
  "stderr": "",
  "returncode": 0
}
```
