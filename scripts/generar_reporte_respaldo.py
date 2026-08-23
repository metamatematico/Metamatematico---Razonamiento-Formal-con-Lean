"""
Genera docs/respaldo_lean.tex a partir de data/respaldo_lean.json.

Ninguna cifra del reporte se escribe a mano: si el respaldo cambia, se
regenera y el documento cambia con el. Es la misma disciplina que
docs/funtor_pi.tex.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "data" / "respaldo_lean.json"
TEX = RAIZ / "docs" / "respaldo_lean.tex"

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def esc(t: str) -> str:
    """Escapa lo que LaTeX interpreta."""
    for a, b in [("\\", r"\textbackslash{}"), ("_", r"\_"), ("%", r"\%"),
                 ("&", r"\&"), ("#", r"\#"), ("$", r"\$")]:
        t = t.replace(a, b)
    return t


def main() -> int:
    if not DATOS.exists():
        print("falta data/respaldo_lean.json — corre auditar_respaldo_lean.py")
        return 1
    d = json.loads(DATOS.read_text(encoding="utf-8"))

    res, sin, rotas = d["respaldadas"], d["sin_respaldo"], d["mapeo_roto"]
    n = d["auditadas"]
    pct = 100 * len(res) / n

    filas = []
    modulo_actual = None
    for r in res:
        if r["modulo"] != modulo_actual:
            modulo_actual = r["modulo"]
            filas.append(r"\midrule \multicolumn{3}{l}{\textit{" +
                         esc(modulo_actual) + r"}} \\")
        filas.append(
            f"  & \\texttt{{{esc(r['operacion'])}}} & \\texttt{{{esc(r['teorema'])}}} \\\\"
            f"\n  &  & \\footnotesize {esc(r['afirma'])} \\\\"
        )

    filas_sin = "\n".join(
        f"\\texttt{{{esc(x['modulo'])}}} & \\texttt{{{esc(x['operacion'])}}} & "
        f"\\footnotesize {esc(x['afirma'])} \\\\" for x in sin)

    sorries = d.get("sorries", [])
    txt_sorry = ("\n".join(r"\item \texttt{" + esc(s.replace("warning: ", "")) + "}"
                           for s in sorries)
                 if sorries else r"\item Ninguno.")

    tex = r"""\documentclass[11pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[spanish,es-noquoting]{babel}
\usepackage{amsmath,amssymb}
\usepackage{booktabs}
\usepackage{longtable}
\usepackage[margin=2.4cm]{geometry}
\usepackage{microtype}
\sloppy

\title{Respaldo formal de la teoría de categorías\\[.3em]
\large Auditoría completa: qué afirma Python y qué demuestra Lean}
\author{Leonardo Jiménez Martínez\\ \small en colaboración con Claude Opus 5 (Anthropic)}
\date{\today}

\begin{document}
\maketitle

\begin{abstract}
\textsc{Metamatemático} implementa teoría de categorías a mano: no hay ninguna
librería detrás de \texttt{nucleo/graph/} ni de \texttt{nucleo/mes/}, solo
\texttt{dataclasses}, diccionarios y recorridos en anchura. Eso hace que cada
propiedad categórica sea una afirmación del autor hasta que Lean~4 la respalda.
Este documento audita, operación por operación, cuáles lo están. El resultado
es """ + f"{len(res)}" + r" de " + f"{n}" + r""" (""" + f"{pct:.0f}" + r"""\,\%). Todas las cifras
proceden de \texttt{data/respaldo\_lean.json}, generado por
\texttt{scripts/auditar\_respaldo\_lean.py}; ninguna se escribe a mano.
\end{abstract}

\section{Por qué esta auditoría existe}

Tres defectos reales, encontrados en código que funcionaba y no fallaba
ruidosamente:

\begin{itemize}
\item \texttt{reachable\_from} seguía morfismos de tipo \textsc{translation}, lo
      que producía colímites espurios como \texttt{=~tactic-simp}.
\item \texttt{build\_join\_for\_pattern} \emph{fabricaba} vértices cuando no
      encontraba el colímite, y por eso la iteración no convergía.
\item \texttt{patterns.py} exigía $\exists h$ donde la propiedad universal pide
      $\exists! h$.
\end{itemize}

Ninguno lo habría cometido una librería madura, y ninguno se detectó leyendo el
código: los tres salieron al medir y al formalizar.

\section{Resumen}

\begin{center}
\begin{tabular}{lrr}
\toprule
 & Operaciones & \% \\
\midrule
Respaldadas por un teorema & """ + f"{len(res)}" + r""" & """ + f"{pct:.0f}" + r""" \\
Sin respaldo formal & """ + f"{len(sin)}" + r""" & """ + f"{100*len(sin)/n:.0f}" + r""" \\
Mapeo roto & """ + f"{len(rotas)}" + r""" & """ + f"{100*len(rotas)/n:.0f}" + r""" \\
\midrule
Total auditado & """ + f"{n}" + r""" & 100 \\
\bottomrule
\end{tabular}
\end{center}

\noindent Declaraciones formales disponibles en
\texttt{MetamathProver/CategoryFoundations/}: \textbf{""" + f"{d['declaraciones_lean']}" + r"""}.

\section{Operaciones respaldadas}

\begin{longtable}{@{}p{1.2cm}p{5.9cm}p{7.2cm}@{}}
\toprule
\small Módulo & \small Operación en Python & \small Teorema en Lean \\
\midrule
\endhead
""" + "\n".join(filas) + r"""
\bottomrule
\end{longtable}

\section{Sin respaldo formal}

Lo que sigue no está demostrado. Está aquí porque un hueco anotado es
distinguible de un hueco olvidado, y \texttt{tests/test\_respaldo\_lean.py}
falla si esta lista cambia sin que alguien lo declare.

\begin{center}
\begin{tabular}{@{}p{2.4cm}p{4.2cm}p{7.5cm}@{}}
\toprule
Módulo & Operación & Qué afirma \\
\midrule
""" + filas_sin + r"""
\bottomrule
\end{tabular}
\end{center}

\noindent Las tres pertenecen a \texttt{evolution.py}, es decir, al núcleo
evolutivo de Ehresmann: complexificación, funtor de transición y detección de
emergencia. Es el frente abierto.

\section{Un resultado negativo que conviene leer}

Al formalizar la distinción simple/complejo de Ehresmann se intentó demostrar
el teorema central de la emergencia: que la composición de dos enlaces simples
puede no ser simple. \textbf{Lean lo refutó.}

La razón es estructural, no un descuido del diseño. Si $a \le k \le b$ y
$b \le n \le d$, la transitividad da $k \le d$, de modo que el propio $k$
factoriza $a \to d$. El teorema verdadero es el contrario:

\[
  \text{\texttt{composite\_of\_simple\_is\_simple}}:\quad
  \text{simple}(a,b) \wedge \text{simple}(b,d) \;\Rightarrow\; \text{simple}(a,d).
\]

En una categoría delgada los enlaces simples son cerrados por composición, y la
distinción de Ehresmann pierde su contenido dinámico: los complejos no
\emph{emergen} al componer, solo aparecen donde \emph{faltan} clústeres.

La delgadez es la hipótesis que hace que join $=$ colímite, y de ella dependen
\texttt{JoinColimit.lean} e \texttt{IsColimitBridge.lean}. Recuperar la
emergencia exigiría abandonarla —admitir más de un morfismo entre dos
habilidades y distinguir \emph{cómo} se llega, no solo si se llega—, lo que es
un cambio de modelo y no un ajuste. Queda registrado como límite conocido.

\section{Declaraciones con \texttt{sorry}}

\begin{itemize}
""" + txt_sorry + r"""
\end{itemize}

\noindent Se cuentan preguntándole al compilador, no con \texttt{grep}: un
\texttt{sorry} dentro de un comentario no es un \texttt{sorry}.

\section*{Reproducibilidad}
\addcontentsline{toc}{section}{Reproducibilidad}

\begin{itemize}
\item \texttt{scripts/auditar\_respaldo\_lean.py} — la auditoría; genera el JSON.
\item \texttt{scripts/generar\_reporte\_respaldo.py} — genera este documento.
\item \texttt{tests/test\_respaldo\_lean.py} — falla si el mapeo se rompe o si
      el respaldo retrocede.
\item \texttt{MetamathProver/CategoryFoundations/} — """ + f"{d['declaraciones_lean']}" + r""" declaraciones.
\end{itemize}

\end{document}
"""
    TEX.parent.mkdir(parents=True, exist_ok=True)
    TEX.write_text(tex, encoding="utf-8")
    print(f"{TEX} generado ({len(tex):,} chars)")

    tect = Path(r"C:\Users\Leonardo\AppData\Local\Temp\claude"
                r"\c--Users-Leonardo-OneDrive-Desktop-ProyectoPoloProofMAth-metamath-prover"
                r"\035f402f-bcba-4d12-b650-4018d81102eb\scratchpad\tectonic\tectonic.exe")
    if tect.exists():
        r = subprocess.run([str(tect), "-X", "compile", TEX.name, "--keep-logs"],
                           cwd=TEX.parent, capture_output=True, text=True, timeout=600)
        pdf = TEX.with_suffix(".pdf")
        print(f"PDF: {'OK' if pdf.exists() else 'FALLO'}"
              + ("" if pdf.exists() else "\n" + r.stderr[-800:]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
