# -*- coding: utf-8 -*-
"""¿Sirve completar la cabecera de imports? Un banco que SI puede decidirlo.

POR QUE HACE FALTA OTRO BANCO
-----------------------------
`imports_del_grafo_contra_lean.py` midio el paso 3 y dio 18 de 20 contra 18
de 20: «inerte». Pero su propio informe traia la cautela que lo invalida como
prueba de ausencia:

    en 14 de los 20 casos el grafo no anade ni un modulo,
    o sea que las dos ramas son LA MISMA EJECUCION.

El test discriminante tenia n ~ 0. «Inerte» quedo sostenido como *no se midio
beneficio*, NO como *se demostro que no lo hay*. La causa es el corpus: los 20
casos salian de LeanWorkbook, que es casi todo desigualdades sobre los reales,
y el conjunto fijo —`Mathlib.Tactic` + `Data.Real.Basic` + `Data.Nat.Basic`—
ya las cubre. `Mathlib.Tactic` sola arrastra 2 972 modulos.

En produccion aparecio el caso que el banco no tenia:

    import Mathlib.Tactic.Ring          (y otros seis)
    obtain <s, b> := Module.Basis.exists_basis K V
    -> error: invalid binder annotation

El nombre era CORRECTO. Faltaba su modulo.

QUE MIDE ESTE BANCO
-------------------
Enunciados REALES de Mathlib, sacados del propio codigo fuente y por tanto
diversos de verdad, bajo tres cabeceras:

    fijo        Mathlib.Tactic + Data.Real.Basic + Data.Nat.Basic   <- EL NULO
    fijo+grafo  lo anterior mas lo que propone el paso 3
    fijo+regla4 lo anterior mas el modulo de cada nombre conocido que
                aparezca en el codigo y que la cabecera no alcance ya

Juez: Lean. El cuerpo es `sorry`, asi que solo se prueba el ENUNCIADO — es
exactamente lo que el paso 3 tiene que hacer posible.

EL ESTRATO, Y POR QUE SE INFORMA
--------------------------------
Antes de compilar nada se clasifica cada caso con el oraculo de alcance:

    estrato A   el conjunto fijo YA alcanza todo lo que el enunciado nombra
    estrato B   no lo alcanza

En el estrato A las tres ramas tienen que empatar; si no empatan, el
instrumento esta roto. El estrato B es donde se decide, y es justo el que el
banco anterior no tenia. La proporcion A/B sobre una muestra AL AZAR dice
cuanto importa esto en la practica, y esa proporcion se publica aunque salga
incomoda.

LA FIRMA DEL INSTRUMENTO ROTO. Si `fijo+regla4` no gana en NINGUN caso del
estrato B, o si alguna rama falla en el estrato A, no se ha medido el sistema:
se ha medido un error de montaje. El guion lo dice y no da nota.

LA PRIMERA CORRIDA · 19 de septiembre de 2026 · SIN NOTA
--------------------------------------------------------
22 casos (11 del estrato B + 11 controles del A), 66 compilados, ~18 min:

    rama            elabora   estrato A   estrato B
    fijo              5/22        5/11        0/11
    fijo+grafo        5/22        5/11        0/11
    fijo+regla4       8/22        5/11        3/11

La alarma de este guion salto y NO se dio nota, y tenia razon: el nulo solo
elabora 5 de 11 en el estrato A, que por construccion cubre entero. Pero el
motivo que la alarma supone —«enunciado mal recortado»— solo explica 3 de los
14 fallos. Mirados uno a uno:

    nombre relativo al namespace -> implicito automatico   6
    contexto mal recortado                                 3
    open de un namespace sin su modulo                     2
    otros                                                  2
    constante desconocida                                  1

LA FAMILIA GRANDE NO ES UN FALLO DEL RECORTE, ES DEL ORACULO. Dentro de
`namespace Foo`, el enunciado escribe `bar` y Lean resuelve `Foo.bar`. El
oraculo de alcance solo mira nombres CUALIFICADOS, asi que no pone
`Foo.bar` en `faltan` y la cabecera se queda sin su modulo. Y entonces Lean
no dice «unknown identifier»: AUTO-LIGA `bar` como implicito y falla mucho
despues con «Function expected at bar ... has type ?m.1». Un import que falta
disfrazado de error de tipos.

Es la misma familia que `_es_error_mecanico` ya se comio en `core.py`: creerse
la forma del mensaje en vez de preguntarle al indice.

QUE HACE FALTA ANTES DE VOLVER A CORRERLO
  1. que `nombres_en` resuelva tambien los nombres relativos al namespace
     vigente, no solo los que llevan punto;
  2. equilibrar `namespace`/`end` y tirar las lineas truncadas al capturar el
     contexto —3 casos se caen por un `end` sin nombre—;
  3. y solo entonces medir, con el estrato A limpio como puerta de validez.

LO UNICO QUE ESTA CORRIDA SI SOSTIENE, porque no depende del estrato A:
`fijo+grafo` dio EXACTAMENTE lo mismo que `fijo` en los 22 casos, y no añadio
ni un modulo en ninguno. Sobre enunciados reales de Mathlib —no las
desigualdades de LeanWorkbook— la mitad b del paso 3 sigue sin aparecer.

No gasta API. Solo Lean.

    python -m scripts.imports_que_discriminan            # en seco, gratis
    python -m scripts.imports_que_discriminan --ejecutar
"""
from __future__ import annotations

