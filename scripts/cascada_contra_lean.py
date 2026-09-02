# -*- coding: utf-8 -*-
"""La cascada, juzgada por Lean y no por un proxy de frecuencias.

El reordenamiento de la cascada se midio contando en que POSICION queda la
tactica que cierra cada prueba de Mathlib: 2,59 -> 1,29, un 50 % menos de
invocaciones. Pero eso es un proxy — supone que la tactica que Mathlib uso es
la que cerraria, y compara ordenes sobre esa suposicion.

Aqui el juez es Lean. Se cogen teoremas de Mathlib, se les quita la prueba y se
deja que `SolverCascade` intente cerrarlos de verdad. Lean dice si o no.

SIN API. Solo `lake env lean`, que es local.

COMO SE EVITA HACER TRAMPA. El fichero de Mathlib donde vive el teorema lo
tiene YA demostrado, asi que importarlo dejaria que `exact?` lo encontrase. Se
importa lo que ese fichero importa —su propia cabecera— y no el fichero mismo:
el contexto exacto que tenia el autor cuando lo demostro, sin la respuesta.

COMO SE SEPARA EL FALLO DE INFRAESTRUCTURA DEL RESULTADO. Un enunciado puede no
elaborar porque usa `variable`s declaradas en su fichero, y eso no es un fallo
de la cascada. Antes de probar tacticas se comprueba el teorema CON `sorry`: si
no compila, el caso se EXCLUYE y se cuenta aparte. Es la leccion de esta
sesion: cuatro instrumentos mios presentaron su propio fallo como resultado.

COMO SE COMPARA VIEJO CONTRA NUEVO SIN PAGAR EL DOBLE. Se corre una sola vez
con el orden nuevo y se anota QUE tactica cerro; despues se calcula, sin tocar
Lean, en que posicion habria estado esa misma tactica con el orden viejo.

    python scripts/cascada_contra_lean.py --n 30
"""
import argparse
import collections
import io
import json
import os
import random
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RAIZ = "E:/Metamatematico"
MATH = RAIZ + "/.lake/packages/mathlib/Mathlib"
SALIDA = RAIZ + "/data/cascada_contra_lean.json"
SEMILLA = 20260901
TIMEOUT = 180

TEO = re.compile(r"^\s*(?:@\[[^\]]*\]\s*)?(?:private\s+|protected\s+)?"
                 r"(?:theorem|lemma)\s+([A-Za-z_][\w.']*)(.*?):=\s*by\b(.*)$")
IMP = re.compile(r"^(?:public\s+|meta\s+|private\s+|protected\s+)*import\s+"
                 r"([A-Za-z_][\w.]*)", re.M)
PRIMERA = re.compile(r"^\s*([a-z_][A-Za-z0-9_]*)")
#: EL CONTEXTO DEL FICHERO, sin el cual el enunciado no elabora.
#:
#: La primera version copiaba solo los `import` y EXCLUIA 93 de 100
#: casos: los enunciados de Mathlib usan `variable`s, `open`s y secciones
#: declarados arriba en su propio fichero. Con 7 medidos y 3 cerrados no
#: se concluye nada — el instrumento se comia la medida entera.
CONTEXTO = re.compile(
    r"^(variable\b.*|open\b.*|universe\b.*|local\s+.*|"
    r"noncomputable\s+section.*|section\b.*)$", re.M)

#: La tabla vieja, para calcular el orden de antes sin volver a correr Lean.
VIEJA = {
    "algebra": "ring", "analysis": "norm_num", "category-theory": "simp",
    "combinatorics": "omega", "computation": "decide", "geometry": "norm_num",
    "logic": "tauto", "number-theory": "norm_num", "optimization": "linarith",
    "probability": "norm_num", "set-theory": "simp", "topology": "simp",
}


def _indent(l):
    return len(l) - len(l.lstrip())


