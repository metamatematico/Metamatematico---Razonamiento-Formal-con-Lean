# -*- coding: utf-8 -*-
"""El bucle de prueba que no cuesta dinero.

QUE HACE. Toma formalizaciones que el LLM ya escribió —grabadas una vez— y las
vuelve a pasar por TODO lo que el sistema hace después: elección de imports,
reparación, cascada de tácticas, premisas. Lean dicta el veredicto. Sin API.

POR QUE HACIA FALTA. Cada pregunta sobre este sistema costaba dinero, y por eso
la más importante —¿el núcleo mejora la respuesta?— llevaba días sin contestar.
Todo lo demás se midió contra sustitutos: Mathlib, ProofNet, LeanWorkbook.
Buenos sustitutos, pero sustitutos.

Con esto, una medición de $1,90 pasa a correr cuantas veces haga falta, y
cualquier cambio en `solver_cascade.py`, `premisas.py` o el mapa de módulos se
puede evaluar antes de subirlo.

LA FRONTERA ESTA DONDE TIENE QUE ESTAR. Se graba el código del LLM ANTES de
normalizar: todo lo que viene después es del sistema y es reejecutable. Lo que
NO puede medir es si otro prompt habría hecho al modelo escribir mejor — eso
sigue necesitando API. Pero grabando una vez con cada configuración, esa
comparación también queda hecha para siempre.

QUE SE COMPARA. Cada grabación se reproduce con varias configuraciones del
sistema, y se cuenta cuántas verifican y cuánto tardan:

    completo        el sistema tal como está
    sin-imports     sin los módulos que propone el grafo
    sin-premisas    sin las tácticas con lemas citados
    desnudo         ni imports del grafo ni premisas

Las diferencias entre columnas son exactamente la contribución de cada pieza,
medida sobre código real y con Lean como juez.

    python scripts/replay.py                    # todas las grabaciones
    python scripts/replay.py --configs completo,desnudo
    python scripts/replay.py --sembrar          # importa las que ya había
"""
import argparse
import asyncio
import collections
import io
import json
import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SALIDA = "E:/Metamatematico/data/replay.json"

#: Qué apaga cada configuración. `completo` no apaga nada.
CONFIGS = {
    "completo":     {"imports": True,  "premisas": True},
    "sin-imports":  {"imports": False, "premisas": True},
    "sin-premisas": {"imports": True,  "premisas": False},
    "desnudo":      {"imports": False, "premisas": False},
}


def sembrar():
    """Importa las formalizaciones que ya estaban en otros bancos.

    El banco de fidelidad guardaba el código Lean de cada caso. Son pocas —siete
    — pero son reales y ya pagadas, y sirven para arrancar sin gastar nada.
    """
    from nucleo.grabacion import _ruta
    fuente = "E:/Metamatematico/data/banco_fidelidad.json"
    if not os.path.exists(fuente):
        print("  no hay banco de fidelidad del que sembrar")
        return 0
    filas = json.load(io.open(fuente, encoding="utf-8"))
    ruta = _ruta()
    ya = set()
    if os.path.exists(ruta):
        for l in io.open(ruta, encoding="utf-8"):
            try:
                ya.add(json.loads(l).get("consulta", ""))
            except Exception:
                pass
    n = 0
    with io.open(ruta, "a", encoding="utf-8") as fh:
        for r in filas:
            cod = (r or {}).get("codigo") or ""
            q = (r or {}).get("pregunta") or ""
            if not cod.strip() or q in ya:
                continue
            fh.write(json.dumps({
                "ts": "sembrado",
                "config": "completo",
                "consulta": q,
                "codigo": cod,
                "area": (r or {}).get("area", ""),
                "skills": [],
                "veredicto": (r or {}).get("lean", ""),
                "modelo": "grabado-en-banco_fidelidad",
                "origen": "banco_fidelidad",
            }, ensure_ascii=False) + "\n")
            n += 1
    print("  sembradas %d formalizaciones desde el banco de fidelidad" % n)
    return n


