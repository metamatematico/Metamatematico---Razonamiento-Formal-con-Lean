# -*- coding: utf-8 -*-
"""Graba lo que el LLM escribió, para no volver a pagarlo nunca.

EL PROBLEMA QUE RESUELVE. Cada pregunta importante sobre este sistema cuesta
API, y por eso la mas importante lleva dias sin respuesta. Todo lo que se ha
medido —el DAG, el orden de tacticas, las premisas, los imports— se midio
contra sustitutos, porque el bucle real esta tarifado.

LA SALIDA ES GRABAR. El modelo formaliza una consulta UNA VEZ; esa
formalizacion se guarda; y a partir de ahi cualquier cambio en imports,
tacticas o premisas se vuelve a probar contra la grabacion, con Lean de juez y
COSTE CERO. Una medicion de $1,90 pasa a correr cuantas veces haga falta.

QUE SE GRABA, y por que exactamente eso:

    consulta      el texto original, para poder repetir el emparejamiento
    codigo        lo que el LLM escribio, ANTES de normalizar. Es la frontera:
                  todo lo que viene despues —imports, tacticas, premisas— es
                  del sistema y se puede volver a ejecutar
    area          la que clasifico el sistema entonces
    skills        las que activo, para detectar si el emparejamiento cambia
    config        con que configuracion se genero. Sin esto no se puede
                  comparar «con vocabulario» contra «sin vocabulario», que es
                  justo la pregunta que sigue abierta
    veredicto     lo que Lean dijo aquella vez, como referencia

LO QUE NO PUEDE MEDIR, y hay que decirlo: si un prompt distinto habria hecho
que el LLM escribiera codigo mejor. Eso sigue necesitando API. Pero grabando
UNA vez con cada configuracion, la comparacion queda hecha para siempre.

La grabacion se activa con la variable de entorno METAMAT_GRABAR=1, o llamando
a `activar()`. Apagada por defecto: no debe cambiar el comportamiento de nadie
que no la pida.
"""
from __future__ import annotations

import json
import logging
import os
import time
from typing import Optional

logger = logging.getLogger(__name__)

_ACTIVA: Optional[bool] = None
_CONFIG = "completo"


def activa() -> bool:
    """¿Hay que grabar? Se decide una vez y se recuerda."""
    global _ACTIVA
    if _ACTIVA is None:
        _ACTIVA = os.environ.get("METAMAT_GRABAR", "").strip() in ("1", "true", "si")
    return _ACTIVA


def activar(config: str = "completo") -> None:
    """Enciende la grabación y etiqueta con qué configuración se está corriendo.

    La etiqueta importa: una grabación hecha sin el vocabulario del grafo y otra
    hecha con él son dos corpus distintos, y compararlos es la pregunta que
    lleva días abierta.
    """
    global _ACTIVA, _CONFIG
    _ACTIVA = True
    _CONFIG = config


def _ruta():
    from nucleo.rutas import dato
    d = dato("grabaciones")
    os.makedirs(d, exist_ok=True)
    return d / "formalizaciones.jsonl"


def grabar(consulta: str, codigo: str, area: str = "",
           skills=(), veredicto: str = "", modelo: str = "",
           extra: Optional[dict] = None) -> None:
    """Anota una formalización. Nunca lanza: grabar no puede romper una respuesta."""
    if not activa() or not codigo or not codigo.strip():
        return
    try:
        fila = {
            "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "config": _CONFIG,
            "consulta": consulta[:1000],
            "codigo": codigo,
            "area": area,
            "skills": list(skills)[:10],
            "veredicto": veredicto,
            "modelo": modelo,
        }
        if extra:
            fila.update(extra)
        with open(_ruta(), "a", encoding="utf-8") as fh:
            fh.write(json.dumps(fila, ensure_ascii=False) + "\n")
    except Exception as e:
        # Deliberadamente silencioso a nivel de WARNING y no mas: si grabar
        # falla, la respuesta al usuario debe salir igual. Pero se avisa, que
        # es la diferencia entre degradarse y degradarse a escondidas.
        logger.warning("no se pudo grabar la formalizacion: %s", type(e).__name__)


def cargar(ruta=None) -> list:
    """Las grabaciones que haya. Lista vacía si no hay ninguna."""
    p = ruta or _ruta()
    if not os.path.exists(p):
        return []
    fuera = []
    with open(p, encoding="utf-8") as fh:
        for l in fh:
            l = l.strip()
            if l:
                try:
                    fuera.append(json.loads(l))
                except Exception:
                    continue
    return fuera
