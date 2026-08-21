"""
METAMATEMÁTICO — Núcleo Lógico Evolutivo
Asistente de razonamiento formal y demostracion de teoremas.
BIOMAT Centro de Biomatemáticas.
"""

import streamlit as st
import json
import re
import time
import sys
import os
import threading
from datetime import datetime

# Forzar UTF-8 globalmente — necesario en Streamlit Cloud (Linux, locale ASCII).
# Debe ir ANTES de cualquier import que use logging o I/O.
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
os.environ.setdefault("PYTHONUTF8", "1")

for _stream in (sys.stdout, sys.stderr):
    try:
        if _stream and hasattr(_stream, "reconfigure"):
            _stream.reconfigure(encoding="utf-8", errors="replace")
    except OSError:
        pass

import logging as _logging
import io as _io

def _fix_logging_utf8() -> None:
    """Reconfigura todos los StreamHandlers del logger raíz para usar UTF-8."""
    for _h in _logging.root.handlers:
        if isinstance(_h, _logging.StreamHandler):
            try:
                if hasattr(_h.stream, "reconfigure"):
                    _h.stream.reconfigure(encoding="utf-8", errors="replace")
                elif hasattr(_h, "setStream"):
                    # Python < 3.11: reemplazar el stream por un wrapper UTF-8
                    _h.setStream(_io.TextIOWrapper(
                        _h.stream.buffer if hasattr(_h.stream, "buffer") else _io.BytesIO(),
                        encoding="utf-8", errors="replace", line_buffering=True,
                    ))
            except Exception:
                pass
    # Handler por defecto si no hay ninguno configurado
    if not _logging.root.handlers:
        _h = _logging.StreamHandler(sys.stderr)
        _h.setFormatter(_logging.Formatter("%(levelname)s:%(name)s:%(message)s"))
        _logging.root.addHandler(_h)

_fix_logging_utf8()

# Nivel de log: sin esto el logger raiz se queda en WARNING y los logger.info
# del nucleo (warmup, carga de pesos, decisiones de los CRs) nunca se escriben,
# dejando el fichero de log vacio. Configurable con NLE_LOG_LEVEL.
_logging.root.setLevel(
    getattr(_logging, os.environ.get("NLE_LOG_LEVEL", "INFO").upper(), _logging.INFO)
)
# Las librerias de red son ruidosas en DEBUG y tapan la traza del nucleo.
for _noisy in ("httpcore", "urllib3", "anthropic", "watchdog", "PIL",
               "fontTools", "fpdf", "matplotlib", "asyncio", "streamlit"):
    _logging.getLogger(_noisy).setLevel(_logging.WARNING)
# httpx se queda en INFO a proposito: su linea por peticion es la unica señal
# de que el LLM se llamo de verdad, y silenciarla deja la traza ciega.
_logging.getLogger("httpx").setLevel(_logging.INFO)

# Logger de modulo: lo usan tanto _init_nucleo como el hilo de warmup, que
# corre fuera de cualquier funcion. Definirlo solo dentro de _init_nucleo
# dejaba al warmup sin `log` y su NameError se comia el centinela .lean_warm.
log = _logging.getLogger(__name__)


def _explica_error_proveedor(err) -> tuple[str, bool]:
    """
    Traduce un error de la API del proveedor a algo legible.

    Devuelve (mensaje_markdown, es_de_cuenta). "De cuenta" significa que el
    fallo es de saldo, clave o permisos: reintentar con el mismo proveedor
    volveria a fallar exactamente igual, asi que la UI debe parar ahi en vez
    de repetir la llamada y enseñar el mismo error dos veces.
    """
    bruto = str(err)
    b = bruto.lower()

    if "credit balance is too low" in b or "billing" in b:
        return (
            "**Saldo agotado en Anthropic.** La API rechazó la petición porque "
            "la cuenta no tiene crédito suficiente.\n\n"
            "- Recarga en **console.anthropic.com → Plans & Billing**, o\n"
            "- cambia de proveedor en la barra lateral: **Groq** y **Google AI "
            "Studio** tienen nivel gratuito.\n\n"
            "El resto del sistema está bien: Lean y el grafo no dependen de esto.",
            True,
        )
    if "authentication_error" in b or "invalid x-api-key" in b or "invalid api key" in b:
        return (
            "**La clave de API no es válida.** Revísala en la barra lateral: "
            "suele ser una clave incompleta al pegarla, o de otro proveedor.",
            True,
        )
    if "permission" in b or "403" in b:
        return (
            "**La clave no tiene permiso** para el modelo elegido. Prueba con "
            "otro modelo de la lista.",
            True,
        )
    if "rate_limit" in b or "429" in b:
        return (
            "**Límite de peticiones alcanzado.** Espera unos segundos y "
            "reenvía la consulta.",
            False,
        )
    if "overloaded" in b or "529" in b:
        return (
            "**El proveedor está saturado** en este momento. Reintenta en unos "
            "segundos o cambia de modelo.",
            False,
        )
    if "not_found" in b or "model" in b and "does not exist" in b:
        return (
            "**Modelo no disponible** para esta cuenta. Elige otro en la barra "
            "lateral.",
            True,
        )
    return (f"El Núcleo encontró un error: {bruto}", False)

# Asegurar que el paquete nucleo sea importable desde el directorio del proyecto
_proj_dir = os.path.dirname(os.path.abspath(__file__))
if _proj_dir not in sys.path:
    sys.path.insert(0, _proj_dir)


import subprocess

# ── Utilidades de actualización ───────────────────────────────────────────────

def _git_run(*args, cwd=None) -> tuple[int, str]:
    """Ejecuta un comando git y retorna (returncode, stdout+stderr)."""
    try:
        r = subprocess.run(
            ["git"] + list(args),
            cwd=cwd or _proj_dir,
            capture_output=True, text=True, timeout=30,
            encoding="utf-8", errors="replace",
        )
        return r.returncode, (r.stdout + r.stderr).strip()
    except Exception as e:
        return 1, str(e)


@st.cache_data(ttl=300)   # refresca cada 5 min
def _check_updates() -> dict:
    """Consulta GitHub para ver si hay commits nuevos. Cache 5 min."""
    # Versión local
    _, local_sha  = _git_run("rev-parse", "--short", "HEAD")
    _, local_msg  = _git_run("log", "--oneline", "-1")

    # Fetch silencioso
    _git_run("fetch", "origin", "main")

    # Commits adelante de origin/main
    _, ahead_behind = _git_run("rev-list", "--left-right", "--count",
                               "HEAD...origin/main")
    try:
        behind = int(ahead_behind.split()[-1])
    except Exception:
        behind = 0

    # Lista de commits nuevos (si los hay)
    _, new_commits = _git_run("log", "HEAD..origin/main", "--oneline")

    return {
        "sha":         local_sha[:7],
        "local_msg":   local_msg,
        "behind":      behind,
        "new_commits": new_commits,
    }


def _do_update() -> tuple[bool, str]:
    """Ejecuta git pull + pip install -r requirements.txt."""
    code1, out1 = _git_run("pull", "origin", "main")
    if code1 != 0:
        return False, f"git pull falló:\n{out1}"

    try:
        req = os.path.join(_proj_dir, "requirements.txt")
        r = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", req, "-q"],
            capture_output=True, text=True, timeout=120,
            encoding="utf-8", errors="replace",
        )
        pip_out = (r.stdout + r.stderr).strip()
    except Exception as e:
        pip_out = str(e)

    return True, f"{out1}\n\n{pip_out}".strip()


