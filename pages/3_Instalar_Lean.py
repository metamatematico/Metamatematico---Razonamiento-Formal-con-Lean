"""
Página de instalación guiada de Lean 4 para usuarios de METAMATEMÁTICO.
Detecta el sistema operativo y proporciona instrucciones exactas.
"""

import streamlit as st
import subprocess
import sys
import os
import platform

st.set_page_config(
    page_title="Instalar Lean 4 — METAMATEMÁTICO",
    page_icon="⚙️",
    layout="wide",
)

# ── CSS coherente con la app principal ───────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap');
*, body { font-family: 'Space Grotesk', 'Inter', sans-serif; }

:root {
    --bg:      #0d0d14;
    --surface: #12121e;
    --border:  #2a2a48;
    --accent:  #7c6af5;
    --cyan:    #06d6c7;
    --pink:    #f72585;
    --text:    #e8e8ff;
    --muted:   #9898c0;
    --dim:     #5858a0;
}

.main .block-container { background: var(--bg); max-width: 860px; }
section[data-testid="stMain"] { background: var(--bg); }
section[data-testid="stSidebar"] { background: #0a0a12 !important; }

h1,h2,h3 { color: var(--text); }
p, li { color: var(--muted); font-size: 0.95rem; line-height: 1.7; }

.step-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 16px;
    padding: 1.4rem 1.8rem;
    margin: 1rem 0;
    position: relative;
}
.step-num {
    position: absolute;
    top: -14px; left: 20px;
    background: linear-gradient(135deg, var(--accent), var(--cyan));
    color: #fff;
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.08em;
    padding: 0.15rem 0.7rem;
    border-radius: 100px;
    text-transform: uppercase;
}
.step-card h3 { margin-top: 0.3rem; color: var(--text); font-size: 1.05rem; }
.step-card p  { margin-bottom: 0.4rem; }

.os-tab { margin-top: 0.5rem; }

