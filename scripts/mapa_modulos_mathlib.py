# -*- coding: utf-8 -*-
"""
De concepto a modulo: el puente que le faltaba al grafo para elegir imports.

El grafo sabe que `ring-theory` es `RingCat` y que `ideals-quotient-rings` es
`Ideal` — 95% de esos nombres verificados con `#check`. Pero un import no pide
un identificador, pide un MODULO: `Mathlib.Algebra.Category.Ring.Basic`. Este
script construye ese mapa recorriendo el fuente y anotando en que fichero se
declara cada nombre.

POR QUE IMPORTA. `_normalize_code` descarta `import Mathlib` —cargarlo entero
se medio en 742 s, muy por encima del timeout— y lo sustituye por una cabecera
estrecha mas imports elegidos POR PALABRAS CLAVE del enunciado. Ese es hoy el
punto donde se decide que ve Lean, y lo decide un diccionario de terminos, no
la estructura de conceptos que el sistema ya tiene.

El mapa se guarda en disco: recorrer Mathlib entero tarda, y no cambia hasta
que cambie la version.

    python -m scripts.mapa_modulos_mathlib
"""
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RAIZ = "E:/Metamatematico"
MATHLIB = RAIZ + "/.lake/packages/mathlib/Mathlib"
SALIDA = RAIZ + "/data/mathlib_modulos.json"

DECL = re.compile(
    r"^\s*(?:@\[[^\]]*\]\s*)?(?:private\s+|protected\s+|noncomputable\s+)*"
    r"(?:structure|def|abbrev|class|inductive)\s+([A-Za-z_][\w.']*)")
NS = re.compile(r"^\s*namespace\s+([A-Za-z_][\w.']*)")
END = re.compile(r"^\s*end\s+([A-Za-z_][\w.']*)")


def modulo_de(ruta):
    """`.../Mathlib/Algebra/Ring/Basic.lean` -> `Mathlib.Algebra.Ring.Basic`."""
    rel = os.path.relpath(ruta, os.path.dirname(MATHLIB))
    return rel[:-5].replace(os.sep, ".").replace("/", ".")


def construir():
    """nombre cualificado -> modulo donde se declara."""
    mapa, ficheros = {}, 0
    for raiz, _d, fs in os.walk(MATHLIB):
        for f in fs:
            if not f.endswith(".lean"):
                continue
            ruta = os.path.join(raiz, f)
            ficheros += 1
            try:
                lineas = io.open(ruta, encoding="utf-8",
                                 errors="replace").read().splitlines()
            except Exception:
                continue
            mod, pila = modulo_de(ruta), []
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
                    largo = ".".join(pila + [m.group(1)]) if pila else m.group(1)
                    # el primero gana: los ficheros `Basic` suelen ir antes y
                    # son los que uno quiere importar
                    mapa.setdefault(largo, mod)
    return mapa, ficheros


def main():
    print("recorriendo el fuente de Mathlib...")
    mapa, ficheros = construir()
    print("  %d ficheros, %d nombres cualificados" % (ficheros, len(mapa)))
    if not mapa:
        print("  ATENCION: mapa vacio — revisa MATHLIB=%s" % MATHLIB)
        return 1

    # cobertura sobre el vocabulario del grafo
    from nucleo.graph.interpretacion import VEREDICTO, VERTICES
    invalidos = {"EuclideanGeometry", "Ideal.Quotient", "QuotientGroup",
                 "RelCWComplex", "Turing.TM0", "Turing.TM1"}
    por_skill, sin_modulo = {}, []
    for k, e in VEREDICTO.items():
        if e.marca not in VERTICES or not e.lean:
            continue
        mods = []
        for pieza in re.split(r"[,+]", e.lean):
            n = pieza.strip()
            if not n or n in invalidos:
                continue
            m = mapa.get(n)
            if m:
                mods.append(m)
            else:
                sin_modulo.append((k, n))
        if mods:
            por_skill[k] = sorted(dict.fromkeys(mods))[:3]

    print("\n=== COBERTURA SOBRE EL GRAFO ===")
    print("  skills con al menos un modulo: %d" % len(por_skill))
    print("  nombres validos sin modulo   : %d" % len(sin_modulo))
    for k, n in sin_modulo[:8]:
        print("     %-28s %s" % (k, n))

    print("\n  ejemplos:")
    for k in list(por_skill)[:6]:
        print("     %-26s -> %s" % (k, ", ".join(por_skill[k])))

    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    io.open(SALIDA, "w", encoding="utf-8").write(json.dumps(
        {"por_skill": por_skill, "nombres": len(mapa)},
        ensure_ascii=False, indent=2))
    print("\n  -> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    sys.exit(main())
