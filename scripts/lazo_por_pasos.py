# -*- coding: utf-8 -*-
"""La puerta del paso 3: ¿el lazo por pasos verifica más que lo servido?

DOS MODOS, Y SÓLO UNO ES LA PUERTA
----------------------------------
    sin_api   las dos ramas sobre la MISMA grabación, gratis:
                A  lo que el sistema de hoy hace con el código que escribió el
                   modelo (`scripts/replay.py`: reparador, imports, compilado,
                   cascada). Sin las rondas de reparación, que gastan API.
                B  el lazo, sólo con D0, sobre el ENUNCIADO de ese código con
                   la prueba cambiada por `sorry`. Sin boceto ni modelo.
              Es un suelo: cuánto cierra la búsqueda sola frente a lo que el
              modelo ya había escrito.

              La primera versión comparaba B con los veredictos de la campaña
              del 2026-09-10, y no son la misma formalización: la campaña es
              de `sonnet-5` y la grabación «completo» de `opus-5` del
              2026-09-08, y aquel veredicto incluye rondas de reparación. Un
              «rescate» salió de ahí y no lo era. El control tiene que salir
              de la MISMA grabación y de la MISMA corrida.
    con_api   la puerta de verdad: el formalizador pide un BOCETO —el
              enunciado y `have` intermedios con `sorry`— y el mediador busca
              con D0 y D3 (el modelo, con la retroalimentación del estado).
              Gasta API, y por eso sin `--ejecutar` sólo ESTIMA el coste.

LA REGLA DE LA PUERTA, ESCRITA ANTES DE CORRER (§9 de la propuesta)
-------------------------------------------------------------------
Las dos ramas sobre las MISMAS consultas y en la MISMA corrida —el control no
es la cifra de una campaña vieja, que se midió con la cascada rota—:

    A · lo servido     `Nucleo._math_via_lean`, la configuración de hoy
    B · el lazo        boceto + mediador (D0, D3) + el fichero como juez

    SIGUE si B verifica más que A, pareado, con McNemar exacto sobre los
    discordantes; y B no rompe ningún caso que A verificaba sin que se vea
    el porqué.

Con 20 casos no hay potencia para un efecto pequeño —el vocabulario dio 3
rescates y 2 roturas, p = 1,0—: por eso la propuesta pide el banco ampliado.
Este guion corre primero las 20 y deja escrito cuánto costaría el resto.

    python -m scripts.lazo_por_pasos                  # sin API, suelo
    python -m scripts.lazo_por_pasos --con-api        # estima, no gasta
    python -m scripts.lazo_por_pasos --con-api --ejecutar --tope 5
"""
from __future__ import annotations

import argparse
import asyncio
import collections
import io
import json
import os
import re
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

CAMPANA = os.path.join(RAIZ, "data", "campana_completo.json")
GRABACIONES = os.path.join(RAIZ, "data", "grabaciones", "formalizaciones.jsonl")
SALIDA = os.path.join(RAIZ, "data", "lazo_por_pasos.%s.json")

_TEO = re.compile(r"^\s*(?:@\[[^\]]*\]\s*)?(?:theorem|lemma|example)\b", re.M)


def enunciado_con_sorry(codigo: str):
    """El código hasta el `:=` del primer teorema, y `by sorry` detrás.

    None si no hay teorema. Lo de antes —imports, `open`, `variable`— se
    conserva: es el contexto del enunciado.
    """
    m = _TEO.search(codigo or "")
    if not m:
        return None
    resto = codigo[m.start():]
    # el `:=` de nivel cero que abre la prueba, no uno dentro de un `let`
    prof, i = 0, 0
    while i < len(resto) - 1:
        ch = resto[i]
        if ch in "([{⟨":
            prof += 1
        elif ch in ")]}⟩":
            prof -= 1
        elif resto.startswith(":=", i) and prof == 0:
            return codigo[:m.start()] + resto[:i].rstrip() + " := by\n  sorry\n"
        i += 1
    return None


