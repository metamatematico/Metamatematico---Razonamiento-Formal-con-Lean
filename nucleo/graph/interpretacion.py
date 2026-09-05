"""
La interpretacion del grafo: que nombra cada etiqueta.

ORIGEN
------
Veredicto del autor sobre las 172 etiquetas, verificado contra Mathlib4
(commit 05322f9, 28 ago 2026). Los nombres Lean que aparecen aqui existen
literalmente en ese arbol salvo los marcados con `lean=None`.

EL CRITERIO, CORREGIDO
----------------------
La prueba que yo propuse —«¿puedo decir *sea X un ___*?»— detecta OBJETOS. La
maquinaria de Ehresmann necesita CATEGORIAS: objetos mas morfismos mas
composicion. Son dos preguntas distintas y la segunda es la que decide.

Con eso, lo que yo llamaba «TEMA» se parte en cinco cosas que no se pueden
tratar igual:

    C   objetos con morfismos canonicos          -> VERTICE
    S   propiedad que recorta una subcategoria   -> VERTICE (y la inclusion es arista)
        plena de un ambiente
    F   un funtor, una construccion o una        -> ARISTA, no vertice
        clase de flechas
    O   un objeto individual concreto            -> vertice degenerado
    T   ni objetos ni flechas                    -> fuera

EL HALLAZGO
-----------
Las 28 etiquetas marcadas `F` no son perdida: son exactamente el material del
que estan hechas las aristas. `homology`, `tensor-products`, `quotient-groups`,
`localization`, `fundamental-group` no son colecciones que se puedan colimitar
— son los funtores A LO LARGO DE LOS CUALES se colimita.

Yo predije que la mayoria serian TEMA. Es menos de un tercio (53 de 172), y de
las que descartaba, veintiocho vuelven al grafo como aristas.

DOS AVISOS QUE AFECTAN A LOS 31 COLIMITES
-----------------------------------------
1. El morfismo NO esta determinado por los objetos. `metric-spaces` con
   contracciones tiene colimites que no tiene con continuas; `Ban` con
   contracciones es completa y cocompleta, con acotadas no. Si el grafo guarda
   solo el nombre del objeto, **el colimite esta subdeterminado**.

2. Colimites en subcategorias plenas. El colimite de espacios Hausdorff en
   `Top` no es el colimite en `Haus` — hay que aplicar el reflector.
   `separation-axioms` no es decorativo: es la razon por la que un colimite
   puede salir mal.
"""
from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Optional

#: Marcas. Ver el docstring del modulo.
C = "C"   # categoria: vertice
S = "S"   # subcategoria plena: vertice, y la inclusion es arista
F = "F"   # funtor / construccion / clase de flechas: ARISTA
O = "O"   # objeto individual: vertice degenerado
T = "T"   # fuera

#: Las marcas que dan un vertice legitimo del grafo categorico.
VERTICES = frozenset({C, S})


@dataclass(frozen=True)
class Etiqueta:
    """Lo que el autor decidio que nombra una etiqueta del grafo."""
    marca: str
    objeto: str = ""        # «un objeto es…»; vacio si F, O o T
    morfismos: str = ""     # cuales son las flechas
    lean: Optional[str] = None   # nombre en Mathlib4; None = no existe
    nota: str = ""

    #: El nombre de la TEORIA, cuando no coincide con el de la categoria.
    #:
    #: `lean` contesta «que es este nodo, categoricamente»: para group-theory
    #: la respuesta es `GrpCat`, la categoria cuyos objetos son grupos. Es
    #: correcta, y es la que sostiene los colimites y la emergencia.
    #:
    #: Pero el mismo campo se estaba usando para contestar otra pregunta muy
    #: distinta: «que modulo tiene que importar Lean para una consulta sobre
    #: grupos». Ahi `GrpCat` es un desastre: `Algebra.Category.Grp.Basic` vive
    #: ARRIBA del DAG de imports de Mathlib —para construir la categoria Grp
    #: hacen falta antes subgrupos y homomorfismos— asi que ante «demuestra que
    #: un grupo de orden primo es ciclico» el sistema ofrecia la categoria Grp
    #: en vez de `Subgroup` y `MonoidHom`, e importaba el envoltorio.
    #:
    #: Medido: 10 de 76 skills con modulo apuntaban al envoltorio categorico, y
    #: explicaban 7 de las 13 dependencias que salian invertidas contra el DAG
    #: real de Mathlib (data/funtor_mathlib.json).
    #:
    #: Vacio = no hay divergencia, la teoria y la categoria se nombran igual.
    teoria: str = ""

    @property
    def es_vertice(self) -> bool:
        return self.marca in VERTICES

    @property
    def es_arista(self) -> bool:
        return self.marca == F


def nombres_de_trabajo(clave: str) -> str:
    """Los nombres Mathlib con los que se TRABAJA en este nodo.

    `teoria` si la hay, y si no `lean`. Es lo que deben consultar el prompt de
    formalizacion y el selector de modulos; `Etiqueta.lean` a secas sigue
    siendo la identidad categorica y no debe usarse para importar.
    """
    e = VEREDICTO.get(clave)
    if e:
        return e.teoria or (e.lean or "")
    # LOS NODOS DE COBERTURA NO INYECTAN NOMBRES TODAVIA, y esto se midio.
    #
    # Tienen modulo, y de ahi se dedujeron identificadores. Parecia obvio que
    # ayudarian: sin ellos, un nodo de cobertura gana sitio en el top-k y no
    # aporta nada. PERO al activarlos, contra ProofNet:
    #
    #     precision   13,5 %  ->  3,2 %      (modelo nulo: 2,9 %)
    #     cobertura   14,2 %  -> 14,0 %      (modelo nulo: 14,4 %)
    #
    # Es decir: DEJARON DE SER MEJORES QUE OFRECER LOS NOMBRES MAS COMUNES. La
    # razon es la que este proyecto lleva entera defendiendo — los 117 nombres
    # curados estan COMPROBADOS con `#check` uno a uno, y estos estan DEDUCIDOS
    # de la ruta del modulo. Deducir no es comprobar.
    #
    # SE INTENTO CERRAR ESTO CON LOS SUSTANTIVOS LEIDOS, Y NO FUNCIONA.
    #
    # El hueco es real y esta medido: el grafo inyecta 169 nombres y Mathlib
    # tiene 34 084 sustantivos —el 0,50 %— mientras la lista de hechos cubre
    # los suyos entera. La mitad que el grafo dice aportar estaba casi vacia.
    #
    # `data/sustantivos_mathlib.jsonl` cierra la parte de datos y es correcta:
    # los nombres se LEEN de la declaracion, no se deducen de la ruta, y una
    # muestra de 200 dio 200 existentes con `#check` frente al 77,4 % de los
    # deducidos. El dato esta bien.
    #
    # Lo que falla es la VIA: ofrecer aqui los sustantivos del modulo del nodo.
    # Medido contra ProofNet A VOLUMEN IGUALADO, que es la unica comparacion
    # que vale cuando cambia cuantos nombres se ofrecen:
    #
    #     volumen ~1 800-2 000   sin: 14,0 % / 17,8 %   con: 11,5 % / 16,5 %
    #     volumen ~2 800-3 100   sin:  9,5 % / 18,9 %   con:  8,5 % / 19,1 %
    #
    # Pierde en precision en los dos puntos. No es dilucion: son peores
    # nombres.
    #
    # Y el motivo se ve sin estadistica. El modulo de un nodo generado es un
    # RINCON de su area, no su centro:
    #
    #     mathlib-analysis-real -> Hyperreal.Infinite, Real.ofDigits, ...
    #
    # `Real` y `Real.sqrt` viven en `Data/Real/Basic`, no en `Analysis/Real`.
    # La clave «modulo del nodo» no lleva a los sustantivos que hacen falta.
    #
    # LO QUE ESTO NO ZANJA: si un indice de sustantivos consultado POR LA
    # CONSULTA —como `premisas.py` hace con los lemas— funcionaria. Es otro
    # mecanismo y otra medicion. La lista ya esta construida para hacerla.
    return ""


