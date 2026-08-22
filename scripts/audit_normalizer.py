"""
Audita que le hace `LeanClient._normalize_code` a codigo Lean 4 que SI compila.

POR QUE
-------
_normalize_code reescribe el codigo antes de verificarlo: quita `import Mathlib`
(cargarlo entero mide 742 s y siempre expira), descarta imports que juzga
inexistentes, inyecta una cabecera estrecha mas imports tematicos, y sustituye
nombres de lemas obsoletos por reemplazo textual.

Cada una de esas cuatro cosas ha roto codigo valido al menos una vez:

  · modulos partidos en directorio (`Mathlib.Topology.Instances.Real`) se
    descartaban en silencio, garantizando el fallo;
  · quitar `import Mathlib` se llevaba por delante la NOTACION `a ≡ b [MOD n]`,
    produciendo "expected token" — un error de parseo que repair_imports, que
    busca "unknown identifier", no puede rescatar;
  · la sustitucion de lemas es `code.replace(viejo, nuevo)` sin limites de
    palabra, asi que puede reescribir el ENUNCIADO del teorema y hacer que Lean
    verifique algo distinto de lo que se pregunto.

Los tres se descubrieron de uno en uno, consulta a consulta. Este script los
busca todos de golpe: LeanWorkbookProofs son 29.750 pruebas Lean 4 que
compilan, asi que cualquiera que deje de compilar tras normalizar es un fallo
del normalizador, no del codigo.

METODO
------
1. Barrido ESTATICO sobre las 29.750 (segundos): que cambia el normalizador y
   donde. No necesita Lean.
2. Confirmacion con Lean sobre una muestra (~20 s por prueba), priorizando los
   casos que el barrido marca como sospechosos.

USO
---
    python scripts/audit_normalizer.py                 # solo estatico
    python scripts/audit_normalizer.py --lean 20       # + Lean sobre 20
"""
from __future__ import annotations

import argparse
import asyncio
import json
import random
import re
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

# La consola de Windows usa cp1252 y los cuadros/flechas del informe la
# revientan. Sin esto el script muere al imprimir la primera cabecera.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ORIGEN = Path(r"E:\MetamatematicoDataSet\LeanWorkbookProofs")
INFORME = RAIZ / "data" / "audit_normalizer.json"

#: Notacion y construcciones que NO estan en la cabecera estrecha y que, si se
#: quedan sin su modulo, producen un error de PARSEO (no de identificador), que
#: es el que repair_imports no sabe arreglar.
NOTACION_RIESGO = [
    ("[MOD ", "Data.Nat.ModEq"),
    ("[ZMOD ", "Data.Int.ModEq"),
    ("∑ ", "BigOperators"),
    ("∏ ", "BigOperators"),
    ("⌊", "Order.Floor"),
    ("⌈", "Order.Floor"),
    ("∫", "MeasureTheory"),
    ("deriv ", "Analysis.Calculus"),
    ("Finset.", "Finset"),
    ("Matrix", "Matrix"),
    ("Polynomial", "Polynomial"),
    ("Real.sqrt", "Analysis.SpecialFunctions"),
    ("Real.log", "Analysis.SpecialFunctions"),
    ("Real.exp", "Analysis.SpecialFunctions"),
    ("Complex.", "Analysis.SpecialFunctions.Complex"),
    ("Nat.choose", "Data.Nat.Choose"),
    ("Nat.factorial", "Data.Nat.Factorial"),
    ("Nat.Prime", "Data.Nat.Prime"),
]


def _statement(code: str) -> str:
    """Enunciado del teorema: desde `theorem`/`lemma` hasta `:= by`."""
    m = re.search(r"^(theorem|lemma)\b.*?:=\s*by", code, re.S | re.M)
    return m.group(0) if m else ""


