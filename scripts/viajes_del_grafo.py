# -*- coding: utf-8 -*-
"""Los viajes que EXISTEN por la fibración, calculados y dejados por escrito.

QUE HACE, Y POR QUE NO LO CALCULA LA INTERFAZ
---------------------------------------------
`fibracion_del_grafo.py` contesta «¿es π una fibración?» — no lo es, y no
puede serlo. Este script contesta la pregunta útil: «¿QUÉ traslados hay?».

Recorre todos los pares (concepto, área que la base pone por debajo) y guarda
los que admiten levantamiento cartesiano. Son 102 de 1436. Cada uno es una
respuesta concreta a «¿qué parte de aquella área sostiene a esto?»:

    probability-theory   [Probability]  <- Analysis   =  real-analysis
    descriptive-set-th.  [SetTheory]    <- Topology   =  point-set-topology
    derived-category     [Algebra]      <- Topology   =  algebraic-topology

Calcularlos son ~1400 levantamientos sobre el grafo entero, que no se pueden
hacer dentro de una página de Streamlit en cada recarga. Se dejan en
`data/viajes.json` y la página los lee, igual que lee el resto de mediciones.

LA BASE ES LA DIRECTA. Ver la cabecera de `nucleo/graph/viaje.py`: la clausura
transitiva convierte 69 flechas en 462 relaciones, y por las 393 que sobran no
se puede viajar porque ningún morfismo las induce.

SE GUARDA LA COBERTURA JUNTO A LOS VIAJES, no en otro fichero. Una lista de
102 traslados correctos da la impresión de un sistema que sabe viajar; la
cobertura dice que son el 7,1 % de lo que la base promete. Separarlos sería
invitar a publicar lo primero sin lo segundo.

No gasta API.

    python -m scripts.viajes_del_grafo
"""
from __future__ import annotations

import asyncio
import io
import json
import os
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RAIZ = pathlib.Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

SALIDA = RAIZ / "data" / "viajes.json"


def main() -> int:
    import logging
    import warnings
    warnings.filterwarnings("ignore")
    logging.disable(logging.WARNING)

    from nucleo.config import NucleoConfig
    from nucleo.core import Nucleo
    from nucleo.graph.functor import OBJETO_BASE
    from nucleo.graph.huella import huella
    from nucleo.graph.viaje import base_directa, cobertura, viajar
    from nucleo.graph.functor import construir_funtor

    yaml = RAIZ / "nucleo_config.yaml"
    cfg = NucleoConfig.from_yaml(str(yaml)) if yaml.exists() else NucleoConfig()
    n = Nucleo(cfg)
    # el constructor no monta el grafo: lo monta initialize(), que es async
    asyncio.run(n.initialize())
    g = n._graph

    pi = base_directa(construir_funtor(g))
    print("grafo: %d skills, %d morfismos" % (len(list(g.skills)),
                                              len(list(g.morphisms))))
    print("base directa: %d areas, %d flechas"
          % (len(pi.codominio.objetos), len(pi.codominio.morfismos)))

    viajes = []
    for s in g.skills:
        a = pi.en_objetos.get(s.id)
        if a is None:
            continue
        for b in sorted(pi.codominio.objetos):
            if b == a or b == OBJETO_BASE:
                continue
            if a not in pi.codominio.alcanzables_desde(b):
                continue
            v = viajar(g, s.id, b, pi)
            if v:
                viajes.append({"origen": v.origen, "area_origen": v.area_origen,
                               "destino": v.destino, "soporte": v.soporte,
                               "candidatos": v.candidatos})

    c = cobertura(g, pi)
    print("\nviajes que existen: %d de %d pares  (%.1f %%)"
          % (len(viajes), c.pares, 100 * c.tasa))
    print("\npor area destino:")
    for b, (ok, tot) in sorted(c.por_area.items(), key=lambda t: -t[1][0]):
        if tot:
            print("   %-24s %4d/%-5d %5.1f %%" % (b, ok, tot, 100.0 * ok / tot))

    print("\nunos cuantos:")
    for v in viajes[:10]:
        print("   %-26s [%-14s] <- %-20s = %s"
              % (v["origen"], v["area_origen"], v["destino"], v["soporte"]))

    datos = {
        "grafo": huella(g),
        "pares": c.pares,
        "con_viaje": c.con_viaje,
        "tasa": round(c.tasa, 4),
        # LA VENTAJA SOBRE EL AZAR VA AQUI Y NO EN UN COMENTARIO. Medida en
        # `fibracion_del_grafo.py`: 7,1 % real contra 6,8 % del nulo. Es 1,1x,
        # o sea nada. Quien lea este fichero tiene que tropezarse con eso
        # antes de citar el 7,1 %.
        "nulo_base_directa": 0.068,
        "ventaja_sobre_el_nulo": 1.1,
        "por_area": {k: {"con_viaje": v[0], "pares": v[1]}
                     for k, v in c.por_area.items()},
        "viajes": sorted(viajes, key=lambda v: (v["area_origen"], v["origen"])),
    }
    io.open(SALIDA, "w", encoding="utf-8").write(
        json.dumps(datos, ensure_ascii=False, indent=2))
    print("\nescrito -> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
