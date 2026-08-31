# -*- coding: utf-8 -*-
"""
Ablacion: ¿el Nucleo Logico mejora la respuesta, o solo esta cableado?

Es la pregunta mas incomoda que se le puede hacer a este sistema, y hasta ahora
no se habia medido nunca. Lo que si estaba probado es OTRA cosa:

  · que el Nucleo es CORRECTO — 740 tests y 385 teoremas Lean dicen que los
    colimites, la congruencia, el orden y el funtor cociente son lo que dicen;
  · que FUNCIONA en caliente — arranca, decide, el grafo no crece.

Ninguna de las dos cosas implica que CONTRIBUYA. El grafo podria estar vacio y
las respuestas salir iguales, y hoy no tenemos con que descartarlo. El README
afirma que el Nucleo es «el cerebro»: o eso se mide, o hay que bajarlo de tono.

QUE SE APAGA, y donde entra cada cosa en `_math_via_lean`

  contexto   `_find_relevant_context` — skills, prerrequisitos y formulas ZFC
             que se inyectan en el prompt de formalizacion
  few-shot   `_build_few_shot_context` — ejemplos reales de LeanWorkbook
             elegidos por afinidad de simbolos con la consulta
  tactica    `domain_default_tactic` + la aprendida por el agente de categoria,
             que encabeza la cascada de solvers

QUE SE MIDE. No solo si verifica: tambien CUANTO CUESTA llegar. Una
configuracion que verifica igual pero necesita mas rondas de revision o mas
tiempo esta peor, y una que verifica igual con el mismo codigo byte a byte
significa que esa pieza no hizo nada.

    python -m scripts.ablacion_nucleo
    python -m scripts.ablacion_nucleo --casos 4
"""
import argparse
import asyncio
import hashlib
import io
import json
import os
import re
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SALIDA = "E:/Metamatematico/data/ablacion_nucleo.json"

#: Ocho casos representativos: dos de cada dificultad. La ablacion multiplica
#: por cuatro el coste, asi que la muestra es corta a proposito.
CASOS = [
    "¿Cuánto es 127 + 458?",
    "Demuestra que 2^10 = 1024",
    "Demuestra que (a+b)^2 = a^2 + 2ab + b^2",
    "Demuestra que (a-b)(a+b) = a^2 - b^2",
    "Demuestra que la raíz de 2 es irracional",
    "Demuestra que la suma de dos números pares es par",
    "Demuestra que en un grupo el elemento neutro es único",
    "Demuestra que P implica (Q implica P)",
]

CONFIGS = ["completo", "sin-contexto", "sin-fewshot", "sin-tactica"]

_INFRA = ("credit balance", "rate_limit", "overloaded", "not_found_error",
          "authentication_error", "permission_error", "APIConnectionError",
          "APITimeoutError", "InternalServerError")


def _es_infra(msg):
    return bool(msg) and any(p.lower() in msg.lower() for p in _INFRA)


def _cargar_clave():
    if os.environ.get("ANTHROPIC_API_KEY"):
        return True
    ruta = "E:/Metamatematico/.env"
    if not os.path.exists(ruta):
        return False
    m = re.search(r'ANTHROPIC_API_KEY\s*=\s*["\']?([^"\'\r\n]+)',
                  io.open(ruta, encoding="utf-8-sig").read())
    if not m:
        return False
    os.environ["ANTHROPIC_API_KEY"] = m.group(1).strip()
    return True


def _apagar(n, config):
    """Desactiva una pieza del Nucleo. Devuelve como restaurarla."""
    if config == "completo":
        return lambda: None

    if config == "sin-contexto":
        orig = n._find_relevant_context
        n._find_relevant_context = lambda *a, **k: {}
        return lambda: setattr(n, "_find_relevant_context", orig)

    if config == "sin-fewshot":
        orig = n._build_few_shot_context
        n._build_few_shot_context = lambda *a, **k: ""
        return lambda: setattr(n, "_build_few_shot_context", orig)

    if config == "sin-tactica":
        # La tactica de dominio llega por dos vias: el default por area y la
        # aprendida por el agente de categoria. Se cierran las dos.
        from nucleo.multi_agent import colimit_agents
        orig_def = colimit_agents.domain_default_tactic
        colimit_agents.domain_default_tactic = lambda *a, **k: None
        orq = n._multi_agent_orchestrator
        orig_lrn = None
        if orq is not None and getattr(orq, "mes_bridge", None) is not None:
            orig_lrn = orq.mes_bridge.query_best_tactic
            orq.mes_bridge.query_best_tactic = lambda *a, **k: None

        def restaurar():
            colimit_agents.domain_default_tactic = orig_def
            if orig_lrn is not None:
                orq.mes_bridge.query_best_tactic = orig_lrn
        return restaurar

    raise ValueError(config)


