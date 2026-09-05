# -*- coding: utf-8 -*-
"""¿Es π : Skills → Áreas una FIBRACIÓN? Y qué se gana si lo es.

QUE PREGUNTA RESUELVE, Y POR QUE «ES FUNTOR» NO BASTA
-----------------------------------------------------
`functor.py` construye π y comprueba las dos leyes de funtor. Eso dice que la
proyección está bien definida — pero un funtor que manda todo a un punto
también cumple las dos leyes y no informa de nada. Que π sea funtor no dice
que la base de áreas SIRVA para algo.

La condición que sí lo dice es la de fibración. Si en la base vale `b' ≼ b`
—«el álgebra conmutativa alimenta a la geometría algebraica»— tiene que poder
LEVANTARSE al total: dado un skill `e` de geometría algebraica, tiene que
existir EL skill de álgebra conmutativa que lo sostiene. No uno cualquiera:
el mayor de los que lo sostienen. Eso es un levantamiento CARTESIANO.

LO QUE SE GANA. Demostrado en `MetamathProver/CategoryFoundations/Fibracion.lean`
(0 sorry; `reindexado_monotono` y `reindexado_compuesto` no dependen de ningún
axioma):

    reindexado_monotono    cada flecha `b' ≼ b` de la base induce una
                           aplicación MONÓTONA fibra(b) → fibra(b'). O sea:
                           una manera de trasladar una pregunta de un área a
                           otra conservando el orden.
    reindexado_compuesto   encadenar restricciones de área no depende del
                           camino que se tome por la base.

Sin la condición cartesiana esa aplicación NO EXISTE, y «unificar los dos
mundos con un funtor» se queda en la etiqueta.

Y `no_toda_monotona_es_fibracion` exhibe un contraejemplo finito, para que
comprobar la condición sobre el grafo real signifique algo: se sabe que puede
fallar.

LAS DEFINICIONES DE AQUI SON LAS DE ALLI
----------------------------------------
`EsCartesiano` en Lean tiene tres campos —`sobre`, `debajo`, `universal`— y
`es_cartesiano` de aquí comprueba esos tres, con los mismos nombres. Si un día
divergen, el teorema deja de respaldar el código y hay que enterarse.

EL ORDEN. `a ≤ b` significa que hay un camino de `a` a `b` en el grafo, que es
el preorden de `is_preorder_leq` y el mismo que usa `QuotientFunctor.lean`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from nucleo.graph.functor import OBJETO_BASE, Funtor


@dataclass
class Levantamiento:
    """El resultado de intentar levantar `b' ≼ π(e)` hasta `e`."""
    objeto: str
    base: str
    #: el skill que sostiene a `objeto` desde `base`, o None si no hay
    cartesiano: Optional[str] = None
    #: cuántos candidatos había antes de exigir que uno fuera el mayor
    candidatos: int = 0
    #: de ésos, cuántos viven EXACTAMENTE en la fibra de `base`. Se cuenta
    #: aparte porque es lo que distingue «no hay soporte del área de abajo» de
    #: «hay soporte pero ninguno domina», y son problemas distintos: el
    #: primero se arregla añadiendo morfismos al grafo, el segundo no.
    soporte: int = 0
    #: por qué falló, si falló
    motivo: str = ""

    def __bool__(self) -> bool:
        return self.cartesiano is not None


def _orden(graph, tipos):
    """Devuelve `leq(a, b)` cacheado: ¿hay camino de a a b?"""
    cache: dict = {}

    def alcanzables(a):
        if a not in cache:
            cache[a] = graph.reachable_from(a, morphism_types=tipos)
        return cache[a]

    def leq(a, b):
        return a == b or b in alcanzables(a)

    return leq


def levantar(pi: Funtor, graph, e: str, base: str, tipos=None) -> Levantamiento:
    """El levantamiento cartesiano de `base ≼ π(e)` en `e`, si existe.

    Los tres campos de `EsCartesiano` (Fibracion.lean), en el mismo orden:

      debajo     el candidato `x` cumple `x ≤ e`
      sobre      su imagen es exactamente `base` (no «por debajo de base»)
      universal  y es EL MAYOR: todo otro candidato pasa por él

    La tercera es la que distingue «hay un skill del área de abajo» de «hay UN
    skill que los sostiene a todos». Sin ella cualquier nodo suelto valdría y
    la construcción no elegiría nada.
    """
    leq = _orden(graph, tipos)
    # candidatos: x ≤ e con π(x) ≼ base. Se usa `≼` y no `=` porque la
    # propiedad universal de Lean cuantifica sobre `π x ≤ b'`, no sobre
    # `π x = b'`: el mayor tiene que dominar también a los de más abajo.
    abajo_de_base = {a for a in pi.codominio.objetos
                     if a == base or base in pi.codominio.alcanzables_desde(a)}
    cand = [s.id for s in graph.skills
            if pi.en_objetos.get(s.id) in abajo_de_base
            and s.id != e and leq(s.id, e)]

    soporte = [x for x in cand if pi.en_objetos.get(x) == base]
    r = Levantamiento(objeto=e, base=base, candidatos=len(cand),
                      soporte=len(soporte))
    # SIN SOPORTE es el caso importante y hay que nombrarlo aparte: no es que
    # el levantamiento salga mal, es que la base afirma `b' ≼ b` y ni un solo
    # skill de `b'` está por debajo de `e`. Eso no se arregla con teoría; se
    # arregla añadiendo morfismos que crucen de área.
    if not soporte:
        r.motivo = "no hay ningun skill de %s por debajo de %s" % (base, e)
        return r
    # el mayor: todos los demás llegan a él
    mayores = [g for g in cand if all(leq(x, g) for x in cand)]
    if not mayores:
        r.motivo = "hay %d candidatos y ninguno domina a los demas" % len(cand)
        return r
    # `sobre`: su imagen tiene que ser exactamente la base, no una de más abajo
    exactos = [g for g in mayores if pi.en_objetos.get(g) == base]
    if not exactos:
        r.motivo = "el mayor vive en %s, no en %s" % (
            pi.en_objetos.get(mayores[0]), base)
        return r
    r.cartesiano = exactos[0]
    return r


@dataclass
class InformeFibracion:
    """Las cifras de la comprobación sobre el grafo entero."""
    pares: int = 0
    levantados: int = 0
    por_motivo: dict = field(default_factory=dict)
    fallos: list = field(default_factory=list)
    fibras: dict = field(default_factory=dict)

    @property
    def tasa(self) -> float:
        return self.levantados / self.pares if self.pares else 0.0

    @property
    def es_fibracion(self) -> bool:
        return self.pares > 0 and self.levantados == self.pares


def verificar_fibracion(pi: Funtor, graph, tipos=None,
                        incluir_base: bool = False) -> InformeFibracion:
    """Comprueba la condición en TODOS los pares (objeto, área de abajo).

    Un par es `(e, b')` con `b' ≺ π(e)` en la base. Los triviales —`b' = π(e)`,
    donde `e` se levanta a sí mismo— no se cuentan: inflarían la tasa sin
    decir nada.

    `incluir_base=False` deja fuera el objeto terminal (las tácticas y
    estrategias, que están fuera de la base a propósito). Con él dentro toda
    área tiene algo por debajo y la condición se vuelve casi vacía.
    """
    inf = InformeFibracion()
    for a in pi.codominio.objetos:
        inf.fibras[a] = sum(1 for v in pi.en_objetos.values() if v == a)

    for s in graph.skills:
        a = pi.en_objetos.get(s.id)
        if a is None:
            continue
        # las áreas ESTRICTAMENTE por debajo de la de `e`
        abajo = [b for b in pi.codominio.objetos
                 if b != a and a in pi.codominio.alcanzables_desde(b)]
        if not incluir_base:
            abajo = [b for b in abajo if b != OBJETO_BASE]
        for b in abajo:
            inf.pares += 1
            r = levantar(pi, graph, s.id, b, tipos)
            if r:
                inf.levantados += 1
            else:
                clave = r.motivo.split(" ")[0] + " " + r.motivo.split(" ")[1] \
                    if " " in r.motivo else r.motivo
                inf.por_motivo[clave] = inf.por_motivo.get(clave, 0) + 1
                if len(inf.fallos) < 40:
                    inf.fallos.append((s.id, b, r.motivo, r.candidatos))
    return inf
