# -*- coding: utf-8 -*-
"""¿Ahorra invocaciones de Lean el rankeador QUE CORRE? La pregunta que faltaba.

POR QUE ESTE SCRIPT, HABIENDO YA DOS
------------------------------------
Hay tres cifras circulando y ninguna contesta esto:

    estado_contra_tactica.py   4,64 -> 1,90 intentos, pero con un modelo de
                               22 tacticas entrenado para ese experimento, no
                               con el que corre
    efecto_orden_cascada.py    2,59 -> 1,29, sin modelo nulo, y sobre teoremas
                               de una linea de Mathlib
    modelo_en_la_cascada.py    1,09 (nulo) -> 1,06 (modelo), pero ENTRENA SU
                               PROPIO modelo, distinto del de produccion, y
                               sobre un corpus que es 95,8 % `simp`: el nulo
                               ya acierta a la primera el 94,4 % y no queda
                               casi nada que medir

Lo que falta es lo obvio: coger el `TacticRanker` REAL —el `.pkl` que la
cascada carga en caliente— y medir en cuantas posiciones coloca la tactica que
de verdad cierra, contra el ORDEN FIJO real de `SOLVER_CASCADE`.

LA METRICA ES DINERO Y TIEMPO, NO ACIERTO
-----------------------------------------
Cada posicion es una invocacion de Lean de entre 12 y 30 segundos. Bajar la
posicion media de 3 a 2 no es «un punto de acierto»: es un tercio del recurso
mas caro del sistema.

    posicion media   invocaciones antes de acertar
    1er intento %    cuantas veces la primera es la buena
    en los 3 %       cuantas veces esta entre las tres primeras

EL REPARTO ES HONESTO. Se mide sobre el 20 % de prueba que el modelo NO vio,
con la misma semilla y la misma particion que `train_tactic_ranker.py`.

TRES ORDENES, sobre los mismos casos:

    fijo       `SOLVER_CASCADE` tal cual: rfl, simp, norm_num, ring...
    frecuencia el nulo fuerte: las tacticas por frecuencia en el entrenamiento
    RANKEADOR  el `.pkl` de produccion

El nulo de frecuencia es el que importa. Un rankeador que no bata a «probar
siempre en orden de lo mas comun» no esta mirando el objetivo, esta contando.

No gasta API ni Lean: la posicion se calcula, no se compila.

    python scripts/ranker_en_la_cascada.py
    python scripts/ranker_en_la_cascada.py --modelo data/tactic_ranker_ngramas.pkl.bak
"""
from __future__ import annotations

import argparse
import collections
import json
import pickle
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))
sys.stdout.reconfigure(encoding="utf-8")

ORIGEN = Path(r"E:\MetamatematicoDataSet\LeanWorkbook")
SALIDA = RAIZ / "data" / "ranker_en_la_cascada.json"
SEMILLA = 0          # la misma que train_tactic_ranker.py
PRUEBA = 0.2

_RE_CABEZA = re.compile(r"^([a-zA-Z_][\w']*)")


def _cabeza(t: str):
    m = _RE_CABEZA.match((t or "").strip())
    return m.group(1) if m else None


def cargar(min_por_clase: int = 40):
    """(state_before, tactica que CIERRA) del corpus de LeanWorkbook."""
    from datasets import load_from_disk
    ds = load_from_disk(str(ORIGEN))
    ds = ds[list(ds.keys())[0]] if hasattr(ds, "keys") else ds
    X, y = [], []
    for fila in ds:
        estado = (fila.get("state_before") or "").strip()
        after = (fila.get("state_after") or "").strip()
        cab = _cabeza(fila.get("tactic") or "")
        # Solo las que CIERRAN el objetivo: es la pregunta de la cascada.
        if estado and cab and after == "no goals":
            X.append(estado)
            y.append(cab)
    cuenta = collections.Counter(y)
    keep = {t for t, n in cuenta.items() if n >= min_por_clase}
    XY = [(a, b) for a, b in zip(X, y) if b in keep]
    return [a for a, _ in XY], [b for _, b in XY]


def posicion(orden, verdadera) -> int:
    """En que puesto queda la tactica que cierra. 1 = primera.

    Si no esta en la lista se cuenta como len+1: la cascada la agotaria entera
    sin acertar. Contarlo como «no aplica» premiaria al orden que la omite.
    """
    for i, nombre in enumerate(orden, start=1):
        if nombre == verdadera:
            return i
    return len(orden) + 1


def resume(posiciones, tope3=3):
    n = len(posiciones)
    return (sum(posiciones) / n,
            100.0 * sum(1 for p in posiciones if p == 1) / n,
            100.0 * sum(1 for p in posiciones if p <= tope3) / n)


