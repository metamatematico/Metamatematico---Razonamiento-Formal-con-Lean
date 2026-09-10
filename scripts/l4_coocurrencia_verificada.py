# -*- coding: utf-8 -*-
"""L4: qué conceptos trabajan juntos EN PRUEBAS QUE LEAN ACEPTÓ.

EL PROBLEMA QUE RESUELVE
------------------------
`CoRegulatorNetwork.record_activation` existe para alimentar el paisaje de uso
de CR_org: cuando un grupo de competencias se repite, CR_org lo liga en un
colímite (Def. 4.1). Es la maquinaria de emergencia del marco de Ehresmann, y
está implementada y verificada en Lean.

Pero hoy se alimenta de esto, en `core.py::_find_relevant_context`:

    _red.record_activation(matched[:6])

donde `matched` son las competencias que el EMPAREJADOR LÉXICO adivinó a
partir de las palabras de la consulta. O sea que el grafo lleva la cuenta de
sus propias conjeturas: un lazo cerrado sin verdad dentro. Los colímites que
salen de ahí agrupan patrones de palabras clave, no matemática que funcionó.

LO QUE HACE ESTE GUION
----------------------
Sustituye la fuente. Una prueba que Lean aceptó cita premisas; el grafo tiene
188 nombres verificados repartidos en 113 conceptos; luego una prueba
verificada induce un conjunto de conceptos, y dos conceptos coocurren si
aparecen en la misma prueba.

    prueba verificada -> premisas citadas -> conceptos -> coocurrencia

El material son los ~40 000 teoremas de Mathlib con sus premisas, extraídos por
`banco_premisas_mathlib.recolectar`. No hay que esperar a acumular uso: la
evidencia ya existe y es gratis.

EL EMPAREJADO ES EXACTO, Y ESO NO ES UN DETALLE
-----------------------------------------------
La primera versión expandía cada nombre a su raíz de namespace, como hace el
emparejador léxico. Con eso los cuatro pares más frecuentes salían así:

    363  cardinal-arithmetic + elementary-number-theory
    362  cardinal-arithmetic + partitions
    362  elementary-number-theory + partitions
    341  bilinear-forms + linear-algebra

y los cuatro son ARTEFACTOS: `Nat.card`, `Nat` y `Nat.Partition` comparten la
raíz `Nat`, y `LinearMap.BilinForm` comparte `LinearMap` con `linear-algebra`.
Cualquier prueba que citara algo de `Nat.` activaba tres conceptos a la vez.

Coocurrir por compartir prefijo no es coocurrir por hacer matemática junta. Con
emparejado exacto una prueba tiene que citar EL nombre que el concepto declara.

QUÉ MUESTRA
-----------
Los pares que sobreviven, ordenados, y la comparación con el modelo nulo: si
dos conceptos coocurren más de lo que su frecuencia individual predice. Sin ese
contraste, «aparecen juntos 178 veces» no dice nada — puede ser que los dos
aparezcan mucho.

No gasta API ni Lean.

    python -m scripts.l4_coocurrencia_verificada
"""
from __future__ import annotations

import argparse
import collections
import io
import json
import math
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SALIDA = "E:/Metamatematico/data/l4_coocurrencia_verificada.json"
LEMAS = "E:/Metamatematico/data/lemas_mathlib.jsonl"


def indice_de_nombres(g):
    """nombre EXACTO de Mathlib -> conceptos que lo declaran.

    Sin expansión a la raíz del namespace: ver la nota de la cabecera.
    """
    from nucleo.graph.interpretacion import nombres_de_trabajo
    por_nombre = collections.defaultdict(set)
    for s in g.skill_ids:
        for p in re.split(r"[,+]", nombres_de_trabajo(s) or ""):
            p = p.strip().split()[0] if p.strip() else ""
            if p:
                por_nombre[p].add(s)
    return por_nombre


