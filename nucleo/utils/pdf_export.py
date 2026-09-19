"""
Exportación de resultados del NLE a PDF.
Usa fpdf (v2) con Arial para soporte Unicode básico.
"""
from __future__ import annotations

import re
import os
from datetime import datetime
from typing import Optional


def _strip_markdown(text: str) -> str:
    """Convierte Markdown a texto plano para el PDF."""
    # Headers → texto con separador
    text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
    # Bold/italic
    text = re.sub(r'\*{1,3}([^*\n]+)\*{1,3}', r'\1', text)

    # EL GUION BAJO SOLO ES CURSIVA EN FRONTERA DE PALABRA.
    #
    # Esto era `_{1,2}([^_]+)_{1,2}` y trataba CUALQUIER par de guiones bajos
    # como cursiva de Markdown. Consecuencias, las dos vistas en un PDF real
    # del teorema fundamental del calculo:
    #
    #   intervalIntegral.integral_eq_sub_of_hasDerivAt
    #     -> intervalIntegral.integraleqsubofhasDerivAt
    #
    #   \int_a^b f(x)\,dx = F(b) - F(a)
    #     -> \inta^b f(x)\,dx = F(b) - F(a)
    #
    # El nombre del lema salia INSERVIBLE: el alumno no puede copiarlo, y
    # ademas parece otro nombre —uno que no existe—, que es justo lo que este
    # sistema existe para no producir. Y todos los subindices de LaTeX se
    # perdian, asi que las formulas del PDF decian algo distinto de la
    # matematica.
    #
    # La regla de Markdown de verdad (CommonMark) es que `_` abre enfasis solo
    # si no esta pegado a un caracter de palabra: `snake_case` NUNCA es
    # cursiva. Se exige eso en los dos extremos, y se prohibe cruzar lineas
    # para que dos guiones lejanos no se emparejen.
    text = re.sub(r'(?<![\w\\])_{1,2}([^_\n]+)_{1,2}(?!\w)', r'\1', text)
    # Inline code
    text = re.sub(r'`([^`]+)`', r'\1', text)
    # Links [text](url) → text
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    # Tables: replace | with spaces
    text = re.sub(r'\|', '  ', text)
    text = re.sub(r'^[-|: ]+$', '', text, flags=re.MULTILINE)
    # Horizontal rules
    text = re.sub(r'^---+$', '─' * 40, text, flags=re.MULTILINE)
    # Remove leading/trailing blank lines
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def _safe_text(text: str) -> str:
    """Limpia caracteres que fpdf no puede renderizar con Arial."""
    # Reemplazos de símbolos matemáticos comunes → ASCII
    replacements = {
        '∀': 'forall ', '∃': 'exists ', '∈': 'in', '∉': 'not in',
        '⊆': '⊆', '⊂': 'subset', '∪': 'union', '∩': 'intersect',
        '→': '->', '←': '<-', '↔': '<->', '⟹': '=>', '⟺': '<=>',
        '∧': '/\\', '∨': '\\/', '¬': 'not ', '⊢': '|-',
        '≤': '<=', '≥': '>=', '≠': '!=', '≈': '~=', '≡': '===',
        'ℝ': 'R', 'ℕ': 'N', 'ℤ': 'Z', 'ℚ': 'Q', 'ℂ': 'C',
        '∞': 'inf', '√': 'sqrt', '∑': 'sum', '∏': 'prod', '∫': 'int',
        '·': '*', '×': 'x', '÷': '/', '±': '+/-',
        '⟩': '>', '⟨': '<', '⌈': 'ceil(', '⌉': ')',
        '’': "'", '‘': "'", '“': '"', '”': '"',
        '—': '--', '–': '-', '…': '...',
        '─': '-', '│': '|', '┌': '+', '┐': '+', '└': '+', '┘': '+',
        '├': '+', '┤': '+', '┬': '+', '┴': '+', '┼': '+',
        '↑': '^', '↓': 'v', '⊕': 'oplus', '⊗': 'otimes',
        'α': 'alpha', 'β': 'beta', 'γ': 'gamma', 'δ': 'delta',
        'ε': 'epsilon', 'λ': 'lambda', 'μ': 'mu', 'π': 'pi',
        'σ': 'sigma', 'τ': 'tau', 'φ': 'phi', 'ψ': 'psi', 'ω': 'omega',
        'Γ': 'Gamma', 'Δ': 'Delta', 'Λ': 'Lambda', 'Σ': 'Sigma',
        'Π': 'Pi', 'Φ': 'Phi', 'Ψ': 'Psi', 'Ω': 'Omega',
    }
    for sym, rep in replacements.items():
        text = text.replace(sym, rep)
    # Quitar cualquier carácter no-latin que quede
    return text.encode('latin-1', errors='replace').decode('latin-1')


