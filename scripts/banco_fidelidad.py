# -*- coding: utf-8 -*-
"""
Banco de fidelidad: ¿el teorema que Lean verifica es el que se preguntó?

Es la promesa central del sistema, y hasta ahora solo se habia comprobado sobre
tres consultas — que fue justo como aparecio el defecto del detector de
tautologias: el sistema respondia VERIFICADO a teoremas que nadie habia
preguntado, correctos como matematica y falsos como respuesta.

QUE MIDE, y por que hacen falta las tres cosas

  1. VERIFICACION — ¿que dijo Lean? Es lo unico que el sistema ya reportaba.
  2. FIDELIDAD    — ¿el enunciado formalizado es el de la pregunta? Un juez
                    LLM independiente lo dictamina viendo la pregunta y el
                    codigo, SIN saber que veredicto dio Lean, para que el sello
                    de verificado no lo contamine.
  3. HONESTIDAD   — para los enunciados FALSOS a proposito: Lean debe
                    rechazarlos y la respuesta debe abrir diciendolo. Un
                    sistema que solo acierta con lo cierto no sirve de nada.

Un caso solo cuenta como bueno si las tres salen bien. Verificar fielmente algo
falso es tan malo como verificar infielmente algo cierto.

    python -m scripts.banco_fidelidad            # los 24 casos
    python -m scripts.banco_fidelidad --rapido   # solo 8, para iterar
"""
import argparse
import asyncio
import io
import json
import os
import re
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SALIDA = "E:/Metamatematico/data/banco_fidelidad.json"

#: (area, pregunta, espera)
#:   "verifica"  — cierto y formalizable: Lean deberia aceptarlo
#:   "rechaza"   — FALSO a proposito: Lean debe rechazarlo y la respuesta avisar
#:   "no-math"   — no deberia entrar al pipeline de Lean
CASOS = [
    # ── aritmetica y algebra elemental ───────────────────────────────────
    ("aritmetica", "¿Cuánto es 127 + 458?", "verifica"),
    ("aritmetica", "¿Cuánto es 17 por 23?", "verifica"),
    ("aritmetica", "Demuestra que 2^10 = 1024", "verifica"),
    ("algebra",    "Demuestra que (a+b)^2 = a^2 + 2ab + b^2", "verifica"),
    ("algebra",    "Demuestra que (a-b)(a+b) = a^2 - b^2", "verifica"),
    ("algebra",    "Si x + 3 = 10, ¿cuánto vale x?", "verifica"),

    # ── teoremas clasicos ────────────────────────────────────────────────
    ("numeros",   "Demuestra que la raíz de 2 es irracional", "verifica"),
    ("numeros",   "Demuestra que hay infinitos números primos", "verifica"),
    ("numeros",   "Demuestra que la suma de dos números pares es par", "verifica"),
    ("numeros",   "Demuestra que n^2 es par si y solo si n es par", "verifica"),
    ("analisis",  "Demuestra que la suma de 1/2^n desde n=1 hasta infinito es 1", "verifica"),
    ("conjuntos", "Demuestra que la unión de conjuntos es conmutativa", "verifica"),

    # ── mas abstractos ───────────────────────────────────────────────────
    ("algebra-abs", "Demuestra que en un grupo el elemento neutro es único", "verifica"),
    ("algebra-abs", "Demuestra que todo subgrupo de un grupo cíclico es cíclico", "verifica"),
    ("topologia",   "Demuestra que la unión de dos conjuntos abiertos es abierta", "verifica"),
    ("logica",      "Demuestra que P implica (Q implica P)", "verifica"),

    # ── FALSOS a proposito: el sistema debe rechazarlos ──────────────────
    ("falso", "Demuestra que 2 + 2 = 5", "rechaza"),
    ("falso", "Demuestra que todo número primo es impar", "rechaza"),
    ("falso", "Demuestra que la raíz de 4 es irracional", "rechaza"),
    ("falso", "Demuestra que para todo n, n^2 > n", "rechaza"),

    # ── controles: no son matematicas ────────────────────────────────────
    ("no-math", "Hola, ¿qué tal estás?", "no-math"),
    ("no-math", "¿Quién fue Alexander Grothendieck?", "no-math"),
    ("no-math", "Cuéntame un chiste", "no-math"),
    ("no-math", "¿Qué tiempo hace hoy en Ciudad de México?", "no-math"),
]

