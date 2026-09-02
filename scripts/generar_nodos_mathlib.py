# -*- coding: utf-8 -*-
"""Genera los nodos de COBERTURA que faltan, leyendo la taxonomía de Mathlib.

POR QUE. El grafo cubre el 32,7 % de los teoremas de Mathlib. Lo que falta no
esta repartido al azar: `Order` esta a cero con 12 128 teoremas y `Data` al
3,4 % con 19 303 — o sea, orden, desigualdades, y la matematica elemental
(Nat, Set, Finset, List). Medido: ante `(a+b)^2 = a^2+2ab+b^2` NO HAY NODO que
recuperar, y por eso tres emparejadores distintos fallaron en algebra (7 %)
mientras acertaban en geometria (53-66 %), donde el nodo si existe.

Mathlib trae la ruta de construccion entera:

    id, name      la ruta del modulo
    description   el docstring `/-! # ... -/`
    keywords      los nombres de declaracion de debajo
    dependencies  EL DAG DE IMPORTS — dependencias reales, no curadas
    level         la profundidad en la jerarquia

QUE SE GENERA Y QUE NO. Solo modulos con >= UMBRAL teoremas debajo, para no
ahogar los 173 nodos curados con mil conceptos de relleno: el trabajo
categorico —colimites, delgadez, orden de complejidad— esta probado en Lean
sobre un grafo pequeño y no debe diluirse.

Y LOS GENERADOS VAN MARCADOS. Llevan `origen="mathlib"` e `interpretado=False`
porque NADIE los ha leido categoricamente. Los 173 de math_domains.py dicen
«un objeto es un grupo, las flechas son homomorfismos»; estos solo dicen donde
vive algo en Mathlib. Mezclarlos sin distinguir haria que interpretacion.py
afirmara sobre ellos lo que nadie ha decidido.

Escribe `nucleo/pillars/mathlib_taxonomy.py`, que es codigo revisable — no un
JSON opaco — para que se pueda leer, corregir a mano y versionar.

    python scripts/generar_nodos_mathlib.py            # muestra lo que haria
    python scripts/generar_nodos_mathlib.py --escribir # lo escribe
"""
import argparse
import collections
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MATH = "E:/Metamatematico/.lake/packages/mathlib/Mathlib"
DESTINO = "E:/Metamatematico/nucleo/pillars/mathlib_taxonomy.py"
UMBRAL = 500
NIVEL = 2
MAX_KW = 24

TEO = re.compile(r"^\s*(?:@\[[^\]]*\]\s*)?(?:private\s+|protected\s+)?"
                 r"(?:theorem|lemma)\s+")
DECL = re.compile(r"^\s*(?:@\[[^\]]*\]\s*)?(?:private\s+|protected\s+"
                  r"|noncomputable\s+)*"
                  r"(?:theorem|lemma|def|structure|class|abbrev)\s+"
                  r"([A-Za-z_][\w.']*)")
DOC = re.compile(r"/-!(.*?)-/", re.S)
IMP = re.compile(r"^(?:public\s+|meta\s+|private\s+|protected\s+)*import\s+"
                 r"([A-Za-z_][\w.]*)", re.M)
IGNORAR = {"Tactic", "Util", "Testing", "Deprecated", "Mathport", "Init", "Lean"}

#: Area de primer nivel -> pilar. ES UNA ASIGNACION DE COBERTURA, no una
#: lectura categorica: dice «esto vive sobre conjuntos», no «un objeto de este
#: nodo es tal cosa y sus flechas son tales otras». Hace falta porque el codigo
#: del runtime accede a `skill.pillar.name` y no admite None.
PILAR = {
    "CategoryTheory": "CAT", "Logic": "LOG", "ModelTheory": "LOG",
    "Computability": "TYPE", "Data": "SET", "Order": "SET",
}