def auditar_estatico(cliente, pruebas: list[str]) -> dict:
    from nucleo.lean.client import LeanClient  # noqa: F401

    hallazgos = Counter()
    sospechosos: list[dict] = []
    imports_caidos = Counter()
    lemas_sustituidos = Counter()

    for i, code in enumerate(pruebas):
        try:
            norm = cliente._normalize_code(code)
        except Exception:
            hallazgos["normalizador_lanza_excepcion"] += 1
            continue

        motivos = []

        # 1. ¿Se quito `import Mathlib` y quedo notacion sin cubrir?
        quito_mathlib = any(
            l.strip() == "import Mathlib" for l in code.splitlines()
        )
        if quito_mathlib:
            hallazgos["import_mathlib_retirado"] += 1
            # Solo cuentan los IMPORTS del codigo normalizado. Mirar el texto
            # entero daba 0 sospechosas siempre: estas pruebas llevan
            # `open BigOperators Real Nat Topology Rat`, que sobrevive a la
            # normalizacion, asi que el nombre del modulo aparecia igual y la
            # comprobacion pasaba sin comprobar nada.
            imports_norm = "\n".join(
                l for l in norm.splitlines() if l.strip().startswith("import")
            )
            for token, modulo in NOTACION_RIESGO:
                if token in code and modulo not in imports_norm:
                    motivos.append(f"notacion {token.strip()!r} sin {modulo}")
                    hallazgos[f"notacion_sin_modulo:{modulo}"] += 1

        # 2. Imports descartados por juzgarlos inexistentes.
        for l in code.splitlines():
            if l.strip().startswith("import Mathlib") and l.strip() != "import Mathlib":
                if l.strip() not in norm:
                    expandido = cliente._expand_split_module(l)
                    if not expandido:
                        imports_caidos[l.strip()] += 1
                        motivos.append(f"import descartado: {l.strip()}")
                        hallazgos["import_descartado"] += 1

        # 3. ¿La sustitucion textual toco el ENUNCIADO del teorema?
        st_antes, st_despues = _statement(code), _statement(norm)
        if st_antes and st_despues and st_antes != st_despues:
            hallazgos["enunciado_alterado"] += 1
            motivos.append("EL ENUNCIADO CAMBIO")
            for viejo, nuevo in cliente._DEPRECATED_LEMMAS:
                if viejo != nuevo and viejo in st_antes:
                    lemas_sustituidos[f"{viejo} -> {nuevo}"] += 1

        if motivos:
            sospechosos.append({"idx": i, "motivos": motivos})

    return {
        "total": len(pruebas),
        "hallazgos": dict(hallazgos.most_common()),
        "imports_caidos": dict(imports_caidos.most_common(10)),
        "lemas_en_enunciado": dict(lemas_sustituidos.most_common(10)),
        "sospechosos": sospechosos,
    }


