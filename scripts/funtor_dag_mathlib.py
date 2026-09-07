# -*- coding: utf-8 -*-
"""¿Las dependencias CURADAS del grafo son dependencias REALES en Mathlib?

Dos intentos anteriores midieron menciones de identificadores dentro de los
ficheros de cada skill. Los dos fallaron por lo mismo: el mapa skill->modulo
apunta al fichero donde se DECLARA un identificador —`commutative-algebra` ->
`Algebra.Category.Ring.Basic`, un fichero— y con eso el corpus era 113 de 7746
ficheros. `commutative-algebra -> algebraic-geometry` salia sin evidencia, que
es absurdo. No fallaba el grafo: fallaba el corpus.

ESTA version no usa el mapa como corpus sino como PUNTERO, que es lo que es, y
mide sobre el DAG de imports de Mathlib entero. Ese DAG es dependencia real:
es aciclico, esta en el fuente, y si el fichero de B importa (transitivamente)
el de A, entonces B depende de A de verdad. No hace falta correr Lean.

    A -> B en el grafo  significa  "A es prerrequisito de B"
    se confirma si       fichero(B)  importa*  fichero(A)
    se INVIERTE si       fichero(A)  importa*  fichero(B)   <- el DAG es aciclico,
                                                               asi que esto prueba
                                                               que la flecha esta al reves
"""
import io, os, re, sys, json, collections
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "E:/Metamatematico")
RAIZ = "E:/Metamatematico"
MATH = RAIZ + "/.lake/packages/mathlib/Mathlib"
# Mathlib usa el sistema de modulos nuevo: las lineas son `public import X`,
# no `import X`. La primera version pedia `import` a principio de linea y
# encontro 342 aristas para 7746 ficheros — un DAG vacio, y con el un "20x
# sobre el azar" que no significaba nada porque el azar tambien era cero.
IMP = re.compile(r"^(?:public\s+|meta\s+|private\s+|protected\s+)*import\s+([A-Za-z_][\w.]*)", re.M)

# ── 1 · el DAG de imports de Mathlib entero ────────────────────────────────
directo = {}
for r, _d, fs in os.walk(MATH):
    for f in fs:
        if not f.endswith(".lean"):
            continue
        mod = "Mathlib." + os.path.relpath(os.path.join(r, f), MATH)[:-5] \
                             .replace("\\", "/").replace("/", ".")
        try:
            txt = io.open(os.path.join(r, f), encoding="utf-8", errors="replace").read(8000)
        except Exception:
            continue
        directo[mod] = [m for m in IMP.findall(txt) if m.startswith("Mathlib")]
print("DAG de imports: %d modulos, %d aristas directas"
      % (len(directo), sum(len(v) for v in directo.values())))

# ── 2 · alcanzabilidad, memoizada ──────────────────────────────────────────
sys.setrecursionlimit(100000)
_cl = {}
def cierre(m):
    """Todo lo que m importa, transitivamente."""
    if m in _cl:
        return _cl[m]
    _cl[m] = set()                      # corta ciclos por si acaso
    acc = set()
    pila = list(directo.get(m, ()))
    visto = set()
    while pila:
        x = pila.pop()
        if x in visto or x not in directo:
            if x not in directo:
                acc.add(x)
            continue
        visto.add(x); acc.add(x)
        if x in _cl and _cl[x]:
            acc |= _cl[x]
        else:
            pila.extend(directo.get(x, ()))
    _cl[m] = acc
    return acc

# ── 3 · el grafo curado ────────────────────────────────────────────────────
mapa = json.load(io.open(RAIZ + "/data/mathlib_modulos.json", encoding="utf-8"))["por_skill"]
mods_skill = {k: [m for m in v if m in directo] for k, v in mapa.items()}
mods_skill = {k: v for k, v in mods_skill.items() if v}
print("skills con modulo resoluble: %d" % len(mods_skill))

from nucleo.core import Nucleo
from nucleo.graph.category import SkillCategory
from nucleo.types import MorphismType
n = Nucleo.__new__(Nucleo); n._graph = SkillCategory()
Nucleo._load_foundational_skills(n)
G = n._graph
med = set(mods_skill)
aristas = sorted({(m.source_id, m.target_id) for m in G.morphisms
                  if m.morphism_type == MorphismType.DEPENDENCY
                  and m.source_id in med and m.target_id in med})
print("dependencias medibles: %d de %d\n"
      % (len(aristas), sum(1 for m in G.morphisms if m.morphism_type == MorphismType.DEPENDENCY)))

def importa(b, a):
    """¿algun modulo de b alcanza algun modulo de a?"""
    objetivo = set(mods_skill[a])
    for mb in mods_skill[b]:
        if objetivo & (cierre(mb) | {mb}):
            return True
    return False