def main(ruta_modelo: str | None) -> int:
    from sklearn.model_selection import train_test_split
    from nucleo.lean.solver_cascade import SOLVER_CASCADE, TacticRanker

    print("Cargando LeanWorkbook...")
    X, y = cargar()
    Xtr, Xte, ytr, yte = train_test_split(
        X, y, test_size=PRUEBA, random_state=SEMILLA, stratify=y)
    print("casos que cierran: %d  ·  prueba: %d  ·  tacticas: %d\n"
          % (len(X), len(Xte), len(set(y))))

    nombres_cascada = [s for s, _ in SOLVER_CASCADE]
    print("orden FIJO de la cascada: %s" % ", ".join(nombres_cascada))

    # LOS TRES ORDENES JUEGAN CON LAS MISMAS CARTAS.
    #
    # La primera version de esta medida daba al nulo de frecuencia el corpus
    # ENTERO —27 tacticas, incluidas `refine'`, `exact` y `rw`, que la cascada
    # NO tiene— mientras el rankeador solo podia reordenar las 12 de
    # `SOLVER_CASCADE`. Con ese reparto el nulo ganaba 4,84 contra 6,42 y el
    # veredicto salia «el rankeador no mira el objetivo», que era falso: el
    # nulo estaba proponiendo tacticas que el sistema no puede ejecutar.
    #
    # Un modelo nulo tiene que ser fuerte, no tramposo. Aqui los tres ordenan
    # exactamente el mismo repertorio, y se evalua solo donde ese repertorio
    # PUEDE acertar: si la tactica que cierra no esta en la cascada, ningun
    # orden la encuentra y el caso no distingue nada.
    en_cascada = set(nombres_cascada)
    pares = [(e, t) for e, t in zip(Xte, yte) if t in en_cascada]
    fuera = len(Xte) - len(pares)
    print("casos cuya tactica SI esta en la cascada: %d de %d  (%d fuera)"
          % (len(pares), len(Xte), fuera))

    frec_entren = collections.Counter(t for t in ytr if t in en_cascada)
    orden_frec = ([t for t, _ in frec_entren.most_common()]
                  + [t for t in nombres_cascada if t not in frec_entren])
    print("orden por FRECUENCIA:     %s\n" % ", ".join(orden_frec))

    Xte = [e for e, _ in pares]
    yte = [t for _, t in pares]

    ranker = TacticRanker(Path(ruta_modelo) if ruta_modelo else None)
    if not ranker.disponible:
        print("No hay modelo cargado. Entrena con train_tactic_ranker.py")
        return 1

    pos_fijo, pos_frec, pos_rank = [], [], []
    for estado, verdadera in zip(Xte, yte):
        pos_fijo.append(posicion(nombres_cascada, verdadera))
        pos_frec.append(posicion(orden_frec, verdadera))
        ordenado = [s for s, _ in ranker.rank(estado, SOLVER_CASCADE)]
        pos_rank.append(posicion(ordenado, verdadera))

    filas = [("fijo (SOLVER_CASCADE)", resume(pos_fijo)),
             ("NULO: por frecuencia", resume(pos_frec)),
             ("RANKEADOR", resume(pos_rank))]

    print("=== POSICION DE LA TACTICA QUE CIERRA (n=%d) ===" % len(Xte))
    print("    cada posicion es una invocacion de Lean de 12-30 s\n")
    print("   %-24s %8s %12s %11s" % ("", "media", "1er intento", "en los 3"))
    for nombre, (m, p1, p3) in filas:
        print("   %-24s %8.2f %10.1f %% %9.1f %%" % (nombre, m, p1, p3))

    m_fijo, m_frec, m_rank = filas[0][1][0], filas[1][1][0], filas[2][1][0]
    print("\n   contra el orden fijo      : %.2f -> %.2f  (%.1fx menos)"
          % (m_fijo, m_rank, m_fijo / m_rank))
    print("   contra el nulo de frecuencia: %.2f -> %.2f  (%+.2f)"
          % (m_frec, m_rank, m_rank - m_frec))
    if m_rank < m_frec:
        veredicto = ("el rankeador bate al nulo de frecuencia: mira el "
                     "objetivo, no solo cuenta")
    else:
        veredicto = ("el rankeador NO bate al nulo de frecuencia: lo que "
                     "parecia mirar el objetivo era contar")
    print("   VEREDICTO: %s" % veredicto)

    json.dump({"n_prueba": len(Xte), "tacticas": len(set(y)),
               "modelo": ruta_modelo or "produccion",
               "resultados": {n: {"posicion_media": m, "primer_intento": p1,
                                  "en_los_3": p3} for n, (m, p1, p3) in filas},
               "veredicto": veredicto},
              open(SALIDA, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("\n-> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--modelo", default=None,
                    help="ruta a un .pkl alternativo (para comparar con el "
                         "modelo anterior)")
    raise SystemExit(main(ap.parse_args().modelo))