import argparse
import io
import json
import os
import random
import re
import subprocess
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

SALIDA = os.path.join(RAIZ, "data", "imports_que_discriminan.json")
MATHLIB = os.path.join(RAIZ, ".lake", "packages", "mathlib", "Mathlib")

#: El modelo nulo, identico al del banco anterior para que sean comparables.
FIJO = ["Mathlib.Tactic", "Mathlib.Data.Real.Basic", "Mathlib.Data.Nat.Basic"]

SEMILLA = 20260911
TOPE_SEG = 90

#: `theorem NOMBRE <binders> : <tipo> := by` en una sola pieza. Se exige que el
#: enunciado quepa en pocas lineas: los de veinte lineas traen `variable`s del
#: fichero que aqui no existen, y medirian el recorte, no la cabecera.
_TEOREMA = re.compile(
    r"^theorem\s+([A-Za-z_][\w'.]*)\s*(.*?)\s*:=\s*by\s*$",
    re.M | re.S)


def _areas() -> list:
    return sorted(d for d in os.listdir(MATHLIB)
                  if os.path.isdir(os.path.join(MATHLIB, d)))


#: Ordenes que declaran CONTEXTO y sin las cuales el enunciado no se sostiene.
_CONTEXTO = re.compile(
    r"^\s*(variable|universe|open|namespace|section|end|"
    r"noncomputable section|local notation|scoped notation|notation|"
    r"local infix|scoped infix|infix|local macro|macro_rules)\b")


def _contexto_hasta(texto: str, pos: int) -> list:
    """Las lineas de contexto vigentes en `pos`, con sus ambitos resueltos.

    LA PRIMERA VERSION DE ESTE GUION NO HACIA ESTO, y el banco entero midio
    otra cosa: de 9 enunciados que el conjunto fijo cubria ENTERO, elaboraba 1.
    Los ocho fallos no eran de imports —`Function expected at Simplex`,
    `Unknown identifier P.parts`, `unexpected token '|'`— sino de `variable`s,
    `open`s y notacion declarados en la cabecera del fichero de Mathlib y que
    el enunciado, sacado solo, no llevaba consigo.

    Un banco asi mide el recortador, no lo que dice medir.

    Los ambitos importan: una `variable` declarada dentro de una `section` que
    ya se cerro NO esta vigente. Se lleva una pila y se descarta lo que el
    `end` correspondiente saco de circulacion.
    """
    lineas = texto[:pos].splitlines()
    pila = [[]]                      # cada ambito, con sus lineas de contexto
    for l in lineas:
        if not _CONTEXTO.match(l):
            continue
        cab = l.split()[0]
        if cab in ("namespace", "section") or l.strip() == "noncomputable section":
            pila.append([l.rstrip()])
        elif cab == "end":
            if len(pila) > 1:
                pila.pop()
        else:
            pila[-1].append(l.rstrip())
    return [l for ambito in pila for l in ambito]


