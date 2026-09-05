# -*- coding: utf-8 -*-
"""Las tres politicas de ranking, sobre los dos bancos, con sus modelos nulos.

POR QUE EXISTE
--------------
Al normalizar el emparejador aparecieron tres politicas posibles y NINGUNA
domina a las otras: cada una gana en una metrica y pierde en otra. Elegir «la
de los numeros mas altos» mirando primero los resultados y decidiendo despues
el objetivo es exactamente el error que costo la cifra de portada de este
proyecto (§12.2 del reporte): comparar variantes de tu propia idea y quedarte
con la ganadora no es una medicion, es una seleccion.

Este script no elige. Barre las tres politicas sobre los DOS bancos a la vez,
imprime las cuatro metricas con sus modelos nulos, y marca la frontera de
Pareto — que es el conjunto de opciones defendibles. Elegir dentro de esa
frontera exige decir QUE metrica es el objetivo, y eso se decide antes de
mirar, no despues.

LAS CUATRO METRICAS Y POR QUE NO SON INTERCAMBIABLES
----------------------------------------------------
  precision   de los nombres que el grafo inyecta, cuantos se usan de verdad.
              Protege el prompt del ruido.
  cobertura   de los nombres que hacian falta, cuantos ofrecio el grafo.
              Es lo que evita una formalizacion fallida.
  silencio    consultas donde el grafo no activa NADA. Con silencio el grafo
              no actua, ni bien ni mal.
  punteria    la 1a skill activada, ¿es del area correcta? Manda sobre el cono
              que se recorre despues.

No gasta API.
"""
import argparse
import io
import json
import os
import random
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SALIDA = "E:/Metamatematico/data/politica_emparejador.json"
PROOFNET = "E:/MetamatematicoDataSet/ProofNet/ProofNet-main/benchmark/%s.jsonl"

POLITICAS = ("plano", "puerta", "concepto")


def _grafo():
    from nucleo.core import Nucleo
    from nucleo.graph.category import SkillCategory
    n = Nucleo.__new__(Nucleo)
    n._graph = SkillCategory()
    Nucleo._load_foundational_skills(n)
    return n, n._graph


def _proofnet():
    recs = []
    for split in ("test", "valid"):
        try:
            with io.open(PROOFNET % split, encoding="utf-8") as fh:
                for l in fh:
                    if l.strip():
                        recs.append(json.loads(l))
        except OSError:
            pass
    return recs


def medir_proofnet(n, g, k=6):
    """precision y cobertura de los nombres inyectados, y su nulo."""
    from scripts.recuperacion_contra_proofnet import (
        nombres_de_oro, _norm, IDENT)          # reutiliza el instrumento
    from nucleo.core import Nucleo
    from nucleo.graph.interpretacion import nombres_de_trabajo
    import collections

    recs = _proofnet()
    if not recs:
        return None

    def ofrecidos(skills):
        out, llenas = set(), 0
        for s in skills:
            if llenas >= k:
                break
            piezas = [p.strip() for p in
                      re.split(r"[,+]", nombres_de_trabajo(s) or "") if p.strip()]
            if not piezas:
                continue
            llenas += 1
            for pieza in piezas:
                out.add(_norm(pieza))
                out.add(_norm(pieza.split(".")[0]))
        return out

    # MODELO NULO: los nombres mas comunes del grafo, sin mirar la consulta.
    todos = collections.Counter()
    for s in g.skill_ids:
        for p in re.split(r"[,+]", nombres_de_trabajo(s) or ""):
            if p.strip():
                todos[_norm(p.strip())] += 1
    nulo = {n_ for n_, _ in todos.most_common(k * 3)}

    acc = {"usados": 0, "ofrecidos": 0, "necesarios": 0, "cubiertos": 0,
           "ofrece_algo": 0}
    accn = dict(acc)
    for r in recs:
        oro = nombres_de_oro(r.get("formal_statement") or "")
        if not oro:
            continue
        for nombre, ofr in (("g", ofrecidos(
                Nucleo._match_skills_to_query(n, r.get("nl_statement") or "", g))),
                            ("n", nulo)):
            d = acc if nombre == "g" else accn
            d["ofrecidos"] += len(ofr)
            d["usados"] += len(ofr & oro)
            d["necesarios"] += len(oro)
            d["cubiertos"] += len(ofr & oro)
            d["ofrece_algo"] += int(bool(ofr))

    def pc(d):
        return (100.0 * d["usados"] / max(d["ofrecidos"], 1),
                100.0 * d["cubiertos"] / max(d["necesarios"], 1),
                d["ofrece_algo"])
    p, c, o = pc(acc)
    pn, cn, _ = pc(accn)
    return {"precision": p, "cobertura": c, "ofrece_algo": o,
            "volumen": acc["ofrecidos"],
            "n_casos": sum(1 for r in recs
                           if nombres_de_oro(r.get("formal_statement") or "")),
            "nulo_precision": pn, "nulo_cobertura": cn}


