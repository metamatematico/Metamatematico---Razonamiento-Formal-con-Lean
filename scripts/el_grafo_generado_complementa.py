# -*- coding: utf-8 -*-
"""¿Puede el grafo GENERADO complementar al curado? Se midió por tres vías. No.

QUÉ ES EL GRAFO GENERADO
------------------------
De los 320 nodos, 147 no los escribió nadie: 125 MODULO y 22 AREA, generados
desde la jerarquía de módulos de Mathlib por `scripts/generar_nodos_mathlib.py`.
Son un segundo grafo dentro del mismo `SkillCategory`, y se construyeron para
dar ALCANCE: el curado nombra 158 conceptos y la taxonomía de Mathlib tiene
1 139, de los que se cubren 211.

Sus 447 nombres se dedujeron de la ruta del módulo, y SE COMPROBARON: 346
válidos con `#check`, 95 inexistentes, 6 namespaces, y sólo 4 nodos sin ningún
nombre válido (`data/nombres_generados_verificados.json`). O sea que la
objeción de la primera hora —«deducir no es comprobar»— está contestada: la
mayoría existe.

Hoy esos nodos SÍ están en el grafo y SÍ ayudan al emparejador a reconocer el
tema, pero rankean detrás y su VOCABULARIO está apagado.

LA PREGUNTA HONESTA: ¿ES COMPLEMENTARIO?
----------------------------------------
Sí lo es, y eso no se había medido nunca. Sobre las 319 formas de oro
distintas de ProofNet:

    cubre el curado      41 (12,9 %)
    cubre el generado    27 ( 8,5 %)
    la UNIÓN             60 (18,8 %)
    aporte neto           19 formas

Ponderado por cuántas veces se pide cada nombre (1 396 apariciones): el curado
cubre el 42,9 %, la unión el 47,6 %. **Hay +4,7 puntos ahí**, y no son
cualquier cosa: son `Finset`(15), `Nonempty`(9), `Disjoint`(6), `Prime`(5),
`Equiv`(5) — el vocabulario de trabajo que al curado le falta.

Pero de 445 formas, sólo 19 sirven. Uno de cada veintitrés.

LAS TRES VÍAS, Y LAS TRES PIERDEN
---------------------------------
Camino real, k=2 plazas, ProofNet n=352:

    hoy (sólo curado)                 precisión 21,64 %   cobertura 18,34 %

  (1) inyectar sus nombres sin filtrar
    + generados, sin criba                      16,11 %             18,70 %

  (2) CRIBA POR USO EN MATHLIB — el criterio NO mira el banco: se cuenta
      cuántas veces aparece cada identificador en los enunciados de los
      183 433 lemas. Repara la precisión de forma MONÓTONA, que confirma que
      el diagnóstico era correcto, y aun así no vuelve a la base:
    + generados, uso >=  200                    18,68 %             18,48 %
    + generados, uso >=  500                    19,40 %             18,48 %
    + generados, uso >= 1000                    19,88 %             18,62 %
    + generados, uso >= 2000                    20,77 %             18,62 %

  (3) CUOTA APARTE, para que no compitan por las 2 plazas curadas
    + 1 plaza generada, uso >= 2000             20,18 %             18,84 %
    + 2 plazas generadas, uso >= 1000           17,33 %             19,05 %

El mejor caso de todos compra +0,50 puntos de cobertura por −1,46 de
precisión. No hay configuración que gane.

POR QUÉ, Y ES UNA SOLA RAZÓN
----------------------------
La clave de un nodo generado es SU MÓDULO, y un módulo es un RINCÓN de su
área, no su centro:

    mathlib-analysis-real  ->  Hyperreal.Infinite, Real.ofDigits, ...

mientras `Real` y `Real.sqrt` viven en `Data/Real/Basic`. La criba tira la
basura pero no puede inventar lo que el módulo nunca tuvo, y lo que sobrevive
son los tipos UNIVERSALES —`Set`(20 259 usos), `Fin`(4 886), `Finset`(4 745),
`List`(2 459), `Filter`(2 440)—.

Ahí está el nudo: **un tipo universal es justo lo que ofrece un modelo nulo.**
Añade cobertura porque aparece en todas partes, y hunde la precisión porque no
distingue nada. El valor del grafo curado es ser ESPECÍFICO; la mitad generada
sólo puede ser GENERAL, y las dos cosas no se suman — se estorban.

QUÉ SÍ FUNCIONA, PARA QUE NO SE PIERDA
--------------------------------------
El grafo generado vale por lo que ya hace: dar ALCANCE al emparejador para
reconocer temas que el curado no nombra. Rankeado detrás, abre el cono del
área sin robar plaza. Eso se queda.

El hueco de vocabulario se cierra por el otro lado, y ahí hay una medida
positiva: extender la interpretación CURADA a los conceptos mudos, como se
hizo con siete nodos —`limits-continuity`, `cardinal-arithmetic`,
`differentiation`…— y subió la cobertura de 14,8 % a 18,3 % ganando también
precisión. Quedan 46 conceptos sin nombres y 53 etiquetas marcadas `T`.

No gasta API ni Lean.

    python -m scripts.el_grafo_generado_complementa
"""
import argparse
import collections
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SALIDA = "E:/Metamatematico/data/grafo_generado_complementa.json"
LEMAS = "E:/Metamatematico/data/lemas_mathlib.jsonl"

