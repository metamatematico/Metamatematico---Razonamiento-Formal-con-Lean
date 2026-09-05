# -*- coding: utf-8 -*-
"""La base canonica: UNA taxonomia de areas, y los sorts que no son areas.

EL PROBLEMA QUE CIERRA
----------------------
El grafo tenia DOS taxonomias de area compitiendo, y no casaban:

  · 22 nodos `area-*`, leidos de los modulos de Mathlib. CamelCase:
    `Algebra`, `CategoryTheory`, `NumberTheory`.
  · 15 valores de `metadata["category"]`, curados a mano. kebab minuscula:
    `algebra`, `category-theory`, `number-theory`.

Ni los nombres coincidian —`categorytheory` frente a `category-theory`— ni el
contenido: CINCO de los 15 valores curados NO SON AREAS MATEMATICAS.

    lean-tactics       como se demuestra, no de que trata
    proof-strategies   idem
    area               la marca de los propios nodos de area
    optimization       no es un area de primer nivel de Mathlib
    computation        el nombre curado de `Computability`

Y `construir_funtor` proyectaba sobre la taxonomia de 15. O sea: el funtor pi
aterrizaba en una base que trataba `lean-tactics` como si fuera una rama de las
matematicas, al mismo nivel que `topology`. Era funtorial y no significaba
nada.

`functor.py` ya habia TROPEZADO con esto y lo habia parcheado por el otro lado:
excluye los morfismos TRANSLATION del funtor «porque van a `lean-tactics`, que
no es una rama sino COMO se demuestra». El sintoma estaba visto; la causa era
que la base mezclaba dos clases de cosa.

LA SEPARACION
-------------
Dos preguntas distintas, dos campos distintos:

    metadata["area"]   ¿de que rama de las matematicas habla? -> la BASE
    metadata["sort"]   ¿que CLASE de objeto es?               -> la FIBRA

Una tactica tiene `sort=TACTICA` y `area=None`. No es que le falte el area: es
que la pregunta no se le aplica. `simp` no trata de topologia ni de algebra.

`metadata["category"]` SE CONSERVA y no cambia de valor. Hay tests y vistas que
lo leen, y romperlos no aporta nada. Queda como etiqueta HEREDADA: nada nuevo
deberia leerla, y lo que hoy la lee para decidir un area deberia migrar a
`area`.
"""
from __future__ import annotations

from typing import Optional

# ═══════════════════════════════════════════════════════════════════════════
# LOS SORTS — que clase de objeto es un nodo
# ═══════════════════════════════════════════════════════════════════════════
#: Concepto matematico interpretado a mano. Lleva veredicto categorico:
#: «un objeto es un grupo, las flechas son homomorfismos». Fibra C.
CONCEPTO = "CONCEPTO"
#: Nodo leido de la taxonomia de Mathlib. Dice DONDE VIVE algo, no que es.
#: Es el que hoy va marcado `interpretado=False`. Fibra M.
MODULO = "MODULO"
#: Nodo de area: la puerta de entrada. Es un objeto de la BASE, no de una
#: fibra, y por eso se distingue de los otros dos.
AREA = "AREA"
#: Tactica de Lean. No es matematica: es como se demuestra.
TACTICA = "TACTICA"
#: Estrategia de prueba. Tampoco es matematica, y por el mismo motivo.
ESTRATEGIA = "ESTRATEGIA"

SORTS = frozenset({CONCEPTO, MODULO, AREA, TACTICA, ESTRATEGIA})

#: Los sorts a los que la pregunta «¿de que area es?» NO SE LES APLICA.
#: Su `area` es None, y eso es una respuesta, no un hueco.
SIN_AREA = frozenset({TACTICA, ESTRATEGIA})


# ═══════════════════════════════════════════════════════════════════════════
# LA BASE — las 22 areas, en la forma en que Mathlib las nombra
# ═══════════════════════════════════════════════════════════════════════════
#
# Se elige la presentacion de Mathlib y no la curada por dos motivos:
#   · es la que produce `_area_de()` al leer la ruta de un modulo, o sea la
#     unica de las dos que se DERIVA de algo y no se escribe a mano;
#   · cubre 22 areas frente a 11, e incluye justo las que el grafo curado no
#     tiene (`OrderTheory`, `RingTheory`, `MeasureTheory`...).
#
AREAS_CANONICAS = frozenset({
    "Algebra", "AlgebraicGeometry", "AlgebraicTopology", "Analysis",
    "CategoryTheory", "Combinatorics", "Computability", "Dynamics",
    "FieldTheory", "Geometry", "GroupTheory", "LinearAlgebra", "Logic",
    "MeasureTheory", "ModelTheory", "NumberTheory", "OrderTheory",
    "Probability", "RepresentationTheory", "RingTheory", "SetTheory",
    "Topology",
})