logger = logging.getLogger(__name__)

_COBERTURA: Optional[dict] = None


def _nombres_de_cobertura() -> dict:
    """id -> identificadores, de los nodos generados desde Mathlib.

    Se importa perezosamente porque el modulo generado puede no existir: el
    grafo curado funciona sin el, y su ausencia no debe romper nada.
    """
    global _COBERTURA
    if _COBERTURA is None:
        try:
            from nucleo.pillars.mathlib_taxonomy import NODOS_MATHLIB
            _COBERTURA = {n.id: list(getattr(n, "nombres", ()) or ())
                          for n in NODOS_MATHLIB}
        except Exception:
            _COBERTURA = {}
    return _COBERTURA


def _e(marca, objeto="", morfismos="", lean=None, nota="", teoria=""):
    return Etiqueta(marca, objeto, morfismos, lean, nota, teoria)


VEREDICTO: dict[str, Etiqueta] = {
    # ═══ BLOQUE 1 — las 15 de las preguntas pendientes ═══════════════════
    "algebraic-geometry": _e(
        C, "un esquema", "morfismos de espacios localmente anillados",
        "AlgebraicGeometry.Scheme"),
    "algebraic-number-theory": _e(
        C, "un cuerpo global (de numeros o de funciones)",
        "homomorfismos de cuerpos",
        "NumberField, FunctionField, NumberField.RingOfIntegers",
        "contiene a number-fields solo si es «cuerpos globales»; si es "
        "«cuerpos de numeros», los dos vertices coinciden"),
    "algebraic-topology": _e(
        C, "un CW-complejo", "aplicaciones continuas",
        "TopCat, RelCWComplex, TopCat.CWComplex",
        "si significara «espacio topologico» seria el mismo vertice que "
        "point-set-topology",
        teoria="FundamentalGroupoid, Path.Homotopy"),
    "arithmetic-geometry": _e(
        C, "un esquema separado y de tipo finito sobre Spec A_K",
        "morfismos sobre la base", "AlgebraicGeometry.Scheme + CategoryTheory.Over",
        "«un esquema sobre un anillo de enteros» es vacio: Spec Z es terminal "
        "en Sch, luego Sch/Spec Z = Sch y colapsaria sobre algebraic-geometry"),
    "cic": _e(
        C, "un contexto (equivalentemente, un tipo cerrado)", "sustituciones",
        "Type u con CategoryTheory.types"),
    "field-theory": _e(
        C, "un cuerpo", "homomorfismos de anillos, todos inyectivos",
        "Field", "no existe FieldCat"),
    "fol-deduction": _e(
        C, "una formula o un secuente", "una derivacion, modulo normalizacion",
        None,
        "NO es tema: un sistema deductivo es una categoria (Lambek). Es el "
        "domicilio de las quince tacticas, que son generadores de flechas. "
        "Mathlib no tiene sistema deductivo sintactico; si el proyecto Foundation"),
    "functors": _e(
        C, "un funtor F : C => D", "transformaciones naturales",
        "CategoryTheory.Functor, CategoryTheory.NatTrans",
        "misma categoria [C,D] que nat-trans, vista en dos capas; ninguna de "
        "las dos fija C y D"),
    "homological-algebra": _e(
        C, "un complejo de cadenas sobre una categoria abeliana",
        "morfismos de complejos", "HomologicalComplex, DerivedCategory"),
    "homological-algebra-cat": _e(
        C, "una categoria abeliana", "funtores exactos",
        "CategoryTheory.Abelian", "mismo objeto que abelian-categories"),
    "homology": _e(
        F, "", "el funtor H_* : D(A) -> grAb",
        "HomologicalComplex.homology, DerivedCategory.HomologySequence",
        "ARISTA, y ahora con DOMINIO PROPIO: sale de `derived-category` y llega "
        "a `graded-objects`. Esta bien definida precisamente porque el cociente "
        "ya invirtio lo que la homologia no distingue.\n"
        "El grupo abeliano graduado es su CODOMINIO, no lo que la etiqueta "
        "nombra; tomarlo como vertice borra la funtorialidad"),
    "limits": _e(
        F, "un cono sobre un diagrama fijo", "el funtor lim",
        "Limits.Cone, HasLimits",
        "ARISTA, y ademas reflexiva: un vertice que nombra la operacion con la "
        "que se calculan los colimites del propio grafo es confusion de nivel"),
    "operator-theory": _e(
        C, "una C*-algebra", "*-homomorfismos",
        "CStarAlgebra, ContinuousLinearMap",
        "«un operador acotado» son las FLECHAS de Hilb, no los objetos"),
    "strategy-contradiction": _e(T, nota="genera ¬¬P → P; propiedad universal: objeto inicial ⊥"),
    "tactic-exact": _e(T, nota="genera la identidad y la aplicacion de terminos"),

    # ═══ BLOQUE 2 — las 32 de los colimites ══════════════════════════════
    "abelian-categories": _e(
        C, "una categoria abeliana", "funtores exactos",
        "CategoryTheory.Abelian", "mismo objeto que homological-algebra-cat"),
    "affine-varieties": _e(
        C, "un esquema afin, Spec de una k-algebra reducida de tipo finito",
        "morfismos de esquemas", "AlgebraicGeometry.AffineScheme"),
    "algebraic-combinatorics": _e(T),
    "analytic-number-theory": _e(T),
    "commutative-algebra": _e(
        C, "un anillo conmutativo", "homomorfismos de anillos", "CommRingCat",
        teoria="CommRing, Ideal, Ideal.span"),
    "complex-analysis": _e(
        C, "un dominio de C, o una superficie de Riemann",
        "aplicaciones holomorfas", "AnalyticOnNhd, DifferentiableOn",
        "subcategoria plena de complex-geometry (dimension 1); sus clases de "
        "isomorfia son el teorema de la aplicacion de Riemann"),
    "complex-geometry": _e(
        C, "una variedad compleja", "aplicaciones holomorfas",
        "IsManifold con modelo complejo"),
    "conditional-expectation": _e(
        F, "", "el operador E[.|N] : L1 -> L1", "MeasureTheory.condExp",
        "ARISTA. Con nucleos de Markov pasa a ser estructura, no añadido"),
    "descriptive-set-theory": _e(
        C, "un espacio polaco / boreliano estandar", "aplicaciones borelianas",
        "PolishSpace, StandardBorelSpace",
        "los borelianos y proyectivos son SUBOBJETOS, no los objetos"),
    "differential-geometry": _e(
        C, "una variedad diferenciable", "aplicaciones C^k",
        "IsManifold, ContMDiff"),
    "elementary-number-theory": _e(
        O, "Z, objeto inicial de CommRing", "", "Int",
        "nombra un OBJETO, no una clase. Como vertice es un punto"),
    "enumerative-combinatorics": _e(T, nota="ambiente: FintypeCat"),
    "ergodic-theory": _e(
        C, "(Omega, mu, T) con T que preserva mu", "factores equivariantes",
        "MeasureTheory.MeasurePreserving, Ergodic"),
    "exact-sequences": _e(
        S, "un complejo aciclico", "morfismos de complejos",
        "CategoryTheory.ShortComplex.Exact"),
    "field-extensions": _e(
        C, "una extension L/k, objeto de la coslice k ↓ Field",
        "k-homomorfismos", "Algebra k L, IntermediateField"),
    "functional-analysis": _e(
        C, "un espacio vectorial topologico", "lineales continuas",
        "ContinuousLinearMap"),
    "galois-theory": _e(
        C, "una extension de Galois finita de k", "k-homomorfismos",
        "IsGalois, IntermediateField"),
    "group-theory": _e(C, "un grupo", "homomorfismos", "GrpCat",
        teoria="Group, Subgroup, MonoidHom"),
    "homotopy-theory": _e(
        C, "el par (Top, W): la categoria RELATIVA, no el cociente ya tomado",
        "las de Top, localizadas en las equivalencias debiles",
        None,
        "DECIDIDO: Top[W^-1], no hTop. La razon esta en el propio grafo: todas "
        "las aristas que salen de este vertice —homology, cohomology, "
        "fundamental-group— invierten W, luego por la propiedad universal de la "
        "localizacion factorizan por Top[W^-1], que es el vertice INICIAL con "
        "esa propiedad. No es una eleccion libre: la imponen las aristas que ya "
        "hay. Con hTop los invariantes dejan de ser conservativos (hay "
        "equivalencias debiles que no son de homotopia) y el vertice deja de "
        "estar determinado.\n"
        "Cierra ademas la arista con algebraic-topology: elegidos los "
        "CW-complejos, Whitehead mas aproximacion celular dan que "
        "hCW -> Top[W^-1] es una EQUIVALENCIA, luego la arista es comprobable, "
        "no declarativa.\n"
        "PRECIO EN LEAN: Mathlib tiene MorphismProperty, calculo de fracciones "
        "y el marco ModelCategory, pero la unica instancia concreta es la "
        "estructura inyectiva sobre complejos de cocadenas. NO hay estructura "
        "de Quillen sobre Top ni sobre SSet, asi que un colimite homotopico "
        "sobre este vertice no se enuncia hoy. El analogo que si se enuncia "
        "vive en DerivedCategory, que es el vertice homological-algebra."),
    "homotopy-type-theory": _e(
        C, "un tipo con su infinito-grupoide de caminos", "funciones y caminos",
        None,
        "IMPOSIBLE en Lean 4: Eq vive en Prop, Prop tiene irrelevancia de "
        "pruebas definicional, luego UIP es teorema y la univalencia es "
        "inconsistente. UNICA etiqueta excluida por fundamento, no por biblioteca"),
    "ideals-quotient-rings": _e(
        S, "un ideal de R (reticulo completo)",
        "inclusiones; R ↦ R/I es el funtor", "Ideal, Ideal.Quotient"),
    "measure-theory": _e(
        C, "un espacio MEDIBLE (no un espacio de medida)",
        "nucleos (CategoryTheory.Kleisli de la monada de MeasCat.Giry)",
        "MeasCat + MeasCat.Giry + CategoryTheory.Kleisli",
        "DECIDIDO. Entre los dos mundos solo hay un funtor y va en una "
        "direccion: Dirac, delta : Meas -> Stoch, identidad en objetos y fiel. "
        "No hay funtor al reves porque un nucleo no es una funcion; con "
        "funciones medibles aqui, ningun diagrama podria tener una pata funcion "
        "y otra nucleo. Fijados los nucleos en probability-theory, la "
        "compatibilidad obliga arriba.\n"
        "El objeto cambia: con funciones la medida era decoracion inerte "
        "—nada la preservaba—; con nucleos, una medida sobre X ES un morfismo "
        "1 -> X desde el espacio de un punto. Un espacio de probabilidad pasa a "
        "ser «objeto mas estado».",
        teoria="MeasurableSpace, MeasureTheory.Measure, MeasureTheory.Integrable"),
    "number-fields": _e(
        C, "un cuerpo de numeros", "Q-homomorfismos", "NumberField"),
    "ordinals": _e(C, "un ordinal", "<= (categoria delgada)", "Ordinal"),
    "point-set-topology": _e(
        C, "un espacio topologico", "continuas", "TopCat",
        teoria="TopologicalSpace, IsOpen, Continuous"),
    "probabilistic-method": _e(T),
    "probability-theory": _e(
        C, "un espacio medible con estado (= objeto mas un morfismo 1 -> X)",
        "nucleos de Markov", "ProbabilityTheory.Kernel, ProbabilityTheory.IsMarkovKernel",
        "SUBCATEGORIA ANCHA de measure-theory: mismos objetos, nucleos de "
        "Markov contenidos en los nucleos. Con funciones medibles la categoria "
        "no tiene el producto que hace falta para independencia; con nucleos es "
        "una categoria de Markov y el condicionamiento es estructura."),
    "random-variables": _e(
        F, "", "un nucleo: es flecha", "Measurable, AEEqFun, Kernel",
        "ARISTA. Con la decision de nucleos vive DENTRO de measure-theory, no "
        "entre dos categorias distintas: probability-theory es subcategoria "
        "ancha, no otro mundo."),
    "solvable-groups": _e(S, "un grupo resoluble", "homomorfismos", "IsSolvable"),
    "strategy-forward": _e(T, nota="genera encadenar hipotesis; composicion"),
    "tactic-apply": _e(T, nota="genera composicion hacia atras"),
    "tactic-rewrite": _e(T, nota="genera transporte por una igualdad; Eq.mpr"),

    # ═══ BLOQUE 3 — categorias y objetos ═════════════════════════════════
    "abelian-groups": _e(C, "un grupo abeliano", "homomorfismos", "AddCommGrpCat",
        teoria="AddCommGroup, AddSubgroup"),
    "adjunctions": _e(F, "", "un par F ⊣ G con unidad y counidad",
                      "CategoryTheory.Adjunction"),
    "banach-spaces": _e(
        C, "un espacio de Banach",
        "contracciones (o acotadas: CAMBIA los colimites)",
        "NormedSpace + CompleteSpace"),
    "bilinear-forms": _e(C, "un par (M, b) con b bilineal", "isometrias",
                         "LinearMap.BilinForm, QuadraticForm"),
    "brownian-motion": _e(O, "el proceso W, o la medida de Wiener", "",
                          "IsBrownianReal, IsPreBrownianReal"),
    "cardinal-arithmetic": _e(T, nota="el sustrato Cardinal si es categoria delgada"),
    "cat-basics": _e(C, "una categoria pequeña", "funtores", "CategoryTheory.Cat",
        teoria="CategoryTheory.Category, CategoryTheory.CategoryStruct"),
    "character-theory": _e(F, "", "chi = tr . rho, invariante de una representacion",
                           "FDRep.character"),
    "cohomology": _e(F, "", "el funtor H^*",
                     "HomologicalComplex.homology, CochainComplex"),
    "compactness": _e(S, "un espacio compacto", "continuas",
                      "CompactSpace, CompHaus",
        teoria="CompactSpace, IsCompact"),
    "conformal-maps": _e(F, "", "las flechas de las superficies de Riemann",
                         "IsConformalMap"),
    "connectedness": _e(S, "un espacio conexo", "continuas", "ConnectedSpace"),
    "covering-spaces": _e(C, "un recubrimiento p : E -> X, objeto de Top/X",
                          "aplicaciones sobre X", "IsCoveringMap"),
    "differential-forms": _e(F, "", "el funtor contravariante M ↦ Omega^*(M)",
                             "ContinuousAlternatingMap", "sin de Rham completo"),
    "differential-topology": _e(C, "una variedad suave", "aplicaciones suaves",
                                "IsManifold"),
    "differentiation": _e(F, "", "el funtor tangente T, o D", "mfderiv, TangentBundle"),
    "divisibility-gcd": _e(
        C, "un elemento de un monoide, con a | b como flecha",
        "divisibilidad: gcd es el producto, lcm el coproducto",
        "GCDMonoid, Associates"),
    "duality-theory": _e(F, "", "una equivalencia contravariante C = D^op",
                         "Module.Dual, CategoryTheory.Opposite"),
    "eigen-theory": _e(C, "un par (V, T) = un modulo sobre k[X]", "entrelazadores",
                       "Module.End, Module.End.HasEigenvalue"),
    "euclidean-geometry": _e(C, "un espacio afin euclideo", "isometrias afines",
                             "EuclideanSpace, AffineIsometry"),
    "finite-fields": _e(S, "un cuerpo finito", "homomorfismos",
                        "GaloisField, Field + Fintype"),
    "fol-metatheory": _e(C, "un lenguaje o una teoria de primer orden",
                         "interpretaciones (FirstOrder.Language.LHom)",
                         "FirstOrder.Language, FirstOrder.Language.Theory, FirstOrder.Language.LHom"),
    "free-groups": _e(S, "un grupo libre; imagen del adjunto izquierdo de Set -> Grp",
                      "homomorfismos", "FreeGroup"),
    "fundamental-group": _e(F, "", "pi_1 : Top* => Grp; sin punto base, el grupoide",
                            "FundamentalGroup, FundamentalGroupoid"),
    "generating-functions": _e(F, "", "la biyeccion (N -> R) = R[[X]]", "PowerSeries"),
    "geometric-topology": _e(C, "una variedad de dimension baja",
                             "homeomorfismos: es un GRUPOIDE", None),
    "graph-coloring": _e(F, "", "una coloracion es un homomorfismo G -> K_alpha",
                         "SimpleGraph.Coloring"),
    "graph-theory": _e(C, "un grafo simple", "homomorfismos de grafos", "SimpleGraph"),
    "group-actions": _e(C, "un G-conjunto = un funtor BG => Set",
                        "aplicaciones equivariantes",
                        "MulAction, Action"),
    "group-homomorphisms": _e(F, "", "la capa de flechas de group-theory", "MonoidHom"),
    "harmonic-analysis": _e(
        C, "un grupo abeliano localmente compacto",
        "homomorfismos continuos; Pontryagin es la autodualidad", "PontryaginDual"),
    "higher-category-theory": _e(C, "una n-categoria o una infinito-categoria",
                                 "funtores", "CategoryTheory.Bicategory, SSet.Quasicategory"),
    "hilbert-spaces": _e(C, "un espacio de Hilbert", "acotadas; es categoria daga",
                         "InnerProductSpace + CompleteSpace, ContinuousLinearMap.adjoint"),
    "holomorphic-functions": _e(F, "", "las flechas de complex-analysis", "AnalyticOnNhd"),
    "ideal-class-group": _e(F, "", "el invariante K ↦ Cl(K)", "ClassGroup"),
    "inner-product-spaces": _e(C, "un espacio con producto interno",
                               "lineales continuas", "InnerProductSpace"),
    "kan-extensions": _e(F, "", "Lan/Ran, adjuntos de la restriccion",
                         "Functor.IsLeftKanExtension"),
    "lambda-calculus": _e(C, "un tipo",
                          "los terminos modulo beta-eta: cartesiana cerrada",
                          None, "es el metanivel de Lean"),
    "large-cardinals": _e(S, "un cardinal con una propiedad de tamaño", "<=",
                          "Cardinal.IsInaccessible"),
    "lebesgue-integration": _e(F, "", "el funcional integral : L1 -> R",
                               "MeasureTheory.integral"),
    "linear-algebra": _e(C, "un espacio vectorial", "aplicaciones lineales",
                         "ModuleCat, FGModuleCat",
        teoria="Module, LinearMap, Matrix"),
    "localization": _e(F, "", "S^-1 R; y la localizacion de categorias",
                       "IsLocalization, CategoryTheory.Localization"),
    "markov-chains": _e(C, "un objeto con un endomorfismo en la categoria de nucleos",
                        "intertwiners", "ProbabilityTheory.Kernel, PMF"),
    "martingale-theory": _e(S, "un proceso adaptado con la propiedad de martingala",
                            "", "MeasureTheory.Martingale, MeasureTheory.Filtration"),
    "metric-spaces": _e(C, "un espacio metrico",
                        "Lipschitz, o isometrias, o continuas: ELIGE", "MetricSpace",
                        "la eleccion cambia que colimites existen"),
    "model-theory": _e(C, "una L-estructura",
                       "homomorfismos, o inmersiones elementales",
                       "FirstOrder.Language.Structure, FirstOrder.Language.ElementaryEmbedding"),
    "modular-arithmetic": _e(C, "Z/nZ, un diagrama indexado por (N, |)",
                             "reducciones; el limite es Z-sombrero",
                             "ZMod, ZMod.castHom"),
    "module-theory": _e(C, "un modulo sobre R", "R-lineales", "ModuleCat R"),
    "monads": _e(C, "una monada sobre C, monoide en [C,C]", "morfismos de monadas",
                 "CategoryTheory.Monad, CategoryTheory.Kleisli"),
    "nat-trans": _e(F, "", "la capa de 2-celdas de functors", "CategoryTheory.NatTrans"),
    "noetherian-rings": _e(S, "un anillo noetheriano", "homomorfismos",
                           "IsNoetherianRing"),
    "p-adic-valuations": _e(C, "un cuerpo valuado (K, v)",
                            "homomorfismos que respetan v",
                            "Valuation, Padic, PadicInt"),
    "partitions": _e(C, "una particion de n; o un diagrama de Young",
                     "orden de dominancia", "Nat.Partition, YoungDiagram"),
    "planar-graphs": _e(S, "un grafo planar", "homomorfismos", None,
                        "sin planaridad en Mathlib"),
    "polynomial-rings": _e(F, "", "R ↦ R[X], adjunto izquierdo del olvido",
                           "Polynomial, MvPolynomial"),
    "projective-geometry": _e(C, "un espacio proyectivo", "proyectividades",
                              "Projectivization"),
    "projective-injective-modules": _e(S, "un modulo proyectivo o inyectivo",
                                       "R-lineales",
                                       "Module.Projective, CategoryTheory.Injective"),
    "projective-varieties": _e(C, "Proj de un anillo graduado",
                               "morfismos de esquemas", "AlgebraicGeometry.Proj"),
    "quotient-groups": _e(F, "", "G ↦ G/N: es el conucleo, un COLIMITE",
                          "QuotientGroup"),
    "real-analysis": _e(O, "R, terminal entre los cuerpos ordenados arquimedianos",
                        "", "Real"),
    "representation-theory": _e(C, "una representacion de G = un k[G]-modulo",
                                "aplicaciones equivariantes",
                                "Rep, FDRep, Representation"),
    "riemann-integration": _e(F, "", "el operador integral (Riemann/Henstock)",
                              "BoxIntegral, intervalIntegral"),
    "riemann-zeta": _e(O, "la funcion zeta", "", "riemannZeta, LSeries"),
    "riemannian-geometry": _e(C, "una variedad riemanniana", "isometrias, o inmersiones",
                              "IsRiemannianManifold, Bundle.RiemannianMetric"),
    "ring-theory": _e(C, "un anillo", "homomorfismos", "RingCat",
        teoria="Ring, Ideal, RingHom"),
    "schemes": _e(C, "un esquema", "morfismos de esquemas",
                  "AlgebraicGeometry.Scheme", "mismo vertice que algebraic-geometry"),
    "separation-axioms": _e(S, "un espacio T0, T1, T2…",
                            "continuas; cada nivel es reflexivo", "T0Space, T2Space",
                            "es la razon por la que un colimite puede salir mal"),
    "sequences-series": _e(F, "", "una sucesion es un funtor N => X: un diagrama",
                           "Filter.Tendsto, HasSum"),
    "sequent-calculus": _e(C, "un secuente", "derivaciones", None,
                           "mismo vertice que fol-deduction"),
    "smooth-manifolds": _e(C, "una variedad suave", "aplicaciones suaves", "IsManifold"),
    "spectral-theory": _e(C, "un par (H, T) con T normal = un C(sigma(T))-modulo",
                          "entrelazadores",
                          "spectrum, ContinuousFunctionalCalculus"),
    "splitting-fields": _e(F, "", "f ↦ SplittingField f",
                           "Polynomial.SplittingField, IsSplittingField"),
    "stochastic-processes": _e(C, "un proceso adaptado = un funtor desde el tiempo",
                               "", "MeasureTheory.Filtration, MeasureTheory.Adapted"),
    "subgroups-cosets": _e(C, "un subgrupo de G; forman un reticulo completo",
                           "inclusiones; G/H es el G-conjunto asociado",
                           "Subgroup, QuotientGroup"),
    "sylow-theory": _e(C, "un p-subgrupo de Sylow de G",
                       "conjugaciones: es un GRUPOIDE CONEXO (2.º teorema)",
                       "Sylow, Sylow.mulAction"),
    "symplectic-geometry": _e(C, "una variedad simplectica", "simplectomorfismos",
                              None, "solo SymplecticGroup"),
    "tensor-products": _e(F, "", "el bifuntor tensor, definido por coigualador",
                          "TensorProduct"),
    "topos-theory": _e(C, "un topos", "morfismos geometricos",
                       "CategoryTheory.Classifier, CategoryTheory.Sheaf", "sin topos elemental"),
    "triangle-geometry": _e(C, "un 2-simplex afin", "semejanzas",
                            "Affine.Triangle, EuclideanGeometry"),
    "turing-machines": _e(C, "una maquina de Turing", "simulaciones",
                          "Turing.TM0, Turing.TM1"),
    "ultraproducts": _e(F, "", "producto ultrafiltrado: colimite filtrado",
                        "FirstOrder.Language.Ultraproduct, Filter.Germ"),
    "unique-factorization": _e(S, "un dominio de factorizacion unica", "homomorfismos",
                               "UniqueFactorizationMonoid"),

    # ═══ VERTICES AÑADIDOS — no estaban entre las 172 ════════════════════
    #
    # El grafo detecto un vertice que FALTA, no un vertice malo, y lo etiqueto
    # con el nombre del invariante que ese vertice calcula —`homology`— porque
    # era la etiqueta mas cercana disponible.
    "derived-category": _e(
        C, "un complejo modulo cuasi-isomorfismo",
        "los de la localizacion",
        "DerivedCategory C, DerivedCategory.Q",
        "EL APICE QUE FALTABA de las cuatro descomposiciones que apuntaban a "
        "`homology`. Es el cociente `homological-algebra` modulo "
        "`exact-sequences`: el pushout que mata los complejos aciclicos, que es "
        "literalmente lo que hace la localizacion por cuasi-isomorfismos.\n"
        "Las tres patas son tres cosas DISTINTAS —la inclusion de los "
        "aciclicos, el colapso, y las cadenas singulares C_* desde "
        "`algebraic-topology`, que manda equivalencias debiles a "
        "cuasi-isomorfismos y por tanto desciende al cociente—. Ninguna de las "
        "tres es la homologia: por eso la descomposicion deja de ser circular y "
        "pasa a ser un teorema.\n"
        "La variante intermedia es HomotopyCategory.quotient; la sucesion "
        "exacta larga que justifica la pata de `exact-sequences` esta en "
        "DerivedCategory/HomologySequence.lean"),
    "sheafed-space-complexes": _e(
        C, "un par (X, K): espacio topologico con un haz de complejos de "
           "grupos abelianos",
        "un par (f, phi): f : X -> Y continua mas phi : K_Y -> f_* K_X",
        "AlgebraicGeometry.SheafedSpace (CochainComplex AddCommGrp Z)",
        "EL APICE QUE FALTABA de {arithmetic-geometry, homological-algebra, "
        "point-set-topology}. Donde vive la cohomologia de haces ANTES de "
        "tomar cohomologia.\n"
        "Las tres patas, todas covariantes: el HAZ CONSTANTE desde "
        "point-set-topology (X |-> (X, Z_X), funtorial porque f^-1 Z_Y = Z_X, "
        "luego phi es la identidad — la pata mas pobre y por eso la que fija "
        "la normalizacion); el OLVIDO a espacio anillado desde "
        "arithmetic-geometry (X |-> (X, O_X en grado 0), via la torre "
        "AlgebraicGeometry.Scheme -> LocallyRingedSpace -> SheafedSpace que Mathlib ya tiene); y "
        "la FIBRA SOBRE EL PUNTO desde homological-algebra (K |-> (pt, K)), "
        "plenamente fiel, que es la pata que explica por que el patron no es "
        "trivial: identifica el algebra homologica pura con la cohomologia de "
        "haces sobre el espacio terminal.\n"
        "El marco esta en Mathlib parametrizado por una categoria cualquiera; "
        "lo que NO esta es la version derivada, invirtiendo cuasi-isomorfismos "
        "fibra a fibra.\n"
        "PRIMER OBJETO DE ORDEN IRREDUCIBLE 3 DEL SISTEMA."),
    "graded-objects": _e(
        C, "un objeto graduado (grupos abelianos graduados)",
        "morfismos graduados", "CategoryTheory.GradedObject",
        "el CODOMINIO de H_*. Tampoco estaba entre las 172: la arista `homology` "
        "no tenia donde llegar"),

    # ═══ BLOQUE 3 — las que son tema, con su residuo ═════════════════════
    "algorithm-analysis": _e(T, nota="una disciplina"),
    "canonical-forms": _e(T, nota="clasificacion; el esqueleto de eigen-theory"),
    "circle-geometry": _e(T, nota="un capitulo; objetos en EuclideanGeometry.Sphere"),
    "compactness-theorem": _e(T, nota="un teorema; Theory.isSatisfiable_iff_isFinitelySatisfiable"),
    "computability-theory": _e(T, nota="una rama; los grados de Turing son orden parcial: TuringDegree"),
    "computational-complexity": _e(T, nota="una rama; las reducciones son un preorden"),
    "contour-integration": _e(T, nota="una tecnica; el emparejamiento H_1 x H^1_dR -> C"),
    "convex-optimization": _e(T, nota="una tecnica; conjuntos convexos con afines"),
    "diophantine-equations": _e(T, nota="familia de problemas; X(Z) es el funtor de puntos"),
    "discrete-optimization": _e(T, nota="una tecnica"),
    "extremal-combinatorics": _e(T, nota="una rama"),
    "forcing": _e(T, nota="una tecnica; el topos de prehaces sobre P. Flypitch quedo en Lean 3"),
    "formal-verification": _e(T, nota="una actividad"),
    "inclusion-exclusion": _e(T, nota="una tecnica; inversion de Mobius: IncidenceAlgebra"),
    "incompleteness": _e(T, nota="dos teoremas; en Foundation (Lean 4), no en Mathlib"),
    "lean-kernel": _e(T, nota="un programa concreto"),
    "limit-theorems": _e(T, nota="teoremas (LGN, TCL)"),
    "limits-continuity": _e(T, nota="dos nociones; continuidad = ser morfismo"),
    "linear-programming": _e(T, nota="una tecnica; la dualidad LP"),
    "matching-theory": _e(T, nota="familia de problemas; SimpleGraph.Subgraph.IsMatching"),
    "np-completeness": _e(T, nota="una clase de problemas"),
    "pde-techniques": _e(T, nota="tecnicas"),
    "prime-factorization": _e(T, nota="un teorema; UniqueFactorizationMonoid"),
    "prime-number-theorem": _e(T, nota="un teorema; en PrimeNumberTheoremAnd, no en Mathlib"),
    "proof-theory": _e(T, nota="una rama; su objeto es la categoria de fol-deduction"),
    "quadratic-residues": _e(T, nota="un capitulo; el simbolo de Legendre es un caracter: legendreSym"),
    "ramsey-theory": _e(T, nota="una rama; sin numeros de Ramsey en Mathlib"),
    "recursion-theory": _e(T, nota="sinonimo de computability-theory"),
    "residue-theorem": _e(T, nota="un teorema; via Complex.integral_circle"),
    "universal-properties": _e(T, nota="el mecanismo, no un tema; Functor.Representable, IsInitial"),
    "variational-methods": _e(T, nota="tecnicas; puntos criticos de funcionales"),
    "yoneda-lemma": _e(T, nota="un lema; el funtor y si es objeto: CategoryTheory.yoneda"),
    "zfc-axioms": _e(T, nota="enunciados; el universo V si es categoria: ZFSet"),

    # ═══ Las tacticas y estrategias restantes ════════════════════════════
    "tactic-calc": _e(T, nota="genera cadenas transitivas; composicion asociativa"),
    "tactic-simp": _e(T, nota="reescritura confluente; cociente por una congruencia"),
    "tactic-ring": _e(T, nota="decision en el anillo conmutativo libre; libertad de Z[X]"),
    "tactic-omega": _e(T, nota="decision en aritmetica de Presburger"),
    "tactic-induction": _e(T, nota="el recursor; algebra inicial"),
    "tactic-aesop": _e(T, nota="busqueda de pruebas"),
    "strategy-inductive": _e(T, nota="el recursor; algebra inicial"),
    "strategy-cases": _e(T, nota="eliminacion de la disyuncion; coproducto"),
    "strategy-construction": _e(T, nota="introduccion del existencial; objeto que representa el funtor"),
    "strategy-backward": _e(T, nota="descomponer el objetivo; levantamiento contra la meta"),
}


