# -*- coding: utf-8 -*-
"""Una consulta real por el camino real, enseñando CADA etapa.

POR QUE HACE FALTA, Y QUE NO SUSTITUYE
--------------------------------------
Los 1124 tests comprueban las piezas y el auditor comprueba que dicen lo mismo
entre si. Ninguno de los dos ejecuta la cadena entera: emparejar, ofrecer
nombres, elegir imports, llamar al modelo, compilar con Lean, reparar y
traducir. Los tres fallos que reporto el usuario en septiembre —modulo
ausente, clase del nombre ausente, enunciado del lema ausente— pasaron los
1124 tests y el auditor, y se veian en cuanto se corria UNA consulta.

Este script corre esa consulta e imprime lo que el sistema decide en cada
paso, para poder mirar donde se tuerce en vez de leer solo el veredicto.

CUESTA DINERO. Es la unica pieza de la bateria que llama al modelo, asi que no
se ejecuta en la suite: se lanza a mano cuando hay que comprobar que el camino
entero funciona.

    python -m scripts.humo_extremo_a_extremo
    python -m scripts.humo_extremo_a_extremo "otra consulta"
    python -m scripts.humo_extremo_a_extremo --bateria
    python -m scripts.humo_extremo_a_extremo --tasa=5    # mide, no comprueba
"""
from __future__ import annotations

import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

#: La que fallo tres veces seguidas. Es el caso de regresion del sistema.
CONSULTA = "Demuestra que todo espacio vectorial tiene una base"

#: LA BATERIA, elegida para tocar caminos DISTINTOS y no tres veces el mismo.
#:
#: Una sola consulta verificada no dice que el sistema funcione: dice que
#: funciona para esa. Cada una de estas entra por una puerta distinta —area,
#: forma del enunciado, idioma, y una que NO debe formalizarse— porque los
#: fallos de este sistema han estado siempre en las costuras, no en el centro.
BATERIA = [
    ("regresion  ", "Demuestra que todo espacio vectorial tiene una base"),
    ("aritmetica ", "Demuestra que la raiz cuadrada de 2 es irracional"),
    ("lean directo", "example (n : Nat) : n + 0 = n := by ?"),
    ("no es mates", "Hola, quien eres y para que sirves"),
]


def _tasa(n, consulta, veces):
    """La misma consulta N veces: esto no es una prueba, es una MEDICION.

    `temperature` esta en 0,7, asi que el modelo MUESTREA la formalizacion:
    cada corrida escribe un enunciado distinto y unos compilan y otros no. Una
    corrida que sale verde no dice que el sistema funcione; dice que funciono
    esa vez. Yo mismo llame «intermitente» a este caso despues de verlo dar
    `verificado` y luego `no_verificado` con la misma entrada, y no era
    intermitencia: era una tasa de exito que nadie habia medido.

    La cota: N corridas son N formalizaciones mas sus revisiones. A ~0,03 $ por
    llamada y ~4 llamadas por corrida, N=5 son unos 0,60 $. No se sube sin
    motivo.
    """
    from collections import Counter
    filas = []
    for i in range(1, veces + 1):
        t0 = time.time()
        try:
            r = n.process_sync(consulta)
            est = getattr(r, "metadata", None) or {}
            lr = getattr(r, "lean_result", None)
            estado = est.get("verification_status") or "(sin veredicto)"
            rondas = est.get("rondas_revision", 0)
            lean = getattr(getattr(lr, "status", None), "name", "-")
        except Exception as e:                                  # noqa: BLE001
            estado, rondas, lean = "EXCEPCION: %s" % type(e).__name__, "-", "-"
        filas.append((i, estado, rondas, lean, time.time() - t0))
        print("  %2d/%d  %-16s rondas=%-3s %-14s %4.0f s"
              % (i, veces, estado[:16], rondas, lean[:14], filas[-1][4]))

    _titulo("TASA DE EXITO · %d corridas" % veces)
    print("  " + consulta)
    cuenta = Counter(f[1] for f in filas)
    ok = cuenta.get("verificado", 0)
    for k, v in cuenta.most_common():
        print("   %-18s %d" % (k, v))
    print()
    print("  verificado en %d de %d  (%.0f %%)"
          % (ok, veces, 100.0 * ok / veces))

    # LA ALARMA DE INSTRUMENTO ROTO. Si TODAS las corridas dan exactamente lo
    # mismo con temperature 0,7, lo raro no es el resultado: es que no haya
    # variacion. O hay una cache por medio, o las corridas no son
    # independientes, y entonces esta cifra no mide lo que dice medir.
    if veces >= 3 and len(cuenta) == 1:
        print()
        print("  AVISO: %d corridas identicas con temperature 0,7."
              % veces)
        print("  Comprobar que no hay cache entre medias antes de citar "
              "esta cifra.")
    return 0


def _titulo(t):
    print("\n" + "=" * 72)
    print(t)
    print("=" * 72)


