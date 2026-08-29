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

# ---------------------------------------------------------------------------
# LA CONVENCION DE INTERPRETACION  (fijada: contravariante)
# ---------------------------------------------------------------------------
#
# Un nodo del grafo es una ETIQUETA DE TEMA, no un objeto matematico. Una
# arista entre etiquetas no denota nada hasta fijar una interpretacion
#
#     I : nodos   -> categorias
#     I : aristas -> funtores
#
# Sin ella, preguntar «¿conmuta este cuadrado?» es preguntar si dos cosas sin
# definir son iguales. Aqui se fija, y se hace comprobable.
#
# CONVENCION (A), CONTRAVARIANTE:
#
#     I(a -> b)  :  I(b) --> I(a)
#
# La arista se lee «b requiere a», y el funtor va en sentido contrario: de un
# objeto de `b` se EXTRAE uno de `a`. Es la lectura de FUNTOR OLVIDO, que es la
# familia mas universal del paisaje —toda categoria estructurada tiene uno— y
# la mejor cubierta por Mathlib.
#
# Ejemplo: `group-theory -> ring-theory` («ring-theory requiere group-theory»)
# se interpreta como un funtor `Ring -> Grp`: de un anillo se extrae un grupo.
#
# ADVERTENCIA REGISTRADA. La convencion NO cubre bien el puente
# geometria/algebra. `Spec` y las secciones globales son CONTRAVARIANTES en el
# espacio —forman una anti-equivalencia `CommRing^op ≃ AffSch`— asi que ningun
# reparto uniforme de varianza acomoda a la vez las familias algebraicas y
# esa. Bajo (A), `commutative-algebra -> algebraic-geometry` pide un funtor
# `I(algebraic-geometry) -> I(commutative-algebra)`, y los candidatos naturales
# van en el otro sentido. Se retira en vez de forzarlo.
VARIANZA = "contravariante"


@dataclass(frozen=True)
class MorfismoCertificado:
    """
    Un morfismo del grafo cuya existencia y distincion estan DEMOSTRADAS.

    `dominio` y `codominio` son las categorias que el funtor conecta, y la
    convencion exige

        dominio   == I(destino de la arista)
        codominio == I(origen  de la arista)

    Se guardan explicitamente para que `respeta_convencion` pueda comprobarlo
    en vez de confiar en que quien lo escribio lo penso bien. Los primeros seis
    pares se escribieron sin esta comprobacion y cuatro iban al reves.
    """
    origen: str            # nodo del grafo, cola de la arista
    destino: str           # nodo del grafo, punta de la arista
    construccion: str      # nombre de la construccion concreta
    dominio: str           # categoria de partida del funtor
    codominio: str         # categoria de llegada del funtor
    teorema: str           # el teorema de Lean que lo respalda
    afirma: str


#: Interpretacion de los nodos que aparecen en los certificados.
INTERPRETACION: dict[str, str] = {
    "group-theory": "Grp",
    "ring-theory": "Ring",
    "field-theory": "Field",
}


#: Morfismos certificados que SI cumplen la convencion (A).
#:
#: Ambos son familias de funtores olvido, que es exactamente lo que (A)
#: privilegia. Los cuatro retirados estan mas abajo, con el motivo.
MORFISMOS_CERTIFICADOS: list[MorfismoCertificado] = [
    MorfismoCertificado(
        "group-theory", "ring-theory", "grupo-aditivo",
        dominio="Ring", codominio="Grp",
        teorema="MorfismosGrupoAnillo.card_aditivo",
        afirma="todo anillo es grupo abeliano bajo la suma; |(ZMod 5, +)| = 5"),
    MorfismoCertificado(
        "group-theory", "ring-theory", "grupo-unidades",
        dominio="Ring", codominio="Grp",
        teorema="MorfismosGrupoAnillo.card_unidades",
        afirma="las unidades forman grupo bajo el producto; |(ZMod 5)^x| = 4"),
    MorfismoCertificado(
        "group-theory", "ring-theory", "grupo-trivial",
        dominio="Ring", codominio="Grp",
        teorema="MorfismosGrupoAnillo.card_trivial",
        afirma="el funtor constante al grupo trivial; cardinal 1"),

    MorfismoCertificado(
        "ring-theory", "field-theory", "anillo-subyacente",
        dominio="Field", codominio="Ring",
        teorema="MultiplicidadDelGrafo.card_anillo_subyacente",
        afirma="el anillo subyacente del cuerpo; |ZMod 5| = 5"),
    MorfismoCertificado(
        "ring-theory", "field-theory", "anillo-matrices",
        dominio="Field", codominio="Ring",
        teorema="MultiplicidadDelGrafo.card_anillo_matrices",
        afirma="el anillo de matrices 2x2 sobre el cuerpo; cardinal 625"),
    MorfismoCertificado(
        "ring-theory", "field-theory", "anillo-trivial",
        dominio="Field", codominio="Ring",
        teorema="MultiplicidadDelGrafo.card_anillo_trivial",
        afirma="el anillo trivial; cardinal 1"),
]