@st.cache_resource(show_spinner="Iniciando Núcleo Lógico Evolutivo…")
def _init_nucleo():
    """Inicializa el Nucleo y devuelve (instancia_o_None, error_str).

    Runs initialize() in a daemon thread with its own event loop so it
    never conflicts with Streamlit's own asyncio loop (Python 3.14).
    """
    import traceback, logging, threading, asyncio
    try:
        from nucleo.core import Nucleo
        from nucleo.config import NucleoConfig
        _cfg_yaml = os.path.join(_proj_dir, "nucleo_config.yaml")
        _cfg = NucleoConfig.from_yaml(_cfg_yaml) if os.path.exists(_cfg_yaml) else NucleoConfig()
        n = Nucleo(_cfg)

        error_holder: list[str] = []

        def _worker():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(n.initialize())
            except BaseException:
                error_holder.append(traceback.format_exc())
            finally:
                loop.close()

        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        t.join(timeout=20)

        if t.is_alive():
            return None, "Timeout: initialize() tardó más de 20 s"
        if error_holder:
            return None, error_holder[0]

        # El precalentamiento de Lean ya NO se lanza desde aqui: vive en
        # _arranca_warmup_lean(), que se dispara al renderizar la pagina para
        # que Mathlib empiece a cargarse en cuanto se abre la app, sin esperar
        # a que el usuario escriba nada.
        return n, ""
    except Exception:
        err = traceback.format_exc()
        log.warning("Nucleo no disponible:\n%s", err)
        return None, err


def _get_nucleo():
    nucleo, _ = _init_nucleo()
    return nucleo


def _get_nucleo_error() -> str:
    _, err = _init_nucleo()
    return err


@st.cache_resource(show_spinner=False)
def _arranca_warmup_lean() -> bool:
    """
    Lanza el precalentamiento de Mathlib al abrir la app.

    Antes esto colgaba de _init_nucleo(), que solo se invoca al procesar una
    consulta: el usuario abria la app, escribia, y solo ENTONCES empezaba a
    cargarse Mathlib — con lo que su primera consulta competia por el disco
    con el propio warmup y habia que reenviarla. Aqui no se necesita el
    Nucleo: basta LeanClient para conocer el ejecutable, el proyecto y el
    header. @st.cache_resource garantiza un unico arranque por proceso,
    aunque Streamlit re-ejecute el script en cada interaccion.

    Calienta EXACTAMENTE los modulos que LeanClient._SAFE_HEADER inyecta en
    cada consulta: `import Mathlib.Tactic` cargaba mucho mas de lo necesario
    sin cubrir lo que las consultas piden de verdad.
    """
    try:
        from nucleo.lean.client import LeanClient
        cliente = LeanClient()
        lean_exe    = cliente.lean_path
        lean_cwd    = str(cliente.project_path)
        warm_header = cliente._SAFE_HEADER
    except Exception as e:
        log.info(f"No se pudo preparar el warmup de Lean (no critico): {e}")
        return False

    # La cache del SO se pierde al reiniciar, asi que un centinela viejo miente.
    # Se borra al arrancar y solo lo reescribe el warmup al terminar:
    # existe .lean_warm  <=>  el warmup completo EN ESTE proceso.
    try:
        os.remove(os.path.join(lean_cwd, ".lean_warm"))
    except OSError:
        pass

    def _lean_warmup():
        import subprocess, time, pathlib
        warmup_file = pathlib.Path(lean_cwd) / "_nle_warmup.lean"
        warmup_file.write_text(
            warm_header + "\ntheorem _nle_warmup : (1 : ℕ) + 1 = 2 := by norm_num\n",
            encoding="utf-8",
        )
        t0 = time.perf_counter()
        try:
            proc = subprocess.run(
                [lean_exe, "env", "lean", str(warmup_file), "--json"],
                cwd=lean_cwd,
                capture_output=True,
                timeout=1080,  # 18 min — mas que los ~12 min medidos en frio
            )
            elapsed = time.perf_counter() - t0
            # El centinela se escribe ANTES de registrar nada: es la unica
            # senal de que Mathlib esta caliente, y la UI bloquea las consultas
            # mientras no exista. Si el log falla, Lean ya cargo igualmente y
            # seria absurdo perder ese trabajo.
            pathlib.Path(lean_cwd, ".lean_warm").write_text(
                f"{elapsed:.0f}", encoding="utf-8"
            )
            log.info(
                f"Lean warmup completado en {elapsed:.0f}s — "
                f"Mathlib en cache del SO (exit {proc.returncode})"
            )
        except subprocess.TimeoutExpired:
            log.warning("Lean warmup excedio 18 min — se cancela")
        except Exception as e:
            log.info(f"Lean warmup error (no critico): {e}")
        finally:
            warmup_file.unlink(missing_ok=True)

    threading.Thread(target=_lean_warmup, daemon=True, name="lean-warmup").start()
    return True

st.set_page_config(
    page_title="METAMATEMÁTICO",
    page_icon="🧮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Mathlib empieza a cargarse AQUI, al abrir la app, no al escribir la primera
# consulta. Es una llamada no bloqueante: solo arranca el hilo y sigue.
_arranca_warmup_lean()

# ── Modelos ───────────────────────────────────────────────────────────────────

PROVIDERS = {
    "Anthropic": {
        "models": [
            "claude-sonnet-5",
            "claude-opus-5",
            "claude-haiku-4-5-20251001",
            "claude-sonnet-4-6",
        ],
        "key_label": "Anthropic API Key",
        "key_placeholder": "sk-ant-...",
        "key_help": "Obtener en console.anthropic.com",
    },
    "Google AI Studio": {
        "models": [
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-1.5-flash",
            "gemini-1.5-pro",
        ],
        "key_label": "Google AI Studio API Key",
        "key_placeholder": "AIza...",
        "key_help": "Obtener gratis en aistudio.google.com",
    },
    "Groq (gratis)": {
        "models": [
            "llama-3.3-70b-versatile",
            "gemma2-9b-it",
            "mixtral-8x7b-32768",
            "llama-3.1-8b-instant",
        ],
        "key_label": "Groq API Key",
        "key_placeholder": "gsk_...",
        "key_help": "Obtener gratis en console.groq.com",
    },
    "DeepSeek": {
        "models": [
            "deepseek-chat",
            "deepseek-reasoner",
        ],
        "key_label": "DeepSeek API Key",
        "key_placeholder": "sk-...",
        "key_help": "Obtener en platform.deepseek.com",
    },
    "Demo (sin API key)": {
        "models": ["demo"],
        "key_label": None,
        "key_placeholder": None,
    },
}

SYSTEM_PROMPT = """Eres un asistente experto en matematicas formales y demostracion de teoremas.

Cuando respondas:
- Explica con claridad y precision matematica
- Usa notacion estandar cuando sea util
- Si es relevante, incluye codigo Lean 4 con tacticas como simp, ring, omega, linarith, induction
- Conecta los conceptos con sus fundamentos (conjuntos, categorias, logica, tipos)

INTEGRIDAD MATEMATICA — CRITICO:
- Si el usuario corrige algo, verifica primero si la correccion es matematicamente correcta antes de aceptarla.
- Nunca abandones una afirmacion correcta por presion social. Si tu respuesta era correcta, defiendela.
- Al reformular una definicion, comprueba que TODOS los tipos/firmas sean consistentes entre si.
  Ejemplo: si eval : B^A x A -> B, entonces el exponencial involucrado es B^A, no C^A.
- En teoria de categorias cartesianamente cerradas (CCC):
  eval : B^A x A -> B (evaluacion; el primer factor es el EXPONENCIAL B^A)
  curry : Hom(C x A, B) -> Hom(C, B^A)  (adjuncion)
  El exponencial siempre lleva el nombre del CODOMINIO como base, no del parametro C.

Responde de forma concisa y estructurada."""

# ── Clasificacion ligera ──────────────────────────────────────────────────────

def classify(query: str) -> dict:
    q = query.lower()
    lean_kw = ["lean", "tactic", "theorem", "lemma", "simp", "ring", "omega",
               "induction", "exact", "apply", "def ", "by "]
    is_lean = any(k in q for k in lean_kw)

    tactic_hints = {
        r"\bn\s*[+\-]\d|\d\s*[+\-]\s*\bn": "omega / linarith",
        r"\*|producto|multiplicaci": "ring / nlinarith",
        r"=\s*\d+$|^\d+\s*=": "rfl / norm_num",
        r"∀|forall|para todo": "intro / apply",
        r"∃|exists|existe": "use / exact ⟨_,_⟩",
        r"succ|Nat\.": "induction / omega",
    }
    tactic = "simp"
    for pat, t in tactic_hints.items():
        if re.search(pat, q, re.I):
            tactic = t
            break

    return {"is_lean": is_lean, "tactic": tactic}


def enrich(query: str, info: dict) -> str:
    if info["is_lean"]:
        return (
            f"[Contexto: goal Lean 4 — tactica sugerida: {info['tactic']}]\n\n"
            + query
        )
    return query


# ── Llamadas a modelos ────────────────────────────────────────────────────────

def call_google(prompt: str, model: str, api_key: str, max_tokens: int) -> dict:
    try:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=api_key)
        resp = client.models.generate_content(
            model=model,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_PROMPT,
                max_output_tokens=max_tokens,
                temperature=0.7,
            ),
        )
        text = resp.text
        usage = getattr(resp, "usage_metadata", None)
        return {
            "content": text,
            "model": model,
            "in_tok": getattr(usage, "prompt_token_count", 0),
            "out_tok": getattr(usage, "candidates_token_count", 0),
            "error": None,
        }
    except ImportError:
        return {"content": "", "error": "Instala: pip install google-genai"}
    except Exception as e:
        return {"content": "", "error": str(e)}


