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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono&display=swap');
*, body { font-family: 'Inter', sans-serif; }

.response-box {
    background: #0d1117;
    border: 1px solid #21262d;
    border-radius: 10px;
    padding: 1.4rem 1.6rem;
    color: #c9d1d9;
    line-height: 1.75;
    font-size: 0.95rem;
    white-space: pre-wrap;
}
.meta { color: #484f58; font-size: 0.76rem; margin-top: 0.6rem; }
code { font-family: 'JetBrains Mono', monospace; font-size: 0.88em;
       background: #161b22; color: #79c0ff; padding: 1px 5px; border-radius: 4px; }
section[data-testid="stSidebar"] { background: #0d1117; border-right: 1px solid #21262d; }
hr { border-color: #21262d; }
</style>
""", unsafe_allow_html=True)

    if "history" not in st.session_state:
        st.session_state.history = []

    # Sidebar
    with st.sidebar:
        st.markdown("## ∑ Demostrador")
        st.caption("NLE v7.0 — UNAM 2025")
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
        max_tokens = st.slider("Tokens maximos", 256, 4096, 1024, 128)

        st.divider()
        st.metric("Consultas", len(st.session_state.history))
        if st.button("Limpiar historial", use_container_width=True):
            st.session_state.history = []
            st.rerun()

    # Centrar contenido en layout wide
    _, col, _ = st.columns([1, 2, 1])
    with col:
        st.markdown("### Problema matematico")

        cols = st.columns(4)
        examples = [
            "Demuestra que √2 es irracional",
            "Explica el Lema de Yoneda",
            "example (n : Nat) : n + 0 = n := by ?",
            "Que es la correspondencia Curry-Howard?",
        ]
        labels = ["Conjuntos", "Categorias", "Lean 4", "Tipos"]
        for i, c in enumerate(cols):
            with c:
                if st.button(labels[i], use_container_width=True, help=examples[i]):
                    st.session_state["_ex"] = examples[i]

        query = st.text_area(
            "query",
            value=st.session_state.pop("_ex", ""),
            height=110,
            placeholder="Escribe tu problema matematico...",
            label_visibility="collapsed",
        )

        send = st.button("Enviar →", type="primary", disabled=not query.strip())

        if send and query.strip():
            info = classify(query)
            prompt = enrich(query, info)

            with st.spinner(""):
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
                st.markdown(
                    f'<div class="response-box">{res["content"]}</div>',
                    unsafe_allow_html=True,
                )
                st.markdown(
                    f'<div class="meta">{res["model"]} · '
                    f'{res["in_tok"]} → {res["out_tok"]} tokens · {elapsed:.1f}s</div>',
                    unsafe_allow_html=True,
                )
                st.session_state.history.insert(0, {
                    "ts": datetime.now().strftime("%H:%M"),
                    "q": query,
                    "a": res["content"],
                    "model": res["model"],
                    "t": round(elapsed, 1),
                })

        if st.session_state.history:
            st.divider()
            with st.expander(f"Historial ({len(st.session_state.history)})"):
                for item in st.session_state.history[:15]:
                    st.markdown(f"**{item['ts']}** — {item['q'][:80]}{'…' if len(item['q'])>80 else ''}")
                    st.caption(f"{item['a'][:200]}{'…' if len(item['a'])>200 else ''}")
                    st.markdown("---")

                if st.button("Exportar JSON"):
                    st.download_button(
                        "Descargar",
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
