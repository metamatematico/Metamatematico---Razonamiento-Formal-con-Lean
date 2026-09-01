# -*- coding: utf-8 -*-
"""
Los que no verificaron: ¿faltaba el lema, o faltaba encontrarlo?

Son dos problemas distintos y solo UNO lo arregla un grafo de conocimiento:

  a) el lema YA EXISTE en Mathlib y el LLM no dio con el       -> recuperable
  b) el lema no existe con ese nombre y habia que demostrarlo  -> no lo arregla
     ninguna vecindad conceptual

La distincion importa porque acaba de morir la hipotesis de los imports:
`import Mathlib` es la norma, tarda ~35 s y verifica al primer intento, asi que
no hay import que afinar. Antes de proponer otra via conviene saber cual de los
dos problemas es el que hay delante.

METODO, y por que no basta con preguntarle al modelo. Se le pide que nombre el
lema de Mathlib, y despues se COMPRUEBA con Lean: `#check <nombre>`. Si Lean lo
acepta, el lema existe de verdad; si no, el modelo se lo invento — que es
exactamente la clase de respuesta que este sistema existe para no dar.

    python -m scripts.diagnostico_fallos
"""
import asyncio
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

#: Los tres que no verificaron en el banco de fidelidad.
FALLOS = [
    "Demuestra que la suma de 1/2^n desde n=1 hasta infinito es 1",
    "Demuestra que todo subgrupo de un grupo cíclico es cíclico",
    "Demuestra que la unión de dos conjuntos abiertos es abierta",
]

PREGUNTA = """¿Existe en Mathlib (Lean 4) un lema o teorema que demuestre esto?

{q}

Responde SOLO con los nombres completos y cualificados, separados por comas, de
los lemas de Mathlib que lo resuelven o casi. Sin explicación, sin código, sin
backticks. Si crees que Mathlib no lo tiene, responde exactamente: NO EXISTE"""


#: Fallos de INFRAESTRUCTURA. El banco y la ablacion ya los separaban; este
#: script se escribio sin esa red y reventaba con un traceback en vez de decir
#: "sin saldo, no medido". Un guion de diagnostico que confunde las dos cosas
#: es peor que no tenerlo: invita a leer un fallo de facturacion como un
#: resultado sobre el sistema.
#: TERMINALES: no tiene sentido reintentar, la tanda se corta.
_TERMINAL = ("credit balance", "authentication_error", "permission_error",
             "not_found_error")

#: TRANSITORIOS: el servicio esta saturado o la red fallo. Se reintenta.
#: Confundirlos con los anteriores hacia abandonar una tanda por un 529, y
#: encima anunciarlo como "sin saldo" — un diagnostico falso sobre la causa.
_TRANSITORIO = ("overloaded", "rate_limit", "APIConnectionError",
                "APITimeoutError", "InternalServerError", "529", "503")


def _es_terminal(e):
    return any(p.lower() in str(e).lower() for p in _TERMINAL)


def _es_transitorio(e):
    return any(p.lower() in str(e).lower() for p in _TRANSITORIO)


async def _con_reintento(fn, intentos=3, espera=8):
    """Llama a `fn`, reintentando los fallos transitorios."""
    import asyncio as _a
    ultimo = None
    for i in range(intentos):
        try:
            return await fn(), None
        except Exception as e:
            ultimo = e
            if _es_terminal(e) or not _es_transitorio(e):
                return None, e
            if i < intentos - 1:
                print("   servicio saturado, reintento %d de %d en %ds..."
                      % (i + 1, intentos - 1, espera))
                await _a.sleep(espera)
    return None, ultimo


def _clave():
    if os.environ.get("ANTHROPIC_API_KEY"):
        return True
    p = "E:/Metamatematico/.env"
    if not os.path.exists(p):
        return False
    m = re.search(r'ANTHROPIC_API_KEY\s*=\s*["\']?([^"\'\r\n]+)',
                  io.open(p, encoding="utf-8-sig").read())
    if not m:
        return False
    os.environ["ANTHROPIC_API_KEY"] = m.group(1).strip()
    return True


async def main():
    if not _clave():
        print("sin ANTHROPIC_API_KEY")
        return 1
    import logging
    logging.basicConfig(level=logging.CRITICAL)
    from nucleo.core import Nucleo
    from nucleo.config import NucleoConfig
    from nucleo.llm.contador import Contador

    n = Nucleo(NucleoConfig())
    await n.initialize()

    print("=== ¿FALTABA EL LEMA, O FALTABA ENCONTRARLO? ===\n")
    recuperables = 0
    sin_medir = False
    for q in FALLOS:
        print("─" * 72)
        print(q)
        r, err = await _con_reintento(
            lambda: n._llm.generate(PREGUNTA.format(q=q), sin_historial=True))
        if err is not None:
            motivo = ("saldo agotado" if _es_terminal(err)
                      else "servicio saturado tras varios reintentos")
            print("   NO MEDIDO — %s: %s" % (motivo, str(err)[:70]))
            print("\n  Los %d casos restantes tampoco se miden."
                  % (len(FALLOS) - FALLOS.index(q) - 1))
            sin_medir = True
            break
        crudo = (r.content or "").strip()
        if "NO EXISTE" in crudo.upper():
            print("   el modelo dice que Mathlib NO lo tiene")
            print("   -> un grafo no lo arregla: hay que demostrarlo")
            continue

        nombres = [x.strip().strip("`.,")
                   for x in re.split(r"[,\n]", crudo) if x.strip()][:4]
        print("   el modelo propone:", ", ".join(nombres) or "(nada)")

        # AQUI esta el punto: se COMPRUEBA, no se cree.
        codigo = "import Mathlib\n" + "\n".join("#check @" + x for x in nombres)
        res = await n._lean.check_code(codigo)
        ok = str(getattr(res, "status", "")).endswith("SUCCESS")
        print("   Lean dice:", "EXISTEN todos" if ok else "alguno NO existe")
        if not ok:
            # uno a uno, para separar los reales de los inventados
            reales = []
            for x in nombres:
                r1 = await n._lean.check_code("import Mathlib\n#check @" + x)
                if str(getattr(r1, "status", "")).endswith("SUCCESS"):
                    reales.append(x)
            print("   reales:", ", ".join(reales) if reales else "NINGUNO")
            print("   inventados:", ", ".join(x for x in nombres
                                              if x not in reales) or "—")
            ok = bool(reales)
        if ok:
            recuperables += 1
            print("   -> RECUPERABLE: el lema estaba en Mathlib y no se uso")

    print("\n" + "=" * 72)
    if sin_medir:
        print("  SIN CONCLUSION: la tanda no se completo.")
        print("  Lo medido hasta el corte: %d recuperables." % recuperables)
        print("\n  " + Contador.resumen().splitlines()[-1])
        return 0
    print("  recuperables por vecindad de lemas: %d de %d"
          % (recuperables, len(FALLOS)))
    if recuperables == 0:
        print("  El grafo tampoco ayuda por esta via: lo que falta son pruebas,")
        print("  no punteros. Conviene dejar de buscarle sitio en el pipeline.")
    print("\n  " + Contador.resumen().splitlines()[-1])
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