async def confirmar_con_lean(cliente, pruebas, sospechosos, n: int) -> dict:
    """Ejecuta Lean sobre una muestra: mitad sospechosas, mitad al azar."""
    from nucleo.lean.client import LeanResultStatus

    idx_sosp = [s["idx"] for s in sospechosos][: n // 2]
    resto = [i for i in range(len(pruebas)) if i not in set(idx_sosp)]
    random.seed(0)
    idx = idx_sosp + random.sample(resto, min(n - len(idx_sosp), len(resto)))

    ok = rescatadas = fallo = 0
    fallos: list[dict] = []
    for k, i in enumerate(idx, 1):
        code = pruebas[i]
        r = await cliente.check_code(code)
        bien = r.status in (LeanResultStatus.SUCCESS, LeanResultStatus.SORRY)
        marca = "sospechosa" if i in set(idx_sosp) else "al azar"

        # Si falla, probar la REPARACION que el pipeline real aplica siempre.
        # Medir solo normalize+check daba una imagen peor que la realidad:
        # repair_imports busca el identificador ausente en las fuentes de
        # Mathlib y deduce su modulo, asi que rescata los fallos de import que
        # no son de notacion. Se reportan los dos numeros por separado.
        reparada = False
        if not bien:
            arreglo = cliente.repair_imports(code, r.error_messages)
            if arreglo:
                r2 = await cliente.check_code(arreglo)
                if r2.status in (LeanResultStatus.SUCCESS, LeanResultStatus.SORRY):
                    reparada = True
                    r = r2

        etiqueta = r.status.name + ("  (rescatada por repair_imports)" if reparada else "")
        print(f"   [{k:2d}/{len(idx)}] {marca:11s} idx={i:<6d} {etiqueta}")

        if bien:
            ok += 1
        elif reparada:
            rescatadas += 1
        else:
            fallo += 1
            fallos.append({
                "idx": i, "marca": marca, "status": r.status.name,
                "error": (r.get_first_error() or "")[:160],
            })
    return {
        "probadas": len(idx),
        "compilan_directo": ok,
        "rescatadas_por_repair": rescatadas,
        "compilan_total": ok + rescatadas,
        "rotas": fallo,
        "fallos": fallos,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--muestra", type=int, default=0,
                    help="0 = todas las pruebas en el barrido estatico")
    ap.add_argument("--lean", type=int, default=0,
                    help="cuantas confirmar ejecutando Lean (0 = ninguna)")
    args = ap.parse_args()

    if not ORIGEN.exists():
        print(f"No encuentro el dataset en {ORIGEN}")
        return 1

    from datasets import load_from_disk
    from nucleo.lean.client import LeanClient

    ds = load_from_disk(str(ORIGEN))
    pruebas = [r["full_proof"] for r in ds]
    if args.muestra:
        pruebas = pruebas[: args.muestra]
    print(f"LeanWorkbookProofs: {len(pruebas):,} pruebas que compilan\n")

    cliente = LeanClient(project_path=str(RAIZ), timeout_ms=400000)

    print("── Barrido estatico ──────────────────────────────────────")
    est = auditar_estatico(cliente, pruebas)
    for k, v in est["hallazgos"].items():
        pct = 100 * v / est["total"]
        print(f"   {k:44s} {v:6,}  ({pct:5.1f}%)")
    if est["imports_caidos"]:
        print("\n   imports descartados mas frecuentes:")
        for k, v in est["imports_caidos"].items():
            print(f"      {v:5,}  {k}")
    if est["lemas_en_enunciado"]:
        print("\n   sustituciones que tocaron el ENUNCIADO:")
        for k, v in est["lemas_en_enunciado"].items():
            print(f"      {v:5,}  {k}")
    print(f"\n   pruebas con al menos un motivo de sospecha: "
          f"{len(est['sospechosos']):,} ({100*len(est['sospechosos'])/est['total']:.1f}%)")

    informe = {"estatico": {k: v for k, v in est.items() if k != "sospechosos"}}

    if args.lean:
        print(f"\n── Confirmacion con Lean ({args.lean} pruebas) ────────────")
        informe["lean"] = asyncio.run(
            confirmar_con_lean(cliente, pruebas, est["sospechosos"], args.lean)
        )
        r = informe["lean"]
        print(f"\n   compilan tras normalizar : {r['compilan_directo']}/{r['probadas']}")
        print(f"   rescatadas por repair    : {r['rescatadas_por_repair']}")
        print(f"   COMPILAN en total        : {r['compilan_total']}/{r['probadas']}"
              f"  ({100*r['compilan_total']/r['probadas']:.0f}%)")
        print(f"   ROTAS por el pipeline    : {r['rotas']}")
        for f in r["fallos"]:
            print(f"      idx={f['idx']} ({f['marca']}) {f['status']}: {f['error'][:90]}")

    INFORME.parent.mkdir(parents=True, exist_ok=True)
    INFORME.write_text(json.dumps(informe, ensure_ascii=False, indent=2),
                       encoding="utf-8")
    print(f"\nInforme -> {INFORME}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