def medir_enganche(n, g, muestra=3000, semilla=20260901):
    """silencio y punteria, sobre el mismo banco que medir_emparejamiento."""
    from nucleo.core import Nucleo
    from scripts.medir_emparejamiento import cargar, MAPA
    filas = cargar()
    random.seed(semilla)
    filas = random.sample(filas, min(muestra, len(filas)))

    sin, ok, mal = 0, 0, 0
    for texto, cat in filas:
        # MISMO mapa etiqueta-del-dataset -> categoria que usa el medidor
        # original. Sin el, las dos cifras no serian comparables.
        esperada = MAPA.get(cat, "")
        m = Nucleo._match_skills_to_query(n, texto, g)
        if not m:
            sin += 1
            continue
        propia = (g.get_skill(m[0]).metadata or {}).get("category") or ""
        if not esperada or not propia:
            continue
        if propia == esperada:
            ok += 1
        else:
            mal += 1
    total = len(filas)
    return {"muestra": total, "silencio": 100.0 * sin / max(total, 1),
            "punteria": 100.0 * ok / max(ok + mal, 1), "ok": ok, "mal": mal,
            # NULO del silencio: un emparejador que responde siempre da 0 %,
            # asi que el silencio no tiene nulo util. El de la punteria si:
            # el area mayoritaria del banco.
            }


def frontera(filas):
    """Las politicas NO dominadas: nadie las supera en TODO a la vez."""
    metricas = ("precision", "cobertura", "punteria", "no_silencio")
    out = []
    for a in filas:
        dominada = any(
            b is not a
            and all(b[m] >= a[m] for m in metricas)
            and any(b[m] > a[m] for m in metricas)
            for b in filas)
        if not dominada:
            out.append(a["politica"])
    return out


def main(k):
    import nucleo.core as core
    filas = []
    for pol in POLITICAS:
        core.POLITICA_RANKING = pol
        n, g = _grafo()
        pn = medir_proofnet(n, g, k=k)
        en = medir_enganche(n, g)
        filas.append({
            "politica": pol,
            "precision": pn["precision"], "cobertura": pn["cobertura"],
            "ofrece_algo": pn["ofrece_algo"], "n_casos": pn["n_casos"],
            "silencio": en["silencio"], "no_silencio": 100.0 - en["silencio"],
            "punteria": en["punteria"],
            "nulo_precision": pn["nulo_precision"],
            "nulo_cobertura": pn["nulo_cobertura"],
        })

    print("\n  BANCO 1 · ProofNet, %d ejercicios con formalizacion de oro"
          % filas[0]["n_casos"])
    print("  BANCO 2 · %d consultas del banco de enganche\n" % 3000)
    print("  %-10s %10s %10s %10s %10s" %
          ("politica", "precision", "cobertura", "silencio", "punteria"))
    print("  " + "-" * 54)
    for f in filas:
        print("  %-10s %9.1f%% %9.1f%% %9.1f%% %9.1f%%" %
              (f["politica"], f["precision"], f["cobertura"],
               f["silencio"], f["punteria"]))
    print("  " + "-" * 54)
    print("  %-10s %9.1f%% %9.1f%% %10s %10s" %
          ("MODELO NULO", filas[0]["nulo_precision"],
           filas[0]["nulo_cobertura"], "-", "-"))

    fr = frontera(filas)
    print("\n  FRONTERA DE PARETO: %s" % ", ".join(fr))
    if len(fr) > 1:
        print("  Ninguna domina. Elegir entre ellas EXIGE decir cual de las")
        print("  cuatro metricas es el objetivo, y eso se decide antes de")
        print("  mirar la tabla. Ver §12.2 del reporte.")
    else:
        print("  %s domina a las demas: es mejor o igual en las cuatro." % fr[0])

    with io.open(SALIDA, "w", encoding="utf-8") as fh:
        json.dump({"k": k, "filas": filas, "frontera": fr}, fh,
                  indent=2, ensure_ascii=False)
    print("\n-> %s" % SALIDA)




