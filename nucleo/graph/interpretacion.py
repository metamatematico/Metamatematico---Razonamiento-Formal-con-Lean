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

    @property
    def es_vertice(self) -> bool:
        return self.marca in VERTICES

    @property
    def es_arista(self) -> bool:
        return self.marca == F


def _e(marca, objeto="", morfismos="", lean=None, nota=""):
    return Etiqueta(marca, objeto, morfismos, lean, nota)


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
        "TopCat, RelCWComplex, CWComplex",
        "si significara «espacio topologico» seria el mismo vertice que "
        "point-set-topology"),
    "arithmetic-geometry": _e(
        C, "un esquema separado y de tipo finito sobre Spec A_K",
        "morfismos sobre la base", "Scheme + CategoryTheory.Over",
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
        "CategoryTheory.Functor, NatTrans",
        "misma categoria [C,D] que nat-trans, vista en dos capas; ninguna de "
        "las dos fija C y D"),
    "homological-algebra": _e(
        C, "un complejo de cadenas sobre una categoria abeliana",
        "morfismos de complejos", "HomologicalComplex, DerivedCategory"),
    "homological-algebra-cat": _e(
        C, "una categoria abeliana", "funtores exactos",
        "CategoryTheory.Abelian", "mismo objeto que abelian-categories"),
    "homology": _e(
        F, "", "el funtor H_*", "HomologicalComplex.homology",
        "ARISTA. El grupo abeliano graduado es el CODOMINIO de H_*, no lo que "
        "la etiqueta nombra; tomarlo como vertice borra la funtorialidad"),
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
        C, "un anillo conmutativo", "homomorfismos de anillos", "CommRingCat"),
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
        "MeasurePreserving, Ergodic"),
    "exact-sequences": _e(
        S, "un complejo aciclico", "morfismos de complejos",
        "ShortComplex.Exact"),
    "field-extensions": _e(
        C, "una extension L/k, objeto de la coslice k ↓ Field",
        "k-homomorfismos", "Algebra k L, IntermediateField"),
    "functional-analysis": _e(
        C, "un espacio vectorial topologico", "lineales continuas",
        "ContinuousLinearMap"),
    "galois-theory": _e(
        C, "una extension de Galois finita de k", "k-homomorfismos",
        "IsGalois, IntermediateField"),
    "group-theory": _e(C, "un grupo", "homomorfismos", "GrpCat"),
    "homotopy-theory": _e(
        C, "un espacio, con las equivalencias debiles invertidas",
        "clases de homotopia",
        "FundamentalGroupoid, SSet, Quasicategory",
        "decidir si es Top localizada o su categoria de homotopia: cambia el colimite"),
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
        C, "un espacio de medida", "funciones medibles",
        "MeasureSpace, Measurable"),
    "number-fields": _e(
        C, "un cuerpo de numeros", "Q-homomorfismos", "NumberField"),
    "ordinals": _e(C, "un ordinal", "<= (categoria delgada)", "Ordinal"),
    "point-set-topology": _e(
        C, "un espacio topologico", "continuas", "TopCat"),
    "probabilistic-method": _e(T),
    "probability-theory": _e(
        C, "un espacio de probabilidad", "NUCLEOS DE MARKOV, no funciones",
        "ProbabilityTheory.Kernel, IsMarkovKernel",
        "con funciones medibles la categoria no tiene el producto que hace "
        "falta para independencia; con nucleos (Kleisli de Giry) es una "
        "categoria de Markov y el condicionamiento es estructura"),
    "random-variables": _e(
        F, "", "una funcion medible: es flecha", "Measurable, AEEqFun",
        "ARISTA de probability-theory a measure-theory"),
    "solvable-groups": _e(S, "un grupo resoluble", "homomorfismos", "IsSolvable"),
    "strategy-forward": _e(T, nota="genera encadenar hipotesis; composicion"),
    "tactic-apply": _e(T, nota="genera composicion hacia atras"),
    "tactic-rewrite": _e(T, nota="genera transporte por una igualdad; Eq.mpr"),

    # ═══ BLOQUE 3 — categorias y objetos ═════════════════════════════════
    "abelian-groups": _e(C, "un grupo abeliano", "homomorfismos", "AddCommGrpCat"),
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
    "cat-basics": _e(C, "una categoria pequeña", "funtores", "CategoryTheory.Cat"),
    "character-theory": _e(F, "", "chi = tr . rho, invariante de una representacion",
                           "FDRep.character"),
    "cohomology": _e(F, "", "el funtor H^*",
                     "HomologicalComplex.homology, CochainComplex"),
    "compactness": _e(S, "un espacio compacto", "continuas",
                      "CompactSpace, CompHaus"),
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
                         "interpretaciones (LHom)",
                         "FirstOrder.Language, Theory, LHom"),
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
                        "MulAction, CategoryTheory.Action"),
    "group-homomorphisms": _e(F, "", "la capa de flechas de group-theory", "MonoidHom"),
    "harmonic-analysis": _e(
        C, "un grupo abeliano localmente compacto",
        "homomorfismos continuos; Pontryagin es la autodualidad", "PontryaginDual"),
    "higher-category-theory": _e(C, "una n-categoria o una infinito-categoria",
                                 "funtores", "Bicategory, SSet.Quasicategory"),
    "hilbert-spaces": _e(C, "un espacio de Hilbert", "acotadas; es categoria daga",
                         "InnerProductSpace + CompleteSpace, adjoint"),
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
                         "ModuleCat, FGModuleCat"),
    "localization": _e(F, "", "S^-1 R; y la localizacion de categorias",
                       "IsLocalization, CategoryTheory.Localization"),
    "markov-chains": _e(C, "un objeto con un endomorfismo en la categoria de nucleos",
                        "intertwiners", "ProbabilityTheory.Kernel, PMF"),
    "martingale-theory": _e(S, "un proceso adaptado con la propiedad de martingala",
                            "", "MeasureTheory.Martingale, Filtration"),
    "metric-spaces": _e(C, "un espacio metrico",
                        "Lipschitz, o isometrias, o continuas: ELIGE", "MetricSpace",
                        "la eleccion cambia que colimites existen"),
    "model-theory": _e(C, "una L-estructura",
                       "homomorfismos, o inmersiones elementales",
                       "FirstOrder.Language.Structure, ElementaryEmbedding"),
    "modular-arithmetic": _e(C, "Z/nZ, un diagrama indexado por (N, |)",
                             "reducciones; el limite es Z-sombrero",
                             "ZMod, ZMod.castHom"),
    "module-theory": _e(C, "un modulo sobre R", "R-lineales", "ModuleCat R"),
    "monads": _e(C, "una monada sobre C, monoide en [C,C]", "morfismos de monadas",
                 "CategoryTheory.Monad, Kleisli"),
    "nat-trans": _e(F, "", "la capa de 2-celdas de functors", "NatTrans"),
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
                              "IsRiemannianManifold, RiemannianMetric"),
    "ring-theory": _e(C, "un anillo", "homomorfismos", "RingCat"),
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
                               "", "Filtration, Adapted"),
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
                       "Subobject.Classifier, Sheaf", "sin topos elemental"),
    "triangle-geometry": _e(C, "un 2-simplex afin", "semejanzas",
                            "Affine.Triangle, EuclideanGeometry"),
    "turing-machines": _e(C, "una maquina de Turing", "simulaciones",
                          "Turing.TM0, Turing.TM1"),
    "ultraproducts": _e(F, "", "producto ultrafiltrado: colimite filtrado",
                        "FirstOrder.Language.Ultraproduct, Filter.Germ"),
    "unique-factorization": _e(S, "un dominio de factorizacion unica", "homomorfismos",
                               "UniqueFactorizationMonoid"),

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

#: Etiquetas cuyos MORFISMOS hay que fijar antes de calcular colimites: la
#: eleccion cambia que colimites existen.
MORFISMO_SIN_FIJAR: list[str] = [
    "metric-spaces", "banach-spaces", "measure-theory", "probability-theory",
    "homotopy-theory",
]


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