def cosechar(n_por_area: int = 2, semilla: int = SEMILLA) -> list:
    """Enunciados reales del fuente de Mathlib, repartidos por area.

    Se toma el fichero al azar dentro de cada area y el primer teorema que
    cumple las condiciones, para no elegir a dedo. Cada caso se lleva CONSIGO
    el contexto vigente del fichero: sin el, el enunciado no elabora por
    razones que no tienen nada que ver con los imports.
    """
    rnd = random.Random(semilla)
    casos = []
    for area in _areas():
        base = os.path.join(MATHLIB, area)
        ficheros = []
        for r, _d, fs in os.walk(base):
            ficheros += [os.path.join(r, f) for f in fs if f.endswith(".lean")]
        if not ficheros:
            continue
        rnd.shuffle(ficheros)
        puestos = 0
        for ruta in ficheros:
            if puestos >= n_por_area:
                break
            try:
                txt = io.open(ruta, encoding="utf-8").read()
            except OSError:
                continue
            for m in _TEOREMA.finditer(txt):
                cuerpo = m.group(2)
                if (not cuerpo or len(cuerpo) > 220 or "\n\n" in cuerpo
                        or cuerpo.count("\n") > 3 or "⦃" in cuerpo):
                    continue
                if ":" not in cuerpo:
                    continue
                rel = os.path.relpath(ruta, os.path.dirname(MATHLIB))
                modulo = rel[:-5].replace(os.sep, ".")
                casos.append({"area": area, "modulo": modulo,
                              "nombre": m.group(1), "cuerpo": cuerpo,
                              "contexto": _contexto_hasta(txt, m.start())})
                puestos += 1
                break
    return casos


def nombres_en(codigo: str) -> list:
    """Modulos de los identificadores conocidos que aparecen en el codigo.

    MIRA TAMBIEN LOS NOMBRES SIN PUNTO, y eso NO es un detalle.

    La primera version copiaba la regla del reparador —«solo los punteados»—,
    que alli es correcta porque REESCRIBE y un nombre suelto puede ser un
    binder local. Aqui no se reescribe nada: se CLASIFICA. Y con esa regla la
    clasificacion salia mal, no solo sesgada:

        SimpleGraph · GrothendieckTopology · IdentDistrib · EuclideanGeometry

    son los nombres que decidian esos enunciados, ninguno lleva punto, y los
    casos acabaron en el estrato A —«el fijo ya lo alcanza»— cuando el fijo no
    los alcanzaba. Con la estratificacion mal hecha, el banco entero no mide
    lo que dice.

    El filtro para los sueltos es deliberadamente estrecho: mayuscula inicial,
    tres letras o mas, y presente en el indice de Mathlib. `E`, `s`, `t` o `n`
    no pasan, y son los binders que de verdad aparecen.
    """
    from nucleo.lean import nombres as _nom
    _nom._cargar()
    fuera = []
    for m in _nom._IDENT_CODIGO.finditer(codigo):
        ident = m.group(1)
        raiz = ident.split(".")[0]
        if raiz in _nom._PALABRAS_LEAN:
            continue
        if "." not in ident and not (ident[:1].isupper() and len(ident) >= 3):
            continue
        if ident in _nom._NOMBRES:
            mod = _nom.modulo_de(ident)
            if mod and mod not in fuera:
                fuera.append(mod)
    return fuera