#: Etiquetas que nombran la MISMA categoria. Un colimite sobre vertices
#: duplicados sale degenerado.
DUPLICADOS: list[tuple[str, list[str]]] = [
    ("Sch", ["algebraic-geometry", "schemes", "arithmetic-geometry"]),
    ("categoria abeliana", ["homological-algebra-cat", "abelian-categories"]),
    ("variedad suave", ["differential-geometry", "differential-topology",
                        "smooth-manifolds"]),
    ("Top", ["point-set-topology", "algebraic-topology"]),
    ("cuerpo de numeros", ["algebraic-number-theory", "number-fields"]),
    ("categoria deductiva", ["fol-deduction", "sequent-calculus", "proof-theory"]),
    ("computabilidad", ["computability-theory", "recursion-theory"]),
    ("[C,D] en dos capas", ["functors", "nat-trans"]),
]

#: Etiquetas cuyos MORFISMOS siguen sin fijar. La eleccion cambia QUE
#: colimites existen, no como se calculan, asi que no la puede tomar el codigo.
#:
#: `measure-theory`, `probability-theory` y `homotopy-theory` salieron de esta
#: lista al decidirse (ver sus notas). Las dos que quedan no participan hoy en
#: ninguna descomposicion, asi que no bloquean nada — pero lo haran en cuanto
#: entren.
MORFISMO_SIN_FIJAR: list[str] = [
    "metric-spaces",    # Lipschitz / isometrias / continuas
    "banach-spaces",    # contracciones (cocompleta) / acotadas (no)
]


