"""
Verificador de Demostraciones y Conjeturas
==========================================
Carga un archivo .txt, .tex o .pdf con una demostración o conjetura matemática.
El NLE la analiza, intenta formalizarla en Lean 4 y reporta si es correcta.
"""
from __future__ import annotations

import io
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
</style>
""", unsafe_allow_html=True)

# ─── Botón volver ─────────────────────────────────────────────────────────────
_c1, _ = st.columns([1, 5])
with _c1:
    if st.button("← Volver al chat", width="stretch"):
        st.switch_page("app.py")

st.title("🔬 Verificador de Demostraciones")
st.markdown(
    "Carga un archivo **`.txt`**, **`.tex`** (LaTeX) o **`.pdf`** con una demostración "
    "o conjetura matemática. El Núcleo Lógico Evolutivo la leerá, intentará formalizarla "
    "en **Lean 4** y reportará si es matemáticamente correcta."
)
st.divider()


# ─── Extracción de texto ──────────────────────────────────────────────────────

def _extract_pdf(data: bytes) -> str:
    """Extrae texto de un PDF usando PyMuPDF (fitz)."""
    try:
        import fitz  # PyMuPDF — ya instalado
        doc = fitz.open(stream=data, filetype="pdf")
        pages_text = []
        for page in doc:
            pages_text.append(page.get_text("text"))
        doc.close()
        return "\n\n".join(pages_text)
    except Exception as e:
        return f"[Error al leer el PDF: {e}]"


# Entornos LaTeX que contienen matemáticas relevantes
_LATEX_ENVS = re.compile(
    r'\\begin\{(theorem|Theorem|lemma|Lemma|proposition|Proposition|'
    r'corollary|Corollary|definition|Definition|proof|Proof|'
    r'claim|Claim|conjecture|Conjecture|remark|Remark|example|Example)\*?\}'
    r'(.*?)'
    r'\\end\{\1\*?\}',
    re.DOTALL,
)

_LATEX_TITLE = re.compile(
    r'\\(title|section|subsection)\{([^}]+)\}'
)


def _extract_latex_blocks(tex: str) -> list[dict]:
    """Extrae bloques theorem/lemma/proof de fuente LaTeX."""
    blocks = []
    for m in _LATEX_ENVS.finditer(tex):
        env = m.group(1).lower()
        content = m.group(2).strip()
        if len(content) > 10:
            blocks.append({"type": env, "content": content})
    return blocks


def _strip_latex(tex: str) -> str:
    """Limpia comandos LaTeX decorativos, conserva notación matemática."""
    tex = re.sub(r'\\(text|mathrm|mathit|mathbf|mathbb|emph)\{([^}]+)\}', r'\2', tex)
    tex = re.sub(r'\\(label|ref|cite|footnote|index)\{[^}]*\}', '', tex)
    tex = re.sub(r'%.*', '', tex)
    tex = re.sub(r'\s+', ' ', tex)
    return tex.strip()


def _is_latex_content(text: str) -> bool:
    """Detecta si el texto contiene marcadores LaTeX."""
    markers = [r'\begin{', r'\end{', r'\frac', r'\forall', r'\exists',
               r'\mathbb', r'\mathcal', r'\sum', r'\prod', r'\int']
    return any(m in text for m in markers)


# ─── Nucleo — compartido con app.py via cache_resource ────────────────────────

def _get_nucleo():
    """Reutiliza la instancia de Nucleo ya inicializada por app.py."""
    # Importar la función cacheada del módulo principal
    # @st.cache_resource garantiza que es el mismo objeto en toda la sesión
    import importlib, sys
    root = str(Path(__file__).parent.parent)
    if root not in sys.path:
        sys.path.insert(0, root)
    app_mod = importlib.import_module("app")
    return app_mod._get_nucleo()


# ─── Construcción del prompt de verificación ──────────────────────────────────

def _build_verify_prompt(content: str, filename: str, mode: str,
                         content_type: str) -> str:
    """Construye el prompt que el NLE envía a Lean + LLM."""
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

raw_bytes  = uploaded.read()
fname      = uploaded.name
ext        = Path(fname).suffix.lower()

with st.spinner("Leyendo archivo…"):
    if ext == ".pdf":
        text_original = _extract_pdf(raw_bytes)
        is_latex = False
        latex_blocks: list[dict] = []
    elif ext in (".tex", ".latex"):
        text_original = raw_bytes.decode("utf-8", errors="replace")
        latex_blocks  = _extract_latex_blocks(text_original)
        is_latex      = True
    else:  # .txt
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

# Mostrar preview del contenido seleccionado
with st.expander("Ver lo que se enviará al NLE", expanded=False):
    st.code(content_to_verify[:1500], language="latex" if _is_latex_content(content_to_verify) else "text")
    if len(content_to_verify) > 1500:
        st.caption(f"… y {len(content_to_verify)-1500} caracteres más.")
    st.caption(f"Total: {len(content_to_verify):,} caracteres · Tipo: {content_type}")

# ─── Verificación ─────────────────────────────────────────────────────────────

st.divider()

col_btn, col_hint = st.columns([2, 3])
with col_btn:
    run = st.button("🔬 Verificar con Lean 4", type="primary", use_container_width=True)
with col_hint:
    st.markdown(
        "<div style='padding:.6rem;color:#6e7681;font-size:.85rem'>"
        "El NLE intentará formalizar el contenido en Lean 4 y verificarlo formalmente. "
        "Puede tardar 10–30 segundos dependiendo de la complejidad.</div>",
        unsafe_allow_html=True
    )

if not run:
    st.stop()

# ─── Ejecutar verificación ────────────────────────────────────────────────────

prompt = _build_verify_prompt(content_to_verify, fname, mode, content_type)

nucleo = _get_nucleo()
if nucleo is None:
    st.error("El Núcleo no está disponible. Configura un proveedor LLM en la página principal.")
    st.stop()

t0 = time.time()
with st.spinner("El NLE está analizando… (Paso 1/3: clasificando) "):
    pass

try:
    nr = nucleo.process_sync(prompt)
    elapsed = time.time() - t0
except Exception as e:
    st.error(f"Error durante la verificación: {e}")
    st.stop()

# ─── Mostrar resultado ────────────────────────────────────────────────────────

conf      = getattr(nr, "confidence", 0.5)
lean_res  = getattr(nr, "lean_result", None)

# Badge principal
if conf >= 0.9:
    st.success(f"✅ **Verificado formalmente por Lean 4** — confianza: {conf:.0%}")
elif conf >= 0.7:
    st.warning(f"⚠️ **Verificación parcial** — confianza: {conf:.0%}")
elif conf >= 0.5:
    st.warning(f"⚠️ **Formalizado con huecos (sorry)** — confianza: {conf:.0%}")
else:
    st.error(f"❌ **No verificado** — confianza: {conf:.0%}")

# Métricas
mc1, mc2, mc3 = st.columns(3)
mc1.metric("Confianza NLE", f"{conf:.0%}")
mc2.metric("Tiempo", f"{elapsed:.1f} s")
if lean_res:
    status_label = {
        "SUCCESS": "✅ Lean OK",
        "SORRY": "⚠️ Sorry parcial",
        "ERROR": "❌ Error Lean",
        "TIMEOUT": "⏱ Timeout",
    }.get(lean_res.status.name if hasattr(lean_res.status, "name") else str(lean_res.status), "—")
    mc3.metric("Lean 4", status_label)
else:
    mc3.metric("Lean 4", "—")

st.divider()

# Respuesta completa del NLE
st.markdown("### 📊 Análisis del NLE")
st.markdown(nr.content)

# ─── Guardar para visualizaciones ────────────────────────────────────────────
try:
    short_prompt = content_to_verify[:300]
    vd = nucleo.get_viz_data(short_prompt)
    st.session_state["viz_data"]       = vd
    st.session_state["current_query"]  = short_prompt
    # Acumular en historial de embeddings
    qe = vd.get("query_embedding")
    if qe:
        hist = st.session_state.get("query_embeddings", [])
        hist.append({"text": f"[ARCHIVO] {fname}: {short_prompt[:60]}", "embedding": qe})
        if len(hist) > 20:
            hist = hist[-20:]
        st.session_state["query_embeddings"] = hist
except Exception:
    pass

# Botón para ir a visualizaciones
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
        st.switch_page("app.py")
