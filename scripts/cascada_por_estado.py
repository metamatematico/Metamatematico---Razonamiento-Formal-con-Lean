# -*- coding: utf-8 -*-
"""La puerta del paso 2: la cascada en la sesión contra la cascada en fichero.

LAS DOS RAMAS, CON EL MISMO ORDEN Y EL MISMO TEXTO
---------------------------------------------------
    A · hoy     `SolverCascade.try_fill_sorry`: el bloque `first | (t ; done) |…`
                en el sitio del sorry, un compilado. Es lo que `_try_solve_sorries`
                hace por cada sorry, sin la rama del LLM de `sorry_filler`.
    B · paso 2  el mismo bloque en el sitio del sorry, elaborado como COMANDO
                en la sesión viva (`cascada_sesion.cerrar_sorries_por_comando`);
                si cierra, la prueba con la táctica GANADORA se compila y ESO
                es el veredicto (invariante I2).

La primera versión aplicaba el bloque en MODO TÁCTICA sobre el proofState. Se
cambió porque el REPL no aplica ahí el límite de heartbeats: en un objetivo
duro (`n * n ≠ 2`) se agotaba a los 120 s, cuando el fichero falla en 16,6 s.
Esa medición está en `data/cascada_por_estado.modo_tactica.json`; ésta mide lo
que corre en producción. Y por lo mismo el banco lleva ahora `DUROS`: la
versión anterior no contenía el fenómeno y no podía verlo.

El orden sale de `SolverCascade.orden_para`, el mismo para las dos. Y B no
reconstruye el código: toma el texto que A manda a Lean —ya normalizado por
`_normalize_code`— y sustituye el bloque por `sorry`. Cabecera, renombres y
táctica son los mismos caracteres; lo único distinto es el canal.

LOS CASOS
---------
Los de `scripts/cascada_contra_lean.py`: teoremas de una línea de Mathlib, sin
su prueba, con la cabecera y el contexto de SU fichero y no el fichero mismo,
para que `exact?` no encuentre la respuesta. Un enunciado que no elabora con
`sorry` se EXCLUYE de las dos ramas y se cuenta aparte: no es un fallo de
ninguna cascada. El filtro lo hace la sesión —más barato— y es simétrico: un
caso excluido no se mide en ninguna rama.

LA REGLA, ESCRITA ANTES DE CORRER
---------------------------------
Se mide cada caso en las dos ramas y se cuentan:

    perdidos   A cierra y B no              -> tiene que ser 0
    ganados    B cierra y A no              -> se enseñan uno a uno
    falsos     la sesión dijo «cierra» y el fichero no lo aceptó
               -> no dañan el veredicto (I2), pero si pasan hay que entender por qué

    SIGUE si   perdidos == 0  y  (ganados > 0  o  B cuesta menos que A)

«Cuesta» en segundos y en procesos de Lean. La carga de cada cabecera en la
sesión se cuenta APARTE: en el sistema servido la sesión vive entre consultas
y esa carga se paga una vez, aquí se paga en cada caso porque cada teorema trae
la cabecera de su fichero. Se dan las dos cuentas, con y sin ella, y la regla
se aplica a la que NO la amortiza —la peor para B—.

Lo que se espera, dicho antes para que no se lea después a conveniencia: B no
puede cerrar más que A salvo donde el bloque entero agota el presupuesto y la
ganadora sola no; lo esperable es un empate en cierres. La ganancia esperada
está en los FALLOS, que son la mayoría: B no necesita compilado para saber que
no cerró.

LA PRIMERA CORRIDA SE ANULO, Y POR QUE
--------------------------------------
Dio «PASA»: 0 perdidos y B más barato. Y NINGUNO de 25 casos cerraba en
NINGUNA rama. Un banco sin cierres no puede decir si B cierra más; su «pasa»
era hueco. Detrás había dos fallos, ninguno de la sesión:

  · en PRODUCCION: `field_simp` no existe bajo `_SAFE_HEADER`, y un `first |`
    es una pieza de sintaxis: Lean rechazaba el bloque entero («unknown
    tactic») sin probar ninguna rama. La cascada servida no cerraba ni
    `a + b = b + a` desde el 2026-09-04. Arreglado en `lean/client.py`, con
    un guardián que compila de verdad.
  · en el BANCO: el contexto de cada teorema acumulaba las `variable` de
    secciones ya cerradas (`contexto_vigente` en `cascada_contra_lean.py`).

La regla de arriba no se tocó entre una corrida y otra.

No gasta API.

    python -m scripts.cascada_por_estado --n 25
"""
from __future__ import annotations

import argparse
import asyncio
import io
import json
import os
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