#: Lo que se retiro al fijar (A), con el motivo. No se borra: un certificado
#: retirado sigue siendo un teorema verdadero — lo que ya no es, es evidencia
#: de multiplicidad de Hom para esa arista.
RETIRADOS: list[tuple[str, str, str]] = [
    ("ring-theory", "module-theory",
     "El funtor certificado va `Ring -> Mod`, o sea I(a) -> I(b): direccion "
     "contraria a (A). En el sentido correcto, `Mod -> Ring` es la proyeccion "
     "al anillo base y no tiene multiplicidad clasica."),
    ("commutative-algebra", "algebraic-geometry",
     "Igual problema de direccion, y ademas irreparable bajo (A): Spec y las "
     "secciones globales son CONTRAVARIANTES en el espacio. Es la "
     "anti-equivalencia `CommRing^op ≃ AffSch`, no un funtor covariante."),
    ("field-extensions", "finite-fields",
     "Lo certificado eran tres OBJETOS distintos (ZMod 2, 3, 5), no tres "
     "morfismos. Es una afirmacion verdadera sobre otra cosa."),
    ("group-theory", "group-actions",
     "Las tres acciones estaban definidas sobre `ZMod 4` fijo, no como "
     "construcciones sobre un grupo arbitrario; la de paridad ni siquiera "
     "generaliza (necesita un epimorfismo G -> Z/2). Y la direccion tambien "
     "estaba invertida."),
]


def respeta_convencion(m: MorfismoCertificado) -> bool:
    """
    ¿El funtor va en el sentido que (A) exige?

    Comprueba `dominio == I(destino)` y `codominio == I(origen)`. Devuelve True
    si alguno de los nodos no esta en `INTERPRETACION` — no se puede comprobar
    lo que no esta interpretado, y decir lo contrario seria un falso negativo.
    """
    d = INTERPRETACION.get(m.destino)
    o = INTERPRETACION.get(m.origen)
    if d is None or o is None:
        return True
    return m.dominio == d and m.codominio == o


