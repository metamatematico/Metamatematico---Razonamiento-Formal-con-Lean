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
import ast
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
    ("category.py", "classify_link", "simple_of_cluster",
     "simple = INDUCIDO por un cluster entre descomposiciones (Ehresmann)."
     " La lectura por factorizacion, que es la que estuvo implementada, esta"
     " en composite_of_simple_is_simple y NO es la definicion"),
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
    ("complexity.py", "TrivialColimit", "join_propio_rompe_aciclicidad",
     "si el colimite es una componente el patron TIENE colimite pero romperia"
     " AciclicoMulti: no es hueco y no entra en la recursion de cn"),

    ("patterns.py", "verify_cocone", "isCocone",
     "el co-cono conmuta"),
    ("patterns.py", "is_join", "join_is_minimal_upper_bound",
     "minimalidad entre las cotas superiores"),
    ("patterns.py", "verify_universal_property", "join_mediating_morphism_unique",
     "el mediador existe y es UNICO (∃!h, no ∃h)"),
    ("patterns.py", "build_colimit", "isJoin_iff_nonempty_isColimit",
     "IsJoin equivale a IsColimit de Mathlib"),
    ("complexificacion.py", "complexificar", "eta_es_colimite",
     "todo patron adquiere colimite en K': el hueco se cierra por construccion"),
    ("complexificacion.py", "_id_emergente", "SC_homologos_mismo_colimite",
     "el id deriva del CONJUNTO DE COTAS: homologos comparten objeto (SC)"),
    ("complexificacion.py", "ObjetoEmergente", "hueco_iff_objeto_nuevo",
     "los huecos son exactamente los objetos que no vienen de K"),
    ("complexificacion.py", "ResultadoComplexificacion", "eta_eq_iota_of_isLUB",
     "lo que ya tenia colimite no recibe objeto nuevo: la preservacion"),
    ("complexificacion.py", "_minimales", "factorizacion_unica",
     "conectar solo con las cotas minimales da el mismo orden; la extension"
     " esta determinada de modo unico por K y la preservacion de colimites"),

    ("no_delgado.py", "multiplicidad", "hom_no_es_delgado",
     "donde |Hom(a,b)| > 1; con 0 pares lub_de_lubs se aplica a todo el grafo"),
    ("no_delgado.py", "caminos", "path_category_axioms",
     "Hom en la categoria LIBRE: los caminos, donde la composicion no es ambigua"),
    ("no_delgado.py", "es_cocono_libre", "cota_superior_no_implica_cocono",
     "co-cono = familia compatible bajo precomposicion, NO cota superior"),
    ("no_delgado.py", "comparar_cocono", "delgado_cocono_automatico",
     "con |Hom| <= 1 la conmutacion se cumple sola y las dos lecturas coinciden"),
    ("no_delgado.py", "congruencia_automatica", "delgado_cocono_automatico",
     "solo identifica aristas que difieren en el TIPO: la semantica que el"
     " propio sistema declara, no una decision nueva"),
    ("no_delgado.py", "pendientes_de_decidir", "cota_superior_no_implica_cocono",
     "las igualdades de caminos que la conmutacion exige y nadie ha declarado"),
    ("no_delgado.py", "registrar_morfismos_certificados", "no_hay_iso",
     "los tres morfismos group-theory -> ring-theory no son isomorfos entre si"),

    ("no_delgado.py", "Congruencia", "cocono_monotono_en_la_congruencia",
     "mas identificaciones, mas co-conos: el espectro esta ordenado"),
    ("no_delgado.py", "hay_cocono_cong", "esCoconoMod",
     "co-cono modulo una congruencia declarada"),
    ("no_delgado.py", "espectro", "el_espectro_no_es_trivial",
     "los dos extremos difieren, luego hay algo que elegir en medio"),
    ("no_delgado.py", "congruencia_respeta_certificados", "no_hay_iso",
     "la congruencia DELGADA identifica morfismos que Lean demostro distintos:"
     " no es una simplificacion, es una identificacion falsa"),

    ("patterns.py", "hay_cluster", "Conectados",
     "cluster dirigido P->Q: toda componente de P alcanza alguna de Q (todo-existe)"),
    ("patterns.py", "decomposiciones_de", "Descomposicion",
     "los patrones cuyo colimite es el objeto; que haya varios es el MP"),
    ("patterns.py", "campos_operativos_isomorfos", None,
     "heuristica estructural, NO la homologia de Ehresmann"),
    ("patterns.py", "verify_multiplicity_principle", "multiplicidad_necesaria_para_complejidad",
     "sin Principio de Multiplicidad todo compuesto de simples es simple: MP es"
     " condicion NECESARIA de la complejidad, no un adorno sobre robustez"),
    ("patterns.py", "detect_pattern_in_graph", "enlaces_complejos_existen",
     "modelo concreto: dos enlaces simples cuya composicion no es simple"),
    ("patterns.py", "_connected_by_cluster", "complex_needs_unconnected",
     "un enlace complejo exige descomposiciones intermedias NO conectadas"),
    ("complexity.py", "_detect_convergence_patterns", "MP_alcanzable_en_preorden",
     "emite tambien las descomposiciones por subconjunto: MP es alcanzable"),
    ("complexity.py", "compute_complexity_order (multi)", "hierarchy_well_founded_multi",
     "con varias descomposiciones, el MAXIMO converge; asignar oscilaba"),
    ("patterns.py", "son_homologos", "Homologos",
     "homologia de Ehresmann: mismo colimite"),
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

    # La FIBRACION: una condicion ADEMAS de la funtorialidad. Que pi sea
    # funtor dice que esta bien definida; que sea fibracion dice que la base
    # SIRVE. Medido sobre el grafo real: NO lo es (0,3 % de los pares), y el
    # cuello de botella son los 29 morfismos que cruzan de area de 230.
    ("fibracion.py", "levantar", "cartesiano_unico",
     "el levantamiento cartesiano es unico salvo equivalencia"),
    ("fibracion.py", "verificar_fibracion", "EsFibracion",
     "todo b' <= pi(e) se levanta cartesianamente a e"),
    ("fibracion.py", "verificar_fibracion (para que sirve)", "reindexado_monotono",
     "en una fibracion cada flecha de la base induce una aplicacion MONOTONA"
     " fibra(b) -> fibra(b'): la manera de trasladar una pregunta de un area"
     " a otra"),
    ("fibracion.py", "verificar_fibracion (encadenar areas)",
     "reindexado_compuesto",
     "restringir por b' y luego por b'' es lo mismo que restringir por b''"),
    ("fibracion.py", "verificar_fibracion (no es vacuo)",
     "no_toda_monotona_es_fibracion",
     "hay monotonas que NO son fibracion: contraejemplo finito, sin el"
     " comprobar la condicion no distinguiria nada"),

    # Los nombres reales. El mapeo decia `complexify`, `transition_functor` y
    # `detect_emergence`, que NO EXISTEN; la auditoria no lo detectaba porque
    # solo validaba el lado de Lean.
    ("evolution.py", "TransitionFunctor", "comp",
     "funtor parcial entre instantaneas: none = objeto eliminado"),
    ("evolution.py", "compose", "comp_assoc",
     "la composicion de transiciones es asociativa"),
    ("evolution.py", "verify_compatibility", "compatible_iff",
     "compatibilidad (Def 3.2) = ley de funtor sobre el orden del tiempo"),
    ("evolution.py", "apply_option", "eliminado_es_absorbente",
     "lo eliminado no vuelve: ninguna composicion posterior lo recupera"),
    ("evolution.py", "measure_emergence", "soloCrece_cadena",
     "emergence_ratio es comparable entre tiempos si nada se elimina"),
    ("evolution.py", "detect_complex_links", "complex_needs_unconnected",
     "un enlace complejo exige descomposiciones intermedias no conectadas"),
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


