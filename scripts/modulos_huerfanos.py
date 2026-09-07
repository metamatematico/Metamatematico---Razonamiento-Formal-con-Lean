# -*- coding: utf-8 -*-
"""Que modulos de `nucleo/` no alcanza nadie desde los puntos de entrada.

UN MODULO HUERFANO NO ES CODIGO MUERTO. Puede ser una herramienta que solo
usan los scripts, o algo a medio conectar. Lo que dice esta medicion es
"nadie lo alcanza desde el arranque", y eso hay que leerlo caso por caso.

ESTE INSTRUMENTO YA DIO TRES RESPUESTAS FALSAS. Van escritas porque cualquier
version ingenua las repite:

  1. `from paquete import submodulo` parece importar un NOMBRE del paquete y
     es un import de MODULO. Ignorarlo dejaba `lean.nombres` como huerfano
     teniendo dos llamadas en core.py.
  2. `from . import x` y `from .x import y` son relativos: hay que resolver
     el punto contra el paquete del fichero que los escribe.
  3. `__init__.py` SE EJECUTA al importar cualquier submodulo. Si
     `nucleo/lean/__init__.py` importa algo, ese algo esta alcanzado en
     cuanto alguien toca `nucleo.lean.loquesea`.

LO QUE SIGUE SIN VER, y por eso el resultado es una cota superior de
huerfanos: los imports por cadena (`importlib.import_module("nucleo.x")`) y
los que estan dentro de un `try` que se traga el fallo. Si un modulo sale
huerfano, mirar a mano antes de tocarlo.

No gasta API.
"""
import ast
import io
import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

RAIZ = "E:/Metamatematico"
PAQUETE = "nucleo"
#: por donde entra el sistema de verdad
ENTRADAS = ("nucleo/core.py", "nucleo/__init__.py", "nucleo/__main__.py",
            "nucleo/cli.py", "app.py")


def modulo_de(ruta):
    """`nucleo/lean/client.py` -> `nucleo.lean.client`."""
    rel = os.path.relpath(ruta, RAIZ).replace(os.sep, "/")[:-3]
    if rel.endswith("/__init__"):
        rel = rel[:-9]
    return rel.replace("/", ".")


def todos_los_modulos():
    fuera = {}
    for r, _d, fs in os.walk(os.path.join(RAIZ, PAQUETE)):
        if "__pycache__" in r:
            continue
        for f in fs:
            if f.endswith(".py"):
                p = os.path.join(r, f)
                fuera[modulo_de(p)] = p
    return fuera


def importa(ruta, mio, existentes):
    """Los modulos del paquete que este fichero alcanza."""
    try:
        arbol = ast.parse(io.open(ruta, encoding="utf-8", errors="replace").read())
    except SyntaxError:
        return set()
    paquete = mio.rsplit(".", 1)[0] if "." in mio else mio
    if os.path.basename(ruta) == "__init__.py":
        paquete = mio
    fuera = set()
    for n in ast.walk(arbol):
        if isinstance(n, ast.Import):
            for a in n.names:
                if a.name.split(".")[0] == PAQUETE:
                    fuera.add(a.name)
        elif isinstance(n, ast.ImportFrom):
            if n.level:                       # relativo: resolver el punto
                partes = paquete.split(".")
                base = ".".join(partes[:len(partes) - n.level + 1])
                base = base + "." + n.module if n.module else base
            else:
                base = n.module or ""
            if base.split(".")[0] != PAQUETE:
                continue
            fuera.add(base)
            # `from paquete import submodulo` es un import de MODULO
            for a in n.names:
                cand = base + "." + a.name
                if cand in existentes:
                    fuera.add(cand)
    return fuera


def main():
    mods = todos_los_modulos()
    pila = []
    for e in ENTRADAS:
        p = os.path.join(RAIZ, e)
        if os.path.exists(p):
            pila.append(modulo_de(p) if e.startswith(PAQUETE) else "__app__")
            if not e.startswith(PAQUETE):
                mods["__app__"] = p
    visto = set()
    while pila:
        m = pila.pop()
        if m in visto or m not in mods:
            continue
        visto.add(m)
        for x in importa(mods[m], m, mods):
            pila.append(x)
            # el __init__ del paquete de x se ejecuta tambien
            partes = x.split(".")
            for i in range(1, len(partes)):
                pila.append(".".join(partes[:i]))

    huerfanos = sorted(m for m in mods
                       if m != "__app__" and m not in visto)
    print("modulos en %s/          : %d" % (PAQUETE, len(mods) - 1))
    print("alcanzados desde el arranque: %d" % len([m for m in visto if m in mods and m != "__app__"]))
    print("NO alcanzados               : %d\n" % len(huerfanos))
    for m in huerfanos:
        n = len(io.open(mods[m], encoding="utf-8", errors="replace").readlines())
        print("   %-44s %4d lineas" % (m, n))
    print("\nRecordatorio: esto es una COTA SUPERIOR. No ve importlib ni los")
    print("imports dentro de un try que se traga el fallo. Mirar a mano.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