SALIDA = os.path.join(RAIZ, "data", "cascada_por_estado.json")

#: objetivos que la cascada NO cierra y en los que las tácticas de búsqueda
#: (`exact?`, `apply?`, `aesop`, `nlinarith`) trabajan de verdad antes de rendirse
DUROS = [
    "(n : ℕ) : n * n ≠ 2",
    "(n : ℕ) (h : 0 < n) : n < 2 ^ n",
    "(a b : ℕ) (h : a * b = 1) : a = 1",
    "(x : ℝ) (h : x ^ 3 = 8) : x = 2",
    "(n : ℕ) : 6 ∣ n * (n + 1) * (n + 2)",
]
MAX_CABECERAS = 3


def partir(codigo):
    """(cabecera, cuerpo, líneas de cabecera). Ver sesion_contra_fichero.partir."""
    lineas = codigo.split("\n")
    i = 0
    while i < len(lineas) and (lineas[i].strip().startswith("import ")
                               or not lineas[i].strip()):
        i += 1
    cab = "\n".join(l.strip() for l in lineas[:i] if l.strip())
    return cab, "\n".join(lineas[i:]), lineas[:i]


def texto_de_A(cliente, codigo_con_bloque):
    """El texto EXACTO que la rama A manda a Lean, y la línea del bloque."""
    norm = cliente._normalize_code(codigo_con_bloque)
    for i, l in enumerate(norm.split("\n")):
        if "first | (" in l:
            return norm, i
    return norm, None


