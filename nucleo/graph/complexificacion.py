"""
Complexificacion de Ehresmann, caso delgado.

QUE ES
------
`build_hierarchy_to_fixpoint` DESCUBRE colimites dentro de G_n y nunca sale de
ahi. Cuando un patron no tiene co-cono limite emite un `ConceptGap` y ahi
termina. Eso deja el sistema en el lado equivocado de la distincion que hace
Ehresmann:

    En matematicas se busca el colimite DENTRO de una categoria fija y la
    respuesta puede ser "no existe". En la modelizacion de sistemas evolutivos
    la inexistencia no cierra el problema: obliga a CAMBIAR de categoria
    mediante la complexificacion, y el objeto nuevo que aparece es
    precisamente el fenomeno emergente.

Mientras el sistema no complexifique, K' = K, y la pregunta por el orden de
complejidad no llega a plantearse: no hay nada que reducir porque no se
construyo nada.

POR QUE ESTO NO ES "FABRICAR UN VERTICE"
----------------------------------------
`build_join_for_pattern` retiro la fabricacion por tres razones, y las tres
eran correctas PARA AQUEL CODIGO. Conviene contestarlas una a una porque la
construccion de aqui es distinta:

1. "Inventar un vertice y cablearlo hasta que cumpla la propiedad universal es
   asumir la conclusion."
   Cierto de la version antigua, que creaba el nodo y le colgaba aristas a
   TODAS las cotas superiores "para asegurar minimalidad". Aqui el objeto no se
   elige: es `eta(P) = cotas superiores de P`, determinado por P. Que sea el
   colimite no se comprueba a posteriori, se sigue de la construccion —
   `eta_es_colimite` en Complexificacion.lean.

2. "No terminaba: cada nodo fabricado era un punto de convergencia nuevo."
   Cierto, y por eso la complexificacion NO va dentro del bucle de
   descubrimiento. Es un paso explicito y unico: K -> K'. Se añade un objeto
   por clase de huecos y se para. Si se quiere K'', es otra llamada. Asi es
   como Ehresmann itera, y es lo unico que puede producir orden de complejidad
   >= 2.

3. "Reescribia el objeto que analizaba."
   Este riesgo es REAL y no desaparece: insertar eta(P) entre las componentes y
   sus cotas puede quitarle la minimalidad a un colimite de otro patron.
   Ehresmann lo dice (§9.4: la insercion K -> K' no preserva colimites en
   general) y por eso la opcion debe EXIGIR la preservacion. Aqui no se
   esconde: se reverifica cada colimite previo y se reporta cual sobrevivio.
   Con `preservar=True` (defecto) se revierte entero si alguno se rompe.

CONDICION SUPLEMENTARIA (SC)
----------------------------
Ehresmann exige que patrones homologos reciban el MISMO colimite. Aqui sale
gratis: dos patrones con las mismas cotas superiores reciben literalmente el
mismo objeto, porque el objeto ES ese conjunto de cotas. Es
`SC_homologos_mismo_colimite`. En el codigo, la deduplicacion por
`frozenset(cotas)`.
"""
from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from nucleo.types import Skill, MorphismType

if TYPE_CHECKING:
    from nucleo.graph.category import SkillCategory
    from nucleo.graph.complexity import ConceptGap
    from nucleo.mes.patterns import PatternManager, ColimitBuilder

logger = logging.getLogger(__name__)


@dataclass
class ObjetoEmergente:
    """Un objeto que la complexificacion añadio a K'."""
    skill_id: str
    component_ids: list[str]
    cotas: list[str]                 # las cotas superiores que lo definen
    patrones: list[str] = field(default_factory=list)   # los huecos que cierra

    def __repr__(self) -> str:
        comps = ", ".join(self.component_ids[:3])
        if len(self.component_ids) > 3:
            comps += f" (+{len(self.component_ids) - 3})"
        return f"ObjetoEmergente({self.skill_id} = join[{comps}])"