async def reproduce(nucleo, fila, cfg):
    """Pasa una grabación por el sistema actual. Devuelve (verifica, segundos)."""
    from nucleo.core import Nucleo

    codigo = fila["codigo"]
    area = fila.get("area") or ""
    t0 = time.time()

    # PASO 3 — los módulos que el grafo propone
    try:
        if cfg["imports"]:
            skills = fila.get("skills") or Nucleo._match_skills_to_query(
                nucleo, fila["consulta"], nucleo._graph)
            mods = Nucleo._modulos_mathlib(nucleo, {"relevant_skills": skills})
        else:
            mods = []
        nucleo._lean.sugerir_imports(mods)
    except Exception:
        mods = []

    result = await nucleo._lean.check_code(codigo)
    verifica = bool(getattr(result, "is_success", False))

    # PASO 6 — la cascada, si queda un `sorry`
    if not verifica and "sorry" in codigo:
        try:
            from nucleo.multi_agent.colimit_agents import domain_tactic_order
            r2 = await nucleo._fill_sorries(
                codigo, result,
                domain_order=domain_tactic_order(area),
                area_premisas=(area if cfg["premisas"] else ""))
            if r2 and getattr(r2[1] if isinstance(r2, tuple) else r2,
                              "is_success", False):
                verifica = True
        except Exception:
            pass

    return verifica, time.time() - t0, len(mods)


async def main(configs, limite):
    from nucleo.core import Nucleo, NucleoConfig
    from nucleo.grabacion import cargar

    filas = cargar()
    if not filas:
        print("No hay grabaciones. Dos formas de conseguirlas:\n"
              "   python scripts/replay.py --sembrar        importa las que ya había\n"
              "   METAMAT_GRABAR=1 python -m nucleo chat    graba mientras usas el sistema")
        return 1
    if limite:
        filas = filas[:limite]
    print("grabaciones: %d" % len(filas))
    print("configuraciones: %s\n" % ", ".join(configs))

    # El constructor no monta los clientes: eso lo hace `initialize()`. Sin
    # llamarlo, `_lean` es None y el reproductor peta en el primer caso.
    nucleo = Nucleo(NucleoConfig())
    ini = getattr(nucleo, "initialize", None)
    if ini is not None:
        r = ini()
        if asyncio.iscoroutine(r):
            await r
    if getattr(nucleo, "_lean", None) is None:
        print("ERROR: el cliente de Lean no arrancó. Sin juez esto no mide "
              "nada,\n       así que se detiene en vez de devolver ceros.")
        return 1

    res = collections.defaultdict(lambda: {"ok": 0, "n": 0, "seg": 0.0})
    detalle = []
    for i, f in enumerate(filas, 1):
        fila = {"consulta": f["consulta"][:60]}
        for c in configs:
            ok, seg, nm = await reproduce(nucleo, f, CONFIGS[c])
            r = res[c]
            r["ok"] += 1 if ok else 0
            r["n"] += 1
            r["seg"] += seg
            fila[c] = {"ok": ok, "seg": round(seg, 1), "mods": nm}
        detalle.append(fila)
        print("  %2d/%d  %-46s %s" % (
            i, len(filas), f["consulta"][:44],
            "  ".join("%s:%s" % (c, "ok" if fila[c]["ok"] else "--")
                      for c in configs)))

    print("\n" + "=" * 64)
    print("  %-14s %10s %10s" % ("", "verifica", "segundos"))
    for c in configs:
        r = res[c]
        print("  %-14s %9.1f %% %9.1f"
              % (c, 100.0 * r["ok"] / max(1, r["n"]), r["seg"] / max(1, r["n"])))

    if "completo" in configs and len(configs) > 1:
        base = res["completo"]["ok"]
        print("\n  LECTURA — la diferencia es la contribución de cada pieza")
        for c in configs:
            if c == "completo":
                continue
            d = base - res[c]["ok"]
            print("     %-14s %+d casos %s" % (
                c, d,
                "· la pieza aporta" if d > 0 else
                ("· la pieza no aporta" if d == 0 else "· la pieza ESTORBA")))
        if all(res[c]["ok"] == base for c in configs):
            print("\n     ninguna diferencia: con esta muestra no se distingue nada.")
            print("     n=%d — hace falta mas grabaciones, o mas dificiles."
                  % len(filas))

    json.dump({"n": len(filas), "configs": configs,
               "resumen": {c: dict(res[c]) for c in configs},
               "detalle": detalle},
              io.open(SALIDA, "w", encoding="utf-8"), indent=1,
              ensure_ascii=False)
    print("\n-> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--configs", default="completo,sin-imports,sin-premisas,desnudo")
    ap.add_argument("--limite", type=int, default=0)
    ap.add_argument("--sembrar", action="store_true",
                    help="importa las formalizaciones ya guardadas en otros bancos")
    a = ap.parse_args()
    if a.sembrar:
        sembrar()
        sys.exit(0)
    cs = [c.strip() for c in a.configs.split(",") if c.strip()]
    malas = [c for c in cs if c not in CONFIGS]
    if malas:
        print("configuraciones desconocidas: %s" % ", ".join(malas))
        print("disponibles: %s" % ", ".join(CONFIGS))
        sys.exit(2)
    sys.exit(asyncio.run(main(cs, a.limite)))