JUEZ = """Eres un revisor de formalizaciones matemáticas. Se te da una PREGUNTA en \
lenguaje natural y un CÓDIGO Lean 4 que pretende formalizarla.

Tu única tarea: decir si el teorema del código es LA MISMA afirmación que la \
pregunta pide, o si formaliza otra cosa.

Ejemplos de INFIEL:
- la pregunta es «¿cuánto es 127 + 458?» y el teorema habla de vectores ortogonales
- la pregunta pide (a+b)²=a²+2ab+b² y el teorema lo enuncia en espacios normados
- el teorema toma la conclusión como hipótesis (tautología)
- el teorema demuestra un caso particular cuando se pedía el general, o al revés

Ejemplos de FIEL:
- se pide 127+458 y el teorema dice `127 + 458 = 585`
- se pide que √2 es irracional y el teorema dice `Irrational (Real.sqrt 2)`
- el teorema generaliza de forma natural y evidente (ℕ en vez de un número concreto) \
manteniendo exactamente lo que se preguntó

Responde SOLO con un JSON, sin nada más:
{"fiel": true|false, "motivo": "una frase"}"""


def _cargar_clave():
    ruta = "E:/Metamatematico/.env"
    if os.environ.get("ANTHROPIC_API_KEY"):
        return True
    if not os.path.exists(ruta):
        return False
    m = re.search(r'ANTHROPIC_API_KEY\s*=\s*["\']?([^"\'\r\n]+)',
                  io.open(ruta, encoding="utf-8-sig").read())
    if not m:
        return False
    os.environ["ANTHROPIC_API_KEY"] = m.group(1).strip()
    return True


def _censura(t):
    return re.sub(r"sk-ant-[A-Za-z0-9_\-]+", "sk-ant-«oculta»", t or "")


#: Fallos de INFRAESTRUCTURA, no del sistema.
#:
#: Se separan porque confundirlos es justo la clase de medicion deshonesta
#: contra la que este repo tiene una suite entera. La primera pasada de 24
#: casos dio 7/24 y esa cifra no medía la fidelidad del sistema: medía en que
#: caso se acabo el saldo de la API. Presentarla como nota habria sido mentir
#: con una tabla.
_INFRA = ("credit balance", "rate_limit", "overloaded", "not_found_error",
          "authentication_error", "permission_error", "APIConnectionError",
          "APITimeoutError", "InternalServerError")


def _es_infra(msg):
    return bool(msg) and any(p.lower() in msg.lower() for p in _INFRA)


async def _juzgar(llm, pregunta, codigo):
    """El juez ve la pregunta y el código. NO ve el veredicto de Lean."""
    if not codigo:
        return None, "sin código que juzgar"
    r = await llm.generate(
        f"PREGUNTA: {pregunta}\n\nCÓDIGO Lean 4:\n```lean\n{codigo}\n```",
        system=JUEZ,
    )
    m = re.search(r"\{.*\}", r.content, re.S)
    if not m:
        return None, "el juez no devolvió JSON"
    try:
        d = json.loads(m.group(0))
        return bool(d.get("fiel")), str(d.get("motivo", ""))[:160]
    except Exception:
        return None, "JSON del juez ilegible"