def _find_arial() -> Optional[str]:
    """Localiza arial.ttf en rutas comunes de Windows/Linux/Mac."""
    candidates = [
        'C:/Windows/Fonts/arial.ttf',
        '/usr/share/fonts/truetype/msttcorefonts/Arial.ttf',
        '/Library/Fonts/Arial.ttf',
        os.path.join(os.path.dirname(__file__), 'Arial.ttf'),
    ]
    return next((p for p in candidates if os.path.exists(p)), None)


def _find_mono() -> Optional[str]:
    """Una monoespaciada CON Unicode para el bloque de codigo Lean.

    POR QUE HACE FALTA. El bloque de codigo se pintaba con `Courier`, que es
    una fuente nucleo de PDF y solo cubre latin-1, y encima se codificaba con
    `encode('latin-1', errors='replace')` SIN pasar por la tabla de simbolos.
    Resultado, visto en un PDF real:

        theorem ftc_evaluation (f F : ? ? ?) (a b : ?)
          ? x in a..b, f x = F b - F a := by

    O sea que la pieza FORMAL —el codigo que Lean compilo y verifico, que es
    lo unico con respaldo en todo el documento— era la peor renderizada del
    PDF, mientras la prosa de al lado leia `R -> R` perfectamente.

    Transliterar a ASCII como hace `_safe_text` tampoco sirve aqui: `int x in
    a..b` se lee, pero NO COMPILA si el alumno lo pega. Un codigo que parece
    Lean y no lo es, en un documento cuya tesis es «esto lo verifico Lean».

    Con una TTF Unicode el codigo sale tal cual, que es lo correcto.
    """
    # DEJAVU PRIMERO: es la unica de la lista con cobertura completa de los
    # simbolos que Lean usa a diario. Consolas —la monoespaciada por defecto de
    # Windows— NO trae `ℝ`, `∀` ni `∈`, y eso son cuadros vacios en el PDF,
    # que es peor que el `?` porque ni siquiera avisa de que falta algo.
    candidatos = [
        'C:/Windows/Fonts/DejaVuSansMono.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',
        '/Library/Fonts/DejaVuSansMono.ttf',
        'C:/Windows/Fonts/consola.ttf',        # Consolas: mono, cobertura parcial
        'C:/Windows/Fonts/lucon.ttf',          # Lucida Console
    ]
    return next((p for p in candidatos if os.path.exists(p)), None)


def _glifos_de(ruta: str) -> Optional[set]:
    """Los puntos de codigo que esta fuente sabe dibujar, o None si no se sabe."""
    try:
        from fontTools.ttLib import TTFont
        t = TTFont(ruta, fontNumber=0, lazy=True)
        cubre = set()
        for tabla in t['cmap'].tables:
            cubre |= set(tabla.cmap)
        t.close()
        return cubre
    except Exception:                                           # noqa: BLE001
        return None


def _solo_lo_que_falte(texto: str, cubre: Optional[set]) -> str:
    """Translitera UNICAMENTE los simbolos que la fuente no tiene.

    NUNCA SE DEJA UN CUADRO VACIO, y nunca se estropea lo que si se puede
    pintar. La alternativa que habia era todo o nada: o `encode('latin-1')`
    —que convertia el codigo Lean entero en interrogantes— o transliterar
    entero, que produce algo que parece Lean y no compila.

    Aqui el codigo sale literal salvo los caracteres que esa fuente concreta
    no sabe dibujar, y esos se sustituyen por su equivalente ASCII en vez de
    desaparecer. Si no se puede leer la fuente, se es conservador y se
    translitera todo.
    """
    if cubre is None:
        return _safe_text(texto)
    fuera = {c for c in set(texto) if ord(c) not in cubre}
    if not fuera:
        return texto
    for c in fuera:
        texto = texto.replace(c, _safe_text(c))
    return texto


