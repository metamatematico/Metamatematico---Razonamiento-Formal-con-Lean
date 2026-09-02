# -*- coding: utf-8 -*-
"""EL BANCO: (enunciado, lemas que la prueba cita de verdad), de 29 750 pruebas.

POR QUE. Todo lo que se ha intentado en recuperacion fallo por la misma razon:
no habia con que medirlo. El descenso por pilares y los embeddings se juzgaron
contra MATH —matematica de concurso, juez equivocado— y contra el area de la
consulta, que es un proxy flojo.

LeanWorkbookProofs trae 29 750 pruebas Lean 4 REALES. Cada una dice que lemas
se citaron para cerrarla. Eso convierte la pregunta en medible:

    de los lemas que el sistema enciende, ¿cuantos cita la prueba de verdad?

Y es justo el hueco que se midio en el grafo: de los 169 nombres que inyecta,
3 son teoremas o lemas y 166 son tipos. Los 21 nombres que el modelo se
invento —`tsum_geometric_two`, `Subgroup.isCyclic`, `isOpen_union`— eran TODOS
lemas.

QUE SE EXTRAE DE CADA PRUEBA

    nl          el enunciado en lenguaje natural, del comentario de cabecera
    enunciado   el teorema Lean, hasta el `:=`
    lemas       los identificadores del CUERPO que existen en Mathlib

COMO SE EVITA CONTAR RUIDO. Un identificador solo cuenta como cita si aparece
en `data/lemas_mathlib.jsonl`, la lista de los 183 594 hechos reales. Asi se
descartan de un golpe las tacticas, las hipotesis locales (`ha`, `h₀`) y las
variables ligadas, sin necesidad de una lista negra que siempre se queda corta.

Y SE QUITAN LOS COMENTARIOS DEL CUERPO antes de buscar: las pruebas de
LeanWorkbook llevan dentro una explicacion en ingles con LaTeX, y ahi hay
palabras que parecen identificadores y no lo son.

No gasta API.

    python scripts/construir_banco_lemas.py --n 5000
"""
import argparse
import collections
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

LISTA = "E:/Metamatematico/data/lemas_mathlib.jsonl"
SALIDA = "E:/Metamatematico/data/banco_lemas.jsonl"
FUENTE = "E:/MetamatematicoDataSet/LeanWorkbookProofs"

COMENT = re.compile(r"/-.*?-/", re.S)
NL = re.compile(r"/-\s*(.*?)\s*-/", re.S)
TEOREMA = re.compile(r"^\s*theorem\s+(\S+)\s*(.*?):=\s*by\b", re.S | re.M)
IDENT = re.compile(r"\b([A-Za-z_][A-Za-z0-9_']*(?:\.[A-Za-z_][A-Za-z0-9_']*)*)\b")


def cargar_nombres():
    """Los nombres reales de Mathlib, cortos y cualificados."""
    cortos, largos = set(), set()
    for l in io.open(LISTA, encoding="utf-8"):
        d = json.loads(l)
        largos.add(d["nombre"])
        cortos.add(d["corto"])
    return cortos, largos


def _es_cita(x, cortos, largos):
    """¿Es este identificador un lema de Mathlib citado, o solo una palabra?

    «Existe en Mathlib» no basta como criterio. Con el salieron como lemas mas
    citados `linear` (35,9 % de las pruebas), `intro`, `apply`, `square`,
    `positive` y `property`: unas son tacticas y otras son palabras inglesas
    que coinciden con algun nombre corto suelto del fuente.

    El discriminador es la CONVENCION DE MATHLIB, que es estable y explicita:
    un lema o teorema lleva guion bajo —`sq_nonneg`, `mul_nonneg`,
    `div_le_div_iff`— o va cualificado con su namespace —`Real.sq_sqrt`—.
    Ninguna tactica ni palabra suelta cumple eso.

    Pierde los pocos lemas de una sola palabra sin namespace, y se acepta: mas
    vale un banco limpio y algo corto que uno grande y sucio, porque el banco
    es el juez de todo lo que venga despues.
    """
    if "." in x:
        return x in largos
    return "_" in x and x in cortos


def main(n_max):
    if not os.path.exists(LISTA):
        print("falta %s — corre antes construir_lista_lemas.py --escribir" % LISTA)
        return 1
    from datasets import load_from_disk

    print("cargando la lista de hechos...")
    cortos, largos = cargar_nombres()
    print("  %d nombres cortos, %d cualificados" % (len(cortos), len(largos)))

    d = load_from_disk(FUENTE)
    total = min(n_max, len(d))
    print("  %d pruebas de %d\n" % (total, len(d)))

    filas = []
    sin_cita = sin_nl = 0
    hist = collections.Counter()
    for r in d.select(range(total)):
        p = r["full_proof"]
        m = TEOREMA.search(p)
        if not m:
            continue
        enunciado = " ".join(m.group(2).split())
        cabeza = p[:m.start()]
        mnl = NL.search(cabeza)
        nl = " ".join(mnl.group(1).split()) if mnl else ""
        if not nl:
            sin_nl += 1
        cuerpo = COMENT.sub(" ", p[m.end():])
        citas = set()
        for mm in IDENT.finditer(cuerpo):
            x = mm.group(1)
            if not _es_cita(x, cortos, largos):
                continue
            citas.add(x)
        if not citas:
            sin_cita += 1
            continue
        hist[min(len(citas), 10)] += 1
        filas.append({"id": r["problem_id"], "nl": nl[:600],
                      "enunciado": enunciado[:400],
                      "lemas": sorted(citas)})

    print("=== BANCO ===\n")
    print("  pruebas con al menos una cita : %d de %d" % (len(filas), total))
    print("  sin ninguna cita utilizable   : %d" % sin_cita)
    print("  sin enunciado en lenguaje nat.: %d" % sin_nl)
    if filas:
        med = sum(len(f["lemas"]) for f in filas) / len(filas)
        print("  lemas citados por prueba      : %.1f de media" % med)
        print("\n  reparto (lemas por prueba):")
        for k in sorted(hist):
            print("     %2s%s %s" % (k, "+" if k == 10 else " ",
                                     "#" * (60 * hist[k] // max(hist.values()))))
        cuenta = collections.Counter(x for f in filas for x in f["lemas"])
        print("\n  los mas citados — ESTE ES EL MODELO NULO A BATIR:")
        for k, v in cuenta.most_common(10):
            print("     %-30s %5d  (%.1f %% de las pruebas)"
                  % (k, v, 100.0 * v / len(filas)))
        print("\n  lemas distintos citados en total: %d" % len(cuenta))
        print("  citados una sola vez            : %d (%.0f %%)"
              % (sum(1 for v in cuenta.values() if v == 1),
                 100.0 * sum(1 for v in cuenta.values() if v == 1) / len(cuenta)))
        print("\n  ejemplo:")
        f = filas[0]
        print("     nl    : %s" % f["nl"][:88])
        print("     lemas : %s" % ", ".join(f["lemas"][:8]))

    with io.open(SALIDA, "w", encoding="utf-8") as fh:
        for f in filas:
            fh.write(json.dumps(f, ensure_ascii=False) + "\n")
    print("\n  -> %s (%.1f MB)" % (SALIDA, os.path.getsize(SALIDA) / 1e6))
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=30000)
    a = ap.parse_args()
    sys.exit(main(a.n))
