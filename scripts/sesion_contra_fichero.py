# -*- coding: utf-8 -*-
"""La puerta del paso 1: ¿acepta la sesión lo mismo que el fichero?

LA PREGUNTA, Y POR QUE ES DE SEGURIDAD Y NO DE VELOCIDAD
--------------------------------------------------------
La velocidad ya está medida y pasa de sobra: con el entorno cargado, una
táctica cuesta 0,02–0,63 s frente a los ~15,5 s de un compilado. Eso es lo
que hace viable un lazo por pasos.

Lo que NO está medido es lo único que puede hacer daño: **que la sesión acepte
algo que el fichero rechaza**. El REPL tiene registrado un caso en que aceptó
pruebas incorrectas (leanprover-community/repl, issue 44). Si eso pasara aquí,
el lazo construiría caminos sobre flechas falsas.

El invariante I2 ya protege el veredicto —«verificado» sale siempre de
`check_code` sobre la prueba ensamblada, nunca de la sesión— así que un
desacuerdo no puede producir un sello falso. Pero sí produciría búsqueda
perdida, y hay que saber cuánta.

    ACEPTA LA SESION / RECHAZA EL FICHERO   es la casilla que importa
    RECHAZA LA SESION / ACEPTA EL FICHERO   es incómodo pero inocuo

ENTRADA IDENTICA, Y ESO NO ES UN DETALLE
-----------------------------------------
La sesión ve EXACTAMENTE los `import` del propio código, nunca más. Tentaba
cargar `import Mathlib` una vez para todos —sería más rápido— pero entonces la
sesión vería MAS biblioteca que el fichero y aceptaría cosas que el fichero no
puede: un desacuerdo que no sería del motor sino de la cabecera.

Lo que sí se hace es cargar cada cabecera DISTINTA una sola vez y mandar sólo
el cuerpo contra ella (ver `partir`). No es un atajo sobre la equivalencia:
la misma cabecera es la misma biblioteca. Es lo que evita que el REPL acumule
un entorno con Mathlib entero por caso, que es como la primera versión llegó a
12,4 GB y tumbó la máquina en el caso 17.

No gasta API. Gasta tiempo de Lean.

    python -m scripts.sesion_contra_fichero --n 12
"""
from __future__ import annotations

import argparse
import io
import json
import os
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

GRABACIONES = os.path.join(RAIZ, "data", "grabaciones", "formalizaciones.jsonl")
SALIDA = os.path.join(RAIZ, "data", "sesion_contra_fichero.json")
TOPE = 300


def _cargar(n):
    filas, vistos = [], set()
    for linea in io.open(GRABACIONES, encoding="utf-8"):
        if not linea.strip():
            continue
        try:
            d = json.loads(linea)
        except Exception:                                      # noqa: BLE001
            continue
        cod = (d.get("codigo") or "").strip()
        #: el mismo codigo aparece varias veces en el fichero; para una
        #: medicion de concordancia cada uno cuenta UNA vez
        if not cod or cod in vistos:
            continue
        vistos.add(cod)
        filas.append(d)
        if n and len(filas) >= n:
            break
    return filas


def por_fichero(codigo):
    """El camino de hoy. Acepta = compila, o sólo avisa de `sorry`."""
    ruta = os.path.join(RAIZ, "_concordancia.lean")
    io.open(ruta, "w", encoding="utf-8").write(codigo + "\n")
    t0 = time.time()
    try:
        p = subprocess.run(["lake", "env", "lean", ruta], cwd=RAIZ,
                           capture_output=True, text=True, timeout=TOPE,
                           encoding="utf-8", errors="replace")
        sal = (p.stdout or "") + (p.stderr or "")
        acepta = p.returncode == 0 or ("declaration uses 'sorry'" in sal
                                       and "error:" not in sal)
        detalle = "" if acepta else sal[:200]
    except subprocess.TimeoutExpired:
        acepta, detalle = None, "TIMEOUT"
    seg = time.time() - t0
    try:
        os.remove(ruta)
    except OSError:
        pass
    return acepta, seg, detalle


def partir(codigo):
    """(cabecera, cuerpo): los `import` del principio, y lo demás.

    POR QUE SE PARTE. La primera versión mandaba el código entero con entorno
    nuevo por caso, y el REPL guarda CADA entorno en el mismo proceso: con
    `import Mathlib` en casi todos iba por 12,4 GB en el caso 16, y el 17 tumbó
    la máquina (WinError 1455, archivo de paginación). Dos casos con la MISMA
    cabecera ven exactamente la misma biblioteca, así que cargarla una vez por
    texto distinto no cambia lo que se mide: sigue sin haber entorno más ancho
    que el del fichero.
    """
    lineas = codigo.splitlines()
    i = 0
    while i < len(lineas) and (lineas[i].strip().startswith("import ")
                               or not lineas[i].strip()):
        i += 1
    cab = "\n".join(l.strip() for l in lineas[:i] if l.strip())
    return cab, "\n".join(lineas[i:])


#: cuántas cabeceras distintas se tienen vivas antes de reiniciar la sesión
MAX_CABECERAS = 3