@dataclass
class ResultadoComplexificacion:
    """Lo que produjo un paso K -> K'."""
    nuevos: list[ObjetoEmergente] = field(default_factory=list)
    huecos_cerrados: int = 0
    colimites_preservados: list[str] = field(default_factory=list)
    colimites_rotos: list[str] = field(default_factory=list)
    revertida: bool = False

    @property
    def preserva(self) -> bool:
        """True si ningun colimite previo perdio su minimalidad."""
        return not self.colimites_rotos

    def __repr__(self) -> str:
        if self.revertida:
            return (f"ResultadoComplexificacion(REVERTIDA: "
                    f"{len(self.colimites_rotos)} colimites rotos)")
        return (f"ResultadoComplexificacion(+{len(self.nuevos)} objetos, "
                f"{self.huecos_cerrados} huecos cerrados, "
                f"{len(self.colimites_preservados)} colimites preservados, "
                f"{len(self.colimites_rotos)} rotos)")


def _id_emergente(cotas: frozenset[str]) -> str:
    """
    Id estable a partir del CONJUNTO DE COTAS, no de las componentes.

    Es la condicion suplementaria hecha codigo: dos patrones con el mismo campo
    de cotas superiores son homologos y deben recibir el mismo objeto. Si el id
    dependiera de las componentes, dos homologos recibirian objetos distintos y
    se violaria SC — la deficiencia (b) que Ehresmann señala en §3.2.
    """
    h = hashlib.sha1("|".join(sorted(cotas)).encode("utf-8")).hexdigest()[:8]
    return f"emergente-{h}"


def _minimales(ids: list[str], graph: "SkillCategory") -> list[str]:
    """
    Los elementos minimales del conjunto, en el preorden de orden.

    Basta conectar eta(P) con estos: el resto queda por encima por
    transitividad. En un poset FINITO todo elemento esta por encima de algun
    minimal del subconjunto, asi que no se pierde ninguna cota.
    """
    from nucleo.graph.category import SkillCategory as _SC
    _ORD = _SC.ORDER_MORPHISMS
    out = []
    for x in ids:
        if not any(
            y != x and graph.is_preorder_leq(y, x, _ORD)
            for y in ids
        ):
            out.append(x)
    return out