def main(tope: int, minimo: int) -> int:
    import logging
    import warnings
    warnings.filterwarnings("ignore")
    logging.disable(logging.WARNING)

    from nucleo.core import Nucleo
    from nucleo.graph.category import SkillCategory
    from scripts.banco_premisas_mathlib import recolectar

    n = Nucleo.__new__(Nucleo)
    n._graph = SkillCategory()
    Nucleo._load_foundational_skills(n)
    g = n._graph

    por_nombre = indice_de_nombres(g)
    conceptos = {s for v in por_nombre.values() for s in v}
    print("nombres exactos indexados: %d" % len(por_nombre))
    print("conceptos que aportan nombres: %d\n" % len(conceptos))

    lemas = [json.loads(l) for l in io.open(LEMAS, encoding="utf-8")]
    cortos = {d["corto"] for d in lemas}
    largos = {d["nombre"] for d in lemas}
    print("recolectando teoremas de Mathlib con sus premisas...")
    casos = recolectar(cortos, largos, tope)
    print("teoremas con premisas: %d" % len(casos))

    # EL MATERIAL ES EL ENUNCIADO, NO LAS PREMISAS. Y ESO SE MIDIO.
    #
    # La primera version cruzaba el vocabulario del grafo con las PREMISAS que
    # cita cada prueba, y dio CERO coincidencias exactas sobre 40 025 teoremas.
    # No era un fallo del codigo: es un desajuste de categoria.
    #
    #     premisas de Mathlib   infinite_of_charZero, cardinalMk_lift_le_mul
    #     vocabulario del grafo Group, Subgroup, MonoidHom, Real
    #
    # Son conjuntos disjuntos por construccion: el grafo nombra OBJETOS y las
    # pruebas citan LEMAS SOBRE esos objetos. Los tipos viven en el ENUNCIADO:
    #
    #     (R A : Type*) [CommRing R] [Ring A] [Algebra R A] : ...
    #
    # Asi que dos conceptos coocurren si un teorema VERIFICADO habla de los dos
    # a la vez, que ademas es lo que uno quiere decir con «trabajan juntos».
    tok = re.compile(r"[A-Za-z_][A-Za-z0-9_.']*")
    solos = collections.Counter()
    pares = collections.Counter()
    con_dos = 0
    for c in casos:
        cs = set()
        for p in set(tok.findall(c.get("enunciado") or "")):
            cs |= por_nombre.get(p, set())
        if not cs:
            continue
        for s in cs:
            solos[s] += 1
        if len(cs) >= 2:
            con_dos += 1
            ls = sorted(cs)
            for i in range(len(ls)):
                for j in range(i + 1, len(ls)):
                    pares[(ls[i], ls[j])] += 1

    # `total` se cuenta sobre EL ENUNCIADO, igual que los pares. Al cambiar la
    # fuente de premisas a enunciado esta linea se quedo mirando las premisas
    # y daba total=1, con lo que todos los «esperados» salian astronomicos y
    # todos los excesos negativos. Un exceso negativo en TODOS los pares es la
    # firma de un denominador mal puesto, no de una anticorrelacion universal.
    total = max(1, sum(1 for c in casos
                       if any(por_nombre.get(p)
                              for p in set(tok.findall(c.get("enunciado") or "")))))
    print("pruebas que tocan al menos un concepto: %d" % total)
    print("pruebas que tocan dos o mas:            %d  (%.1f %%)"
          % (con_dos, 100.0 * con_dos / max(1, len(casos))))
    print("pares distintos: %d\n" % len(pares))

    # ── EL MODELO NULO: coocurrir por ser frecuentes ────────────────────
    #
    # Si A sale en 500 pruebas y B en 400 de 1 000, se esperan 200 juntas sin
    # que haya ninguna relación. Lo que interesa es el EXCESO sobre eso. Se
    # usa el logaritmo de la razón observado/esperado, que es simétrico y no
    # premia a los pares grandes por serlo.
    filas = []
    for (a, b), obs in pares.items():
        if obs < minimo:
            continue
        esperado = solos[a] * solos[b] / total
        if esperado <= 0:
            continue
        filas.append({"a": a, "b": b, "juntas": obs,
                      "esperadas": round(esperado, 1),
                      "exceso": round(math.log2(obs / esperado), 2)})
    filas.sort(key=lambda f: -f["exceso"])

    print("=== PARES QUE COOCURREN MAS DE LO ESPERADO ===")
    print("   (juntas >= %d; 'exceso' es log2 de observado/esperado)\n" % minimo)
    print("   %6s %9s %7s  %s" % ("juntas", "esperadas", "exceso", "conceptos"))
    for f in filas[:25]:
        print("   %6d %9.1f %7.2f  %s + %s"
              % (f["juntas"], f["esperadas"], f["exceso"], f["a"], f["b"]))

    print("\n=== LOS MAS FRECUENTES EN CRUDO (para contraste) ===")
    for (a, b), k in pares.most_common(8):
        esp = solos[a] * solos[b] / total
        print("   %6d  esperadas %7.1f  exceso %+5.2f   %s + %s"
              % (k, esp, math.log2(k / esp) if esp > 0 else 0, a, b))

    json.dump({"teoremas": len(casos), "con_dos_o_mas": con_dos,
               "pares_distintos": len(pares), "minimo": minimo,
               "pares": filas[:200]},
              io.open(SALIDA, "w", encoding="utf-8"), indent=1,
              ensure_ascii=False)
    print("\n-> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--tope", type=int, default=40000)
    ap.add_argument("--minimo", type=int, default=5,
                    help="coocurrencias mínimas para entrar (def. 5)")
    a = ap.parse_args()
    raise SystemExit(main(a.tope, a.minimo))
