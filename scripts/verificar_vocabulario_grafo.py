# -*- coding: utf-8 -*-
"""
¿Existen de verdad los nombres Mathlib que declara el grafo?

INTENTO ANTERIOR, Y POR QUE FALLO. La primera medicion dio «8 de 117 existen»,
que era absurdo: `CompactSpace`, `MetricSpace` y `TopCat` estan en Mathlib sin
ninguna duda. El fallo era del instrumento — se comprobaba a traves de
`LeanClient.check_code`, que llama a `_normalize_code`, y ese **sustituye
`import Mathlib` por una cabecera estrecha** de seis modulos. Los nombres se
estaban comprobando contra un Mathlib recortado.

Aqui se invoca `lake env lean` directamente sobre un archivo con `import
Mathlib` entero: una sola ejecucion, sin normalizador de por medio, y se lee
que identificadores rechaza Lean.

Sin coste de API.

    python -m scripts.verificar_vocabulario_grafo
"""
import io
import json
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RAIZ = "E:/Metamatematico"
SALIDA = RAIZ + "/data/vocabulario_grafo.json"


def nombres_del_grafo():
    """Identificadores comprobables, por vertice.

    El campo `lean` a veces trae varios separados por coma y a veces una
    expresion (`Scheme + CategoryTheory.Over`). Solo se comprueba lo que es un
    identificador cualificado; el resto se cuenta aparte, sin darlo por bueno.
    """
    from nucleo.graph.interpretacion import VEREDICTO, VERTICES
    ident = re.compile(r"^[A-Za-z_][A-Za-z0-9_.']*$")
    por_vertice, raros = {}, {}
    for k, e in VEREDICTO.items():
        if e.marca not in VERTICES or not e.lean:
            continue
        piezas = [x.strip() for x in re.split(r"[,+]", e.lean) if x.strip()]
        ok = [x for x in piezas if ident.match(x)]
        no = [x for x in piezas if not ident.match(x)]
        if ok:
            por_vertice[k] = ok
        if no:
            raros[k] = no
    return por_vertice, raros


def main():
    por_vertice, raros = nombres_del_grafo()
    todos = sorted({x for v in por_vertice.values() for x in v})
    print("=== EL VOCABULARIO DEL GRAFO, CONTRA MATHLIB ENTERO ===")
    print("  vertices con nombre        : %d" % len(por_vertice))
    print("  identificadores a comprobar: %d" % len(todos))
    print("  expresiones no comprobables: %d vertices" % len(raros))

    # Un archivo, una ejecucion. Cada `#check` en su linea, para poder
    # atribuir cada error al identificador que lo causo.
    ruta = RAIZ + "/_vocab_check.lean"
    io.open(ruta, "w", encoding="utf-8").write(
        "import Mathlib\n" + "\n".join("#check @" + n for n in todos) + "\n")

    print("\n  ejecutando `lake env lean` (una sola vez, con Mathlib entero)...")
    try:
        p = subprocess.run(
            ["lake", "env", "lean", ruta], cwd=RAIZ,
            capture_output=True, text=True, encoding="utf-8",
            errors="replace", timeout=1800,
        )
        salida = (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired:
        print("  TIMEOUT a los 30 min — sin conclusion")
        os.remove(ruta)
        return 1
    finally:
        if os.path.exists(ruta):
            os.remove(ruta)

    # Lean marca la linea del error; la linea 1 es el import, asi que el
    # identificador N esta en la linea N+1.
    fallidos = set()
    for m in re.finditer(r":(\d+):\d+: error", salida):
        i = int(m.group(1)) - 2
        if 0 <= i < len(todos):
            fallidos.add(todos[i])
    # y por si el mensaje nombra el identificador directamente
    for m in re.finditer(r"[Uu]nknown identifier `([^`]+)`", salida):
        if m.group(1) in todos:
            fallidos.add(m.group(1))

    reales = [n for n in todos if n not in fallidos]
    print("\n  EXISTEN: %d de %d  (%.0f%%)"
          % (len(reales), len(todos), 100 * len(reales) / max(1, len(todos))))
    if fallidos:
        print("\n  NO existen (%d):" % len(fallidos))
        for n in sorted(fallidos):
            print("     %s" % n)

    # que vertices quedan sin ningun nombre valido: son los que habria que
    # corregir antes de usar el grafo como vocabulario
    huerfanos = [k for k, v in por_vertice.items()
                 if not any(x in reales for x in v)]
    print("\n  vertices SIN ningun nombre valido: %d" % len(huerfanos))
    for k in sorted(huerfanos)[:15]:
        print("     %-30s -> %s" % (k, ", ".join(por_vertice[k])))

    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    io.open(SALIDA, "w", encoding="utf-8").write(json.dumps(
        {"total": len(todos), "reales": reales, "fallidos": sorted(fallidos),
         "huerfanos": sorted(huerfanos),
         "no_comprobables": {k: v for k, v in raros.items()}},
        ensure_ascii=False, indent=2))
    print("\n  detalle -> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    sys.exit(main())
