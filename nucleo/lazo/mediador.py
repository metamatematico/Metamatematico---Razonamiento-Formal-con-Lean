# -*- coding: utf-8 -*-
"""El mediador: la búsqueda por pasos sobre la categoría de estados.

EL ALGORITMO (§4 de la propuesta)
---------------------------------
    1  la cabecera, una vez; el boceto con sus `sorry`, una vez
       si no elabora -> vuelve al formalizador                    (I5)
    2  cada `sorry` es una raíz de E
    3  mientras quede frontera y presupuesto:
         s <- el mejor de la frontera   (menos objetivos, luego menos profundo)
         para cada proponente, de más barato a más caro:
           para cada candidato: filtros gratuitos (I4, I6) -> Lean -> clase
         si s cerró, su raíz está resuelta
    4  si todas las raíces llegan al terminal: se ensambla la prueba y la
       compila el FICHERO; ése es el veredicto                     (I2)

LAS CLASES DE RESPUESTA
-----------------------
    cierra      goals [] y proofStatus «Completed»  -> camino hasta ⊤
    progresa    un estado nuevo                     -> a la frontera
    confluye    un estado ya visto en otra rama     -> se anota, no se re-expande (I3)
    no_avanza   el mismo estado o un antecesor      -> descartado: sería un ciclo
    incompleta  goals [] sin «Completed»: sorry, o   -> fallo; va a la memoria
                el kernel rechazando (issue 44)
    nombre      identificador desconocido           -> a la memoria del estado
    forma       error de tipos                      -> a la memoria, con la firma
    fallo       la táctica falla                    -> a la memoria
    cara        agotó el tope                       -> vetada; la sesión se rehace

SÓLO LEAN CREA FLECHAS (I1). Los proponentes producen candidatos; una flecha
existe si y sólo si la sesión aceptó la táctica en ese estado. Y ni siquiera
eso da el sello: lo da `check_code` sobre la prueba ensamblada (I2).

EL MODO TÁCTICA TIENE UN AGUJERO, Y SE CUBRE AQUÍ
-------------------------------------------------
El REPL no aplica el límite de heartbeats en modo táctica. Cada táctica lleva
un tope; si lo agota, la sesión queda inservible y se rehace, y los estados
abiertos se RECONSTRUYEN repitiendo su camino desde la raíz: un estado es su
camino, no su número de proofState, que sólo vale dentro de una sesión.
"""
from __future__ import annotations

import heapq
import itertools
import logging
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

from nucleo.graph.estados import normalizar
from nucleo.lazo import filtros

logger = logging.getLogger(__name__)


@dataclass
class Presupuesto:
    lean: int = 150            # llamadas a la sesión
    llamadas: int = 6          # llamadas al modelo
    segundos: float = 240.0
    nodos: int = 80
    profundidad: int = 8
    tope_tactica: int = 20     # segundos por táctica (el agujero de heartbeats)


@dataclass
class Nodo:
    id: int
    raiz: int
    objetivos: list
    camino: list
    profundidad: int
    ps: Optional[int] = None
    gen: int = 0
    padre: Optional[int] = None
    fallos: list = field(default_factory=list)
    probadas: set = field(default_factory=set)

    @property
    def clave(self) -> str:
        return clave_de(self.objetivos)


def clave_de(objetivos) -> str:
    """Identidad de objeto de E: los objetivos normalizados, en su orden."""
    return "\n‖\n".join(normalizar(g) for g in objetivos)


@dataclass
class Resultado:
    veredicto: str               # verificado · parcial · no_elabora · agotado · rechazado_por_fichero
    raices: int = 0
    cerradas: int = 0
    caminos: dict = field(default_factory=dict)
    codigo: str = ""
    llamadas_lean: int = 0
    llamadas_llm: int = 0
    segundos: float = 0.0
    nodos: int = 0
    confluencias: int = 0
    motivo: str = ""


def _subclase(error: str) -> str:
    e = (error or "").lower()
    if "timeout" in e:
        return "cara"
    if "unknown identifier" in e or "unknown constant" in e:
        return "nombre"
    if "type mismatch" in e or "failed to synthesize" in e:
        return "forma"
    return "fallo"


