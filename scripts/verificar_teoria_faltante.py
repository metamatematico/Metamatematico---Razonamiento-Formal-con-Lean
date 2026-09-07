# -*- coding: utf-8 -*-
"""Comprueba con Lean los nombres de `teoria` que faltaban en 12 conceptos.

DE DONDE SALEN Y POR QUE NO ES UN HUECO CUALQUIERA.

46 conceptos curados no inyectan ningun nombre de Mathlib, y en su mayoria eso
es CORRECTO: estan marcados T, F u O —teorema, tecnica, clase de problemas— y
`VERTICES` solo admite S y C. Un teorema no es un objeto de la categoria, y
darle identidad categorica seria el error que el registro existe para impedir.

Pero `teoria` NO es la identidad categorica. El propio campo lo dice: es «los
nombres de Mathlib con los que se TRABAJA en este nodo», separado a proposito
de `lean` porque para group-theory la identidad es `GrpCat` y lo que hay que
importar es `Subgroup`. Un nodo marcado T puede tener `teoria` sin dejar de ser
un teorema — y de hecho es justo donde mas falta hace, porque el modelo
INVENTA lemas: de 28 nombres que propuso de memoria, los 21 inexistentes eran
todos lemas.

Y los nombres ya estaban escritos, en la nota que dejo quien interpreto el
nodo: «un lema; el funtor y si es objeto: CategoryTheory.yoneda».

QUE HACE ESTE SCRIPT. Coge esos nombres —curados a mano desde las notas, no
extraidos por regex: `Con` en «Con hTop los invariantes...» es la preposicion
española, y `DerivedCategory` en la nota de homotopy-theory nombra OTRO
vertice— y los pasa por `#check`. Deducir no es comprobar, y esa distincion es
la que explica que los nombres deducidos de rutas de modulo hundieran la
precision de 13,5 % a 3,2 %.

Una sola ejecucion con Mathlib entero importado, ~12 min. No gasta API.

    python -m scripts.verificar_teoria_faltante
"""
import io
import json
import os
import re
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RAIZ = "E:/Metamatematico"
SALIDA = RAIZ + "/data/teoria_faltante_verificada.json"
TIMEOUT = 2400

#: concepto -> nombres propuestos, CURADOS A MANO desde su nota.
#:
#: El criterio en cada caso: el objeto o el lema con el que se trabaja de
#: verdad en ese tema, no una traduccion del titulo del nodo.
PROPUESTAS = {
    # el sustrato si es un objeto, aunque «aritmetica cardinal» sea un tema
    "cardinal-arithmetic": ["Cardinal"],
    # un capitulo de geometria; los objetos viven en Sphere
    "circle-geometry": ["EuclideanGeometry.Sphere"],
    # es un teorema, y este es SU nombre en Mathlib
    "compactness-theorem": [
        "FirstOrder.Language.Theory.isSatisfiable_iff_isFinitelySatisfiable"],
    # una rama; los grados de Turing si son un orden parcial
    "computability-theory": ["TuringDegree"],
    # el ambiente en que se cuenta
    "enumerative-combinatorics": ["FintypeCat"],
    # la nota decide Top[W^-1]; Mathlib tiene el marco, no la instancia.
    # `Con` de la nota es la preposicion, y `DerivedCategory` es OTRO vertice.
    "homotopy-theory": ["CategoryTheory.MorphismProperty", "SSet",
                        "TopCat"],
    # la tecnica es inversion de Mobius, y su objeto es el algebra de
    # incidencia
    "inclusion-exclusion": ["IncidenceAlgebra"],
    "matching-theory": ["SimpleGraph.Subgraph.IsMatching"],
    "prime-factorization": ["UniqueFactorizationMonoid"],
    # el mecanismo se ejerce con estos dos
    "universal-properties": ["CategoryTheory.Limits.IsInitial",
                             "CategoryTheory.Functor.Representable"],
    "yoneda-lemma": ["CategoryTheory.yoneda"],
    # los axiomas son enunciados; el universo si es un objeto
    "zfc-axioms": ["ZFSet"],
}


def verificar(nombres):
    """Los que Lean acepta como termino. Una sola ejecucion."""
    ruta = RAIZ + "/_teoria_check.lean"
    io.open(ruta, "w", encoding="utf-8").write(
        "import Mathlib\n" + "\n".join("#check @" + n for n in nombres) + "\n")
    t0 = time.time()
    try:
        p = subprocess.run(["lake", "env", "lean", ruta], cwd=RAIZ,
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=TIMEOUT)
        salida = (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired:
        print("  TIMEOUT tras %.0f s — sin veredicto, no se concluye nada"
              % (time.time() - t0))
        return None, ""
    finally:
        if os.path.exists(ruta):
            os.remove(ruta)
    malos = set()
    for m in re.finditer(r":(\d+):\d+: error", salida):
        i = int(m.group(1)) - 2          # linea 1 = import, el resto los #check
        if 0 <= i < len(nombres):
            malos.add(nombres[i])
    return {n for n in nombres if n not in malos}, salida


def main():
    todos = sorted({n for v in PROPUESTAS.values() for n in v})
    print("%d conceptos · %d nombres propuestos" % (len(PROPUESTAS), len(todos)))

    # primero el indice, que es gratis y filtra lo obvio
    from nucleo.lean import nombres as N
    N._cargar()
    fuera = [n for n in todos if not N.existe(n)]
    if fuera:
        print("\n  no estan ni en el indice de %d nombres: %s"
              % (len(N._NOMBRES or ()), fuera))

    print("\ncomprobando con Lean (import Mathlib, ~12 min)...")
    buenos, salida = verificar(todos)
    if buenos is None:
        return 1

    print("\n=== VEREDICTO DE LEAN ===")
    aceptados = {}
    for sid, props in sorted(PROPUESTAS.items()):
        ok = [n for n in props if n in buenos]
        mal = [n for n in props if n not in buenos]
        estado = "OK " if ok else "---"
        print("  %s %-26s %s" % (estado, sid, ", ".join(ok) or "ninguno"))
        if mal:
            print("      RECHAZADOS por Lean: %s" % ", ".join(mal))
        if ok:
            aceptados[sid] = ok

    print("\n  %d de %d nombres aceptados · %d de %d conceptos con teoria"
          % (len(buenos), len(todos), len(aceptados), len(PROPUESTAS)))

    io.open(SALIDA, "w", encoding="utf-8").write(json.dumps(
        {"propuestos": PROPUESTAS, "aceptados": aceptados,
         "rechazados": sorted(set(todos) - buenos)},
        ensure_ascii=False, indent=1))
    print("  -> %s" % SALIDA)
    print("\n  Lo aceptado se escribe a mano en `teoria` en interpretacion.py,")
    print("  y DESPUES se mide contra ProofNet a volumen igualado: mas nombres")
    print("  no es mejor por si solo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
