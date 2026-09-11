# -*- coding: utf-8 -*-
"""Que modulos de Mathlib alcanza una cabecera de `import`.

POR QUE HACE FALTA
------------------
El sistema NO usa `import Mathlib`: cargarlo entero tarda 742 s y siempre
expira, asi que `_normalize_code` lo borra y deja una cabecera estrecha. Bajo
una cabecera estrecha, un lema PERFECTAMENTE REAL da «unknown constant».

Eso paso en produccion con este caso, que es el que motivo este modulo:

    import Mathlib.Tactic.Ring          -- y otros seis modulos
    ...
    obtain @$\\langle$@s, b@$\\rangle$@ := Module.Basis.exists_basis K V

`Module.Basis.exists_basis` existe, el indice sabe que vive en
`Mathlib.LinearAlgebra.Basis.VectorSpace`, y la cabecera alcanzaba 773 de los
7 747 modulos de Mathlib — ninguno de ellos ese. El nombre estaba BIEN; lo que
faltaba era el import.

QUE NO SE PUEDE HACER: anadir el modulo de cada nombre sin mirar. Cada import
cuesta elaboracion, y la mayoria ya vienen por transitividad —
`Mathlib.Tactic` arrastra 2 972 modulos el solo—. Hay que saber que alcanza ya
la cabecera, y eso es exactamente lo que este modulo responde.

EL DATO. `data/mathlib_imports.dot` lo genera la herramienta que trae Mathlib
en `.lake/packages/importGraph`, asi que no hay que reconstruir nada. Cuidado
con el sentido de las aristas: en ese fichero

    "A" -> "B"    significa    B importa a A

es decir, la arista va del importado al importador, o del prerrequisito al
dependiente. Para saber que alcanza B hay que seguirlas al reves.
"""
from __future__ import annotations

import io
import pathlib
import re
from collections import deque
from typing import Iterable, Optional

#: dep[modulo] = modulos que ESE modulo importa directamente.
_DEP: Optional[dict] = None
_TODOS: set = set()

_ARISTA = re.compile(r'"([^"]+)"\s*->\s*"([^"]+)"')

#: Si una cabecera trae esto, alcanza Mathlib entero y no hay nada que anadir.
_AMPLIOS = frozenset({"Mathlib"})


def _ruta() -> pathlib.Path:
    return (pathlib.Path(__file__).resolve().parent.parent.parent
            / "data" / "mathlib_imports.dot")


def _cargar() -> None:
    global _DEP, _TODOS
    if _DEP is not None:
        return
    _DEP, _TODOS = {}, set()
    p = _ruta()
    if not p.exists():
        return
    try:
        with io.open(p, encoding="utf-8") as f:
            for linea in f:
                m = _ARISTA.search(linea)
                if not m:
                    continue
                a, b = m.group(1), m.group(2)
                _DEP.setdefault(b, []).append(a)
                _TODOS.add(a)
                _TODOS.add(b)
    except OSError:
        _DEP, _TODOS = {}, set()


def disponible() -> bool:
    """Sin el DAG no se puede decidir, y adivinar seria peor que no hacer nada."""
    _cargar()
    return bool(_DEP)


def cuantos() -> int:
    _cargar()
    return len(_TODOS)


def alcanza(cabecera: Iterable[str]) -> set:
    """Modulos que la cabecera importa, directa o transitivamente.

    Incluye los de la propia cabecera. Devuelve conjunto vacio si no hay DAG,
    que quien llame debe leer como «no se sabe», no como «no alcanza nada».
    """
    _cargar()
    if not _DEP:
        return set()
    inicio = [m for m in cabecera if m]
    vistos, cola = set(inicio), deque(inicio)
    while cola:
        x = cola.popleft()
        for d in _DEP.get(x, ()):
            if d not in vistos:
                vistos.add(d)
                cola.append(d)
    return vistos


def es_amplia(cabecera: Iterable[str]) -> bool:
    """`import Mathlib` a secas: lo alcanza todo, no hay nada que completar."""
    return any(m in _AMPLIOS for m in cabecera)


def faltan_para(cabecera: Iterable[str], modulos: Iterable[str],
                tope: int = 6) -> list:
    """Los de `modulos` que la cabecera NO alcanza ya, en orden y sin repetir.

    `tope` acota el coste: cada import se elabora, y una consulta que mencione
    quince lemas de quince ficheros distintos no debe convertirse en quince
    imports. Se devuelven los primeros, que son los del enunciado.
    """
    cab = list(cabecera)
    if es_amplia(cab):
        return []
    ya = alcanza(cab)
    if not ya:
        return []
    fuera, vistos = [], set(cab)
    for m in modulos:
        if not m or m in ya or m in vistos:
            continue
        vistos.add(m)
        fuera.append(m)
        if len(fuera) >= tope:
            break
    return fuera
