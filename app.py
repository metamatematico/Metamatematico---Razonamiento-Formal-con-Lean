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
from datetime import datetime

# Forzar UTF-8 en stdout/stderr para que caracteres como ℝ, ∀, ∃ no rompan
# el logging de Streamlit en Windows (cp1252 por defecto).
try:
    if sys.stdout and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except OSError:
    pass
try:
    if sys.stderr and hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except OSError:
    pass

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
def _get_nucleo():
    """Singleton del Nucleo — persiste entre reruns de Streamlit."""
    try:
        import asyncio
        import concurrent.futures
        from nucleo.core import Nucleo
        from nucleo.config import NucleoConfig

        n = Nucleo(NucleoConfig())

        def _init():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(n.initialize())
            finally:
                loop.close()

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            pool.submit(_init).result(timeout=60)

        return n
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"Nucleo no disponible: {e}")
        return None

st.set_page_config(
    page_title="METAMATEMÁTICO",
    page_icon="🧮",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Modelos ───────────────────────────────────────────────────────────────────

PROVIDERS = {
    "Anthropic": {
        "models": [
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
            "content": r.content[0].text,
            "model": r.model,
            "in_tok": r.usage.input_tokens,
            "out_tok": r.usage.output_tokens,
            "error": None,
        }
    except ImportError:
        return {"content": "", "error": "Instala: pip install anthropic"}
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


# ── Onboarding modal (nivel de módulo — @st.dialog no puede estar dentro de funciones) ──

@st.dialog("👋 Bienvenido a METAMATEMÁTICO", width="large")
def _show_onboarding():
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
            _secret_map = {"Anthropic": "ANTHROPIC_API_KEY", "Google AI Studio": "GOOGLE_API_KEY", "Groq (gratis)": "GROQ_API_KEY"}
            _env_key = ""
            _sname = _secret_map.get(provider, "")
            if _sname:
                try:
                    _env_key = st.secrets[_sname]
                except Exception:
                    _env_key = os.environ.get(_sname, "")
            api_key = st.text_input(
                cfg["key_label"],
                value=_env_key,
                type="password",
                placeholder=cfg["key_placeholder"],
                help=cfg.get("key_help", ""),
            )

        model = st.selectbox("Modelo", cfg["models"])
        max_tokens = st.slider("Tokens máx.", 256, 4096, 1024, 128)

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
        _is_remote = not (
            os.environ.get("STREAMLIT_SERVER_ADDRESS", "localhost") in ("localhost", "127.0.0.1")
            or st.context.headers.get("host", "").startswith("localhost")
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
        "Demo (sin API key)": "demo",
    }

    for item in reversed(st.session_state.history):
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(item["q"])
        with st.chat_message("assistant", avatar="🧮"):
            st.markdown(item["a"])
            tok_str = (f' · {item["in_tok"]}→{item["out_tok"]} tok'
                       if item.get("in_tok") else "")
            st.caption(
                f'◆ {item["model"]} · {item["t"]}s{tok_str}'
            )

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

    # Archivo subido → preparar como consulta de verificación
    _file_key = f"_pf_{getattr(uploaded_file, 'name', '')}_{getattr(uploaded_file, 'size', 0)}"
    if uploaded_file is not None and st.session_state.get("_processed_file") != _file_key:
        st.session_state["_processed_file"] = _file_key
        _ftext = _extract_file_text(uploaded_file)
        if _ftext.strip() and not _ftext.startswith("[Error"):
            st.session_state["_pending_file"] = {
                "display": f"📎 Verificar archivo: `{uploaded_file.name}`",
                "prompt":  _build_file_verify_prompt(_ftext, uploaded_file.name),
            }
            st.rerun()
        elif _ftext.startswith("[Error"):
            st.error(_ftext)

    # ── Input de chat (fixed al fondo) ────────────────────────────────────────
    prompt = st.chat_input("Escribe un teorema, problema matemático o goal de Lean 4…")

    # Ejemplo rápido pulsado → inyectar como prompt
    if st.session_state.get("_pending_query"):
        prompt = st.session_state.pop("_pending_query")

    # Archivo adjunto pendiente → convertir en prompt (preserva display vs real)
    _pending_file = st.session_state.pop("_pending_file", None)
    if _pending_file and not prompt:
        prompt = _pending_file["prompt"]

    # Texto que se muestra al usuario en la burbuja
    _display_query = _pending_file["display"] if _pending_file else prompt

    if prompt and prompt.strip():
        # Mostrar mensaje del usuario (display limpio cuando hay archivo)
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(_display_query)

        # Procesar
        nucleo = _get_nucleo()
        res = None
        elapsed = 0.0

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
                res = {
                    "content":  nr.content,
                    "model":    model,
                    "in_tok":   0,
                    "out_tok":  0,
                    "_meta":    f'{model}{confidence_badge}' + (f' · CR:{cr_src}' if cr_src else ''),
                    "error":    "",
                }
            except Exception as _nucleo_err:
                import logging
                logging.getLogger(__name__).warning(
                    f"Nucleo.process_sync falló: {_nucleo_err}"
                )
                st.warning(f"⚠ El Núcleo encontró un error: {_nucleo_err}", icon="⚠️")

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
                elif provider != "Demo (sin API key)" and not api_key:
                    res = {"content": "", "error": "Introduce tu API key en el panel lateral."}
                else:
                    res = call_demo(prompt, info)
                elapsed = time.time() - t0
            res.setdefault("_meta", model)

        # Mostrar respuesta del asistente
        with st.chat_message("assistant", avatar="🧮"):
            if res.get("error"):
                st.error(res["error"])
            else:
                st.markdown(res["content"])
                tok_str = (f' · {res["in_tok"]}→{res["out_tok"]} tok'
                           if res.get("in_tok") else "")
                st.caption(f'◆ {res.get("_meta", model)} · {elapsed:.1f}s{tok_str}')

                # Feedback
                _fb_key = len(st.session_state.history)
                fb_c1, fb_c2, _ = st.columns([1, 1, 10])
                with fb_c1:
                    if st.button("👍", key=f"_fb_pos_{_fb_key}", help="Útil"):
                        st.session_state["_pending_feedback"] = 1.0
                with fb_c2:
                    if st.button("👎", key=f"_fb_neg_{_fb_key}", help="No útil"):
                        st.session_state["_pending_feedback"] = -0.5

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

pg = st.navigation([
    st.Page(page_home, title="METAMATEMÁTICO", icon="🧮", default=True),
    st.Page("pages/1_Visualizaciones.py", title="Visualizaciones", icon="📊"),
])
pg.run()