#: Area -> categoria del grafo, para que las tacticas medidas les apliquen.
CATEGORIA = {
    "Algebra": "algebra", "RingTheory": "algebra", "GroupTheory": "algebra",
    "LinearAlgebra": "algebra", "FieldTheory": "algebra",
    "RepresentationTheory": "algebra",
    "Analysis": "analysis", "CategoryTheory": "category-theory",
    "Combinatorics": "combinatorics", "Computability": "computation",
    "Geometry": "geometry", "Logic": "logic", "ModelTheory": "logic",
    "NumberTheory": "number-theory", "Probability": "probability",
    "MeasureTheory": "probability", "Dynamics": "probability",
    "SetTheory": "set-theory", "Order": "set-theory", "Topology": "topology",
    "Data": "algebra", "AlgebraicGeometry": "geometry",
    "AlgebraicTopology": "topology", "NumberField": "number-theory",
}


def _palabras(nombre):
    n = nombre.split(".")[-1]
    n = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", n)
    return n.replace("_", " ").lower()


def recorrer():
    """clave de profundidad NIVEL -> datos crudos del subarbol."""
    datos = collections.defaultdict(
        lambda: {"teoremas": 0, "docs": [], "titulos": [], "decls": [],
                 "imports": set(), "modulos": []})
    for raiz, _d, fs in os.walk(MATH):
        for f in sorted(fs):
            if not f.endswith(".lean"):
                continue
            rel = os.path.relpath(os.path.join(raiz, f), MATH)
            partes = rel[:-5].replace("\\", "/").split("/")
            if partes[0] in IGNORAR or len(partes) < NIVEL:
                continue
            clave = ".".join(partes[:NIVEL])
            try:
                txt = io.open(os.path.join(raiz, f), encoding="utf-8",
                              errors="replace").read()
            except Exception:
                continue
            d = datos[clave]
            d["teoremas"] += sum(1 for l in txt.splitlines() if TEO.match(l))
            d["modulos"].append("Mathlib." + ".".join(partes))
            # SOLO el docstring del fichero RAIZ del concepto, o de su Basic /
            # Defs. La primera version cogia el primer docstring alfabetico del
            # subarbol y salian descripciones falsas: `Analysis.SpecialFunctions`
            # quedaba como «Inverse of the cosh function» y `Topology.Instances`
            # como «Ternary Cantor Set». Una descripcion equivocada es peor que
            # una generica, y mas cuando es justo el texto que el emparejador
            # semantico compara.
            hoja = partes[NIVEL - 1] if len(partes) == NIVEL else None
            raiz_concepto = (len(partes) == NIVEL or
                             (len(partes) == NIVEL + 1
                              and partes[NIVEL] in ("Basic", "Defs")))
            if raiz_concepto:
                m = DOC.search(txt)
                if m:
                    cuerpo = re.sub(r"[#*`]", " ", m.group(1)).strip()
                    cuerpo = " ".join(cuerpo.split())
                    if len(cuerpo) > 30:
                        # el del propio modulo manda sobre el de Basic/Defs
                        d["docs"].insert(0 if hoja else len(d["docs"]),
                                         cuerpo[:300])
            # Los TITULOS de los docstrings del subarbol, como respaldo. El
            # nodo mas grande, `Algebra.Order` con 5140 teoremas, no tiene
            # fichero raiz ni Basic, y sin esto se quedaba descrito con una
            # sopa de identificadores: «algebra order. smul, comp, perm». Los
            # titulos siguen siendo palabras de Mathlib y dicen de que va.
            if len(d["titulos"]) < 12:
                mt = DOC.search(txt)
                if mt:
                    prim = mt.group(1).strip().splitlines()
                    for l in prim[:2]:
                        l = l.strip().lstrip("#").strip()
                        if 8 < len(l) < 70 and l not in d["titulos"]:
                            d["titulos"].append(l)
                            break
            if len(d["decls"]) < 400:
                for l in txt.splitlines():
                    mm = DECL.match(l)
                    if mm:
                        d["decls"].append(mm.group(1))
            for imp in IMP.findall(txt[:8000]):
                if imp.startswith("Mathlib."):
                    p = imp.split(".")
                    if len(p) > NIVEL and p[1] not in IGNORAR:
                        otro = ".".join(p[1:NIVEL + 1])
                        if otro != clave:
                            d["imports"].add(otro)
    return datos


def _id(clave):
    return "mathlib-" + clave.replace(".", "-").lower()