def _guardar(tabla):
    de_acuerdo = sum(1 for t in tabla if t["fichero"] == t["sesion"])
    peligro = [t for t in tabla if t["sesion"] and t["fichero"] is False]
    inocuo = [t for t in tabla if t["fichero"] and not t["sesion"]]
    json.dump({"n": len(tabla), "de_acuerdo": de_acuerdo,
               "sesion_acepta_fichero_no": len(peligro),
               "sesion_rechaza_fichero_si": len(inocuo),
               "segundos_fichero": round(sum(t["fichero_seg"] for t in tabla), 1),
               "segundos_sesion": round(sum(t["sesion_seg"] for t in tabla), 1),
               "tabla": tabla},
              io.open(SALIDA, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return de_acuerdo, peligro, inocuo


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=12,
                    help="cuantas grabaciones distintas (cada una son 2 "
                         "elaboraciones: una por camino)")
    args = ap.parse_args()

    from nucleo.lean.sesion import SesionLean

    filas = _cargar(args.n)
    print("%d formalizaciones distintas · %d elaboraciones\n"
          % (len(filas), 2 * len(filas)))

    tabla = []
    print("  %-44s %-10s %-10s %s" % ("consulta", "fichero", "sesion", ""))
    print("  " + "-" * 82)
    s, entornos = SesionLean().abrir(), {}
    try:
        for f in filas:
            cod = (f.get("codigo") or "").strip()
            a_ok, a_seg, a_det = por_fichero(cod)
            # LA MISMA CABECERA QUE EL FICHERO, cargada una vez por texto
            # distinto. Nunca un entorno más ancho: si el código no trae
            # imports, el cuerpo va con env=None, sin biblioteca alguna.
            cab, cuerpo = partir(cod)
            t0 = time.time()
            if cab and cab not in entornos:
                if len(entornos) >= MAX_CABECERAS:
                    s.cerrar()
                    s, entornos = SesionLean().abrir(), {}
                entornos[cab] = s.comando(cab, env=None).env
            r = s.comando(cuerpo if cab else cod,
                          env=entornos.get(cab) if cab else None)
            r.segundos = time.time() - t0
            b_ok = r.clase != "error"
            marca = ("de acuerdo" if a_ok == b_ok else
                     "SESION ACEPTA, FICHERO NO" if (b_ok and a_ok is False)
                     else "sesion rechaza, fichero si")
            tabla.append({"consulta": (f.get("consulta") or "")[:70],
                          "fichero": a_ok, "fichero_seg": round(a_seg, 1),
                          "sesion": b_ok, "sesion_seg": round(r.segundos, 1),
                          "clase": r.clase, "marca": marca,
                          "err_fichero": a_det[:160], "err_sesion": r.error[:160]})
            print("  %-44s %-10s %-10s %s"
                  % ((f.get("consulta") or "")[:44],
                     ("acepta" if a_ok else "rechaza") + " %.0fs" % a_seg,
                     ("acepta" if b_ok else "rechaza") + " %.0fs" % r.segundos,
                     "" if a_ok == b_ok else marca))
            if a_ok != b_ok:
                print("      fichero: %s" % a_det[:100].replace("\n", " "))
                print("      sesion : %s" % r.error[:100].replace("\n", " "))
            # caso a caso: si la máquina se cae, lo medido queda
            _guardar(tabla)
    finally:
        s.cerrar()

    de_acuerdo, peligro, inocuo = _guardar(tabla)
    fs = sum(t["fichero_seg"] for t in tabla)
    ss = sum(t["sesion_seg"] for t in tabla)

    print("\n=== LA PUERTA ===\n")
    print("  de acuerdo                          %2d de %d" % (de_acuerdo, len(tabla)))
    print("  SESION acepta y FICHERO rechaza     %2d   <- la casilla que importa"
          % len(peligro))
    print("  sesion rechaza y fichero acepta     %2d   (incomodo, inocuo)"
          % len(inocuo))
    print("\n  segundos: fichero %.0f · sesion %.0f" % (fs, ss))

    print("\n=== VEREDICTO ===\n")
    if peligro:
        print("  NO PASA. La sesion acepta %d caso(s) que el fichero rechaza:"
              % len(peligro))
        for t in peligro[:4]:
            print("     %s" % t["consulta"][:70])
            print("        el fichero dijo: %s" % t["err_fichero"][:110])
        print("\n  El paso 2 NO se construye hasta entender esto.")
    else:
        print("  PASA en la mitad de seguridad: 0 casos aceptados por la")
        print("  sesion que el fichero rechace. Con la velocidad ya medida")
        print("  (0,02-0,63 s por tactica contra 15,5), la puerta del paso 1")
        print("  esta cerrada.")
        if inocuo:
            print("\n  %d caso(s) al reves —la sesion es MAS estricta—. No es un"
                  % len(inocuo))
            print("  riesgo, pero se mira: puede ser cabecera y no motor.")

    print("\n-> %s" % SALIDA)
    return 1 if peligro else 0


if __name__ == "__main__":
    raise SystemExit(main())
