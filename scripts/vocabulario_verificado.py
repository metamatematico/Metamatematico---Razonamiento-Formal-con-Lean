# -*- coding: utf-8 -*-
"""
¿Es el grafo un vocabulario VERIFICADO de Mathlib?

Del diagnostico de los fallos salio un resultado que cambia donde tiene sentido
meter el grafo: de 11 nombres de Mathlib que propuso el modelo, **10 no
existen**. `tsum_geometric_two`, `Subgroup.isCyclic`, `isOpen_union` — siguen la
convencion de nombres al dedillo y no estan. En el unico caso donde acerto
(`IsOpen.union`) lo enterro entre tres invenciones: tenia la respuesta y no
supo distinguirla de sus propias fabricaciones.

Eso le da al grafo un papel que no necesita razonamiento ni aceleracion: ser un
VOCABULARIO que existe. Pero antes de construir nada hay que comprobar la
premisa, porque seria ridiculo sustituir las invenciones del modelo por las del
grafo.

DOS MEDIDAS

  1. Los nombres que el grafo declara — 82 vertices con su `lean` — se pasan
     por `#check`. Sin coste de API: solo Lean.
  2. La tasa de invencion del modelo sobre una muestra mas amplia, para saber
     si el 10-de-11 del diagnostico era representativo.

    python -m scripts.vocabulario_verificado            # solo el grafo (gratis)
    python -m scripts.vocabulario_verificado --modelo N # + N consultas al LLM
"""
import argparse
import asyncio
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SALIDA = "E:/Metamatematico/data/vocabulario_verificado.json"

#: Conceptos para medir la invencion del modelo. Se eligen de areas que el
#: grafo cubre, que es donde tendria sentido que ayudase.
CONSULTAS = [
    "la suma de una serie geometrica de razon 1/2",
    "todo subgrupo de un grupo ciclico es ciclico",
    "la union de dos conjuntos abiertos es abierta",
    "la raiz de 2 es irracional",
    "hay infinitos numeros primos",
    "el elemento neutro de un grupo es unico",
    "el teorema fundamental del algebra",
    "toda funcion continua en un compacto alcanza su maximo",
    "el lema de Zorn",
    "la desigualdad de Cauchy-Schwarz",
]

PREGUNTA = """Nombra los lemas de Mathlib (Lean 4) que demuestran esto:

{q}

Responde SOLO con nombres completos y cualificados, separados por comas. Sin
explicacion, sin backticks. Si Mathlib no lo tiene, responde: NO EXISTE"""

_TERMINAL = ("credit balance", "authentication_error", "permission_error")
_TRANSITORIO = ("overloaded", "rate_limit", "APIConnectionError",
                "APITimeoutError", "InternalServerError", "529", "503")


def _terminal(e):
    return any(p.lower() in str(e).lower() for p in _TERMINAL)


def _transitorio(e):
    return any(p.lower() in str(e).lower() for p in _TRANSITORIO)


async def _reintenta(fn, intentos=3, espera=8):
    ultimo = None
    for i in range(intentos):
        try:
            return await fn(), None
        except Exception as e:
            ultimo = e
            if _terminal(e) or not _transitorio(e):
                return None, e
            if i < intentos - 1:
                print("   saturado, reintento %d..." % (i + 1))
                await asyncio.sleep(espera)
    return None, ultimo


def _clave():
    if os.environ.get("ANTHROPIC_API_KEY"):
        return True
    p = "E:/Metamatematico/.env"
    if not os.path.exists(p):
        return False
    m = re.search(r'ANTHROPIC_API_KEY\s*=\s*["\']?([^"\'\r\n]+)',
                  io.open(p, encoding="utf-8-sig").read())
    if m:
        os.environ["ANTHROPIC_API_KEY"] = m.group(1).strip()
        return True
    return False


def _nombres_del_grafo():
    """Los nombres Mathlib que el grafo declara, uno por vertice.

    El campo `lean` a veces lleva varios separados por coma, y a veces una
    expresion (`Scheme + CategoryTheory.Over`). Se parte y se limpia: lo que
    no sea un identificador cualificado no se puede comprobar con `#check` y
    se cuenta aparte, sin darlo por bueno ni por malo.
    """
    from nucleo.graph.interpretacion import VEREDICTO, VERTICES
    ident = re.compile(r"^[A-Za-z_][A-Za-z0-9_.']*$")
    comprobables, no_comprobables = {}, {}
    for k, e in VEREDICTO.items():
        if e.marca not in VERTICES or not e.lean:
            continue
        piezas = [x.strip() for x in re.split(r"[,+]", e.lean) if x.strip()]
        ok = [x for x in piezas if ident.match(x)]
        no = [x for x in piezas if not ident.match(x)]
        if ok:
            comprobables[k] = ok
        if no:
            no_comprobables[k] = no
    return comprobables, no_comprobables