# ═══════════════════════════════════════════════════════════════════════════
# EL PUENTE — de la etiqueta curada al area canonica
# ═══════════════════════════════════════════════════════════════════════════
#
# ESTO ES UN JUICIO, no una derivacion, igual que `_AREA_DE_DATA`. Diez de las
# doce entradas son la misma palabra en otra ortografia y no tienen discusion.
# Las dos que si la tienen van razonadas:
#
#   computation -> Computability
#       Las ocho skills son maquinas de Turing, recursion, lambda-calculo y
#       complejidad. `Computability` es el area de Mathlib que las recibe.
#       `np-completeness` y `algorithm-analysis` quedan algo forzadas ahi,
#       pero no hay area mas cercana y dejarlas sin area seria peor.
#
#   optimization -> Analysis
#       Mathlib no tiene area `Optimization`. Archiva la convexidad en
#       `Mathlib.Analysis.Convex`, y tres de las cinco skills
#       —convex-optimization, duality-theory, variational-methods— son
#       analisis sin discusion. Las otras dos, `linear-programming` y
#       `discrete-optimization`, encajan peor: son mas combinatorias que
#       analiticas. Se anota aqui para que quien lo mida lo sepa, en vez de
#       repartirlas a ojo una por una.
#
CATEGORIA_A_AREA: dict[str, str] = {
    "algebra":         "Algebra",
    "analysis":        "Analysis",
    "category-theory": "CategoryTheory",
    "combinatorics":   "Combinatorics",
    "computation":     "Computability",
    "geometry":        "Geometry",
    "logic":           "Logic",
    "number-theory":   "NumberTheory",
    "optimization":    "Analysis",
    "probability":     "Probability",
    "set-theory":      "SetTheory",
    "topology":        "Topology",
}

#: Las etiquetas curadas que NO nombran un area, y el sort que si les
#: corresponde. Sacarlas de la base es la mitad del arreglo; la otra mitad es
#: que ahora tienen donde ir.
CATEGORIA_A_SORT: dict[str, str] = {
    "lean-tactics":     TACTICA,
    "proof-strategies": ESTRATEGIA,
    "area":             AREA,
}

# Invariante barato, comprobado al importar: todo destino del puente tiene que
# existir en la base. Un typo aqui produce un area fantasma que nada alcanza y
# que ninguna cifra delata.
assert set(CATEGORIA_A_AREA.values()) <= AREAS_CANONICAS, (
    "areas del puente que no estan en la base: %s"
    % sorted(set(CATEGORIA_A_AREA.values()) - AREAS_CANONICAS))
assert set(CATEGORIA_A_SORT.values()) <= SORTS