def cargar_casos():
    """(consulta, grabación «completo» más reciente) para las 20 de la campaña."""
    c = json.load(io.open(CAMPANA, encoding="utf-8"))
    consultas = [f["consulta"] for f in c["filas"]]
    ultima = {}
    for l in io.open(GRABACIONES, encoding="utf-8"):
        if not l.strip():
            continue
        d = json.loads(l)
        if d.get("config") == "completo" and d.get("consulta") in consultas:
            ultima[d["consulta"]] = d
    return [(q, ultima.get(q)) for q in consultas]


async def sin_api(p):
    from nucleo.core import Nucleo, NucleoConfig
    from nucleo.lean import nombres
    from nucleo.lean.sesion import SesionLean
    from nucleo.lean.solver_cascade import SolverCascade
    from nucleo.lazo.mediador import Mediador
    from nucleo.lazo.proponentes import D0Cascada
    from nucleo.lazo.registro import Registro
    from scripts.replay import CONFIGS, reproduce

    # el núcleo del camino servido, como lo monta `replay.py`: sin él la rama A
    # no sería lo que el sistema hace hoy
    nucleo = Nucleo(NucleoConfig())
    ini = getattr(nucleo, "initialize", None)
    if ini is not None:
        r = ini()
        if asyncio.iscoroutine(r):
            await r
    cl = nucleo._lean

    def abrir(cab):
        s = SesionLean().abrir()
        return s, s.comando(cab, env=None).env

    filas = []
    print("  %-46s %-8s %-14s %s" % ("consulta", "A hoy", "B lazo·D0", ""))
    print("  " + "-" * 96)
    for q, g in cargar_casos():
        if not g:
            filas.append({"consulta": q, "A": None, "B": "sin_grabacion"})
            continue
        # A · el camino servido sobre el código que el modelo escribió
        a_ok, a_seg, _, _ = await reproduce(nucleo, g, CONFIGS["completo"])
        # B · el lazo sobre el enunciado de ESE código
        boceto = enunciado_con_sorry(g.get("codigo") or "")
        if not boceto:
            filas.append({"consulta": q, "A": a_ok, "B": "sin_enunciado"})
            continue
        # EL REPARADOR, COMO EN EL CAMINO SERVIDO. `core.py` repara nombres e
        # imports ANTES de compilar; la primera corrida de este banco no lo
        # hacía, y 10 de 20 enunciados «no elaboraban» —la raíz de 2, Cauchy—
        # porque `Irrational` y compañía viven fuera de la cabecera estrecha.
        # Era el banco, no el lazo: el mismo fallo que ya tuvo `replay.py`.
        try:
            boceto, _ = nombres.reparar_codigo(boceto)
        except Exception:                                      # noqa: BLE001
            pass
        m = Mediador(abrir, cl, [D0Cascada(SolverCascade(cl))], p,
                     registro=Registro(problema=q), existe=nombres.existe)
        r = await m.resolver(boceto)
        filas.append({"consulta": q, "A": bool(a_ok), "A_seg": round(a_seg, 1),
                      "B": r.veredicto, "cerradas": r.cerradas, "raices": r.raices,
                      "lean": r.llamadas_lean, "nodos": r.nodos,
                      "segundos": round(r.segundos, 1), "caminos": r.caminos,
                      "motivo": r.motivo[:200], "enunciado": boceto[-600:]})
        print("  %-46s %-8s %-14s %d llamadas · %.0f s"
              % (q[:46], "verifica" if a_ok else "no", r.veredicto,
                 r.llamadas_lean, r.segundos))
    return filas


