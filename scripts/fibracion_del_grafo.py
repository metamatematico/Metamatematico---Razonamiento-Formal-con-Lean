# -*- coding: utf-8 -*-
"""¿Es π : Skills → Áreas una fibración? Y si no, ¿qué parte de la base sí?

QUE SE PREGUNTA
---------------
`verificar_funtor.py` ya comprueba que π es funtor. Eso dice que está bien
definida, no que la base sirva: un funtor constante también es funtor.

La condición que sí lo dice es la de fibración, demostrada en
`MetamathProver/CategoryFoundations/Fibracion.lean`. Si vale `b' ≼ b` en la
base, todo objeto `e` sobre `b` tiene que tener un levantamiento CARTESIANO
sobre `b'`: el mayor de los skills de `b'` que están por debajo de `e`.

Lo que se gana si vale, y sólo si vale (Lean, 0 sorry, sin axiomas):
`reindexado_monotono` da una aplicación monótona fibra(b) → fibra(b'), que es
justo la manera de trasladar una pregunta de un área a otra; y
`reindexado_compuesto` dice que encadenarlas no depende del camino.

LAS TRES COSAS QUE SE MIDEN
---------------------------
  1. LA TASA, y su DESCOMPOSICIÓN por cuál de las tres condiciones falla:
     no hay candidato / no hay mayor / el mayor vive en otra fibra. Sin
     descomponer, un 0 % no dice qué habría que arreglar.

  2. EL MODELO NULO: se baraja π conservando el tamaño de cada fibra y se
     rehace la base. Si una asignación aleatoria de áreas levanta tanto como
     la real, la asignación real no está aportando estructura. Comparar la
     fibración con nada no sería una medición.

  3. LA PARTE QUE SÍ. De las flechas de la base, cuáles admiten levantamiento
     para TODOS los objetos de su fibra. Esa subbase sí es una fibración —por
     construcción— y es la que se puede usar. Convierte el resultado negativo
     en algo utilizable en vez de en un lamento.

LO QUE ESTA MEDIDA NO DICE. Nada sobre si las áreas están bien elegidas. Dice
si la relación ENTRE áreas que el grafo induce está sostenida por los skills.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import random
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.stdout.reconfigure(encoding="utf-8")

from nucleo.graph.category import SkillCategory
from nucleo.graph.fibracion import levantar, verificar_fibracion
from nucleo.graph.functor import OBJETO_BASE, Funtor, construir_funtor

SALIDA = RAIZ / "data" / "fibracion_del_grafo.json"


def _grafo():
    from scripts.train_gnn_ppo import build_skill_graph
    return build_skill_graph()


def _clasifica(motivo: str) -> str:
    if motivo.startswith("no hay ningun"):
        return "sin soporte del area de abajo"
    if motivo.startswith("hay "):
        return "hay soporte pero ninguno domina"
    return "el mayor esta en otra fibra"


def _barajar(pi: Funtor, semilla: int) -> Funtor:
    """π con las áreas repartidas al azar, conservando el tamaño de las fibras.

    Conservar los tamaños es lo que hace que la comparación sea justa: una
    fibra grande tiene más candidatos, y sin fijar los tamaños el nulo
    mediría eso en vez de la asignación.
    """
    rng = random.Random(semilla)
    ids = list(pi.en_objetos)
    areas = list(pi.en_objetos.values())
    rng.shuffle(areas)
    return dict(zip(ids, areas))


def main(a) -> int:
    graph = _grafo()
    tipos = SkillCategory.ORDER_MORPHISMS
    pi = construir_funtor(graph)

    print("grafo: %d skills, %d morfismos" % (len(graph.skills),
                                              len(graph.morphisms)))
    print("base:  %d areas, %d flechas directas"
          % (len(pi.codominio.objetos), len(pi.codominio.morfismos)))
    print()

    # ── 1 · la tasa y su descomposición ─────────────────────────────────────
    inf = verificar_fibracion(pi, graph, tipos=tipos)
    print("1 · LA CONDICION DE FIBRACION")
    print("   pares (objeto, area estrictamente por debajo)   %6d" % inf.pares)
    print("   con levantamiento cartesiano                    %6d  (%.1f %%)"
          % (inf.levantados, 100 * inf.tasa))
    print("   ¿es fibracion?                                  %s"
          % inf.es_fibracion)

    porque: collections.Counter = collections.Counter()
    for _e, _b, motivo, _n in inf.fallos:
        porque[_clasifica(motivo)] += 1
    # los fallos guardados están topados; se recuentan todos
    porque.clear()
    for s in graph.skills:
        ar = pi.en_objetos.get(s.id)
        if ar is None:
            continue
        for b in pi.codominio.objetos:
            if b == ar or b == OBJETO_BASE:
                continue
            if ar not in pi.codominio.alcanzables_desde(b):
                continue
            r = levantar(pi, graph, s.id, b, tipos)
            if not r:
                porque[_clasifica(r.motivo)] += 1
    print()
    print("   por que falla:")
    for k, v in porque.most_common():
        print("      %-30s %5d  (%.1f %%)" % (k, v, 100 * v / max(1, inf.pares)))

    # ── 1bis · de donde sale ese numero ───────────────────────────
    # Un 0,3 % pide explicacion antes que interpretacion. La base se construye
    # como la IMAGEN de las flechas del grafo, y luego se toma su clausura
    # transitiva; si hay pocas flechas que crucen de area, unas pocas generan
    # muchisimas relaciones entre areas que ningun objeto sostiene.
    dentro = cruzan = tocan_base = 0
    for m in graph.morphisms:
        if m.morphism_type not in tipos:
            continue
        x, y = pi.en_objetos.get(m.source_id), pi.en_objetos.get(m.target_id)
        if x == OBJETO_BASE or y == OBJETO_BASE:
            tocan_base += 1
        elif x == y:
            dentro += 1
        else:
            cruzan += 1
    tot = dentro + cruzan + tocan_base
    print()
    print("1bis · DE DONDE SALE ESE NUMERO")
    print("   morfismos de orden          %4d" % tot)
    print("      dentro de un area        %4d  %.1f %%" % (dentro, 100 * dentro / max(1, tot)))
    print("      CRUZAN de area           %4d  %.1f %%   <- los unicos que"
          " sostienen la base" % (cruzan, 100 * cruzan / max(1, tot)))
    print("      tocan el fundacional     %4d  %.1f %%" % (tocan_base, 100 * tocan_base / max(1, tot)))
    sin_soporte = porque.get("sin soporte del area de abajo", 0)
    print("   pares sin NI UN skill del area de abajo por debajo:"
          " %d de %d (%.1f %%)"
          % (sin_soporte, inf.pares, 100 * sin_soporte / max(1, inf.pares)))
    print("   -> %d flechas que cruzan generan %d relaciones entre areas por"
          % (cruzan, len(buenas_pares := [
              (x, y) for x in pi.codominio.objetos
              for y in pi.codominio.objetos
              if x != y and y in pi.codominio.alcanzables_desde(x)])))
    print("      clausura transitiva. La base AFIRMA de mas.")

    # ── 2 · el modelo nulo ──────────────────────────────────────────────────
    print()
    print("2 · MODELO NULO — las mismas fibras, las areas al azar")
    tasas = []
    for i in range(a.repeticiones):
        mezcla = _barajar(pi, a.semilla + i)
        # se reconstruye el codominio a partir de la π barajada
        from nucleo.graph.functor import CategoriaAgentes, MorfismoAgente
        cod = CategoriaAgentes(objetos=set(mezcla.values()))
        agr: dict = collections.defaultdict(list)
        for m in graph.morphisms:
            if m.morphism_type not in tipos:
                continue
            x, y = mezcla.get(m.source_id), mezcla.get(m.target_id)
            if x is None or y is None or x == y:
                continue
            agr[(x, y)].append(m)
        for (x, y), ms in agr.items():
            cod.morfismos[(x, y)] = MorfismoAgente(
                source_id=x, target_id=y, multiplicidad=len(ms),
                tipos=frozenset(str(m.morphism_type).split(".")[-1] for m in ms))
        pi_n = Funtor(en_objetos=mezcla, codominio=cod)
        inf_n = verificar_fibracion(pi_n, graph, tipos=tipos)
        tasas.append(inf_n.tasa)
        print("   baraja %d: %6d pares, %.1f %% levantados"
              % (i + 1, inf_n.pares, 100 * inf_n.tasa))
    media = sum(tasas) / max(1, len(tasas))
    print("   media del nulo: %.1f %%   ·   real: %.1f %%   ·   ventaja %+.1f"
          % (100 * media, 100 * inf.tasa, 100 * (inf.tasa - media)))

    # ── 3 · la subbase que sí es fibración ──────────────────────────────────
    print()
    print("3 · LA PARTE DE LA BASE QUE SI SE LEVANTA")
    print("   (una flecha b'->b sobrevive si TODOS los objetos de la fibra de")
    print("    b se levantan a b'; esa subbase es fibracion por construccion)")
    buenas, malas = [], []
    for b in sorted(pi.codominio.objetos):
        if b == OBJETO_BASE:
            continue
        for c in sorted(pi.codominio.objetos):
            if c == b or c == OBJETO_BASE:
                continue
            if c not in pi.codominio.alcanzables_desde(b):
                continue          # b ≼ c hace falta para que el par exista
            fibra = [s.id for s in graph.skills
                     if pi.en_objetos.get(s.id) == c]
            if not fibra:
                continue
            ok = sum(1 for e in fibra if levantar(pi, graph, e, b, tipos))
            (buenas if ok == len(fibra) else malas).append(
                (b, c, ok, len(fibra)))
    print("   flechas de la base (en clausura) con TODA su fibra levantada:"
          " %d de %d" % (len(buenas), len(buenas) + len(malas)))
    for b, c, ok, n in buenas[:10]:
        print("      %s -> %s   (%d/%d)" % (b, c, ok, n))
    print("   las mejores que NO llegan:")
    for b, c, ok, n in sorted(malas, key=lambda x: -x[2] / x[3])[:8]:
        print("      %-14s -> %-14s %3d/%-3d = %.0f %%" % (b, c, ok, n,
                                                           100 * ok / n))

    SALIDA.write_text(json.dumps({
        "skills": len(graph.skills), "morfismos": len(graph.morphisms),
        "areas": len(pi.codominio.objetos),
        "flechas_base": len(pi.codominio.morfismos),
        "pares": inf.pares, "levantados": inf.levantados,
        "tasa": round(inf.tasa, 4), "es_fibracion": inf.es_fibracion,
        "por_que_falla": dict(porque),
        "morfismos_de_orden": tot,
        "morfismos_dentro_de_area": dentro,
        "morfismos_que_cruzan": cruzan,
        "morfismos_al_fundacional": tocan_base,
        "relaciones_entre_areas_por_clausura": len(buenas_pares),
        "nulo_media": round(media, 4), "nulo_tasas": [round(t, 4) for t in tasas],
        "subbase_fibracion": [list(x) for x in buenas],
        "subbase_fallida": [list(x) for x in malas],
        "fibras": inf.fibras,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print()
    print("escrito -> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--repeticiones", type=int, default=5)
    ap.add_argument("--semilla", type=int, default=20260904)
    raise SystemExit(main(ap.parse_args()))