# ═══════════════════════════════════════════════════════════════════════════
# LAS KEYWORDS DE LAS AREAS
# ═══════════════════════════════════════════════════════════════════════════
#
# Los 22 nodos de area tenian CERO keywords. Medido: `0 de 22`. El area es la
# PUERTA DE ENTRADA al grafo y era inalcanzable por via lexica — el
# emparejador compara contra id, nombre y keywords, y el id `area-numbertheory`
# no casa con «numeros primos» ni con «number theory».
#
# Van en español y en ingles, y sin acentos no hace falta: `nucleo.texto`
# normaliza los dos lados. Se escriben en singular y en plural solo cuando el
# plural es la forma en que la gente escribe de verdad («numeros primos»).
#
KEYWORDS_AREA: dict[str, list[str]] = {
    "Algebra": [
        "algebra", "álgebra", "algebraico", "algebraica", "algebraic",
        "estructura algebraica", "anillo", "ring", "cuerpo", "campo",
        "field", "modulo", "módulo", "module", "ideal",
    ],
    "AlgebraicGeometry": [
        "geometria algebraica", "geometría algebraica", "algebraic geometry",
        "esquema", "scheme", "variedad algebraica", "algebraic variety",
        "haz", "sheaf",
    ],
    "AlgebraicTopology": [
        "topologia algebraica", "topología algebraica", "algebraic topology",
        "homologia", "homología", "homology", "cohomologia", "cohomology",
        "grupo fundamental", "fundamental group", "homotopia", "homotopy",
    ],
    "Analysis": [
        "analisis", "análisis", "analysis", "calculo", "cálculo", "calculus",
        "derivada", "derivative", "integral", "limite", "límite", "limit",
        "continuidad", "continuity", "continua", "continuous", "serie",
        "series", "sucesion", "sucesión", "sequence", "convergencia",
        "convergence", "real", "reales", "convexidad", "convex",
    ],
    "CategoryTheory": [
        "categoria", "categoría", "category", "categorias", "categorías",
        "funtor", "functor", "transformacion natural",
        "transformación natural", "natural transformation", "colimite",
        "colímite", "colimit", "limite categorico", "adjuncion", "adjunción",
        "adjunction", "morfismo", "morphism",
    ],
    "Combinatorics": [
        "combinatoria", "combinatorics", "combinatorio", "conteo",
        "counting", "grafo", "graph", "permutacion", "permutación",
        "permutation", "combinacion", "combinación", "combination",
        "binomial", "finset", "cardinalidad finita",
    ],
    "Computability": [
        "computabilidad", "computability", "computable", "decidible",
        "decidable", "maquina de turing", "máquina de turing",
        "turing machine", "recursion", "recursión", "recursive",
        "complejidad", "complexity", "algoritmo", "algorithm",
        "lambda calculo", "lambda cálculo", "lambda calculus",
    ],
    "Dynamics": [
        "dinamica", "dinámica", "dynamics", "sistema dinamico",
        "sistema dinámico", "dynamical system", "orbita", "órbita", "orbit",
        "flujo", "flow", "iteracion", "iteración", "ergodico", "ergódico",
        "ergodic",
    ],
    "FieldTheory": [
        "teoria de cuerpos", "teoría de cuerpos", "field theory",
        "extension de cuerpos", "extensión de cuerpos", "field extension",
        "galois", "polinomio minimo", "polinomio mínimo",
        "algebraicamente cerrado", "algebraically closed",
    ],
    "Geometry": [
        "geometria", "geometría", "geometry", "geometrico", "geométrico",
        "triangulo", "triángulo", "triangle", "circulo", "círculo",
        "circle", "angulo", "ángulo", "angle", "distancia", "distance",
        "euclidiana", "euclidean", "variedad", "manifold", "curvatura",
        "curvature",
    ],
    "GroupTheory": [
        "teoria de grupos", "teoría de grupos", "group theory", "grupo",
        "group", "subgrupo", "subgroup", "homomorfismo", "homomorphism",
        "sylow", "grupo abeliano", "abelian group", "orden del grupo",
    ],
    "LinearAlgebra": [
        "algebra lineal", "álgebra lineal", "linear algebra", "matriz",
        "matrix", "matrices", "vector", "espacio vectorial",
        "vector space", "determinante", "determinant", "autovalor",
        "eigenvalue", "base", "dimension", "dimensión", "rango", "rank",
    ],
    "Logic": [
        "logica", "lógica", "logic", "logico", "lógico", "proposicion",
        "proposición", "proposition", "cuantificador", "quantifier",
        "predicado", "predicate", "deduccion", "deducción", "deduction",
        "inferencia", "inference", "tautologia", "tautología", "tautology",
        "implica", "implies", "demostrabilidad",
    ],
    "MeasureTheory": [
        "teoria de la medida", "teoría de la medida", "measure theory",
        "medida", "measure", "medible", "measurable", "lebesgue",
        "integral de lebesgue", "casi por todas partes", "almost everywhere",
    ],
    "ModelTheory": [
        "teoria de modelos", "teoría de modelos", "model theory", "modelo",
        "model", "estructura de primer orden", "first order structure",
        "satisfaccion", "satisfacción", "satisfaction", "compacidad",
        "compactness", "elementalmente equivalente",
    ],
    "NumberTheory": [
        "teoria de numeros", "teoría de números", "number theory", "numero",
        "número", "number", "numeros", "números", "primo", "prime",
        "primos", "primes", "divisibilidad", "divisibility", "divisor",
        "congruencia", "congruence", "modular", "entero", "integer",
        "enteros", "integers", "natural", "naturales", "mcd", "gcd",
        "factorizacion", "factorización", "factorization",
    ],
    "OrderTheory": [
        "teoria del orden", "teoría del orden", "order theory", "orden",
        "order", "ordenado", "ordered", "reticulo", "retículo", "lattice",
        "supremo", "supremum", "infimo", "ínfimo", "infimum", "cota",
        "bound", "monotono", "monótono", "monotone", "preorden", "preorder",
        "parcialmente ordenado", "partial order",
    ],
    "Probability": [
        "probabilidad", "probability", "probabilistico", "probabilístico",
        "aleatorio", "random", "variable aleatoria", "random variable",
        "esperanza", "expectation", "distribucion", "distribución",
        "distribution", "independencia", "independence", "estadistica",
        "estadística",
    ],
    "RepresentationTheory": [
        "teoria de representaciones", "teoría de representaciones",
        "representation theory", "representacion", "representación",
        "representation", "caracter", "carácter", "character",
        "representacion irreducible", "irreducible representation",
    ],
    "RingTheory": [
        "teoria de anillos", "teoría de anillos", "ring theory", "anillo",
        "ring", "anillos", "rings", "ideal", "ideales", "ideals",
        "dominio", "domain", "noetheriano", "noetherian", "localizacion",
        "localización", "localization", "polinomio", "polynomial",
    ],
    "SetTheory": [
        "teoria de conjuntos", "teoría de conjuntos", "set theory",
        "conjunto", "set", "conjuntos", "sets", "cardinal", "cardinalidad",
        "cardinality", "ordinal", "zfc", "union", "unión", "interseccion",
        "intersección", "intersection", "subconjunto", "subset",
        "forcing", "eleccion", "elección", "choice",
    ],
    "Topology": [
        "topologia", "topología", "topology", "topologico", "topológico",
        "topological", "abierto", "open", "cerrado", "closed", "compacto",
        "compact", "compacidad", "conexo", "connected", "conexidad",
        "entorno", "neighborhood", "homeomorfismo", "homeomorphism",
        "metrico", "métrico", "metric",
    ],
}

