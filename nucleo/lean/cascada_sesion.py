# -*- coding: utf-8 -*-
"""La cascada por estado: D0 dentro de la sesión de Lean (paso 2 del lazo).

QUE CAMBIA RESPECTO A HOY
-------------------------
Hoy `SolverCascade._cascada_de_un_tiro` mete las tácticas en un solo
`first | (t ; done ; trace …) | …` y COMPILA UN FICHERO POR CADA SORRY:
~15,5 s cada uno, cierre o no.

Aquí el mismo bloque, con el mismo orden, se elabora en una sesión de Lean que
vive entre consultas: sin arrancar Lean ni cargar la cabecera cada vez.

DOS MODOS, Y EL SERVIDO ES EL DE COMANDO
----------------------------------------
    `cerrar_sorries`             el bloque como TÁCTICA sobre el proofState
    `cerrar_sorries_por_comando` el teorema con el bloque en el sitio del sorry,
                                 elaborado como COMANDO

El primero es el que el lazo por pasos necesitará (paso 3), pero el REPL no
le aplica el límite de heartbeats: sobre `n * n ≠ 2` se agotó a los 120 s. El
segundo se elabora como un fichero, con su límite, y el mismo caso falla en
5,5 s. `resolver`, que es lo que llama el núcleo, usa el de comando.

QUE NO CAMBIA, Y ES EL INVARIANTE I2
------------------------------------
**La sesión busca; el fichero decide.** Que la sesión diga «cierra» no es un
veredicto: `ensamblar` escribe la prueba con la táctica GANADORA en el sitio de
cada sorry, y quien la da por buena es `LeanClient.check_code` sobre ese
fichero, igual que hoy. La puerta del paso 1 midió 20 de 20 de acuerdo, pero
el REPL tiene registrado un caso en que aceptó pruebas incorrectas (issue 44),
y un buscador que se equivoca cuesta un camino perdido, no un sello falso.

POR QUE LA GANADORA SOLA Y NO EL BLOQUE
---------------------------------------
Porque es lo que el lazo escribe —«cada sorry sustituido por su camino»— y
porque el bloque entero comparte un presupuesto de heartbeats por declaración:
un `exact?` caro que falla puede dejar sin presupuesto a la táctica que habría
cerrado. La ganadora sola no carga con las ramas que perdieron.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Optional

from nucleo.lean.solver_cascade import _ADMITEN_CON_SORRY, _MARCA, _bloque_first

logger = logging.getLogger(__name__)


def _avisos_sorry(respuesta) -> int:
    """Cuántos «declaration uses 'sorry'» trae una respuesta del REPL."""
    return sum(1 for m in respuesta.mensajes or []
               if "declaration uses 'sorry'" in str((m or {}).get("data") or ""))


@dataclass
class CierrePorEstado:
    """Lo que pasó con UN sorry en la sesión."""
    motivo: str                    # cierra · sin_marca · no_cierra · agotada
    ganadora: str = ""
    linea: Optional[int] = None    # posición del sorry en el código enviado
    columna: Optional[int] = None
    segundos: float = 0.0
    error: str = ""
    #: el bloque que se probó en ESTE sorry; es lo que se escribe si cerró
    #: sin marca, porque entonces no se sabe qué rama ganó
    bloque: str = ""

    @property
    def cerrado(self) -> bool:
        return self.motivo in ("cierra", "sin_marca")


def ganadora_de(mensajes) -> str:
    """La táctica que ganó el `first |`, por la marca que su rama imprime.

    De `data` y no de buscar en el texto crudo, por la razón que
    `_cascada_de_un_tiro` documenta: partir la salida por la marca devolvía
    trozos de JSON como nombre de táctica.
    """
    for m in mensajes or []:
        txt = str((m or {}).get("data") or "")
        if txt.startswith(_MARCA):
            return txt[len(_MARCA):].strip()
    return ""


def cerrar_sorries(sesion, codigo: str, orden, env=None,
                   tope: Optional[int] = None) -> tuple[list, str]:
    """Aplica el bloque de la cascada a cada sorry del código.

    Devuelve (cierres, error_de_elaboracion). Si el código no elabora, la
    lista va vacía y el error explica por qué: es el invariante I5, un
    enunciado que no elabora no se busca, vuelve al formalizador.
    """
    r = sesion.comando(codigo, env=env)
    if r.clase == "error":
        return [], r.error or "no elabora"
    cierres = []
    for s in r.sorries:
        pos = s.get("pos") or {}
        kw = {} if tope is None else {"tope": tope}
        # `orden` puede ser el bloque ya hecho, la lista de tácticas, o una
        # función del OBJETIVO: la sesión da el objetivo exacto de cada sorry,
        # que es mejor base para ordenar que el texto de la declaración.
        o = orden(s.get("goal") or "") if callable(orden) else orden
        bloque = o if isinstance(o, str) else _bloque_first(o)
        t = sesion.tactica(bloque, s["proofState"], **kw)
        if t.clase == "cierra":
            g = ganadora_de(t.mensajes)
            c = CierrePorEstado("cierra" if g else "sin_marca", ganadora=g)
        elif "TIMEOUT" in t.error:
            # la sesión queda inservible tras un timeout: ver SesionLean._pide
            c = CierrePorEstado("agotada", error=t.error)
        else:
            c = CierrePorEstado("no_cierra", error=t.error)
        c.linea, c.columna, c.segundos = pos.get("line"), pos.get("column"), t.segundos
        c.bloque = bloque
        cierres.append(c)
        if c.motivo == "agotada":
            break
    return cierres, ""


_SORRY = re.compile(r"\bsorry\b")


def ensamblar(codigo: str, cierres, bloque: str = "",
              parcial: bool = False) -> Optional[str]:
    """El código con cada sorry sustituido por la táctica que lo cerró.

    None si algún sorry no se cerró: una prueba parcial no se manda a
    verificar como si fuera entera. Con `parcial=True` los que no cerraron se
    quedan como `sorry` —así el fichero confirma los cerrados y sigue diciendo
    SORRY por los demás—, y hace falta al menos uno cerrado.

    Si la sesión cerró sin marca —no se sabe qué rama ganó— se escribe el
    bloque entero, que es lo que cerró.

    La posición la da el REPL (línea 1-indexada, columna 0-indexada) y se
    comprueba que ahí haya de verdad un `sorry`: si no casa, None, en vez de
    sustituir otra cosa.
    """
    if not cierres or not any(c.cerrado for c in cierres):
        return None
    if not parcial and not all(c.cerrado for c in cierres):
        return None
    lineas = codigo.split("\n")
    # de atrás hacia delante, para que sustituir no mueva las posiciones
    for c in sorted((c for c in cierres if c.cerrado),
                    key=lambda c: (c.linea or 0, c.columna or 0), reverse=True):
        tac = c.ganadora or c.bloque or bloque
        if not tac or not _sustituye(lineas, c.linea, c.columna, tac):
            return None
    return "\n".join(lineas)


def _sustituye(lineas: list, linea, columna, tac: str) -> bool:
    """Cambia el `sorry` de (línea, columna) por `tac`, EN SITIO. False si ahí
    no hay un `sorry`: no se sustituye otra cosa."""
    if linea is None or columna is None or not (1 <= linea <= len(lineas)):
        return False
    l = lineas[linea - 1]
    if not _SORRY.match(l, columna):
        return False
    antes = l[:columna].rstrip()
    # `:= sorry` es un TÉRMINO; en modo táctica `sorry` es una táctica.
    # `=>` NO entra: en `induction … with | zero => sorry` es táctica, y
    # envolverla en `(by …)` la rompería. Si el modo se adivina mal, lo que
    # pasa es que el fichero la rechaza: se pierde un cierre, no se inventa.
    if antes.endswith(":=") or antes.endswith("("):
        tac = "(by %s)" % tac
    lineas[linea - 1] = l[:columna] + tac + l[columna + len("sorry"):]
    return True


def cerrar_sorries_por_comando(sesion, codigo: str, orden, env=None,
                               tope: Optional[int] = None) -> tuple[list, str]:
    """Lo mismo que `cerrar_sorries`, pero elaborando COMANDOS, no tácticas.

    POR QUE ESTE Y NO EL OTRO EN EL CAMINO SERVIDO. En modo táctica el REPL no
    aplica el límite de heartbeats: sobre `n * n ≠ 2` el bloque se agotó a los
    120 s —y `set_option maxHeartbeats … in` no lo corta—, mientras el mismo
    bloque en fichero falla en 16,6 s. En modo comando el teorema se elabora
    como en un fichero, con su límite, pero sin arrancar Lean ni cargar la
    cabecera: el mismo caso falla en 5,5 s. Medido el 2026-09-21.

    Se elabora una vez con los `sorry` para saber dónde están (y que elabora:
    invariante I5); después, por cada sorry, el código con ESE sorry cambiado
    por el bloque y los demás intactos. Cierra si no hay ningún error; qué rama
    ganó lo dice la marca.
    """
    r0 = sesion.comando(codigo, env=env)
    if r0.clase == "error":
        return [], r0.error or "no elabora"
    cierres = []
    for s in r0.sorries:
        pos = s.get("pos") or {}
        o = orden(s.get("goal") or "") if callable(orden) else orden
        bloque = o if isinstance(o, str) else _bloque_first(o)
        lineas = codigo.split("\n")
        if not _sustituye(lineas, pos.get("line"), pos.get("column"), bloque):
            c = CierrePorEstado("no_cierra", error="la posición no es un sorry")
        else:
            t = sesion.comando("\n".join(lineas), env=env)
            if "TIMEOUT" in t.error:
                c = CierrePorEstado("agotada", error=t.error)
            elif t.clase == "error":
                c = CierrePorEstado("no_cierra", error=t.error)
            else:
                g = ganadora_de(t.mensajes)
                if g in _ADMITEN_CON_SORRY and _avisos_sorry(t) >= _avisos_sorry(r0):
                    # `apply?` «ganó» admitiendo el objetivo con sorry: el
                    # aviso sigue ahí. No es un cierre; sin esto cada fallo
                    # duro costaría un compilado de confirmación para nada.
                    c = CierrePorEstado("no_cierra", error="%s admitió con sorry" % g)
                else:
                    c = CierrePorEstado("cierra" if g else "sin_marca", ganadora=g)
            c.segundos = t.segundos
        c.linea, c.columna, c.bloque = pos.get("line"), pos.get("column"), bloque
        cierres.append(c)
        if c.motivo == "agotada":
            break
    return cierres, ""


# ═══════════════════════════════════════════════════════════════════════════
# EN EL CAMINO SERVIDO
# ═══════════════════════════════════════════════════════════════════════════
def partir(codigo: str) -> tuple[str, str, list]:
    """(cabecera, cuerpo, líneas de cabecera): los `import` del principio.

    La cabecera va a la sesión UNA vez por texto distinto; el cuerpo se
    elabora contra ella. Misma cabecera, misma biblioteca: la sesión nunca ve
    más que el fichero (ver `scripts/sesion_contra_fichero.py`).
    """
    lineas = codigo.split("\n")
    i = 0
    while i < len(lineas) and (lineas[i].strip().startswith("import ")
                               or not lineas[i].strip()):
        i += 1
    cab = "\n".join(l.strip() for l in lineas[:i] if l.strip())
    return cab, "\n".join(lineas[i:]), lineas[:i]


class SesionCompartida:
    """Una sesión viva ENTRE consultas, con sus cabeceras ya cargadas.

    Es donde está la ganancia: la cabecera estrecha es casi siempre la misma,
    así que se paga una vez por proceso y no una por sorry. Tiene un cerrojo
    porque la interfaz web puede atender dos consultas a la vez, y el REPL es
    un solo canal de entrada y salida.

    Cuántas cabeceras vivas: pocas. Cada entorno con Mathlib ocupa memoria en
    el MISMO proceso, y el banco del paso 1 llegó a 12,4 GB y tumbó la
    máquina por no reiniciar. Al pasar del tope, se reinicia.
    """

    def __init__(self, max_cabeceras: int = 3):
        import threading
        self.cerrojo = threading.Lock()
        self.sesion = None
        self.entornos: dict = {}
        self.max_cabeceras = max_cabeceras

    @property
    def viva(self) -> bool:
        return self.sesion is not None and self.sesion.viva

    def abrir(self) -> None:
        from nucleo.lean.sesion import SesionLean
        self.cerrar()
        self.sesion = SesionLean().abrir()
        self.entornos = {}

    def cerrar(self) -> None:
        if self.sesion is not None:
            try:
                self.sesion.cerrar()
            except Exception:                                  # noqa: BLE001
                pass
        self.sesion, self.entornos = None, {}

    def entorno(self, cabecera: str):
        if cabecera not in self.entornos:
            if len(self.entornos) >= self.max_cabeceras:
                self.abrir()
            env = self.sesion.comando(cabecera, env=None).env
            if env is None:
                return None
            self.entornos[cabecera] = env
        return self.entornos[cabecera]


_COMPARTIDA: Optional[SesionCompartida] = None


def compartida() -> SesionCompartida:
    global _COMPARTIDA
    if _COMPARTIDA is None:
        _COMPARTIDA = SesionCompartida()
    return _COMPARTIDA


async def resolver(codigo: str, cliente, orden_de) -> Optional[dict]:
    """La cascada por estado sobre todos los sorries de `codigo`.

    Devuelve {cerrados, total, ganadoras} o None. **None no es «no cierra»:
    es «la sesión no pudo decirlo»** —no hay REPL, no elabora en la sesión,
    una táctica agotó el tiempo, o el fichero no confirmó lo que la sesión
    cerró—, y entonces el llamante hace lo de siempre: la cascada en fichero.

    El texto es el que `check_code` compilaría —normalizado—, para que la
    sesión vea la misma cabecera que el fichero. Todo cierre lo confirma el
    fichero antes de contar (invariante I2); los que no cierran no necesitan
    compilado, y ése es el ahorro: 22,7 s frente a 223 s en los 18 fallos del
    banco (`data/cascada_por_estado.json`).
    """
    from nucleo.lean.client import LeanResultStatus
    texto = cliente._normalize_code(codigo)
    cab, cuerpo, lineas_cab = partir(texto)
    comp = compartida()
    with comp.cerrojo:
        try:
            if not comp.viva:
                comp.abrir()
            env = comp.entorno(cab)
            if env is None:
                return None
            # MODO COMANDO: el modo táctica no respeta el límite de heartbeats
            # y se agota en los fallos duros (ver cerrar_sorries_por_comando)
            cierres, err = cerrar_sorries_por_comando(comp.sesion, cuerpo,
                                                      orden_de, env=env)
        except Exception as e:                                 # noqa: BLE001
            logger.info("cascada por estado: la sesión falló (%s); al fichero", e)
            comp.cerrar()
            return None
        if any(c.motivo == "agotada" for c in cierres):
            # tras un timeout el REPL no sirve, y el sorry agotado no está
            # decidido: que lo decida el fichero
            comp.cerrar()
            return None
    if err or not cierres:
        return None
    ganadoras = [c.ganadora or "first|" for c in cierres if c.cerrado]
    if ganadoras:
        ens = ensamblar(cuerpo, cierres, parcial=True)
        if ens is None:
            return None
        r = await cliente.check_code("\n".join(lineas_cab) + "\n" + ens)
        todos = len(ganadoras) == len(cierres)
        confirma = r.is_success if todos else (
            r.status == LeanResultStatus.SORRY and not r.get_first_error())
        if not confirma:
            logger.warning("cascada por estado: la sesión cerró %d sorry y el "
                           "fichero no lo confirma; decide el fichero",
                           len(ganadoras))
            return None
    return {"cerrados": len(ganadoras), "total": len(cierres),
            "ganadoras": ganadoras}