# ── 4 · resultado ──────────────────────────────────────────────────────────
ok = [(a, b) for a, b in aristas if importa(b, a)]
inv = [(a, b) for a, b in aristas if not importa(b, a) and importa(a, b)]
nada = [(a, b) for a, b in aristas if not importa(b, a) and not importa(a, b)]

pares = [(a, b) for a in med for b in med if a != b]
base = sum(1 for a, b in pares if importa(b, a))

print("=== DEPENDENCIAS DEL GRAFO CONTRA EL DAG REAL ===\n")
print("  confirmadas (B importa* A)  : %3d / %d  = %5.1f %%"
      % (len(ok), len(aristas), 100.0 * len(ok) / len(aristas)))
print("  INVERTIDAS  (A importa* B)  : %3d / %d  = %5.1f %%"
      % (len(inv), len(aristas), 100.0 * len(inv) / len(aristas)))
print("  independientes en Mathlib   : %3d / %d  = %5.1f %%"
      % (len(nada), len(aristas), 100.0 * len(nada) / len(aristas)))
print("\n  par cualquiera (azar)       : %3d / %d = %5.1f %%"
      % (base, len(pares), 100.0 * base / len(pares)))
print("  factor sobre el azar        : %.2f x"
      % ((len(ok) / len(aristas)) / (base / len(pares))))

print("\nINVERTIDAS — la flecha apunta al reves (el DAG es aciclico, no hay duda):")
for a, b in inv[:14]:
    print("   %-26s -> %-26s" % (a, b))
print("\nINDEPENDIENTES — ni una importa a la otra:")
for a, b in nada[:12]:
    print("   %-26s -> %-26s" % (a, b))


# ── 5 · ¿falla el grafo, o falla el puntero? ───────────────────────────────
#
# Las invertidas tienen todas la misma forma: el lado GENERAL apunta al
# envoltorio categorico —Algebra.Category.Grp, Topology.Category.TopCat,
# CategoryTheory.Category.Cat— que en Mathlib vive ARRIBA del DAG: para
# construir la categoria Grp hacen falta antes subgrupos y homomorfismos.
#
# O sea que "group-theory -> subgroups-cosets" es una flecha correcta y sale
# invertida porque el modulo elegido para group-theory es la categoria Grp y
# no la teoria de grupos. Separar las dos cosas es lo unico que permite decir
# si el grafo curado modela algo o no.
ENVOLTORIO = (".Category.", "CategoryTheory.Category.Cat")
cat_skills = {k for k, v in mods_skill.items()
              if any(any(e in m for e in ENVOLTORIO) for m in v)}
print("\n=== SEPARANDO EL PUNTERO DEL GRAFO ===\n")
print("  skills que apuntan al envoltorio categorico: %d de %d"
      % (len(cat_skills), len(mods_skill)))
print("  " + ", ".join(sorted(cat_skills)))

lim = [(a, b) for a, b in aristas if a not in cat_skills and b not in cat_skills]
ok2 = [(a, b) for a, b in lim if importa(b, a)]
inv2 = [(a, b) for a, b in lim if not importa(b, a) and importa(a, b)]
p2 = [(a, b) for a in med if a not in cat_skills
      for b in med if b not in cat_skills and a != b]
base2 = sum(1 for a, b in p2 if importa(b, a))
print("\n  sin ellas quedan %d dependencias medibles:" % len(lim))
print("    confirmadas : %3d = %5.1f %%" % (len(ok2), 100.0 * len(ok2) / max(1, len(lim))))
print("    invertidas  : %3d = %5.1f %%" % (len(inv2), 100.0 * len(inv2) / max(1, len(lim))))
print("    azar        : %5.1f %%" % (100.0 * base2 / len(p2)))
print("    factor      : %.2f x"
      % ((len(ok2) / max(1, len(lim))) / (base2 / len(p2))))
print("\n  invertidas que quedan (candidatas de verdad a flecha mal puesta):")
for a, b in inv2:
    print("    %-24s -> %s" % (a, b))