def main() -> int:
    import warnings
    import logging
    warnings.filterwarnings("ignore")
    logging.disable(logging.WARNING)

    bateria = "--bateria" in sys.argv
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    consulta = args[0] if args else CONSULTA

    from dotenv import load_dotenv
    load_dotenv(os.path.join(RAIZ, ".env"))

    from nucleo.core import Nucleo, PLAZAS_CON_NOMBRES
    from nucleo.config import NucleoConfig

    _titulo("CONSULTA")
    print("  " + consulta)

    # EL CONSTRUCTOR NO CONSTRUYE EL GRAFO. `Nucleo(cfg)` vuelve en 0,7 s con
    # `_graph = None`; quien lo monta todo —skills, colimites, agentes— es
    # `initialize()`, que es asincrono y en la app corre en un hilo aparte.
    # Llamar al constructor y darse por listo es un error facil: el objeto
    # existe, no falla nada, y el grafo esta vacio.
    import asyncio
    cfg_yaml = os.path.join(RAIZ, "nucleo_config.yaml")
    cfg = (NucleoConfig.from_yaml(cfg_yaml) if os.path.exists(cfg_yaml)
           else NucleoConfig())
    t0 = time.time()
    n = Nucleo(cfg)
    asyncio.run(n.initialize())
    print("\n  nucleo listo en %.1f s · %d skills"
          % (time.time() - t0, len(list(n._graph.skills))))

    veces = 0
    for x in sys.argv:
        if x.startswith("--tasa="):
            veces = int(x.split("=", 1)[1])
    if veces:
        return _tasa(n, consulta, veces)

    if bateria:
        return _bateria(n)

    g = n._graph
    _titulo("1 · QUE ENGANCHA EL GRAFO")
    ids = [getattr(x, "id", x)
           for x in Nucleo._match_skills_to_query(n, consulta, g)]
    for sid in ids[:8]:
        sk = g.get_skill(sid)
        print("   %-34s %s" % (sid, (sk.metadata or {}).get("sort") if sk else "?"))

    _titulo("2 · QUE NOMBRES OFRECE, Y DE QUE CLASE")
    noms = n._nombres_mathlib(ids, consulta, g)
    if not noms:
        print("   NINGUNO — el prompt sale sin vocabulario del grafo")
    for sid, v in noms.items():
        print("   %-26s %s" % (sid, n._con_su_clase(v)))
    print("\n   (plazas con nombre = %d)" % PLAZAS_CON_NOMBRES)

    _titulo("3 · QUE MODULOS MANDA IMPORTAR")
    ctx = {"relevant_skills": ids, "mathlib_verificado": noms}
    mods = n._modulos_de_los_nombres(ctx)
    for m in mods:
        print("   " + m)
    if not mods:
        print("   NINGUNO — el nombre ofrecido no se podra resolver")

    _titulo("4 · EL CAMINO ENTERO (llama al modelo y a Lean)")
    t0 = time.time()
    r = n.process_sync(consulta)
    print("  %.1f s" % (time.time() - t0))

    est = getattr(r, "metadata", None) or {}

    # EL CODIGO SALE DEL `lean_result`, no de los metadatos: ahi es donde el
    # pipeline deja lo que Lean compilo DE VERDAD, despues de normalizar la
    # cabecera y de las rondas de reparacion. Leerlo de otro sitio enseñaria
    # lo que el modelo escribio, que es otra cosa.
    lr = getattr(r, "lean_result", None)

    for k in sorted(est):
        v = est[k]
        if isinstance(v, (str, int, float, bool)) and len(str(v)) < 90:
            print("   %-24s %s" % (k, v))
    if lr is not None:
        print("   %-24s %s" % ("lean status", getattr(
            getattr(lr, "status", None), "name", "?")))

    codigo = (getattr(lr, "code", "") or est.get("lean_code")
              or est.get("codigo_lean") or "")
    if codigo:
        _titulo("5 · EL LEAN QUE SE COMPILO")
        for linea in codigo.splitlines():
            print("   " + linea)

    _titulo("VEREDICTO")
    print("  status:", est.get("verification_status", "(sin dato)"))
    texto = (getattr(r, "content", "") or "")[:400]
    print("\n  respuesta (primeros 400):")
    for l in texto.splitlines()[:10]:
        print("   " + l)
    return 0


def _bateria(n) -> int:
    """Varias consultas por el camino real, con el nucleo ya montado.

    Se monta UNA vez: `initialize()` tarda lo suyo y el warmup de Mathlib mas,
    asi que reiniciarlo por consulta mediria el arranque en vez del sistema.
    """
    from nucleo.core import Nucleo
    filas = []
    for etiqueta, q in BATERIA:
        t0 = time.time()
        try:
            r = n.process_sync(q)
            est = getattr(r, "metadata", None) or {}
            lr = getattr(r, "lean_result", None)
            estado = est.get("verification_status") or "(sin veredicto)"
            rondas = est.get("rondas_revision", 0)
            lean = getattr(getattr(lr, "status", None), "name", "-")
        except Exception as e:                                  # noqa: BLE001
            estado, rondas, lean = "EXCEPCION: %s" % type(e).__name__, "-", "-"
        filas.append((etiqueta, q, estado, rondas, lean, time.time() - t0))
        print("  %s  %-28s %5.0f s" % (etiqueta, estado, filas[-1][5]))

    _titulo("BATERIA")
    print("  %-12s %-16s %-7s %-14s %6s  %s"
          % ("caso", "veredicto", "rondas", "lean", "seg", "consulta"))
    for et, q, estado, rondas, lean, seg in filas:
        print("  %-12s %-16s %-7s %-14s %5.0f  %s"
              % (et, estado[:16], rondas, lean[:14], seg, q[:44]))

    malos = [f for f in filas if str(f[2]).startswith("EXCEPCION")]
    print("\n  excepciones: %d de %d" % (len(malos), len(filas)))
    return 1 if malos else 0


if __name__ == "__main__":
    raise SystemExit(main())
