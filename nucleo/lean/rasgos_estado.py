# -*- coding: utf-8 -*-
"""La ESTRUCTURA de un estado de prueba de Lean, no sus caracteres.

POR QUE ESTO VIVE EN `nucleo/` Y NO EN `scripts/`
-------------------------------------------------
El rankeador de tacticas se guarda con `pickle` y se carga EN CALIENTE dentro
de la cascada. Un `Pipeline` de scikit-learn serializa la REFERENCIA a sus
transformadores, no su codigo, asi que si la clase vive en un guion de
`scripts/` la deserializacion falla en produccion con `ModuleNotFoundError` y
la cascada se queda sin modelo, en silencio y solo en el camino real.

Por eso el extractor y su envoltorio de scikit-learn estan aqui, en un modulo
importable desde el paquete.

QUE MIDE, Y POR QUE ESTOS RASGOS
--------------------------------
Un estado de prueba se parte por `⊢`, la barra de deduccion: encima lo que se
supone, debajo lo que hay que demostrar. Los rasgos leen la FORMA de las dos
mitades — la relacion principal del objetivo, los tipos que aparecen, los
operadores, las conectivas, cuantas hipotesis hay, la profundidad de anidado —
en vez de contar caracteres.

La relacion del objetivo es el rasgo que mas manda: una igualdad se cierra con
`ring`, una desigualdad con `nlinarith`, y eso no es una opinion sino lo que
hacen las 13 059 pruebas del corpus medido.

MEDIDO (`scripts/estado_contra_tactica.py`, 13 059 transiciones que CIERRAN
objetivo, 22 tacticas):

                        acierto   equilibrado
    nulo (mayoritaria)   23,77 %      4,55 %
    n-gramas             60,53 %     34,14 %
    ESTRUCTURA           61,14 %     36,26 %
    las dos juntas       67,11 %     47,65 %

Y lo que importa en operacion: los intentos de Lean por objetivo bajan de
4,64 con el orden fijo a 1,90 con el modelo. Cada intento es una compilacion
de entre 12 y 30 segundos, asi que el ahorro es el recurso mas caro del
sistema.

La ultima fila es la razon de este modulo: la estructura y los n-gramas NO son
redundantes. Juntos ganan 6,6 puntos de acierto y 13,5 de equilibrado sobre
los n-gramas solos, que es lo que el rankeador usaba.
"""
from __future__ import annotations

import collections
import re

from sklearn.base import BaseEstimator, TransformerMixin

#: La barra de deduccion. Encima las hipotesis, debajo el objetivo.
BARRA = "⊢"

RELACIONES = ["≥", "≤", ">", "<", "≠", "=", "∣", "∈", "⊆", "↔", "→"]
TIPOS = ["ℝ", "ℕ", "ℤ", "ℚ", "ℂ", "Finset", "Set", "Matrix", "Polynomial"]
OPERADORES = ["^", "√", "∑", "∏", "∫", "!", "%", "⌊", "|", "/", "*", "+", "-"]
CONECTIVAS = ["∧", "∨", "¬", "∀", "∃"]

_VAR = re.compile(r"\b[a-z]\b")


def parte_estado(estado: str) -> tuple[str, str]:
    """(hipotesis, objetivo) de un estado de prueba."""
    i = estado.find(BARRA)
    if i < 0:
        return estado, ""
    return estado[:i], estado[i + 1:]


def _profundidad(s: str) -> int:
    prof = mx = 0
    for c in s:
        if c in "([{":
            prof += 1
            mx = max(mx, prof)
        elif c in ")]}":
            prof -= 1
    return min(mx, 8)


def _simetrico(obj: str) -> bool:
    """Todas las variables aparecen el mismo numero de veces.

    Es el rasgo que en Lean predice `sq_nonneg` y la familia de desigualdades
    simetricas: `a^2+b^2 >= 2*a*b` trata a `a` y `b` igual.
    """
    v = collections.Counter(_VAR.findall(obj))
    return len(v) > 1 and len(set(v.values())) == 1


def rasgos_estado(estado: str) -> dict:
    """La estructura del estado de prueba, como diccionario de rasgos."""
    hip, obj = parte_estado(estado or "")
    f: dict[str, int] = {}

    # LA RELACION PRINCIPAL DEL OBJETIVO, en exclusiva: solo una vale.
    f["obj_rel=ninguna"] = 1
    for r in RELACIONES:
        if r in obj:
            f["obj_rel=%s" % r] = 1
            f["obj_rel=ninguna"] = 0
            break

    for r in RELACIONES:
        f["obj_%s" % r] = int(r in obj)
        f["hip_%s" % r] = int(r in hip)
    for t in TIPOS:
        f["tipo_%s" % t] = int(t in estado)
    for o in OPERADORES:
        f["op_%s" % o] = int(o in obj)
    for c in CONECTIVAS:
        f["obj_conec_%s" % c] = int(c in obj)
        f["hip_conec_%s" % c] = int(c in hip)

    lineas = [l for l in hip.split("\n") if l.strip()]
    f["n_hipotesis"] = min(len(lineas), 12)
    f["hay_hipotesis"] = int(bool(lineas))
    f["n_variables"] = min(len(set(_VAR.findall(obj))), 8)
    f["prof_max"] = _profundidad(obj)
    f["largo_obj"] = min(len(obj) // 20, 15)
    f["obj_negado"] = int(obj.strip().startswith("¬"))
    f["obj_es_falso"] = int("False" in obj)
    f["simetrico"] = int(_simetrico(obj))
    return f


class RasgosEstado(BaseEstimator, TransformerMixin):
    """Transformador de scikit-learn: lista de estados -> lista de dicts.

    Se combina con `DictVectorizer` en el `Pipeline`. Es una clase y no una
    funcion con `FunctionTransformer` a proposito: `FunctionTransformer`
    serializa la referencia a la funcion y da los mismos problemas de carga
    que se explican en la cabecera del modulo.

    HEREDA DE `BaseEstimator`, Y NO ES COSMETICO. Sin ese padre, scikit-learn
    avisa en cada uso:

        DeprecationWarning: 'RasgosEstado' object has no attribute
        '__sklearn_tags__' ... This warning will be replaced by an error
        in 1.8.

    O sea que el rankeador —la pieza que ahorra 3,7 veces las invocaciones de
    Lean— dejaria de cargar en la siguiente version mayor de la biblioteca. Un
    aviso de deprecacion con fecha es una averia programada, no ruido.
    `TransformerMixin` aporta ademas `fit_transform` gratis.
    """

    def fit(self, X, y=None):                                  # noqa: N803
        return self

    def transform(self, X):                                    # noqa: N803
        return [rasgos_estado(x) for x in X]
