# -*- coding: utf-8 -*-
"""Construye la categoría de estados de prueba y la mide.

QUE MIDE, Y POR QUE CADA COSA
-----------------------------
  1. LA FORMA. Objetos, flechas, cuántas componen. Sin composición no hay
     categoría: habría una lista de pares.

  2. EL OBJETO TERMINAL. `no goals` recibe más de la mitad de las flechas. Es
     el enunciado categórico de «una prueba acaba cuando no quedan objetivos»,
     y además explica una cifra que engaña: en bruto sale UNA componente conexa
     con el 99,9 % de los objetos. Quitando el sumidero quedan trece mil.
     Por eso se mide la conectividad CON y SIN él.

  3. LAS PARALELAS. Dos tácticas distintas con el mismo origen y el mismo
     destino. Es lo único que esta categoría afirma y un árbol no podría.

  4. LA RAMIFICACION, que es la MALA noticia y va aquí para que nadie la pase
     por alto: cuántos estados registran más de una táctica distinta. Si son
     pocos, el corpus no puede enseñar a ELEGIR, porque recoge la prueba que
     alguien escribió y no las que descartó.

No gasta API. Necesita el dataset LeanWorkbook en disco.

    python -m scripts.categoria_de_estados
"""
from __future__ import annotations

import collections
import io
import json
import pathlib
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

RAIZ = pathlib.Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

FUENTE = "E:/MetamatematicoDataSet/LeanWorkbook"
SALIDA = RAIZ / "data" / "categoria_de_estados.json"


def _componentes(objetos, pares) -> collections.Counter:
    padre = {o: o for o in objetos}

    def raiz(x):
        while padre[x] != x:
            padre[x] = padre[padre[x]]
            x = padre[x]
        return x

    for a, b in pares:
        if a not in padre or b not in padre:
            continue
        ra, rb = raiz(a), raiz(b)
        if ra != rb:
            padre[ra] = rb
    return collections.Counter(raiz(o) for o in objetos)


def main() -> int:
    from datasets import load_from_disk

    from nucleo.graph.estados import TERMINAL, construir

    d = load_from_disk(FUENTE)
    ds = d[list(d.keys())[0]] if hasattr(d, "keys") else d
    c = construir((r["state_before"], r["tactic"], r["state_after"])
                  for r in ds)

    cierran = sum(1 for f in c.flechas if f.cierra)
    conj_origen = set(c.salientes)
    componen = sum(1 for f in c.flechas if f.destino in conj_origen)

    print("1 · LA FORMA")
    print("   objetos (estados)          %6d" % len(c.objetos))
    print("   flechas (tácticas)         %6d" % len(c.flechas))
    print("   flechas por objeto         %8.2f" % (len(c.flechas) / len(c.objetos)))
    print("   COMPONEN                   %6d  (%.1f %%)"
          % (componen, 100.0 * componen / len(c.flechas)))

    print("\n2 · EL OBJETO TERMINAL")
    print("   flechas que llegan a `%s`  %6d  (%.1f %%)"
          % (TERMINAL, c.entrantes[TERMINAL],
             100.0 * c.entrantes[TERMINAL] / len(c.flechas)))
    con = _componentes(c.objetos, [(f.origen, f.destino) for f in c.flechas])
    sin_obj = {o for o in c.objetos if o != TERMINAL}
    sin = _componentes(sin_obj, [(f.origen, f.destino) for f in c.flechas
                                 if not f.cierra])
    tam_con, tam_sin = collections.Counter(con.values()), collections.Counter(sin.values())
    print("   componentes CON el terminal %5d   la mayor %6d" % (len(con), max(tam_con)))
    print("   componentes SIN el terminal %5d   la mayor %6d" % (len(sin), max(tam_sin)))
    print("   -> la conectividad es ENTERA a traves del terminal")

    print("\n3 · LAS PARALELAS  (dos tacticas, mismo origen y destino)")
    par = c.paralelas()
    print("   pares                      %6d" % len(par))
    vistas = collections.Counter()
    for _o, _d, tacs in par:
        vistas[" / ".join(tacs)] += 1
    for k, v in vistas.most_common(6):
        print("      %-34s %d" % (k, v))

    print("\n4 · LA RAMIFICACION  (lo que este corpus NO puede enseñar)")
    ramifican = sum(1 for fs in c.salientes.values()
                    if len({f.tactica for f in fs}) > 1)
    print("   estados con >1 tactica distinta %4d de %d  (%.2f %%)"
          % (ramifican, len(c.objetos), 100.0 * ramifican / len(c.objetos)))
    print("   El corpus recoge la prueba que alguien escribio, no las que")
    print("   descarto: casi nunca hay dos opciones en el mismo punto.")

    # EL TOPE DE `camino` ES UNA SALVAGUARDA, NO UNA MEDIDA. Con el valor por
    # defecto (60) esta medicion informaba «longitud maxima 60», que es el
    # tope y no la cadena: la mas larga tiene 108 pasos. Un limite del codigo
    # publicado como si fuera un hallazgo del corpus.
    largos = []
    for r0 in c.raices():
        largos.append(len(c.camino(r0, tope=10000)))
    print("\n   cadenas: %d raices, longitud media %.2f, maxima %d"
          % (len(largos), sum(largos) / max(1, len(largos)), max(largos or [0])))

    datos = {
        "fuente": FUENTE,
        "objetos": len(c.objetos),
        "flechas": len(c.flechas),
        "cierran": cierran,
        "componen": componen,
        "terminal": TERMINAL,
        "flechas_al_terminal": c.entrantes[TERMINAL],
        "componentes_con_terminal": len(con),
        "componentes_sin_terminal": len(sin),
        "mayor_sin_terminal": max(tam_sin),
        "paralelas": len(par),
        "paralelas_por_par": dict(vistas.most_common(20)),
        "estados_que_ramifican": ramifican,
        "raices": len(largos),
        "longitud_media": round(sum(largos) / max(1, len(largos)), 3),
        "longitud_maxima": max(largos or [0]),
    }
    io.open(SALIDA, "w", encoding="utf-8").write(
        json.dumps(datos, ensure_ascii=False, indent=2))
    print("\nescrito -> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
