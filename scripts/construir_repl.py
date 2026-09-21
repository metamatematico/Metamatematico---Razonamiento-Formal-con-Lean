# -*- coding: utf-8 -*-
"""Trae y construye el REPL de Lean con el toolchain EXACTO del proyecto.

POR QUE UN GUION Y NO UNAS INSTRUCCIONES EN UN README
------------------------------------------------------
`nucleo/lean/sesion.py` no sirve de nada sin este binario, y el binario no
está en el repositorio —son 11 MB de artefacto de terceros—. Un README que
diga «clona y construye» deja fuera lo único que importa, que es CUAL clonar:

    el REPL tiene un tag por version de Lean, y `master` va por delante
    del toolchain de este proyecto.

Con un REPL de otra version el fallo no es limpio: elabora, contesta, y se
equivoca en casos concretos. Se habria echado la culpa al diseño.

QUE HACE
--------
  1. lee `lean-toolchain` del proyecto           -> v4.29.0-rc4
  2. clona el REPL en ESE tag, en `.lake/repl`   -> ya ignorado por git
  3. `lake build`                                -> ~40 s, no depende de Mathlib
  4. comprueba que el toolchain del REPL coincide con el del proyecto

`.lake` es una junction a C:\\MetamatematicoLake en esta maquina, asi que el
binario acaba en el SSD y no en el disco USB. Eso no se fuerza aqui: se hereda
de donde apunte `.lake`.

No gasta API.

    python -m scripts.construir_repl
    python -m scripts.construir_repl --rehacer   # borra y vuelve a empezar
"""
from __future__ import annotations

import argparse
import io
import os
import shutil
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

ORIGEN = "https://github.com/leanprover-community/repl"
DESTINO = os.path.join(RAIZ, ".lake", "repl")
BINARIO = os.path.join(DESTINO, ".lake", "build", "bin",
                       "repl.exe" if sys.platform == "win32" else "repl")


def toolchain_de(carpeta: str) -> str:
    ruta = os.path.join(carpeta, "lean-toolchain")
    try:
        return io.open(ruta, encoding="utf-8").read().strip()
    except OSError:
        return ""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--rehacer", action="store_true")
    args = ap.parse_args()

    tc = toolchain_de(RAIZ)
    if not tc:
        print("no se pudo leer %s/lean-toolchain" % RAIZ)
        return 1
    # `leanprover/lean4:v4.29.0-rc4`  ->  `v4.29.0-rc4`, que es el tag del REPL
    tag = tc.split(":")[-1].strip()
    print("toolchain del proyecto : %s" % tc)
    print("tag del REPL a usar    : %s\n" % tag)

    if args.rehacer and os.path.isdir(DESTINO):
        print("borrando %s ..." % DESTINO)
        shutil.rmtree(DESTINO, ignore_errors=True)

    if not os.path.isdir(DESTINO):
        print("clonando en %s ..." % DESTINO)
        r = subprocess.run(["git", "clone", "--depth", "1", "--branch", tag,
                            ORIGEN, DESTINO], capture_output=True, text=True)
        if r.returncode != 0:
            print("  fallo el clon: %s" % (r.stderr or "")[:300])
            print("  ¿existe el tag %s? Los tags del REPL van por version de "
                  "Lean." % tag)
            return 1
    else:
        print("ya existe %s (usa --rehacer para empezar de cero)" % DESTINO)

    # LA COMPROBACION QUE JUSTIFICA ESTE GUION: que sean el mismo toolchain.
    tc_repl = toolchain_de(DESTINO)
    print("\ntoolchain del REPL     : %s" % tc_repl)
    if tc_repl != tc:
        print("  NO COINCIDE con el del proyecto. Se para aqui: un REPL de")
        print("  otra version elabora y contesta, pero se equivoca en casos")
        print("  concretos, y el fallo se leeria como fallo del diseño.")
        return 1
    print("  coinciden\n")

    print("construyendo ...")
    r = subprocess.run(["lake", "build"], cwd=DESTINO, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    ultimas = [l for l in (r.stdout or "").split("\n") if l.strip()][-3:]
    for l in ultimas:
        print("  %s" % l)
    if r.returncode != 0:
        print("  fallo la construccion: %s" % (r.stderr or "")[:300])
        return 1

    if not os.path.exists(BINARIO):
        print("\nconstruyo sin error pero no hay binario en %s" % BINARIO)
        return 1
    print("\n-> %s  (%.1f MB)"
          % (BINARIO, os.path.getsize(BINARIO) / 1e6))
    print("\nComprobar que responde:")
    print("   python -m scripts.sesion_contra_fichero --n 3")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