# ---------------------------------------------------------------------------
# La regla que decide si un colimite existe
# ---------------------------------------------------------------------------
#
# Mira la FORMA del diagrama, no su contenido. En los patrones del sistema la
# forma se lee directamente de `index_morphisms`:
#
#   FORMA COPRODUCTO — diagrama discreto, sin enlaces distinguidos.
#       Existe en los dos vertices decididos, sin condiciones. En nucleos
#       sobrevive siempre porque Hom(coproducto de A_i, X) = producto de
#       Hom(A_i, TX). No hay nada que decidir.
#
#   FORMA PUSHOUT O COIGUALADOR — hay enlaces distinguidos.
#       · en `measure-theory`: existe si y solo si las flechas del diagrama son
#         DETERMINISTAS, y entonces se calcula en Meas exactamente como antes.
#         Razon: delta es el funtor libre de la adjuncion de CategoryTheory.Kleisli, luego es
#         adjunto por la izquierda, luego preserva TODOS los colimites; y Meas
#         es cocompleta por ser topologica sobre Set. Con patas genuinamente
#         estocasticas no hay garantia: la categoria de nucleos no es cocompleta.
#       · en `homotopy-theory`: NO EXISTE NUNCA. Ni hTop ni Top[W^-1] tienen
#         pushouts — esa carencia es la razon historica de las categorias de
#         modelos. Lo que si existe es el colimite HOMOTOPICO, que es otra
#         operacion, no un caso particular de esta.
#
# Consecuencia para el codigo: sobre el vertice homotopico y forma pushout, el
# resultado correcto no es «este colimite vale X» sino «este vertice no admite
# la operacion», y la maquinaria debe decirlo con esas palabras.

