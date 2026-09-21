# -*- coding: utf-8 -*-
"""Vecinos de estado: la táctica entera que cerró un estado parecido.

POR QUÉ, SI YA HAY UN RANKEADOR
-------------------------------
El rankeador (`TacticRanker`) ordena NOMBRES: dice «prueba `nlinarith`». Lo que
cierra una desigualdad de competición casi nunca es el nombre desnudo: es
`nlinarith [sq_nonneg (a - b), sq_nonneg (a + b)]`, con los hechos que hay que
citarle. Esos argumentos no los puede inventar un clasificador de nombres, pero
están escritos en las 25 214 transiciones de LeanWorkbook: basta encontrar el
estado más parecido y copiar lo que lo cerró.

QUÉ DEVUELVE
------------
Tácticas completas, ordenadas por la similitud del estado de donde salieron,
sin repetir. El que decide si sirven es Lean: esto sólo propone (I1).

EL SESGO, DECLARADO (§6 de la propuesta)
----------------------------------------
LeanWorkbook es matemática de competición: 81 % de pruebas hacia delante y
ningún caso de inducción. Los vecinos heredan eso. Sirven para desigualdades y
álgebra elemental; fuera de ahí propondrán tácticas de desigualdad a objetivos
que no lo son, y Lean las rechazará en centésimas de segundo.

EL ÍNDICE SE CONSTRUYE SÓLO CON LO QUE SE PUEDE VER
---------------------------------------------------
`construir` recibe los pares que se le den. El banco le da la partición de
ENTRENAMIENTO del rankeador —misma semilla, misma estratificación—, así que
ningún estado de prueba está en su propio índice.
"""
from __future__ import annotations

import logging
import pickle
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class IndiceDeVecinos:
    """(estado, táctica) indexados por n-gramas de caracteres del estado."""

    def __init__(self):
        self._vec = None
        self._matriz = None
        self._tacticas: list = []

    @property
    def disponible(self) -> bool:
        return self._matriz is not None and bool(self._tacticas)

    def construir(self, estados, tacticas) -> "IndiceDeVecinos":
        from sklearn.feature_extraction.text import TfidfVectorizer
        # los mismos n-gramas que el rankeador (char_wb 1-4): ven los símbolos
        # —`^ 2`, `√`, `∑`— que distinguen una desigualdad de otra
        self._vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(1, 4),
                                    min_df=2, sublinear_tf=True)
        self._matriz = self._vec.fit_transform(list(estados))
        self._tacticas = [t.strip() for t in tacticas]
        return self

    def proponer(self, estado: str, k: int = 5, vecinos: int = 40) -> list:
        """Las k tácticas distintas de los estados más parecidos, en su orden."""
        if not self.disponible or not estado:
            return []
        q = self._vec.transform([estado])
        sims = (self._matriz @ q.T).toarray().ravel()
        orden = sims.argsort()[::-1][:vecinos]
        fuera, vistos = [], set()
        for i in orden:
            t = self._tacticas[i]
            # una táctica por línea: es lo que el lazo sabe ensamblar
            if not t or "\n" in t or t in vistos:
                continue
            vistos.add(t)
            fuera.append(t)
            if len(fuera) >= k:
                break
        return fuera

    def guardar(self, ruta) -> None:
        with open(ruta, "wb") as fh:
            pickle.dump({"vec": self._vec, "matriz": self._matriz,
                         "tacticas": self._tacticas}, fh)

    @classmethod
    def cargar(cls, ruta) -> Optional["IndiceDeVecinos"]:
        try:
            with open(ruta, "rb") as fh:
                d = pickle.load(fh)
        except Exception as e:                                 # noqa: BLE001
            logger.debug("sin índice de vecinos (%s)", e)
            return None
        i = cls()
        i._vec, i._matriz, i._tacticas = d["vec"], d["matriz"], d["tacticas"]
        return i