def main(escribir):
    global UMBRAL
    print("recorriendo Mathlib...")
    datos = recorrer()
    print("  %d conceptos a profundidad %d" % (len(datos), NIVEL))

    from nucleo.core import Nucleo
    from nucleo.graph.category import SkillCategory
    import json
    n = Nucleo.__new__(Nucleo)
    n._graph = SkillCategory()
    Nucleo._load_foundational_skills(n)
    # LOS YA GENERADOS NO CUENTAN COMO «EXISTENTES».
    #
    # El grafo del runtime ya carga los nodos de una generacion anterior, asi
    # que sin esta linea el generador los saltaria por «id repetido» y el
    # fichero nuevo saldria SIN ELLOS: regenerar con otro umbral habria BORRADO
    # los 44 de la tanda anterior en vez de ampliarlos. La generacion tiene que
    # ser reproducible desde cero, no incremental sobre su propio resultado.
    existentes = {s for s in n._graph.skill_ids if not s.startswith("mathlib-")}

    cubiertos = set()
    por_skill = json.load(io.open("E:/Metamatematico/data/mathlib_modulos.json",
                                  encoding="utf-8"))["por_skill"]
    for mods in por_skill.values():
        for m in mods:
            p = m.replace("Mathlib.", "", 1).split(".")
            cubiertos.add(".".join(p[:NIVEL]))

    candidatos = {k: v for k, v in datos.items()
                  if v["teoremas"] >= UMBRAL and k not in cubiertos}
    print("  con >= %d teoremas y sin cubrir: %d\n" % (UMBRAL, len(candidatos)))

    fichas = []
    for clave in sorted(candidatos, key=lambda k: -candidatos[k]["teoremas"]):
        d = candidatos[clave]
        area = clave.split(".")[0]
        sid = _id(clave)
        if sid in existentes:
            print("  se salta %s: el id ya existe" % sid)
            continue
        # keywords: vocabulario de las declaraciones, lo mas frecuente primero
        cnt = collections.Counter()
        for x in d["decls"]:
            for w in _palabras(x).split():
                if len(w) > 3:
                    cnt[w] += 1
        kws = [w for w, _ in cnt.most_common(MAX_KW)]

        # LOS NOMBRES QUE EL NODO APORTA AL PROMPT.
        #
        # Sin esto un nodo de cobertura gana sitio en el top-k del emparejador
        # y NO APORTA NI UN NOMBRE, porque `nombres_de_trabajo` solo lee el
        # veredicto y estos no lo tienen. Medido al pasar de 44 a 125 nodos: la
        # cobertura contra ProofNet BAJO de 14,2 % a 12,6 % y los enunciados
        # con algo que ofrecer de 280 a 258. Ocupaban y no daban.
        #
        # `keywords` no sirve para esto: son fragmentos en minuscula —`smul`,
        # `coeff`— y no identificadores. Lo que si es un identificador valido es
        # el ultimo componente del modulo, que en Mathlib es casi siempre el
        # namespace raiz: Polynomial, Finset, Filter, Nat. Y las declaraciones
        # que empiezan por mayuscula, que son tipos y estructuras.
        # Solo TIPOS, no lemas. «Empieza por mayuscula» colaba
        # `C_eq_algebraMap` y `X_pow_smul_rTensor_monomial`, que son nombres de
        # lema larguisimos y especificos: inundaban lo ofrecido y hundieron la
        # precision contra ProofNet de 13,5 % a 3,1 %, por debajo del modelo
        # nulo. Un tipo de Mathlib va en CamelCase SIN guiones bajos.
        ultimo = clave.split(".")[-1]
        tipos = []
        for x in d["decls"]:
            c0 = x.split(".")[-1]
            if (c0[:1].isupper() and "_" not in c0 and len(c0) >= 3
                    and c0 not in tipos and c0 != ultimo):
                tipos.append(c0)
            if len(tipos) >= 4:
                break
        nombres = [ultimo] + tipos
        # Sin docstring propio no se inventa: se describe con las palabras
        # del modulo y su vocabulario, que es verdad aunque sea pobre.
        if d["docs"]:
            desc = d["docs"][0]
        elif d["titulos"]:
            desc = "%s: %s" % (" ".join(_palabras(p) for p in clave.split(".")),
                               "; ".join(d["titulos"][:6]))
        else:
            desc = "%s. %s" % (" ".join(_palabras(p) for p in clave.split(".")),
                               ", ".join(kws[:10]))
        # dependencias: solo hacia conceptos que TAMBIEN se generan o existen
        deps = sorted(_id(o) for o in d["imports"]
                      if o in candidatos and _id(o) != sid)
        fichas.append({
            "id": sid,
            "name": clave.replace(".", " · "),
            "description": desc[:280],
            "pillar": PILAR.get(area, "SET"),
            "level": 2,
            "dependencies": deps[:6],
            "category": CATEGORIA.get(area, "algebra"),
            "keywords": kws,
            "nombres": nombres,
            "modulo": "Mathlib." + clave,
            "teoremas": d["teoremas"],
        })
        print("  %-38s %6d teoremas · %2d deps · %s"
              % (sid, d["teoremas"], len(deps), desc[:46]))

    print("\n  total: %d nodos, %d teoremas cubiertos de mas"
          % (len(fichas), sum(f["teoremas"] for f in fichas)))
    if not escribir:
        print("\n  (sin --escribir no se toca nada)")
        return 0

    lineas = ['# -*- coding: utf-8 -*-',
              '"""Nodos de COBERTURA generados desde la taxonomia de Mathlib.',
              '',
              'GENERADO por scripts/generar_nodos_mathlib.py — no editar a mano sin',
              'anotarlo: una regeneracion lo pisa. Se versiona como codigo, y no como',
              'JSON, para que se pueda leer y corregir en la revision.',
              '',
              'ESTOS NODOS NO ESTAN INTERPRETADOS. Los 173 de math_domains.py llevan un',
              'veredicto categorico —«un objeto es un grupo, las flechas son',
              'homomorfismos»— decidido a mano. Estos solo dicen DONDE VIVE algo en',
              'Mathlib, con que vocabulario se habla de ello y de que depende segun el',
              'DAG de imports. Por eso llevan `interpretado=False`: para que nada',
              'afirme sobre ellos lo que nadie ha decidido.',
              '',
              'Las dependencias SI son reales: salen de los imports de Mathlib, que son',
              'aciclicos y estan en el fuente. No son curacion humana y no pueden estar',
              'al reves.',
              '',
              'Umbral: %d teoremas. Profundidad: %d.' % (UMBRAL, NIVEL),
              '"""',
              'from dataclasses import dataclass, field',
              '',
              '',
              '@dataclass',
              'class NodoCobertura:',
              '    """Un concepto de Mathlib que el grafo no tenia."""',
              '    id: str',
              '    name: str',
              '    description: str',
              '    pillar: str',
              '    level: int',
              '    category: str',
              '    modulo: str',
              '    teoremas: int',
              '    dependencies: list = field(default_factory=list)',
              '    keywords: list = field(default_factory=list)',
              '    #: Identificadores de Mathlib que este nodo aporta al prompt.',
              '    #: PENDIENTE de comprobar con `#check`, como manda la casa.',
              '    nombres: list = field(default_factory=list)',
              '',
              '',
              'NODOS_MATHLIB = [']
    for f in fichas:
        lineas.append('    NodoCobertura(')
        lineas.append('        id=%r,' % f["id"])
        lineas.append('        name=%r,' % f["name"])
        lineas.append('        description=%r,' % f["description"])
        lineas.append('        pillar=%r, level=%d, category=%r,'
                      % (f["pillar"], f["level"], f["category"]))
        lineas.append('        modulo=%r, teoremas=%d,' % (f["modulo"], f["teoremas"]))
        lineas.append('        dependencies=%r,' % (f["dependencies"],))
        lineas.append('        keywords=%r,' % (f["keywords"],))
        lineas.append('        nombres=%r,' % (f["nombres"],))
        lineas.append('    ),')
    lineas.append(']')
    lineas.append('')
    io.open(DESTINO, "w", encoding="utf-8").write("\n".join(lineas))
    print("\n  -> %s" % DESTINO)
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--escribir", action="store_true")
    ap.add_argument("--umbral", type=int, default=UMBRAL,
                    help="teoremas minimos para generar un nodo")
    a = ap.parse_args()
    UMBRAL = a.umbral
    sys.exit(main(a.escribir))
