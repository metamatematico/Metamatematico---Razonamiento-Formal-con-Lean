# -*- coding: utf-8 -*-
"""Encontrar la notación de una consulta, y partirla en piezas.

POR QUÉ SE REHACE Y NO SE PARCHEA
---------------------------------
`traductor.NOTACION` es una regex, y una regex no puede reconocer una expresión
porque una expresión es un ÁRBOL. Medido sobre seis consultas reales:

    (a+b)^2 = a^2 + 2ab + b^2      ->  ['2 = a^2']     parte por la mitad
    f(x) = x^2 + 1                 ->  ['2 + 1']       idem
    \\int_0^\\infty e^{-x} dx        ->  ['\\int','\\infty'] sólo los comandos
    n^2 es par si y sólo si n es par -> []             pierde `n^2`
    ¿Es 17 un número primo?        ->  []              pierde el 17
    ∀x ∈ ℝ, x² ≥ 0                 ->  []              NADA en Unicode

El último es el que obliga a rehacerlo: el alumno que escribe con símbolos
—que es el que más notación usa— era invisible.

CÓMO SE DECIDE QUÉ ES NOTACIÓN
------------------------------
Dos vías, en este orden:

  1. DELIMITADORES EXPLÍCITOS. `$...$`, `$$...$$`, `\\[...\\]`, `\\(...\\)`.
     Si el alumno los puso, el tramo es exactamente lo que encerró. No se
     adivina nada.

  2. RACHAS MAXIMALES. Sin delimitadores, un tramo es la racha más larga de
     piezas matemáticas seguidas. Una pieza es matemática si es un símbolo
     (operador, relación, delimitador, letra de conjunto), un número, o una
     PALABRA CORTA —una o dos letras, que es como se escriben las variables—
     o una función conocida (`sin`, `log`, `lim`...).

     La racha se corta en cuanto aparece una palabra larga que no es función:
     `es`, `par`, `primo`, `demuestra`. Eso es lo que separa la notación de la
     prosa sin necesidad de saber español.

LO QUE ESTO NO HACE. No entiende LaTeX completo: `\\frac{a}{b}` entra como
tramo pero sus llaves se leen como delimitadores, no como argumentos. Para lo
que hace falta —saber la relación principal, si hay cuantificadores, y si la
expresión está bien formada— es suficiente, y se dice para que nadie lo tome
por un parser de LaTeX.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Optional

# ═══════════════════════════════════════════════════════════════════════════
# EL ALFABETO
# ═══════════════════════════════════════════════════════════════════════════
#: Relaciones. El orden importa al tokenizar: las de dos caracteres primero,
#: para que `<=` no salga como `<` seguido de `=`.
RELACIONES = ["<=", ">=", "!=", "==", "≤", "≥", "≠", "≡", "≅", "∼", "≈",
              "∈", "∉", "⊂", "⊆", "⊄", "⊃", "⊇", "∣", "∤", "=", "<", ">"]

#: Conectivas lógicas y cuantificadores.
LOGICA = ["<->", "->", "⟺", "⟹", "↔", "→", "∧", "∨", "¬", "∀", "∃", "∄"]

#: Operadores aritméticos y de conjunto.
OPERADORES = ["+", "-", "*", "/", "^", "±", "×", "÷", "·", "∘", "∪", "∩",
              "∖", "√", "∑", "∏", "∫", "∂", "∇", "!", "%"]

#: Delimitadores. Se emparejan al comprobar la buena formación.
ABRE = {"(": ")", "[": "]", "{": "}", "⟨": "⟩", "⌊": "⌋", "⌈": "⌉"}
CIERRA = {v: k for k, v in ABRE.items()}

#: Tipos y conjuntos que se escriben con una sola letra de molde.
CONJUNTOS = ["ℝ", "ℕ", "ℤ", "ℚ", "ℂ", "𝔽", "∅", "∞"]

#: Funciones que se escriben con palabra y SÍ son notación. Sin esta lista,
#: `sin x` se corta en `sin` y la racha se pierde — y `sin` en español es
#: además una preposición, que es justo el caso que rompía al traductor.
FUNCIONES = {
    "sin", "cos", "tan", "sec", "csc", "cot", "arcsin", "arccos", "arctan",
    "senh", "cosh", "tanh", "sen", "log", "ln", "exp", "lim", "max", "min",
    "sup", "inf", "det", "dim", "deg", "gcd", "mcd", "mcm", "lcm", "mod",
    "sqrt", "abs", "int", "sum", "prod", "frac", "binom", "cdot", "infty",
    "forall", "exists", "in", "subset", "cup", "cap", "leq", "geq", "neq",
    "mathbb", "mathcal", "mathrm", "left", "right", "quad", "text",
}

#: COMANDO LaTeX -> su simbolo. Media clase escribe `\int` y la otra media
#: `∫`; sin este mapa las dos consultas dan rasgos distintos y el sistema
#: aprende dos veces la misma cosa. Es la misma normalizacion que se hace con
#: los acentos, un nivel mas arriba.
COMANDO_SIMBOLO = {
    r"\int": "\u222b", r"\sum": "\u2211", r"\prod": "\u220f",
    r"\sqrt": "\u221a", r"\infty": "\u221e", r"\partial": "\u2202",
    r"\nabla": "\u2207",
    r"\leq": "\u2264", r"\le": "\u2264", r"\geq": "\u2265",
    r"\ge": "\u2265", r"\neq": "\u2260", r"\ne": "\u2260",
    r"\equiv": "\u2261", r"\approx": "\u2248",
    r"\in": "\u2208", r"\notin": "\u2209", r"\subset": "\u2282",
    r"\subseteq": "\u2286", r"\supset": "\u2283", r"\supseteq": "\u2287",
    r"\mid": "\u2223",
    r"\cup": "\u222a", r"\cap": "\u2229", r"\setminus": "\u2216",
    r"\times": "\u00d7", r"\div": "\u00f7", r"\cdot": "\u00b7",
    r"\circ": "\u2218", r"\pm": "\u00b1",
    r"\forall": "\u2200", r"\exists": "\u2203",
    r"\land": "\u2227", r"\wedge": "\u2227", r"\lor": "\u2228",
    r"\vee": "\u2228", r"\neg": "\u00ac", r"\lnot": "\u00ac",
    r"\to": "\u2192", r"\rightarrow": "\u2192", r"\implies": "\u27f9",
    r"\leftrightarrow": "\u2194", r"\iff": "\u27fa",
    r"\emptyset": "\u2205", r"\varnothing": "\u2205",
}

#: `\mathbb{R}` es como se escribe un conjunto en LaTeX, y sin esto la mitad
#: de las consultas escritas en LaTeX perdian el rasgo del tipo. Se resuelve
#: ANTES de tokenizar, sustituyendo la pareja comando+llaves por el simbolo.
_MATHBB = re.compile(
    r"\\mathbb\s*\{\s*([A-Z])\s*\^\s*\{([^{}]*)\}\s*\}"   # \mathbb{R^{+}}
    r"|\\mathbb\s*\{\s*([A-Z])([^{}]*?)\s*\}"                 # \mathbb{R}, {R^+}
    r"|\\mathbb\s+([A-Z])\b")                                  # \mathbb R
_LETRA_CONJUNTO = {"R": "\u211d", "N": "\u2115", "Z": "\u2124",
                   "Q": "\u211a", "C": "\u2102", "F": "\U0001d53d"}


def _bb(m: "re.Match") -> str:
    """`\\mathbb{R}`, `\\mathbb{R^+}`, `\\mathbb R` -> `ℝ` (+ lo que colgaba).

    Las tres formas aparecen en los datos y las tres decían lo mismo. Sin
    unificarlas, `a, b, c \\in \\mathbb{R^+}` se rechazaba —el `+` quedaba sin
    operando— y el rasgo `tipo_R` se perdía en 1 de cada 40 enunciados.
    """
    if m.group(1):
        return _LETRA_CONJUNTO.get(m.group(1), m.group(0)) + "^" + m.group(2)
    if m.group(3):
        return _LETRA_CONJUNTO.get(m.group(3), m.group(0)) + (m.group(4) or "")
    return _LETRA_CONJUNTO.get(m.group(5), m.group(0))


def normalizar_latex(texto: str) -> str:
    r"""`\mathbb{R}` -> `ℝ`. Se aplica al tokenizar, no al buscar tramos."""
    return _MATHBB.sub(_bb, texto or "")


#: Llaves y barras escapadas: en LaTeX `\\{` es una llave literal. Si no se
#: traducen, el `\\` suelto entra como comando y descoloca el conteo.
ESCAPES = {"\\{": "{", "\\}": "}", "\\|": "|", "\\_": "_",
           "\\langle": "\u27e8", "\\rangle": "\u27e9",
           "\\lfloor": "\u230a", "\\rfloor": "\u230b",
           "\\lceil": "\u2308", "\\rceil": "\u2309"}

#: Superíndices y subíndices Unicode: `x²` es `x^2`.
_SUPER = {"⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4", "⁵": "5",
          "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9", "ⁿ": "n"}
_SUB = {"₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4", "₅": "5",
        "₆": "6", "₇": "7", "₈": "8", "₉": "9", "ₙ": "n"}

_SIMBOLOS = set("".join(RELACIONES + LOGICA + OPERADORES + CONJUNTOS)
                + "".join(ABRE) + "".join(CIERRA) + "_^,|")

#: Griegas: se usan como variables, así que cuentan como pieza matemática.
_GRIEGAS = set("αβγδεζηθικλμνξοπρστυφχψω" "ΑΒΓΔΕΖΗΘΙΚΛΜΝΞΟΠΡΣΤΥΦΧΨΩ")

#: Palabras de DOS letras que son gramática, no variables. Sólo se usan para
#: RECORTAR LOS BORDES de una racha: dentro de una expresión no aparecen, y
#: fuera de ella son lo que hacía que `n^2 es` y `Es 17 un` entraran enteros.
#:
#: Las de UNA letra NO entran nunca: `a`, `y`, `o` son preposición y
#: conjunción en español, pero también son las variables más comunes que
#: existe. Ahí manda la variable.
BORDE_NO = {
    # español
    "es", "un", "el", "la", "lo", "de", "en", "al", "se", "su", "si", "no",
    "ni", "ya", "va", "ha", "he", "me", "te", "mi", "tu", "os", "le", "da",
    # inglés
    "is", "it", "in", "on", "of", "to", "be", "we", "if", "or", "an", "as",
    "at", "by", "do", "go", "my", "so", "up", "us",
}

_PALABRA = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+")
_NUMERO = re.compile(r"\d+(?:[.,]\d+)?")
_COMANDO = re.compile(r"\\[A-Za-z]+")

#: Espaciado de LaTeX: `\,` `\;` `\!` `\:` `\ ` y el salto `\\`. No son
#: matemáticas, son tipografía. Medido: `$x+y+z=9\;,$` —un enunciado
#: perfectamente correcto— se rechazaba entero por culpa del `\;`.
_TEX_ESPACIO = re.compile(r"\\\\(?![{}|])|\\[,;:!>< ]")

#: Comandos que sólo colocan cosas en la página. Se tiran al tokenizar: si se
#: dejan, `\left(` mete un átomo delante del paréntesis y la expresión deja de
#: parsear. `\text` y `\begin`/`\end` van aquí por lo mismo.
COMANDOS_MAQUETA = {
    "\\left", "\\right", "\\limits", "\\nolimits", "\\displaystyle",
    "\\textstyle", "\\scriptstyle", "\\quad", "\\qquad", "\\,", "\\;",
    "\\!", "\\:", "\\ ", "\\\\", "\\begin", "\\end", "\\text", "\\mbox",
    "\\n", "\\t", "\\r",           # el salto de linea escrito como texto
    "\\label", "\\nonumber", "\\hspace", "\\vspace", "\\phantom",
    "\\big", "\\Big", "\\bigg", "\\Bigg", "\\bigl", "\\bigr",
    "\\Bigl", "\\Bigr", "\\biggl", "\\biggr", "\\mathrm", "\\mathcal",
    "\\mathbf", "\\boldsymbol", "\\operatorname",
}

#: Los cuatro delimitadores explícitos, de más largo a más corto.
_EXPLICITO = re.compile(
    r"\$\$(.+?)\$\$"          # $$ ... $$
    r"|\$([^$\n]+?)\$"        # $ ... $
    r"|\\\[(.+?)\\\]"         # \[ ... \]
    r"|\\\((.+?)\\\)",        # \( ... \)
    re.S)


# ═══════════════════════════════════════════════════════════════════════════
# TRAMOS
# ═══════════════════════════════════════════════════════════════════════════
@dataclass
class Tramo:
    """Un trozo de la consulta que es notación."""
    texto: str
    inicio: int
    fin: int
    explicito: bool = False   # ¿venía entre $...$?

    def __len__(self) -> int:
        return len(self.texto)


#: Símbolos que pueden ABRIR una expresión: los que también son prefijo.
#: Un `=` o un `/` al principio de una racha no abre nada —viene de la prosa.
PUEDE_ABRIR = set("-+\u221a\u2211\u220f\u222b\u2202\u2207\u00ac\u2200\u2203\u2204")

#: Símbolos que pueden CERRAR una expresión: sólo el factorial es postfijo.
PUEDE_CERRAR = set("!")

_OPERADOR = set(RELACIONES + LOGICA + OPERADORES) | {"_", "^"}


def _es_atomo(tok: str) -> bool:
    """¿Este token es algo sobre lo que operar —un número, una variable, un
    comando con contenido— y no un operador ni tipografía?"""
    if not tok or tok in COMANDOS_MAQUETA or _TEX_ESPACIO.fullmatch(tok):
        return False
    if tok.startswith("\\"):
        return tok not in COMANDO_SIMBOLO
    if _NUMERO.fullmatch(tok):
        return True
    if tok[0] in _GRIEGAS or tok in _SUPER or tok in _SUB:
        return True
    return bool(_PALABRA.fullmatch(tok))


def _es_pieza(tok: str) -> bool:
    """¿Este token puede formar parte de una expresión?"""
    if not tok:
        return False
    if tok in _SIMBOLOS or tok[0] in _SIMBOLOS:
        return True
    if tok[0] in _GRIEGAS or tok in _SUPER or tok in _SUB:
        return True
    if tok.startswith("\\"):
        return True
    if _NUMERO.fullmatch(tok):
        return True
    if _PALABRA.fullmatch(tok):
        # una o dos letras es una variable; y las funciones conocidas
        return len(tok) <= 2 or tok.lower() in FUNCIONES
    return False


def _piezas(texto: str):
    r"""(inicio, fin, token) de cada pieza del texto, en orden.

    NO se normaliza aqui. `extraer` corta el texto con estas posiciones, y
    `normalizar_latex` cambia la longitud —`\mathbb{R}` son diez caracteres y
    `R-de-molde` es uno—, asi que normalizar aqui desplazaba todos los tramos
    posteriores. La normalizacion vive en `tokenizar`, que no devuelve
    posiciones al exterior.
    """
    i, n = 0, len(texto)
    while i < n:
        c = texto[i]
        if c.isspace():
            i += 1
            continue
        m = _TEX_ESPACIO.match(texto, i)
        if m:
            yield m.start(), m.end(), m.group(0)
            i = m.end()
            continue
        m = _COMANDO.match(texto, i)
        if m:
            yield m.start(), m.end(), m.group(0)
            i = m.end()
            continue
        m = _NUMERO.match(texto, i)
        if m:
            yield m.start(), m.end(), m.group(0)
            i = m.end()
            continue
        m = _PALABRA.match(texto, i)
        if m:
            yield m.start(), m.end(), m.group(0)
            i = m.end()
            continue
        # relaciones y conectivas de dos o tres caracteres, antes que de uno
        for op in sorted(RELACIONES + LOGICA, key=len, reverse=True):
            if len(op) > 1 and texto.startswith(op, i):
                yield i, i + len(op), op
                i += len(op)
                break
        else:
            yield i, i + 1, c
            i += 1


def _recortar(racha, resto) -> Optional[Tramo]:
    """Poda los bordes de una racha y decide si merece ser tramo.

    DOS PODAS Y UN FILTRO, y los tres salieron de casos que fallaban:

      · por delante y por detrás se quitan las palabras de `BORDE_NO`, que es
        lo que metía `Es` en «¿Es 17 un número primo?» y `es` en `n^2 es`;
      · un tramo tiene que contener al menos un SÍMBOLO que no sea una coma:
        si no, `, ` suelto entraba como notación;
      · y tiene que quedar algo después de podar.
    """
    r = list(racha)
    def _podable(t):
        return _PALABRA.fullmatch(t) and t.lower() in BORDE_NO
    while r and _podable(r[0][2]):
        r.pop(0)
    while r and _podable(r[-1][2]):
        r.pop()

    # LOS BORDES QUE NO PUEDEN SER BORDE. Una racha no empieza por `)` ni por
    # `=`, y no termina por `(` ni por `+`: cuando eso pasa, el símbolo es de
    # la prosa y no de la fórmula. Es el guion de «Cauchy-Schwarz», el
    # paréntesis de «(AM-GM)», el de la enumeración «b) ...» y el `[` de
    # «[-1; 1]» partido por el punto y coma. Entre los cuatro eran 91 de 3000
    # enunciados buenos rechazados.
    def _mal_al_abrir(t):
        return (t in CIERRA
                or (t in _OPERADOR and t not in PUEDE_ABRIR))

    def _mal_al_cerrar(t):
        return (t in ABRE
                or (t in _OPERADOR and t not in PUEDE_CERRAR))

    while r and _mal_al_abrir(r[0][2]):
        r.pop(0)
    while r and _mal_al_cerrar(r[-1][2]):
        r.pop()
    if not r:
        return None
    util = [t for _a, _b, t in r
            if not _PALABRA.fullmatch(t) and t != ","]
    if not util:
        return None
    # UN TRAMO NECESITA ALGO SOBRE LO QUE OPERAR. Sin esto, el guion de
    # «Cauchy-Schwarz» y de «non-negative» entraba como tramo —era una racha
    # de un solo símbolo entre dos palabras largas— y se rechazaba como
    # «operador sin operando». Eran 126 de 3000 enunciados buenos, el 4,2 %.
    if not any(_es_atomo(t) for _a, _b, t in r):
        return None
    ini, fin = r[0][0], r[-1][1]
    return Tramo(resto[ini:fin].strip(), ini, fin)


def extraer(texto: str) -> list[Tramo]:
    """Los tramos de notación de una consulta, en orden de aparición.

    Los delimitadores explícitos mandan; el resto sale de rachas maximales.
    """
    texto = texto or ""
    tramos: list[Tramo] = []
    tapado = list(texto)

    # 1 · lo que el alumno delimitó
    for m in _EXPLICITO.finditer(texto):
        cuerpo = next(g for g in m.groups() if g is not None)
        for k in range(m.start(), m.end()):
            tapado[k] = " "
        # EL FILTRO DEL ATOMO TAMBIEN AQUI. Quien escribe `$a$ $\geq$ $b$` usa
        # el dolar para dar espacio, no para delimitar tres formulas: el de en
        # medio no tiene sobre que operar y no es un enunciado que revisar.
        if not any(_es_atomo(t) for _a, _b, t in _piezas(cuerpo)):
            continue
        tramos.append(Tramo(cuerpo.strip(), m.start(), m.end(), explicito=True))

    # 2 · rachas maximales sobre lo que queda
    resto = "".join(tapado)
    racha: list[tuple[int, int, str]] = []

    def _cerrar():
        t = _recortar(racha, resto)
        if t:
            tramos.append(t)
        racha.clear()

    for a, b, tok in _piezas(resto):
        if _es_pieza(tok):
            racha.append((a, b, tok))
        else:
            _cerrar()
    _cerrar()

    tramos.sort(key=lambda t: t.inicio)
    return [t for t in tramos if t.texto]


# ═══════════════════════════════════════════════════════════════════════════
# TOKENS
# ═══════════════════════════════════════════════════════════════════════════
@dataclass
class Token:
    tipo: str      # numero | var | rel | log | op | abre | cierra | comando | coma
    valor: str
    pos: int = 0


def _clasifica(tok: str) -> str:
    if tok in ABRE:
        return "abre"
    if tok in CIERRA:
        return "cierra"
    if tok in RELACIONES:
        return "rel"
    if tok in LOGICA:
        return "log"
    if tok in OPERADORES:
        return "op"
    if tok == ",":
        return "coma"
    if tok in ("_", "^"):
        return "op"
    if _NUMERO.fullmatch(tok):
        return "numero"
    if tok.startswith("\\"):
        return "comando"
    return "var"


def tokenizar(texto: str) -> list[Token]:
    """Los tokens de un tramo, con los superíndices Unicode ya normalizados.

    `x²` se convierte en `x ^ 2`: si no, el rasgo «hay potencia» se pierde
    justo en las consultas que más símbolos usan.
    """
    fuera: list[Token] = []
    for a, _b, tok in _piezas(normalizar_latex(texto or "")):
        if tok in COMANDOS_MAQUETA or _TEX_ESPACIO.fullmatch(tok):
            continue
        if tok in _SUPER:
            fuera.append(Token("op", "^", a))
            fuera.append(Token("numero", _SUPER[tok], a))
            continue
        if tok in _SUB:
            fuera.append(Token("op", "_", a))
            fuera.append(Token("numero", _SUB[tok], a))
            continue
        # `\int` y `∫` son el mismo operador escrito de dos maneras
        tok = ESCAPES.get(tok, COMANDO_SIMBOLO.get(tok, tok))
        fuera.append(Token(_clasifica(tok), tok, a))
    return fuera