def violaciones_de_convencion() -> list[MorfismoCertificado]:
    """Los certificados que NO cumplen (A). Debe estar vacia."""
    return [m for m in MORFISMOS_CERTIFICADOS if not respeta_convencion(m)]


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
    for mc in MORFISMOS_CERTIFICADOS:
        if (graph.get_skill(mc.origen) is None
                or graph.get_skill(mc.destino) is None):
            logger.debug(f"no estan {mc.origen} o {mc.destino}; se omite")
            continue
        m = graph.add_morphism(
            mc.origen, mc.destino, MorphismType.DEPENDENCY,
            construccion=mc.construccion,
            metadata={"teorema_lean": mc.teorema, "afirma": mc.afirma,
                      "certificado": True,
                      "dominio": mc.dominio, "codominio": mc.codominio},
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


# ---------------------------------------------------------------------------
# La congruencia que NO requiere decision humana
# ---------------------------------------------------------------------------

#: Tipos de pregunta, por quien puede contestarla.
TIPO_REFUTADO = "refutado-por-lean"   # ya decidido: son distintos
TIPO_GENERICO = "generico-vs-construccion"
TIPO_COMPUESTO = "compuesto-vs-directo"


@dataclass
class Pendiente:
    """
    Un par de caminos paralelos cuya igualdad hay que decidir.

    `tipo` dice quien puede contestarla:

      · TIPO_REFUTADO  — nadie tiene que contestar: Lean ya demostro que son
        distintos (`no_hay_iso`). No es una pregunta abierta, es un resultado.
      · TIPO_GENERICO  — la arista sin nombre frente a una construccion
        certificada. Es una decision de MODELADO: ¿que representaba la arista
        generica antes de que existieran las construcciones?
      · TIPO_COMPUESTO — dos rutas distintas de la misma fuente al mismo
        destino. Es un TEOREMA sobre el dominio: ¿conmuta ese cuadrado?
    """
    origen: str
    destino: str
    camino_a: tuple[str, ...]
    camino_b: tuple[str, ...]
    tipo: str = TIPO_COMPUESTO
    afecta_colimite: bool = False      # ¿toca alguna de las 31 descomposiciones?

    @property
    def es_pregunta(self) -> bool:
        """False si Lean ya la contesto."""
        return self.tipo != TIPO_REFUTADO

    def __repr__(self) -> str:
        marca = "  [TOCA COLIMITE]" if self.afecta_colimite else ""
        return (f"Pendiente({self.tipo}: {self.origen} -> {self.destino}, "
                f"{len(self.camino_a)} vs {len(self.camino_b)} pasos){marca}")


def _describir(graph: "SkillCategory", camino: tuple[str, ...]) -> str:
    """Un camino, legible: los nodos por los que pasa y las construcciones."""
    if not camino:
        return "id"
    trozos = []
    for mid in camino:
        m = graph.get_morphism(mid)
        if m is None:
            trozos.append("?")
            continue
        c = m.metadata.get("construccion")
        trozos.append(f"{m.source_id}--[{c or m.morphism_type.name.lower()}]-->{m.target_id}")
    return "  ".join(trozos)


#: Relaciones que SI son decisiones matematicas, declaradas a mano.
#:
#: `congruencia_automatica` no las puede derivar —son teoremas o definiciones
#: sobre el dominio, no convenciones del grafo— y por eso van aqui, una a una,
#: con su motivo. Cada entrada es `(camino_a, camino_b, motivo)` donde cada
#: camino es una lista de `(origen, destino, construccion)`: se identifican por
#: CONSTRUCCION y no por id de arista, que cambia en cada carga del grafo.
RELACIONES_DECLARADAS: list[tuple[list, list, str]] = [
    (
        [("exact-sequences", "homological-algebra", "inclusion-de-aciclicos"),
         ("homological-algebra", "derived-category", "localizacion")],
        [("exact-sequences", "derived-category", "colapso")],
        "EL CUADRADO DEL PUSHOUT CONMUTA. Incluir un complejo aciclico y luego "
        "localizar da lo mismo que colapsarlo a cero, porque eso es "
        "exactamente lo que hace invertir los cuasi-isomorfismos. No es una "
        "conjetura: es la definicion de la categoria derivada, y sin "
        "declararlo `derived-category` es cota superior minimal de su propio "
        "patron y aun asi no admite co-cono",
    ),
]


def congruencia_declarada(graph: "SkillCategory") -> Congruencia:
    """
    La congruencia del sistema: la automatica mas las relaciones declaradas.

    La automatica solo recoge lo que el grafo ya afirmaba de si mismo. Las
    declaradas son afirmaciones sobre la MATEMATICA, y por eso se escriben una
    a una en `RELACIONES_DECLARADAS` con su motivo, en vez de derivarse.

    Una relacion cuyas aristas no existan en el grafo se omite en silencio: la
    congruencia describe lo que hay, no lo impone.
    """
    cong = congruencia_automatica(graph)

    def _resolver(camino) -> Optional[tuple[str, ...]]:
        ids: list[str] = []
        for origen, destino, construccion in camino:
            m = next(
                (h for h in graph.hom(origen, destino)
                 if h.metadata.get("construccion") == construccion),
                None,
            )
            if m is None:
                return None
            ids.append(m.id)
        return tuple(ids)

    for camino_a, camino_b, _motivo in RELACIONES_DECLARADAS:
        a, b = _resolver(camino_a), _resolver(camino_b)
        if a is not None and b is not None:
            cong.declarar(a, b)
    return cong


def congruencia_automatica(graph: "SkillCategory") -> Congruencia:
    """
    La parte de la congruencia que se DERIVA, sin decidir nada nuevo.

    Solo identifica aristas paralelas que difieren unicamente en el TIPO y no
    tienen construccion declarada. No es una decision matematica: es la
    semantica que el propio sistema declara en `is_preorder_leq`,

        «Los distintos tipos de morfismo (dep/an/tr) son etiquetas en el unico
         morfismo entre dos nodos, no morfismos categoricamente distintos.»

    Lo que NO hace, y no debe hacer:

      · identificar dos morfismos con CONSTRUCCION distinta — Lean demostro que
        son distintos (`no_hay_iso`), asi que declararlos iguales seria falso;
      · identificar dos CAMINOS distintos de longitud >= 2 — que dos rutas
        compuestas den el mismo morfismo es un teorema sobre el dominio, no una
        convencion. Eso sale en `pendientes_de_decidir`.
    """
    cong = Congruencia()
    vistos: set[tuple[str, str]] = set()
    for m in graph.morphisms:
        if m.morphism_type == MorphismType.IDENTITY:
            continue
        par = (m.source_id, m.target_id)
        if par in vistos:
            continue
        vistos.add(par)
        genericos = [
            h.id for h in graph.hom(*par)
            if h.morphism_type != MorphismType.IDENTITY
            and not h.metadata.get("construccion")
        ]
        for i in range(len(genericos) - 1):
            cong.declarar((genericos[i],), (genericos[i + 1],))
    return cong


def pendientes_de_decidir(
    graph: "SkillCategory",
    pattern_manager,
    colimit_builder,
    cong: Optional[Congruencia] = None,
    max_longitud: int = MAX_LONGITUD,
) -> list[Pendiente]:
    """
    Los pares de caminos paralelos que la congruencia automatica no resuelve.

    Es la lista de preguntas que hay que contestar, y esta acotada a lo que el
    sistema realmente usa: los caminos que aparecen al comprobar los co-conos
    de las descomposiciones registradas. No los 9.151 pares del grafo entero.

    `afecta_colimite=True` marca las que tocan una descomposicion con colimite
    registrado — las unicas que pueden cambiar un resultado hoy.
    """
    cong = cong if cong is not None else congruencia_automatica(graph)
    out: dict[tuple, Pendiente] = {}

    for p in pattern_manager.all_patterns:
        col = colimit_builder.get_colimit_for_pattern(p.id)
        if col is None:
            continue
        apex = col.skill_id
        for c in p.component_ids:
            cs = caminos(graph, c, apex, max_longitud)
            for i in range(len(cs)):
                for j in range(i + 1, len(cs)):
                    a, b = cs[i], cs[j]
                    if cong.iguales(a, b):
                        continue
                    clave = (c, apex, a, b)
                    if clave in out:
                        continue
                    out[clave] = Pendiente(
                        origen=c, destino=apex,
                        camino_a=a, camino_b=b,
                        tipo=_clasificar(graph, a, b),
                        afecta_colimite=True,
                    )
    return list(out.values())


def _construcciones(graph: "SkillCategory", camino: tuple[str, ...]) -> list:
    out = []
    for mid in camino:
        m = graph.get_morphism(mid)
        out.append(m.metadata.get("construccion") if m else None)
    return out


def _clasificar(graph: "SkillCategory", a: tuple[str, ...], b: tuple[str, ...]) -> str:
    """De que tipo es la pregunta — y si es una pregunta."""
    if len(a) != 1 or len(b) != 1:
        return TIPO_COMPUESTO
    ca, cb = _construcciones(graph, a)[0], _construcciones(graph, b)[0]
    if ca is not None and cb is not None:
        # Dos construcciones certificadas sobre la misma arista: Lean ya
        # demostro que NO son isomorfas. No hay nada que decidir.
        return TIPO_REFUTADO
    if ca is None or cb is None:
        return TIPO_GENERICO
    return TIPO_COMPUESTO


def informe_pendientes(
    graph: "SkillCategory",
    pendientes: list[Pendiente],
    limite: int = 12,
) -> str:
    """Las preguntas, en forma legible para quien tiene que contestarlas."""
    preguntas = [p for p in pendientes if p.es_pregunta]
    refutadas = len(pendientes) - len(preguntas)
    if not preguntas:
        return f"No queda ninguna pregunta ({refutadas} ya refutadas por Lean)."

    lineas = [
        f"{len(preguntas)} preguntas abiertas "
        f"(+{refutadas} ya refutadas por Lean: son distintos).",
        "",
    ]
    for tipo, cabecera in (
        (TIPO_COMPUESTO,
         "TEOREMAS SOBRE EL DOMINIO — ¿conmuta el cuadrado?"),
        (TIPO_GENERICO,
         "DECISIONES DE MODELADO — ¿que era la arista sin nombre?"),
    ):
        grupo = [p for p in preguntas if p.tipo == tipo]
        if not grupo:
            continue
        lineas.append(f"── {cabecera}  ({len(grupo)})")
        lineas.append("")
        for k, p in enumerate(grupo[:limite], 1):
            lineas.append(f"  {k}. ¿Son el mismo morfismo {p.origen} -> {p.destino}?")
            lineas.append(f"       (a) {_describir(graph, p.camino_a)}")
            lineas.append(f"       (b) {_describir(graph, p.camino_b)}")
            lineas.append("")
        if len(grupo) > limite:
            lineas.append(f"  … y {len(grupo) - limite} mas de este tipo.")
            lineas.append("")
    return "\n".join(lineas)
