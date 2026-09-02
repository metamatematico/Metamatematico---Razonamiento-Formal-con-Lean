# -*- coding: utf-8 -*-
"""LA LISTA: todos los teoremas y lemas de Mathlib, con su enunciado y su sitio.

POR QUE. El grafo cubre CONCEPTOS, no hechos. Medido: de los 169 nombres que
inyecta hoy, 3 son teoremas o lemas y 166 son tipos, estructuras y clases.
Es decir, le da a Lean los sustantivos —`Subgroup`, `AddCommGroup`— y no los
hechos que cierran una prueba.

Y ahi es justo donde el modelo alucina. De los 28 nombres que propuso de
memoria, 21 no existen: `tsum_geometric_two`, `Subgroup.isCyclic`,
`isOpen_union`. Miralos — son todos LEMAS. El modelo acierta razonablemente los
sustantivos e inventa los hechos, y el grafo hoy le ayuda en la mitad donde ya
iba bien.

QUE ES ESTO. La capa plana: nombre cualificado, enunciado, modulo, area y tipo
de declaracion, para cada teorema, lema, corolario e instancia de Mathlib. Se
construye una vez y se consulta muchas.

NO ES EL GRAFO, y no pretende serlo. El grafo son 298 nodos curados o
generados, con estructura categorica y aristas. Esta lista son ~174 000
entradas sin estructura. La idea es que la consulta ENCIENDA entradas de la
lista y que ese encendido despierte la rama correspondiente del grafo — cada
capa haciendo lo que sabe hacer.

    python scripts/construir_lista_lemas.py            # cuenta y muestra
    python scripts/construir_lista_lemas.py --escribir # y la guarda
"""
import argparse
import collections
import io
import json
import os
import re
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

MATH = "E:/Metamatematico/.lake/packages/mathlib/Mathlib"
SALIDA = "E:/Metamatematico/data/lemas_mathlib.jsonl"

#: Declaraciones que son HECHOS. `def`, `structure` y `class` son sustantivos y
#: ya los cubre el grafo; aqui interesa lo que se puede citar en una prueba.
HECHO = re.compile(
    r"^\s*(?:@\[[^\]]*\]\s*)?(?:private\s+|protected\s+|noncomputable\s+)*"
    r"(theorem|lemma|instance)\s+([A-Za-z_][\w.']*)?")
NS = re.compile(r"^\s*namespace\s+([A-Za-z_][\w.']*)")
END = re.compile(r"^\s*end\s+([A-Za-z_][\w.']*)")
IGNORAR = {"Tactic", "Util", "Testing", "Deprecated", "Mathport", "Init"}

#: FUERA LOS COMENTARIOS ANTES DE BUSCAR DECLARACIONES.
#:
#: Sin esto, una frase en prosa dentro de un docstring —«theorem the statement
#: is ...»— casa con el patron y entra en la lista un hecho llamado `the`. Y no
#: se queda ahi: el banco valida las citas CONTRA esta lista, asi que `the`,
#: `to`, `and` y `of` aparecieron como los lemas mas citados de Mathlib, por
#: delante de `sq_nonneg`. Una lista sucia contamina todo lo que la consulte.
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
    """Un registro por hecho, con lo que hace falta para poder recuperarlo."""
    filas = []
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
                m = HECHO.match(l)
                if not m or not m.group(2):
                    continue
                corto = m.group(2)
                largo = ".".join(pila + [corto]) if pila else corto
                # EL ENUNCIADO: desde el nombre hasta el `:=`, que puede
                # ocupar varias lineas. Se corta a 6 para no arrastrar pruebas.
                trozo = []
                for j in range(i, min(i + 6, len(ls))):
                    trozo.append(ls[j])
                    if ":=" in ls[j]:
                        break
                enunciado = " ".join(" ".join(trozo).split())
                enunciado = enunciado.split(":=")[0].strip()
                enunciado = re.sub(r"^\s*(?:@\[[^\]]*\]\s*)?"
                                   r"(?:private |protected |noncomputable )*"
                                   r"(?:theorem|lemma|instance)\s+\S*\s*", "",
                                   enunciado)
                filas.append({
                    "nombre": largo,
                    "corto": corto,
                    "tipo": m.group(1),
                    "enunciado": enunciado[:400],
                    "modulo": modulo,
                    "concepto": concepto,
                })
    return filas


def main(escribir):
    t0 = time.time()
    print("recorriendo Mathlib...")
    filas = recorrer()
    seg = time.time() - t0
    print("  %d hechos en %.0f s\n" % (len(filas), seg))
    if not filas:
        print("  ATENCION: ni uno — revisa MATH=%s" % MATH)
        return 1

    print("por tipo:", dict(collections.Counter(f["tipo"] for f in filas)))
    conceptos = collections.Counter(f["concepto"] for f in filas)
    print("conceptos distintos: %d\n" % len(conceptos))
    print("los que mas hechos tienen:")
    for c, k in conceptos.most_common(8):
        print("   %-34s %6d" % (c, k))

    print("\nejemplos:")
    for f in filas[:3]:
        print("   %-44s %s" % (f["nombre"][:42], f["enunciado"][:70]))

    sin_enunciado = sum(1 for f in filas if len(f["enunciado"]) < 5)
    print("\n  sin enunciado utilizable: %d (%.1f %%)"
          % (sin_enunciado, 100.0 * sin_enunciado / len(filas)))

    if not escribir:
        crudo = sum(len(json.dumps(f, ensure_ascii=False)) for f in filas[:500])
        print("\n  tamaño estimado: %.0f MB"
              % (crudo / 500 * len(filas) / 1e6))
        print("  (sin --escribir no se guarda nada)")
        return 0

    with io.open(SALIDA, "w", encoding="utf-8") as fh:
        for f in filas:
            fh.write(json.dumps(f, ensure_ascii=False) + "\n")
    print("\n  -> %s (%.0f MB)"
          % (SALIDA, os.path.getsize(SALIDA) / 1e6))
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--escribir", action="store_true")
    a = ap.parse_args()
    sys.exit(main(a.escribir))
