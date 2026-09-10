# -*- coding: utf-8 -*-
"""EL SUELO: el mismo modelo, sin nada del sistema. ¿Cuánto hace solo?

LA PREGUNTA QUE HACE FALTA PARA LEER TODAS LAS DEMÁS
----------------------------------------------------
La campaña midió el sistema con y sin el vocabulario del grafo: 12 de 20
contra 11 de 20. Ruido. Pero la rama «sin-vocabulario» NO es un modelo
desnudo — conserva los imports, la selección de premisas, la cascada de
tácticas, la revisión de sintaxis, LAS RONDAS DE REPARACIÓN, los ejemplos
few-shot de miniF2F, la cualificación de nombres contra 217 419
identificadores y el protocolo de refutación. Es el sistema menos una pieza.

Así que sabemos que el grafo no explica el 60 %, y NO sabemos qué lo explica.
Si el modelo solo hace 11 de 20, el aparato entero sobra. Si hace 3, el
aparato es el producto.

CÓMO SE MIDE, Y POR QUÉ ASÍ
---------------------------
No apagando piezas una a una —son ocho y cada interruptor es una ocasión de
equivocarse— sino SALTÁNDOSE EL SISTEMA: una llamada al modelo, se extrae el
bloque de código, Lean lo verifica UNA vez. Sin reintentos, sin reparación,
sin cascada, sin premisas, sin grafo.

EL PROMPT ES JUSTO, NO MÍNIMO. Se le pide lo mismo que el sistema le pide —un
único bloque Lean 4 autocontenido, con sus imports— porque un suelo con un
prompt mutilado no mide el suelo: mide el prompt. Lo que NO lleva son los
ejemplos, el vocabulario, las advertencias acumuladas y las segundas
oportunidades. Eso es lo que el sistema añade.

MISMAS 20 CONSULTAS, mismo modelo, mismo verificador. La única diferencia es
el sistema.

    python -m scripts.linea_base_llm                 # en seco
    python -m scripts.linea_base_llm --ejecutar
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

SALIDA = "E:/Metamatematico/data/linea_base_llm.json"

#: Una llamada por caso, y el prompt es corto: sin few-shot no hay bloque de
#: ejemplos. Medido sobre las tandas: ~300 de entrada y ~600 de salida.
TOKENS_POR_CASO = (300, 600)

SISTEMA = (
    "You are a Lean 4 expert working with Mathlib. "
    "You formalize mathematical statements and prove them."
)

PLANTILLA = (
    "Formalize and prove the following statement in Lean 4 with Mathlib.\n\n"
    "STATEMENT: %s\n\n"
    "Write ONLY ONE Lean 4 code block. Nothing else.\n"
    "The code must be self-contained, with the imports it needs.\n"
    "Write the claim as a `theorem` or `lemma`.\n"
    "If you do not know the full proof, use `sorry` as a placeholder."
)


def _cargar_clave() -> bool:
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


async def main(ejecutar: bool, modelo: str, tope: float) -> int:
    from scripts.campana_de_grabacion import CASOS
    from nucleo.llm.contador import precio_de

    casos = CASOS[:20]
    pe, ps = precio_de(modelo)
    ent, sal = TOKENS_POR_CASO
    por_caso = ent / 1e6 * pe + sal / 1e6 * ps
    print("=== LÍNEA BASE: EL MODELO SOLO ===")
    print("  casos          : %d  (los mismos de la campaña)" % len(casos))
    print("  modelo         : %s" % modelo)
    print("  COSTE ESTIMADO : $%.3f  ($%.4f por caso)"
          % (len(casos) * por_caso, por_caso))
    print("  TOPE DURO      : $%.2f" % tope)
    if not ejecutar:
        print("\n  PASADA EN SECO. Para gastar: --ejecutar")
        return 0
    if not _cargar_clave():
        print("\n  No hay ANTHROPIC_API_KEY ni .env.")
        return 1

    import logging
    logging.disable(logging.INFO)
    from nucleo.llm.client import LLMClient, LLMConfig, LLMProvider
    from nucleo.lean.client import LeanClient
    from nucleo.llm.contador import Contador

    llm = LLMClient(LLMConfig(model=modelo, provider=LLMProvider.ANTHROPIC,
                              api_key=os.environ["ANTHROPIC_API_KEY"],
                              max_tokens=2048))
    lean = LeanClient()
    bloque = re.compile(r"```(?:lean4?|Lean4?)?\s*\n(.*?)```", re.S)

    inicial = Contador.total()
    filas = []
    print()
    for i, q in enumerate(casos, 1):
        if Contador.total() - inicial + 0.02 > tope:
            print("\n  TOPE alcanzado. Se para.")
            break
        t0 = time.time()
        veredicto, err, codigo = "", None, ""
        try:
            # `sin_historial`: cada caso es independiente. Sin esto el
            # segundo prompt arrastra la respuesta del primero y la línea
            # base deja de ser una línea base.
            r = await llm.generate(PLANTILLA % q, system=SISTEMA,
                                   sin_historial=True)
            texto = getattr(r, "content", "") or ""
            m = bloque.search(texto)
            codigo = (m.group(1) if m else texto).strip()
            if codigo:
                lr = await lean.check_code(codigo)
                veredicto = str(getattr(lr, "status", ""))
        except Exception as exc:                                # noqa: BLE001
            err = "%s: %s" % (type(exc).__name__, exc)
        seg = time.time() - t0
        gastado = Contador.total() - inicial
        filas.append({"consulta": q, "veredicto": veredicto,
                      "seg": round(seg, 1), "nchars": len(codigo),
                      "error": err, "gastado": round(gastado, 4)})
        print("  [%2d/%2d] %-42s %-26s %5.1fs  $%.3f"
              % (i, len(casos), q[:42], veredicto.split(".")[-1] or "SIN CODIGO",
                 seg, gastado))

    ok = sum(1 for f in filas if f["veredicto"].endswith("SUCCESS"))
    print("\n  LÍNEA BASE: %d de %d verifican (%.0f %%)"
          % (ok, len(filas), 100.0 * ok / max(1, len(filas))))
    print("  gasto real: $%.3f" % (Contador.total() - inicial))
    print("\n  PARA COMPARAR (campaña, mismos 20 casos):")
    print("    sistema completo         12 de 20  (60 %)")
    print("    sistema sin vocabulario  11 de 20  (55 %)")

    json.dump({"modelo": modelo, "n": len(filas), "verifica": ok,
               "gastado": round(Contador.total() - inicial, 4),
               "filas": filas},
              io.open(SALIDA, "w", encoding="utf-8"), indent=1,
              ensure_ascii=False)
    print("\n-> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ejecutar", action="store_true")
    ap.add_argument("--modelo", default="claude-sonnet-5")
    ap.add_argument("--tope", type=float, default=0.60)
    a = ap.parse_args()
    raise SystemExit(asyncio.run(main(a.ejecutar, a.modelo, a.tope)))