#: Un identificador de Mathlib dentro de un enunciado. Se exige mayúscula
#: inicial para quedarse con tipos y clases y no con las variables ligadas.
IDENT = re.compile(r"\b([A-Z][A-Za-z0-9_']*(?:\.[A-Za-z_][A-Za-z0-9_']*)*)\b")


def uso_en_mathlib() -> collections.Counter:
    """Cuántas veces se usa cada identificador, sobre los enunciados reales.

    ES EL CRITERIO DE LA CRIBA, Y NO MIRA EL BANCO. Si el filtro saliera del
    oro de ProofNet, la medición estaría ajustada al banco y no diría nada.
    Contar usos dentro de Mathlib es independiente por construcción.
    """
    uso = collections.Counter()
    for linea in io.open(LEMAS, encoding="utf-8"):
        for m in IDENT.finditer(json.loads(linea).get("enunciado") or ""):
            uso[m.group(1)] += 1
    return uso


def main(k_curado: int) -> int:
    from scripts.recuperacion_contra_proofnet import (
        cargar, nombres_de_oro, _norm)
    from nucleo.core import Nucleo
    from nucleo.graph.category import SkillCategory
    from nucleo.graph.interpretacion import (
        nombres_de_trabajo, _nombres_de_cobertura)

    uso = uso_en_mathlib()
    print("uso contado sobre los enunciados de Mathlib: %d identificadores"
          % len(uso))

    filas = cargar()
    n = Nucleo.__new__(Nucleo)
    n._graph = SkillCategory()
    Nucleo._load_foundational_skills(n)
    g = n._graph
    cobertura = _nombres_de_cobertura() or {}

    def exp(txt):
        o = set()
        for p in re.split(r"[,+]", txt or ""):
            p = p.strip()
            if p:
                o.add(_norm(p)); o.add(_norm(p.split(".")[0]))
        return o

    CUR = {s: exp(nombres_de_trabajo(s)) for s in g.skill_ids
           if exp(nombres_de_trabajo(s))}

    def generados(umbral):
        out = {}
        for s in g.skill_ids:
            if s in CUR:
                continue
            nm = cobertura.get(s) or []
            if isinstance(nm, str):
                nm = [nm]
            sel = sorted([x for x in nm if uso.get(x, 0) >= umbral],
                         key=lambda x: -uso.get(x, 0))
            if sel:
                out[s] = exp(", ".join(sel[:2]))
        return out

    def medir(nombre, GEN, k_gen, comparten):
        """`comparten`: los generados compiten por las plazas curadas."""
        tp = fp = fn = 0
        con = casos = 0
        for _id, nl, formal in filas:
            oro = nombres_de_oro(formal)
            if not oro:
                continue
            casos += 1
            m = Nucleo._match_skills_to_query(n, nl, g)
            ofr = set()
            if comparten:
                todo = dict(CUR); todo.update(GEN)
                llenas = 0
                for s in m:
                    if llenas >= k_curado:
                        break
                    if s in todo:
                        llenas += 1; ofr |= todo[s]
            else:
                llenas = 0
                for s in m:
                    if llenas >= k_curado:
                        break
                    if s in CUR:
                        llenas += 1; ofr |= CUR[s]
                lg = 0
                for s in m:
                    if lg >= k_gen:
                        break
                    if s in GEN:
                        lg += 1; ofr |= GEN[s]
            if ofr:
                con += 1
            tp += len(ofr & oro); fp += len(ofr - oro); fn += len(oro - ofr)
        p = 100.0 * tp / max(1, tp + fp)
        c = 100.0 * tp / max(1, tp + fn)
        print("  %-40s prec %5.2f %%  cob %5.2f %%  ofrece %3d/%d"
              % (nombre, p, c, con, casos))
        return {"precision": p, "cobertura": c, "con_algo": con}

    res = {}
    print("\nCAMINO REAL (curados k=%d)\n" % k_curado)
    res["base"] = medir("hoy (sólo curado)", {}, 0, False)
    res["sin_criba"] = medir("(1) generados, sin criba",
                             generados(0), 0, True)
    for u in (200, 500, 1000, 2000):
        res["criba_%d" % u] = medir("(2) generados, uso >= %d" % u,
                                    generados(u), 0, True)
    for u in (1000, 2000):
        for kg in (1, 2):
            res["cuota_%d_%d" % (kg, u)] = medir(
                "(3) %d plaza(s) aparte, uso >= %d" % (kg, u),
                generados(u), kg, False)

    mejor = max((v for kk, v in res.items() if kk != "base"),
                key=lambda v: v["cobertura"] - v["precision"] * 0)
    print("\n  LECTURA: ninguna configuración gana en los dos ejes.")
    print("  La base sigue siendo precisión %.2f %% / cobertura %.2f %%"
          % (res["base"]["precision"], res["base"]["cobertura"]))

    json.dump({"k_curado": k_curado, "resultados": res},
              io.open(SALIDA, "w", encoding="utf-8"), indent=1,
              ensure_ascii=False)
    print("\n-> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    from nucleo.core import PLAZAS_CON_NOMBRES
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("-k", type=int, default=PLAZAS_CON_NOMBRES)
    raise SystemExit(main(ap.parse_args().k))
