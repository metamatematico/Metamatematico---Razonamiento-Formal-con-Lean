"""
Consultores Avanzados
=====================
Módulo para matemáticos expertos. Genera artefactos verificables:
archivos .lean, scripts Python, trazas de auditoría, con verificación
automática en Lean 4.
"""
from __future__ import annotations

import asyncio
import io
import json
import sys
import zipfile
from pathlib import Path

import streamlit as st

# ─── Estilo ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.block-container { padding-top: 1.5rem; }
h1, h2, h3 { color: #c9d1d9; }
.card {
    background: #131c2e; border: 1px solid #30363d;
    border-radius: 10px; padding: 1rem 1.2rem; margin-bottom: 0.8rem;
}
.badge-ok   { color: #3fb950; font-weight: bold; }
.badge-warn { color: #d29922; font-weight: bold; }
.badge-err  { color: #f85149; font-weight: bold; }
.badge-pend { color: #8b949e; }
</style>
""", unsafe_allow_html=True)

# ─── Botón volver ─────────────────────────────────────────────────────────────
_c1, _ = st.columns([1, 5])
with _c1:
    if st.button("← Volver al chat", use_container_width=True):
        st.switch_page("app.py")

st.title("🔭 Consultores Avanzados")
st.markdown(
    "Genera **N artefactos matemáticos verificables**: archivos `.lean` autocontenidos, "
    "skeletons de demostración, scripts Python para verificación numérica, y trazas de "
    "auditoría completas. Cada candidato se verifica automáticamente en **Lean 4**."
)

# ─── Nucleo — compartido con app.py ───────────────────────────────────────────

def _get_nucleo():
    # app.py runs as __main__ under st.navigation — look there first to
    # avoid re-executing app.py (which would cause DuplicateElementId).
    for mod_name in ("__main__", "app"):
        mod = sys.modules.get(mod_name)
        if mod is not None and hasattr(mod, "_get_nucleo"):
            return mod._get_nucleo()
    # Fallback: fresh import (only on direct page reload edge cases)
    import importlib
    root = str(Path(__file__).parent.parent)
    if root not in sys.path:
        sys.path.insert(0, root)
    return importlib.import_module("app")._get_nucleo()


nucleo = _get_nucleo()

# ─── Panel de configuración ───────────────────────────────────────────────────

with st.sidebar:
    st.header("⚙️ Configuración")
    n_candidates = st.slider("Número de candidatos", min_value=1, max_value=6, value=3)
    activate = st.toggle("Activar módulo", value=nucleo.consultores_active)

    if activate and not nucleo.consultores_active:
        try:
            nucleo.set_consultores_mode(n_candidates=n_candidates)
            st.success(f"Módulo activo ({n_candidates} candidatos)")
        except RuntimeError as e:
            st.error(str(e))
    elif not activate and nucleo.consultores_active:
        nucleo.disable_consultores_mode()
        st.info("Módulo desactivado")

    if nucleo.consultores_active:
        if st.button("Actualizar n_candidatos"):
            nucleo.set_consultores_mode(n_candidates=n_candidates)
            st.success(f"Actualizado a {n_candidates} candidatos")

    st.divider()
    st.caption(
        "El módulo usa el mismo LLM y Lean 4 configurados en el chat principal. "
        "No requiere clave de API adicional."
    )

# ─── Estado del módulo ────────────────────────────────────────────────────────

if not nucleo.consultores_active:
    st.info(
        "El módulo Consultores Avanzados está **desactivado**. "
        "Actívalo en el panel lateral para continuar."
    )
    st.stop()

# ─── Formulario de consulta ───────────────────────────────────────────────────

st.subheader("Consulta matemática")

query = st.text_area(
    "Enunciado del problema o teorema",
    height=180,
    placeholder=(
        "Ejemplo: Demuestra que para todo entero n ≥ 2, el producto de los primeros n "
        "primos más 1 no es necesariamente primo. Genera candidatos Lean 4 con Mathlib."
    ),
    key="consultores_query",
)

run_btn = st.button("🚀 Generar artefactos", type="primary", disabled=not query.strip())

# ─── Ejecución ────────────────────────────────────────────────────────────────

def _run_async(coro):
    """Run async coroutine in sync Streamlit context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result(timeout=300)
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


if run_btn and query.strip():
    with st.spinner("Generando y verificando artefactos (puede tardar 30-90 s)…"):
        try:
            result = _run_async(nucleo._consultores.process(query.strip()))
            st.session_state["consultores_result"] = result
        except Exception as e:
            st.error(f"Error al procesar: {e}")
            st.stop()

# ─── Resultados ───────────────────────────────────────────────────────────────

result = st.session_state.get("consultores_result")
if result is None:
    st.stop()

if result.error:
    st.error(f"El módulo reportó un error: {result.error}")
    with st.expander("Respuesta LLM cruda"):
        st.code(result.raw_llm_response, language="text")
    st.stop()

# Encabezado de resultados
col_type, col_verified, col_total = st.columns(3)
col_type.metric("Tipo de petición", result.request_type.value.capitalize())
n_verified = sum(
    1 for rc in result.ranked_candidates if rc.candidate.lean_verified is True
)
col_verified.metric("Candidatos verificados en Lean", f"{n_verified}/{len(result.ranked_candidates)}")
best_score = result.best.metrics.total_score if result.best else 0.0
col_total.metric("Puntuación del mejor", f"{best_score:.2f}")

# Resumen ejecutivo
if result.executive_summary:
    st.subheader("Resumen ejecutivo")
    st.markdown(result.executive_summary)

# Spec formal
if result.spec and result.spec.enunciado_formal:
    with st.expander("📋 Especificación formal"):
        st.markdown(f"**Enunciado formal:**\n```\n{result.spec.enunciado_formal}\n```")
        if result.spec.mathlib_anchors:
            st.markdown("**Anclajes Mathlib:**")
            for a in result.spec.mathlib_anchors:
                st.markdown(f"- `{a}`")
        if result.spec.supuestos:
            st.markdown("**Supuestos:** " + "; ".join(result.spec.supuestos))

st.divider()
st.subheader("Candidatos")

# ─── Tabs por candidato ───────────────────────────────────────────────────────

tabs = st.tabs([
    f"#{rc.rank} {rc.candidate.verification_badge}" for rc in result.ranked_candidates
])

for tab, rc in zip(tabs, result.ranked_candidates):
    cand = rc.candidate
    m = rc.metrics

    with tab:
        # Métricas del candidato
        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("Puntuación total", f"{m.total_score:.2f}")
        mc2.metric("Completitud", f"{m.completeness:.0%}")
        mc3.metric("Lean score", f"{m.lean_score:.2f}")
        badge_color = (
            "badge-ok" if cand.lean_verified and cand.sorry_count == 0
            else "badge-warn" if cand.lean_verified
            else "badge-err" if cand.lean_verified is False
            else "badge-pend"
        )
        mc4.markdown(
            f'<span class="{badge_color}">{cand.verification_badge}</span>',
            unsafe_allow_html=True,
        )

        if cand.lean_errors:
            with st.expander("⚠️ Errores Lean"):
                for err in cand.lean_errors:
                    st.code(err, language="text")

        # Archivo .lean
        if cand.lean_file:
            st.markdown("**Archivo `.lean`**")
            st.code(cand.lean_file, language="lean")

        # Skeleton
        if cand.proof_skeleton:
            with st.expander("🧩 Skeleton / estrategia de demostración"):
                st.markdown(cand.proof_skeleton)

        # Solver script
        if cand.solver_script:
            with st.expander("🐍 Script Python (solver numérico / OR-Tools)"):
                st.code(cand.solver_script, language="python")

        # Bridge
        if cand.verification_bridge:
            with st.expander("🌉 Bridge de verificación (solution.json → Lean)"):
                st.code(cand.verification_bridge, language="python")

        # Plan de verificación
        if cand.verification_plan:
            with st.expander("📝 Plan de verificación"):
                for step in cand.verification_plan:
                    st.markdown(f"- {step}")

        # Comandos
        if cand.lean_commands:
            with st.expander("💻 Comandos exactos"):
                st.code("\n".join(cand.lean_commands), language="bash")

        # Descarga de artefactos
        st.divider()
        _download_files: dict[str, bytes] = {}
        if cand.lean_file:
            _download_files[f"candidato_{rc.rank}.lean"] = cand.lean_file.encode()
        if cand.solver_script:
            _download_files[f"solver_{rc.rank}.py"] = cand.solver_script.encode()
        if cand.verification_bridge:
            _download_files[f"bridge_{rc.rank}.py"] = cand.verification_bridge.encode()

        if _download_files:
            buf = io.BytesIO()
            with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
                for fname, data in _download_files.items():
                    zf.writestr(fname, data)
            buf.seek(0)
            st.download_button(
                label=f"⬇️ Descargar artefactos (candidato #{rc.rank})",
                data=buf,
                file_name=f"consultores_candidato_{rc.rank}.zip",
                mime="application/zip",
            )

# ─── Audit trace ──────────────────────────────────────────────────────────────

if result.audit:
    with st.expander("🔍 Traza de auditoría"):
        st.json(result.audit.to_dict())

# ─── Descarga global ──────────────────────────────────────────────────────────

st.divider()
st.subheader("Descarga completa")

full_report = {
    "query": result.query,
    "request_type": result.request_type.value,
    "executive_summary": result.executive_summary,
    "spec": {
        "enunciado_formal": result.spec.enunciado_formal if result.spec else "",
        "mathlib_anchors": result.spec.mathlib_anchors if result.spec else [],
    },
    "candidates": [
        {
            "rank": rc.rank,
            "verification_badge": rc.candidate.verification_badge,
            "lean_verified": rc.candidate.lean_verified,
            "sorry_count": rc.candidate.sorry_count,
            "total_score": round(rc.metrics.total_score, 4),
            "lean_file": rc.candidate.lean_file,
            "solver_script": rc.candidate.solver_script,
            "verification_bridge": rc.candidate.verification_bridge,
            "lean_commands": rc.candidate.lean_commands,
        }
        for rc in result.ranked_candidates
    ],
    "audit": result.audit.to_dict() if result.audit else {},
}

st.download_button(
    label="⬇️ Descargar reporte completo (JSON)",
    data=json.dumps(full_report, ensure_ascii=False, indent=2).encode("utf-8"),
    file_name="consultores_reporte.json",
    mime="application/json",
)

# Mega-zip con todo
mega_buf = io.BytesIO()
with zipfile.ZipFile(mega_buf, "w", zipfile.ZIP_DEFLATED) as zf:
    zf.writestr("reporte.json", json.dumps(full_report, ensure_ascii=False, indent=2))
    for rc in result.ranked_candidates:
        if rc.candidate.lean_file:
            zf.writestr(f"lean/candidato_{rc.rank}.lean", rc.candidate.lean_file)
        if rc.candidate.solver_script:
            zf.writestr(f"scripts/solver_{rc.rank}.py", rc.candidate.solver_script)
        if rc.candidate.verification_bridge:
            zf.writestr(f"scripts/bridge_{rc.rank}.py", rc.candidate.verification_bridge)
mega_buf.seek(0)
st.download_button(
    label="⬇️ Descargar todo en ZIP",
    data=mega_buf,
    file_name="consultores_artefactos.zip",
    mime="application/zip",
)