async def main(rapido=False):
    if not _cargar_clave():
        print("No hay ANTHROPIC_API_KEY ni .env — el banco necesita el LLM.")
        return 1

    import logging
    logging.basicConfig(level=logging.CRITICAL)
    from nucleo.core import Nucleo
    from nucleo.config import NucleoConfig

    casos = CASOS[::3] if rapido else CASOS
    n = Nucleo(NucleoConfig())
    await n.initialize()

    # espia: nos quedamos con el ULTIMO codigo que se mandó a Lean
    orig_lean = n._lean.check_code
    ultimo = {"codigo": None}

    async def espia(code, **kw):
        ultimo["codigo"] = code
        return await orig_lean(code, **kw)
    n._lean.check_code = espia

    filas = []
    print("=== BANCO DE FIDELIDAD · %d casos ===\n" % len(casos))
    for i, (area, q, espera) in enumerate(casos, 1):
        ultimo["codigo"] = None
        t0 = time.time()
        try:
            r = await asyncio.wait_for(n.process(q), timeout=900)
            err = None
        except Exception as e:
            r, err = None, "%s: %s" % (type(e).__name__, _censura(str(e)))

        dt = time.time() - t0
        codigo = ultimo["codigo"]
        texto = _censura(getattr(r, "content", "") or "") if r else ""
        lean = str(getattr(getattr(r, "lean_result", None), "status", "")) if r else ""
        verifica = "SUCCESS" in lean
        aviso = "NO verificó" in texto or "no verificó" in texto

        fiel, motivo = (None, "")
        if codigo and espera != "no-math":
            try:
                fiel, motivo = await _juzgar(n._llm, q, codigo)
            except Exception as e:
                motivo = "juez fallo: %s" % type(e).__name__

        if _es_infra(err) or _es_infra(motivo):
            # ok=None: NO MEDIDO. No cuenta ni a favor ni en contra.
            ok = None
            detalle = "NO MEDIDO — falló la API: " + (err or motivo)[:80]
        elif espera == "no-math":
            ok = codigo is None
            detalle = "no tocó Lean" if ok else "entró al pipeline sin ser matemática"
        elif espera == "rechaza":
            ok = (not verifica) and aviso
            detalle = ("rechazado y avisado" if ok else
                       "VERIFICÓ UN ENUNCIADO FALSO" if verifica else
                       "no verificó pero no avisa")
        else:
            ok = verifica and fiel is True
            detalle = ("verificado y fiel" if ok else
                       "verificado pero INFIEL: " + motivo if verifica and fiel is False else
                       "no verificó" if not verifica else
                       "fidelidad indeterminada: " + motivo)

        filas.append(dict(area=area, pregunta=q, espera=espera, ok=ok,
                          lean=lean, fiel=fiel, motivo=motivo, seg=round(dt, 1),
                          codigo=(codigo or "")[:400], error=err))
        print("%2d/%d %-11s %-9s %5.0fs  %s" %
              (i, len(casos), area,
               "ok" if ok else ("NO MEDIDO" if ok is None else "FALLA"),
               dt, q[:48]))
        print("        %s" % detalle)

        # Sin saldo no tiene sentido seguir: cada caso restante seria otro
        # NO MEDIDO y otra ejecucion de Lean tirada.
        if "credit balance" in (err or "").lower():
            print("\n  SE ACABÓ EL SALDO DE LA API — se detiene el banco.")
            print("  Los %d casos restantes quedan SIN MEDIR." % (len(casos) - i))
            break

    print("\n" + "=" * 70)
    medidos = [f for f in filas if f["ok"] is not None]
    sin_medir = len(casos) - len(medidos)
    for grupo in ("verifica", "rechaza", "no-math"):
        g = [f for f in medidos if f["espera"] == grupo]
        if g:
            print("  %-9s  %d/%d" % (grupo, sum(f["ok"] for f in g), len(g)))
    infieles = [f for f in medidos if f["fiel"] is False]
    print("\n  VERIFICADOS PERO INFIELES: %d" % len(infieles))
    for f in infieles:
        print("     %s\n        %s" % (f["pregunta"][:56], f["motivo"]))
    if medidos:
        print("\n  TOTAL %d/%d MEDIDOS"
              % (sum(f["ok"] for f in medidos), len(medidos)))
    if sin_medir:
        print("\n  %d de %d casos SIN MEDIR — fallo de la API, no del sistema."
              % (sin_medir, len(casos)))
        print("  Mientras queden sin medir, NO hay nota del sistema: una cifra "
              "parcial\n  presentada como total seria una medicion deshonesta.")

    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    io.open(SALIDA, "w", encoding="utf-8").write(
        json.dumps(filas, ensure_ascii=False, indent=2))
    print("\n  detalle -> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--rapido", action="store_true")
    a = ap.parse_args()
    sys.exit(asyncio.run(main(a.rapido)))
