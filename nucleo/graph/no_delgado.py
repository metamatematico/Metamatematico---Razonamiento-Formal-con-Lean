"""
Salir de la delgadez: `Hom(a,b)` como conjunto, no como booleano.

EL PROBLEMA
-----------
`lub_de_lubs` (Complexificacion.lean §8) demuestra que mientras la categoria sea
delgada, iterar colimites no puede producir orden de complejidad >= 2: el
colimite es el supremo, el supremo es asociativo, todo se aplana.

`§9` y `§10` del mismo archivo localizan el eslabon exacto: **la condicion de
co-cono es vacua cuando `Hom` tiene a lo sumo un elemento**. Un enlace
distinguido `x : P_i -> P_j` induce por precomposicion

    x* : Hom(P_j, A) -> Hom(P_i, A)

y un co-cono es una familia `(f_i)` con `f_i = x*(f_j)`. Si cada `Hom` tiene un
elemento, esa igualdad se cumple sola y «co-cono» degenera a «cota superior».

`cota_superior_no_implica_cocono` exhibe el contraejemplo: dos enlaces
distinguidos paralelos con `Hom` de dos elementos, y NINGUNA eleccion es
co-cono, pese a que el apice es cota superior de las dos componentes.

QUE HACE ESTE MODULO
--------------------
Da la version operativa de esa definicion, sobre el grafo real:

  · `multiplicidad`      — donde `Hom(a,b)` tiene mas de un elemento;
  · `caminos`            — `Hom(a,b)` en la categoria LIBRE (caminos), que es
                           donde la composicion esta definida sin ambiguedad;
  · `es_cocono_libre`    — la condicion de familia compatible, de verdad;
  · `comparar_cocono`    — donde la version delgada y la libre discrepan.

QUE **NO** HACE
---------------
No sustituye a `find_colimit`. El pipeline de colimites sigue corriendo sobre el
cociente delgado —`is_preorder_leq`, `reachable_from`— y esta bien que asi sea
mientras el grafo no tenga multiplicidad que aprovechar: hoy solo 2 pares de los
552 tienen mas de un morfismo, mas los que se registren a mano.

Y hay una decision de diseño pendiente que no se puede tomar desde el codigo:
en la categoria LIBRE casi nada conmuta, luego casi no hay co-conos; en la
delgada todo conmuta, luego el colimite es el supremo. Lo correcto esta en
medio —caminos modulo relaciones declaradas, que es la construccion por
generadores y relaciones de Ehresmann §3.5— y las relaciones son contenido
matematico que hay que escribir, no derivar.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from itertools import product
from typing import TYPE_CHECKING, Optional

from nucleo.types import MorphismType

if TYPE_CHECKING:
    from nucleo.graph.category import SkillCategory
    from nucleo.types import Pattern

logger = logging.getLogger(__name__)

#: Cota de longitud para enumerar caminos. En la categoria libre `Hom(a,b)` es
#: infinito si hay ciclos y explota combinatoriamente si no; se acota y se dice.
MAX_LONGITUD = 3


@dataclass
class InformeMultiplicidad:
    """Donde el grafo deja de ser delgado."""
    pares_totales: int = 0
    pares_multiples: int = 0
    detalle: list[tuple[str, str, list[str]]] = field(default_factory=list)

    @property
    def es_delgado(self) -> bool:
        return self.pares_multiples == 0

    def __repr__(self) -> str:
        return (f"InformeMultiplicidad({self.pares_multiples}/{self.pares_totales} "
                f"pares con |Hom| > 1, "
                f"{'DELGADO' if self.es_delgado else 'NO delgado'})")


def multiplicidad(graph: "SkillCategory") -> InformeMultiplicidad:
    """
    Los pares `(a,b)` con `|Hom(a,b)| > 1`, sin contar identidades.

    Es la medida de cuanto margen tiene el sistema para salir de la delgadez.
    Con 0 pares, `lub_de_lubs` se aplica a todo el grafo y no hay emergencia
    posible; cada par que se añade es un sitio donde deja de aplicarse.
    """
    inf = InformeMultiplicidad()
    vistos: set[tuple[str, str]] = set()
    for m in graph.morphisms:
        if m.morphism_type == MorphismType.IDENTITY:
            continue
        par = (m.source_id, m.target_id)
        if par in vistos:
            continue
        vistos.add(par)
        hs = [h for h in graph.hom(*par)
              if h.morphism_type != MorphismType.IDENTITY]
        inf.pares_totales += 1
        if len(hs) > 1:
            inf.pares_multiples += 1
            # Se listan las CONSTRUCCIONES, que es lo que distingue de verdad
            # a dos morfismos paralelos. Sin nombre, el morfismo es la
            # dependencia generica que declaro el dominio.
            inf.detalle.append((
                par[0], par[1],
                sorted(h.metadata.get("construccion") or "(generico)" for h in hs),
            ))
    return inf


def caminos(
    graph: "SkillCategory",
    origen: str,
    destino: str,
    max_longitud: int = MAX_LONGITUD,
) -> list[tuple[str, ...]]:
    """
    `Hom(origen, destino)` en la CATEGORIA LIBRE sobre el quiver: los caminos.

    Cada camino es la tupla de ids de sus aristas. Es la unica lectura en la que
    la composicion esta definida sin ambiguedad —concatenar— y en la que dos
    morfismos paralelos distintos siguen siendo distintos.

    `path_category_axioms` (SkillCategory.lean) es el respaldo de que esto es una
    categoria.
    """
    if origen == destino:
        return [()]
    salida: list[tuple[str, ...]] = []

    def _ir(actual: str, camino: tuple[str, ...]) -> None:
        if len(camino) >= max_longitud:
            return
        for m in graph.outgoing_morphisms(actual):
            if m.morphism_type == MorphismType.IDENTITY:
                continue
            nuevo = camino + (m.id,)
            if m.target_id == destino:
                salida.append(nuevo)
            _ir(m.target_id, nuevo)

    _ir(origen, ())
    return salida


def es_cocono_libre(
    pattern: "Pattern",
    eleccion: dict[str, tuple[str, ...]],
    graph: "SkillCategory",
) -> bool:
    """
    ¿Es `eleccion` una familia COMPATIBLE, o sea un co-cono de verdad?

    La condicion de Ehresmann: para cada enlace distinguido `x : P_i -> P_j`,

        P(x) ; f_j = f_i

    En la categoria libre eso es igualdad de caminos: concatenar la arista del
    enlace con el camino elegido para `P_j` tiene que dar exactamente el camino
    elegido para `P_i`.

    Con `index_morphisms` vacio la condicion es vacua y devuelve True siempre —
    que es lo que pasaba en los 116 patrones antes de que los enlaces
    distinguidos se poblaran.
    """
    for nombre, (i_idx, j_idx) in pattern.index_morphisms.items():
        link_id = pattern.functor_map_morphisms.get(nombre)
        ci = pattern.functor_map_objects.get(i_idx)
        cj = pattern.functor_map_objects.get(j_idx)
        if link_id is None or ci is None or cj is None:
            continue
        if ci not in eleccion or cj not in eleccion:
            return False
        if (link_id,) + eleccion[cj] != eleccion[ci]:
            return False
    return True


def hay_cocono_libre(
    pattern: "Pattern",
    apex: str,
    graph: "SkillCategory",
    max_longitud: int = MAX_LONGITUD,
    max_combinaciones: int = 20000,
) -> Optional[bool]:
    """
    ¿Existe algun co-cono sobre `pattern` con vertice `apex`?

    Returns:
        True/False, o None si la busqueda supero `max_combinaciones` — en cuyo
        caso no se afirma nada. Un "no se sabe" explicito es mejor que un False
        que en realidad significa "me rendi".
    """
    homs: dict[str, list[tuple[str, ...]]] = {}
    for c in pattern.component_ids:
        cs = caminos(graph, c, apex, max_longitud)
        if not cs:
            return False               # falta cota: no puede haber co-cono
        homs[c] = cs

    total = 1
    for cs in homs.values():
        total *= len(cs)
        if total > max_combinaciones:
            logger.debug(
                f"hay_cocono_libre: {total} combinaciones supera la cota; "
                f"no se afirma nada para apex={apex}"
            )
            return None

    comps = list(homs.keys())
    for combo in product(*(homs[c] for c in comps)):
        if es_cocono_libre(pattern, dict(zip(comps, combo)), graph):
            return True
    return False


def comparar_cocono(
    pattern: "Pattern",
    apex: str,
    graph: "SkillCategory",
    max_longitud: int = MAX_LONGITUD,
) -> dict:
    """
    Contrasta las dos lecturas sobre el mismo par (patron, apice).

    `delgado` es la que usa el sistema hoy: apice es cota superior de las
    componentes. `libre` exige la conmutacion de verdad.

    `discrepan=True` marca un sitio donde la delgadez estaba concediendo un
    co-cono que no lo es — y por tanto un colimite que podria no serlo.
    """
    from nucleo.graph.category import SkillCategory as _SC
    _ORD = _SC.ORDER_MORPHISMS

    delgado = all(
        graph.is_preorder_leq(c, apex, _ORD) for c in pattern.component_ids
    )
    libre = hay_cocono_libre(pattern, apex, graph, max_longitud)
    return {
        "delgado": delgado,
        "libre": libre,
        "discrepan": libre is not None and delgado != libre,
        "n_enlaces_distinguidos": len(pattern.index_morphisms),
    }


# ---------------------------------------------------------------------------
# Morfismos certificados en Lean
# ---------------------------------------------------------------------------

#: Morfismos cuya multiplicidad esta DEMOSTRADA, no supuesta.
#:
#: Cada entrada es (origen, destino, construccion, teorema, que afirma). El
#: teorema vive en MorfismosGrupoAnillo.lean y separa las construcciones por
#: cardinal sobre ZMod 5: 5, 4 y 1. Distintos dos a dos, luego no hay
#: isomorfismo posible (`no_hay_iso`), luego el par NO es delgado
#: (`hom_no_es_delgado`).
#:
#: `la_lista_completa` añade el matiz que hace esto interesante: dentro de la
#: clase de operaciones definibles por un termino afin del anillo, el grupo
#: aditivo es el UNICO —los cinco candidatos que pasan son `x + y + c`—. El
#: grupo de unidades escapa a esa clase porque no se define por un termino sino
#: por una condicion. No son dos variantes de lo mismo: son de especies
#: distintas.
MORFISMOS_CERTIFICADOS: list[tuple[str, str, str, str, str]] = [
    ("group-theory", "ring-theory", "grupo-aditivo",
     "MorfismosGrupoAnillo.card_aditivo",
     "todo anillo es grupo abeliano bajo la suma; |(ZMod 5, +)| = 5"),
    ("group-theory", "ring-theory", "grupo-unidades",
     "MorfismosGrupoAnillo.card_unidades",
     "las unidades forman grupo bajo el producto; |(ZMod 5)^x| = 4"),
    ("group-theory", "ring-theory", "grupo-trivial",
     "MorfismosGrupoAnillo.card_trivial",
     "el funtor constante al grupo trivial; cardinal 1"),

    # ── ring-theory -> field-theory ────────────────────────────────────────
    ("ring-theory", "field-theory", "anillo-subyacente",
     "MultiplicidadDelGrafo.card_anillo_subyacente",
     "el anillo subyacente del cuerpo; |ZMod 5| = 5"),
    ("ring-theory", "field-theory", "anillo-matrices",
     "MultiplicidadDelGrafo.card_anillo_matrices",
     "el anillo de matrices 2x2 sobre el cuerpo; cardinal 625"),
    ("ring-theory", "field-theory", "anillo-trivial",
     "MultiplicidadDelGrafo.card_anillo_trivial",
     "el anillo trivial; cardinal 1"),

    # ── ring-theory -> module-theory ───────────────────────────────────────
    ("ring-theory", "module-theory", "modulo-regular",
     "MultiplicidadDelGrafo.card_modulo_regular",
     "el anillo como modulo sobre si mismo; cardinal 5"),
    ("ring-theory", "module-theory", "modulo-libre-2",
     "MultiplicidadDelGrafo.card_modulo_libre2",
     "el modulo libre de rango 2; cardinal 25"),
    ("ring-theory", "module-theory", "modulo-cero",
     "MultiplicidadDelGrafo.card_modulo_cero",
     "el modulo cero; cardinal 1"),

    # ── field-extensions -> finite-fields ──────────────────────────────────
    ("field-extensions", "finite-fields", "cuerpo-primo-2",
     "MultiplicidadDelGrafo.card_cuerpo_2",
     "el cuerpo primo de caracteristica 2; cardinal 2"),
    ("field-extensions", "finite-fields", "cuerpo-primo-3",
     "MultiplicidadDelGrafo.card_cuerpo_3",
     "el cuerpo primo de caracteristica 3; cardinal 3"),
    ("field-extensions", "finite-fields", "cuerpo-primo-5",
     "MultiplicidadDelGrafo.card_cuerpo_5",
     "el cuerpo primo de caracteristica 5; cardinal 5"),

    # ── group-theory -> group-actions ──────────────────────────────────────
    #
    # El par instructivo: las tres acciones comparten CONJUNTO SUBYACENTE, asi
    # que el cardinal no las separa. Lo hace el numero de puntos fijos. La
    # multiplicidad no siempre se ve por el tamaño del resultado.
    ("group-theory", "group-actions", "accion-traslacion",
     "MultiplicidadDelGrafo.fijos_traslacion",
     "traslacion g.x = g+x; 0 puntos fijos"),
    ("group-theory", "group-actions", "accion-trivial",
     "MultiplicidadDelGrafo.fijos_trivial",
     "accion trivial g.x = x; 4 puntos fijos"),
    ("group-theory", "group-actions", "accion-paridad",
     "MultiplicidadDelGrafo.fijos_paridad",
     "los g impares intercambian 0<->1; 2 puntos fijos"),

    # ── commutative-algebra -> algebraic-geometry ──────────────────────────
    #
    # El PRIMERO que participa en los colimites del grafo: algebraic-geometry
    # es colimite de {commutative-algebra, functors}. Los anteriores eran
    # dependencias que ningun patron de convergencia usaba, asi que su
    # multiplicidad no podia cambiar ningun resultado.
    ("commutative-algebra", "algebraic-geometry", "espectro-primo",
     "MultiplicidadDelGrafo.card_spec",
     "Spec R con la topologia de Zariski; un cuerpo tiene un unico primo"),
    ("commutative-algebra", "algebraic-geometry", "espacio-discreto",
     "MultiplicidadDelGrafo.card_discreto",
     "el conjunto subyacente con la topologia discreta; 5 puntos"),
]


def registrar_morfismos_certificados(graph: "SkillCategory") -> list[str]:
    """
    Mete en el grafo la multiplicidad que Lean certifico.

    Es el primer sitio del sistema donde `Hom(a,b)` tiene mas de un elemento por
    una razon matematica y no por una arista repetida. Cada morfismo lleva en
    sus metadatos el teorema que lo respalda.

    Returns:
        Los ids de los morfismos registrados (los que ya existian incluidos).
    """
    ids: list[str] = []
    for origen, destino, constr, teorema, afirma in MORFISMOS_CERTIFICADOS:
        if graph.get_skill(origen) is None or graph.get_skill(destino) is None:
            logger.debug(f"no estan {origen} o {destino} en el grafo; se omite")
            continue
        m = graph.add_morphism(
            origen, destino, MorphismType.DEPENDENCY,
            construccion=constr,
            metadata={"teorema_lean": teorema, "afirma": afirma,
                      "certificado": True},
        )
        if m is not None:
            ids.append(m.id)
    if ids:
        logger.info(
            f"registrados {len(ids)} morfismos certificados; "
            f"Hom(group-theory, ring-theory) deja de ser delgado"
        )
    return ids


# ---------------------------------------------------------------------------
# Congruencia: caminos modulo relaciones declaradas
# ---------------------------------------------------------------------------

@dataclass
class Congruencia:
    """
    Las relaciones que identifican caminos: la eleccion que faltaba.

    `no_delgado` decia que la decision entre categoria LIBRE y DELGADA no la
    toma el codigo. Esta clase la hace explicita y parametrizable en vez de
    dejarla implicita en el cociente.

    El espectro esta ORDENADO, y eso si es un teorema:
    `cocono_monotono_en_la_congruencia` — cuantas mas identificaciones, mas
    co-conos. Los dos extremos lo acotan:

      · `Congruencia()` vacia         -> categoria LIBRE. Casi nada conmuta,
                                         casi no hay co-conos
                                         (`cocono_libre_puede_fallar`).
      · `Congruencia(total=True)`     -> categoria DELGADA. Todo paralelo se
                                         identifica, la conmutacion se cumple
                                         sola (`cocono_delgado_siempre`), y por
                                         `lub_de_lubs` no hay emergencia.

    Declarar una relacion nunca quita co-conos: solo puede añadirlos. Asi que
    crecer el conjunto mueve el sistema en una direccion conocida.

    Attributes:
        relaciones: pares de caminos paralelos declarados iguales.
        total: si True, TODO par de caminos paralelos se identifica (delgado).
    """
    relaciones: list[tuple[tuple[str, ...], tuple[str, ...]]] = field(default_factory=list)
    total: bool = False

    def declarar(self, p: tuple[str, ...], q: tuple[str, ...]) -> "Congruencia":
        """Declara `p = q`. Deben ser paralelos; el llamador lo garantiza."""
        if (p, q) not in self.relaciones and (q, p) not in self.relaciones:
            self.relaciones.append((p, q))
        return self

    def iguales(self, p: tuple[str, ...], q: tuple[str, ...]) -> bool:
        """
        ¿Son `p` y `q` el mismo morfismo bajo esta congruencia?

        Cierre por contexto: si `p = q` esta declarado, entonces
        `r·p·s = r·q·s` para cualesquiera `r`, `s`. Se aplica hasta punto fijo
        sobre los dos caminos dados, que es finito porque las reescrituras no
        alargan.

        NOTA sobre el alcance: el problema de la palabra para una presentacion
        arbitraria es indecidible. Aqui se decide sobre caminos ACOTADOS, con
        reescritura hasta punto fijo. Basta para lo que el sistema usa, y no se
        promete mas.
        """
        if p == q:
            return True
        if self.total:
            return True
        vistos = {p}
        frontera = [p]
        while frontera:
            actual = frontera.pop()
            for a, b in self.relaciones:
                for desde, hacia in ((a, b), (b, a)):
                    n = len(desde)
                    if n == 0:
                        continue
                    for i in range(len(actual) - n + 1):
                        if actual[i:i + n] == desde:
                            nuevo = actual[:i] + hacia + actual[i + n:]
                            if nuevo == q:
                                return True
                            if nuevo not in vistos:
                                vistos.add(nuevo)
                                frontera.append(nuevo)
        return False


#: La congruencia que reproduce el sistema actual. Se nombra para que deje de
#: ser una suposicion tacita: hoy el pipeline corre AQUI, en el extremo donde
#: `lub_de_lubs` prohibe la emergencia.
DELGADA = Congruencia(total=True)

#: El otro extremo. Util para medir, no para producir.
LIBRE = Congruencia()


def es_cocono_cong(
    pattern: "Pattern",
    eleccion: dict[str, tuple[str, ...]],
    cong: Congruencia,
) -> bool:
    """Co-cono modulo una congruencia. Es `esCoconoMod` de Complexificacion.lean."""
    for nombre, (i_idx, j_idx) in pattern.index_morphisms.items():
        link_id = pattern.functor_map_morphisms.get(nombre)
        ci = pattern.functor_map_objects.get(i_idx)
        cj = pattern.functor_map_objects.get(j_idx)
        if link_id is None or ci is None or cj is None:
            continue
        if ci not in eleccion or cj not in eleccion:
            return False
        if not cong.iguales((link_id,) + eleccion[cj], eleccion[ci]):
            return False
    return True


def hay_cocono_cong(
    pattern: "Pattern",
    apex: str,
    graph: "SkillCategory",
    cong: Congruencia,
    max_longitud: int = MAX_LONGITUD,
    max_combinaciones: int = 20000,
) -> Optional[bool]:
    """¿Hay co-cono sobre `pattern` con vertice `apex`, modulo `cong`?"""
    homs: dict[str, list[tuple[str, ...]]] = {}
    for c in pattern.component_ids:
        cs = caminos(graph, c, apex, max_longitud)
        if not cs:
            return False
        homs[c] = cs
    total = 1
    for cs in homs.values():
        total *= len(cs)
        if total > max_combinaciones:
            return None
    comps = list(homs.keys())
    for combo in product(*(homs[c] for c in comps)):
        if es_cocono_cong(pattern, dict(zip(comps, combo)), cong):
            return True
    return False


def espectro(
    pattern: "Pattern",
    apex: str,
    graph: "SkillCategory",
    cong: Congruencia,
    max_longitud: int = MAX_LONGITUD,
) -> dict:
    """
    Situa una congruencia concreta entre los dos extremos.

    Por `cocono_monotono_en_la_congruencia` se cumple
    `libre <= cong <= delgada` como implicaciones, asi que las tres columnas
    solo pueden ir de False a True en ese orden. Si aparece otra cosa, hay un
    error en la congruencia.
    """
    return {
        "libre": hay_cocono_cong(pattern, apex, graph, LIBRE, max_longitud),
        "declarada": hay_cocono_cong(pattern, apex, graph, cong, max_longitud),
        "delgada": hay_cocono_cong(pattern, apex, graph, DELGADA, max_longitud),
        "n_relaciones": len(cong.relaciones),
    }


def congruencia_respeta_certificados(
    cong: Congruencia,
    graph: "SkillCategory",
) -> list[tuple[str, str, str]]:
    """
    Comprueba que la congruencia no identifica morfismos que Lean separo.

    Es el sentido menos obvio del certificado, y el mas util en la practica:
    `no_hay_iso` no solo dice que `grupo-aditivo` y `grupo-unidades` existen
    como morfismos distintos — dice que **declararlos iguales seria falso**.

    La congruencia total (`DELGADA`) los identifica a todos, luego viola todos
    los certificados. Que es precisamente el diagnostico del sistema actual:
    esta en un extremo del espectro que la matematica ya refuto para los pares
    donde hay multiplicidad demostrada.

    Returns:
        Las violaciones, como (origen, destino, motivo). Vacia = compatible.
    """
    violaciones: list[tuple[str, str, str]] = []
    por_par: dict[tuple[str, str], list] = {}
    for m in graph.morphisms:
        if m.metadata.get("certificado"):
            por_par.setdefault((m.source_id, m.target_id), []).append(m)

    for (origen, destino), ms in por_par.items():
        for i, a in enumerate(ms):
            for b in ms[i + 1:]:
                if cong.iguales((a.id,), (b.id,)):
                    violaciones.append((
                        origen, destino,
                        f"identifica '{a.metadata.get('construccion')}' con "
                        f"'{b.metadata.get('construccion')}', que "
                        f"{a.metadata.get('teorema_lean')} separa",
                    ))
    return violaciones
