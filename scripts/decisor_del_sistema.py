# -*- coding: utf-8 -*-
"""La tabla del decisor: qué corre, qué no, y con qué número detrás.

Imprime, para cada capacidad del sistema, el veredicto recalculado desde su
fichero de medición. No lleva ningún número escrito a mano: si una medición
cambia, esta tabla cambia con ella.

El resumen de abajo compara el decisor con SU modelo nulo, que es
«ejecutarlo todo». Lo que se compara es coste —llamadas al modelo y
compilados de Lean por consulta—; la calidad no se compara aquí porque haría
falta gastar API y Lean, y el argumento de que no baja es la regla del
módulo: lo que se apaga se apagó porque se midió que no batía a no hacerlo.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.stdout.reconfigure(encoding="utf-8")

from nucleo.decisor import (CAPACIDADES, COMPILADO, Contexto, LLAMADA, LOCAL,
                            decidir, decidir_todo, leer_veredicto)

SALIDA = RAIZ / "data" / "decisor_del_sistema.json"


def main(a) -> int:
    ctx = Contexto(consulta=a.consulta, es_matematica=True,
                   rasgos={"sin_notacion": 0})
    try:
        from nucleo.sintaxis import revisar
        r = revisar(a.consulta)
        ctx.rasgos = r.rasgos
    except Exception:                                       # noqa: BLE001
        pass

    d = decidir(ctx)
    todo = decidir_todo(ctx)

    print("CONSULTA: %s" % a.consulta)
    print("=" * 78)
    print()
    print("CORREN (%d)" % len(d.activas))
    for c in d.activas:
        print("   %s" % c.nombre)
        print("      %s" % c.que_hace)
        print("      %-14s %s" % (c.coste, d.motivos[c.nombre]))
        if c.donde:
            print("      -> %s" % c.donde)
        print()
    print("NO CORREN (%d)" % len(d.apagadas))
    for c in d.apagadas:
        print("   %s" % c.nombre)
        print("      %s" % c.que_hace)
        print("      %-14s %s" % (c.coste, d.motivos[c.nombre]))
        if c.donde:
            print("      -> %s" % c.donde)
        print()

    print("=" * 78)
    print("COSTE POR CONSULTA")
    print("   %-22s %-10s %-10s %s" % ("", "modelo", "Lean", "local"))
    for etiqueta, dec in (("decisor", d), ("su nulo (todo)", todo)):
        c = dec.coste
        print("   %-22s %-10d %-10d %d"
              % (etiqueta, c[LLAMADA], c[COMPILADO], c[LOCAL]))
    ahorro_lean = todo.coste[COMPILADO] - d.coste[COMPILADO]
    ahorro_llam = todo.coste[LLAMADA] - d.coste[LLAMADA]
    print()
    print("   ahorra %d compilado(s) de Lean y %d llamada(s) al modelo"
          % (ahorro_lean, ahorro_llam))

    perdedoras = [(c.nombre, d.veredictos[c.nombre]) for c in d.apagadas
                  if d.veredictos[c.nombre].gana is False]
    print()
    print("LO QUE SE APAGA POR MEDICION (%d)" % len(perdedoras))
    for n, v in perdedoras:
        print("   %-32s real %8.3f   nulo %8.3f" % (n, v.real, v.nulo))

    SALIDA.write_text(json.dumps({
        "consulta": a.consulta,
        "activas": [c.nombre for c in d.activas],
        "apagadas": [c.nombre for c in d.apagadas],
        "motivos": d.motivos,
        "veredictos": {k: {"real": v.real, "nulo": v.nulo, "gana": v.gana,
                           "motivo": v.motivo}
                       for k, v in d.veredictos.items()},
        "coste_decisor": d.coste,
        "coste_nulo": todo.coste,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    print()
    print("escrito -> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--consulta",
                    default="Demuestra que (a+b)^2 = a^2 + 2ab + b^2")
    raise SystemExit(main(ap.parse_args()))
