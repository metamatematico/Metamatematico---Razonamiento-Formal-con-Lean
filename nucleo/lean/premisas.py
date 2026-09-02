# -*- coding: utf-8 -*-
"""Qué lemas pasarle a una táctica, cuando la táctica desnuda no basta.

EL HUECO QUE CIERRA. La cascada prueba tacticas SIN ARGUMENTOS: `simp`, `ring`,
`nlinarith`. Medido con Lean como juez sobre teoremas de una linea de Mathlib,
cierra el 16 %, y de los 21 que fallaron, OCHO usaban `simp` — que la cascada
si ofrece. Mathlib escribe `simp [foo, bar]` citando lemas, y la cascada probaba
`simp` a secas. Es decir: no podia reproducir ninguna prueba que necesitara
citar un hecho.

DE DONDE SALEN LAS PREMISAS. De `data/indice_premisas.json`, destilado de las
citas reales de 46 880 teoremas de Mathlib. Dos fuentes que aciertan cosas
distintas y por eso se combinan:

    prior      los lemas mas citados DEL AREA, sin mirar el objetivo. Pone las
               herramientas universales — `mul_comm`, `le_antisymm`.
    contenido  solapamiento lexico entre el objetivo y el texto del lema. Pone
               las especificas — `dist_eq_norm_vsub` para algo con distancias.

QUE SE EXCLUYE, y es lo que hizo que esto funcionara: los lemas `@[simp]`.
Medido, el 42,1 % de las premisas citadas ya llevan esa etiqueta, y `simp` las
conoce sin que nadie se las pase. Filtrarlas hizo pasar al hibrido de empatar
con el prior (9,4 % vs 9,2 %) a superarlo (14,0 % vs 11,7 %).

LA ESTRATEGIA ES POR AREA, no global, y tambien esta medida. En categorias el
contenido saca 0,0 % —sus enunciados son diagramas, no palabras— y mezclarlo
EMPEORA respecto al prior solo; ahi el indice dice `nulo` y se respeta.

NADA DE ESTO AFECTA A LA CORRECCION. Una premisa mal elegida hace que la
tactica falle y se pase a la siguiente; Lean sigue siendo quien decide.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Optional

logger = logging.getLogger(__name__)

#: Se carga una vez y se reutiliza. `None` = aun no intentado.
_INDICE: Optional[dict] = None
_INVERTIDO: Optional[dict] = None

_TOKEN = re.compile(r"[A-Za-z]{3,}")


def _cargar() -> dict:
    global _INDICE
    if _INDICE is None:
        from nucleo.rutas import dato
        ruta = dato("indice_premisas.json")
        try:
            with open(ruta, encoding="utf-8") as fh:
                _INDICE = json.load(fh)
            logger.debug("indice de premisas: %d en catalogo",
                         len(_INDICE.get("catalogo", ())))
        except Exception as e:
            # Sin indice el sistema funciona igual, solo que sin premisas. Se
            # avisa en WARNING y no en debug: es una degradacion silenciosa de
            # las que este proyecto lleva toda la sesion cazando.
            _INDICE = {}
            logger.warning(
                "SIN INDICE DE PREMISAS (%s): %s. La cascada probara solo "
                "tacticas desnudas. Regenerar con: "
                "python scripts/construir_indice_premisas.py",
                type(e).__name__, ruta)
    return _INDICE


def _invertido() -> dict:
    """token -> posiciones del catalogo. Se construye una vez, es pequeño."""
    global _INVERTIDO
    if _INVERTIDO is None:
        idx = _cargar()
        inv: dict[str, list[int]] = {}
        for i, e in enumerate(idx.get("catalogo", ())):
            for t in set(_TOKEN.findall(e["t"].lower())):
                inv.setdefault(t, []).append(i)
        _INVERTIDO = inv
    return _INVERTIDO


def _por_contenido(objetivo: str, k: int) -> list[str]:
    """Los lemas del catalogo que mas comparten vocabulario con el objetivo."""
    idx = _cargar()
    cat = idx.get("catalogo") or []
    if not cat:
        return []
    inv = _invertido()
    puntos: dict[int, int] = {}
    for t in set(_TOKEN.findall(objetivo.lower())):
        for i in inv.get(t, ()):
            puntos[i] = puntos.get(i, 0) + 1
    if not puntos:
        return []
    mejores = sorted(puntos, key=lambda i: -puntos[i])[:k]
    return [cat[i]["n"] for i in mejores]


def premisas_para(objetivo: str, area: str = "", k: int = 8) -> list[str]:
    """Los lemas a citar para este objetivo, segun la estrategia de su area.

    Devuelve lista vacia si no hay indice — y entonces la cascada se comporta
    exactamente como antes, probando tacticas desnudas.
    """
    idx = _cargar()
    if not idx:
        return []
    prior = idx.get("por_area", {}).get(area) or idx.get("global") or []
    estrategia = (idx.get("estrategia") or {}).get(area, "hibrido")

    if estrategia == "nulo":
        return list(prior[:k])
    if estrategia == "lexico":
        return _por_contenido(objetivo, k)

    # hibrido: mitad y mitad, sin repetir. Y si una mitad no llena su parte,
    # la otra la completa — reservar plazas para el contenido y dejarlas
    # VACIAS cuando no encuentra nada seria peor que no reservarlas: ante
    # `a * b = b * a` el contenido no casa con ningun lema del catalogo y se
    # devolvian 4 premisas en vez de 8, tirando la mitad del presupuesto.
    mitad = max(1, k // 2)
    fuera = list(prior[:mitad])
    for n in _por_contenido(objetivo, k):
        if n not in fuera:
            fuera.append(n)
        if len(fuera) >= k:
            break
    for n in prior[mitad:]:
        if len(fuera) >= k:
            break
        if n not in fuera:
            fuera.append(n)
    return fuera[:k]


#: Que tacticas admiten una lista de lemas entre corchetes. `ring` y `omega` no
#: la admiten, asi que no se les ofrece.
_ADMITEN_PREMISAS = ("simp", "nlinarith", "linarith", "aesop", "field_simp")


def tacticas_con_premisas(objetivo: str, area: str = "", k: int = 8,
                          tacticas=_ADMITEN_PREMISAS) -> list[tuple[str, int]]:
    """(tactica con sus premisas, timeout), para añadir al final de la cascada.

    Van AL FINAL a proposito: son mas caras —el termino es mas largo y la
    tactica tiene mas que mirar— y solo tienen sentido cuando la version
    desnuda ya fallo. Si la desnuda cierra, esto no llega a probarse.
    """
    ps = premisas_para(objetivo, area, k)
    if not ps:
        return []
    lista = ", ".join(ps)
    # `simp` admite muchas; a las aritmeticas se les dan menos, que su termino
    # crece rapido y el timeout es corto.
    cortas = ", ".join(ps[:4])
    fuera = []
    for t in tacticas:
        arg = lista if t in ("simp", "aesop", "field_simp") else cortas
        fuera.append(("%s [%s]" % (t, arg), 6 if t == "aesop" else 4))
    return fuera
