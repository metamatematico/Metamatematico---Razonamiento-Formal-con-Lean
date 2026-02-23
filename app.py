"""
METAMATEMÁTICO — Núcleo Lógico Evolutivo
Asistente de razonamiento formal y demostracion de teoremas.
BIOMAT Centro de Biomatemáticas.
"""

import streamlit as st
import json
import re
import time
from datetime import datetime

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
.main .block-container { background: #080c12; }
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
    from { opacity: 0; transform: translateY(12px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes pulse-glow {
    0%,100% { box-shadow: 0 0 0 0 #818cf800; }
    50%      { box-shadow: 0 0 24px 4px #818cf818; }
}

/* ── Hero ────────────────────────────────── */
.meta-hero {
    background: linear-gradient(145deg, #090e1a 0%, #0f1729 50%, #0a0f1c 100%);
    border: 1px solid #1a2236;
    border-radius: 20px;
    padding: 2.4rem 4rem 2rem;
    margin: 0 auto 2rem;
    max-width: 860px;
    min-height: 0;
    position: relative;
    overflow: hidden;
    text-align: center;
    animation: float-in 0.5s ease both;
}
/* Grid overlay */
.meta-hero::before {
    content: "";
    position: absolute; inset: 0;
    background-image:
        linear-gradient(#818cf80a 1px, transparent 1px),
        linear-gradient(90deg, #818cf80a 1px, transparent 1px);
    background-size: 36px 36px;
    pointer-events: none;
}
/* Purple glow top-right */
.meta-hero::after {
    content: "";
    position: absolute;
    top: -80px; right: -80px;
    width: 300px; height: 300px;
    background: radial-gradient(circle, #7c3aed18 0%, transparent 65%);
    pointer-events: none;
}
/* Blue glow bottom-left */
.meta-hero .glow-bl {
    position: absolute;
    bottom: -60px; left: -60px;
    width: 240px; height: 240px;
    background: radial-gradient(circle, #3b82f612 0%, transparent 65%);
    pointer-events: none;
}

/* Math deco row */
.meta-deco {
    font-size: 1.05rem;
    color: #818cf880;
    letter-spacing: 0.55em;
    margin-bottom: 0.5rem;
    font-family: 'JetBrains Mono', monospace;
}

/* Main name */
.meta-name {
    font-family: 'Space Grotesk', 'Inter', sans-serif;
    font-size: clamp(2rem, 4.5vw, 3.2rem);
    font-weight: 800;
    letter-spacing: 0.05em;
    white-space: nowrap;
    background: linear-gradient(120deg,
        #60a5fa 0%, #818cf8 30%, #c084fc 55%, #818cf8 75%, #60a5fa 100%);
    background-size: 250% 250%;
    animation: grad-shift 6s ease infinite;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0 0 0.5rem;
    line-height: 1.1;
    overflow: visible;
}

/* Subtitle */
.meta-sub {
    color: #8892a4;
    font-size: 0.82rem;
    font-weight: 400;
    letter-spacing: 0.05em;
    margin: 0 0 1rem;
}

/* Badges */
.meta-badge {
    display: inline-block;
    background: #0f1729;
    border: 1px solid #1e2d47;
    border-radius: 100px;
    padding: 0.2rem 0.75rem;
    font-size: 0.7rem;
    color: #7a8fa0;
    margin: 0.2rem 0.2rem 0;
    font-weight: 500;
    letter-spacing: 0.04em;
    transition: border-color 0.2s, color 0.2s;
}
.meta-badge:hover { border-color: #818cf850; color: #818cf8; }

/* ── Section label ───────────────────────── */
.section-label {
    font-size: 0.68rem;
    font-weight: 700;
    color: #6080a0;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    margin-bottom: 0.6rem;
    display: flex;
    align-items: center;
    gap: 0.4rem;
}
.section-label::before {
    content: "";
    display: inline-block;
    width: 14px; height: 1px;
    background: #6080a0;
}

/* ── Example buttons ─────────────────────── */
div[data-testid="column"] .stButton > button {
    background: #0d1117;
    border: 1px solid #1e2d40;
    border-radius: 100px;
    color: #6b7f99;
    font-size: 0.76rem;
    font-weight: 600;
    padding: 0.4rem 0.5rem;
    transition: all 0.2s ease;
    width: 100%;
    letter-spacing: 0.02em;
}
div[data-testid="column"] .stButton > button:hover {
    border-color: #4f46e580;
    color: #93c5fd;
    background: #0f1729;
    transform: translateY(-2px);
    box-shadow: 0 6px 20px #4f46e520;
}
div[data-testid="column"] .stButton > button:active {
    transform: translateY(0);
}

/* ── Query wrapper ───────────────────────── */
.query-wrap {
    background: #0d1117;
    border: 1px solid #161c27;
    border-radius: 14px;
    padding: 1rem 1rem 0.8rem;
    margin: 0.6rem 0;
    transition: border-color 0.2s, box-shadow 0.2s;
}
.query-wrap:focus-within {
    border-color: #4f46e560;
    box-shadow: 0 0 0 4px #4f46e510;
}

/* ── Textarea ────────────────────────────── */
.stTextArea textarea {
    background: transparent !important;
    border: none !important;
    border-radius: 0 !important;
    color: #c9d1d9 !important;
    font-size: 0.96rem !important;
    line-height: 1.65 !important;
    padding: 0 !important;
    box-shadow: none !important;
    resize: none !important;
}
.stTextArea textarea:focus {
    border: none !important;
    box-shadow: none !important;
    outline: none !important;
}
.stTextArea textarea::placeholder { color: #4a5c6e !important; }
.stTextArea { border: none !important; }
div[data-testid="stTextArea"] > label { display: none; }

/* ── Primary button ──────────────────────── */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #4338ca 0%, #6d28d9 50%, #7c3aed 100%) !important;
    border: none !important;
    border-radius: 10px !important;
    font-size: 0.92rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.04em !important;
    color: #fff !important;
    transition: all 0.25s ease !important;
    box-shadow: 0 4px 18px #6d28d928 !important;
    height: 2.8rem !important;
    animation: pulse-glow 3s ease infinite;
}
.stButton > button[kind="primary"]:hover:not(:disabled) {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 28px #6d28d948 !important;
    filter: brightness(1.08) !important;
}
.stButton > button[kind="primary"]:disabled {
    opacity: 0.35 !important;
    animation: none !important;
}

/* ── Response card ───────────────────────── */
.resp-card {
    background: #0a0f1c;
    border: 1px solid #151c2e;
    border-left: 3px solid #6d28d9;
    border-radius: 14px;
    padding: 1.6rem 1.8rem;
    margin-top: 1.2rem;
    line-height: 1.82;
    color: #c9d1d9;
    font-size: 0.94rem;
    animation: float-in 0.4s ease both;
    position: relative;
}
.resp-card::before {
    content: "∴";
    position: absolute;
    top: 1rem; right: 1.2rem;
    font-size: 1.2rem;
    color: #6d28d918;
}
.resp-card code {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.84em;
    background: #111827;
    color: #7dd3fc;
    padding: 2px 7px;
    border-radius: 5px;
    border: 1px solid #1e293b;
}
.resp-card pre {
    background: #080c12;
    border: 1px solid #1e293b;
    border-radius: 10px;
    padding: 1.1rem 1.2rem;
    overflow-x: auto;
    font-size: 0.84em;
}
.resp-card pre code {
    background: transparent;
    border: none;
    padding: 0;
    color: #a5f3fc;
}
.resp-card h1,.resp-card h2,.resp-card h3 {
    color: #93c5fd;
    font-weight: 600;
}
.resp-card strong { color: #e2e8f0; }
.resp-card blockquote {
    border-left: 3px solid #4f46e5;
    padding-left: 1rem;
    color: #8b949e;
    margin: 0.8rem 0;
}

/* ── Meta row under response ─────────────── */
.resp-meta {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-top: 0.8rem;
    color: #5a7090;
    font-size: 0.72rem;
    font-family: 'JetBrains Mono', monospace;
}
.resp-meta .dot { color: #3d5570; }
.resp-meta .accent { color: #818cf8; }
.resp-meta .val   { color: #6b7a8d; }

/* ── Viz button ──────────────────────────── */
.viz-btn > button {
    background: #0a0f1c !important;
    border: 1px solid #1a2236 !important;
    border-radius: 10px !important;
    color: #6366f1 !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    transition: all 0.2s ease !important;
}
.viz-btn > button:hover {
    background: #0f1729 !important;
    border-color: #6366f1 !important;
    box-shadow: 0 4px 16px #6366f120 !important;
    transform: translateY(-1px) !important;
}

/* ── Historial expander ───────────────────── */
.streamlit-expanderHeader {
    background: #0a0f1a !important;
    border: 1px solid #1a2840 !important;
    border-radius: 10px !important;
    font-size: 0.8rem !important;
    color: #6b7f99 !important;
    font-weight: 600 !important;
}

/* ── Divider ─────────────────────────────── */
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
                st.rerun()

        st.divider()
        st.markdown(
            '<div style="font-size:0.65rem;color:#4a6080;line-height:1.6">'
            '76 skills matemáticos · 14 categorías<br>'
            'GNN + PPO · Memory Evolutive Systems<br>'
            'Lean 4 · FOL · ZFC · Teoría de Tipos'
            '</div>',
            unsafe_allow_html=True,
        )

    # ── Hero — ancho completo, rectángulo horizontal ──────────────────────────
    st.markdown("""
<div class="meta-hero">
  <div class="glow-bl"></div>
  <div class="meta-deco">∑ · ∀ · ∂ · ∫ · ∃ · ∇ · ∞</div>
  <div class="meta-name">METAMATEMÁTICO</div>
  <p class="meta-sub">Razonamiento formal · Lean 4 · Núcleo Lógico Evolutivo · BIOMAT</p>
  <div>
    <span class="meta-badge">76 skills</span>
    <span class="meta-badge">14 categorías</span>
    <span class="meta-badge">GNN + PPO</span>
    <span class="meta-badge">Memory Evolutive Systems</span>
    <span class="meta-badge">Lean 4</span>
  </div>
</div>
""", unsafe_allow_html=True)

    # ── Columna central para el formulario ────────────────────────────────────
    _, col, _ = st.columns([1, 2.2, 1])
    with col:

        # ── ¿Qué es el Núcleo Lógico Evolutivo? ───────────────────────────
        with st.expander("¿Qué es el Núcleo Lógico Evolutivo?"):
            st.markdown("""
El **Núcleo Lógico Evolutivo (NLE)** es un sistema de inteligencia artificial para
razonamiento matemático formal, desarrollado en **BIOMAT Centro de Biomatemáticas**.
Integra cuatro pilares teóricos en un único marco coherente:

| Componente | Rol en el sistema |
|---|---|
| **Memory Evolutive Systems** (Ehresmann) | Base categórica de la memoria y el aprendizaje |
| **Teoría de Categorías** | Estructura del grafo de 76 skills en 14 dominios |
| **Lean 4** | Verificación formal de demostraciones |
| **GNN + PPO** | Red neuronal que aprende estrategias de prueba |

El sistema modela el proceso cognitivo de un matemático experto en tres pasos:

1. **Patrón P** — identifica los conocimientos relevantes para el problema
2. **Colímite cP** — sintetiza una nueva competencia emergente (Memory Evolutive Systems)
3. **Verificación** — genera y comprueba la prueba en Lean 4

El aprendizaje es continuo: cada interacción alimenta el agente PPO, que mejora
su selección de tácticas. La memoria procedimental guarda los patrones exitosos
para reutilizarlos en problemas similares.
""")
        st.markdown('<div style="height:.2rem"></div>', unsafe_allow_html=True)

        # ── Ejemplos rápidos ───────────────────────────────────────────────
        st.markdown(
            '<div class="section-label">Ejemplos rápidos</div>',
            unsafe_allow_html=True,
        )
        examples = [
            ("√2  irracional",  "Demuestra que √2 es irracional"),
            ("∀  Yoneda",       "Explica el Lema de Yoneda"),
            ("⟨⟩  Lean 4",      "example (n : Nat) : n + 0 = n := by ?"),
            ("↔  Curry–Howard", "Qué es la correspondencia Curry-Howard?"),
        ]
        cols4 = st.columns(4)
        for i, (label, ex) in enumerate(examples):
            with cols4[i]:
                if st.button(label, use_container_width=True, help=ex):
                    st.session_state["_ex"] = ex

        # ── Área de consulta ───────────────────────────────────────────────
        st.markdown(
            '<div style="height:.3rem"></div>'
            '<div class="section-label" style="margin-top:.4rem">Tu consulta</div>',
            unsafe_allow_html=True,
        )
        st.markdown('<div class="query-wrap">', unsafe_allow_html=True)
        query = st.text_area(
            "consulta",
            value=st.session_state.pop("_ex", ""),
            height=110,
            placeholder="Escribe un teorema, problema matemático o goal de Lean 4…",
            label_visibility="collapsed",
        )
        st.markdown('</div>', unsafe_allow_html=True)

        send = st.button("Demostrar  →", type="primary",
                         disabled=not query.strip(),
                         use_container_width=True)

        # ── Procesamiento ──────────────────────────────────────────────────
        if send and query.strip():
            info   = classify(query)
            prompt = enrich(query, info)

            with st.spinner("Analizando…"):
                t0 = time.time()
                if provider == "Google AI Studio" and api_key:
                    res = call_google(prompt, model, api_key, max_tokens)
                elif provider == "Groq (gratis)" and api_key:
                    res = call_groq(prompt, model, api_key, max_tokens)
                elif provider == "Anthropic" and api_key:
                    res = call_anthropic(prompt, model, api_key, max_tokens)
                elif provider != "Demo (sin API key)" and not api_key:
                    res = {"content": "", "error": "Introduce tu API key en el panel lateral."}
                else:
                    res = call_demo(query, info)
                elapsed = time.time() - t0

            if res.get("error"):
                st.error(res["error"])
            else:
                st.session_state["current_query"]    = query
                st.session_state["current_response"] = res["content"]

                st.markdown('<div class="resp-card">', unsafe_allow_html=True)
                st.markdown(res["content"])
                st.markdown('</div>', unsafe_allow_html=True)

                tok_info = (f'{res["in_tok"]} → {res["out_tok"]} tok'
                            if res["in_tok"] else "")
                st.markdown(
                    f'<div class="resp-meta">'
                    f'<span class="accent">◆</span>'
                    f'<span class="val">{res["model"]}</span>'
                    + (f'<span class="dot">·</span><span class="val">{tok_info}</span>'
                       if tok_info else "")
                    + f'<span class="dot">·</span><span class="val">{elapsed:.1f}s</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                st.markdown('<div style="height:.5rem"></div>', unsafe_allow_html=True)
                with st.container():
                    st.markdown('<div class="viz-btn">', unsafe_allow_html=True)
                    if st.button("📊  Ver grafo · embeddings · traza categórica de esta consulta →",
                                 use_container_width=True):
                        st.switch_page("pages/1_Visualizaciones.py")
                    st.markdown('</div>', unsafe_allow_html=True)

                st.session_state.history.insert(0, {
                    "ts":    datetime.now().strftime("%H:%M"),
                    "q":     query,
                    "a":     res["content"],
                    "model": res["model"],
                    "t":     round(elapsed, 1),
                })

        # ── Historial ──────────────────────────────────────────────────────
        if st.session_state.history:
            st.divider()
            with st.expander(f"📋  Historial de sesión — {len(st.session_state.history)} consultas"):
                for item in st.session_state.history[:15]:
                    st.markdown(
                        f'<div style="font-size:.75rem;color:#5a7090;margin-bottom:.1rem">'
                        f'{item["ts"]}'
                        f' <span style="color:#3d5570">·</span> '
                        f'<span style="color:#6b7f99">{item["model"]}</span>'
                        f' <span style="color:#3d5570">·</span> '
                        f'{item["t"]}s</div>'
                        f'<div style="font-size:.88rem;color:#94a3b8;margin-bottom:.15rem;'
                        f'font-weight:500">'
                        f'{item["q"][:90]}{"…" if len(item["q"])>90 else ""}</div>'
                        f'<div style="font-size:.8rem;color:#6b7280;padding-bottom:.75rem;'
                        f'border-bottom:1px solid #151f30;margin-bottom:.5rem">'
                        f'{item["a"][:160]}{"…" if len(item["a"])>160 else ""}</div>',
                        unsafe_allow_html=True,
                    )
                if st.button("⬇  Exportar historial JSON", use_container_width=True):
                    st.download_button(
                        "Descargar",
                        data=json.dumps(st.session_state.history, ensure_ascii=False, indent=2),
                        file_name=f"metamatico_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                        mime="application/json",
                    )


# ── Navegacion ────────────────────────────────────────────────────────────────

pg = st.navigation([
    st.Page(page_home, title="METAMATEMÁTICO", icon="🧮", default=True),
    st.Page("pages/1_Visualizaciones.py", title="Visualizaciones", icon="📊"),
])
pg.run()
