# -*- coding: utf-8 -*-
"""La expresión como ÁRBOL, y si está bien formada.

QUÉ RESUELVE
------------
Hasta aquí el sistema trataba la notación como texto. Un texto no sabe cuál es
su relación principal, ni qué es hipótesis y qué es tesis, ni si le falta un
paréntesis. Un árbol sí, y las tres cosas son lo que el paso 1 necesita para
recuperar bien y lo que hace falta para no gastar una llamada al modelo en una
consulta que no está bien escrita.

EL ANÁLISIS ES POR PRECEDENCIA (escalada de Pratt). Las precedencias van de lo
más flojo a lo más fuerte, que es el orden en que un matemático las lee:

    ↔          la equivalencia ata lo último
    →          la implicación
    ∨  ∧  ¬    las conectivas
    = < ≤ ∈ ∣  LAS RELACIONES  ← la que manda en el enunciado
    + -
    * / ·
    -unario
    ^ _        asocia a la DERECHA: a^b^c es a^(b^c)
    !          postfijo
    átomos

LO QUE NO HACE, y se dice para que nadie lo tome por un parser de LaTeX:
`\\frac{a}{b}` se lee como el comando `\\frac` seguido de dos grupos, no como
una fracción con numerador y denominador. Para saber la relación principal, si
hay cuantificadores y si los delimitadores casan, sobra.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from nucleo.sintaxis.lexico import (ABRE, CIERRA, Token, tokenizar)

# ═══════════════════════════════════════════════════════════════════════════
# EL ÁRBOL
# ═══════════════════════════════════════════════════════════════════════════
@dataclass
class Nodo:
    """Un nodo de la expresión.

    `clase` dice qué es: num, var, comando, bin, prefijo, postfijo, grupo,
    aplicacion, lista. `valor` es el símbolo, y `hijos` los operandos.
    """
    clase: str
    valor: str = ""
    hijos: list["Nodo"] = field(default_factory=list)

    def __repr__(self) -> str:            # pragma: no cover - depuración
        if not self.hijos:
            return "%s(%s)" % (self.clase, self.valor)
        return "%s(%s %s)" % (self.clase, self.valor,
                              " ".join(repr(h) for h in self.hijos))

    def recorrer(self):
        yield self
        for h in self.hijos:
            yield from h.recorrer()

    def profundidad(self) -> int:
        return 1 + max((h.profundidad() for h in self.hijos), default=0)


#: (símbolo -> (precedencia, asocia a la derecha)). Menor liga más flojo.
BINARIOS: dict[str, tuple[int, bool]] = {}
for _s in ("↔", "⟺", "<->"):
    BINARIOS[_s] = (1, False)
for _s in ("→", "⟹", "->"):
    BINARIOS[_s] = (2, True)
BINARIOS["∨"] = (3, False)
BINARIOS["∧"] = (4, False)
for _s in ("=", "<", ">", "≤", "≥", "≠", "<=", ">=", "!=", "==", "≡", "≅",
           "∼", "≈", "∈", "∉", "⊂", "⊆", "⊄", "⊃", "⊇", "∣", "∤"):
    BINARIOS[_s] = (6, False)
for _s in ("+", "-", "±", "∪", "∖"):
    BINARIOS[_s] = (7, False)
for _s in ("*", "/", "·", "×", "÷", "∩", "∘", "%"):
    BINARIOS[_s] = (8, False)
for _s in ("^", "_"):
    BINARIOS[_s] = (10, True)     # a la derecha: a^b^c = a^(b^c)

PREFIJOS = {"¬": 5, "∀": 5, "∃": 5, "∄": 5, "-": 9, "+": 9,
            "√": 9, "∑": 5, "∏": 5, "∫": 5, "∂": 9, "∇": 9}
POSTFIJOS = {"!": 11}

#: `[0,∞)` y `(0,1]` son intervalos medio abiertos, notación estándar, no
#: delimitadores descasados. Medido: 54 de 3000 enunciados buenos se
#: rechazaban por esto —el dominio de un logaritmo, la mitad de las veces.
_INTERVALO = {("[", ")"), ("(", "]")}

#: Los que son RELACIÓN, para saber cuál manda en el enunciado.
ES_RELACION = {s for s, (p, _d) in BINARIOS.items() if p == 6}
ES_LOGICA = {s for s, (p, _d) in BINARIOS.items() if p <= 4}


# ═══════════════════════════════════════════════════════════════════════════
# DIAGNÓSTICO
# ═══════════════════════════════════════════════════════════════════════════
@dataclass
class Diagnostico:
    """Qué se pudo leer, y qué está mal si algo lo está."""
    ok: bool
    arbol: Optional[Nodo] = None
    fallos: list[str] = field(default_factory=list)
    detalle: list[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.ok


class _Fallo(Exception):
    def __init__(self, codigo: str, detalle: str = ""):
        super().__init__(codigo)
        self.codigo, self.detalle = codigo, detalle


class _Parser:
    def __init__(self, toks: list[Token]):
        self.t = toks
        self.i = 0

    def _mira(self) -> Optional[Token]:
        return self.t[self.i] if self.i < len(self.t) else None

    def _come(self) -> Token:
        tok = self.t[self.i]
        self.i += 1
        return tok

    # ── expresión ────────────────────────────────────────────────────────
    #: Tokens que pueden ABRIR un átomo. Si uno aparece justo detrás de otro
    #: átomo, entre los dos hay una multiplicación que nadie escribió: `2ab`,
    #: `3x`, `2(a+b)`. Sin esto el parser rechazaba
    #: `(a+b)^2 = a^2 + 2ab + b^2`, que es notación perfectamente correcta —y
    #: un falso positivo aquí es peor que no mirar, porque rechaza consultas
    #: buenas.
    _ABRE_ATOMO = ("numero", "var", "comando", "abre")

    #: `2\\sum a^3b` y `3\\sqrt{2}` son productos implícitos igual que `2ab`,
    #: pero el que sigue es un operador y no un átomo. Medido: 144 de 3000
    #: enunciados buenos —el 4,8 %— se rechazaban con «∑ queda suelto».
    _ABRE_GRANDE = ("\u221a", "\u2211", "\u220f", "\u222b")

    def expr(self, minimo: int = 0) -> Nodo:
        izq = self.unario()
        while True:
            tok = self._mira()
            # yuxtaposición: `2ab` es `2 * a * b`
            if (tok is not None
                    and (tok.tipo in self._ABRE_ATOMO
                         or tok.valor in self._ABRE_GRANDE)
                    and BINARIOS["*"][0] >= minimo):
                der_nodo = self.expr(BINARIOS["*"][0] + 1)
                izq = Nodo("bin", "*", [izq, der_nodo])
                continue
            if tok is None or tok.valor not in BINARIOS:
                break
            prec, der = BINARIOS[tok.valor]
            if prec < minimo:
                break
            self._come()
            sig = prec if der else prec + 1
            if self._mira() is None:
                raise _Fallo("operador_sin_operando",
                             "«%s» no tiene nada a la derecha" % tok.valor)
            marca = self._marca_de_indice(tok.valor)
            der_nodo = marca if marca is not None else self.expr(sig)
            izq = Nodo("bin", tok.valor, [izq, der_nodo])
        return izq

    #: Los operadores GRANDES llevan limites pegados antes del cuerpo:
    #: `∫_0^1 x^2 dx`, `∑_{i=1}^n i`. Sin esto el parser leia el `_`
    #: como binario sin izquierda y rechazaba la integral entera —otro falso
    #: positivo, de los que rechazan notacion buena.
    _GRANDES = ("∑", "∏", "∫")

    def unario(self) -> Nodo:
        tok = self._mira()
        if tok is None:
            raise _Fallo("expresion_vacia", "no hay nada que leer")
        if tok.valor in PREFIJOS and (tok.tipo in ("op", "log")):
            self._come()
            limites: list[Nodo] = []
            if tok.valor in self._GRANDES:
                limites = self._limites()
            if self._mira() is None:
                if limites:
                    # `∑_{i=1}^n` sin cuerpo visible es legitimo al final
                    # de un tramo; se conserva lo leido en vez de tirarlo.
                    return Nodo("prefijo", tok.valor, limites)
                raise _Fallo("operador_sin_operando",
                             "«%s» abre y no cierra" % tok.valor)
            cuerpo = self.expr(PREFIJOS[tok.valor])
            return Nodo("prefijo", tok.valor, [cuerpo] + limites)
        return self.postfijo()

    #: Los signos que en un índice son una MARCA y no una operación:
    #: `ℝ^+` (los positivos), `A^T` (la traspuesta), `x^*` (el conjugado).
    #: Sin esto, `\\mathbb{R^+}` se leía como «erre elevado a más-algo» y el
    #: `+` se quedaba sin operando: 37 de 3000 enunciados buenos, el 1,2 %.
    _MARCAS = ("+", "-", "*", "\u2217", "\u22c6")

    def _marca_de_indice(self, operador: str) -> Optional[Nodo]:
        """Si detrás de `^` o `_` hay una marca suelta, la devuelve."""
        if operador not in ("^", "_"):
            return None
        tok = self._mira()
        if tok is None or tok.valor not in self._MARCAS:
            return None
        sig = self.t[self.i + 1] if self.i + 1 < len(self.t) else None
        if sig is not None and sig.tipo in ("numero", "var", "comando", "abre"):
            return None                      # `2^-3` es un exponente de verdad
        self._come()
        return Nodo("marca", tok.valor)

    def _limites(self) -> list[Nodo]:
        """Los `_inferior` y `^superior` que cuelgan de un operador grande."""
        fuera: list[Nodo] = []
        while True:
            tok = self._mira()
            if tok is None or tok.valor not in ("_", "^"):
                return fuera
            self._come()
            if self._mira() is None:
                raise _Fallo("operador_sin_operando",
                             "«%s» no tiene limite" % tok.valor)
            fuera.append(Nodo("limite", tok.valor, [self.postfijo()]))

    def postfijo(self) -> Nodo:
        n = self.atomo()
        while True:
            tok = self._mira()
            if tok is None or tok.valor not in POSTFIJOS:
                break
            self._come()
            n = Nodo("postfijo", tok.valor, [n])
        return n

    def atomo(self) -> Nodo:
        tok = self._mira()
        if tok is None:
            raise _Fallo("expresion_vacia", "falta un operando")
        if tok.tipo == "abre":
            self._come()
            cierre = ABRE[tok.valor]
            partes = [self.expr(0)]
            while self._mira() is not None and self._mira().tipo == "coma":
                self._come()
                partes.append(self.expr(0))
            sig = self._mira()
            if sig is None:
                raise _Fallo("delimitador_sin_cerrar",
                             "falta «%s»" % cierre)
            if sig.valor != cierre and (tok.valor, sig.valor) not in _INTERVALO:
                raise _Fallo("delimitador_sin_cerrar",
                             "se abrió «%s» y se cerró «%s»"
                             % (tok.valor, sig.valor))
            self._come()
            dentro = partes[0] if len(partes) == 1 else Nodo("lista", ",", partes)
            return Nodo("grupo", tok.valor, [dentro])
        if tok.tipo == "cierra":
            raise _Fallo("delimitador_sin_abrir",
                         "«%s» cierra algo que no se abrió" % tok.valor)
        if tok.tipo in ("numero", "var", "comando"):
            self._come()
            n = Nodo({"numero": "num", "var": "var",
                      "comando": "comando"}[tok.tipo], tok.valor)
            # aplicación: `f(x)`, `sin(x)` — un átomo seguido de un grupo
            sig = self._mira()
            if sig is not None and sig.tipo == "abre" and tok.tipo != "numero":
                arg = self.atomo()
                return Nodo("aplicacion", tok.valor, [arg])
            return n
        raise _Fallo("token_inesperado", "«%s» no cabe aquí" % tok.valor)


def parsear(texto: str) -> Diagnostico:
    """Lee un tramo de notación y devuelve su árbol, o por qué no se pudo."""
    toks = tokenizar(texto)
    if not toks:
        return Diagnostico(False, None, ["expresion_vacia"],
                           ["no hay notación que leer"])
    # UN TRAMO PUEDE SER UN FRAGMENTO. Quien escribe `$a$ $\\geq$ $b$` parte
    # una sola fórmula en tres trozos, y dos de ellos empiezan por una
    # relación. Rechazarlos era decirle que su enunciado está mal cuando lo
    # que pasa es que usa el dólar para dar espacio. Se pone un hueco a la
    # izquierda y se sigue leyendo.
    hueco = False
    if toks[0].valor in BINARIOS and toks[0].valor not in PREFIJOS:
        toks = [Token("var", "?", toks[0].pos)] + toks
        hueco = True
    # Y la puntuación de la frase que se coló dentro del dólar —`$a, b, c,$`,
    # `$x\\le 1.$`— no es parte de la fórmula.
    while toks and toks[-1].tipo == "coma":
        toks.pop()
    # Y una RELACIÓN al final tampoco cierra nada: `$a \\ge$ $b$` corta la
    # fórmula justo detrás del signo. Se quita sólo si es relación o lógica
    # —un `+` colgando sí es sospechoso y se sigue cazando—.
    while toks and toks[-1].tipo in ("rel", "log"):
        toks.pop()
    if not toks or (hueco and len(toks) < 3):
        return Diagnostico(False, None, ["expresion_vacia"],
                           ["no hay notación que leer"])
    p = _Parser(toks)
    try:
        # LA COMA DE PRIMER NIVEL SEPARA, NO ROMPE. `∀x ∈ ℝ, x² ≥ 0` pone el
        # alcance del cuantificador a un lado y el cuerpo al otro; leerlo como
        # error rechazaba una de las formas más comunes de escribir un
        # enunciado con símbolos.
        partes = [p.expr(0)]
        # La coma separa; y un cuantificador que aparece DESPUÉS de una
        # expresión completa —`|z| ≥ 0 ∀z ∈ ℂ`— también abre una parte nueva,
        # que es como se escribe «para todo» al final de una frase.
        while True:
            sig = p._mira()
            if sig is None:
                break
            if sig.tipo == "coma":
                p._come()
                if p._mira() is None:
                    break
                partes.append(p.expr(0))
                continue
            if sig.valor in ("∀", "∃", "∄"):
                partes.append(p.expr(0))
                continue
            break
        arbol = partes[0] if len(partes) == 1 else Nodo("lista", ",", partes)
    except _Fallo as f:
        return Diagnostico(False, None, [f.codigo], [f.detalle])
    except RecursionError:                            # pragma: no cover
        return Diagnostico(False, None, ["demasiado_anidada"],
                           ["la expresión anida más de lo razonable"])
    sobra = p._mira()
    if sobra is not None:
        return Diagnostico(False, arbol, ["sobra_texto"],
                           ["«%s» queda suelto al final" % sobra.valor])
    return Diagnostico(True, arbol)


def bien_formada(consulta: str) -> Diagnostico:
    """¿La notación de esta consulta está bien escrita?

    UNA CONSULTA SIN NOTACIÓN ESTÁ BIEN FORMADA. «Demuestra que en un grupo el
    elemento neutro es único» no tiene fórmula que revisar, y decir que está
    mal sería peor que no mirar: se rechazaría media biblioteca de enunciados
    perfectamente correctos.

    Se informa del PRIMER tramo que falla, con su código y su detalle, porque
    lo que el alumno necesita es saber dónde mirar, no un listado.
    """
    from nucleo.sintaxis.lexico import extraer
    tramos = extraer(consulta)
    if not tramos:
        return Diagnostico(True, None)
    arboles = []
    for t in tramos:
        d = parsear(t.texto)
        if not d.ok:
            return Diagnostico(False, None, d.fallos,
                               ["en «%s»: %s" % (t.texto, x) for x in d.detalle])
        arboles.append(d.arbol)
    if len(arboles) == 1:
        return Diagnostico(True, arboles[0])
    return Diagnostico(True, Nodo("lista", "·", arboles))
