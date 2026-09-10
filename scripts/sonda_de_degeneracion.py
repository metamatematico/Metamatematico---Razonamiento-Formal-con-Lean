# -*- coding: utf-8 -*-
"""¿Discrimina algo la red neuronal? Se mide, no se opina.

QUE PASO
--------
El GNN+PPO se entreno hasta el 100 % de precision sobre este objetivo:

    todo problema matematico  ->  accion ASSIST

Ese objetivo SE SATISFACE CON UNA CONSTANTE. Un modelo que responda siempre
`ASSIST` acierta el 100 %, y eso fue lo que la red aprendio. El «100 % / 100 %
/ 100 %» del informe de entrenamiento no era un logro: era un modelo nulo con
otro nombre.

El runtime ya lo detecta —`CoRegulatorNetwork._neural_agent_is_degenerate`—
y la descarta, pero esa comprobacion vive dentro del sistema y no deja cifra.
Este guion la saca fuera y la escribe, para que el decisor pueda leerla como
lee cualquier otra evidencia.

LA SONDA
--------
Cuatro entradas deliberadamente heterogeneas: un teorema, un saludo, un hecho
no matematico y un fragmento de Lean. Una politica util no puede dar la misma
accion a las cuatro.

    acciones distintas = 1   ->  constante: no discrimina
    acciones distintas > 1   ->  al menos separa algo

EL MODELO NULO es la politica constante, que por definicion da 1. Comparar
contra el es lo unico que distingue «aprendio» de «se quedo quieta», y es
justo la comparacion que faltaba cuando se publico el 100 %.

No gasta API ni Lean.

    python -m scripts.sonda_de_degeneracion
"""
from __future__ import annotations

import argparse
import io
import json
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SALIDA = "E:/Metamatematico/data/sonda_de_degeneracion.json"

#: Deliberadamente heterogenea. Si las cuatro dan lo mismo, la red no mira la
#: entrada.
SONDA = (
    ("teorema",      "Demuestra que la raiz de 2 es irracional"),
    ("saludo",       "Hola, como estas"),
    ("hecho no mat", "Cual es la capital de Francia"),
    ("codigo Lean",  "```lean\ntheorem t : 1 = 1 := rfl\n```"),
)


def main() -> int:
    import logging
    import warnings
    warnings.filterwarnings("ignore")
    logging.disable(logging.WARNING)

    from nucleo.types import State

    # HAY QUE CARGAR LOS PESOS, Y HAY QUE COMPROBAR QUE SE CARGARON.
    #
    # `NucleoAgent(graph, use_neural=True)` NO carga nada: inicializa la red al
    # azar. Los pesos entrenados entran por `NucleoAgent.load()`.
    #
    # La primera version de este guion usaba el constructor y la sonda dio
    # TRES acciones distintas — «discrimina»— cuando lo que estaba midiendo era
    # ruido de una red sin entrenar. Dos agentes recien construidos tenian
    # pesos distintos entre si, que es la prueba de que no venian de ningun
    # fichero. Medir una red sin cargar es medir el generador de aleatorios.
    from nucleo.rutas import dato
    from nucleo.graph.category import SkillCategory
    from nucleo.core import Nucleo

    n = Nucleo.__new__(Nucleo)
    n._graph = SkillCategory()
    Nucleo._load_foundational_skills(n)

    agente = None
    ruta = str(dato("neural_agent.json"))
    try:
        from nucleo.rl.agent import NucleoAgent
        agente = NucleoAgent.load(ruta, n._graph)
    except Exception as exc:                                   # noqa: BLE001
        print("no se pudieron cargar los pesos (%s: %s)"
              % (type(exc).__name__, exc))
        return 1

    # Comprobacion de que los pesos son los del fichero y no ruido.
    try:
        import torch
        estado = torch.load(ruta + ".pt", map_location="cpu", weights_only=True)
        propios = dict(agente._network.named_parameters())
        clave = next(k for k in estado if k in propios)
        cargados = torch.allclose(estado[clave], propios[clave].detach())
        print("pesos del fichero cargados: %s  (%s)\n"
              % (cargados, clave))
        if not cargados:
            print("   LOS PESOS NO COINCIDEN. La sonda mediria ruido; se aborta.")
            return 1
    except Exception as exc:                                   # noqa: BLE001
        print("no se pudo verificar la carga (%s): se aborta por prudencia"
              % type(exc).__name__)
        return 1

    acciones = []
    print("SONDA (%d entradas heterogeneas)\n" % len(SONDA))
    for etiqueta, texto in SONDA:
        accion = "(sin red)"
        if agente is not None:
            try:
                accion = str(agente._select_neural(
                    State(lean_goal=texto)).action_type)
            except Exception as exc:                           # noqa: BLE001
                accion = "ERROR:%s" % type(exc).__name__
        acciones.append(accion)
        print("   %-14s -> %s" % (etiqueta, accion))

    distintas = len(set(acciones))
    nulo = 1                       # la politica constante da exactamente 1
    print("\n   acciones distintas : %d" % distintas)
    print("   modelo nulo        : %d  (la politica constante)" % nulo)
    degenerada = distintas <= nulo
    print("   VEREDICTO: %s"
          % ("DEGENERADA — no discrimina, es una constante" if degenerada
             else "discrimina: separa al menos dos casos"))

    json.dump({"entradas": len(SONDA), "acciones_distintas": distintas,
               "nulo_constante": nulo, "degenerada": bool(degenerada),
               "acciones": dict(zip([e for e, _ in SONDA], acciones))},
              io.open(SALIDA, "w", encoding="utf-8"), indent=1,
              ensure_ascii=False)
    print("\n-> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args()
    raise SystemExit(main())