def estimar(n_casos: int, llamadas_d3: int, modelo: str = "claude-sonnet-5"):
    """Lo que costaría la puerta con API, con la tarifa del contador."""
    from nucleo.llm.contador import precio_de
    pe, ps = precio_de(modelo)
    # lo servido: medido en la campaña del 2026-09-10 con sonnet-5, por caso,
    # y escalado por la tarifa del modelo pedido (mismos tokens, otro precio)
    c = json.load(io.open(CAMPANA, encoding="utf-8"))
    pe0, ps0 = precio_de(c.get("modelo") or "claude-sonnet-5")
    servido = c["gastado"] / max(1, len(c["filas"])) * (pe + ps) / (pe0 + ps0)
    # el lazo: un boceto (como una formalización) + D3 hasta su presupuesto
    boceto = 4000 * pe / 1e6 + 1500 * ps / 1e6
    d3 = llamadas_d3 * (2500 * pe / 1e6 + 400 * ps / 1e6)
    return servido, boceto + d3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--con-api", action="store_true")
    ap.add_argument("--ejecutar", action="store_true")
    ap.add_argument("--tope", type=float, default=0.0)
    ap.add_argument("--llamadas-d3", type=int, default=6)
    ap.add_argument("--modelo", default="claude-haiku-4-5",
                    help="el MISMO modelo para las dos ramas; si no, se mide el modelo y no el lazo")
    args = ap.parse_args()

    from nucleo.lazo.mediador import Presupuesto
    p = Presupuesto(llamadas=args.llamadas_d3)

    if not args.con_api:
        print("MODO SIN API · A = replay de la grabación · B = lazo sobre su enunciado\n")
        filas = asyncio.new_event_loop().run_until_complete(sin_api(p))
        va = {f["consulta"] for f in filas if f.get("A")}
        vb = {f["consulta"] for f in filas if f.get("B") == "verificado"}
        noel = [f for f in filas if f.get("B") == "no_elabora"]
        print("\n=== LAS DOS RAMAS, LA MISMA GRABACIÓN ===\n")
        print("  A · lo servido hoy, sobre el código del modelo   %2d de %d" % (len(va), len(filas)))
        print("  B · el lazo sólo con D0, sobre su enunciado      %2d de %d" % (len(vb), len(filas)))
        print("  las dos %d · sólo A %d · sólo B %d · A o B %d"
              % (len(va & vb), len(va - vb), len(vb - va), len(va | vb)))
        print("  enunciados que no elaboran en B: %d" % len(noel))
        for q in sorted(vb - va):
            print("     sólo B: %s" % q[:70])
        print("\n  NO ES LA PUERTA: B no tiene boceto ni modelo, y A no tiene las")
        print("  rondas de reparación, que gastan API. Dice cuánto cierra la")
        print("  búsqueda sola frente a lo que el modelo ya había escrito.")
        json.dump({"modo": "sin_api", "n": len(filas), "A": len(va), "B": len(vb),
                   "ambas": len(va & vb), "solo_A": len(va - vb), "solo_B": len(vb - va),
                   "no_elabora_B": len(noel), "filas": filas},
                  io.open(SALIDA % "sin_api", "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print("\n-> %s" % (SALIDA % "sin_api"))
        return 0

    n = len(cargar_casos())
    s_caso, l_caso = estimar(n, args.llamadas_d3, args.modelo)
    print("MODO CON API · estimación con la tarifa de %s\n" % args.modelo)
    print("  por caso: lo servido %.3f $ (medido) · el lazo %.3f $ (estimado, %d llamadas D3)"
          % (s_caso, l_caso, args.llamadas_d3))
    print("  las %d consultas, las dos ramas:  %.2f $" % (n, n * (s_caso + l_caso)))
    print("  el banco ampliado (~220), las dos: %.2f $" % (220 * (s_caso + l_caso)))
    if not args.ejecutar:
        print("\n  Sin --ejecutar no se gasta nada.")
        return 0
    print("\n  --ejecutar: aún no implementado a propósito; se construye cuando")
    print("  el presupuesto esté aprobado, para no gastar por un error de este guion.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
