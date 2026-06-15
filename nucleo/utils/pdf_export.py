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
    text = re.sub(r'\*{1,3}([^*]+)\*{1,3}', r'\1', text)
    text = re.sub(r'_{1,2}([^_]+)_{1,2}', r'\1', text)
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
    pdf.multi_cell(0, 5.5, q_clean)
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
        pdf.multi_cell(0, 5.5, para)
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
        pdf.set_font("Courier", "", 9)

        lean_clean = lean_code.strip()
        # Reemplazar solo los chars no-latin para Courier (sin TTF custom)
        lean_clean = lean_clean.encode('latin-1', errors='replace').decode('latin-1')

        for line in lean_clean.splitlines():
            pdf.multi_cell(0, 5, line, fill=True, border=0)

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