#: Donde vive cada modulo del mapeo.
UBICACION = {
    "category.py": "nucleo/graph/category.py",
    "complexity.py": "nucleo/graph/complexity.py",
    "functor.py": "nucleo/graph/functor.py",
    "patterns.py": "nucleo/mes/patterns.py",
    "evolution.py": "nucleo/graph/evolution.py",
    "complexificacion.py": "nucleo/graph/complexificacion.py",
    "no_delgado.py": "nucleo/graph/no_delgado.py",
}


def operaciones_python() -> dict:
    """
    Las funciones, metodos y clases que existen de verdad en cada modulo.

    La auditoria validaba solo el lado de Lean, de modo que una entrada podia
    nombrar una funcion de Python INEXISTENTE y pasar como "sin respaldo" sin
    que nadie lo notara. Ocurrio: `complexify`, `transition_functor` y
    `detect_emergence` no existen; las reales se llaman `apply_option`,
    `TransitionFunctor` y `measure_emergence`.
    """
    out = {}
    for modulo, ruta in UBICACION.items():
        f = RAIZ / ruta
        if not f.exists():
            out[modulo] = set()
            continue
        arbol = ast.parse(f.read_text(encoding="utf-8"))
        nombres = set()
        for nodo in ast.walk(arbol):
            if isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef,
                                 ast.ClassDef)):
                nombres.add(nodo.name)
        out[modulo] = nombres
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

    ops = operaciones_python()
    fantasma = []
    for modulo, op, _, _ in MAPEO:
        base = op.split(".")[0].split(" ")[0]
        conocidas = ops.get(modulo)
        if conocidas is not None and base not in conocidas:
            fantasma.append((modulo, op))

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
    print(f"{'':4s}op. fantasma   {len(fantasma):3d}/{n}")

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
        "operaciones_fantasma": [{"modulo": m, "operacion": o}
                                 for m, o in fantasma],
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
    return 1 if (rotas or fantasma) else 0


if __name__ == "__main__":
    raise SystemExit(main())