class Mediador:
    """Una búsqueda por pasos para un código con `sorry`.

    `abrir(cabecera)` devuelve una sesión viva y el entorno de esa cabecera:
    se llama al empezar y cada vez que una táctica agota su tope. `cliente` es el
    `LeanClient` del veredicto (I2).
    """

    def __init__(self, abrir: Callable, cliente, proponentes: list,
                 presupuesto: Optional[Presupuesto] = None, registro=None,
                 existe: Optional[Callable] = None, cerrar_al_final: bool = True):
        self._abrir = abrir
        self._cliente = cliente
        self._prop = list(proponentes)
        self.p = presupuesto or Presupuesto()
        self._reg = registro
        self._existe = existe
        #: False deja viva la sesión para el siguiente problema: un banco de
        #: cientos de enunciados con `import Mathlib` no puede recargarla en
        #: cada uno. Tras un tope agotado se rehace SIEMPRE, con esto o sin esto.
        self._cerrar_al_final = cerrar_al_final
        self._gen = 0
        self._sesion = None
        self._env = None
        self._raiz_ps: list = []

    # ── la sesión, y rehacerla ───────────────────────────────────────────
    def _plantar(self, cuerpo: str):
        r = self._sesion.comando(cuerpo, env=self._env)
        self.lean += 1
        return r

    def _rehacer(self, cuerpo: str) -> bool:
        """Sesión nueva y raíces nuevas: los proofState viejos ya no valen."""
        try:
            if self._sesion is not None:
                self._sesion.cerrar()
        except Exception:                                      # noqa: BLE001
            pass
        self._sesion, self._env = self._abrir(self._cab)
        self._gen += 1
        r = self._plantar(cuerpo)
        if r.clase == "error":
            return False
        # POR POSICIÓN, no por orden: el REPL devuelve los sorries
        # desordenados (visto en la sonda del paso 2), así que emparejarlos
        # por índice cambiaría una raíz por otra en silencio
        por_pos = {((s.get("pos") or {}).get("line"), (s.get("pos") or {}).get("column")):
                   s["proofState"] for s in r.sorries}
        nuevos = [por_pos.get((p.get("line"), p.get("column"))) for p in self._pos]
        if any(x is None for x in nuevos):
            return False
        self._raiz_ps = nuevos
        return True

    def _asegurar(self, nodo: Nodo) -> bool:
        """Que el proofState del nodo valga en la sesión de ahora."""
        if nodo.gen == self._gen and nodo.ps is not None:
            return True
        ps = self._raiz_ps[nodo.raiz]
        for t in nodo.camino:
            r = self._sesion.tactica(t, ps, tope=self.p.tope_tactica)
            self.lean += 1
            if r.clase not in ("progresa",) or r.proof_state is None:
                return False
            ps = r.proof_state
        nodo.ps, nodo.gen = ps, self._gen
        return True

    def sondear(self, tactica: str, nodo: Nodo):
        """Una táctica de SONDA para un proponente (D2): lee, no crea flechas.

        Cuenta en el presupuesto de Lean como cualquier otra, y si agota su
        tope la sesión se rehace aquí mismo —igual que con una candidata—.
        """
        if not self._asegurar(nodo):
            return None
        r = self._sesion.tactica(tactica, nodo.ps, tope=self.p.tope_tactica)
        self.lean += 1
        if "TIMEOUT" in (r.error or ""):
            if self._rehacer(self._cuerpo):
                self._asegurar(nodo)
            return None
        return r

    def _anota(self, **kw) -> None:
        if self._reg is not None:
            self._reg.anota(**kw)

    # ── la búsqueda ──────────────────────────────────────────────────────
    async def resolver(self, codigo: str) -> Resultado:
        from nucleo.lean.cascada_sesion import partir, _sustituye
        t0 = time.time()
        self.lean, self.llm = 0, 0
        texto = self._cliente._normalize_code(codigo)
        cab, cuerpo, lineas_cab = partir(texto)
        self._cab = cab
        self._cuerpo = cuerpo

        self._sesion, self._env = self._abrir(cab)
        r0 = self._plantar(cuerpo)
        if r0.clase == "error" or not r0.sorries:
            return Resultado("no_elabora", motivo=r0.error or "sin sorry",
                             llamadas_lean=self.lean, segundos=time.time() - t0)

        raices = r0.sorries
        self._raiz_ps = [s["proofState"] for s in raices]
        pos = [(s.get("pos") or {}) for s in raices]
        self._pos = pos
        contador = itertools.count()
        frontera: list = []
        vistos: dict = {}
        resueltas: dict = {}
        confl = 0
        nodos = []

        def empuja(nodo: Nodo) -> None:
            nodos.append(nodo)
            # POR RAÍZ: un estado que otra raíz ya alcanzó no le sirve a ésta,
            # que necesita su propio camino hasta el terminal
            vistos[(nodo.raiz, nodo.clave)] = nodo
            heapq.heappush(frontera, (len(nodo.objetivos), nodo.profundidad,
                                      next(contador), nodo))

        for i, s in enumerate(raices):
            empuja(Nodo(id=len(nodos), raiz=i, objetivos=[s.get("goal") or ""],
                        camino=[], profundidad=0, ps=self._raiz_ps[i],
                        gen=self._gen))

        def queda() -> bool:
            return (self.lean < self.p.lean and len(nodos) < self.p.nodos
                    and time.time() - t0 < self.p.segundos)

        while frontera and queda() and len(resueltas) < len(raices):
            _, _, _, nodo = heapq.heappop(frontera)
            if nodo.raiz in resueltas or nodo.profundidad > self.p.profundidad:
                continue
            if not self._asegurar(nodo):
                continue
            cerrado = False
            for prop in self._prop:
                if cerrado or not queda():
                    break
                if prop.coste == "llamada":
                    if self.llm >= self.p.llamadas:
                        continue
                    self.llm += 1
                try:
                    if getattr(prop, "usa_sesion", False):
                        cands = await prop.proponer(nodo, mediador=self)
                    else:
                        cands = await prop.proponer(nodo)
                except Exception as e:                         # noqa: BLE001
                    logger.info("el proponente %s falló: %s", prop.nombre, e)
                    continue
                for c in cands:
                    if cerrado or not queda():
                        break
                    c = (c or "").strip()
                    if not c or c in nodo.probadas:
                        continue
                    nodo.probadas.add(c)
                    rech = filtros.revisar(c, nodo.objetivos[0] if nodo.objetivos else "",
                                           existe=self._existe)
                    if rech is not None:
                        # no gasta Lean, pero SÍ va a la memoria del estado: el
                        # modelo tiene que saber que ese nombre no existe
                        nodo.fallos.append({"tactica": c, "clase": "filtro:" + rech.motivo,
                                            "lean": rech.detalle})
                        self._anota(nodo=nodo.id, estado=nodo.clave, tactica=c,
                                    proponente=prop.nombre, clase="filtro:" + rech.motivo)
                        continue
                    t1 = time.time()
                    resp = self._sesion.tactica(c, nodo.ps, tope=self.p.tope_tactica)
                    self.lean += 1
                    clase = resp.clase
                    if clase == "error":
                        clase = _subclase(resp.error)
                    destino = ""
                    if clase == "cierra":
                        resueltas[nodo.raiz] = nodo.camino + [c]
                        cerrado = True
                        destino = "⊤"
                    elif clase == "progresa":
                        nueva = clave_de(resp.objetivos)
                        destino = nueva
                        antecesores = self._antecesores(nodo, nodos)
                        if nueva == nodo.clave or nueva in antecesores:
                            clase = "no_avanza"
                        elif (nodo.raiz, nueva) in vistos:
                            clase = "confluye"
                            confl += 1
                        else:
                            empuja(Nodo(id=len(nodos), raiz=nodo.raiz,
                                        objetivos=list(resp.objetivos),
                                        camino=nodo.camino + [c],
                                        profundidad=nodo.profundidad + 1,
                                        ps=resp.proof_state, gen=self._gen,
                                        padre=nodo.id))
                    else:
                        nodo.fallos.append({"tactica": c, "clase": clase,
                                            "lean": resp.error})
                    self._anota(nodo=nodo.id, estado=nodo.clave, tactica=c,
                                proponente=prop.nombre, clase=clase,
                                destino=destino, segundos=round(time.time() - t1, 3))
                    if clase == "cara":
                        # la sesión no sirve tras un tope agotado: se rehace y
                        # este nodo se reconstruye por su camino al volver
                        if not self._rehacer(cuerpo):
                            return Resultado("agotado", motivo="no se pudo rehacer la sesión",
                                             llamadas_lean=self.lean, llamadas_llm=self.llm,
                                             segundos=time.time() - t0, nodos=len(nodos))
                        if not self._asegurar(nodo):
                            break

        res = Resultado("agotado", raices=len(raices), cerradas=len(resueltas),
                        caminos=dict(resueltas), llamadas_lean=self.lean,
                        llamadas_llm=self.llm, nodos=len(nodos), confluencias=confl)
        try:
            if self._sesion is not None and self._cerrar_al_final:
                self._sesion.cerrar()
        except Exception:                                      # noqa: BLE001
            pass

        # ── el veredicto lo da el fichero (I2) ───────────────────────────
        if resueltas:
            lineas = cuerpo.split("\n")
            # de atrás hacia delante para no mover posiciones
            orden = sorted(resueltas, key=lambda i: (pos[i].get("line", 0),
                                                     pos[i].get("column", 0)),
                           reverse=True)
            for i in orden:
                camino = resueltas[i]
                if not _sustituye(lineas, pos[i].get("line"), pos[i].get("column"),
                                  "; ".join(camino)):
                    res.veredicto, res.motivo = "agotado", "no se pudo ensamblar"
                    res.segundos = time.time() - t0
                    return res
            ens = "\n".join(lineas_cab) + "\n" + "\n".join(lineas)
            rf = await self._cliente.check_code(ens)
            res.codigo = ens
            if len(resueltas) == len(raices):
                res.veredicto = "verificado" if rf.is_success else "rechazado_por_fichero"
            else:
                from nucleo.lean.client import LeanResultStatus
                ok = rf.status == LeanResultStatus.SORRY and not rf.get_first_error()
                res.veredicto = "parcial" if ok else "rechazado_por_fichero"
            if res.veredicto == "rechazado_por_fichero":
                res.motivo = (rf.get_first_error() or "")[:300]
        res.segundos = time.time() - t0
        return res

    @staticmethod
    def _antecesores(nodo: Nodo, nodos: list) -> set:
        claves, n = set(), nodo
        while n is not None:
            claves.add(n.clave)
            n = nodos[n.padre] if n.padre is not None else None
        return claves