async def _existen(lean, nombres):
    """Devuelve el subconjunto que Lean acepta. Por lotes, luego uno a uno."""
    if not nombres:
        return set()
    codigo = "import Mathlib\n" + "\n".join("#check @" + n for n in nombres)
    r = await lean.check_code(codigo)
    if str(getattr(r, "status", "")).endswith("SUCCESS"):
        return set(nombres)
    reales = set()
    for n in nombres:
        r1 = await lean.check_code("import Mathlib\n#check @" + n)
        if str(getattr(r1, "status", "")).endswith("SUCCESS"):
            reales.add(n)
    return reales


async def main(n_modelo):
    import logging
    logging.basicConfig(level=logging.CRITICAL)
    from nucleo.core import Nucleo
    from nucleo.config import NucleoConfig
    from nucleo.llm.contador import Contador

    _clave()
    n = Nucleo(NucleoConfig())
    await n.initialize()
    informe = {}

    # ── 1 · el vocabulario del grafo, sin coste de API ───────────────────
    comprobables, raros = _nombres_del_grafo()
    todos = sorted({x for v in comprobables.values() for x in v})
    print("=== EL VOCABULARIO DEL GRAFO ===")
    print("  vertices con nombre Mathlib : %d" % len(comprobables))
    print("  identificadores comprobables: %d" % len(todos))
    print("  expresiones no comprobables : %d vertices" % len(raros))
    print("  comprobando con Lean, por lotes de 12...\n")

    reales = set()
    for i in range(0, len(todos), 12):
        lote = todos[i:i + 12]
        r = await _existen(n._lean, lote)
        reales |= r
        malos = [x for x in lote if x not in r]
        print("   lote %2d: %2d/%2d existen%s"
              % (i // 12 + 1, len(r), len(lote),
                 ("  ->  NO: " + ", ".join(malos)) if malos else ""))

    inventados = [x for x in todos if x not in reales]
    print("\n  EL GRAFO: %d de %d existen (%.0f%%)"
          % (len(reales), len(todos), 100 * len(reales) / max(1, len(todos))))
    if inventados:
        print("  no existen: %s" % ", ".join(inventados))
    informe["grafo"] = {"total": len(todos), "reales": sorted(reales),
                        "inventados": inventados}

    # ── 2 · la tasa de invencion del modelo ──────────────────────────────
    if n_modelo:
        print("\n=== LA TASA DE INVENCIÓN DEL MODELO ===")
        prop = inv = 0
        filas = []
        for q in CONSULTAS[:n_modelo]:
            r, err = await _reintenta(
                lambda: n._llm.generate(PREGUNTA.format(q=q),
                                        sin_historial=True))
            if err is not None:
                print("   NO MEDIDO (%s) — se detiene" % str(err)[:50])
                informe["modelo_incompleto"] = True
                break
            crudo = (r.content or "").strip()
            if "NO EXISTE" in crudo.upper():
                print("   %-46s el modelo dice que no existe" % q[:46])
                continue
            nombres = [x.strip().strip("`.,")
                       for x in re.split(r"[,\n]", crudo) if x.strip()][:4]
            ok = await _existen(n._lean, nombres)
            prop += len(nombres)
            inv += len(nombres) - len(ok)
            print("   %-46s %d/%d reales" % (q[:46], len(ok), len(nombres)))
            if ok:
                print("        existen: %s" % ", ".join(sorted(ok)))
            filas.append({"consulta": q, "propuestos": nombres,
                          "reales": sorted(ok)})
        if prop:
            print("\n  EL MODELO: %d de %d inventados (%.0f%%)"
                  % (inv, prop, 100 * inv / prop))
        informe["modelo"] = {"propuestos": prop, "inventados": inv,
                             "detalle": filas}

    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    io.open(SALIDA, "w", encoding="utf-8").write(
        json.dumps(informe, ensure_ascii=False, indent=2))
    print("\n  detalle -> %s" % SALIDA)
    print("  " + Contador.resumen().splitlines()[-1])
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--modelo", type=int, default=0,
                    help="cuantas consultas al LLM (0 = solo el grafo)")
    a = ap.parse_args()
    sys.exit(asyncio.run(main(a.modelo)))