def call_groq(prompt: str, model: str, api_key: str, max_tokens: int) -> dict:
    try:
        from groq import Groq
        client = Groq(api_key=api_key)
        r = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.7,
        )
        u = r.usage
        return {
            "content": r.choices[0].message.content,
            "model": r.model,
            "in_tok": u.prompt_tokens if u else 0,
            "out_tok": u.completion_tokens if u else 0,
            "error": None,
        }
    except ImportError:
        return {"content": "", "error": "Instala: pip install groq"}
    except Exception as e:
        return {"content": "", "error": str(e)}


def call_anthropic(prompt: str, model: str, api_key: str, max_tokens: int) -> dict:
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        r = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )
        return {
            # Con pensamiento adaptativo el primer bloque es un ThinkingBlock
            # (sin .text); hay que quedarse con el bloque de tipo "text".
            "content": next((b.text for b in r.content if b.type == "text"), ""),
            "model": r.model,
            "in_tok": r.usage.input_tokens,
            "out_tok": r.usage.output_tokens,
            "error": None,
        }
    except ImportError:
        return {"content": "", "error": "Instala: pip install anthropic"}
    except Exception as e:
        return {"content": "", "error": str(e)}


def call_deepseek(prompt: str, model: str, api_key: str, max_tokens: int) -> dict:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        kwargs: dict = dict(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
            max_tokens=max_tokens,
            stream=False,
        )
        if "reasoner" not in model:
            kwargs["temperature"] = 0.7
        r = client.chat.completions.create(**kwargs)
        u = r.usage
        return {
            "content": r.choices[0].message.content or "",
            "model": r.model,
            "in_tok": u.prompt_tokens if u else 0,
            "out_tok": u.completion_tokens if u else 0,
            "error": None,
        }
    except ImportError:
        return {"content": "", "error": "Instala: pip install openai"}
    except Exception as e:
        return {"content": "", "error": str(e)}



def call_demo(query: str, info: dict) -> dict:
    if info["is_lean"]:
        text = (
            "Para este goal en Lean 4, las tacticas recomendadas son:\n\n"
            f"```lean4\n-- Núcleo Lógico Evolutivo\n"
            f"by\n  {info['tactic'].split('/')[0].strip()}  -- primer intento\n"
            f"  <;> simp [*]             -- simplificacion general\n"
            f"  <;> omega                -- aritmetica lineal\n```\n\n"
            "El sistema prueba en orden: `rfl → simp → ring → linarith → omega → aesop`"
        )
    else:
        text = (
            "**Modo demo** — conecta un modelo real para obtener respuestas completas.\n\n"
            "Este sistema analiza tu consulta matematica, identifica el area de conocimiento "
            "relevante y enriquece el contexto antes de enviarlo al modelo. "
            "Soporta consultas sobre teoria de conjuntos, categorias, logica formal y Lean 4."
        )
    return {"content": text, "model": "demo", "in_tok": 0, "out_tok": 0, "error": None}


# ── Helpers para adjuntos de archivo ─────────────────────────────────────────

def _extract_file_text(uploaded_file) -> str:
    """Extrae texto de un archivo subido (txt, tex, latex, pdf)."""
    name = uploaded_file.name.lower()
    if name.endswith(".pdf"):
        try:
            import fitz  # PyMuPDF
            raw = uploaded_file.read()
            doc = fitz.open(stream=raw, filetype="pdf")
            return "\n".join(page.get_text() for page in doc)
        except ImportError:
            return "[Error: instala PyMuPDF → pip install pymupdf]"
        except Exception as e:
            return f"[Error al leer PDF: {e}]"
    else:  # txt / tex / latex
        raw = uploaded_file.read()
        for enc in ("utf-8", "utf-8-sig", "latin-1"):
            try:
                return raw.decode(enc)
            except UnicodeDecodeError:
                continue
        return raw.decode("latin-1", errors="replace")


