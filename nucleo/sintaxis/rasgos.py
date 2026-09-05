# -*- coding: utf-8 -*-
"""Los rasgos estructurales de una consulta, leídos de su ÁRBOL.

DE DÓNDE VIENE ESTO
-------------------
`scripts/sintaxis_contra_premisas.py` demostró que 68 rasgos estructurales
igualan a 40 000 n-gramas de caracteres prediciendo qué lemas hace falta, y
`estado_contra_tactica.py` que GANAN a los n-gramas prediciendo qué táctica
cierra un objetivo (61,1 % contra 60,5 %, con cien veces menos rasgos).

Pero aquellos rasgos se calculan sobre ENUNCIADOS DE LEAN, que sólo existen
después de que el modelo formalice — o sea, después del paso 2. Para el paso 1
no servían: allí sólo hay la consulta del alumno.

Éstos se calculan sobre el árbol de la consulta, así que están disponibles
ANTES de llamar al modelo. Es el mismo vocabulario de rasgos —relación
principal, tipos, operadores, conectivas, profundidad, simetría— trasladado de
un enunciado de Lean a una expresión escrita a mano.

LO QUE CAMBIA AL TENER ÁRBOL Y NO TEXTO
---------------------------------------
La relación principal deja de ser «la primera que aparece» y pasa a ser la que
MANDA en la expresión: la más superficial del árbol. Sobre
`(a+b)^2 = a^2 + 2ab + b^2` un buscador de texto encuentra `=`, `+` y `^` sin
saber cuál gobierna; el árbol dice que la raíz es `=` y que las potencias
cuelgan de ella. Es la diferencia entre contar símbolos y leer una expresión.
"""
from __future__ import annotations

import collections
from typing import Optional

from nucleo.sintaxis.arbol import (ES_LOGICA, ES_RELACION, Nodo,
                                   bien_formada)

#: Los tipos que se nombran con letra de molde. Un `ℝ` en la consulta dice
#: mucho más que la palabra «real», porque la palabra también aparece en
#: «realmente» y el símbolo no aparece por accidente.
TIPOS = {"ℝ": "R", "ℕ": "N", "ℤ": "Z", "ℚ": "Q", "ℂ": "C", "𝔽": "F"}

#: Operadores cuya PRESENCIA discrimina. `√` sobre ℤ no existe, `∫` es
#: análisis, `!` es combinatoria: cada uno acota el área sin decir su nombre.
OPERADORES_MARCA = ["^", "√", "∑", "∏", "∫", "!", "%", "/", "∂", "∇"]

CONECTIVAS = ["∧", "∨", "¬", "∀", "∃", "→", "↔", "->", "<->", "⟹", "⟺"]


def _relacion_principal(n: Optional[Nodo]) -> str:
    """La relación que MANDA: la más superficial del árbol, no la primera.

    Se busca por anchura a propósito. En profundidad, `(a+b)^2 = a^2` daría
    con el `^` de la izquierda antes que con el `=` que gobierna, y la
    relación principal es justo la que gobierna.
    """
    if n is None:
        return "ninguna"
    cola = collections.deque([n])
    while cola:
        x = cola.popleft()
        if x.clase == "bin" and x.valor in ES_RELACION:
            return x.valor
        cola.extend(x.hijos)
    return "ninguna"


def _conectiva_principal(n: Optional[Nodo]) -> str:
    """Igual, pero para la lógica: `→` en «si p entonces q»."""
    if n is None:
        return "ninguna"
    cola = collections.deque([n])
    while cola:
        x = cola.popleft()
        if x.clase == "bin" and x.valor in ES_LOGICA:
            return x.valor
        if x.clase == "prefijo" and x.valor in ("∀", "∃", "∄", "¬"):
            return x.valor
        cola.extend(x.hijos)
    return "ninguna"


def _simetrica(n: Optional[Nodo]) -> bool:
    """¿Cada variable aparece el mismo número de veces?

    `a + b + c` frente a `a + 2b`. Una desigualdad simétrica se ataca distinto
    que una que no lo es — es el rasgo que en Lean predice `sq_nonneg`.
    """
    if n is None:
        return False
    c = collections.Counter(x.valor for x in n.recorrer() if x.clase == "var")
    return len(c) > 1 and len(set(c.values())) == 1


def rasgos_de_arbol(n: Optional[Nodo]) -> dict:
    """El vocabulario de rasgos, calculado sobre el árbol."""
    f: dict[str, int] = {}
    rel = _relacion_principal(n)
    con = _conectiva_principal(n)
    f["rel=%s" % rel] = 1
    f["conec=%s" % con] = 1
    f["hay_relacion"] = int(rel != "ninguna")
    f["hay_logica"] = int(con != "ninguna")

    if n is None:
        for t in TIPOS.values():
            f["tipo_%s" % t] = 0
        for o in OPERADORES_MARCA:
            f["op_%s" % o] = 0
        f.update({"n_variables": 0, "n_numeros": 0, "prof_max": 0,
                  "n_grupos": 0, "n_aplicaciones": 0, "simetrica": 0,
                  "n_nodos": 0})
        return f

    nodos = list(n.recorrer())
    valores = {x.valor for x in nodos}
    for simbolo, nombre in TIPOS.items():
        f["tipo_%s" % nombre] = int(simbolo in valores)
    for o in OPERADORES_MARCA:
        f["op_%s" % o] = int(o in valores)
    for c in CONECTIVAS:
        f["tiene_%s" % c] = int(c in valores)

    f["n_variables"] = len({x.valor for x in nodos if x.clase == "var"})
    f["n_numeros"] = sum(1 for x in nodos if x.clase == "num")
    f["n_grupos"] = sum(1 for x in nodos if x.clase == "grupo")
    f["n_aplicaciones"] = sum(1 for x in nodos if x.clase == "aplicacion")
    f["prof_max"] = min(n.profundidad(), 12)
    f["n_nodos"] = min(len(nodos), 60)
    f["simetrica"] = int(_simetrica(n))
    return f


def rasgos_de_consulta(consulta: str) -> dict:
    """Los rasgos de una consulta del alumno, antes de llamar a nadie.

    Una consulta SIN notación devuelve el vector de ceros con
    `rel=ninguna` — que es información, no un hueco: dice que el enunciado
    está escrito en prosa, y la prosa se recupera por otras vías.
    """
    d = bien_formada(consulta)
    f = rasgos_de_arbol(d.arbol if d.ok else None)
    f["bien_formada"] = int(d.ok)
    f["sin_notacion"] = int(d.arbol is None)
    return f