def generate_pdf(
    query: str,
    response: str,
    lean_code: Optional[str] = None,
    confidence: float = 0.0,
    area: str = "",
    status: str = "",
    title: str = "METAMATEMÁTICO — Resultado",
    timestamp: Optional[datetime] = None,
) -> bytes:
    """
    Genera un PDF con el resultado de una consulta al NLE.

    Returns:
        bytes del PDF generado.
    """
    import fpdf

    ts = timestamp or datetime.now()
    ts_str = ts.strftime("%d/%m/%Y %H:%M")

    pdf = fpdf.FPDF(format="A4")
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()

    # ── Fuente ────────────────────────────────────────────────────────────────
    arial_path = _find_arial()
    if arial_path:
        pdf.add_font("Main", "", arial_path)
        pdf.add_font("Main", "B", arial_path)
        font_name = "Main"
    else:
        font_name = "Helvetica"  # fallback sin Unicode completo

    mono_path = _find_mono()
    mono_cubre = None
    if mono_path:
        try:
            pdf.add_font("Mono", "", mono_path)
            mono_name = "Mono"
            mono_cubre = _glifos_de(mono_path)
        except Exception:                                       # noqa: BLE001
            mono_name = "Courier"
    else:
        mono_name = "Courier"

    # ── Encabezado ────────────────────────────────────────────────────────────
    pdf.set_font(font_name, "B", 15)
    pdf.set_text_color(80, 0, 160)
    pdf.cell(0, 9, "METAMATEMÁTICO", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font(font_name, "", 9)
    pdf.set_text_color(100, 100, 160)
    pdf.cell(0, 5,
             "Nucleo Logico Evolutivo v7.0  |  BIOMAT · Centro de Biomatematicas  |  "
             f"Generado: {ts_str}",
             new_x="LMARGIN", new_y="NEXT")

    pdf.set_draw_color(140, 0, 255)
    pdf.set_line_width(0.5)
    pdf.line(pdf.l_margin, pdf.get_y() + 2, pdf.w - pdf.r_margin, pdf.get_y() + 2)
    pdf.ln(6)

    # ── Metadatos ─────────────────────────────────────────────────────────────
    meta_parts = []
    if area:
        meta_parts.append(f"Area: {_safe_text(area)}")
    if confidence:
        meta_parts.append(f"Confianza NLE: {confidence:.0%}")
    if status:
        _status_map = {
            "verificado": "Lean 4: verificado formalmente",
            "parcial":    "Lean 4: parcialmente verificado (sorry)",
            "no_verificado": "Lean 4: no verificado",
            "timeout":    "Lean 4: timeout (reintentar)",
            "sin_entorno": "Lean 4: entorno no disponible",
        }
        meta_parts.append(_status_map.get(status, f"Estado: {status}"))

    if meta_parts:
        pdf.set_font(font_name, "", 9)
        pdf.set_text_color(80, 80, 80)
        pdf.cell(0, 5, "  |  ".join(meta_parts), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(3)

    # ── Consulta ──────────────────────────────────────────────────────────────
    pdf.set_font(font_name, "B", 11)
    pdf.set_text_color(40, 40, 80)
    pdf.cell(0, 7, "Consulta", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font(font_name, "", 10)
    pdf.set_text_color(30, 30, 30)
    q_clean = _safe_text(query[:800])
    # new_x="LMARGIN": por defecto multi_cell deja el cursor en el borde
    # derecho de la celda; con w=0 eso es el margen derecho, y la siguiente
    # llamada calcularia un ancho ~0 ("Not enough horizontal space").
    pdf.multi_cell(0, 5.5, q_clean, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)

    # ── Respuesta ─────────────────────────────────────────────────────────────
    pdf.set_font(font_name, "B", 11)
    pdf.set_text_color(40, 40, 80)
    pdf.cell(0, 7, "Respuesta del NLE", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font(font_name, "", 10)
    pdf.set_text_color(20, 20, 20)

    resp_plain = _safe_text(_strip_markdown(response))
    for para in resp_plain.split("\n\n"):
        para = para.strip()
        if not para:
            continue
        pdf.multi_cell(0, 5.5, para, new_x="LMARGIN", new_y="NEXT")
        pdf.ln(2)

    # ── Código Lean ───────────────────────────────────────────────────────────
    if lean_code and lean_code.strip():
        pdf.ln(3)
        pdf.set_font(font_name, "B", 11)
        pdf.set_text_color(40, 40, 80)
        pdf.cell(0, 7, "Codigo Lean 4", new_x="LMARGIN", new_y="NEXT")

        pdf.set_fill_color(245, 245, 250)
        pdf.set_draw_color(180, 180, 220)
        pdf.set_text_color(20, 20, 60)
        pdf.set_font(mono_name, "", 9)

        lean_clean = lean_code.strip()
        if mono_name != "Courier":
            lean_clean = _solo_lo_que_falte(lean_clean, mono_cubre)
        else:
            # SIN FUENTE UNICODE NO HAY CODIGO EXACTO, y hay que elegir el mal
            # menor. `?` es ilegible Y no compila; la transliteracion al menos
            # se lee. Se marca que NO es el codigo literal para que nadie lo
            # pegue creyendo que si.
            lean_clean = _safe_text(lean_clean)

        for line in lean_clean.splitlines():
            # Sin new_x="LMARGIN" el cursor se queda en el margen derecho y la
            # segunda linea de codigo aborta la exportacion entera.
            pdf.multi_cell(0, 5, line or " ", fill=True, border=0,
                           new_x="LMARGIN", new_y="NEXT")

    # ── Pie ───────────────────────────────────────────────────────────────────
    pdf.ln(8)
    pdf.set_draw_color(200, 200, 220)
    pdf.set_line_width(0.3)
    pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
    pdf.ln(3)
    pdf.set_font(font_name, "", 8)
    pdf.set_text_color(140, 140, 160)
    pdf.cell(
        0, 5,
        "Generado por METAMATEMÁTICO (NLE v7.0)  |  "
        "Leonardo Jimenez Martinez  |  BIOMAT",
        new_x="LMARGIN", new_y="NEXT", align="C",
    )

    return bytes(pdf.output())