FORMA_COPRODUCTO = "coproducto"
FORMA_PUSHOUT = "pushout-o-coigualador"

#: Vertices donde la forma pushout NO admite colimite en absoluto.
SIN_PUSHOUT: frozenset[str] = frozenset({"homotopy-theory"})

#: Vertices donde la forma pushout existe solo si las flechas son deterministas.
PUSHOUT_SI_DETERMINISTA: frozenset[str] = frozenset({
    "measure-theory", "probability-theory",
})


def forma_de(pattern) -> str:
    """La forma del diagrama: coproducto si es discreto, pushout si no."""
    return FORMA_COPRODUCTO if not pattern.index_morphisms else FORMA_PUSHOUT


def admite_colimite(pattern, apex: str) -> tuple[bool, str]:
    """
    ¿Admite este vertice la operacion que el patron le pide?

    Returns:
        (admite, motivo). `admite=False` no significa «el colimite no existe»
        sino «este vertice no admite la operacion», que es distinto y hay que
        decirlo con esas palabras.
    """
    forma = forma_de(pattern)
    if forma == FORMA_COPRODUCTO:
        return True, "forma coproducto: existe sin condiciones"
    if apex in SIN_PUSHOUT:
        return False, (
            f"«{apex}» no admite la operacion: ni hTop ni Top[W^-1] tienen "
            "pushouts. Lo que existe es el colimite HOMOTOPICO, que es otra "
            "operacion, no un caso particular de esta"
        )
    if apex in PUSHOUT_SI_DETERMINISTA:
        return True, (
            f"«{apex}»: forma pushout, existe solo si las flechas del diagrama "
            "son deterministas; entonces se calcula en Meas como antes"
        )
    return True, "forma pushout: sin restriccion declarada para este vertice"