def _guardar(filas, excluidos, extra=None):
    doc = {"n": len(filas), "excluidos": excluidos, "filas": filas}
    doc.update(extra or {})
    json.dump(doc, io.open(SALIDA, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)


def main(n):
    from nucleo.lean.cascada_sesion import cerrar_sorries_por_comando, ensamblar
    from nucleo.lean.client import LeanClient
    from nucleo.lean.sesion import SesionLean
    from nucleo.lean.solver_cascade import SolverCascade, _bloque_first
    from scripts.cascada_contra_lean import candidatos
    from scripts.tacticas_reales_mathlib import AREA

    cliente = LeanClient(project_path=RAIZ)
    base = SolverCascade(cliente)
    bucle = asyncio.new_event_loop()

    print("buscando teoremas de una linea en Mathlib...")
    cands = candidatos(AREA, n)
    #: LOS DUROS, que el banco no tenía y por eso no vio el agotamiento: en
    #: los 18 fallos de Mathlib la cascada fallaba rápido, y en `n * n ≠ 2`
    #: el modo táctica tardó >120 s. Sin área de Mathlib ni fichero: van con
    #: la cabecera estrecha, como una consulta de alumno. Se miden aparte
    #: de las n de Mathlib, así que el banco tiene n + len(DUROS) filas.
    duros = [{"nombre": "duro_%d" % i, "sig": sig, "area": "algebra",
              "imports": [], "contexto": [], "fichero": "sintetico.lean"}
             for i, sig in enumerate(DUROS, 1)]
    n_total = n + len(duros)
    print("  %d candidatos; se mediran hasta %d que elaboren\n" % (len(cands), n))
    print("  %-34s %-12s %-22s %-22s" % ("teorema", "area", "A · fichero", "B · sesion"))
    print("  " + "-" * 92)

    filas, excluidos = [], 0
    s, entornos, seg_cabeceras = SesionLean().abrir(), {}, 0.0
    try:
        for c in duros + cands:
            if len(filas) >= n_total:
                break
            codigo = ("\n".join("import " + i for i in c["imports"])
                      + "\n\n" + "\n".join(c["contexto"])
                      + "\n\ntheorem _probe_ %s := by\n  sorry\n" % c["sig"])
            linea_sorry = codigo.split("\n").index("  sorry") + 1
            orden = base.orden_para(c["sig"],
                                    area_premisas=c["area"])
            con_bloque = codigo.replace("\n  sorry\n",
                                        "\n  " + _bloque_first(orden) + "\n")
            normA, i_bloque = texto_de_A(cliente, con_bloque)
            if i_bloque is None:
                print("  %-34s el normalizador no dejo el bloque: se excluye"
                      % c["nombre"][:34])
                excluidos += 1
                continue
            lineas = normA.split("\n")
            tactica = lineas[i_bloque].strip()
            sangria = lineas[i_bloque][:len(lineas[i_bloque]) - len(lineas[i_bloque].lstrip())]
            lineas[i_bloque] = sangria + "sorry"
            codB = "\n".join(lineas)
            cab, cuerpo, lineas_cab = partir(codB)

            # ── la cabecera en la sesión, una vez por texto distinto ──────
            #: SE CARGA AL CASO QUE LA USA, y sólo si ese caso se mide. El
            #: ensayo de 2 casos sumaba también las cabeceras de los EXCLUIDOS
            #: —3 de 5—, que la rama A nunca paga porque no los compila: un
            #: sesgo de contabilidad contra B, visto antes de la corrida real.
            seg_cab = 0.0
            if cab not in entornos:
                if len(entornos) >= MAX_CABECERAS:
                    s.cerrar()
                    s, entornos = SesionLean().abrir(), {}
                t0 = time.time()
                entornos[cab] = s.comando(cab, env=None).env
                seg_cab = time.time() - t0
            env = entornos[cab]

            # ── B: elabora (y filtra) + la cascada sobre el proofState ────
            t0 = time.time()
            # MODO COMANDO, el que corre en producción: el modo táctica no
            # respeta los heartbeats y se agota en los fallos duros
            cierres, err = cerrar_sorries_por_comando(s, cuerpo, tactica, env=env)
            seg_B_sesion = time.time() - t0
            if err or env is None:
                excluidos += 1
                continue
            if any(x.motivo == "agotada" for x in cierres):
                s.cerrar()
                s, entornos = SesionLean().abrir(), {}
            b_dice = bool(cierres) and all(x.cerrado for x in cierres)
            ganadora_B = ",".join(x.ganadora or "?" for x in cierres)
            b_ok, seg_B_fichero, procesos_B = False, 0.0, 0
            if b_dice:
                ens = ensamblar(cuerpo, cierres, tactica)
                if ens is not None:
                    t0 = time.time()
                    rB = bucle.run_until_complete(
                        cliente.check_code("\n".join(lineas_cab) + "\n" + ens))
                    seg_B_fichero = time.time() - t0
                    procesos_B = 1
                    b_ok = bool(rB.is_success)

            # ── A: la cascada de hoy, un compilado ────────────────────────
            casc = SolverCascade(cliente, solvers=orden)
            t0 = time.time()
            rA = bucle.run_until_complete(casc.try_fill_sorry(codigo, linea_sorry))
            seg_A = time.time() - t0
            a_ok = bool(rA.success)

            fila = {"nombre": c["nombre"], "area": c["area"], "fichero": c["fichero"],
                    "n_tacticas": len(orden),
                    "A_cierra": a_ok, "A_ganadora": rA.solver or "",
                    "A_seg": round(seg_A, 1), "A_procesos": 1,
                    "B_sesion_dice": b_dice, "B_ganadora": ganadora_B,
                    "B_cierra": b_ok, "B_seg_sesion": round(seg_B_sesion, 2),
                    "B_seg_fichero": round(seg_B_fichero, 1),
                    "B_procesos": procesos_B,
                    "B_seg_cabecera": round(seg_cab, 1),
                    "B_motivos": [x.motivo for x in cierres]}
            filas.append(fila)
            seg_cabeceras += seg_cab
            marca = ("" if a_ok == b_ok else
                     "  <- PERDIDO" if a_ok else "  <- GANADO")
            if b_dice and not b_ok:
                marca += "  <- la sesion dijo cierra, el fichero no"
            print("  %-34s %-12s %-22s %-22s%s" % (
                c["nombre"][:34], c["area"][:12],
                ("cierra " + (rA.solver or "")[:10] if a_ok else "no") + " %.0fs" % seg_A,
                ("cierra " + ganadora_B[:10] if b_ok else "no")
                + " %.1f+%.0fs" % (seg_B_sesion, seg_B_fichero), marca))
            _guardar(filas, excluidos, {"segundos_cabeceras_B": round(seg_cabeceras, 1)})
    finally:
        s.cerrar()
        bucle.close()

    # ── la regla, tal como se escribió arriba ────────────────────────────
    perdidos = [f for f in filas if f["A_cierra"] and not f["B_cierra"]]
    ganados = [f for f in filas if f["B_cierra"] and not f["A_cierra"]]
    falsos = [f for f in filas if f["B_sesion_dice"] and not f["B_cierra"]]
    segA = sum(f["A_seg"] for f in filas)
    segB = sum(f["B_seg_sesion"] + f["B_seg_fichero"] for f in filas)
    segB_con = segB + seg_cabeceras
    procA = sum(f["A_procesos"] for f in filas)
    procB = sum(f["B_procesos"] for f in filas)
    fallosA = [f for f in filas if not f["A_cierra"]]

    print("\n=== LO MEDIDO ===\n")
    print("  medidos %d · excluidos por no elaborar %d" % (len(filas), excluidos))
    print("  cierra A (fichero)   %2d de %d" % (sum(f["A_cierra"] for f in filas), len(filas)))
    print("  cierra B (sesion)    %2d de %d" % (sum(f["B_cierra"] for f in filas), len(filas)))
    print("  perdidos %d · ganados %d · falsos de la sesion %d"
          % (len(perdidos), len(ganados), len(falsos)))
    print("\n  segundos  A %.0f   ·   B %.0f sin cabeceras, %.0f con ellas"
          % (segA, segB, segB_con))
    print("  procesos de Lean  A %d   ·   B %d" % (procA, procB))
    if fallosA:
        print("  en los %d casos que NO cierran: A %.0f s · B %.1f s"
              % (len(fallosA), sum(f["A_seg"] for f in fallosA),
                 sum(f["B_seg_sesion"] + f["B_seg_fichero"] for f in fallosA)))
    for f in ganados:
        print("    ganado: %s con %s" % (f["nombre"], f["B_ganadora"]))
    for f in perdidos:
        print("    PERDIDO: %s (A cerro con %s)" % (f["nombre"], f["A_ganadora"]))

    print("\n=== LA PUERTA ===\n")
    #: la regla se aplica a la cuenta CON cabeceras: la peor para B
    mas_barato = segB_con < segA
    pasa = not perdidos and (bool(ganados) or mas_barato)
    if pasa:
        print("  PASA: 0 perdidos, y %s." % (
            "%d ganados" % len(ganados) if ganados else
            "B cuesta menos incluso pagando cada cabecera (%.0f s frente a %.0f)"
            % (segB_con, segA)))
    else:
        print("  NO PASA: %s." % (
            "%d perdido(s)" % len(perdidos) if perdidos else
            "0 ganados y B no cuesta menos pagando las cabeceras "
            "(%.0f s frente a %.0f)" % (segB_con, segA)))
    if falsos:
        print("\n  %d vez/veces la sesion dijo «cierra» y el fichero no. El" % len(falsos))
        print("  veredicto no se contamina (I2), pero hay que entender por que.")

    # ── LA FUGA: ¿el cierre es del teorema encontrándose a sí mismo? ──────
    #: `_normalize_code` pone la cabecera estrecha, que alcanza cientos de
    #: módulos; si el fichero del teorema está entre ellos, `simp` o `exact?`
    #: pueden cerrarlo CON EL PROPIO TEOREMA. En la primera corrida válida los
    #: 7 cierres eran de ésos, y ninguno de los 14 no alcanzables cerraba. Vale
    #: la comparación A-B, que ven el mismo texto; no vale la tasa.
    fuga = {}
    try:
        from nucleo.lean import alcance
        al = alcance.alcanza([l.split()[1] for l in cliente._SAFE_HEADER.splitlines()
                              if l.startswith("import")])
        for f in filas:
            f["su_fichero_alcanzable"] = (
                "Mathlib." + f["fichero"][:-5].replace("/", ".")) in al
        alc = [f for f in filas if f["su_fichero_alcanzable"]]
        fuga = {"alcanzables": len(alc),
                "cierres_alcanzables": sum(f["A_cierra"] for f in alc),
                "cierres_no_alcanzables": sum(
                    f["A_cierra"] for f in filas if not f["su_fichero_alcanzable"])}
        print("\n  LA FUGA: %d de %d casos tienen su propio fichero al alcance de la"
              % (fuga["alcanzables"], len(filas)))
        print("  cabecera; cierran %d de ésos y %d de los demás. Los cierres NO son"
              % (fuga["cierres_alcanzables"], fuga["cierres_no_alcanzables"]))
        print("  una tasa de la cascada: sólo sirven para comparar A con B.")
    except Exception as e:                                     # noqa: BLE001
        print("  (no se pudo medir la fuga: %s)" % e)

    _guardar(filas, excluidos, {
        "fuga": fuga,
        "segundos_cabeceras_B": round(seg_cabeceras, 1),
        "perdidos": len(perdidos), "ganados": len(ganados), "falsos": len(falsos),
        "segundos_A": round(segA, 1), "segundos_B": round(segB, 1),
        "segundos_B_con_cabeceras": round(segB_con, 1),
        #: lo que lee el decisor: null si se perdio algun cierre, y entonces
        #: la capacidad se apaga sola por barata que sea
        "segundos_B_si_no_pierde": None if perdidos else round(segB_con, 1),
        "procesos_A": procA, "procesos_B": procB, "pasa": pasa})
    print("\n-> %s" % SALIDA)
    return 0 if pasa else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=25)
    raise SystemExit(main(ap.parse_args().n))