async def main(n_casos):
    if not _cargar_clave():
        print("No hay ANTHROPIC_API_KEY ni .env.")
        return 1

    import logging
    logging.basicConfig(level=logging.CRITICAL)
    from nucleo.core import Nucleo
    from nucleo.config import NucleoConfig

    casos = CASOS[:n_casos]
    n = Nucleo(NucleoConfig())
    await n.initialize()

    orig_lean = n._lean.check_code
    estado = {"codigo": None, "llamadas": 0}

    async def espia(code, **kw):
        estado["codigo"] = code
        estado["llamadas"] += 1
        return await orig_lean(code, **kw)
    n._lean.check_code = espia

    filas = []
    print("=== ABLACIÓN DEL NÚCLEO · %d casos × %d configuraciones ===\n"
          % (len(casos), len(CONFIGS)))

    corto = False
    for q in casos:
        print("─" * 74)
        print(q)
        for config in CONFIGS:
            restaurar = _apagar(n, config)
            estado.update(codigo=None, llamadas=0)
            t0 = time.time()
            try:
                r = await asyncio.wait_for(n.process(q), timeout=900)
                err = None
            except Exception as e:
                r, err = None, "%s: %s" % (type(e).__name__, e)
            finally:
                restaurar()

            dt = time.time() - t0
            md = (getattr(r, "metadata", {}) or {}) if r else {}
            lean = str(getattr(getattr(r, "lean_result", None), "status", "")) if r else ""
            codigo = estado["codigo"] or ""
            fila = dict(
                pregunta=q, config=config,
                verifica=("SUCCESS" in lean),
                lean=lean, rondas=md.get("rondas_revision"),
                llamadas_lean=estado["llamadas"], seg=round(dt, 1),
                huella=hashlib.sha1(codigo.encode()).hexdigest()[:10] if codigo else "",
                nchars=len(codigo), error=err,
            )
            filas.append(fila)
            print("   %-13s %-4s  %5.0fs  lean×%d  rondas=%s  %s"
                  % (config, "ok" if fila["verifica"] else "no",
                     dt, fila["llamadas_lean"], fila["rondas"], fila["huella"]))
            if _es_infra(err):
                print("\n   FALLO DE API — se detiene: %s" % err[:90])
                corto = True
                break
        if corto:
            break

    # ── comparacion ──────────────────────────────────────────────────────
    print("\n" + "=" * 74)
    medidos = [f for f in filas if not _es_infra(f["error"])]
    por_q = {}
    for f in medidos:
        por_q.setdefault(f["pregunta"], {})[f["config"]] = f
    completas = {q: d for q, d in por_q.items() if len(d) == len(CONFIGS)}

    print("  casos con las %d configuraciones medidas: %d de %d\n"
          % (len(CONFIGS), len(completas), len(casos)))
    if not completas:
        print("  Sin casos completos NO hay conclusion: la ablacion compara "
              "columnas,\n  y una columna a medias no se puede comparar.")
    else:
        print("  %-13s %8s %8s %8s %10s" %
              ("config", "verifica", "seg", "lean×", "≠ código"))
        base = {q: d["completo"] for q, d in completas.items()}
        for config in CONFIGS:
            sub = [d[config] for d in completas.values()]
            distinto = sum(
                1 for q, d in completas.items()
                if d[config]["huella"] != base[q]["huella"])
            print("  %-13s %5d/%-2d %8.0f %8.1f %10s" % (
                config, sum(f["verifica"] for f in sub), len(sub),
                sum(f["seg"] for f in sub) / len(sub),
                sum(f["llamadas_lean"] for f in sub) / len(sub),
                "—" if config == "completo" else "%d/%d" % (distinto, len(sub))))

        print("\n  LECTURA")
        for config in CONFIGS[1:]:
            sub = [d[config] for d in completas.values()]
            b = [d["completo"] for d in completas.values()]
            dv = sum(f["verifica"] for f in sub) - sum(f["verifica"] for f in b)
            ig = sum(1 for q, d in completas.items()
                     if d[config]["huella"] == base[q]["huella"])
            if dv == 0 and ig == len(sub):
                print("    %-13s NO APORTA NADA medible: mismo código, mismo "
                      "veredicto." % config)
            elif dv == 0:
                print("    %-13s mismo veredicto, pero cambia el código en %d/%d "
                      "casos." % (config, len(sub) - ig, len(sub)))
            elif dv < 0:
                print("    %-13s APORTA: apagarlo pierde %d verificación(es)."
                      % (config, -dv))
            else:
                print("    %-13s apagarlo MEJORA en %d: la pieza estorba."
                      % (config, dv))

    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    io.open(SALIDA, "w", encoding="utf-8").write(
        json.dumps(filas, ensure_ascii=False, indent=2))
    print("\n  detalle -> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--casos", type=int, default=len(CASOS))
    a = ap.parse_args()
    sys.exit(asyncio.run(main(a.casos)))