def _build_file_verify_prompt(text: str, filename: str) -> str:
    """Construye prompt de verificación para contenido matemático de un archivo."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "txt"
    is_latex = ext in ("tex", "latex") or "\\begin{" in text[:500] or "\\theorem" in text[:500]
    type_label = "LaTeX matemático" if is_latex else "texto matemático"

    max_chars = 3500
    excerpt = text[:max_chars] + ("\n\n[… contenido truncado …]" if len(text) > max_chars else "")

    return (
        f"El usuario ha subido el archivo `{filename}` con el siguiente {type_label}:\n\n"
        f"```\n{excerpt}\n```\n\n"
        "Analiza el contenido y:\n"
        "1. Identifica si contiene teoremas, lemas, demostraciones o conjeturas.\n"
        "2. Verifica la corrección lógica y matemática.\n"
        "3. Si hay una demostración, evalúa si es válida y señala posibles errores.\n"
        "4. Si es una conjetura, evalúa su plausibilidad y sugiere estrategias de demostración.\n"
        "5. Sugiere cómo formalizarlo en Lean 4 si es pertinente.\n"
        "6. Da un veredicto final: ✅ Correcto, ⚠️ Parcialmente correcto, o ❌ Incorrecto/Incompleto.\n\n"
        "Sé preciso y riguroso en tu análisis matemático."
    )


# ── Onboarding modal ─────────────────────────────────────────────────────────
# @st.dialog must be applied at module level; wrapped in try/except for safety.

def _onboarding_body():
    st.markdown(
        "Para usar **todo el poder del sistema** configura estas tres cosas. "
        "Con solo la API key ya puedes empezar a chatear."
    )
    st.divider()

    st.markdown("#### 🔑 Paso 1 — API Key &nbsp;*(obligatorio para chatear)*")
    cola, colb = st.columns([2, 1])
    with cola:
        st.markdown(
            "1. Abre el **panel izquierdo** (sidebar ←)\n"
            "2. Selecciona proveedor: **Anthropic**, Google AI Studio o Groq\n"
            "3. Pega tu clave en el campo contraseña"
        )
    with colb:
        st.info("💡 **Groq es gratis**\nconsole.groq.com")
    st.divider()

    st.markdown("#### ⚙️ Paso 2 — Instalar Lean 4 en tu PC &nbsp;*(verificación formal)*")
    st.caption("Opcional pero recomendado — verifica matemáticamente cada demostración.")
    st.markdown("**En terminal (Linux / macOS / WSL2 en Windows):**")
    st.code("curl https://elan.lean-lang.org/elan-init.sh -sSf | sh", language="bash")
    st.markdown("**Luego descarga Mathlib** (200 000+ teoremas, ~500 MB):")
    st.code("lake exe cache get", language="bash")
    st.caption("Guía completa → página **⚙️ Instalar Lean 4** en el menú lateral izquierdo.")
    st.divider()

    st.markdown("#### ⚡ Paso 3 — Conectar tu Lean con la app &nbsp;*(agente local)*")
    st.caption("Tu PC verificará las demostraciones en tiempo real.")
    st.code(
        "git clone https://github.com/metamatematico/Metamatematico---Razonamiento-Formal-con-Lean.git\n"
        "cd Metamatematico---Razonamiento-Formal-con-Lean\n"
        "python scripts/local_agent.py",
        language="bash",
    )
    st.divider()

    st.caption(
        "✅ Con solo la **API key** ya puedes chatear y explorar matemáticas.  \n"
        "✅ Con **Lean + agente** cada demostración se verifica formalmente en tiempo real."
    )
    if st.button("✓ Entendido, ¡comenzar!", type="primary", use_container_width=True):
        st.session_state["onboarded"] = True
        st.rerun()


try:
    _show_onboarding = st.dialog(
        "👋 Bienvenido a METAMATEMÁTICO", width="large"
    )(_onboarding_body)
except Exception:
    _show_onboarding = _onboarding_body  # fallback: render inline


# ── Pagina principal ──────────────────────────────────────────────────────────

def page_home():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500&family=Space+Grotesk:wght@400;500;600;700;800&display=swap');

*, body { font-family: 'Space Grotesk', 'Inter', sans-serif; }

/* ─── CSS Variables (vibrant dark palette) ────────────────── */
:root {
    --bg-base:      #0d0d14;
    --bg-surface:   #12121e;
    --bg-raised:    #1a1a2e;
    --bg-overlay:   #22223a;
    --border:       #2a2a48;
    --border-hov:   #4a4a80;
    --text-1:       #e8e8ff;
    --text-2:       #9898c0;
    --text-3:       #5858a0;
    --accent:       #7c6af5;
    --accent-2:     #06d6c7;
    --accent-3:     #f72585;
    --accent-glow:  #7c6af530;
    --accent-glow2: #06d6c720;
    --neon-purple:  #b04fff;
    --neon-cyan:    #00f5e9;
    --neon-pink:    #ff2d78;
}

/* ── Scrollbar ───────────────────────────────────────────── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: var(--bg-base); }
::-webkit-scrollbar-thumb {
    background: var(--accent);
    border-radius: 4px;
}

/* ── Global bg ───────────────────────────────────────────── */
.main .block-container {
    background: var(--bg-base);
    padding-bottom: 5rem;
    max-width: 900px;
    padding-top: 2rem;
}
section[data-testid="stMain"] { background: var(--bg-base); }

/* ── Sidebar ──────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background: #0a0a12 !important;
    border-right: 1px solid var(--border);
}
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stSlider  label,
section[data-testid="stSidebar"] .stTextInput label {
    font-size: 0.73rem;
    font-weight: 600;
    color: var(--text-3);
    text-transform: uppercase;
    letter-spacing: 0.09em;
}

/* ── Keyframes ─────────────────────────────────────────────── */
@keyframes neon-shift {
    0%   { background-position: 0% 50%; }
    50%  { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
@keyframes float-in {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes grid-pulse {
    0%,100% { opacity: 0.04; }
    50%      { opacity: 0.10; }
}
@keyframes border-glow {
    0%,100% { box-shadow: 0 0 12px #7c6af540, 0 0 40px #7c6af510; }
    50%      { box-shadow: 0 0 20px #06d6c740, 0 0 60px #06d6c710; }
}

/* ── Hero ─────────────────────────────────────────────────── */
.meta-hero {
    background: linear-gradient(135deg, #0f0f1e 0%, #16163a 50%, #0f0f1e 100%);
    border: 1px solid #3a3a70;
    border-radius: 20px;
    padding: 2rem 2.6rem 1.8rem;
    margin: 0 auto 1.8rem;
    position: relative;
    overflow: hidden;
    display: flex;
    align-items: center;
    gap: 1.4rem;
    animation: border-glow 6s ease infinite;
}
/* Grid neon texture */
.meta-hero::before {
    content: "";
    position: absolute; inset: 0;
    background-image:
        linear-gradient(#7c6af518 1px, transparent 1px),
        linear-gradient(90deg, #06d6c712 1px, transparent 1px);
    background-size: 40px 40px;
    animation: grid-pulse 5s ease infinite;
    pointer-events: none;
}
/* Neon top glow line */
.meta-hero::after {
    content: "";
    position: absolute;
    top: 0; left: 10%; right: 10%;
    height: 1px;
    background: linear-gradient(90deg, transparent, #7c6af580, #06d6c780, transparent);
    pointer-events: none;
}

/* ── Title ──────────────────────────────────────────────────── */
.meta-name {
    font-family: 'Space Grotesk', 'Inter', sans-serif;
    font-size: 1.65rem;
    font-weight: 800;
    letter-spacing: 0.02em;
    background: linear-gradient(120deg,
        #e8e8ff 0%, #b04fff 25%, #7c6af5 45%,
        #06d6c7 65%, #b04fff 80%, #e8e8ff 100%);
    background-size: 300% 300%;
    animation: neon-shift 8s ease infinite;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
    line-height: 1.1;
}
.meta-sub {
    color: var(--text-3);
    font-size: 0.71rem;
    font-weight: 400;
    letter-spacing: 0.06em;
    margin: 0.2rem 0 0;
}
.meta-badge {
    display: inline-block;
    background: linear-gradient(135deg, #1a1a3a, #12122a);
    border: 1px solid #3a3a70;
    border-radius: 100px;
    padding: 0.12rem 0.65rem;
    font-size: 0.63rem;
    color: var(--accent-2);
    margin: 0.15rem 0.15rem 0;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}

/* ── Quick-example buttons ───────────────────────────────────── */
div[data-testid="column"] .stButton > button {
    background: #12122a;
    border: 1px solid #2a2a50;
    border-radius: 100px;
    color: var(--text-2);
    font-size: 0.75rem;
    font-weight: 600;
    padding: 0.5rem 0.7rem;
    transition: all 0.22s ease;
    width: 100%;
    letter-spacing: 0.03em;
    margin-bottom: 0.3rem;
}
div[data-testid="column"] .stButton > button:hover {
    border-color: var(--accent);
    color: var(--neon-cyan);
    background: #1e1e40;
    transform: translateY(-2px);
    box-shadow: 0 6px 20px var(--accent-glow), 0 0 0 1px #7c6af530;
}

/* ── Chat messages ───────────────────────────────────────────── */
[data-testid="stChatMessage"] {
    animation: float-in 0.28s ease both;
    background: transparent !important;
    border: none !important;
    padding: 0.4rem 0 !important;
}

/* User bubble */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) > div:last-child {
    background: linear-gradient(135deg, #1a1a35, #14142a) !important;
    border: 1px solid #3a3a70 !important;
    border-radius: 18px 18px 4px 18px !important;
    padding: 0.82rem 1.1rem !important;
    color: var(--text-1) !important;
    font-size: 0.94rem !important;
    margin-left: 2rem !important;
}

/* Assistant bubble */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) > div:last-child {
    background: linear-gradient(135deg, #101025, #0e0e1e) !important;
    border: 1px solid #2a2a50 !important;
    border-left: 3px solid var(--accent) !important;
    border-radius: 18px 18px 18px 4px !important;
    padding: 0.95rem 1.15rem !important;
    color: var(--text-1) !important;
    font-size: 0.93rem !important;
    line-height: 1.8 !important;
    margin-right: 2rem !important;
    box-shadow: -4px 0 20px var(--accent-glow) !important;
}

/* ── Chat input ──────────────────────────────────────────────── */
[data-testid="stChatInput"] {
    background: #12122a !important;
    border: 1px solid var(--border) !important;
    border-radius: 16px !important;
    box-shadow: 0 2px 12px #00000050 !important;
}
[data-testid="stChatInput"]:focus-within {
    border-color: var(--accent) !important;
    box-shadow: 0 0 0 3px var(--accent-glow), 0 0 20px var(--accent-glow2) !important;
}
[data-testid="stChatInput"] textarea {
    background: transparent !important;
    color: var(--text-1) !important;
    font-size: 0.94rem !important;
}
[data-testid="stChatInput"] textarea::placeholder { color: var(--text-3) !important; }

/* ── Viz button ──────────────────────────────────────────────── */
.viz-btn > button {
    background: linear-gradient(135deg, #12122a, #1a1a40) !important;
    border: 1px solid var(--accent) !important;
    border-radius: 12px !important;
    color: var(--neon-cyan) !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    transition: all 0.22s ease !important;
}
.viz-btn > button:hover {
    background: linear-gradient(135deg, #1e1e40, #26265a) !important;
    border-color: var(--neon-cyan) !important;
    box-shadow: 0 4px 20px var(--accent-glow), 0 0 30px var(--accent-glow2) !important;
}

/* ── File attach (paperclip strip) ──────────────────────────── */
.file-attach { margin-bottom: 0.3rem; }
.file-attach [data-testid="stFileUploader"] {
    background: #12122a !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
    padding: 0.3rem 0.8rem !important;
}
.file-attach [data-testid="stFileUploaderDropzone"] {
    background: transparent !important;
    border: 1px dashed #3a3a70 !important;
    border-radius: 8px !important;
    padding: 0.35rem 0.8rem !important;
    min-height: unset !important;
}
.file-attach [data-testid="stFileUploaderDropzone"] > div {
    flex-direction: row !important;
    align-items: center !important;
    gap: 0.5rem !important;
}
.file-attach [data-testid="stFileUploaderDropzone"] small,
.file-attach [data-testid="stFileUploaderDropzone"] p {
    font-size: 0.71rem !important;
    color: var(--text-3) !important;
    margin: 0 !important;
}
.file-attach [data-testid="stFileUploaderDropzone"] button {
    background: #1a1a3a !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
    color: var(--text-2) !important;
    font-size: 0.72rem !important;
    padding: 0.2rem 0.65rem !important;
    min-height: unset !important;
    line-height: 1.5 !important;
}
.file-attach [data-testid="stFileUploaderDropzone"] button:hover {
    border-color: var(--accent) !important;
    color: var(--amber-soft) !important;
    background: #2a2418 !important;
}

/* ── Code blocks inside chat ─────────────────────────────────── */
[data-testid="stChatMessage"] code {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.83em;
    background: #1a1610;
    color: var(--amber-soft);
    padding: 2px 6px;
    border-radius: 4px;
    border: 1px solid #3a3020;
}
[data-testid="stChatMessage"] pre {
    background: #161210;
    border: 1px solid #302820;
    border-radius: 10px;
    padding: 1rem 1.1rem;
    overflow-x: auto;
}
[data-testid="stChatMessage"] pre code {
    background: transparent; border: none; padding: 0; color: #d4b878;
}

/* ── Divider ────────────────────────────────────────────────── */
hr { border-color: #2a2520 !important; }

/* ── Streamlit misc overrides ───────────────────────────────── */
.stButton > button {
    background: #26211a;
    border: 1px solid var(--border);
    border-radius: 10px;
    color: var(--text-2);
    transition: all 0.2s ease;
}
.stButton > button:hover {
    border-color: var(--accent-dim);
    color: var(--amber-soft);
    background: #2e2820;
}
.stSelectbox > div > div,
.stTextInput > div > div > input {
    background: #201c16 !important;
    border-color: var(--border) !important;
    color: var(--text-1) !important;
}
.stSlider [data-baseweb="slider"] [data-testid="stThumbValue"] {
    color: var(--accent) !important;
}
[data-baseweb="slider"] [role="slider"] {
    background: var(--accent) !important;
    border-color: var(--accent) !important;
}
div[data-testid="stCaption"] { color: var(--text-3) !important; }
[data-testid="stExpander"] {
    background: #201c16 !important;
    border: 1px solid var(--border) !important;
    border-radius: 10px !important;
}
</style>
""", unsafe_allow_html=True)

    if "history" not in st.session_state:
        st.session_state.history = []
    # onboarded: False en primera visita, True tras "Entendido"
    if "onboarded" not in st.session_state:
        st.session_state["onboarded"] = False

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("""
<div style="padding:0.8rem 0 0.5rem">
  <div style="font-family:'Space Grotesk','Inter',sans-serif;font-size:1.05rem;font-weight:800;
              letter-spacing:0.04em;
              background:linear-gradient(120deg,#e8e8ff,#b04fff,#06d6c7);
              -webkit-background-clip:text;-webkit-text-fill-color:transparent;
              background-clip:text">METAMATEMÁTICO</div>
  <div style="font-size:0.67rem;color:#5858a0;margin-top:5px;letter-spacing:0.07em;
              text-transform:uppercase;font-weight:600">BIOMAT · Centro de Biomatemáticas</div>
</div>
""", unsafe_allow_html=True)
        st.divider()

        provider = st.selectbox("Proveedor", list(PROVIDERS.keys()))
        cfg = PROVIDERS[provider]

        api_key = None
        if cfg["key_label"]:
            _secret_map = {"Anthropic": "ANTHROPIC_API_KEY", "Google AI Studio": "GOOGLE_API_KEY", "Groq (gratis)": "GROQ_API_KEY", "DeepSeek": "DEEPSEEK_API_KEY"}
            _env_key = ""
            _sname = _secret_map.get(provider, "")
            if _sname:
                try:
                    _env_key = st.secrets[_sname]
                except Exception:
                    _env_key = os.environ.get(_sname, "")
            # El widget necesita `key=` estable: sin el, cualquier st.rerun()
            # (por ejemplo al adjuntar un PDF) lo redibuja con value=_env_key y
            # BORRA la clave que el usuario acababa de pegar -> modo demo.
            # Con key=, Streamlit la conserva en session_state entre reruns.
            _key_widget = f"_apikey_{provider}"
            if _key_widget not in st.session_state:
                st.session_state[_key_widget] = _env_key
            api_key = st.text_input(
                cfg["key_label"],
                type="password",
                key=_key_widget,
                placeholder=cfg["key_placeholder"],
                help=cfg.get("key_help", ""),
            )

        model = st.selectbox("Modelo", cfg["models"])
        # Los modelos actuales piensan por defecto y `max_tokens` es el tope
        # de razonamiento + respuesta juntos: con 4096 la respuesta se trunca.
        # 16000 es el maximo prudente sin streaming (evita timeouts HTTP).
        max_tokens = st.slider("Tokens máx.", 256, 16000, 8192, 256)

        # Persist API config so other pages (Verificador, etc.) can reuse it
        st.session_state["_api_key"]    = api_key or ""
        st.session_state["_provider"]   = provider
        st.session_state["_model"]      = model
        st.session_state["_max_tokens"] = max_tokens
        # Sincronizar env vars para que el LLMClient las detecte automáticamente
        if api_key:
            _provider_env = {
                "Anthropic":          "ANTHROPIC_API_KEY",
                "Google AI Studio":   "GOOGLE_API_KEY",
                "Groq (gratis)":      "GROQ_API_KEY",
                "DeepSeek":           "DEEPSEEK_API_KEY",
            }
            _env_name = _provider_env.get(provider, "")
            if _env_name:
                os.environ[_env_name] = api_key

        st.divider()

        n_hist = len(st.session_state.history)
        st.markdown(
            f'<div style="font-size:0.67rem;color:#5858a0;text-transform:uppercase;'
            f'letter-spacing:.1em;font-weight:700;margin-bottom:.5rem">Sesión activa</div>'
            f'<div style="font-size:2rem;font-weight:800;color:#e8e8ff;line-height:1">{n_hist}'
            f'<span style="font-size:.78rem;font-weight:400;color:#9898c0"> consultas</span></div>',
            unsafe_allow_html=True,
        )
        if n_hist:
            st.markdown('<div style="height:.4rem"></div>', unsafe_allow_html=True)
            if st.button("Limpiar historial", width="stretch"):
                st.session_state.history = []
                st.session_state.pop("current_query", None)
                st.session_state.pop("viz_data", None)
                st.rerun()

        # ── Estado de Lean 4 (warmup) ─────────────────────────────────────────
        _warm_sentinel = os.path.join(_proj_dir, ".lean_warm")
        if os.path.exists(_warm_sentinel):
            try:
                _warm_s = open(_warm_sentinel, encoding="utf-8").read().strip()
                st.success(f"**Lean 4 ✓ listo** — caché caliente ({_warm_s}s carga inicial)", icon="🔥")
            except Exception:
                st.success("**Lean 4 ✓ listo**", icon="🔥")
        else:
            # Verificar si hay un proceso lake corriendo (warmup activo)
            _warmup_running = any(t.name == "lean-warmup" for t in __import__("threading").enumerate())
            if _warmup_running:
                # Cifras medidas, no estimadas: Mathlib son 1,58 GB en 7.753
                # .olean. Con la cache del SO caliente el warmup baja a ~20 s;
                # en frio (tras reiniciar el equipo) sube a varios minutos.
                st.warning(
                    "**Lean 4 ⏳ cargando Mathlib…**\n\n"
                    "Lee 1,58 GB de `.olean` del disco. Con la caché del "
                    "sistema caliente tarda ~15 s; en frío, tras reiniciar el "
                    "equipo, varios minutos.\n\n"
                    "Puedes preguntar cosas no matemáticas mientras tanto: "
                    "solo las verificaciones necesitan Lean.",
                    icon="⏳",
                )
                # Streamlit no repinta por su cuenta: sin este boton el aviso
                # se queda congelado aunque el warmup ya haya terminado, y
                # parece que Mathlib no carga cuando en realidad si cargo.
                if st.button("Comprobar de nuevo", width="stretch",
                             key="_recheck_warm"):
                    st.rerun()
            else:
                st.info("**Lean 4** disponible (no iniciado aún)", icon="🔵")

        st.divider()

        with st.expander("¿Qué es el NLE?"):
            st.markdown("""
El **Núcleo Lógico Evolutivo** integra cuatro pilares en un único marco:

| Componente | Rol |
|---|---|
| **MES** (Ehresmann) | Memoria categórica |
| **Categorías** | Grafo de 76 skills |
| **Lean 4** | Verificación formal |
| **GNN + PPO** | Aprendizaje continuo |

Cada consulta alimenta el agente PPO y la memoria procedimental guarda los patrones exitosos.
""")
        st.markdown(
            '<div style="font-size:0.64rem;color:#5858a0;line-height:1.7;margin-top:.5rem">'
            '76 skills matemáticos · 14 categorías<br>'
            'GNN + PPO · Memory Evolutive Systems<br>'
            'Lean 4 · FOL · ZFC · Teoría de Tipos'
            '</div>',
            unsafe_allow_html=True,
        )

        # ── Panel de actualizaciones ──────────────────────────────────────────
        st.divider()
        upd = _check_updates()
        sha = upd["sha"]

        if upd["behind"] == 0:
            st.markdown(
                f'<div style="font-size:0.65rem;color:#06d6c7;font-weight:600">'
                f'✔ Al día · <code style="color:#5858a0">{sha}</code></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div style="font-size:0.65rem;color:#b04fff;font-weight:700">'
                f'⬆ {upd["behind"]} actualización(es) disponible(s)</div>'
                f'<div style="font-size:0.6rem;color:#5858a0;margin-top:2px">'
                f'Local: <code>{sha}</code></div>',
                unsafe_allow_html=True,
            )
            with st.expander("Ver cambios"):
                st.code(upd["new_commits"] or "(sin detalles)", language="")

            if st.button("⬆ Actualizar ahora", width="stretch", type="primary"):
                with st.spinner("Descargando actualización…"):
                    ok, msg = _do_update()
                if ok:
                    _check_updates.clear()
                    st.success("✔ Actualización aplicada. Reinicia la app para cargar los cambios.")
                    st.code(msg[:800] if msg else "")
                else:
                    st.error(f"No se pudo actualizar:\n{msg[:400]}")

        if st.button("🔄 Comprobar actualizaciones", width="stretch"):
            _check_updates.clear()
            st.rerun()

        # ── Panel: usa tu cómputo local ───────────────────────────────────
        try:
            _ctx_host = (st.context.headers or {}).get("host", "")
        except Exception:
            _ctx_host = ""
        _is_remote = not (
            os.environ.get("STREAMLIT_SERVER_ADDRESS", "localhost") in ("localhost", "127.0.0.1")
            or _ctx_host.startswith("localhost")
        )
        if _is_remote:
            st.divider()
            with st.expander("⚡ Amplía el poder con tu PC"):
                st.markdown(
                    """
**¿Tienes Lean 4 instalado localmente?**
Conecta tu máquina para que la verificación formal ocurra en tu hardware,
no en el servidor.

**1. Instala Lean 4** (si no lo tienes):
```bash
curl https://elan.lean-lang.org/elan-init.sh -sSf | sh
```

**2. Clona el repositorio:**
```bash
git clone https://github.com/metamatematico/\
Metamatematico---Razonamiento-Formal-con-Lean.git
cd Metamatematico---Razonamiento-Formal-con-Lean
lake update   # descarga Mathlib (~20-30 min)
```

**3. Lanza el agente local:**
```bash
python scripts/local_agent.py \\
  --server https://ESTA_URL \\
  --check    # verifica tu instalación primero
```

Cuando el agente esté activo, Lean corre en tu PC y
los resultados se muestran aquí.
                    """,
                    unsafe_allow_html=False,
                )

    # ── Hero compacto ──────────────────────────────────────────────────────────
    st.markdown("""
<div class="meta-hero">
  <div>
    <div class="meta-name">METAMATEMÁTICO</div>
    <div class="meta-sub">Razonamiento formal · Lean 4 · Núcleo Lógico Evolutivo · BIOMAT</div>
    <div style="margin-top:.4rem">
      <span class="meta-badge">76 skills</span>
      <span class="meta-badge">GNN + PPO</span>
      <span class="meta-badge">MES</span>
      <span class="meta-badge">Lean 4</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

    # ── Bienvenida para usuarios nuevos (modal, definida a nivel de módulo) ─────
    if not st.session_state.get("onboarded", False):
        _show_onboarding()

    # ── Ejemplos rápidos ───────────────────────────────────────────────────────
    examples = [
        ("√2  irracional",  "Demuestra que √2 es irracional"),
        ("∀  Yoneda",       "Explica el Lema de Yoneda"),
        ("⟨⟩  Lean 4",      "example (n : Nat) : n + 0 = n := by ?"),
        ("↔  Curry–Howard", "Qué es la correspondencia Curry-Howard?"),
    ]
    cols4 = st.columns(4)
    for i, (label, ex) in enumerate(examples):
        with cols4[i]:
            if st.button(label, width="stretch", help=ex, key=f"_ex_{i}"):
                st.session_state["_pending_query"] = ex
                st.rerun()

    st.markdown('<div style="height:1.2rem"></div>', unsafe_allow_html=True)

    # ── Historial como burbujas de chat ───────────────────────────────────────
    # Mostrar del más antiguo al más reciente (history[0] es el más reciente)
    _PROVIDER_MAP = {
        "Google AI Studio":   "google",
        "Groq (gratis)":      "groq",
        "Anthropic":          "anthropic",
        "DeepSeek":           "deepseek",
        "Demo (sin API key)": "demo",
    }

    for _hist_idx, item in enumerate(reversed(st.session_state.history)):
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(item["q"])
        with st.chat_message("assistant", avatar="🧮"):
            st.markdown(item["a"])
            tok_str = (f' · {item["in_tok"]}→{item["out_tok"]} tok'
                       if item.get("in_tok") else "")
            _cap_c, _pdf_c = st.columns([8, 2])
            with _cap_c:
                st.caption(f'◆ {item["model"]} · {item["t"]}s{tok_str}')
            with _pdf_c:
                try:
                    from nucleo.utils.pdf_export import generate_pdf
                    import re as _re2
                    _lm = _re2.search(r'```lean\n(.*?)```', item["a"], _re2.DOTALL)
                    _pdf_h = generate_pdf(
                        query=item["q"],
                        response=item["a"],
                        lean_code=_lm.group(1).strip() if _lm else "",
                        timestamp=datetime.strptime(
                            datetime.now().strftime(f"%Y%m%d {item.get('ts','00:00')}"),
                            "%Y%m%d %H:%M"
                        ),
                    )
                    st.download_button(
                        "⬇️ PDF",
                        data=_pdf_h,
                        file_name=f"metamat_hist_{_hist_idx}.pdf",
                        mime="application/pdf",
                        key=f"_pdf_hist_{_hist_idx}",
                        help="Descargar esta respuesta como PDF",
                    )
                except Exception:
                    pass

    # Botón de visualizaciones (si hay consulta activa)
    if st.session_state.get("current_query"):
        st.markdown('<div class="viz-btn">', unsafe_allow_html=True)
        if st.button("📊  Ver grafo · embeddings · traza categórica →",
                     width="stretch", key="_viz_btn"):
            st.switch_page("pages/1_Visualizaciones.py")
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Aplicar feedback pendiente ────────────────────────────────────────────
    if st.session_state.get("_pending_feedback") is not None:
        _nucleo_fb = _get_nucleo()
        if _nucleo_fb is not None:
            _nucleo_fb.apply_feedback(st.session_state.pop("_pending_feedback"))
        else:
            st.session_state.pop("_pending_feedback", None)

    # ── Adjuntar archivo (📎 paperclip) ─────────────────────────────────────
    st.markdown('<div class="file-attach">', unsafe_allow_html=True)
    uploaded_file = st.file_uploader(
        "📎 Adjuntar archivo matemático (.txt, .tex, .pdf)",
        type=["txt", "tex", "latex", "pdf"],
        label_visibility="collapsed",
        key="_file_attach",
        help="Sube un .txt, .tex o .pdf con un teorema o demostración para verificarlo",
    )
    st.markdown('</div>', unsafe_allow_html=True)

    # Archivo subido → solo se guarda como contexto activo. NO se dispara
    # ningun analisis automatico: el nucleo espera una orden explicita del
    # usuario (ej. "detecta errores", "verifica este teorema").
    _file_key = f"_pf_{getattr(uploaded_file, 'name', '')}_{getattr(uploaded_file, 'size', 0)}"
    if uploaded_file is not None and st.session_state.get("_processed_file") != _file_key:
        st.session_state["_processed_file"] = _file_key
        _ftext = _extract_file_text(uploaded_file)
        if _ftext.strip() and not _ftext.startswith("[Error"):
            st.session_state["_active_file"] = {
                "name": uploaded_file.name,
                "text": _ftext,
            }
            st.rerun()
        elif _ftext.startswith("[Error"):
            st.error(_ftext)

    # Mostrar indicador de archivo activo + accion explicita opcional
    _active_file = st.session_state.get("_active_file")
    if _active_file:
        col_fa, col_fb, col_fc = st.columns([4, 2, 1])
        with col_fa:
            st.caption(f"📎 Archivo activo: **{_active_file['name']}** — escribe que quieres que haga con él")
        with col_fb:
            if st.button("🔍 Verificar completo", key="_verify_file", help="Analisis automatico completo (correccion, Lean 4, veredicto)"):
                st.session_state["_pending_query"] = _build_file_verify_prompt(_active_file["text"], _active_file["name"])
                st.session_state["_pending_query_display"] = f"📎 `{_active_file['name']}` — verificación completa"
                st.rerun()
        with col_fc:
            if st.button("✕", key="_clear_file", help="Quitar archivo"):
                st.session_state.pop("_active_file", None)
                st.session_state.pop("_processed_file", None)
                st.rerun()

    # ── Input de chat (fixed al fondo) ────────────────────────────────────────
    prompt = st.chat_input("Escribe un teorema, problema matemático o goal de Lean 4…")

    # Ejemplo rápido pulsado (o "Verificar completo" de un archivo) → inyectar como prompt
    if st.session_state.get("_pending_query"):
        prompt = st.session_state.pop("_pending_query")

    # Si hay archivo activo y el usuario escribe una pregunta → enriquecer prompt con el archivo
    elif _active_file and prompt and "```" not in prompt:
        _ctx_snippet = _active_file["text"][:2000]
        prompt = (
            f"El usuario tiene cargado el archivo `{_active_file['name']}`:\n\n"
            f"```\n{_ctx_snippet}\n```\n\n"
            f"Pregunta del usuario sobre ese archivo: {prompt}"
        )

    # Texto que se muestra al usuario en la burbuja
    _display_query = st.session_state.get("_pending_query_display") or prompt
    st.session_state.pop("_pending_query_display", None)

    if prompt and prompt.strip():
        # Mostrar mensaje del usuario (display limpio cuando hay archivo)
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(_display_query)

        # Procesar
        nucleo = _get_nucleo()
        res = None
        elapsed = 0.0

        # Si el warmup de Lean sigue en vuelo, la consulta y el warmup pelean
        # por el mismo disco: la consulta expira a los 360 s sin devolver nada.
        # Antes se rechazaba la consulta y habia que reescribirla; ahora se
        # ESPERA al warmup y se sigue sola. Solo afecta a las consultas que van
        # a usar Lean: un saludo no toca el verificador y no debe esperar.
        _warm_listo = os.path.exists(os.path.join(_proj_dir, ".lean_warm"))
        _warm_curro = any(t.name == "lean-warmup" for t in threading.enumerate())
        _usa_lean = False
        if nucleo is not None and _warm_curro and not _warm_listo:
            try:
                _usa_lean = nucleo._is_mathematical(prompt) or "```lean" in prompt
            except Exception:
                _usa_lean = True   # ante la duda, esperar

        if _usa_lean:
            _hilo_warm = next(
                (t for t in threading.enumerate() if t.name == "lean-warmup"), None
            )
            if _hilo_warm is not None:
                with st.spinner(
                    "Cargando Mathlib por primera vez desde el arranque… "
                    "tu consulta se enviará automáticamente al terminar "
                    "(no hace falta reenviarla)."
                ):
                    _hilo_warm.join(timeout=1140)   # algo menos que el tope del warmup
                _warm_listo = os.path.exists(os.path.join(_proj_dir, ".lean_warm"))

            if not _warm_listo:
                st.warning(
                    "**Mathlib no terminó de cargar.** El precalentamiento agotó "
                    "su tiempo, así que la verificación fallaría igualmente.\n\n"
                    "Revisa el estado de Lean en la barra lateral antes de "
                    "reintentar.",
                    icon="⏳",
                )
                st.stop()

        if nucleo is not None:
            try:
                nucleo.reconfigure_llm(
                    _PROVIDER_MAP.get(provider, "demo"),
                    model,
                    api_key or "",
                    max_tokens,
                )
                # Sincronizar conversacion interna con el historial visible
                nucleo.sync_conversation(st.session_state.history)
                with st.spinner("Analizando con el Núcleo…"):
                    t0 = time.time()
                    nr = nucleo.process_sync(prompt)
                    elapsed = time.time() - t0

                try:
                    vd = nucleo.get_viz_data(prompt)
                    st.session_state["viz_data"] = vd
                    # Acumular historial de query embeddings para la visualización
                    qe = vd.get("query_embedding")
                    if qe:
                        history = st.session_state.get("query_embeddings", [])
                        history.append({"text": prompt, "embedding": qe})
                        if len(history) > 20:          # máximo 20 queries
                            history = history[-20:]
                        st.session_state["query_embeddings"] = history
                except Exception:
                    st.session_state.pop("viz_data", None)

                confidence_badge = (
                    f' · ⬡ {nr.confidence:.0%}'
                    if hasattr(nr, "confidence") else ""
                )
                cr_src = nr.metadata.get("source_cr", "") if hasattr(nr, "metadata") else ""

                # Rutas que NO pasan por el verificador (p. ej. demostraciones
                # geometricas por reordenamiento de areas). Sin este aviso la
                # respuesta parece verificada solo porque menciona Mathlib.
                _sin_lean = (
                    nr.metadata.get("sin_verificacion_lean", False)
                    if hasattr(nr, "metadata") else False
                )
                if _sin_lean:
                    nr.content += (
                        "\n\n---\n"
                        "> ⚠️ **Sin verificación de Lean.** Esta respuesta es una "
                        "explicación en lenguaje natural: el argumento no se formalizó "
                        "ni lo comprobó el verificador. Pide la versión formal si "
                        "quieres una prueba verificada con Mathlib."
                    )

                # Extraer lean_code del contenido para el PDF
                import re as _re
                _lean_match = _re.search(r'```lean\n(.*?)```', nr.content, _re.DOTALL)
                _lean_code  = _lean_match.group(1).strip() if _lean_match else ""
                _conf       = getattr(nr, "confidence", 0.0)
                _area       = (nr.metadata.get("area", "") if hasattr(nr, "metadata") else "")
                _vstatus    = (nr.metadata.get("verification_status", "") if hasattr(nr, "metadata") else "")

                res = {
                    "content":   nr.content,
                    "model":     model,
                    "in_tok":    0,
                    "out_tok":   0,
                    "_meta":     f'{model}{confidence_badge}'
                                 + (f' · CR:{cr_src}' if cr_src else '')
                                 + (' · ⚠ sin Lean' if _sin_lean else ''),
                    "error":     "",
                    "_lean_code": _lean_code,
                    "_conf":      _conf,
                    "_area":      _area,
                    "_vstatus":   _vstatus,
                }
            except Exception as _nucleo_err:
                import logging, traceback
                logging.getLogger(__name__).warning(
                    f"Nucleo.process_sync falló: {_nucleo_err}\n{traceback.format_exc()}"
                )
                _msg, _es_de_cuenta = _explica_error_proveedor(_nucleo_err)
                # Si el fallo es de saldo/clave/permisos, el reintento de abajo
                # llamaria al MISMO proveedor y devolveria el MISMO error: se
                # mostraba dos veces y en JSON crudo. Se corta aqui.
                if _es_de_cuenta:
                    with st.chat_message("assistant", avatar="🧮"):
                        st.error(_msg)
                    st.session_state.history.append(
                        {"role": "assistant", "content": _msg,
                         "model": model, "t": 0.0}
                    )
                    st.stop()
                st.warning(f"⚠ {_msg}", icon="⚠️")

        if res is None:
            info   = classify(prompt)
            enriched = enrich(prompt, info)
            with st.spinner("Analizando…"):
                t0 = time.time()
                if provider == "Google AI Studio" and api_key:
                    res = call_google(enriched, model, api_key, max_tokens)
                elif provider == "Groq (gratis)" and api_key:
                    res = call_groq(enriched, model, api_key, max_tokens)
                elif provider == "Anthropic" and api_key:
                    res = call_anthropic(enriched, model, api_key, max_tokens)
                elif provider == "DeepSeek" and api_key:
                    res = call_deepseek(enriched, model, api_key, max_tokens)
                elif provider != "Demo (sin API key)" and not api_key:
                    res = {"content": "", "error": "Introduce tu API key en el panel lateral."}
                else:
                    res = call_demo(prompt, info)
                elapsed = time.time() - t0
            res.setdefault("_meta", model)

        # Mostrar respuesta del asistente
        with st.chat_message("assistant", avatar="🧮"):
            if res.get("error"):
                # Traducir tambien los errores de la ruta directa (sin Nucleo),
                # para no volcar el JSON de la API al usuario.
                st.error(_explica_error_proveedor(res["error"])[0])
            else:
                st.markdown(res["content"])
                tok_str = (f' · {res["in_tok"]}→{res["out_tok"]} tok'
                           if res.get("in_tok") else "")
                st.caption(f'◆ {res.get("_meta", model)} · {elapsed:.1f}s{tok_str}')

                # Feedback + descarga PDF
                _fb_key = len(st.session_state.history)
                fb_c1, fb_c2, _, pdf_col = st.columns([1, 1, 6, 3])
                with fb_c1:
                    if st.button("👍", key=f"_fb_pos_{_fb_key}", help="Útil"):
                        st.session_state["_pending_feedback"] = 1.0
                with fb_c2:
                    if st.button("👎", key=f"_fb_neg_{_fb_key}", help="No útil"):
                        st.session_state["_pending_feedback"] = -0.5
                with pdf_col:
                    try:
                        from nucleo.utils.pdf_export import generate_pdf
                        _pdf_bytes = generate_pdf(
                            query=prompt,
                            response=res["content"],
                            lean_code=res.get("_lean_code", ""),
                            confidence=res.get("_conf", 0.0),
                            area=res.get("_area", ""),
                            status=res.get("_vstatus", ""),
                        )
                        _fn = f"metamat_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                        st.download_button(
                            "⬇️ PDF",
                            data=_pdf_bytes,
                            file_name=_fn,
                            mime="application/pdf",
                            key=f"_pdf_{_fb_key}",
                            help="Descargar resultado como PDF",
                        )
                    except Exception as _pdf_err:
                        st.caption(f"PDF: {_pdf_err}")

            if not res.get("error"):
                st.session_state["current_query"]    = prompt
                st.session_state["current_response"] = res["content"]

                # Guardar en historial para persistir al navegar
                st.session_state.history.insert(0, {
                    "ts":     datetime.now().strftime("%H:%M"),
                    "q":      _display_query,   # nombre de archivo o texto original
                    "a":      res["content"],
                    "model":  res.get("_meta", model),
                    "in_tok": res.get("in_tok", 0),
                    "out_tok":res.get("out_tok", 0),
                    "t":      round(elapsed, 1),
                })

        # Botón de visualizaciones tras la nueva respuesta
        if not res.get("error"):
            st.markdown('<div class="viz-btn" style="margin-top:.5rem">', unsafe_allow_html=True)
            if st.button("📊  Ver grafo · embeddings · traza categórica de esta consulta →",
                         width="stretch", key="_viz_btn_new"):
                st.switch_page("pages/1_Visualizaciones.py")
            st.markdown('</div>', unsafe_allow_html=True)


# ── Navegacion ────────────────────────────────────────────────────────────────

try:
    _home_page = st.Page(page_home, title="METAMATEMÁTICO", icon="🧮", default=True)
    st.session_state["_home_page"] = _home_page
    pg = st.navigation([
        _home_page,
        st.Page("pages/1_Visualizaciones.py", title="Visualizaciones", icon="📊"),
        st.Page("pages/2_Verificador.py", title="Verificador", icon="🔬"),
        st.Page("pages/3_Instalar_Lean.py", title="Instalar Lean 4", icon="⚙️"),
        st.Page("pages/4_Consultores_Avanzados.py", title="Consultores Avanzados", icon="🔭"),
    ])
    pg.run()
except Exception as _run_err:
    import traceback as _tb
    st.error(f"Error: {type(_run_err).__name__}: {_run_err}")
    with st.expander("Ver detalle"):
        st.code(_tb.format_exc(), language="text")