def candidatos(area_de_dir, n):
    """Teoremas de una linea, con su cabecera de imports y su area."""
    fuera = []
    for raiz, _d, fs in os.walk(MATH):
        for f in fs:
            if not f.endswith(".lean"):
                continue
            rel = os.path.relpath(os.path.join(raiz, f), MATH).replace("\\", "/")
            area = area_de_dir.get(rel.split("/")[0])
            if not area:
                continue
            try:
                txt = io.open(os.path.join(raiz, f), encoding="utf-8",
                              errors="replace").read()
            except Exception:
                continue
            cabecera = [m for m in IMP.findall(txt[:8000])
                        if m.startswith("Mathlib")]
            if not cabecera:
                continue
            ls = txt.splitlines()
            for i, l in enumerate(ls):
                m = TEO.match(l)
                if not m:
                    continue
                sig, resto = m.group(2), m.group(3).strip()
                if not resto or not sig.strip() or ":" not in sig:
                    continue
                sig_next = ls[i + 1] if i + 1 < len(ls) else ""
                if sig_next.strip() and _indent(sig_next) > _indent(l):
                    continue
                p = PRIMERA.match(resto)
                if not p:
                    continue
                fuera.append({"nombre": m.group(1), "sig": sig.strip(),
                              "tactica_mathlib": p.group(1), "area": area,
                              "imports": cabecera[:8],
                              # solo lo declarado ANTES del teorema
                              "contexto": CONTEXTO.findall(
                                  "\n".join(ls[:i]))[-25:],
                              "fichero": rel})
    random.seed(SEMILLA)
    random.shuffle(fuera)
    return fuera[:n * 8]          # de sobra: muchos se caeran al elaborar


def corre(imports, sig, cuerpo, contexto=()):
    """True si Lean acepta. Devuelve tambien la salida, para diagnosticar."""
    ruta = RAIZ + "/_cascada_check.lean"
    src = ("\n".join("import " + i for i in imports)
           + "\n\n" + "\n".join(contexto)
           + "\n\ntheorem _probe_ %s := by\n  %s\n" % (sig, cuerpo))
    io.open(ruta, "w", encoding="utf-8").write(src)
    try:
        p = subprocess.run(["lake", "env", "lean", ruta], cwd=RAIZ,
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=TIMEOUT)
        salida = (p.stdout or "") + (p.stderr or "")
        return ("error" not in salida.lower()), salida
    except subprocess.TimeoutExpired:
        return False, "TIMEOUT"
    finally:
        if os.path.exists(ruta):
            os.remove(ruta)


