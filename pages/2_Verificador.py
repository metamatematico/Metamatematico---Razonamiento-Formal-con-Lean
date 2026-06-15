"""
Verificador de Demostraciones y Conjeturas
==========================================
Carga un archivo .txt, .tex o .pdf con una demostración o conjetura matemática.
El NLE la analiza, intenta formalizarla en Lean 4 y reporta si es correcta.
"""
from __future__ import annotations

import os
import re
import sys
import time
from pathlib import Path

import streamlit as st

# ─── Estilo ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.block-container { padding-top: 1.5rem; }
h1, h2, h3 { color: #c9d1d9; }
.result-box {
    background: #131c2e; border: 1px solid #30363d;
    border-radius: 10px; padding: 1rem 1.2rem; margin-top: 1rem;
}
section[data-testid="stSidebar"] {
    background: #0a0a12 !important;
    border-right: 1px solid #2a2a48;
}
section[data-testid="stSidebar"] .stSelectbox label,
section[data-testid="stSidebar"] .stSlider  label,
section[data-testid="stSidebar"] .stTextInput label {
    font-size: 0.73rem;
    font-weight: 600;
    color: #5858a0;
    text-transform: uppercase;
    letter-spacing: 0.09em;
}
</style>
""", unsafe_allow_html=True)

# ─── Sidebar: configuración API (independiente del chat principal) ─────────────

_PROVIDERS = {
    "Anthropic": {
        "models": ["claude-haiku-4-5-20251001", "claude-sonnet-4-6"],
        "key_label": "Anthropic API Key",
        "key_placeholder": "sk-ant-...",
        "key_help": "Obtener en console.anthropic.com",
        "env_var": "ANTHROPIC_API_KEY",
    },
    "Google AI Studio": {
        "models": ["gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-1.5-flash", "gemini-1.5-pro"],
        "key_label": "Google AI Studio API Key",
        "key_placeholder": "AIza...",
        "key_help": "Obtener gratis en aistudio.google.com",
        "env_var": "GOOGLE_API_KEY",
    },
    "Groq (gratis)": {
        "models": ["llama-3.3-70b-versatile", "gemma2-9b-it", "mixtral-8x7b-32768", "llama-3.1-8b-instant"],
        "key_label": "Groq API Key",
        "key_placeholder": "gsk_...",
        "key_help": "Obtener gratis en console.groq.com",
        "env_var": "GROQ_API_KEY",
    },
    "DeepSeek": {
        "models": ["deepseek-chat", "deepseek-reasoner"],
        "key_label": "DeepSeek API Key",
        "key_placeholder": "sk-...",
        "key_help": "Obtener en platform.deepseek.com",
        "env_var": "DEEPSEEK_API_KEY",
    },
    "Demo (sin API key)": {
        "models": ["demo"],
        "key_label": None,
        "env_var": None,
    },
}

_PROVIDER_MAP = {
    "Google AI Studio":   "google",
    "Groq (gratis)":      "groq",
    "Anthropic":          "anthropic",
    "DeepSeek":           "deepseek",
    "Demo (sin API key)": "demo",
}

with st.sidebar:
    st.markdown("""
<div style="padding:0.8rem 0 0.5rem">
  <div style="font-family:'Space Grotesk','Inter',sans-serif;font-size:1.05rem;font-weight:800;
              letter-spacing:0.04em;
              background:linear-gradient(120deg,#e8e8ff,#b04fff,#06d6c7);
              -webkit-background-clip:text;-webkit-text-fill-color:transparent;
              background-clip:text">METAMATEMÁTICO</div>
  <div style="font-size:0.67rem;color:#5858a0;margin-top:5px;letter-spacing:0.07em;
              text-transform:uppercase;font-weight:600">🔬 Verificador</div>
</div>
""", unsafe_allow_html=True)
    st.divider()

    # Pre-seleccionar el proveedor del chat principal si está en la misma sesión
    _prov_list = list(_PROVIDERS.keys())
    _default_prov = st.session_state.get("_provider", "Anthropic")
    _default_idx = _prov_list.index(_default_prov) if _default_prov in _prov_list else 0

    v_provider = st.selectbox("Proveedor", _prov_list, index=_default_idx)
    v_cfg = _PROVIDERS[v_provider]

    v_api_key = ""
    if v_cfg["key_label"]:
        # Pre-rellenar con el valor del chat principal (misma sesión) o variable de entorno
        _pre = st.session_state.get("_api_key", "")
        if not _pre and v_cfg["env_var"]:
            try:
                _pre = st.secrets.get(v_cfg["env_var"], "")
            except Exception:
                _pre = os.environ.get(v_cfg["env_var"], "")
        # Force-sync: once a keyed widget exists in session_state, value= is ignored.
        if _pre:
            st.session_state["_v_api_key_input"] = _pre
        v_api_key = st.text_input(
            v_cfg["key_label"],
            value=_pre,
            type="password",
            placeholder=v_cfg["key_placeholder"],
            help=v_cfg.get("key_help", ""),
            key="_v_api_key_input",
        )

    v_model = st.selectbox("Modelo", v_cfg["models"])
    v_max_tokens = st.slider(
        "Tokens máx.", 256, 4096,
        st.session_state.get("_max_tokens", 1024),
        128,
    )
    # Sincronizar API key en env var y session_state para que persista entre páginas
    if v_api_key:
        st.session_state["_api_key"] = v_api_key
        _key_env_map = {
            "anthropic": "ANTHROPIC_API_KEY",
            "google":    "GOOGLE_API_KEY",
            "groq":      "GROQ_API_KEY",
            "deepseek":  "DEEPSEEK_API_KEY",
        }
        _env_name = _key_env_map.get(_PROVIDER_MAP.get(v_provider, ""), "")
        if _env_name:
            os.environ[_env_name] = v_api_key

    st.divider()
    if st.button("← Volver al chat", use_container_width=True):
        home = st.session_state.get("_home_page")
        if home:
            st.switch_page(home)
        else:
            st.rerun()

    st.divider()
    st.markdown(
        '<div style="font-size:0.64rem;color:#5858a0;line-height:1.7">'
        '76 skills matemáticos · 14 categorías<br>'
        'GNN + PPO · Lean 4 · Mathlib'
        '</div>',
        unsafe_allow_html=True,
    )


# ─── Cabecera ────────────────────────────────────────────────────────────────

st.title("🔬 Verificador de Demostraciones")
st.markdown(
    "Carga un archivo **`.txt`**, **`.tex`** (LaTeX) o **`.pdf`** con una demostración "
    "o conjetura matemática. El Núcleo Lógico Evolutivo la leerá, intentará formalizarla "
    "en **Lean 4** y reportará si es matemáticamente correcta."
)
st.divider()


# ─── Extracción de texto ──────────────────────────────────────────────────────

def _extract_pdf(data: bytes) -> str:
    try:
        import fitz
        doc = fitz.open(stream=data, filetype="pdf")
        pages_text = [page.get_text("text") for page in doc]
        doc.close()
        return "\n\n".join(pages_text)
    except Exception as e:
        return f"[Error al leer el PDF: {e}]"


_LATEX_ENVS = re.compile(
    r'\\begin\{(theorem|Theorem|lemma|Lemma|proposition|Proposition|'
    r'corollary|Corollary|definition|Definition|proof|Proof|'
    r'claim|Claim|conjecture|Conjecture|remark|Remark|example|Example)\*?\}'
    r'(.*?)'
    r'\\end\{\1\*?\}',
    re.DOTALL,
)


def _extract_latex_blocks(tex: str) -> list[dict]:
    blocks = []
    for m in _LATEX_ENVS.finditer(tex):
        env = m.group(1).lower()
        content = m.group(2).strip()
        if len(content) > 10:
            blocks.append({"type": env, "content": content})
    return blocks


def _strip_latex(tex: str) -> str:
    tex = re.sub(r'\\(text|mathrm|mathit|mathbf|mathbb|emph)\{([^}]+)\}', r'\2', tex)
    tex = re.sub(r'\\(label|ref|cite|footnote|index)\{[^}]*\}', '', tex)
    tex = re.sub(r'%.*', '', tex)
    tex = re.sub(r'\s+', ' ', tex)
    return tex.strip()


def _is_latex_content(text: str) -> bool:
    markers = [r'\begin{', r'\end{', r'\frac', r'\forall', r'\exists',
               r'\mathbb', r'\mathcal', r'\sum', r'\prod', r'\int']
    return any(m in text for m in markers)


# ─── Nucleo — compartido con app.py via cache_resource ────────────────────────

def _get_nucleo():
    for mod_name in ("__main__", "app"):
        mod = sys.modules.get(mod_name)
        if mod is not None and hasattr(mod, "_get_nucleo"):
            return mod._get_nucleo()
    import importlib
    root = str(Path(__file__).parent.parent)
    if root not in sys.path:
        sys.path.insert(0, root)
    return importlib.import_module("app")._get_nucleo()


# ─── Construcción del prompt de verificación ──────────────────────────────────

def _build_verify_prompt(content: str, filename: str, mode: str,
                         content_type: str) -> str:
    is_latex = _is_latex_content(content)
    fmt_tag  = "[LaTeX]" if is_latex else "[Texto plano]"

    mode_instructions = {
        "Verificar demostración": (
            "El siguiente texto contiene una demostración matemática. Tu tarea es:\n"
            "1. Identificar el enunciado principal que se está demostrando.\n"
            "2. Formalizarlo como un `theorem` o `lemma` en Lean 4 con los imports de Mathlib.\n"
            "3. Intentar reproducir la demostración con tácticas Lean.\n"
            "4. Reportar si la demostración es correcta, incompleta o contiene errores."
        ),
        "Evaluar conjetura": (
            "El siguiente texto contiene una conjetura matemática (no demostrada). Tu tarea es:\n"
            "1. Identificar el enunciado de la conjetura.\n"
            "2. Formalizarlo en Lean 4.\n"
            "3. Intentar verificarlo con las tácticas disponibles (norm_num, ring, omega, etc.).\n"
            "4. Si Lean no puede verificarlo, explicar qué parte requeriría demostración adicional."
        ),
        "Solo formalizar en Lean 4": (
            "El siguiente texto contiene un enunciado matemático. Tu tarea es:\n"
            "1. Escribir el código Lean 4 equivalente con los imports correctos de Mathlib.\n"
            "2. Asegurarte de que la sintaxis sea válida (puedes usar `sorry` para huecos).\n"
            "3. Explicar qué representa cada línea del código generado."
        ),
        "Detectar errores": (
            "El siguiente texto contiene un argumento matemático. Tu tarea es:\n"
            "1. Formalizarlo en Lean 4.\n"
            "2. Identificar errores lógicos o pasos inválidos que Lean rechace.\n"
            "3. Explicar cada error encontrado y cómo podría corregirse."
        ),
    }

    instr = mode_instructions.get(mode, mode_instructions["Verificar demostración"])
    return (
        f"{instr}\n\n"
        f"Archivo: `{filename}` — Tipo: {content_type} {fmt_tag}\n\n"
        f"--- CONTENIDO ---\n{content}\n--- FIN DEL CONTENIDO ---"
    )


# ─── UI Principal ─────────────────────────────────────────────────────────────

col_upload, col_config = st.columns([2, 1])

with col_upload:
    uploaded = st.file_uploader(
        "Carga tu archivo matemático",
        type=["txt", "tex", "latex", "pdf"],
        help="Soporta texto plano (.txt), LaTeX (.tex / .latex) y PDF (.pdf)",
        label_visibility="collapsed",
    )
    if not uploaded:
        st.markdown("""
        <div style="background:#0d1117;border:2px dashed #30363d;border-radius:12px;
                    padding:2rem;text-align:center;color:#6e7681;">
        <div style="font-size:2.5rem">📁</div>
        <div style="margin-top:.5rem">Arrastra un archivo aquí o haz click arriba</div>
        <div style="font-size:.8rem;margin-top:.3rem">.txt · .tex · .latex · .pdf</div>
        </div>
        """, unsafe_allow_html=True)

with col_config:
    st.markdown("**Tipo de análisis**")
    mode = st.radio(
        "modo",
        ["Verificar demostración", "Evaluar conjetura",
         "Solo formalizar en Lean 4", "Detectar errores"],
        label_visibility="collapsed",
    )
    st.markdown("**Límite de caracteres**")
    max_chars = st.slider("max_chars", 500, 8000, 3000, 500, label_visibility="collapsed",
                          help="Caracteres máximos enviados al NLE (archivos grandes se truncan)")

if not uploaded:
    st.stop()

# ─── Procesar archivo ─────────────────────────────────────────────────────────

raw_bytes = uploaded.read()
fname     = uploaded.name
ext       = Path(fname).suffix.lower()

with st.spinner("Leyendo archivo…"):
    if ext == ".pdf":
        text_original = _extract_pdf(raw_bytes)
        is_latex = False
        latex_blocks: list[dict] = []
    elif ext in (".tex", ".latex"):
        text_original = raw_bytes.decode("utf-8", errors="replace")
        latex_blocks  = _extract_latex_blocks(text_original)
        is_latex      = True
    else:
        text_original = raw_bytes.decode("utf-8", errors="replace")
        is_latex      = _is_latex_content(text_original)
        latex_blocks  = _extract_latex_blocks(text_original) if is_latex else []

# ─── Preview del archivo ──────────────────────────────────────────────────────

st.markdown(f"### 📄 `{fname}`")

tab_preview, tab_bloques = st.tabs(["Vista del archivo", "Bloques matemáticos detectados"])

with tab_preview:
    if ext == ".pdf":
        st.text_area("Texto extraído del PDF", value=text_original[:3000], height=250,
                     disabled=True, label_visibility="collapsed")
        if len(text_original) > 3000:
            st.caption(f"Mostrando los primeros 3,000 de {len(text_original):,} caracteres.")
    else:
        st.code(text_original[:3000], language="latex" if is_latex else "text")
        if len(text_original) > 3000:
            st.caption(f"Mostrando los primeros 3,000 de {len(text_original):,} caracteres.")

with tab_bloques:
    if latex_blocks:
        st.success(f"Se encontraron **{len(latex_blocks)}** bloques matemáticos en el archivo.")
        for i, b in enumerate(latex_blocks):
            ico = {"theorem": "📐", "lemma": "📎", "proof": "✏️", "definition": "📖",
                   "conjecture": "❓", "corollary": "➡️", "proposition": "💡"}.get(b["type"], "•")
            with st.expander(f"{ico} **{b['type'].capitalize()}** #{i+1} "
                             f"— {_strip_latex(b['content'])[:70]}…"):
                st.code(b["content"][:800], language="latex")
    else:
        if is_latex or ext in (".tex", ".latex"):
            st.warning("No se encontraron entornos theorem/lemma/proof explícitos. "
                       "Se analizará el archivo completo.")
        else:
            st.info("Archivo de texto plano — se analizará el contenido completo.")

# ─── Selector de contenido a verificar ───────────────────────────────────────

st.divider()
st.markdown("### 🎯 ¿Qué quieres verificar?")

if latex_blocks:
    block_options = {
        f"[{i+1}] {b['type'].capitalize()} — {_strip_latex(b['content'])[:60]}…": i
        for i, b in enumerate(latex_blocks)
    }
    block_options["📄 Analizar el archivo completo"] = -1

    selected_label = st.selectbox(
        "Selecciona el bloque o el documento completo",
        list(block_options.keys()),
        label_visibility="collapsed",
    )
    selected_idx = block_options[selected_label]

    if selected_idx == -1:
        content_to_verify = text_original[:max_chars]
        content_type = "documento completo"
    else:
        content_to_verify = latex_blocks[selected_idx]["content"]
        content_type = latex_blocks[selected_idx]["type"]
else:
    content_to_verify = text_original[:max_chars]
    content_type = "texto"

with st.expander("Ver lo que se enviará al NLE", expanded=False):
    st.code(content_to_verify[:1500], language="latex" if _is_latex_content(content_to_verify) else "text")
    if len(content_to_verify) > 1500:
        st.caption(f"… y {len(content_to_verify)-1500} caracteres más.")
    st.caption(f"Total: {len(content_to_verify):,} caracteres · Tipo: {content_type}")

# ─── Verificación ─────────────────────────────────────────────────────────────

st.divider()

# Validar que hay API key antes de mostrar el botón
if not v_api_key and v_provider != "Demo (sin API key)":
    st.warning(
        f"⚠️ Introduce tu **{v_cfg['key_label']}** en el panel izquierdo para usar el Verificador. "
        f"Si acabas de ponerla en el chat principal y estás en la misma pestaña, "
        f"ya debería aparecer pre-rellenada arriba."
    )

col_btn, col_hint = st.columns([2, 3])
with col_btn:
    run = st.button("🔬 Verificar con Lean 4", type="primary", use_container_width=True,
                    disabled=(not v_api_key and v_provider != "Demo (sin API key)"))
with col_hint:
    _model_str = f"`{v_model}`" if v_provider != "Demo (sin API key)" else "modo demo"
    st.markdown(
        f"<div style='padding:.6rem;color:#6e7681;font-size:.85rem'>"
        f"Proveedor: <b>{v_provider}</b> · modelo {_model_str}<br>"
        f"Primera verificación del día puede tardar <b>~2 min</b> (carga de Mathlib).</div>",
        unsafe_allow_html=True,
    )

if not run:
    st.stop()

# ─── Ejecutar verificación ────────────────────────────────────────────────────

prompt = _build_verify_prompt(content_to_verify, fname, mode, content_type)

nucleo = _get_nucleo()
if nucleo is None:
    st.error("El Núcleo no está disponible. Recarga la aplicación.")
    st.stop()

# Configurar el LLM con los valores del sidebar de esta página
try:
    nucleo.reconfigure_llm(
        _PROVIDER_MAP.get(v_provider, "demo"),
        v_model,
        v_api_key,
        v_max_tokens,
    )
except Exception as _recfg_err:
    st.warning(f"No se pudo reconfigurar el LLM: {_recfg_err}")

t0 = time.time()
_lean_info = st.info(
    "⏳ El NLE está formalizando en Lean 4… "
    "La **primera verificación del día** puede tardar hasta ~2 minutos "
    "mientras Mathlib carga sus módulos compilados (.olean). "
    "Las verificaciones siguientes serán rápidas (~10 s).",
    icon=None,
)

try:
    with st.spinner("Verificando con Lean 4 + Mathlib…"):
        nr = nucleo.process_sync(prompt)
    elapsed = time.time() - t0
    _lean_info.empty()
except Exception as e:
    import traceback, logging
    logging.getLogger(__name__).error(
        f"Error verificador: {e}\n{traceback.format_exc()}"
    )
    _lean_info.empty()
    st.error(f"Error durante la verificación: {e}")
    with st.expander("🔍 Traceback completo"):
        st.code(traceback.format_exc())
    st.stop()

# ─── Mostrar resultado ────────────────────────────────────────────────────────

conf     = getattr(nr, "confidence", 0.5)
lean_res = getattr(nr, "lean_result", None)

if conf >= 0.9:
    st.success(f"✅ **Verificado formalmente por Lean 4** — confianza: {conf:.0%}")
elif conf >= 0.7:
    st.warning(f"⚠️ **Verificación parcial** — confianza: {conf:.0%}")
elif conf >= 0.5:
    st.warning(f"⚠️ **Formalizado con huecos (sorry)** — confianza: {conf:.0%}")
else:
    st.error(f"❌ **No verificado** — confianza: {conf:.0%}")

mc1, mc2, mc3 = st.columns(3)
mc1.metric("Confianza NLE", f"{conf:.0%}")
mc2.metric("Tiempo", f"{elapsed:.1f} s")
if lean_res:
    status_label = {
        "SUCCESS":       "✅ Lean OK",
        "SORRY":         "⚠️ Sorry parcial",
        "ERROR":         "❌ Error Lean",
        "TIMEOUT":       "⏱ Timeout",
        "NOT_AVAILABLE": "☁️ Sin entorno",
    }.get(lean_res.status.name if hasattr(lean_res.status, "name") else str(lean_res.status), "—")
    mc3.metric("Lean 4", status_label)
else:
    mc3.metric("Lean 4", "—")

st.divider()
st.markdown("### 📊 Análisis del NLE")
st.markdown(nr.content)

# ─── Detalle del error Lean (cuando hay error real de compilación) ────────────
if lean_res and hasattr(lean_res, "status") and lean_res.status.name == "ERROR":
    with st.expander("🔍 Ver error exacto de Lean 4"):
        _lean_msgs = getattr(lean_res, "messages", []) or []
        if _lean_msgs:
            for _m in _lean_msgs:
                _sev  = getattr(_m, "severity", None)
                _msg  = getattr(_m, "message", str(_m))
                _pos  = getattr(_m, "position", None)
                _loc  = f" (línea {_pos.line})" if _pos else ""
                if hasattr(_sev, "name") and _sev.name == "ERROR":
                    st.error(f"**Error{_loc}:** {_msg}")
                elif hasattr(_sev, "name") and _sev.name == "WARNING":
                    st.warning(f"**Advertencia{_loc}:** {_msg}")
                else:
                    st.info(f"{_msg}")
        else:
            st.code(getattr(lean_res, "output", "sin output"), language="text")
        st.caption(
            "💡 Este error proviene del código Lean 4 generado por el LLM. "
            "Intenta reformular tu pregunta con más detalle, o usa el **Verificador** "
            "para pegar y editar el código Lean directamente."
        )

# ─── Descarga PDF ─────────────────────────────────────────────────────────────
try:
    import re as _re
    from nucleo.utils.pdf_export import generate_pdf
    from datetime import datetime as _dt
    _lean_match = _re.search(r'```lean\n(.*?)```', nr.content, _re.DOTALL)
    _lean_code  = _lean_match.group(1).strip() if _lean_match else ""
    _pdf_bytes  = generate_pdf(
        query=content_to_verify[:600],
        response=nr.content,
        lean_code=_lean_code,
        confidence=conf,
        area=getattr(nr, "metadata", {}).get("area", "") if hasattr(nr, "metadata") else "",
        status=getattr(nr, "metadata", {}).get("verification_status", "") if hasattr(nr, "metadata") else "",
        title=f"Verificación: {fname}",
    )
    _fn = f"verificacion_{fname.replace('.','_')}_{_dt.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    st.download_button(
        "⬇️ Descargar resultado como PDF",
        data=_pdf_bytes,
        file_name=_fn,
        mime="application/pdf",
        use_container_width=True,
    )
except Exception as _pdf_err:
    st.caption(f"PDF no disponible: {_pdf_err}")

# ─── Guardar para visualizaciones ────────────────────────────────────────────
try:
    short_prompt = content_to_verify[:300]
    vd = nucleo.get_viz_data(short_prompt)
    st.session_state["viz_data"]      = vd
    st.session_state["current_query"] = short_prompt
    qe = vd.get("query_embedding")
    if qe:
        hist = st.session_state.get("query_embeddings", [])
        hist.append({"text": f"[ARCHIVO] {fname}: {short_prompt[:60]}", "embedding": qe})
        if len(hist) > 20:
            hist = hist[-20:]
        st.session_state["query_embeddings"] = hist
except Exception:
    pass

st.divider()
col_v1, col_v2 = st.columns(2)
with col_v1:
    if st.button("📊 Ver grafo de skills activados →", use_container_width=True):
        st.switch_page("pages/1_Visualizaciones.py")
with col_v2:
    if st.button("💬 Continuar en el chat →", use_container_width=True):
        st.session_state["_pending_query"] = (
            f"Analiza y explica la verificación del archivo `{fname}` "
            f"que arrojó confianza {conf:.0%}"
        )
        home = st.session_state.get("_home_page")
        if home:
            st.switch_page(home)
        else:
            st.rerun()