.check-ok  { color: #06d6c7; font-weight: 700; }
.check-err { color: #f72585; font-weight: 700; }
.check-warn{ color: #b04fff; font-weight: 700; }

.tip-box {
    background: #1a1a3a;
    border: 1px solid #3a3a70;
    border-left: 3px solid var(--cyan);
    border-radius: 10px;
    padding: 0.8rem 1.1rem;
    margin: 0.8rem 0;
    font-size: 0.88rem;
    color: var(--muted);
}
</style>
""", unsafe_allow_html=True)


# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<h1 style="
    background: linear-gradient(120deg, #e8e8ff, #b04fff, #06d6c7);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; font-size: 2rem; margin-bottom: 0.2rem;">
    ⚙️ Instalar Lean 4
</h1>
<p style="color:#5858a0; font-size:0.85rem; margin-top:0;">
    Lean 4 es el verificador formal que hace que METAMATEMÁTICO pueda
    <strong style="color:#9898c0">garantizar matemáticamente</strong> sus respuestas.
    Sin Lean, el sistema responde con el LLM pero sin verificación formal.
</p>
""", unsafe_allow_html=True)

st.divider()

# ── Por qué necesitas Lean ────────────────────────────────────────────────────
with st.expander("¿Por qué necesito instalar Lean en mi computadora?", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
**Sin Lean local:**
- ❌ Las demostraciones no se verifican formalmente
- ❌ El sistema responde "formalización pendiente"
- ❌ No hay garantía matemática de corrección
- ✅ El chat y GNN+PPO siguen funcionando
        """)
    with col2:
        st.markdown("""
**Con Lean local:**
- ✅ Cada prueba se verifica formalmente
- ✅ El sistema confirma si una demostración es correcta
- ✅ Acceso completo a Mathlib (200,000+ teoremas)
- ✅ Tu PC amplía el poder del sistema
        """)

st.divider()

# ── Detectar OS del usuario ────────────────────────────────────────────────────
_os = platform.system()  # si corre local; remoto siempre es el servidor
st.markdown("### Elige tu sistema operativo")
os_choice = st.radio(
    "Sistema operativo",
    ["🪟 Windows", "🍎 macOS", "🐧 Linux"],
    horizontal=True,
    label_visibility="collapsed",
)

# ═══════════════════════════════════════════════════════════════════════════════
# PASO 1 — Instalar elan (gestor de versiones de Lean)
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="step-card">
  <div class="step-num">Paso 1</div>
  <h3>Instalar <code>elan</code> — el gestor de versiones de Lean</h3>
  <p><code>elan</code> instala y gestiona Lean 4 automáticamente (como <code>nvm</code> para Node).</p>
</div>
""", unsafe_allow_html=True)

if "Windows" in os_choice:
    st.markdown("""
**Opción A — PowerShell (recomendada):**
```powershell
# Abre PowerShell como Administrador y ejecuta:
winget install leanprover.elan
```

**Opción B — Instalador gráfico:**
1. Descarga [elan-x86_64-pc-windows-msvc.zip](https://github.com/leanprover/elan/releases/latest)
2. Extrae y ejecuta `elan-init.exe`
3. Acepta las opciones por defecto

**Opción C — WSL2 (Windows Subsystem for Linux):**
```bash
# Dentro de WSL2 (Ubuntu):
curl https://elan.lean-lang.org/elan-init.sh -sSf | sh -s -- -y
```
    """)
    st.markdown("""
<div class="tip-box">
💡 <strong>Recomendado para Windows:</strong> usar WSL2 con Ubuntu 22.04.
La verificación Lean es más rápida y estable en Linux/WSL2 que en Windows nativo.
<br>Instala WSL2: <code>wsl --install</code> en PowerShell como Administrador.
</div>
""", unsafe_allow_html=True)

elif "macOS" in os_choice:
    st.markdown("""
**Terminal (bash/zsh):**
```bash
curl https://elan.lean-lang.org/elan-init.sh -sSf | sh -s -- -y
source ~/.zshrc   # o source ~/.bashrc
```

**Verificar:**
```bash
lean --version
# Salida esperada: Lean (version 4.x.x, ...)
```
    """)

else:  # Linux
    st.markdown("""
**Ubuntu / Debian / Fedora:**
```bash
curl https://elan.lean-lang.org/elan-init.sh -sSf | sh -s -- -y
source ~/.bashrc
```

**Arch Linux:**
```bash
yay -S elan-lean   # o paru -S elan-lean
```

**Verificar:**
```bash
lean --version
lake --version
```
    """)

# ═══════════════════════════════════════════════════════════════════════════════
# PASO 2 — Clonar el repositorio
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="step-card">
  <div class="step-num">Paso 2</div>
  <h3>Clonar el repositorio de METAMATEMÁTICO</h3>
  <p>El repositorio contiene el proyecto Lean con la configuración de Mathlib.</p>
</div>
""", unsafe_allow_html=True)

if "Windows" in os_choice:
    st.markdown("""
```powershell
# En PowerShell o terminal de WSL2:
git clone https://github.com/metamatematico/Metamatematico---Razonamiento-Formal-con-Lean.git
cd Metamatematico---Razonamiento-Formal-con-Lean
```

Si no tienes Git: [git-scm.com/download/win](https://git-scm.com/download/win)
    """)
else:
    st.markdown("""
```bash
git clone https://github.com/metamatematico/Metamatematico---Razonamiento-Formal-con-Lean.git
cd Metamatematico---Razonamiento-Formal-con-Lean
```
    """)

# ═══════════════════════════════════════════════════════════════════════════════
# PASO 3 — Descargar Mathlib
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="step-card">
  <div class="step-num">Paso 3</div>
  <h3>Descargar Mathlib</h3>
  <p>
    Mathlib es la biblioteca matemática de Lean 4 con más de 200,000 teoremas verificados.
    Se descarga una vez y queda en caché.
  </p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
```bash
# Dentro del directorio del repositorio:
lake update              # configura las dependencias (~1 min)
lake exe cache get       # descarga Mathlib precompilado (~500 MB, ~5-10 min)
```
""")

st.markdown("""
<div class="tip-box">
⏱️ <strong>Tiempo estimado:</strong> 5–15 minutos dependiendo de tu conexión.
<br>Si <code>lake exe cache get</code> falla, Lean compilará Mathlib desde fuente
(puede tomar 30–60 min la primera vez, pero solo ocurre una vez).
</div>
""", unsafe_allow_html=True)

# ── Verificación ──────────────────────────────────────────────────────────────
st.markdown("""
```bash
# Probar que Mathlib funciona:
echo 'import Mathlib.Tactic
theorem test : 1 + 1 = 2 := by norm_num' > /tmp/test.lean
lake env lean /tmp/test.lean
# Si no hay error: ¡Mathlib está listo!
```
""")

# ═══════════════════════════════════════════════════════════════════════════════
# PASO 4 — Lanzar el agente local
# ═══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<div class="step-card">
  <div class="step-num">Paso 4</div>
  <h3>Lanzar el agente de verificación local</h3>
  <p>
    El agente conecta tu instalación de Lean con METAMATEMÁTICO.
    Mientras esté activo, la verificación formal ocurre en tu máquina.
  </p>
</div>
""", unsafe_allow_html=True)

st.markdown("""
```bash
# Verificar instalación:
python scripts/local_agent.py --check

# Conectar con esta instancia (reemplaza la URL):
python scripts/local_agent.py --server https://URL_DE_LA_APP

# Modo standalone (sin servidor web — verifica código manualmente):
python scripts/local_agent.py
```
""")

# ═══════════════════════════════════════════════════════════════════════════════
# PASO 5 — Verificación rápida (si la app corre localmente)
# ═══════════════════════════════════════════════════════════════════════════════
st.divider()
st.markdown("### Verificar instalación (en esta máquina)")

if st.button("▶ Comprobar si Lean está instalado aquí", type="primary"):
    results = {}

    with st.spinner("Buscando Lean..."):
        # lean
        for cmd in ["lean", os.path.expanduser("~/.elan/bin/lean")]:
            try:
                r = subprocess.run([cmd, "--version"],
                                   capture_output=True, text=True, timeout=8)
                if r.returncode == 0:
                    results["lean"] = ("ok", r.stdout.strip() or r.stderr.strip())
                    break
            except Exception:
                continue
        if "lean" not in results:
            results["lean"] = ("err", "No encontrado")

        # lake
        for cmd in ["lake", os.path.expanduser("~/.elan/bin/lake")]:
            try:
                r = subprocess.run([cmd, "--version"],
                                   capture_output=True, text=True, timeout=8)
                if r.returncode == 0:
                    results["lake"] = ("ok", r.stdout.strip() or r.stderr.strip())
                    break
            except Exception:
                continue
        if "lake" not in results:
            results["lake"] = ("err", "No encontrado")

        # Mathlib quick test
        if results.get("lean", ("err",))[0] == "ok":
            try:
                import tempfile
                code = "import Mathlib.Tactic\ntheorem t : 1+1=2 := by norm_num"
                with tempfile.NamedTemporaryFile(
                    suffix=".lean", mode="w", encoding="utf-8", delete=False
                ) as f:
                    f.write(code); tmp = f.name
                lean_bin = os.path.expanduser("~/.elan/bin/lean")
                lean_cmd = "lean" if results["lean"][0]=="ok" else lean_bin
                r = subprocess.run(
                    [os.path.expanduser("~/.elan/bin/lake"), "env", lean_cmd, tmp],
                    capture_output=True, text=True, timeout=45
                )
                os.unlink(tmp)
                if r.returncode == 0:
                    results["mathlib"] = ("ok", "1+1=2 verificado con norm_num ✓")
                else:
                    out = (r.stdout + r.stderr)[:200]
                    if "could not find" in out.lower() or "unknown package" in out.lower():
                        results["mathlib"] = ("warn", "Mathlib no descargado — ejecuta: lake exe cache get")
                    else:
                        results["mathlib"] = ("warn", out)
            except Exception as e:
                results["mathlib"] = ("warn", f"No se pudo probar Mathlib: {e}")
        else:
            results["mathlib"] = ("warn", "Requiere Lean instalado primero")

    # Mostrar resultados
    icons = {"ok": "✅", "err": "❌", "warn": "⚠️"}
    labels = {"lean": "Lean 4", "lake": "Lake (build tool)", "mathlib": "Mathlib"}
    all_ok = all(v[0] == "ok" for v in results.values())

    for key, (status, msg) in results.items():
        st.markdown(f"{icons[status]} **{labels[key]}**: `{msg}`")

    st.markdown("---")
    if all_ok:
        st.success("🎉 ¡Todo listo! Tu Lean 4 + Mathlib está funcionando correctamente.")
        st.markdown("""
Ahora puedes lanzar el agente local para conectar tu cómputo:
```bash
python scripts/local_agent.py --check
```
        """)
    else:
        missing = [labels[k] for k, (s, _) in results.items() if s != "ok"]
        st.warning(f"Sigue los pasos anteriores para instalar: **{', '.join(missing)}**")

# ── Links útiles ──────────────────────────────────────────────────────────────
st.divider()
st.markdown("### Referencias")
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
**Documentación oficial**
- [lean-lang.org](https://lean-lang.org)
- [Theorem Proving in Lean 4](https://lean-lang.org/theorem_proving_in_lean4/)
- [Mathlib docs](https://leanprover-community.github.io/mathlib4_docs/)
    """)
with col2:
    st.markdown("""
**Comunidad**
- [Lean Zulip Chat](https://leanprover.zulipchat.com)
- [Mathlib4 GitHub](https://github.com/leanprover-community/mathlib4)
- [leanprover-community.github.io](https://leanprover-community.github.io)
    """)
with col3:
    st.markdown("""
**Recursos adicionales**
- [Natural Number Game](https://adam.math.hhu.de/)
- [Lean 4 en VSCode](https://marketplace.visualstudio.com/items?itemName=leanprover.lean4)
- [Mathematics in Lean](https://leanprover-community.github.io/mathematics_in_lean/)
    """)
