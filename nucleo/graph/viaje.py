# -*- coding: utf-8 -*-
"""Viajar por la fibración: trasladar un concepto de un área a la que lo sostiene.

QUE ES UN VIAJE
---------------
Estás en `probability-theory`, que vive en el área `Probability`. La base dice
que `Analysis ≼ Probability` —el análisis alimenta a la probabilidad—. Viajar
es responder: ¿QUÉ concepto de análisis sostiene a éste? La respuesta es el
levantamiento cartesiano, y aquí es `real-analysis`.

Eso es exactamente `reindexado_monotono` de
`MetamathProver/CategoryFoundations/Fibracion.lean` (0 sorry, sin axiomas):
cada flecha de la base induce una aplicación fibra(b) → fibra(b') que CONSERVA
EL ORDEN. Encadenar dos viajes no depende del camino (`reindexado_compuesto`).

POR QUE ESTE MODULO NO SUPONE QUE PI SEA UNA FIBRACION
------------------------------------------------------
No lo es, y no puede serlo. Está medido:

    base cerrada transitivamente    13 de 6753 pares   0,2 %   (nulo 6,5 %)
    base directa                   102 de 1436 pares   7,1 %   (nulo 6,8 %)

La segunda fila es la importante y es una MALA noticia disfrazada de buena: al
no cerrar la base la tasa sube treinta y cinco veces, pero el modelo nulo sube
con ella y la ventaja se queda en 1,1x. La subida era casi toda artefacto de
achicar el denominador, no estructura.

Y no se arregla añadiendo morfismos: `scripts/base_no_es_un_orden.py` demuestra
que la clausura transitiva es monótona, así que una arista nueva sólo puede
AÑADIR relaciones a la base, y las áreas ya forman una componente fuertemente
conexa de 21 de 23. Exigir que TODO objeto de cualquiera de esas áreas se
levante a cualquier otra es matemática falsa: no todo concepto de álgebra
depende de uno de probabilidad.

LO QUE SI HAY, Y ES LO QUE ESTE MODULO SIRVE. Los 102 levantamientos que
existen son correctos uno a uno:

    probability-theory   [Probability]  <- Analysis   =  real-analysis
    descriptive-set-th.  [SetTheory]    <- Topology   =  point-set-topology
    differential-topol.  [Topology]     <- Geometry   =  differential-geometry
    derived-category     [Algebra]      <- Topology   =  algebraic-topology

Así que el viaje no es una capacidad general: es un conjunto concreto de
traslados reales. Este módulo los hace CONSULTABLES en vez de dejarlos en un
informe, y `cobertura()` dice cuántos son para que nadie los presente como más
de lo que son. Un viaje que no existe devuelve `None` con su motivo, nunca una
aproximación: inventar un traslado plausible es justo lo que este sistema
existe para no hacer.

LA BASE ES LA DIRECTA, NO SU CLAUSURA
-------------------------------------
`CategoriaAgentes.alcanzables_desde` cierra transitivamente. Para viajar eso no
vale: la clausura convierte 69 flechas en 462 relaciones, y las 393 nuevas no
las sostiene ningún morfismo. Viajar por una de ellas sería afirmar un soporte
que no existe. Aquí sólo se viaja por flechas que un morfismo real induce.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from nucleo.graph.fibracion import levantar
from nucleo.graph.functor import (OBJETO_BASE, CategoriaAgentes, Funtor,
                                  construir_funtor)


class BaseDirecta(CategoriaAgentes):
    """La base SIN cerrar: `b ≼ a` sólo si un morfismo real lo induce.

    Es la misma categoría de áreas, con la relación de alcanzabilidad
    restringida a un paso. Se hereda en vez de copiarse para que `hom`,
    `hay_flecha` y las multiplicidades sigan siendo las mismas.
    """

    def alcanzables_desde(self, a: str) -> set:
        return {a} | {t for (s, t) in self.morfismos if s == a}


def base_directa(pi: Funtor) -> Funtor:
    """El mismo π con la base sin cerrar."""
    return Funtor(
        en_objetos=pi.en_objetos,
        codominio=BaseDirecta(objetos=set(pi.codominio.objetos),
                              morfismos=dict(pi.codominio.morfismos)),
        colapsados=pi.colapsados,
    )


@dataclass
class Viaje:
    """Un traslado de `origen` al área `destino`, o la razón de que no exista."""
    origen: str
    #: el área desde la que se pregunta, π(origen)
    area_origen: str = ""
    #: el área a la que se viaja
    destino: str = ""
    #: el concepto de `destino` que sostiene a `origen`, o None
    soporte: Optional[str] = None
    #: cuántos skills de `destino` estaban por debajo de `origen`
    candidatos: int = 0
    motivo: str = ""

    def __bool__(self) -> bool:
        return self.soporte is not None

    def __repr__(self) -> str:
        if self:
            return "%s [%s] -> %s = %s" % (self.origen, self.area_origen,
                                           self.destino, self.soporte)
        return "%s -> %s : SIN VIAJE (%s)" % (self.origen, self.destino,
                                              self.motivo)


def viajar(graph, origen: str, destino: str, pi: Optional[Funtor] = None) -> Viaje:
    """El concepto de `destino` que sostiene a `origen`, si lo hay.

    `destino` es un ÁREA, no un skill: se pregunta «¿qué parte del análisis
    sostiene esto?», no «¿llega esto hasta aquel nodo?».
    """
    pi = base_directa(pi or construir_funtor(graph))
    a = pi.en_objetos.get(origen)
    v = Viaje(origen=origen, area_origen=a or "", destino=destino)

    if a is None:
        v.motivo = "%s no esta en el grafo, o no tiene area" % origen
        return v
    if destino == a:
        v.motivo = "el origen ya vive en %s" % destino
        return v
    if destino not in pi.codominio.objetos:
        v.motivo = "%s no es un area de la base" % destino
        return v
    # LA BASE TIENE QUE AFIRMARLO PRIMERO. Sin esta comprobacion se contestaria
    # a pares que la base no relaciona, y entonces el resultado no seria un
    # levantamiento cartesiano sino «un nodo de aquella area que resulta estar
    # por debajo», que es otra cosa y no la respalda ningun teorema.
    if a not in pi.codominio.alcanzables_desde(destino):
        v.motivo = ("la base no afirma %s <= %s: ningun morfismo del grafo lo "
                    "induce" % (destino, a))
        return v

    r = levantar(pi, graph, origen, destino, None)
    v.candidatos = r.candidatos
    v.soporte = r.cartesiano
    v.motivo = r.motivo
    return v


def destinos(graph, origen: str, pi: Optional[Funtor] = None) -> list:
    """A donde se puede viajar DESDE `origen`, con su soporte.

    Devuelve sólo los viajes que existen: es la lista que se le puede enseñar
    a alguien sin prometerle nada que luego falle.
    """
    pi = base_directa(pi or construir_funtor(graph))
    a = pi.en_objetos.get(origen)
    if a is None:
        return []
    salida = []
    for b in sorted(pi.codominio.objetos):
        if b == a or b == OBJETO_BASE:
            continue
        if a not in pi.codominio.alcanzables_desde(b):
            continue
        v = viajar(graph, origen, b, pi)
        if v:
            salida.append(v)
    return salida


def ruta(graph, origen: str, destino: str, pi: Optional[Funtor] = None,
         tope: int = 4) -> list:
    """Encadena viajes hasta `destino` cuando no hay flecha directa.

    Es `reindexado_compuesto`: componer dos reindexados da el reindexado de la
    composicion, asi que encadenar traslados es legitimo y el resultado no
    depende del camino. Se busca en anchura para dar el MAS CORTO, y `tope`
    acota la longitud porque una cadena larga traslada tan lejos del concepto
    original que deja de responder a la pregunta.

    Devuelve la lista de `Viaje` encadenados, o [] si no hay ruta.
    """
    pi = base_directa(pi or construir_funtor(graph))
    if pi.en_objetos.get(origen) is None:
        return []

    # (nodo actual, viajes hechos). En anchura: el primero que llega es el mas corto.
    cola = [(origen, [])]
    vistos = {origen}
    while cola:
        actual, hechos = cola.pop(0)
        if len(hechos) >= tope:
            continue
        for v in destinos(graph, actual, pi):
            if v.destino == destino:
                return hechos + [v]
            if v.soporte not in vistos:
                vistos.add(v.soporte)
                cola.append((v.soporte, hechos + [v]))
    return []


@dataclass
class Cobertura:
    """Cuantos viajes existen de verdad. Se publica junto a cualquier viaje."""
    pares: int = 0
    con_viaje: int = 0
    por_area: dict = field(default_factory=dict)

    @property
    def tasa(self) -> float:
        return self.con_viaje / self.pares if self.pares else 0.0


def cobertura(graph, pi: Optional[Funtor] = None) -> Cobertura:
    """Los pares que la base afirma, y en cuantos existe el viaje.

    ESTA FUNCION ACOMPAÑA A LAS OTRAS A PROPOSITO. `destinos()` devuelve una
    lista bonita de traslados y da la impresion de un sistema que sabe viajar;
    esta dice que son el 7 % de los que la base promete. Enseñar lo primero sin
    lo segundo es el mismo error que citar una precision sin su modelo nulo.
    """
    pi = base_directa(pi or construir_funtor(graph))
    c = Cobertura()
    for s in graph.skills:
        a = pi.en_objetos.get(s.id)
        if a is None:
            continue
        for b in pi.codominio.objetos:
            if b == a or b == OBJETO_BASE:
                continue
            if a not in pi.codominio.alcanzables_desde(b):
                continue
            c.pares += 1
            par = c.por_area.setdefault(b, [0, 0])
            par[1] += 1
            if levantar(pi, graph, s.id, b, None):
                c.con_viaje += 1
                par[0] += 1
    return c
