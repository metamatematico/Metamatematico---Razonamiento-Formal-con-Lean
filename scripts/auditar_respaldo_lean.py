"""
Audita que TODA afirmacion categorica de Python tenga respaldo en Lean.

POR QUE
-------
`nucleo/graph/` y `nucleo/mes/` implementan teoria de categorias a mano: no hay
ninguna libreria detras, solo dataclasses, dicts y BFS. Eso significa que cada
propiedad categorica es una afirmacion nuestra hasta que Lean la respalda, y
esta sesion ya ha enseñado lo que cuesta:

  · reachable_from seguia TRANSLATION -> colimites espurios (= tactic-simp)
  · build_join_for_pattern FABRICABA vertices -> el punto fijo no convergia
  · patterns.py usaba ∃h donde la propiedad universal pide ∃!h

Los tres estaban en codigo que "funcionaba". Ninguno fallaba ruidosamente.

QUE HACE ESTE SCRIPT
--------------------
1. Extrae de los .lean todas las declaraciones formales realmente presentes.
2. Comprueba que cada entrada del mapeo apunta a un teorema que EXISTE (si se
   renombra en Lean, la auditoria falla en vez de mentir).
3. Reporta que operaciones de Python quedan SIN respaldo, que es el numero que
   importa.
4. Cuenta los `sorry` reales preguntandoselo al compilador, no al grep.

USO
---
    python scripts/auditar_respaldo_lean.py            # informe
    python scripts/auditar_respaldo_lean.py --sorry    # + consulta a lake
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
LEAN = RAIZ / "MetamathProver" / "CategoryFoundations"
SALIDA = RAIZ / "data" / "respaldo_lean.json"

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

#: EL MAPEO. Cada operacion categorica de Python -> el teorema de Lean que la
#: respalda, o None si no lo tiene.
#:
#: Una entrada con None no es una omision: es el resultado que este script
#: existe para reportar.
MAPEO: list[tuple[str, str, str | None, str]] = [
    # (modulo, operacion, teorema en Lean, que afirma)
    ("category.py", "identity", "preorder_is_thin",
     "id_a existe y es unico en Hom(a,a)"),
    ("category.py", "compose", "preorder_comp_trans",
     "la composicion existe y es asociativa por transitividad"),
    ("category.py", "hom", "thin_unique_hom",
     "Hom(a,b) tiene a lo sumo un elemento"),
    ("category.py", "reachable_from", "reachable_refl",
     "el cierre transitivo-reflexivo es el preorden"),
    ("category.py", "is_preorder_leq", "preorder_le_of_hom",
     "a<=b syss hay morfismo a->b"),
    ("category.py", "classify_link", "composite_of_simple_is_simple",
     "simple = factoriza por un cluster; los simples cierran por composicion"),
    ("category.py", "verify_axioms", "path_category_axioms",
     "los axiomas de categoria valen en la categoria libre del quiver"),
    ("category.py", "apply_complexity_order", "hierarchy_well_founded",
     "la iteracion de cn alcanza punto fijo"),
    ("category.py", "verify_pillar_multiplicity", "MultiplicityPrinciple",
     "existen patrones homologos con el mismo colimite"),

    ("complexity.py", "find_cocones", "isCocone",
     "co-cono = cota superior de las componentes"),
    ("complexity.py", "find_colimit", "isColimitInFiniteCategory",
     "colimite = co-cono minimal, decidible en categoria finita"),
    ("complexity.py", "find_existing_join", "join_implies_colimit",
     "el join es el colimite"),
    ("complexity.py", "build_join_for_pattern", "colimit_is_least_upper_bound",
     "la universalidad es un TEST, no una construccion"),
    ("complexity.py", "build_hierarchy_to_fixpoint", "hierarchy_well_founded",
     "la iteracion termina"),
    ("complexity.py", "compute_complexity_order", "cn_join_gt_component",
     "cn(join) > cn de cada componente"),
    ("complexity.py", "_find_upper_bounds", "colimit_is_upper_bound",
     "las cotas superiores del patron"),

    ("patterns.py", "verify_cocone", "isCocone",
     "el co-cono conmuta"),
    ("patterns.py", "is_join", "join_is_minimal_upper_bound",
     "minimalidad entre las cotas superiores"),
    ("patterns.py", "verify_universal_property", "join_mediating_morphism_unique",
     "el mediador existe y es UNICO (∃!h, no ∃h)"),
    ("patterns.py", "build_colimit", "isJoin_iff_nonempty_isColimit",
     "IsJoin equivale a IsColimit de Mathlib"),
    ("patterns.py", "are_homologous", "Homologos",
     "dos descomposiciones distintas del mismo colimite"),
    ("patterns.py", "verify_multiplicity_principle", "multiplicity_gives_robustness",
     "la multiplicidad da robustez: perder una descomposicion no destruye el colimite"),
    ("patterns.py", "find_homologous_patterns", "colimite_unico",
     "el colimite de un patron es unico, luego la homologia esta bien definida"),

    ("functor.py", "construir_funtor", "proyeccion_es_funtor",
     "una proyeccion monotona es funtor en categorias thin"),
    ("functor.py", "verificar_functorialidad", "proyeccion_es_funtor",
     "las dos leyes de funtor"),
    ("functor.py", "verificar_preservacion_colimites", "functor_preserves_cocone",
     "los funtores preservan co-conos"),
    ("functor.py", "verificar_preservacion_colimites (minimalidad)",
     "functor_not_preserves_join",
     "y NO preservan la minimalidad: contraejemplo finito"),
    ("functor.py", "CategoriaAgentes.alcanzables_desde", "refleja_no_alcanzabilidad",
     "pi refleja la no-alcanzabilidad"),

    ("evolution.py", "complexify", None,
     "complexificacion de Ehresmann como funtor de transicion"),
    ("evolution.py", "transition_functor", None,
     "el functor de transicion entre configuraciones"),
    ("evolution.py", "detect_emergence", None,
     "deteccion de emergencia"),
]


def declaraciones_lean() -> dict[str, str]:
    """Todas las declaraciones formales presentes, con su fichero."""
    rx = re.compile(
        r"^(?:theorem|lemma|def|structure|instance|axiom|opaque)\s+"
        r"([A-Za-z_][A-Za-z0-9_'.₀-₉]*)", re.M)
    out: dict[str, str] = {}
    for f in sorted(LEAN.glob("*.lean")):
        for m in rx.finditer(f.read_text(encoding="utf-8")):
            out[m.group(1)] = f.name
    return out


def sorries_reales() -> list[str]:
    """Le pregunta al compilador, no al grep: un `sorry` en un comentario no cuenta."""
    lake = Path.home() / ".elan" / "bin" / "lake"
    try:
        r = subprocess.run([str(lake), "build"], cwd=RAIZ, capture_output=True,
                           text=True, timeout=900)
    except Exception as e:
        return [f"(no pude ejecutar lake: {e})"]
    return [l.strip() for l in (r.stdout + r.stderr).splitlines()
            if "uses `sorry`" in l]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sorry", action="store_true",
                    help="ejecuta lake build para contar los sorry reales")
    args = ap.parse_args()

    decls = declaraciones_lean()
    print(f"Declaraciones formales en CategoryFoundations: {len(decls)}")
    print(f"Entradas auditadas: {len(MAPEO)}\n")

    respaldadas, sin_respaldo, rotas = [], [], []
    for modulo, op, teorema, afirma in MAPEO:
        if teorema is None:
            sin_respaldo.append((modulo, op, afirma))
        elif teorema not in decls:
            rotas.append((modulo, op, teorema))
        else:
            respaldadas.append((modulo, op, teorema, decls[teorema], afirma))

    print("== RESPALDADAS ==========================================")
    for modulo, op, t, fich, afirma in respaldadas:
        print(f"   {modulo:14s} {op:42s} -> {t}")
        print(f"   {'':14s} {'':42s}    {fich}: {afirma}")

    if rotas:
        print("\n== MAPEO ROTO (el teorema ya no existe) =================")
        for modulo, op, t in rotas:
            print(f"   {modulo:14s} {op:42s} -> {t}  NO ENCONTRADO")

    print("\n== SIN RESPALDO FORMAL ==================================")
    for modulo, op, afirma in sin_respaldo:
        print(f"   {modulo:14s} {op:42s}    {afirma}")

    n = len(MAPEO)
    print(f"\n{'':4s}respaldadas    {len(respaldadas):3d}/{n}  "
          f"({100*len(respaldadas)/n:.0f} %)")
    print(f"{'':4s}sin respaldo   {len(sin_respaldo):3d}/{n}")
    print(f"{'':4s}mapeo roto     {len(rotas):3d}/{n}")

    informe = {
        "declaraciones_lean": len(decls),
        "auditadas": n,
        "respaldadas": [{"modulo": m, "operacion": o, "teorema": t,
                         "fichero": f, "afirma": a}
                        for m, o, t, f, a in respaldadas],
        "sin_respaldo": [{"modulo": m, "operacion": o, "afirma": a}
                         for m, o, a in sin_respaldo],
        "mapeo_roto": [{"modulo": m, "operacion": o, "teorema": t}
                       for m, o, t in rotas],
    }

    if args.sorry:
        print("\n== SORRY REALES (segun el compilador) ===================")
        s = sorries_reales()
        informe["sorries"] = s
        for l in s:
            print(f"   {l}")
        if not s:
            print("   ninguno")

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(informe, ensure_ascii=False, indent=2),
                      encoding="utf-8")
    print(f"\nInforme -> {SALIDA}")
    return 1 if rotas else 0


if __name__ == "__main__":
    raise SystemExit(main())