# ── 6 · POR CLASE DE ARISTA, que es lo unico comparable ────────────────────
#
# Al arreglar el mapa de modulos —de 76 a 223 skills— las dependencias
# medibles pasaron de 73 a 282 y la tasa de confirmadas "cayo" del 78,1 % al
# 61,3 %. Leerlo como un empeoramiento es un ERROR DE CATEGORIA, y es mio: las
# 209 aristas nuevas no son de la misma clase que las 73 viejas.
#
#   curada     237 aristas, TODAS skill -> skill     AFIRMA PRERREQUISITO
#   jerarquia  221: area->mathlib 125, area->skill 74, skill->area 22
#   cobertura  125, todas skill -> mathlib-*          AFIRMA COBERTURA
#
# Solo `curada` afirma un prerrequisito, y es la unica comparable con el 78,1 %
# publicado.
#
# En `jerarquia` el juez es dudoso, y la razon esta MEDIDA (no supuesta):
# `area-analysis` apunta a UN fichero, y no a la raiz de la rama sino a un
# teorema representativo de dentro —Analysis.SpecialFunctions.Trigonometric
# .Basic—, que importa* 1625 de los 7746 modulos. Entre ellos, Normed.Module
# .Basic, que es justo el de `banach-spaces`: de ahi que la arista salga
# "invertida". No lo esta. La flecha afirma PERTENENCIA A LA RAMA y el DAG
# responde a otra pregunta —cual de los dos ficheros va antes—, y el fichero
# elegido para el area ya esta por encima de casi toda su propia rama.
#
# Y ojo con la explicacion facil: los punteros de area NO son mas profundos
# que los de un skill (mediana 1342 frente a 1352 modulos importados). Lo que
# falla no es la profundidad sino CUAL fichero representa al area.
# Las 44 invertidas de esa fila no son, por tanto, 44 flechas mal puestas.
#
# Y cada clase lleva SU PROPIO nulo, sobre pares de la misma forma
# (fuentes de la clase x destinos de la clase). Un nulo global compararia las
# aristas de cobertura contra un azar que no tiene su misma composicion.
clase_de = {}
for m in G.morphisms:
    if m.morphism_type != MorphismType.DEPENDENCY:
        continue
    md = getattr(m, "metadata", None) or {}
    c = md.get("construccion") or "curada"
    # las 14 con nombre propio (grupo-unidades, H_*, colapso...) son curadas
    # a mano igual que las sin marca: se agrupan con ellas, no aparte.
    if c not in ("jerarquia", "cobertura"):
        c = "curada"
    clase_de[(m.source_id, m.target_id)] = c

por_clase = {}
for a, b in aristas:
    por_clase.setdefault(clase_de.get((a, b), "curada"), []).append((a, b))

print("\n=== POR CLASE DE ARISTA (cada una con su nulo) ===\n")
print("  %-10s %8s %7s %7s %7s %8s %7s"
      % ("clase", "medibles", "ok", "inv", "indep", "nulo", "factor"))
print("  " + "-" * 60)
resumen_clases = {}
for c in ("curada", "jerarquia", "cobertura"):
    ar_c = por_clase.get(c, [])
    if not ar_c:
        continue
    okc = sum(1 for a, b in ar_c if importa(b, a))
    invc = sum(1 for a, b in ar_c if not importa(b, a) and importa(a, b))
    indc = len(ar_c) - okc - invc
    # nulo de la MISMA forma: fuentes de esta clase x destinos de esta clase
    fu = {a for a, _b in ar_c}
    de = {b for _a, b in ar_c}
    pc = [(a, b) for a in fu for b in de if a != b]
    nulo = sum(1 for a, b in pc if importa(b, a)) / max(1, len(pc))
    tasa = okc / len(ar_c)
    print("  %-10s %8d %7d %7d %7d %7.1f %% %6.2fx"
          % (c, len(ar_c), okc, invc, indc, 100 * nulo,
             tasa / nulo if nulo else float("inf")))
    resumen_clases[c] = {"medibles": len(ar_c), "confirmadas": okc,
                         "invertidas": invc, "independientes": indc,
                         "tasa_pct": 100 * tasa, "nulo_pct": 100 * nulo,
                         "factor": (tasa / nulo) if nulo else None,
                         "pares_del_nulo": len(pc)}
print("""
LECTURA: solo `curada` afirma un prerrequisito y por tanto solo esa fila es
comparable con la cifra publicada del 78,1 %. `jerarquia` y `cobertura` son
costuras de etiquetado —pertenencia a una rama, cobertura de un modulo— y el
DAG de imports no es el juez de ninguna de las dos.""")

json.dump({"medibles": len(aristas), "confirmadas": len(ok), "invertidas": len(inv),
           "por_clase": resumen_clases,
           "independientes": len(nada), "azar_pct": 100.0 * base / len(pares),
           "skills_envoltorio_categorico": sorted(cat_skills),
           "sin_envoltorio": {"medibles": len(lim), "confirmadas": len(ok2),
                              "invertidas": len(inv2),
                              "azar_pct": 100.0 * base2 / len(p2)},
           "lista_invertidas": [list(x) for x in inv],
           "lista_independientes": [list(x) for x in nada]},
          io.open(RAIZ + "/data/funtor_mathlib.json", "w", encoding="utf-8"),
          indent=1, ensure_ascii=False)
print("\n-> data/funtor_mathlib.json")