# ═══════════════════════════════════════════════════════════════════════════
# LA COMPARACION A VOLUMEN IGUALADO
# ═══════════════════════════════════════════════════════════════════════════
#
# POR QUE HACE FALTA. `plano` salia mas preciso que `concepto` —16,2 % frente
# a 9,5 %— y la lectura obvia era «acierta mejor los nombres». Es falsa: solo
# 2,02 CONCEPTOs sobreviven a su corte de top-10 frente a 5,87 en `concepto`,
# y los MODULO no tienen ni un nombre. O sea que `plano` no acierta mas: OFRECE
# MENOS, y la precision sube porque baja el denominador.
#
# Comparar precisiones a volumenes distintos no dice cual es mejor politica.
# La comparacion limpia barre `k` —las plazas con nombres— y enfrenta las
# curvas a IGUAL numero de nombres ofrecidos.


def curva(k_max=14):
    import nucleo.core as core
    out = {}
    for pol in POLITICAS:
        core.POLITICA_RANKING = pol
        n, g = _grafo()
        puntos = []
        for k in range(1, k_max + 1):
            r = medir_proofnet(n, g, k=k)
            puntos.append({"k": k, "volumen": r["volumen"],
                           "precision": r["precision"],
                           "cobertura": r["cobertura"]})
        out[pol] = puntos
    return out


def main_curva(k_max):
    c = curva(k_max)
    print("")
    print("  PRECISION Y COBERTURA EN FUNCION DEL VOLUMEN OFRECIDO")
    print("  (volumen = nombres inyectados sobre los 352 ejercicios)")
    print("")
    for pol, pts in c.items():
        print("  %s" % pol.upper())
        print("     %4s %9s %11s %11s"
              % ("k", "volumen", "precision", "cobertura"))
        visto = set()
        for q in pts:
            if q["volumen"] in visto:      # el corte a top-10 ya saturo
                continue
            visto.add(q["volumen"])
            print("     %4d %9d %10.1f%% %10.1f%%"
                  % (q["k"], q["volumen"], q["precision"], q["cobertura"]))
        print("")

    print("  A IGUAL VOLUMEN (el punto mas cercano de cada politica):")
    print("")
    print("     %-9s %9s %11s %11s"
          % ("politica", "volumen", "precision", "cobertura"))
    for objetivo in (1500, 2500, 3500, 5000):
        print("     --- objetivo ~%d nombres ---" % objetivo)
        for pol, pts in c.items():
            mejor = min(pts, key=lambda x: abs(x["volumen"] - objetivo))
            if abs(mejor["volumen"] - objetivo) > objetivo * 0.4:
                print("     %-9s %9s   (no llega a ese volumen)" % (pol, "-"))
                continue
            print("     %-9s %9d %10.1f%% %10.1f%%"
                  % (pol, mejor["volumen"], mejor["precision"],
                     mejor["cobertura"]))
    with io.open("E:/Metamatematico/data/curva_emparejador.json", "w",
                 encoding="utf-8") as fh:
        json.dump(c, fh, indent=2, ensure_ascii=False)
    print("")
    print("-> E:/Metamatematico/data/curva_emparejador.json")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("-k", type=int, default=6, help="plazas con nombres")
    ap.add_argument("--curva", action="store_true",
                    help="barre k y compara a volumen igualado")
    a = ap.parse_args()
    main_curva(14) if a.curva else main(a.k)
