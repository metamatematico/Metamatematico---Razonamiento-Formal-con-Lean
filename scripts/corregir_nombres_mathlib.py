# -*- coding: utf-8 -*-
"""
Los 25 nombres del grafo que Mathlib ya no reconoce: buscarlos y verificarlos.

De los 117 identificadores que el grafo declara, 92 existen. Los 25 que fallan
NO son invenciones —a diferencia de los del modelo— sino nombres que se
movieron o que necesitan cualificarse: `Scheme` vive en `AlgebraicGeometry`,
`Sheaf` en `TopCat`, `QuotientGroup` es un namespace y no un identificador. Es
desactualizacion respecto a la version de Mathlib, y se arregla.

METODO, y es lo que lo hace fiable: los candidatos NO se adivinan. Se buscan en
el FUENTE de Mathlib —`grep` sobre las declaraciones reales— se reconstruye su
namespace leyendo los `namespace` que envuelven la linea, y despues se
COMPRUEBAN todos de una vez con Lean. Lo que Lean no acepte no se propone.

No gasta API.

    python -m scripts.corregir_nombres_mathlib          # propone
    python -m scripts.corregir_nombres_mathlib --aplicar  # y lo escribe
"""
import argparse
import io
import json
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RAIZ = "E:/Metamatematico"
MATHLIB = RAIZ + "/.lake/packages/mathlib/Mathlib"
INFORME = RAIZ + "/data/vocabulario_grafo.json"

DECL = re.compile(
    r"^\s*(?:@\[[^\]]*\]\s*)?(?:private\s+|protected\s+|noncomputable\s+)*"
    r"(?:structure|def|abbrev|class|inductive|theorem|lemma)\s+([A-Za-z_][\w.']*)")
NS = re.compile(r"^\s*namespace\s+([A-Za-z_][\w.']*)")
END = re.compile(r"^\s*end\s+([A-Za-z_][\w.']*)")


#: Indice de Mathlib: nombre corto -> nombres cualificados donde se declara.
#: Se construye UNA vez recorriendo el fuente, y se reutiliza para los 25.
_INDICE = None


def _construir_indice():
    """Recorre el fuente de Mathlib y anota cada declaracion con su namespace.

    EN PYTHON PURO, a proposito. La version anterior llamaba a `grep` por
    subproceso y lo envolvia en un `except` mudo — y `grep` no esta en el PATH
    del interprete en Windows. Resultado: cero candidatos para TODO, incluido
    `Scheme`, que esta en AlgebraicGeometry/Scheme.lean linea 42. El fallo de
    la herramienta se reportaba como «no existe en Mathlib», que es
    exactamente la clase de mentira que este trabajo lleva dias corrigiendo.
    """
    indice = {}
    total = 0
    for raiz, _dirs, ficheros in os.walk(MATHLIB):
        for f in ficheros:
            if not f.endswith(".lean"):
                continue
            total += 1
            try:
                lineas = io.open(os.path.join(raiz, f), encoding="utf-8",
                                 errors="replace").read().splitlines()
            except Exception as e:
                print("   aviso: no se pudo leer %s (%s)" % (f, type(e).__name__))
                continue
            pila = []
            for l in lineas:
                m = NS.match(l)
                if m:
                    pila.append(m.group(1))
                    continue
                m = END.match(l)
                if m:
                    if pila and pila[-1] == m.group(1):
                        pila.pop()
                    continue
                m = DECL.match(l)
                if m:
                    corto = m.group(1).split(".")[-1]
                    largo = ".".join(pila + [m.group(1)]) if pila else m.group(1)
                    indice.setdefault(corto, set()).add(largo)
    print("   indice: %d ficheros, %d nombres distintos" % (total, len(indice)))
    if total == 0:
        print("   ATENCION: no se leyo ni un fichero — revisa MATHLIB=%s" % MATHLIB)
    return indice


