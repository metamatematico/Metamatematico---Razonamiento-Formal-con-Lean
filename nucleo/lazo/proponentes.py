# -*- coding: utf-8 -*-
"""Quién propone tácticas para un estado, de más barato a más caro.

    D0 · la cascada     las tácticas de `SolverCascade.orden_para`, UNA A UNA.
                        No el bloque `first | …`: en modo táctica el REPL no
                        aplica el límite de heartbeats y el bloque entero se
                        agotaba a los 120 s sobre `n * n ≠ 2`, mientras cada
                        táctica suelta tarda menos de 3 s (medido al empezar el
                        paso 3). Y sueltas tienen otra ventaja: una que
                        PROGRESA sin cerrar es una flecha nueva de E, que el
                        bloque tiraba.
    D3 · el modelo      k tácticas con la retroalimentación del estado. Es el
                        único que gasta una llamada, así que va el último y sólo
                        si el estado sigue abierto.
    Guionado            tácticas fijas por subcadena del objetivo. Sirve para
                        probar el mediador contra Lean SIN gastar API: la
                        mecánica —estados, confluencias, ensamblado, I2— se
                        verifica aparte del modelo.

Del paso 4 entró D1v, los vecinos de estado. D2 (`apply?` leyendo su «Try
this») y D1 denso (un encoder de premisas) se midieron, no batieron a su
nulo y se quitaron.
"""
from __future__ import annotations

import logging
import re
from typing import Callable, Optional

from nucleo.lazo import retro as _retro

logger = logging.getLogger(__name__)

#: identificadores con aspecto de lema: los que merece la pena buscarle firma
_IDENT = re.compile(r"(?<![\w.'])([A-Za-z_][\w']*(?:\.[\w']+)*)")


class Proponente:
    nombre = "?"
    #: «local» no gasta nada fuera de Lean; «llamada» gasta una llamada al modelo
    coste = "local"

    async def proponer(self, nodo) -> list:
        raise NotImplementedError


class D0Cascada(Proponente):
    """Las tácticas de la cascada, en el orden que el sistema ya mide."""
    nombre = "D0"

    def __init__(self, cascada, domain_order=None, area_premisas: str = ""):
        self._c = cascada
        self._orden = domain_order
        self._area = area_premisas

    async def proponer(self, nodo) -> list:
        orden = self._c.orden_para(nodo.objetivos[0] if nodo.objetivos else "",
                                   domain_order=self._orden,
                                   area_premisas=self._area)
        return [t for t, _ in orden]


class Guionado(Proponente):
    """Tácticas fijas por subcadena del objetivo principal. Para bancos sin API."""
    nombre = "guion"

    def __init__(self, guion: dict, siempre: Optional[list] = None):
        self._g = guion
        self._siempre = list(siempre or [])

    async def proponer(self, nodo) -> list:
        obj = nodo.objetivos[0] if nodo.objetivos else ""
        fuera = [t for clave, ts in self._g.items() if clave in obj for t in ts]
        return fuera + self._siempre


class D3Modelo(Proponente):
    """El modelo, con la retroalimentación del estado. Gasta una llamada."""
    nombre = "D3"
    coste = "llamada"

    def __init__(self, llm, k: int = 4, campos=_retro.CAMPOS,
                 firmas_de: Optional[Callable] = None,
                 ranker_de: Optional[Callable] = None):
        self._llm = llm
        self.k = k
        self.campos = campos
        self._firmas_de = firmas_de
        self._ranker_de = ranker_de
        self.llamadas = 0
        #: lo que el modelo contestó, crudo, por si hay que auditar una ronda
        self.respuestas: list = []

    def _firmas(self, nodo) -> dict:
        """La firma real de cada nombre que ya falló aquí: la FORMA, no el nombre."""
        if not self._firmas_de:
            return {}
        nombres = set()
        for f in nodo.fallos:
            if f.get("clase") in ("nombre", "forma", "fallo"):
                for n in _IDENT.findall(f.get("tactica") or ""):
                    if "_" in n or "." in n:
                        nombres.add(n)
        try:
            return dict(list(self._firmas_de(nombres).items())[:8]) if nombres else {}
        except Exception as e:                                 # noqa: BLE001
            logger.debug("sin firmas (%s)", e)
            return {}

    async def proponer(self, nodo) -> list:
        ranker = None
        if self._ranker_de and nodo.objetivos:
            try:
                ranker = self._ranker_de(nodo.objetivos[0])
            except Exception:                                  # noqa: BLE001
                ranker = None
        r = _retro.construir(nodo, k=self.k, firmas=self._firmas(nodo),
                             ranker=ranker, campos=self.campos)
        self.llamadas += 1
        resp = await self._llm.generate(_retro.prompt(r), system=_retro.SISTEMA,
                                        sin_historial=True)
        texto = getattr(resp, "content", "") or ""
        self.respuestas.append({"nodo": nodo.id, "texto": texto[:2000]})
        return _retro.leer(texto, k=self.k)


class D1Vecinos(Proponente):
    """Las tácticas enteras que cerraron estados parecidos (`vecinos.py`)."""
    nombre = "D1v"

    def __init__(self, indice, k: int = 5):
        self._i = indice
        self.k = k

    async def proponer(self, nodo) -> list:
        if self._i is None or not nodo.objetivos:
            return []
        return self._i.proponer(nodo.objetivos[0], k=self.k)