# ---------------------------------------------------------------------------
# Degradaciones: dejan de ser vertices y pasan a la capa de flechas
# ---------------------------------------------------------------------------
#
# No se borran: se DEGRADAN. Nada se pierde si se reparten sus aristas
# incidentes segun la direccion.
#
#   aristas que ENTRAN  (X -> etiqueta)  -> atributo de X, un predicado
#   aristas que SALEN   (etiqueta -> Y)  -> un funtor
#
# `limits` fallaba no por estar mal poblado sino porque nombraba la operacion
# con la que se calcula el propio grafo. `nat-trans` es el mismo caso y no una
# fusion: `functors` y `nat-trans` no son dos vertices repetidos, son el nivel
# de objetos y el de flechas de [C,D].

DEGRADADAS: dict[str, dict[str, str]] = {
    "limits": {
        "entrantes": "atributo del vertice: «X tiene limites de forma J». "
                     "En Lean, HasLimitsOfShape J X — un predicado, no un vertice",
        "salientes": "el funtor lim : [J,Y] => Y, adjunto por la derecha de la "
                     "diagonal. En Lean, CategoryTheory.Limits.lim con la "
                     "adjuncion constLimAdj; su dual es colimConstAdj",
    },
    "nat-trans": {
        "entrantes": "atributo: la capa de 2-celdas de [C,D]",
        "salientes": "la capa de morfismos de `functors`, no un vertice propio",
    },
}


# ---------------------------------------------------------------------------
# Fusiones: etiquetas que nombran la misma categoria
# ---------------------------------------------------------------------------
#
# CRITERIO DE SUPERVIVENCIA: sobrevive la que nombra los OBJETOS, no la rama.
# Donde ninguna candidata nombra objetos, sobrevive la mas fundacional y queda
# anotado que el nombre es de rama — suciedad, no problema.
#
# Las retiradas NO se borran: quedan como ALIAS del superviviente. Si se
# borraran, las 172 dejarian de mapear sobre el grafo y se perderia la
# trazabilidad de por que desaparecieron.

