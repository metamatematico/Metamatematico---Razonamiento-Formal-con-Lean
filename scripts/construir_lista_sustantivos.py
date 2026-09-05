# -*- coding: utf-8 -*-
"""LA OTRA MITAD: los sustantivos de Mathlib —def, structure, class, abbrev.

POR QUE EXISTE ESTE FICHERO
---------------------------
`construir_lista_lemas.py` se escribio sobre esta observacion, y es correcta:

    «de los 169 nombres que el grafo inyecta, 3 son teoremas o lemas y 166 son
     tipos, estructuras y clases. Le da a Lean los SUSTANTIVOS y no los hechos.»

De ahi salio la lista de 183 433 hechos, para cubrir la mitad que faltaba. Pero
la justificacion de dejar fuera los sustantivos decia:

    «`def`, `structure` y `class` son sustantivos y YA LOS CUBRE EL GRAFO»

y esa parte NO se comprobo. Contados sobre el fuente de Mathlib:

    def         29 883        class        1 845
    abbrev       2 949        structure    1 490
    inductive      300
    ------------------------------------------
    TOTAL       36 467 sustantivos

El grafo inyecta 166. Cubre el 0,45 % de lo que la frase afirma cubrir.

Y el hueco cae justo donde el reparto de trabajo dice que el grafo aporta: el
modelo acierta razonablemente los sustantivos e inventa los hechos —de los 28
nombres que propuso de memoria, los 21 inexistentes eran TODOS lemas—, asi que
la capa de sustantivos es la que sostiene la mitad buena del modelo. Estaba al
0,45 %.

LA DIFERENCIA CON LOS NOMBRES GENERADOS, Y ES LA IMPORTANTE
-----------------------------------------------------------
Los 125 nodos generados proponen 447 identificadores DEDUCIDOS de la ruta del
modulo, y 95 no existen en Mathlib (§7.7): el filtro pedia CamelCase, que deja
pasar `Basic` —un fichero— igual que `Polynomial` —un tipo—. La forma no
distingue.

Aqui los nombres se LEEN DE LA DECLARACION: si el fuente dice `structure Foo`,
`Foo` existe. Es la misma diferencia que hay entre deducir y comprobar, y es la
razon de que esta lista pueda inyectarse y aquellos nombres no.

Aun asi se verifica una muestra con `#check` antes de dar la lista por buena
—`--verificar`—, porque «leido del fuente» y «existe en el entorno instalado»
no son lo mismo: un `private def` no se exporta, y un nombre dentro de una
seccion `variable` puede cualificarse distinto.

    python scripts/construir_lista_sustantivos.py             # cuenta y muestra
    python scripts/construir_lista_sustantivos.py --escribir  # y la guarda
    python scripts/construir_lista_sustantivos.py --verificar 60
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
import time

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RAIZ = "E:/Metamatematico"
MATH = RAIZ + "/.lake/packages/mathlib/Mathlib"
SALIDA = RAIZ + "/data/sustantivos_mathlib.jsonl"

#: Declaraciones que son SUSTANTIVOS: nombran una cosa, no afirman un hecho.
#:
#: `instance` NO entra: ya esta en la lista de hechos, y ahi es donde sirve
#: —una instancia se cita en una prueba—. Duplicarla aqui haria que las dos
#: listas se pisaran al medir cobertura.
SUSTANTIVO = re.compile(
    r"^\s*(?:@\[[^\]]*\]\s*)?(?:private\s+|protected\s+|noncomputable\s+)*"
    r"(def|structure|class|abbrev|inductive)\s+([A-Za-z_][\w.']*)")

#: `private` no se exporta fuera de su fichero, asi que ofrecerlo al modelo es
#: ofrecerle un nombre que no podra usar. Se detecta aparte del patron para
#: poder contarlo en vez de perderlo en silencio.
PRIVADO = re.compile(r"^\s*(?:@\[[^\]]*\]\s*)?private\s")

NS = re.compile(r"^\s*namespace\s+([A-Za-z_][\w.']*)")
END = re.compile(r"^\s*end\s+([A-Za-z_][\w.']*)")
IGNORAR = {"Tactic", "Util", "Testing", "Deprecated", "Mathport", "Init"}

#: Misma leccion que en la lista de hechos: sin quitar los comentarios, la
#: prosa de un docstring entra como declaracion. Alli produjo `the` como el
#: lema mas citado de Mathlib.
BLOQUE = re.compile(r"/-.*?-/", re.S)
LINEA = re.compile(r"--[^\n]*")


def _sin_comentarios(txt):
    """Vacia los comentarios CONSERVANDO los saltos de linea.

    Se conservan porque el recorrido es por lineas y lleva la pila de
    `namespace`: si se colapsan, los nombres cualificados salen mal.
    """
    def _blanquear(m):
        return "".join(c if c == "\n" else " " for c in m.group(0))
    return LINEA.sub(" ", BLOQUE.sub(_blanquear, txt))


def recorrer():
    """Un registro por sustantivo, con lo que hace falta para recuperarlo."""
    filas = []
    privados = 0
    for raiz, _d, fs in os.walk(MATH):
        for f in fs:
            if not f.endswith(".lean"):
                continue
            rel = os.path.relpath(os.path.join(raiz, f), MATH).replace("\\", "/")
            partes = rel[:-5].split("/")
            if partes[0] in IGNORAR:
                continue
            try:
                ls = _sin_comentarios(
                    io.open(os.path.join(raiz, f), encoding="utf-8",
                            errors="replace").read()).splitlines()
            except Exception:
                continue
            modulo = "Mathlib." + ".".join(partes)
            concepto = ".".join(partes[:2])
            pila = []
            for i, l in enumerate(ls):
                m = NS.match(l)
                if m:
                    pila.append(m.group(1))
                    continue
                m = END.match(l)
                if m:
                    if pila and pila[-1] == m.group(1):
                        pila.pop()
                    continue
                m = SUSTANTIVO.match(l)
                if not m or not m.group(2):
                    continue
                if PRIVADO.match(l):
                    privados += 1
                    continue
                corto = m.group(2)
                largo = ".".join(pila + [corto]) if pila else corto

                # LA FIRMA: desde el nombre hasta `:=` o `where`, que es donde
                # empieza el cuerpo. Se corta a 6 lineas para no arrastrar la
                # definicion entera.
                trozo = []
                for j in range(i, min(i + 6, len(ls))):
                    trozo.append(ls[j])
                    if ":=" in ls[j] or re.search(r"\bwhere\b", ls[j]):
                        break
                firma = " ".join(" ".join(trozo).split())
                firma = re.split(r":=|\bwhere\b", firma)[0].strip()
                firma = re.sub(r"^\s*(?:@\[[^\]]*\]\s*)?"
                               r"(?:private |protected |noncomputable )*"
                               r"(?:def|structure|class|abbrev|inductive)\s+\S*\s*",
                               "", firma)
                filas.append({
                    "nombre": largo,
                    "corto": corto,
                    "tipo": m.group(1),
                    "firma": firma[:400],
                    "modulo": modulo,
                    "concepto": concepto,
                })
    return filas, privados


def verificar(filas, n, semilla=20260904):
    """`#check` sobre una muestra. Existe porque leer del fuente NO basta.

    §7.7 de este proyecto: 95 de 447 nombres deducidos de la ruta no existian.
    Aqui los nombres se leen de la declaracion, que es otra cosa — pero
    «declarado en el fuente» y «accesible en el entorno» tampoco coinciden
    siempre. Se comprueba en vez de suponerlo.
    """
    random.Random(semilla).shuffle(filas)
    muestra = filas[:n]
    src = "import Mathlib\n" + "\n".join(
        "#check @%s" % r["nombre"] for r in muestra)
    ruta = RAIZ + "/_sustantivos_check.lean"
    io.open(ruta, "w", encoding="utf-8").write(src)
    t0 = time.time()
    try:
        p = subprocess.run(["lake", "env", "lean", ruta], cwd=RAIZ,
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=1800)
        salida = (p.stdout or "") + (p.stderr or "")
    except Exception as e:                       # noqa: BLE001
        return None, "no se pudo correr Lean: %s" % type(e).__name__
    finally:
        try:
            os.remove(ruta)
        except OSError:
            pass
    malos = set(re.findall(r"unknown (?:identifier|constant) '([^']+)'", salida))
    return {"muestra": len(muestra), "no_existen": len(malos),
            "existen": len(muestra) - len(malos),
            "ejemplos_malos": sorted(malos)[:10],
            "seg": round(time.time() - t0, 1)}, None


def main(a):
    t0 = time.time()
    filas, privados = recorrer()
    tipos = collections.Counter(f["tipo"] for f in filas)
    conc = collections.Counter(f["concepto"] for f in filas)

    print("")
    print("  SUSTANTIVOS DE MATHLIB           %7d" % len(filas))
    for k, v in tipos.most_common():
        print("     %-10s                  %7d" % (k, v))
    print("     (private, descartados)       %7d" % privados)
    print("")
    print("  conceptos distintos              %7d" % len(conc))
    print("  sin firma utilizable             %7d"
          % sum(1 for f in filas if not f["firma"]))
    print("  segundos                         %7.1f" % (time.time() - t0))
    print("")
    print("  los 10 conceptos con mas sustantivos:")
    for k, v in conc.most_common(10):
        print("     %-34s %6d" % (k, v))

    # LA COMPARACION QUE MOTIVA LA LISTA
    try:
        from nucleo.graph.interpretacion import nombres_de_trabajo
        from nucleo.core import Nucleo
        from nucleo.graph.category import SkillCategory
        n = Nucleo.__new__(Nucleo)
        n._graph = SkillCategory()
        Nucleo._load_foundational_skills(n)
        del_grafo = set()
        for sid in n._graph.skill_ids:
            for p in re.split(r"[,+]", nombres_de_trabajo(sid) or ""):
                if p.strip():
                    del_grafo.add(p.strip())
        print("")
        print("  el grafo inyecta hoy             %7d nombres" % len(del_grafo))
        print("  cobertura sobre los sustantivos  %7.2f %%"
              % (100.0 * len(del_grafo) / max(len(filas), 1)))
    except Exception as e:                       # noqa: BLE001
        print("  (sin comparacion con el grafo: %s)" % type(e).__name__)

    if a.verificar:
        print("")
        print("  verificando %d con #check (tarda)..." % a.verificar)
        r, err = verificar(list(filas), a.verificar)
        if err:
            print("     %s" % err)
        else:
            print("     existen      %d de %d  (%.1f %%)"
                  % (r["existen"], r["muestra"],
                     100.0 * r["existen"] / max(r["muestra"], 1)))
            print("     no existen   %d" % r["no_existen"])
            if r["ejemplos_malos"]:
                print("     ejemplos:    %s" % ", ".join(r["ejemplos_malos"]))
            print("     %.1f s" % r["seg"])

    if a.escribir:
        with io.open(SALIDA, "w", encoding="utf-8") as fh:
            for f in filas:
                fh.write(json.dumps(f, ensure_ascii=False) + "\n")
        print("")
        print("  -> %s" % SALIDA)
    else:
        print("")
        print("  (no escrito; usa --escribir)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--escribir", action="store_true")
    ap.add_argument("--verificar", type=int, default=0,
                    help="comprueba N nombres al azar con #check")
    main(ap.parse_args())
