# -*- coding: utf-8 -*-
"""Propone identificadores de Mathlib para los huecos del grafo, POR MODULO.

EL HUECO
--------
45 de los 159 conceptos curados no aportan NINGUN identificador al prompt. Y
de 62 enunciados reales de Mathlib que nombran algo fuera de la cabecera fija,
en 43 el grafo no tiene ningun nodo que lo cubra. Ningun recorrido recupera lo
que no esta: hay que curar.

DOS VIAS, Y SOLO UNA FUNCIONA. ESTO IMPORTA.
--------------------------------------------
La primera version de este guion buscaba en Mathlib POR LAS PALABRAS CLAVE del
concepto. Sale mal, y el resultado se conserva aqui porque es evidencia:

    lean-kernel     ->  ProbabilityTheory.Kernel     (caso «kernel»)
    zfc-axioms      ->  Order.Coframe.MinimalAxioms  (caso «axioms»)
    residue-theorem ->  SecondCountableTopologyEither
    fol-deduction   ->  TopologicalSpace

Es el mismo fallo que este repositorio ya tiene medido tres veces —el indice
completo de 217 419 nombres da 1,53 % de precision, que empata con el azar—
y es la FRONTERA DE FORMALIZACION otra vez: buscar por palabra sobre nombres
de Mathlib es aplicar una herramienta de ANTES de la frontera a un indice de
DESPUES. Los nombres de Mathlib codifican estructura de tipos, no prosa.

La via que SI funciona es la contraria: partir del MODULO y quedarse con sus
sustantivos mas citados.

    Computability.DFA      ->  DFA.eval, Language.IsRegular
    Computability.Partrec  ->  Computable, Partrec, Nat.Partrec
    Algebra.Lie.Basic      ->  LieEquiv, LieHom
    Analysis.Complex.Circle->  Circle, Circle.exp

La clave que sirve es ESTRUCTURAL, no lexica. Dado el modulo, los nombres
canonicos salen solos; lo dificil —que modulo corresponde a que concepto— es
un juicio matematico y no lo da ninguna busqueda.

DE DONDE SALEN LOS NOMBRES
--------------------------
De `data/sustantivos_mathlib.jsonl`: 34 084 sustantivos LEIDOS DE SU
DECLARACION, con su modulo y cuantas veces se citan. No se deduce nada de la
ruta, que es justo lo que se midio que falla: de los 447 identificadores
deducidos asi, 95 NO EXISTEN. De los leidos, `#check` sobre una muestra da
200 de 200.

Las citas ordenan: distinguen el nombre canonico de la variante.

ESTO PROPONE, NO DECIDE. Y NADA SE ADOPTA SIN MEDIRLO
-----------------------------------------------------
Que un nombre exista no lo hace CORRECTO para el concepto. Cada tanda que
entre en `interpretacion.py` se comprueba con

    python -m scripts.recuperacion_contra_proofnet

—precision y cobertura contra 371 formalizaciones de oro, con su modelo nulo,
y sin gastar API—. Si la precision baja, no entra. Ya paso: ofrecer los
sustantivos del modulo de cada nodo GENERADO bajaba de 14,0 % a 11,5 %.

    python -m scripts.proponer_vocabulario                # los que hacen falta
    python -m scripts.proponer_vocabulario --modulo Mathlib.Computability.DFA
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

SUSTANTIVOS = os.path.join(RAIZ, "data", "sustantivos_mathlib.jsonl")
EMERGE = os.path.join(RAIZ, "data", "lo_que_falta_emerge.json")
SALIDA = os.path.join(RAIZ, "data", "vocabulario_propuesto.json")


def por_modulo() -> dict:
    """modulo -> sus sustantivos, ya ordenados por citas."""
    if not os.path.exists(SUSTANTIVOS):
        return {}
    fuera = {}
    for l in io.open(SUSTANTIVOS, encoding="utf-8"):
        l = l.strip()
        if not l:
            continue
        try:
            s = json.loads(l)
        except ValueError:
            continue
        fuera.setdefault(s.get("modulo") or "", []).append(s)
    for m in fuera:
        fuera[m].sort(key=lambda x: -int(x.get("citas") or 0))
    return fuera


def modulos_que_hacen_falta() -> list:
    """Los que enunciados reales nombraron y el grafo no cubre."""
    if not os.path.exists(EMERGE):
        return []
    d = json.load(io.open(EMERGE, encoding="utf-8"))
    fuera = []
    for x in d.get("detalle", []):
        if x.get("veredicto") != "sin_nodo":
            continue
        for m in x.get("faltan", []):
            if m not in fuera:
                fuera.append(m)
    return fuera


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--modulo", default="", help="solo ese modulo")
    ap.add_argument("--k", type=int, default=4,
                    help="cuantos sustantivos por modulo")
    args = ap.parse_args()

    import warnings
    import logging
    warnings.filterwarnings("ignore")
    logging.disable(logging.WARNING)

    sus = por_modulo()
    if not sus:
        print("falta data/sustantivos_mathlib.jsonl. Sin el no hay de donde\n"
              "proponer, y deducir de la ruta es lo que se midio que falla.")
        return 1

    mods = [args.modulo] if args.modulo else modulos_que_hacen_falta()
    if not mods:
        print("no hay modulos pendientes. Corre antes:\n"
              "   python -m scripts.imports_que_discriminan --por-area 8\n"
              "   python -m scripts.lo_que_falta_emerge")
        return 1

    print("sustantivos leidos de su declaracion : %d en %d modulos"
          % (sum(len(v) for v in sus.values()), len(sus)))
    print("modulos que enunciados reales pidieron y el grafo no cubre: %d\n"
          % len(mods))

    propuesta, vacios = {}, []
    for m in sorted(mods):
        ss = sus.get(m, [])[:args.k]
        if not ss:
            vacios.append(m)
            continue
        propuesta[m] = [{"nombre": s["nombre"], "tipo": s.get("tipo") or "",
                         "citas": int(s.get("citas") or 0)} for s in ss]
        print("%s" % m.replace("Mathlib.", ""))
        for s in ss:
            print("    %-36s %-10s citas %d"
                  % (s["nombre"][:36], (s.get("tipo") or "")[:10],
                     int(s.get("citas") or 0)))
        print()

    if vacios:
        print("SIN SUSTANTIVOS PROPIOS (%d): %s" % (len(vacios), ", ".join(
            v.replace("Mathlib.", "") for v in vacios[:8])))
        print("   Son modulos que solo aportan teoremas, no tipos nuevos. El")
        print("   grafo aporta SUSTANTIVOS: de sus 176 identificadores ninguno")
        print("   es un teorema. Estos no le tocan.")

    json.dump({"propuesta": propuesta, "sin_sustantivos": vacios},
              io.open(SALIDA, "w", encoding="utf-8"), indent=1,
              ensure_ascii=False)
    print("\n-> %s" % SALIDA)
    print("\nEL PASO QUE FALTA ES UN JUICIO, NO UNA BUSQUEDA: decidir a que")
    print("concepto del grafo pertenece cada modulo, o si hace falta uno")
    print("nuevo. Y despues, medir:")
    print("   python -m scripts.recuperacion_contra_proofnet")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