def complexificar(
    graph: "SkillCategory",
    pattern_manager: "PatternManager",
    colimit_builder: "ColimitBuilder",
    gaps: "list[ConceptGap]",
    *,
    preservar: bool = True,
) -> ResultadoComplexificacion:
    """
    Un paso de complexificacion: K -> K'.

    Por cada hueco con al menos una cota superior se añade el objeto
    `eta(P) = cotas superiores de P`, con las aristas que lo hacen el minimo
    entre ellas:

        c -> eta(P)      para cada componente c de P
        eta(P) -> m      para cada cota superior minimal m

    Un hueco SIN cotas superiores no se puede cerrar asi: `eta(P)` seria el
    objeto maximo y colgaria de todo el grafo. Se deja abierto y se dice.

    Args:
        gaps: los huecos a cerrar (normalmente los de build_hierarchy_to_fixpoint).
        preservar: si True y algun colimite previo pierde su minimalidad, se
            revierte el paso ENTERO y no se toca el grafo. Es el objetivo (iii)
            de la opcion de Ehresmann, que exige preservar los colimites que ya
            existian. Con False se aplica igual y se reporta lo roto.

    Returns:
        ResultadoComplexificacion con los objetos nuevos y el balance de
        preservacion.
    """
    from nucleo.graph.complexity import find_cocones, find_colimit

    res = ResultadoComplexificacion()

    # ── Estado previo, para poder reverificar y revertir ────────────────────
    previos: list[tuple[str, list[str]]] = []
    for col in colimit_builder.all_colimits:
        pat = pattern_manager.get_pattern(col.pattern_id) if col.pattern_id else None
        if pat and col.skill_id:
            previos.append((col.skill_id, list(pat.component_ids)))

    # ── Agrupar los huecos por campo de cotas: SC ──────────────────────────
    por_cotas: dict[frozenset, ObjetoEmergente] = {}
    sin_cotas = 0
    for gap in gaps:
        # Un hueco YA CERRADO no vuelve a abrirse. Sin esta guarda el paso no
        # es idempotente y reaparece la no-terminacion que hizo retirar la
        # fabricacion de nodos: tras insertar eta(P), eta(P) pasa a ser cota
        # superior de P, luego el conjunto de cotas cambia, luego una segunda
        # llamada crea OTRO objeto por el mismo hueco, y asi sin fin.
        if find_colimit(list(gap.component_ids), graph, colimit_builder) is not None:
            logger.debug(
                f"hueco ya cerrado, se omite: {list(gap.component_ids)[:3]}…"
            )
            continue
        cotas = find_cocones(list(gap.component_ids), graph)
        if not cotas:
            sin_cotas += 1
            logger.debug(
                f"hueco sin cotas superiores, no se puede cerrar en un paso: "
                f"{list(gap.component_ids)[:3]}…"
            )
            continue
        clave = frozenset(cotas)
        if clave in por_cotas:
            # Homologos: comparten objeto. SC_homologos_mismo_colimite.
            obj = por_cotas[clave]
            for c in gap.component_ids:
                if c not in obj.component_ids:
                    obj.component_ids.append(c)
            if gap.pattern_id:
                obj.patrones.append(gap.pattern_id)
        else:
            por_cotas[clave] = ObjetoEmergente(
                skill_id=_id_emergente(clave),
                component_ids=list(gap.component_ids),
                cotas=sorted(cotas),
                patrones=[gap.pattern_id] if gap.pattern_id else [],
            )

    if not por_cotas:
        logger.info(
            f"complexificar: nada que hacer ({sin_cotas} huecos sin cotas superiores)"
        )
        return res

    # ── Insertar los objetos ────────────────────────────────────────────────
    añadidos: list[str] = []
    for obj in por_cotas.values():
        if graph.get_skill(obj.skill_id) is not None:
            continue                          # ya existe de un paso anterior
        comps = [graph.get_skill(c) for c in obj.component_ids]
        comps = [c for c in comps if c is not None]
        pilares = [c.pillar for c in comps if c.pillar is not None]
        skill = Skill(
            id=obj.skill_id,
            name=f"join[{', '.join(obj.component_ids[:3])}]",
            description=(
                "Objeto emergente: colimite del patron, aportado por la "
                "complexificacion. Falta nombrarlo — el concepto que le "
                "corresponde lo aporta la matematica, no la construccion."
            ),
            pillar=max(set(pilares), key=pilares.count) if pilares else None,
            # level es taxonomia CURADA: no se inventa. Se hereda el maximo de
            # las componentes y se marca provisional. cn lo calcula el sistema.
            level=max((c.level for c in comps), default=0),
            metadata={
                "emergente": True,
                "level_provisional": True,
                "componentes": list(obj.component_ids),
                "cotas": list(obj.cotas),
                "sin_nombrar": True,
            },
        )
        graph.add_skill(skill)
        añadidos.append(obj.skill_id)
        for c in obj.component_ids:
            graph.add_morphism(c, obj.skill_id, MorphismType.DEPENDENCY)
        for m in _minimales(obj.cotas, graph):
            graph.add_morphism(obj.skill_id, m, MorphismType.DEPENDENCY)
        res.nuevos.append(obj)

    # ── Reverificacion ──────────────────────────────────────────────────────
    for skill_id, comps in previos:
        if colimit_builder.is_join(skill_id, comps, graph)["is_join"]:
            res.colimites_preservados.append(skill_id)
        else:
            res.colimites_rotos.append(skill_id)

    for obj in res.nuevos:
        if find_colimit(obj.component_ids, graph, colimit_builder) == obj.skill_id:
            res.huecos_cerrados += 1
        else:
            logger.warning(
                f"complexificar: {obj.skill_id} no salio como colimite de su "
                f"patron — revisar las cotas minimales"
            )

    # ── Preservacion: revertir si se rompio algo ───────────────────────────
    if preservar and res.colimites_rotos:
        logger.warning(
            f"complexificar: {len(res.colimites_rotos)} colimites previos "
            f"perdieron la minimalidad; se revierte el paso entero"
        )
        for sid in añadidos:
            graph.remove_skill(sid)
        res.revertida = True
        res.nuevos = []
        res.huecos_cerrados = 0
        return res

    logger.info(f"complexificar: {res}")
    return res
