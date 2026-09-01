# -*- coding: utf-8 -*-
"""¿Cuánto de Mathlib queda FUERA del grafo? Y por tanto, qué nodos faltan.

Se decidio que el grafo debe cubrir toda la matematica, elemental incluida.
Antes de escribir fichas a mano conviene saber cuanto falta y donde, porque
Mathlib ya trae la taxonomia hecha: 7746 ficheros organizados en una jerarquia
de modulos por matematicos, verificada, y con los teoremas dentro.

COMO SE MIDE LA COBERTURA. Cada skill del grafo apunta a uno o mas modulos
(data/mathlib_modulos.json). Un skill cubre su modulo Y TODO SU SUBARBOL: quien
dice `Mathlib.Algebra.Group.Defs` esta hablando de la teoria de grupos entera.
Se mide que porcion de Mathlib cae bajo algun subarbol cubierto.

Y SE PESA POR TEOREMAS, no por numero de modulos. Un subarbol con 12 000
teoremas no vale lo mismo que uno con 30, y contar nodos daria una cobertura
falsamente buena o falsamente mala segun como este partido el arbol.

Lo que sale es, ademas de la cifra, LA LISTA DE LO QUE FALTA ordenada por
cuantos teoremas hay debajo: esos son exactamente los nodos que hay que crear,
y vienen con nombre y ruta ya puestos por Mathlib.

No gasta API.
"""
import collections
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MATH = "E:/Metamatematico/.lake/packages/mathlib/Mathlib"
MAPA = "E:/Metamatematico/data/mathlib_modulos.json"
SALIDA = "E:/Metamatematico/data/cobertura_taxonomia.json"

#: Profundidad a la que se considera que un modulo es un CONCEPTO.
#: `Mathlib.Algebra.Group` si; `Mathlib.Algebra.Group.Defs` es ya el detalle.
NIVEL = 2

TEO = re.compile(r"^\s*(?:@\[[^\]]*\]\s*)?(?:private\s+|protected\s+)?"
                 r"(?:theorem|lemma)\s+")

#: Fuera del recuento: no son matematica que el grafo deba modelar.
IGNORAR = {"Tactic", "Util", "Testing", "Deprecated", "Mathport", "Init", "Lean"}


def recorrer():
    """modulo de profundidad NIVEL -> (teoremas debajo, ficheros)."""
    concepto = collections.Counter()
    ficheros = collections.Counter()
    total = 0
    for raiz, _d, fs in os.walk(MATH):
        for f in fs:
            if not f.endswith(".lean"):
                continue
            rel = os.path.relpath(os.path.join(raiz, f), MATH)
            partes = rel[:-5].replace("\\", "/").split("/")
            if partes[0] in IGNORAR:
                continue
            clave = ".".join(partes[:NIVEL])
            try:
                txt = io.open(os.path.join(raiz, f), encoding="utf-8",
                              errors="replace").read()
            except Exception:
                continue
            k = sum(1 for l in txt.splitlines() if TEO.match(l))
            concepto[clave] += k
            ficheros[clave] += 1
            total += k
    return concepto, ficheros, total


def main():
    print("recorriendo la taxonomia de Mathlib...")
    concepto, ficheros, total = recorrer()
    print("  %d conceptos a profundidad %d · %d teoremas\n"
          % (len(concepto), NIVEL, total))

    por_skill = json.load(io.open(MAPA, encoding="utf-8"))["por_skill"]
    #: Prefijos que el grafo dice cubrir, sin el `Mathlib.` inicial.
    cubiertos = set()
    for mods in por_skill.values():
        for m in mods:
            p = m.replace("Mathlib.", "", 1).split(".")
            cubiertos.add(".".join(p[:NIVEL]))

    dentro = {k: v for k, v in concepto.items() if k in cubiertos}
    fuera = {k: v for k, v in concepto.items() if k not in cubiertos}
    t_dentro = sum(dentro.values())

    print("=== COBERTURA DEL GRAFO SOBRE MATHLIB ===\n")
    print("  conceptos cubiertos : %4d de %4d = %5.1f %%"
          % (len(dentro), len(concepto), 100.0 * len(dentro) / len(concepto)))
    print("  TEOREMAS cubiertos  : %6d de %6d = %5.1f %%"
          % (t_dentro, total, 100.0 * t_dentro / max(1, total)))
    print("  (la segunda es la que vale: pesa por cuanta matematica hay debajo)")

    # por area de primer nivel
    area_tot = collections.Counter()
    area_cub = collections.Counter()
    for k, v in concepto.items():
        a = k.split(".")[0]
        area_tot[a] += v
        if k in cubiertos:
            area_cub[a] += v
    print("\n=== POR AREA, pesado por teoremas ===\n")
    print("  %-22s %9s %9s %7s" % ("area", "cubiertos", "totales", "%"))
    for a, tot_a in area_tot.most_common(16):
        c = area_cub[a]
        print("  %-22s %9d %9d %6.1f%%" % (a, c, tot_a, 100.0 * c / max(1, tot_a)))

    print("\n=== LOS 25 CONCEPTOS QUE MAS FALTAN ===")
    print("    (ordenados por teoremas debajo: son los nodos a crear)\n")
    for k, v in sorted(fuera.items(), key=lambda x: -x[1])[:25]:
        print("  %-34s %6d teoremas  %3d ficheros" % (k, v, ficheros[k]))

    json.dump({"nivel": NIVEL, "conceptos": len(concepto),
               "conceptos_cubiertos": len(dentro),
               "teoremas": total, "teoremas_cubiertos": t_dentro,
               "por_area": {a: {"cubiertos": area_cub[a], "totales": area_tot[a]}
                            for a in area_tot},
               "faltan": dict(sorted(fuera.items(), key=lambda x: -x[1])[:120])},
              io.open(SALIDA, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("\n-> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    sys.exit(main())