assert set(KEYWORDS_AREA) == AREAS_CANONICAS, (
    "areas sin keywords: %s · keywords sin area: %s"
    % (sorted(AREAS_CANONICAS - set(KEYWORDS_AREA)),
       sorted(set(KEYWORDS_AREA) - AREAS_CANONICAS)))


# ═══════════════════════════════════════════════════════════════════════════
# LA API
# ═══════════════════════════════════════════════════════════════════════════

#: El pilar fundacional -> el area que le corresponde, para los 10 skills L0.
#:
#: Esos diez se declaran directamente en `core.py` y no llevan `category`, asi
#: que el puente de arriba no los alcanza. Tres de los cuatro pilares tienen
#: area evidente. El cuarto NO, y no es un descuido:
#:
#:   TYPE -> None. Mathlib no tiene un area `TypeTheory`. `cic` y `lean-kernel`
#:   son la METATEORIA DEL PROBADOR, no una rama que el probador formalice.
#:   Ademas `cic` es el nodo del que cuelga `area-computability`, y el pilar no
#:   pertenece al area que sostiene — la misma regla que ya evita el 2-ciclo
#:   entre `cat-basics` y `area-categorytheory`.
AREA_DE_PILAR: dict[str, Optional[str]] = {
    "SET":  "SetTheory",
    "CAT":  "CategoryTheory",
    "LOG":  "Logic",
    "TYPE": None,
}

assert set(v for v in AREA_DE_PILAR.values() if v) <= AREAS_CANONICAS


def area_de_categoria(categoria: str) -> Optional[str]:
    """La etiqueta curada -> el area canonica, o None si no nombra un area.

    None tiene DOS lecturas distintas y las dos son correctas:
      · `lean-tactics` -> None porque la pregunta no se le aplica;
      · una etiqueta desconocida -> None porque nadie la ha interpretado.
    `sort_de_categoria` distingue la primera; la segunda se queda sin sort y
    cae a CONCEPTO, que es lo que era antes de existir este modulo.
    """
    return CATEGORIA_A_AREA.get((categoria or "").strip().lower())


def sort_de_categoria(categoria: str) -> Optional[str]:
    """La etiqueta curada -> su sort, si la etiqueta lo determina."""
    return CATEGORIA_A_SORT.get((categoria or "").strip().lower())


def es_area(nombre: str) -> bool:
    """¿`nombre` es un objeto de la base?"""
    return nombre in AREAS_CANONICAS


def id_de_area(area: str) -> str:
    """`NumberTheory` -> `area-numbertheory`, el id del nodo puerta."""
    return "area-" + (area or "").lower()


def area_de_id(area_id: str) -> Optional[str]:
    """`area-numbertheory` -> `NumberTheory`. La inversa, contra la base.

    No basta con recapitalizar: `numbertheory` no dice donde va la mayuscula.
    Se resuelve buscando en la base, que es la unica fuente.
    """
    if not (area_id or "").startswith("area-"):
        return None
    cola = area_id[5:].lower()
    for a in AREAS_CANONICAS:
        if a.lower() == cola:
            return a
    return None


def keywords_de_area(area: str) -> list[str]:
    """Los terminos ES+EN con los que se entra a un area."""
    return list(KEYWORDS_AREA.get(area, ()))
