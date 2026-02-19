"""
NLE v7.0 — Demostrador Matematico
Entry point con navegacion multi-pagina.
"""

import streamlit as st
import json
import re
import time
from datetime import datetime

st.set_page_config(
    page_title="NLE v7.0 — Demostrador Matematico",
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
            f"```lean4\n-- Cascade NLE v7.0\n"
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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

*, body { font-family: 'Inter', sans-serif; }

/* ── Sidebar ─────────────────────────────── */
section[data-testid="stSidebar"] {
    background: #080c12 !important;
    border-right: 1px solid #1c2333;
}
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stSlider label,
section[data-testid="stSidebar"] .stTextInput label {
    font-size: 0.78rem;
    font-weight: 500;
    color: #6e7681;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

/* ── Hero header ─────────────────────────── */
.nle-hero {
    background: linear-gradient(135deg, #0d1424 0%, #111827 50%, #0d1117 100%);
    border: 1px solid #1c2333;
    border-radius: 14px;
    padding: 1.8rem 2rem 1.4rem;
    margin-bottom: 1.6rem;
    position: relative;
    overflow: hidden;
}
.nle-hero::before {
    content: "";
    position: absolute;
    top: -40px; right: -40px;
    width: 180px; height: 180px;
    background: radial-gradient(circle, #818cf820 0%, transparent 70%);
    pointer-events: none;
}
.nle-title {
    font-size: 1.65rem;
    font-weight: 700;
    background: linear-gradient(135deg, #93c5fd, #818cf8, #c084fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin: 0 0 0.3rem;
    line-height: 1.2;
}
.nle-subtitle {
    color: #6e7681;
    font-size: 0.82rem;
    font-weight: 400;
    margin: 0;
    letter-spacing: 0.02em;
}
.nle-badge {
    display: inline-block;
    background: #1c2333;
    border: 1px solid #2d3748;
    border-radius: 20px;
    padding: 0.18rem 0.65rem;
    font-size: 0.72rem;
    color: #8b949e;
    margin-right: 0.4rem;
    margin-top: 0.7rem;
}

/* ── Quick example buttons ───────────────── */
div[data-testid="column"] .stButton > button {
    background: #111827;
    border: 1px solid #1f2937;
    border-radius: 20px;
    color: #6e7681;
    font-size: 0.78rem;
    font-weight: 500;
    padding: 0.35rem 0.6rem;
    transition: all 0.18s ease;
    width: 100%;
}
div[data-testid="column"] .stButton > button:hover {
    border-color: #818cf8;
    color: #93c5fd;
    background: #131c2e;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px #818cf820;
}

/* ── Textarea ────────────────────────────── */
.stTextArea textarea {
    background: #111827 !important;
    border: 1px solid #1f2937 !important;
    border-radius: 10px !important;
    color: #c9d1d9 !important;
    font-size: 0.95rem !important;
    line-height: 1.6 !important;
    transition: border-color 0.2s;
}
.stTextArea textarea:focus {
    border-color: #818cf8 !important;
    box-shadow: 0 0 0 3px #818cf815 !important;
}

/* ── Send button ─────────────────────────── */
div[data-testid="stMainBlockContainer"] > div > div > div .stButton:last-of-type > button[kind="primary"],
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #4f46e5, #7c3aed) !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    letter-spacing: 0.02em !important;
    transition: all 0.2s ease !important;
    box-shadow: 0 4px 14px #7c3aed30 !important;
}
.stButton > button[kind="primary"]:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px #7c3aed45 !important;
}

/* ── Response card ───────────────────────── */
.resp-card {
    background: #0d1117;
    border: 1px solid #1c2333;
    border-left: 3px solid #818cf8;
    border-radius: 12px;
    padding: 1.5rem 1.8rem;
    margin-top: 1rem;
    line-height: 1.78;
    color: #c9d1d9;
    font-size: 0.93rem;
}
.resp-card code {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.85em;
    background: #161b22;
    color: #79c0ff;
    padding: 2px 6px;
    border-radius: 4px;
}
.resp-card pre {
    background: #161b22;
    border: 1px solid #21262d;
    border-radius: 8px;
    padding: 1rem;
    overflow-x: auto;
    font-size: 0.85em;
}
.resp-meta {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-top: 0.7rem;
    color: #3d444d;
    font-size: 0.74rem;
    font-family: 'JetBrains Mono', monospace;
}
.resp-meta span { color: #484f58; }

/* ── Divider / HR ────────────────────────── */
hr { border-color: #1c2333 !important; }

/* ── Expander ────────────────────────────── */
.streamlit-expanderHeader {
    background: #111827 !important;
    border-radius: 8px !important;
    font-size: 0.85rem !important;
    color: #6e7681 !important;
}
</style>
""", unsafe_allow_html=True)

    if "history" not in st.session_state:
        st.session_state.history = []

    # ── Sidebar ───────────────────────────────────────────────────────────────
    with st.sidebar:
        st.markdown("""
<div style="padding:0.5rem 0 0.2rem">
  <div style="font-size:1.1rem;font-weight:700;color:#93c5fd;letter-spacing:-0.01em">🧮 NLE v7.0</div>
  <div style="font-size:0.72rem;color:#3d444d;margin-top:2px">BIOMAT · UNAM · 2025</div>
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
        max_tokens = st.slider("Tokens", 256, 4096, 1024, 128)

        st.divider()

        n_hist = len(st.session_state.history)
        st.markdown(
            f'<div style="font-size:0.78rem;color:#6e7681;text-transform:uppercase;'
            f'letter-spacing:.06em;margin-bottom:.4rem">Sesión</div>'
            f'<div style="font-size:1.5rem;font-weight:700;color:#c9d1d9">{n_hist}'
            f'<span style="font-size:.8rem;font-weight:400;color:#484f58"> consultas</span></div>',
            unsafe_allow_html=True,
        )
        if n_hist and st.button("Limpiar historial", use_container_width=True):
            st.session_state.history = []
            st.rerun()

    # ── Contenido central ─────────────────────────────────────────────────────
    _, col, _ = st.columns([1, 2, 1])
    with col:

        # Hero
        st.markdown("""
<div class="nle-hero">
  <p class="nle-title">Demostrador Matemático</p>
  <p class="nle-subtitle">Razonamiento formal · Lean 4 · Memory Evolutive Systems</p>
  <span class="nle-badge">76 skills</span>
  <span class="nle-badge">14 categorías</span>
  <span class="nle-badge">GNN + PPO</span>
  <span class="nle-badge">NLE v7.0</span>
</div>
""", unsafe_allow_html=True)

        # Ejemplos rápidos
        st.markdown(
            '<div style="font-size:0.74rem;color:#484f58;text-transform:uppercase;'
            'letter-spacing:.07em;margin-bottom:.5rem">Ejemplos rápidos</div>',
            unsafe_allow_html=True,
        )
        examples = [
            ("√2 irracional",   "Demuestra que √2 es irracional"),
            ("Yoneda",          "Explica el Lema de Yoneda"),
            ("Lean 4",          "example (n : Nat) : n + 0 = n := by ?"),
            ("Curry-Howard",    "Qué es la correspondencia Curry-Howard?"),
        ]
        cols4 = st.columns(4)
        for i, (label, ex) in enumerate(examples):
            with cols4[i]:
                if st.button(label, use_container_width=True, help=ex):
                    st.session_state["_ex"] = ex

        # Área de consulta
        st.markdown('<div style="height:.4rem"></div>', unsafe_allow_html=True)
        query = st.text_area(
            "query",
            value=st.session_state.pop("_ex", ""),
            height=120,
            placeholder="Escribe tu problema matemático o goal de Lean 4...",
            label_visibility="collapsed",
        )

        send = st.button("Enviar →", type="primary", disabled=not query.strip(),
                         use_container_width=True)

        # ── Procesamiento ──────────────────────────────────────────────────
        if send and query.strip():
            info = classify(query)
            prompt = enrich(query, info)

            with st.spinner("Procesando…"):
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
                # Guardar consulta activa para visualizaciones
                st.session_state["current_query"] = query
                st.session_state["current_response"] = res["content"]

                # Render respuesta como markdown dentro de la tarjeta
                st.markdown('<div class="resp-card">', unsafe_allow_html=True)
                st.markdown(res["content"])
                st.markdown('</div>', unsafe_allow_html=True)

                tok_info = (f'{res["in_tok"]} → {res["out_tok"]} tok'
                            if res["in_tok"] else "")
                st.markdown(
                    f'<div class="resp-meta">'
                    f'<span style="color:#818cf8">◆</span>'
                    f'<span>{res["model"]}</span>'
                    f'{"<span>·</span><span>" + tok_info + "</span>" if tok_info else ""}'
                    f'<span>·</span><span>{elapsed:.1f}s</span>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

                # Botón para ver visualizaciones contextuales
                st.markdown('<div style="height:.6rem"></div>', unsafe_allow_html=True)
                if st.button("📊 Ver grafo de skills y traza de esta consulta →",
                             use_container_width=True):
                    st.switch_page("pages/1_Visualizaciones.py")

                st.session_state.history.insert(0, {
                    "ts": datetime.now().strftime("%H:%M"),
                    "q": query,
                    "a": res["content"],
                    "model": res["model"],
                    "t": round(elapsed, 1),
                })

        # ── Historial ──────────────────────────────────────────────────────
        if st.session_state.history:
            st.divider()
            with st.expander(f"Historial — {len(st.session_state.history)} consultas"):
                for item in st.session_state.history[:15]:
                    st.markdown(
                        f'<div style="font-size:.8rem;color:#484f58;margin-bottom:.15rem">'
                        f'{item["ts"]} · <span style="color:#6e7681">{item["model"]}</span>'
                        f' · {item["t"]}s</div>'
                        f'<div style="font-size:.9rem;color:#c9d1d9;margin-bottom:.2rem">'
                        f'{item["q"][:90]}{"…" if len(item["q"])>90 else ""}</div>'
                        f'<div style="font-size:.82rem;color:#484f58;padding-bottom:.8rem;'
                        f'border-bottom:1px solid #1c2333">'
                        f'{item["a"][:180]}{"…" if len(item["a"])>180 else ""}</div>',
                        unsafe_allow_html=True,
                    )
                st.markdown('<div style="height:.5rem"></div>', unsafe_allow_html=True)
                if st.button("Exportar JSON"):
                    st.download_button(
                        "Descargar historial",
                        data=json.dumps(st.session_state.history, ensure_ascii=False, indent=2),
                        file_name=f"historial_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
                        mime="application/json",
                    )


# ── Navegacion ────────────────────────────────────────────────────────────────

pg = st.navigation([
    st.Page(page_home, title="Demostrador", icon="🧮", default=True),
    st.Page("pages/1_Visualizaciones.py", title="Visualizaciones", icon="📊"),
])
pg.run()