FUSIONES: dict[str, str] = {
    # retirada                      -> superviviente
    "homological-algebra-cat": "abelian-categories",
    "differential-geometry": "smooth-manifolds",
    "differential-topology": "smooth-manifolds",
    "sequent-calculus": "fol-deduction",
    "proof-theory": "fol-deduction",
    "recursion-theory": "computability-theory",
    "schemes": "algebraic-geometry",
    "algebraic-topology": "point-set-topology",
}

#: Motivo por el que sobrevive cada uno, y la suciedad que queda.
NOTA_FUSION: dict[str, str] = {
    "abelian-categories": "nombra los objetos; homological-algebra-cat nombra la rama",
    "smooth-manifolds": "nombra los objetos; las otras dos nombran ramas",
    "fol-deduction": "ninguna candidata nombra los objetos de la categoria "
                     "deductiva; sobrevive la mas fundacional. El nombre sigue "
                     "siendo de rama: suciedad anotada",
    "computability-theory": "ambas son T; la fusion es de etiquetas, no de vertices",
    "algebraic-geometry": "el criterio pedia `schemes`, que nombra los objetos, "
                          "pero `algebraic-geometry` es el que aparece en las "
                          "descomposiciones; se conserva ese y `schemes` queda "
                          "como alias. Suciedad anotada",
    "point-set-topology": "ninguna nombra los objetos; sobrevive la mas "
                          "fundacional. Ver AVISO_TOP",
}

#: El documento separa `algebraic-topology` = CW-complejos (subcategoria plena)
#: de `point-set-topology` = Top. La regla operativa permite fusionar porque
#: NINGUNA descomposicion usa la distincion — pero la distincion es real. Si
#: alguna descomposicion futura la usa, hay que deshacer esta fusion y pasarla
#: a SUBCATEGORIA_PLENA.
AVISO_TOP = ("fusion permitida por la regla —ninguna descomposicion usa la "
             "distincion CW ⊊ Top— pero la distincion es matematicamente real")


# ---------------------------------------------------------------------------
# Las que NO se fusionan: ambiente mas subcategoria plena
# ---------------------------------------------------------------------------
#
# LA REGLA: fusiona SALVO que alguna descomposicion use precisamente esa
# distincion. Si la usa, no fusiones — convierte el par en ambiente mas
# subcategoria plena con una arista de inclusion, que es lo que realmente son.
# Retirar la etiqueta y meter la inclusion arreglan igual el colimite; lo que
# no se puede es hacer las dos cosas.
#
# MEDIDO: las cuatro descomposiciones que la fusion iba a «arreglar» son
# exactamente las cuatro que USAN la distincion, y en las cuatro uno de los
# miembros es el APICE y el otro una COMPONENTE. Fusionar colapsaria el apice
# dentro de su propio patron y el colimite pasaria a ser trivial.

SUBCATEGORIA_PLENA: dict[str, tuple[str, str]] = {
    # subcategoria            -> (ambiente, que la recorta)
    "arithmetic-geometry": (
        "algebraic-geometry",
        "esquemas separados y de tipo finito sobre Spec O_K, dentro de Sch"),
    "number-fields": (
        "algebraic-number-theory",
        "cuerpos de numeros, dentro de los cuerpos globales"),
}


# ---------------------------------------------------------------------------
# El aviso: una fusion es un COCIENTE del diagrama indice
# ---------------------------------------------------------------------------
#
# Identificar dos vertices no es solo rellenar un hueco: es tomar un cociente
# del diagrama, y el colimite del cociente NO es el colimite del original.
# Donde las dos etiquetas fusionadas coexistian en el mismo diagrama, lo que
# antes era un COPRODUCTO pasa a ser un COIGUALADOR, y el valor se mueve aunque
# el colimite ya existiera y estuviera bien.
#
# Por eso la comprobacion no va sobre las que se arreglan, sino sobre las que
# contienen A LA VEZ los dos miembros de un par fusionado: esas cambian de
# valor y hay que RECALCULARLAS, no celebrarlas.

def cambia_de_valor(pattern, apex: str) -> list[tuple[str, str]]:
    """
    Los pares fusionados que coexisten en esta descomposicion.

    No vacia = el colimite cambia de valor al fusionar, aunque ya existiera y
    fuera correcto. Hay que recalcular.
    """
    nodos = set(pattern.component_ids) | {apex}
    fuera: list[tuple[str, str]] = []
    for retirada, superviviente in FUSIONES.items():
        if retirada in nodos and superviviente in nodos:
            fuera.append((retirada, superviviente))
    return fuera


def resolver(etiqueta: str) -> str:
    """La etiqueta que sobrevive: sigue los alias hasta el final."""
    visto = set()
    while etiqueta in FUSIONES and etiqueta not in visto:
        visto.add(etiqueta)
        etiqueta = FUSIONES[etiqueta]
    return etiqueta


def vertices_tras_fusionar() -> list[str]:
    """Los vertices que quedan: los que sobreviven y no fueron degradados."""
    return sorted({
        resolver(k) for k, v in VEREDICTO.items()
        if v.es_vertice and k not in DEGRADADAS
    })


# ---------------------------------------------------------------------------
# El apice que faltaba
# ---------------------------------------------------------------------------
#
# Cuatro descomposiciones apuntaban a `homology`, que es una ARISTA. El
# diagnostico NO era el de `limits`:
#
#   · `limits` aparecia como COMPONENTE y el patron estaba mal poblado —habia
#     un objeto donde debia haber una operacion—, luego las descomposiciones
#     que lo contenian eran falsas como enunciados y hay que regenerarlas;
#   · `homology` aparece como APICE con componentes legitimas, forma correcta y
#     co-cono bien formado. Borrarlas seria tirar cuatro detecciones ciertas por
#     un nombre mal puesto en el vertice de llegada.
#
# El apice correcto es el COCIENTE `homological-algebra` modulo
# `exact-sequences` — la categoria derivada:
#
#       exact-sequences  ──inclusion──>  homological-algebra
#              │                                │
#          colapso                              │
#              v                                v
#              0        ──────────────────>    D(A)
#
# Y `homology` sale de ahi: H_* : D(A) -> grAb.

#: Los vertices que NO estaban entre las 172 del veredicto. El grafo los pedia
#: —una descomposicion apuntaba a un sitio que no existia como vertice— y los
#: habia etiquetado con lo mas cercano disponible.
#:
#: Se mantienen aparte para que la guardia sobre el veredicto del autor siga
#: siendo exacta: 172 etiquetas suyas, mas lo que el grafo obligue a añadir.
VERTICES_ANADIDOS: frozenset[str] = frozenset({
    "derived-category", "graded-objects", "sheafed-space-complexes",
})

#: Etiquetas del veredicto que YA NO SON VERTICES del grafo: se degradaron a
#: flechas y se retiraron. Siguen en la tabla —el veredicto es un dato
#: editorial y borrarlas perderia la trazabilidad de por que se fueron— pero no
#: hay que buscarlas en el grafo.
#:
#: `homology` y `cohomology` son FUNTORES entre categorias, y un funtor es una
#: flecha:
#:
#:     H_*, H^* : derived-category -> graded-objects
#:
#: Estan bien definidos precisamente porque el cociente ya invirtio lo que la
#: homologia no distingue. La cohomologia es la misma flecha con el signo de la
#: graduacion cambiado, no otro vertice.
DEGRADADAS_A_FLECHA: frozenset[str] = frozenset({
    "homology", "cohomology",
})

#: Cuantas etiquetas publico el autor.
LAS_DEL_AUTOR = 172


