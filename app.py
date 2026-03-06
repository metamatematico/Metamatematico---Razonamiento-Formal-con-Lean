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

# Asegurar que el paquete nucleo sea importable desde el directorio del proyecto
_proj_dir = os.path.dirname(os.path.abspath(__file__))
if _proj_dir not in sys.path:
    sys.path.insert(0, _proj_dir)


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
    "Demo (sin API key)": {
        "models": ["demo"],
        "key_label": None,
        "key_placeholder": None,
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
    "Anthropic": {
        "models": [
            "claude-haiku-4-5-20251001",
            "claude-sonnet-4-6",
        ],
        "key_label": "Anthropic API Key",
        "key_placeholder": "sk-ant-...",
        "key_help": "Obtener en console.anthropic.com",
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


# ── Pagina principal ──────────────────────────────────────────────────────────

def page_home():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;500&family=Space+Grotesk:wght@700;800&display=swap');

*, body { font-family: 'Inter', sans-serif; }

/* ── Scrollbar ───────────────────────────── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: #080c12; }
::-webkit-scrollbar-thumb { background: #1c2333; border-radius: 4px; }

/* ── Global bg ───────────────────────────── */
.main .block-container { background: #080c12; padding-bottom: 5rem; }
section[data-testid="stMain"]       { background: #080c12; }

/* ── Sidebar ─────────────────────────────── */
section[data-testid="stSidebar"] {
    background: #060a10 !important;
    border-right: 1px solid #151c28;
}
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stSlider  label,
section[data-testid="stSidebar"] .stTextInput label {
    font-size: 0.75rem;
    font-weight: 600;
    color: #7a8fa0;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

/* ── Animated gradient keyframes ────────── */
@keyframes grad-shift {
    0%,100% { background-position: 0% 50%; }
    50%      { background-position: 100% 50%; }
}
@keyframes float-in {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
}

/* ── Hero compacto ───────────────────────── */
.meta-hero {
    background: linear-gradient(145deg, #090e1a 0%, #0f1729 50%, #0a0f1c 100%);
    border: 1px solid #1a2236;
    border-radius: 16px;
    padding: 1.2rem 2rem 1rem;
    margin: 0 auto 1rem;
    position: relative;
    overflow: hidden;
    display: flex;
    align-items: center;
    gap: 1.2rem;
}
.meta-hero::before {
    content: "";
    position: absolute; inset: 0;
    background-image:
        linear-gradient(#818cf808 1px, transparent 1px),
        linear-gradient(90deg, #818cf808 1px, transparent 1px);
    background-size: 32px 32px;
    pointer-events: none;
}
.meta-name {
    font-family: 'Space Grotesk', 'Inter', sans-serif;
    font-size: 1.5rem;
    font-weight: 800;
    letter-spacing: 0.06em;
    background: linear-gradient(120deg, #60a5fa 0%, #818cf8 40%, #c084fc 70%, #818cf8 100%);
    background-size: 250% 250%;
    animation: grad-shift 6s ease infinite;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0;
    line-height: 1.1;
}
.meta-sub {
    color: #5a7090;
    font-size: 0.72rem;
    font-weight: 400;
    letter-spacing: 0.04em;
    margin: 0.15rem 0 0;
}
.meta-badge {
    display: inline-block;
    background: #0f1729;
    border: 1px solid #1e2d47;
    border-radius: 100px;
    padding: 0.12rem 0.55rem;
    font-size: 0.65rem;
    color: #7a8fa0;
    margin: 0.15rem 0.15rem 0;
    font-weight: 500;
}

/* ── Example buttons ─────────────────────── */
div[data-testid="column"] .stButton > button {
    background: #0d1117;
    border: 1px solid #1e2d40;
    border-radius: 100px;
    color: #6b7f99;
    font-size: 0.74rem;
    font-weight: 600;
    padding: 0.35rem 0.5rem;
    transition: all 0.2s ease;
    width: 100%;
    letter-spacing: 0.02em;
}
div[data-testid="column"] .stButton > button:hover {
    border-color: #4f46e580;
    color: #93c5fd;
    background: #0f1729;
    transform: translateY(-1px);
}

/* ── Chat messages ───────────────────────── */
[data-testid="stChatMessage"] {
    animation: float-in 0.3s ease both;
    background: transparent !important;
    border: none !important;
    padding: 0.4rem 0 !important;
}

/* User bubble */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) > div:last-child {
    background: #0f1729 !important;
    border: 1px solid #1e2d47 !important;
    border-radius: 14px 14px 4px 14px !important;
    padding: 0.75rem 1rem !important;
    color: #c9d1d9 !important;
    font-size: 0.94rem !important;
    margin-left: 2rem !important;
}

/* Assistant bubble */
[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-assistant"]) > div:last-child {
    background: #0a0f1c !important;
    border: 1px solid #151c2e !important;
    border-left: 3px solid #6d28d9 !important;
    border-radius: 14px 14px 14px 4px !important;
    padding: 0.9rem 1.1rem !important;
    color: #c9d1d9 !important;
    font-size: 0.93rem !important;
    line-height: 1.75 !important;
    margin-right: 2rem !important;
}

/* ── Chat input ──────────────────────────── */
[data-testid="stChatInput"] {
    background: #0d1117 !important;
    border: 1px solid #1e2d40 !important;
    border-radius: 14px !important;
}
[data-testid="stChatInput"] textarea {
    background: transparent !important;
    color: #c9d1d9 !important;
    font-size: 0.94rem !important;
}
[data-testid="stChatInput"] textarea::placeholder { color: #4a5c6e !important; }

/* ── Viz button ──────────────────────────── */
.viz-btn > button {
    background: #0a0f1c !important;
    border: 1px solid #1a2236 !important;
    border-radius: 10px !important;
    color: #6366f1 !important;
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}
.viz-btn > button:hover {
    background: #0f1729 !important;
    border-color: #6366f1 !important;
    box-shadow: 0 4px 16px #6366f120 !important;
}

/* Code blocks inside chat */
[data-testid="stChatMessage"] code {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.83em;
    background: #111827;
    color: #7dd3fc;
    padding: 2px 6px;
    border-radius: 4px;
    border: 1px solid #1e293b;
}
[data-testid="stChatMessage"] pre {
    background: #080c12;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 1rem 1.1rem;
    overflow-x: auto;
}
[data-testid="stChatMessage"] pre code {
    background: transparent; border: none; padding: 0; color: #a5f3fc;
}

/* Divider */
hr { border-color: #141c2a !important; }
</style>
""", unsafe_allow_html=True)

    if "history" not in st.session_state:
        st.session_state.history = []

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("""
<div style="padding:0.8rem 0 0.4rem">
  <div style="font-family:'Space Grotesk',sans-serif;font-size:1.05rem;font-weight:800;
              letter-spacing:0.06em;
              background:linear-gradient(120deg,#60a5fa,#818cf8,#c084fc);
              -webkit-background-clip:text;-webkit-text-fill-color:transparent;
              background-clip:text">METAMATEMÁTICO</div>
  <div style="font-size:0.68rem;color:#2d3748;margin-top:4px;letter-spacing:0.06em;
              text-transform:uppercase;font-weight:600">BIOMAT · Centro de Biomatemáticas</div>
</div>
""", unsafe_allow_html=True)
        st.divider()

        provider = st.selectbox("Proveedor", list(PROVIDERS.keys()))
        cfg = PROVIDERS[provider]

        api_key = None
        if cfg["key_label"]:
            api_key = st.text_input(
                cfg["key_label"],
                type="password",
                placeholder=cfg["key_placeholder"],
                help=cfg.get("key_help", ""),
            )

        model = st.selectbox("Modelo", cfg["models"])
        max_tokens = st.slider("Tokens máx.", 256, 4096, 1024, 128)

        st.divider()

        n_hist = len(st.session_state.history)
        st.markdown(
            f'<div style="font-size:0.68rem;color:#6080a0;text-transform:uppercase;'
            f'letter-spacing:.1em;font-weight:700;margin-bottom:.5rem">Sesión activa</div>'
            f'<div style="font-size:2rem;font-weight:800;color:#c9d1d9;line-height:1">{n_hist}'
            f'<span style="font-size:.78rem;font-weight:400;color:#7a8fa0"> consultas</span></div>',
            unsafe_allow_html=True,
        )
        if n_hist:
            st.markdown('<div style="height:.4rem"></div>', unsafe_allow_html=True)
            if st.button("Limpiar historial", use_container_width=True):
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
            '<div style="font-size:0.65rem;color:#4a6080;line-height:1.6;margin-top:.5rem">'
            '76 skills matemáticos · 14 categorías<br>'
            'GNN + PPO · Memory Evolutive Systems<br>'
            'Lean 4 · FOL · ZFC · Teoría de Tipos'
            '</div>',
            unsafe_allow_html=True,
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
            if st.button(label, use_container_width=True, help=ex, key=f"_ex_{i}"):
                st.session_state["_pending_query"] = ex
                st.rerun()

    st.markdown('<div style="height:.4rem"></div>', unsafe_allow_html=True)

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
                     use_container_width=True, key="_viz_btn"):
            st.switch_page("pages/1_Visualizaciones.py")
        st.markdown('</div>', unsafe_allow_html=True)

    # ── Aplicar feedback pendiente ────────────────────────────────────────────
    if st.session_state.get("_pending_feedback") is not None:
        _nucleo_fb = _get_nucleo()
        if _nucleo_fb is not None:
            _nucleo_fb.apply_feedback(st.session_state.pop("_pending_feedback"))
        else:
            st.session_state.pop("_pending_feedback", None)

    # ── Input de chat (fixed al fondo) ────────────────────────────────────────
    prompt = st.chat_input("Escribe un teorema, problema matemático o goal de Lean 4…")

    # Ejemplo rápido pulsado → inyectar como prompt
    if st.session_state.get("_pending_query"):
        prompt = st.session_state.pop("_pending_query")

    if prompt and prompt.strip():
        # Mostrar mensaje del usuario
        with st.chat_message("user", avatar="🧑‍💻"):
            st.markdown(prompt)

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
                with st.spinner("Analizando con el Núcleo…"):
                    t0 = time.time()
                    nr = nucleo.process_sync(prompt)
                    elapsed = time.time() - t0

                try:
                    st.session_state["viz_data"] = nucleo.get_viz_data(prompt)
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
                    "q":      prompt,
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
                         use_container_width=True, key="_viz_btn_new"):
                st.switch_page("pages/1_Visualizaciones.py")
            st.markdown('</div>', unsafe_allow_html=True)


# ── Navegacion ────────────────────────────────────────────────────────────────

pg = st.navigation([
    st.Page(page_home, title="METAMATEMÁTICO", icon="🧮", default=True),
    st.Page("pages/1_Visualizaciones.py", title="Visualizaciones", icon="📊"),
])
pg.run()