def _fuente(imports: list, caso: dict) -> str:
    """El fichero de prueba, CON el contexto vigente del fichero original.

    Sin el contexto esto media otra cosa: ver `_contexto_hasta`.
    """
    return ("\n".join("import " + i for i in imports)
            + "\n\n" + "\n".join(caso.get("contexto") or [])
            + "\n\ntheorem probe_del_banco " + caso["cuerpo"] + " := by sorry\n")


def corre(imports: list, caso: dict) -> tuple:
    """(elabora, segundos). `sorry` en el cuerpo: solo se prueba el enunciado."""
    ruta = os.path.join(RAIZ, "_banco_imports.lean")
    io.open(ruta, "w", encoding="utf-8").write(_fuente(imports, caso))
    t0 = time.time()
    try:
        p = subprocess.run(["lake", "env", "lean", ruta], cwd=RAIZ,
                           capture_output=True, text=True, timeout=TOPE_SEG,
                           encoding="utf-8", errors="replace")
        salida = (p.stdout or "") + (p.stderr or "")
        # `sorry` produce un AVISO, no un error: el enunciado elaboro.
        ok = p.returncode == 0 or ("declaration uses 'sorry'" in salida
                                   and "error:" not in salida)
    except subprocess.TimeoutExpired:
        ok, salida = False, "TIMEOUT"
    except Exception as e:                                     # noqa: BLE001
        ok, salida = False, "%s: %s" % (type(e).__name__, e)
    seg = time.time() - t0
    try:
        os.remove(ruta)
    except OSError:
        pass
    return ok, seg, salida[:400]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--ejecutar", action="store_true",
                    help="compila de verdad; sin esto solo clasifica (gratis)")
    ap.add_argument("--por-area", type=int, default=1)
    ap.add_argument("--tope-estrato", type=int, default=12,
                    help="maximo de casos por estrato al compilar. Cada "
                         "compilado son ~18 s: 62 y 62 no caben en tiempo")
    ap.add_argument("--balanceado", action="store_true",
                    help="compila solo el estrato B mas igual numero de "
                         "controles del A: la prevalencia sale de la muestra "
                         "al azar y el efecto, de este subconjunto")
    args = ap.parse_args()

    import warnings
    import logging
    warnings.filterwarnings("ignore")
    logging.disable(logging.WARNING)

    from nucleo.lean import alcance

    if not alcance.disponible():
        print("sin data/mathlib_imports.dot no se puede clasificar. Se aborta.")
        return 1

    casos = cosechar(args.por_area)
    print("enunciados cosechados del fuente de Mathlib: %d, de %d areas\n"
          % (len(casos), len({c["area"] for c in casos})))

    ya = alcance.alcanza(FIJO)
    print("el conjunto fijo alcanza %d modulos de %d\n"
          % (len(ya), alcance.cuantos()))

    # ── clasificacion por estrato, gratis ────────────────────────────────
    for c in casos:
        # EL CONTEXTO TAMBIEN NOMBRA COSAS. Un `open EuclideanGeometry` de la
        # cabecera del fichero falla con «unknown namespace» si su modulo no
        # esta importado, y ese fallo no es del enunciado. El fichero de
        # prueba lleva el contexto, asi que la clasificacion tiene que mirarlo.
        c["mods_nombres"] = nombres_en(
            "\n".join(c.get("contexto") or []) + "\n" + c["cuerpo"])
        c["faltan"] = [m for m in c["mods_nombres"] if m not in ya]
        c["estrato"] = "B" if c["faltan"] else "A"

    nA = sum(1 for c in casos if c["estrato"] == "A")
    nB = len(casos) - nA
    print("ESTRATO A  el conjunto fijo ya alcanza todo : %d" % nA)
    print("ESTRATO B  no lo alcanza (aqui se decide)   : %d" % nB)
    print("           %.0f %% de una muestra al azar\n"
          % (100.0 * nB / max(1, len(casos))))
    for c in casos:
        if c["estrato"] == "B":
            print("   %-22s %-46s faltan: %s"
                  % (c["area"], c["nombre"][:44], c["faltan"][:2]))

    # ── el subconjunto que se compila ────────────────────────────────────
    #
    # LA PREVALENCIA SALE DE LA MUESTRA AL AZAR; EL TAMANO DEL EFECTO, DE UN
    # SUBCONJUNTO BALANCEADO. Compilar los 203 al azar seria repetir el error
    # del banco anterior: 194 de ellos son empates por construccion —el fijo
    # ya alcanza todo— y gastarian 582 compilados para no decir nada. Se
    # compilan TODOS los del estrato B y otros tantos del A como control.
    #
    # Las dos cifras se informan por separado y NO se mezclan: la del estrato
    # B no es una tasa de exito del sistema, es el efecto alli donde la
    # cabecera decide.
    completo = casos
    if args.balanceado:
        rnd = random.Random(SEMILLA)
        soloA = [c for c in casos if c["estrato"] == "A"]
        soloB = [c for c in casos if c["estrato"] == "B"]
        rnd.shuffle(soloA)
        rnd.shuffle(soloB)
        k = min(args.tope_estrato, len(soloB), len(soloA))
        casos = soloB[:k] + soloA[:k]
        print("\nsubconjunto balanceado: %d del estrato B + %d controles del A"
              % (k, k))
        print("(la PREVALENCIA sale de los %d al azar; el EFECTO, de estos %d)"
              % (len(completo), len(casos)))

    if not args.ejecutar:
        print("\n(en seco. Con --ejecutar se compila con Lean, ~%d compilados)"
              % (len(casos) * 3))
        json.dump({"casos": casos, "estrato_A": nA, "estrato_B": nB,
                   "fijo": FIJO, "ejecutado": False},
                  io.open(SALIDA, "w", encoding="utf-8"), indent=1,
                  ensure_ascii=False)
        print("-> %s" % SALIDA)
        return 0

    # ── con Lean de juez ─────────────────────────────────────────────────
    from nucleo.graph.category import SkillCategory
    from nucleo.core import Nucleo
    n = Nucleo.__new__(Nucleo)
    n._graph = SkillCategory()
    Nucleo._load_foundational_skills(n)

    ramas = ["fijo", "fijo+grafo", "fijo+regla4"]
    res = {r: {"ok": 0, "n": 0, "seg": 0.0, "mods": 0} for r in ramas}
    print("\n%-22s %-30s %s" % ("area", "teorema", "  ".join(
        "%-12s" % r for r in ramas)))
    print("-" * 100)

    for c in casos:
        fila = {}
        for r in ramas:
            if r == "fijo":
                imports = list(FIJO)
            elif r == "fijo+grafo":
                try:
                    ms = Nucleo._match_skills_to_query(n, c["nombre"], n._graph)
                    ids = [x if isinstance(x, str) else getattr(x, "id", "")
                           for x in ms]
                    prop = Nucleo._modulos_mathlib(n, {"matched_skills": ids})
                except Exception:                              # noqa: BLE001
                    prop = []
                imports = list(FIJO) + [m for m in prop if m not in FIJO]
            else:
                imports = list(FIJO) + list(c["faltan"])
            ok, seg, err = corre(imports, c)
            d = res[r]
            d["ok"] += 1 if ok else 0
            d["n"] += 1
            d["seg"] += seg
            d["mods"] += len(imports)
            fila[r] = {"ok": ok, "seg": round(seg, 1), "mods": len(imports),
                       "err": "" if ok else err}
        c["resultado"] = fila
        print("%-22s %-30s %s" % (
            c["area"][:22], c["nombre"][:30],
            "  ".join("%-12s" % ("OK  %4.0fs" % fila[r]["seg"] if fila[r]["ok"]
                                 else "--  %4.0fs" % fila[r]["seg"])
                      for r in ramas)))

    print("\n=== RESUMEN ===\n")
    print("  %-14s %8s %10s %8s" % ("rama", "elabora", "segundos", "modulos"))
    for r in ramas:
        d = res[r]
        print("  %-14s %4d/%-3d %9.0f %8d"
              % (r, d["ok"], d["n"], d["seg"], d["mods"]))

    # ── lectura por estrato ──────────────────────────────────────────────
    print("\n=== POR ESTRATO ===\n")
    for est in ("A", "B"):
        sub = [c for c in casos if c["estrato"] == est]
        if not sub:
            continue
        print("  estrato %s (%d casos): %s" % (est, len(sub), "  ".join(
            "%s %d/%d" % (r, sum(1 for c in sub if c["resultado"][r]["ok"]),
                          len(sub)) for r in ramas)))

    # ── la firma del instrumento roto ────────────────────────────────────
    subA = [c for c in casos if c["estrato"] == "A"]
    subB = [c for c in casos if c["estrato"] == "B"]
    roto = []
    # LA COMPROBACION QUE FALTABA, y su falta invalido la primera corrida.
    #
    # Se pedia que las ramas COINCIDIERAN en el estrato A, y coincidian: las
    # tres fallaban igual, 1 de 9. Un nulo que no elabora lo que cubre entero
    # no esta midiendo cabeceras — esta midiendo el recortador. Los ocho
    # fallos eran `Function expected at Simplex`, `Unknown identifier
    # P.parts`, `unexpected token '|'`: variables, opens y notacion del
    # fichero de Mathlib que el enunciado, sacado solo, no llevaba consigo.
    #
    # El acuerdo entre ramas NO detecta eso. Hay que exigir que el nulo
    # ACIERTE donde por construccion tiene todo lo que hace falta.
    if subA:
        okA = sum(1 for c in subA if c["resultado"]["fijo"]["ok"])
        if okA < 0.7 * len(subA):
            roto.append(
                "el NULO solo elabora %d de %d en el estrato A, que por "
                "construccion cubre entero: los fallos no pueden ser de "
                "imports, son del enunciado mal recortado" % (okA, len(subA)))
    if subA and any(c["resultado"]["fijo"]["ok"] !=
                    c["resultado"]["fijo+regla4"]["ok"] for c in subA):
        roto.append("en el estrato A las ramas NO empatan: si el fijo ya "
                    "alcanza todo, completar no puede cambiar nada")
    if subB and all(c["resultado"]["fijo+regla4"]["ok"] <=
                    c["resultado"]["fijo"]["ok"] for c in subB):
        roto.append("en el estrato B completar no gana ni una vez, que es "
                    "justo lo que este banco se construyo para detectar")
    if roto:
        print("\n  INSTRUMENTO SOSPECHOSO — no se da nota:")
        for m in roto:
            print("    · %s" % m)
    else:
        g = res["fijo+regla4"]["ok"] - res["fijo"]["ok"]
        print("\n  VEREDICTO: completar la cabecera elabora %+d enunciados "
              "sobre el nulo" % g)
        if subB:
            gb = (sum(1 for c in subB if c["resultado"]["fijo+regla4"]["ok"])
                  - sum(1 for c in subB if c["resultado"]["fijo"]["ok"]))
            print("             y en el estrato B, donde se decide: %+d de %d"
                  % (gb, len(subB)))

    json.dump({"casos": casos, "resumen": res, "estrato_A": nA,
               "estrato_B": nB, "n_muestra_al_azar": len(completo),
               "prevalencia_B": round(100.0 * nB / max(1, len(completo)), 1),
               "balanceado": bool(args.balanceado),
               "fijo": FIJO, "semilla": SEMILLA,
               "ejecutado": True, "roto": roto},
              io.open(SALIDA, "w", encoding="utf-8"), indent=1,
              ensure_ascii=False)
    print("\n-> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
