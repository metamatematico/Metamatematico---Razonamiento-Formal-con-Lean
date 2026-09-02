# -*- coding: utf-8 -*-
"""Dónde está cada cosa, resuelto desde el propio paquete.

POR QUE EXISTE. Habia dos rutas ABSOLUTAS incrustadas en el runtime:

    core.py            "E:/Metamatematico/data/mathlib_modulos.json"
    llm/contador.py    "E:/Metamatematico/data/uso_llm.json"

El proyecto YA se movio una vez —de C:\\...\\metamath-prover a E:\\Metamatematico—
y las dos fallan en silencio si vuelve a pasar:

  · la primera esta dentro de un `try` cuyo `except` deja el cache en `{}`, que
    no es `None`, asi que NO SE REINTENTA NUNCA y ademas es atributo de clase.
    El grafo dejaria de elegir los modulos que importa Lean —uno de los dos
    unicos sitios donde el grafo actua en caliente— con un `logger.debug` como
    unico aviso;
  · la segunda deja de anotar el gasto, y te quedas sin saber lo que cuesta.

Las dos son de la misma familia que llevamos toda la sesion corrigiendo: la
herramienta falla y el sistema informa como si no hubiera pasado nada.
"""
from pathlib import Path

#: La raiz del repositorio, deducida de donde vive este fichero.
#: `nucleo/rutas.py` -> `nucleo/` -> la raiz.
RAIZ = Path(__file__).resolve().parent.parent

#: Donde viven los indices derivados de Mathlib y la contabilidad.
DATOS = RAIZ / "data"


def dato(nombre: str) -> Path:
    """Ruta a un fichero de `data/`. No comprueba que exista: eso lo decide
    quien lo lee, que es quien sabe si su ausencia es grave o normal."""
    return DATOS / nombre
