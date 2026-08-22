"""
Construye pi: Skills -> Agentes sobre el grafo real y verifica sus leyes.

Produce data/funtor_pi.json, que es la fuente de todas las cifras del
reporte docs/funtor_pi.tex. Ninguna cifra del reporte se escribe a mano.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SALIDA = RAIZ / "data" / "funtor_pi.json"


def construir_grafo():
    """El mismo grafo que usa el sistema: 10 fundacionales + los dominios."""
    sys.argv = ["x"]
    from scripts.train_gnn_ppo import build_skill_graph
    return build_skill_graph()


def descubrir_colimites(graph):
    """Ejecuta el descubrimiento de colimites hasta el punto fijo."""
    from nucleo.mes.patterns import PatternManager, ColimitBuilder
    from nucleo.graph.complexity import build_hierarchy_to_fixpoint

    pm = PatternManager()
    cb = ColimitBuilder(pm)
    cn, huecos = build_hierarchy_to_fixpoint(graph, pm, cb)

    # Los colimites viven en el ColimitBuilder, no en el patron: cada uno
    # lleva pattern_id (de quien es colimite) y skill_id (que objeto ES).
    colimites = []
    for col in cb.all_colimits:
        pat = pm.get_pattern(col.pattern_id) if col.pattern_id else None
        comps = list(getattr(pat, "component_ids", []) or []) if pat else []
        if col.skill_id and comps:
            colimites.append((comps, col.skill_id))
    return cn, huecos, colimites


def main() -> int:
    from nucleo.graph.functor import (
        construir_funtor, verificar_functorialidad,
        verificar_preservacion_colimites, OBJETO_BASE,
    )

    g = construir_grafo()
    print(f"Grafo de skills: {len(g.skills)} objetos, {len(g.morphisms)} morfismos\n")

    print("== construccion de pi ==================================")
    pi = construir_funtor(g, solo_jerarquia=True)
    A = pi.codominio
    print(f"   codominio: {A}")
    print(f"   morfismos de Skills colapsados a identidad: {pi.colapsados}")
    print(f"   objetos: {sorted(A.objetos)}")
    print()
    print("   morfismos inducidos, por multiplicidad:")
    for m in sorted(A.morfismos.values(), key=lambda x: -x.multiplicidad)[:12]:
        print(f"      {m.multiplicidad:3d}  {m.source_id} -> {m.target_id}")

    print()
    print("== leyes de funtor =====================================")
    ver = verificar_functorialidad(pi, g, solo_jerarquia=True)
    for k, v in ver.items():
        print(f"   {k:32s} {v}")

    print()
    print("== colimites ===========================================")
    cn, huecos, colimites = descubrir_colimites(g)
    print(f"   descubiertos: {len(colimites)} · huecos: {len(huecos)}")
    pres = verificar_preservacion_colimites(pi, g, colimites)
    print(f"   co-cono preservado    : {pres['cocono_preservado']}/{pres['colimites']}")
    print(f"   colimite preservado   : {pres['colimite_preservado']}/{pres['colimites']}")
    print(f"   colapsados a un punto : {pres['colapsados_a_un_punto']}/{pres['colimites']}")
    print()
    for d in pres["detalle"][:10]:
        marca = "colapsa" if d["colapsado"] else ("cocono" if d["cocono"] else "NO")
        comps = ", ".join(d["componentes"][:3])
        print(f"      [{marca:7s}] join({comps}) = {d['join']}")
        print(f"                  pi: {d['pi_componentes']} -> {d['pi_join']}")

    informe = {
        "grafo": {"objetos": len(g.skills), "morfismos": len(g.morphisms)},
        "codominio": {
            "objetos": sorted(A.objetos),
            "n_objetos": len(A.objetos),
            "n_morfismos": len(A.morfismos),
            "morfismos": [
                {"de": m.source_id, "a": m.target_id,
                 "multiplicidad": m.multiplicidad, "tipos": sorted(m.tipos)}
                for m in sorted(A.morfismos.values(),
                                key=lambda x: (-x.multiplicidad, x.source_id))
            ],
            "objeto_base": OBJETO_BASE,
        },
        "colapsados_a_identidad": pi.colapsados,
        "functorialidad": ver,
        "preservacion": {k: v for k, v in pres.items() if k != "detalle"},
        "preservacion_detalle": pres["detalle"],
        "max_cn": max(cn.values()) if cn else 0,
        "n_huecos": len(huecos),
    }
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    SALIDA.write_text(json.dumps(informe, ensure_ascii=False, indent=2),
                      encoding="utf-8")
    print(f"\nInforme -> {SALIDA}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