APICE_FALTANTE: dict[str, dict] = {
    "homology": {
        "apice_correcto": "derived-category",
        "codominio": "graded-objects",
        "componentes": ["algebraic-topology", "exact-sequences",
                        "homological-algebra"],
        "patas": {
            "exact-sequences": "la inclusion de los aciclicos, y el colapso",
            "homological-algebra": "el cociente por cuasi-isomorfismos",
            "algebraic-topology": "las cadenas singulares C_*, que mandan "
                                  "equivalencias debiles a cuasi-isomorfismos",
        },
    },
}

#: LO QUE EL TEST ENCONTRO, y no estaba previsto.
#:
#: El test estructural que decide entre las lecturas (a) y (b) —«¿emite
#: `exact-sequences` alguna flecha, o solo recibe?»— lo pasa: emite tres. No es
#: una cospan, luego la deteccion no es vacia y la lectura del cociente
#: sobrevive.
#:
#: Pero al mirar CUALES emite aparece que la arista que el pushout necesita
#: —`exact-sequences -> homological-algebra`, la inclusion de los aciclicos—
#: NO EXISTE en el grafo. Emite a `abelian-categories`, a `homology` y a
#: `tactic-ring`; y recibe solo de `module-theory`.
#:
#: O sea: al grafo le falta un vertice Y una arista. Lo primero ya se sabia;
#: lo segundo es nuevo.
ARISTA_FALTANTE: tuple[str, str, str] = (
    "exact-sequences", "homological-algebra",
    "la inclusion de los complejos aciclicos, que es una de las dos patas del "
    "pushout que define la categoria derivada",
)

#: Y una prediccion que NO se cumple. Se esperaba que las cuatro variantes se
#: distinguieran por el nivel al que toman el cociente (Ch -> K, K -> D) y que
#: al regenerarlas colapsaran a dos. No: son UN patron de tres componentes mas
#: sus tres subconjuntos de dos, que es lo que emite el detector desde que se
#: habilito la multiplicidad. No hay dos cocientes ahi, hay uno y su conjunto
#: potencia.
NO_SON_DOS_COCIENTES = (
    "las cuatro son {alg-top, exact-seq, hom-alg} y sus tres subconjuntos de "
    "dos, no cuatro niveles de cociente"
)


# ---------------------------------------------------------------------------
# Patrones espurios: no les falta apice, les falta poder tenerlo
# ---------------------------------------------------------------------------
#
# Un hueco sin cotas superiores no significa siempre «falta un concepto». A
# veces significa que el patron no puede tener colimite, y entonces buscarle
# apice es perder el tiempo. Hay que retirarlo, como se retiraron los cuatro de
# `homological-algebra-cat`.

PATRONES_ESPURIOS: dict[tuple[str, ...], str] = {
    ("algebraic-combinatorics", "group-theory", "module-theory"): (
        "`algebraic-combinatorics` NO ES UNA CATEGORIA: esta marcada T porque "
        "no nombra objetos —nadie dice «sea X una combinatoria algebraica»—. "
        "Un co-cono exige un funtor desde CADA componente; sin objetos no hay "
        "funtor, sin funtor no hay pata, y con dos patas de tres no hay "
        "colimite. Lo que el sistema detecto es co-ocurrencia bibliografica "
        "—funciones simetricas, tablas de Young y caracteres del simetrico "
        "aparecen juntos en los tres sitios—: tema compartido, no vertice "
        "compartido"
    ),
    ("algebraic-geometry", "functors", "homological-algebra", "limits",
     "operator-theory"): (
        "dos motivos independientes, cualquiera basta. (a) Contiene `limits`, "
        "ya degradado: esta en el lote de los que hay que regenerar. (b) Lo "
        "que queda tampoco se pega: el unico apice concebible es el mundo no "
        "conmutativo —categorias dg o estables, X |-> Perf(X)— y ahi fallan "
        "dos patas de cuatro. Un objeto de `homological-algebra` es un "
        "complejo, no una categoria; uno de `functors` es un funtor, no una "
        "categoria. Se les pueden forzar patas —el algebra dg de "
        "endomorfismos, el colage— pero ninguna es canonica, y una pata "
        "forzada no es una pata. La de `algebraic-geometry` si existe pero es "
        "CONTRAVARIANTE, el caso Spec. Con dos patas ausentes y una invertida "
        "lo que hay es una cota superior en la literatura, no un co-cono"
    ),
}

#: El vecino verdadero del primer espurio. Sustituyendo la etiqueta T por el
#: vertice que si nombra objetos, el apice existe y ya tenia etiqueta.
VECINO_VERDADERO: dict[tuple[str, ...], dict] = {
    ("algebraic-combinatorics", "group-theory", "module-theory"): {
        "sustituir": ("algebraic-combinatorics", "group-actions"),
        "apice": "representation-theory",
        "lectura": "categoria TOTAL sobre grupos variables: objeto (G, M), "
                   "morfismo (phi, f) con phi : G -> H y f : M -> Res_phi N "
                   "equivariante",
        "patas": {
            "group-actions": "linealizacion, (G, X) |-> (G, k[X]) — en "
                             "Mathlib es Rep.linearization",
            "group-theory": "representacion regular, G |-> (G, k[G]); sobre "
                            "un morfismo phi, su extension lineal",
            "module-theory": "fibra sobre el grupo trivial, M |-> (1, M): un "
                             "modulo es una representacion del grupo trivial",
        },
        "mathlib": "Rep k G para G FIJO; la version sobre G variable es la "
                   "construccion de Grothendieck de la restriccion y hay que "
                   "montarla a mano",
    },
}

#: `functors` sobra en el patron de `sheafed-space-complexes`, y se comprueba.
#:
#: La cuarta pata seria la HACIFICACION, P |-> (X, P^++), y solo existe si
#: `functors` se instancia como PREHACES, [Abiertos(X)^op, Ch(Ab)]. Sin fijar
#: dominio y codominio, `functors` nombra `Cat` y no hay pata.
#:
#: MEDIDO: la variante de cuatro componentes registra colimite, pero los unicos
#: caminos de `functors` al apice son COMPUESTOS Y PASAN POR SUS PROPIAS
#: CO-COMPONENTES (functors -> algebraic-geometry -> arithmetic-geometry -> apice,
#: y functors -> homological-algebra -> apice). Eso no es una pata: es la
#: enfermedad del vertice de segundo nivel, la misma de `limits` y la misma de
#: `homological-algebra-cat`.
FUNCTORS_SOBRA = (
    "sheafed-space-complexes",
    "la pata de `functors` seria la hacificacion y solo existe instanciandolo "
    "como prehaces; sin eso sus unicos caminos al apice pasan por sus propias "
    "co-componentes",
)


#: Restricciones que hay que imponer si la descomposicion usa ciertas
#: operaciones. No son opcionales: son condiciones de existencia.
RESTRICCIONES: dict[str, str] = {
    "producto": "si la descomposicion usa el producto (independencia, tensor "
                "de nucleos), restringir a nucleos S-FINITOS. La composicion y "
                "su asociatividad valen sin hipotesis (Kernel.comp_assoc no las "
                "pide), pero compProd_apply y prod_apply' exigen IsSFiniteKernel",
    "condicionamiento": "si usa condicionamiento o inversion bayesiana, "
                        "restringir los objetos a BORELIANOS ESTANDAR, que es "
                        "donde existe la desintegracion. Eso explica la arista "
                        "con descriptive-set-theory: no es decorativa, es la "
                        "condicion de existencia",
}


def marca(etiqueta: str) -> Optional[str]:
    e = VEREDICTO.get(etiqueta)
    return e.marca if e else None


def vertices() -> list[str]:
    """Las etiquetas que son vertices legitimos del grafo categorico."""
    return sorted(k for k, v in VEREDICTO.items() if v.es_vertice)


def aristas() -> list[str]:
    """Las etiquetas que son FUNTORES: aristas, no vertices."""
    return sorted(k for k, v in VEREDICTO.items() if v.es_arista)


def recuento() -> dict[str, int]:
    from collections import Counter
    return dict(Counter(v.marca for v in VEREDICTO.values()))