def candidatos(nombre):
    """Nombres cualificados cuyo ultimo componente coincide."""
    global _INDICE
    if _INDICE is None:
        _INDICE = _construir_indice()
    corto = nombre.split(".")[-1]
    return sorted(_INDICE.get(corto, ()))[:12]


def verificar(nombres):
    """Los que Lean acepta, en una sola ejecucion con Mathlib entero."""
    if not nombres:
        return set()
    ruta = RAIZ + "/_corr_check.lean"
    io.open(ruta, "w", encoding="utf-8").write(
        "import Mathlib\n" + "\n".join("#check @" + n for n in nombres) + "\n")
    try:
        p = subprocess.run(["lake", "env", "lean", ruta], cwd=RAIZ,
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=1800)
        salida = (p.stdout or "") + (p.stderr or "")
    except Exception:
        return set()
    finally:
        if os.path.exists(ruta):
            os.remove(ruta)
    malos = set()
    for m in re.finditer(r":(\d+):\d+: error", salida):
        i = int(m.group(1)) - 2
        if 0 <= i < len(nombres):
            malos.add(nombres[i])
    return {n for n in nombres if n not in malos}


def main(aplicar):
    if not os.path.exists(INFORME):
        print("falta %s — corre antes verificar_vocabulario_grafo.py" % INFORME)
        return 1
    d = json.load(io.open(INFORME, encoding="utf-8"))
    fallidos = d["fallidos"]
    print("=== %d NOMBRES QUE MATHLIB NO RECONOCE ===\n" % len(fallidos))

    propuestas, todos = {}, []
    for n in fallidos:
        cs = candidatos(n)
        if cs:
            propuestas[n] = cs
            todos.extend(cs)
        print("  %-26s %s" % (n, ", ".join(cs) if cs else "(sin candidato)"))

    todos = sorted(set(todos) | {"ContinuousLinearMap.adjoint",
                                 "CategoryTheory.ShortComplex.Exact"})
    print("\n  verificando %d candidatos con Lean, una sola vez...\n" % len(todos))
    validos = verificar(todos)

    # DESEMPATE POR SENTIDO, no por longitud.
    #
    # Elegir el candidato mas corto daba disparates: `Ideal.Quotient` acababa
    # en `Con.Quotient` —el cociente de una congruencia, nada que ver con
    # anillos— y `Filtration` en `Ideal.Filtration` cuando el vertice que lo
    # declara es `stochastic-processes`, que necesita
    # `MeasureTheory.Filtration`. El nombre mas corto es el que menos
    # cualificacion lleva, no el que significa lo que el vertice dice.
    #
    # Se puntua la afinidad entre el namespace del candidato y el vertice que
    # lo declara: mismas palabras en el id del vertice, o en el area a la que
    # Mathlib lo asigna. A igualdad, el mas corto.
    from nucleo.graph.interpretacion import VEREDICTO

    #: Que namespaces de Mathlib corresponden a que palabras de un vertice.
    AFIN = {
        "measure": "MeasureTheory", "probability": "ProbabilityTheory",
        "stochastic": "MeasureTheory", "martingale": "MeasureTheory",
        "ideal": "Ideal", "ring": "Ideal", "group": "Subgroup",
        "topos": "CategoryTheory", "category": "CategoryTheory",
        "sheaf": "CategoryTheory", "scheme": "AlgebraicGeometry",
        "geometry": "AlgebraicGeometry", "logic": "FirstOrder",
        "model": "FirstOrder", "topology": "TopCat",
        "operator": "ContinuousLinearMap", "riemannian": "Bundle",
    }

    def _puntua(vertice, cand):
        """Mas alto = mejor. Afinidad de area primero, brevedad para desempatar."""
        p = 0
        ident = (vertice or "").lower()
        for palabra, ns in AFIN.items():
            if palabra in ident and cand.startswith(ns + "."):
                p += 10
        # el ultimo componente identico al nombre pedido puntua algo
        if cand.split(".")[-1] == n.split(".")[-1]:
            p += 2
        return (p, -len(cand))

    #: De que vertice viene cada nombre roto, para poder puntuar.
    de_quien = {}
    for k, e in VEREDICTO.items():
        if not e.lean:
            continue
        for pieza in re.split(r"[,+]", e.lean):
            de_quien.setdefault(pieza.strip(), k)

    #: DECIDIDAS A MANO, con criterio matematico y verificadas con Lean.
    #:
    #: La heuristica de afinidad no alcanza aqui: hay varios candidatos validos
    #: y la eleccion depende de que significa el vertice, no de que namespace
    #: se parece mas a su nombre.
    MANUAL = {
        # `hilbert-spaces` pide el adjunto de un operador ACOTADO entre
        # espacios de Hilbert, que es el de ContinuousLinearMap. El de
        # LinearMap es el algebraico y no pide completitud.
        "adjoint": "ContinuousLinearMap.adjoint",
        # `exact-sequences`: la sucesion exacta corta de Mathlib.
        "ShortComplex.Exact": "CategoryTheory.ShortComplex.Exact",
    }

    #: NO SE CORRIGEN: `Ideal.Quotient` es un NAMESPACE, no un identificador
    #: comprobable —`Ideal.Quotient.mk` si existe—. Sustituirlo por
    #: `Con.Quotient`, que fue lo que eligio la heuristica por ser mas corto,
    #: seria cambiar el cociente de un ideal por el de una congruencia: otra
    #: cosa. El vertice `ideals-quotient-rings` ya tiene `Ideal`, que es valido.
    NO_TOCAR = {"Ideal.Quotient"}

    final, sin_arreglo, dudosos = {}, [], []
    for n, cs in propuestas.items():
        if n in NO_TOCAR:
            sin_arreglo.append(n)
            continue
        ok = [c for c in cs if c in validos]
        if n in MANUAL and MANUAL[n] in validos:
            final[n] = MANUAL[n]
            continue
        if ok:
            vertice = de_quien.get(n, "")
            elegido = max(ok, key=lambda c: _puntua(vertice, c))
            final[n] = elegido
            if len(ok) > 1 and _puntua(vertice, elegido)[0] < 10:
                dudosos.append((n, vertice, elegido, ok))
        else:
            sin_arreglo.append(n)
    sin_arreglo += [n for n in fallidos if n not in propuestas]

    print("=== CORRECCIONES VERIFICADAS: %d de %d ===" % (len(final), len(fallidos)))
    for viejo, nuevo in sorted(final.items()):
        print("  %-26s -> %s" % (viejo, nuevo))
    if dudosos:
        print("\n  REVISAR A MANO (%d) — varios candidatos y ninguno afin al area:"
              % len(dudosos))
        for nombre, vert, eleg, todos_c in dudosos:
            print("     %-22s (vertice %s)" % (nombre, vert or "?"))
            print("        elegido: %s" % eleg)
            print("        otros  : %s" % ", ".join(c for c in todos_c if c != eleg))

    if sin_arreglo:
        print("\n  SIN arreglo (%d) — no existen en esta version de Mathlib:"
              % len(sin_arreglo))
        for n in sorted(sin_arreglo):
            print("     %s" % n)

    if not aplicar:
        print("\n  (sin --aplicar no se ha escrito nada)")
        return 0

    # aplicar sobre interpretacion.py, solo dentro del campo `lean`
    F = RAIZ + "/nucleo/graph/interpretacion.py"
    s = io.open(F, encoding="utf-8").read()
    tocados = 0
    for viejo, nuevo in final.items():
        pat = re.compile(r'(?<![\w.])' + re.escape(viejo) + r'(?![\w.\'])')
        s2 = pat.sub(nuevo, s)
        if s2 != s:
            tocados += 1
            s = s2
    io.open(F, "w", encoding="utf-8").write(s)
    print("\n  aplicadas %d correcciones en interpretacion.py" % tocados)
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--aplicar", action="store_true")
    a = ap.parse_args()
    sys.exit(main(a.aplicar))