def main(n):
    from nucleo.lean.solver_cascade import SOLVER_CASCADE, GoalAnalyzer
    from nucleo.multi_agent.colimit_agents import domain_tactic_order
    from scripts.tacticas_reales_mathlib import AREA

    an = GoalAnalyzer()
    solvers = [s for s, _ in SOLVER_CASCADE]
    print("buscando teoremas de una linea en Mathlib...")
    cands = candidatos(AREA, n)
    print("  %d candidatos; se probaran hasta %d validos\n" % (len(cands), n))

    filas = []
    excluidos = 0
    for c in cands:
        if len(filas) >= n:
            break
        # 1. ¿elabora el enunciado? Con `sorry`, que nunca falla por tactica.
        ok_sorry, _ = corre(c["imports"], c["sig"], "sorry", c["contexto"])
        if not ok_sorry:
            excluidos += 1
            continue
        # 2. la cascada, con el orden NUEVO.
        #
        # Y detras, las tacticas CON PREMISAS. La cascada desnuda cerraba el
        # 16 %, y de los 21 fallos OCHO usaban `simp` — que si ofrece. Mathlib
        # escribe `simp [foo, bar]`; sin poder citar un hecho, la cascada no
        # puede reproducir esas pruebas. Se cuentan aparte para saber cuanto
        # aportan de verdad.
        orden = [x for x, _ in an.prioritize(
            c["sig"], domain_order=domain_tactic_order(c["area"]))]
        n_desnudas = min(6, len(orden))
        orden = orden[:n_desnudas]
        try:
            from nucleo.lean.premisas import tacticas_con_premisas
            orden += [t for t, _ in tacticas_con_premisas(c["sig"], c["area"])]
        except Exception as e:
            print("   sin premisas: %s" % type(e).__name__)
        cerro, pos = None, None
        for i, tac in enumerate(orden, 1):
            ok, _ = corre(c["imports"], c["sig"], tac, c["contexto"])
            if ok:
                cerro, pos = tac, i
                break
        # 3. donde habria estado ESA tactica con el orden viejo, sin Lean
        pos_vieja = None
        if cerro:
            pri = []
            t = VIEJA.get(c["area"], "")
            if t in solvers:
                pri.append(t)
            for patron, tacticas in an.GOAL_PATTERNS:
                if re.search(patron, c["sig"]):
                    pri.extend(x for x in tacticas if x not in pri)
                    break
            viejo = [x for x in pri if x in solvers]
            viejo += [x for x in solvers if x not in viejo]
            pos_vieja = viejo.index(cerro) + 1
        filas.append({"nombre": c["nombre"], "area": c["area"],
                      "con_premisas": bool(cerro and "[" in cerro),
                      "n_desnudas": n_desnudas,
                      "fichero": c["fichero"],
                      "tactica_mathlib": c["tactica_mathlib"],
                      "cerro": cerro, "pos_nueva": pos, "pos_vieja": pos_vieja})
        print("  %-38s %-14s %s" % (
            c["nombre"][:36], c["area"],
            "%s en %d (antes %d)" % (cerro, pos, pos_vieja) if cerro
            else "no cerro en 6 intentos"))

    cerrados = [f for f in filas if f["cerro"]]
    con_p = [f for f in cerrados if f.get("con_premisas")]
    print("\n  de los que cerraron, lo hicieron CON PREMISAS: %d de %d"
          % (len(con_p), len(cerrados)))
    for f in con_p:
        print("     %-34s %s" % (f["nombre"][:32], f["cerro"][:70]))
    print("\n" + "=" * 66)
    print("  medidos      : %d   (excluidos por no elaborar: %d)"
          % (len(filas), excluidos))
    print("  los cierra   : %d de %d = %.0f %%"
          % (len(cerrados), len(filas),
             100.0 * len(cerrados) / max(1, len(filas))))
    if cerrados:
        pn = sum(f["pos_nueva"] for f in cerrados) / len(cerrados)
        pv = sum(f["pos_vieja"] for f in cerrados) / len(cerrados)
        print("\n  posicion media de la tactica que cerro, JUZGADO POR LEAN:")
        print("     orden viejo : %.2f" % pv)
        print("     orden nuevo : %.2f     (%.0f %% menos)"
              % (pn, 100.0 * (pv - pn) / pv if pv else 0))
        igual = sum(1 for f in cerrados
                    if f["cerro"] == f["tactica_mathlib"])
        print("\n  cerro con la MISMA tactica que uso Mathlib: %d de %d"
              % (igual, len(cerrados)))
        print("  (si es baja, el proxy de frecuencias no era tan buen juez)")
        print("\n  por area:")
        for a, g in sorted(collections.Counter(
                f["area"] for f in cerrados).items()):
            sub = [f for f in cerrados if f["area"] == a]
            print("     %-16s %2d casos · nueva %.2f · vieja %.2f"
                  % (a, g, sum(f["pos_nueva"] for f in sub) / g,
                     sum(f["pos_vieja"] for f in sub) / g))

    json.dump({"n": len(filas), "excluidos": excluidos, "filas": filas},
              io.open(SALIDA, "w", encoding="utf-8"), indent=1,
              ensure_ascii=False)
    print("\n-> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=30)
    a = ap.parse_args()
    sys.exit(main(a.n))
