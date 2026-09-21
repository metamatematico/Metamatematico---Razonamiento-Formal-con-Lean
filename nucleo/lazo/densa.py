# -*- coding: utf-8 -*-
"""D1 denso: las premisas de Mathlib que un encoder entrenado acerca al estado.

EL ENCODER (§6 de la propuesta)
-------------------------------
`premise-selection` de Zhu et al. (ICLR 2026): un DistilRoBERTa entrenado para
que el estado IMPRESO por Lean —hipótesis y `⊢`, el formato de `ppGoal`, que
es el que da el REPL— quede cerca de las premisas que su prueba usó. Las
premisas ya están codificadas (`l3lab/lean-premises`, rama v4.29.0, la de
nuestra Mathlib), así que aquí sólo se codifica el estado: una pasada de un
modelo de 82 M parámetros, que en CPU tarda décimas.

El nombre de cada fila de la matriz lo da `modelos/.../premisas.jsonl`, que
escribe `scripts/alinear_premisas.py` SÓLO si comprueba que el orden casa (la
longitud y, re-codificando una muestra, el contenido). Sin ese fichero este
proponente no propone nada: una premisa mal alineada es peor que ninguna.

DE PREMISA A TÁCTICA
--------------------
El encoder da nombres, no tácticas. Cada premisa se prueba con las formas en
que una premisa entra en un paso —`exact`, `apply`, `rw`—, y al final todas
juntas en `simp [..]`. El orden es por premisa y no por forma: la primera
premisa es la que el encoder cree más útil, y su `exact` cuesta lo mismo que
el `rw` de la décima. Todo lo decide Lean; esto sólo ordena.

Sólo entran proposiciones: una definición no se `exact`-a.
"""
from __future__ import annotations

import io
import json
import os
import re
from typing import Optional

from nucleo.lazo.proponentes import Proponente

_RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODELO = os.path.join(_RAIZ, "modelos", "premise-selection")
DATOS = os.path.join(_RAIZ, "modelos", "lean-premises-v4.29.0")
EMB = os.path.join(DATOS, "embeddings",
                   "all-distilroberta-v1-lr2e-4-bs256-nneg3-ml-ne2-v4.29.0.npy")
INDICE = os.path.join(DATOS, "premisas.jsonl")

#: un nombre que se puede escribir tal cual en una táctica. Los que llevan
#: `«»`, espacios o sufijos internos (`_private`, `match_1`) se saltan.
_ESCRIBIBLE = re.compile(r"^[A-Za-z_][A-Za-z0-9_'.!?₀-₉]*$")
_INTERNO = re.compile(r"(^|\.)(_|match_|proof_|eq_\d|_private)")


def escribible(nombre: str) -> bool:
    return bool(_ESCRIBIBLE.match(nombre)) and not _INTERNO.search(nombre)


def plantillas(premisas: list) -> list:
    """Las tácticas en que entran estas premisas, por orden de premisa."""
    fuera = []
    for p in premisas:
        for t in ("exact %s" % p, "apply %s" % p, "rw [%s]" % p):
            fuera.append(t)
    if premisas:
        fuera.append("simp [%s]" % ", ".join(premisas))
    return fuera


class IndiceDenso:
    """El encoder y la matriz, cargados la primera vez que se buscan."""

    def __init__(self, modelo: str = MODELO, emb: str = EMB, indice: str = INDICE,
                 dispositivo: str = "cpu"):
        self._rutas = (modelo, emb, indice)
        self._disp = dispositivo
        self._m = self._e = self._nombres = None

    def disponible(self) -> bool:
        return all(os.path.exists(r) for r in self._rutas)

    def _carga(self):
        if self._m is not None:
            return
        import numpy as np
        from sentence_transformers import SentenceTransformer
        modelo, emb, indice = self._rutas
        filas = [json.loads(l) for l in io.open(indice, encoding="utf-8")]
        e = np.load(emb, mmap_mode="r")
        if len(filas) != e.shape[0]:
            raise ValueError("premisas.jsonl (%d) no casa con los embeddings (%d)"
                             % (len(filas), e.shape[0]))
        util = [i for i, f in enumerate(filas) if f["prop"] and escribible(f["nombre"])]
        self._e = np.ascontiguousarray(e[util])
        self._nombres = [filas[i]["nombre"] for i in util]
        self._m = SentenceTransformer(modelo, device=self._disp)

    def buscar(self, estado: str, k: int = 4) -> list:
        """[(nombre, coseno)] de las k premisas más cercanas al estado."""
        import numpy as np
        self._carga()
        q = self._m.encode([estado], normalize_embeddings=True)[0].astype(self._e.dtype)
        s = self._e @ q
        top = np.argpartition(-s, k)[:k]
        top = top[np.argsort(-s[top])]
        return [(self._nombres[i], float(s[i])) for i in top]


class D1Denso(Proponente):
    """Las premisas que el encoder acerca al objetivo, hechas tácticas."""
    nombre = "D1d"

    def __init__(self, indice: Optional[IndiceDenso] = None, k: int = 4):
        self._i = indice if indice is not None else IndiceDenso()
        self.k = k

    async def proponer(self, nodo) -> list:
        if not nodo.objetivos or not self._i.disponible():
            return []
        return plantillas([n for n, _ in self._i.buscar(nodo.objetivos[0], k=self.k)])
