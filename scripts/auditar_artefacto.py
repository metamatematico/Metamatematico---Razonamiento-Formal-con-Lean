# -*- coding: utf-8 -*-
"""Cada cifra del artefacto contra su fuente: el grafo del runtime o su JSON.

No compara el documento consigo mismo —eso ya lo hace el auditor de
alineacion— sino con lo que MIDE cada cosa. Es la familia de error que el
auditor no ve: la cifra que cuadra con su propio parrafo y lleva meses sin
releerse.
"""
import collections
import io
import json
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, "E:/Metamatematico")
R = "E:/Metamatematico/"


def J(n):
    try:
        return json.load(io.open(R + "data/" + n, encoding="utf-8"))
    except Exception:
        return {}


# ── la verdad ───────────────────────────────────────────────────────────────
from nucleo.core import Nucleo                       # noqa: E402
from nucleo.graph.category import SkillCategory      # noqa: E402

n = Nucleo.__new__(Nucleo)
n._graph = SkillCategory()
Nucleo._load_foundational_skills(n)
g = n._graph
meta = {s.id: (s.metadata or {}) for s in g.skills}
tipo = collections.Counter(m.morphism_type.name for m in g.morphisms)
sort = collections.Counter(meta[s.id].get("sort") or "CONCEPTO" for s in g.skills)

pn, fu, do, he = (J("recuperacion_proofnet.json"), J("funtor_mathlib.json"),
                  J("banco_docstrings.json"), J("banco_herald.json"))
fi, em, ra, im = (J("fibracion_del_grafo.json"), J("emparejamiento.json"),
                  J("ranker_en_la_cascada.json"), J("imports_contra_lean.json"))
vi, es, tr = (J("viajes.json"), J("categoria_de_estados.json"),
              J("tactic_ranker_report.json"))

lx, nu = pn["resultados"]["lexico"], pn["resultados"]["nulo"]
cur = fu["por_clase"]["curada"]
dg, dn = do["resultados"]["grafo"], do["resultados"]["nulo"]
hg, hn = he["resultados"]["grafo"], he["resultados"]["nulo"]
rk = ra["resultados"]

VERDAD = {
    "nodos": len(list(g.skills)),
    "morfismos": sum(tipo.values()),
    "DEPENDENCY": tipo["DEPENDENCY"], "TRANSLATION": tipo["TRANSLATION"],
    "IDENTITY": tipo["IDENTITY"], "ANALOGY": tipo["ANALOGY"],
    "CONCEPTO": sort["CONCEPTO"], "MODULO": sort["MODULO"], "AREA": sort["AREA"],
    "ProofNet precision": lx["precision"], "ProofNet cobertura": lx["cobertura"],
    "ProofNet nulo prec": nu["precision"], "ProofNet nulo cob": nu["cobertura"],
    "ProofNet factor": lx["precision"] / nu["precision"],
    "ProofNet con_algo": lx["con_algo"],
    "DAG medibles": cur["medibles"], "DAG confirmadas": cur["confirmadas"],
    "DAG tasa": cur["tasa_pct"], "DAG nulo": cur["nulo_pct"],
    "DAG factor": cur["factor"],
    "docstrings prec": dg["precision"], "docstrings cob": dg["cobertura"],
    "docstrings nulo p": dn["precision"], "docstrings nulo c": dn["cobertura"],
    "docstrings factor": dg["precision"] / dn["precision"],
    "Herald prec": hg["precision"], "Herald cob": hg["cobertura"],
    "Herald nulo p": hn["precision"], "Herald factor": hg["precision"] / hn["precision"],
    "fibracion pares": fi["pares"], "fibracion levantados": fi["levantados"],
    "fibracion tasa%": 100 * fi["tasa"], "fibracion nulo%": 100 * fi["nulo_media"],
    "morf de orden": fi["morfismos_de_orden"],
    "cruzan de area": fi["morfismos_que_cruzan"],
    "dentro de area": fi["morfismos_dentro_de_area"],
    "al fundacional": fi["morfismos_al_fundacional"],
    "area equilibrada": em["area_equilibrada"],
    "area nulo": em["nulo_mayoria_equilibrada"],
    "skill area": em["skill_area_equilibrada"],
    "sin skill": em["sin_skill"],
    "skills por consulta": em["skills_por_consulta"],
    "ranker posicion": rk["RANKEADOR"]["posicion_media"],
    "ranker nulo pos": rk["NULO: por frecuencia"]["posicion_media"],
    "ranker fijo pos": rk["fijo (SOLVER_CASCADE)"]["posicion_media"],
    "ranker 1er": rk["RANKEADOR"]["primer_intento"],
    "ranker acc": 100 * tr["accuracy"], "ranker base": 100 * tr["baseline_mayoritaria"],
    "imports grafo": im["resumen"]["grafo"]["ok"],
    "imports fijo": im["resumen"]["fijo"]["ok"],
    "imports azar": im["resumen"]["azar"]["ok"],
    "viajes pares": vi["pares"], "viajes con": vi["con_viaje"],
    "viajes tasa%": 100 * vi["tasa"], "viajes nulo%": 100 * vi["nulo_base_directa"],
    "estados objetos": es["objetos"], "estados flechas": es["flechas"],
    "estados paralelas": es["paralelas"], "estados ramifican": es["estados_que_ramifican"],
    "estados al terminal": es["flechas_al_terminal"],
}

print("LA VERDAD, DE SU FUENTE")
for k, v in VERDAD.items():
    print("   %-24s %s" % (k, ("%.2f" % v) if isinstance(v, float) else v))

# ── el documento ────────────────────────────────────────────────────────────
s = io.open(R + "docs/arquitectura_nle.html", encoding="utf-8").read()
svg = " ".join(re.sub(r"<[^>]+>", " ", m.group(0))
               for m in re.finditer(r"<svg[\s\S]*?</svg>", s))
prosa = re.sub(r"<svg[\s\S]*?</svg>", " ", s)
prosa = re.sub(r"<[^>]+>", " ", prosa)
todo = re.sub(r"[\s\u00a0\u202f]+", " ", prosa + " " + svg)

def hay(*formas):
    return [f for f in formas if f in todo]

print("\nCOMPROBACIONES")
PARES = [
    ("353 nodos/objetos", ("353 nodos", "353 objetos")),
    ("1 586 morfismos", ("1 586 morfismos", "1586 morfismos")),
    ("DEPENDENCY 688", ("DEPENDENCY · 688", "688")),
    ("TRANSLATION 538", ("TRANSLATION · 538", "538")),
    ("ProofNet 23,9 %", ("23,9 %",)),
    ("ProofNet nulo 1,45", ("1,45 %",)),
    ("factor 16,5x", ("16,5×", "16,5x")),
    ("DAG 73,7 %", ("73,7 %",)),
    ("DAG nulo 31,3 %", ("31,3 %",)),
    ("docstrings 19,2x", ("19,2×",)),
    ("Herald 9,0x", ("9,0×",)),
    ("area 62,1 %", ("62,1 %",)),
    ("area nulo 33,3 %", ("33,3 %",)),
    ("skill area 38,9 %", ("38,9 %",)),
    ("ranker 1,57", ("1,57",)),
    ("ranker nulo 2,44", ("2,44",)),
    ("ranker 0,621", ("0,621",)),
    ("imports 18 de 20", ("18 de 20", "18/20")),
    ("imports azar 12", ("12 de 20", "18 frente a 12")),
    ("282 de 284", ("282 de 284", "282 de las 284")),
    ("fibracion 0,1 %", ("0,1 %",)),
    ("fibracion nulo 4,3 %", ("4,3 %",)),
    ("688 morf de orden", ("688 morfismos de orden",)),
    ("105 cruzan", ("105 de 688", "105 cruzan")),
    ("estados 24 752", ("24 752",)),
    ("estados 25 206", ("25 206",)),
    ("16 paralelos", ("16 pares paralelos",)),
    # LOS RECUENTOS POR SORT, que la primera version no miraba y por eso
    # dejo pasar una figura entera contradiciendo al grafo Y a su aria.
    ("CONCEPTO 189", ("CONCEPTO · 189", "189 conceptos", "189 nodos")),
    ("MODULO 125", ("MODULO · 125", "125 modulos", "125 módulos")),
    ("AREA 24", ("AREA · 24", "24 nodos con sort AREA")),
    ("IDENTITY 353", ("IDENTITY · 353", "353 identidades")),
    ("ANALOGY 7", ("ANALOGY · 7", "7 analogias", "7 analogías")),
    ("552 entran 11 salen", ("552 aristas y solo emiten 11",
                             "552 aristas y sólo emiten 11", "552 entran")),
    ("147 aportan nombres", ("147 lo hacen",)),
]
mal = []
for et, formas in PARES:
    if not hay(*formas):
        mal.append(et)
        print("   FALTA   %-22s (buscaba %s)" % (et, " | ".join(formas)))
print("   %d de %d presentes" % (len(PARES) - len(mal), len(PARES)))

suma = VERDAD["DEPENDENCY"] + VERDAD["TRANSLATION"] + VERDAD["ANALOGY"] + VERDAD["IDENTITY"]
sumas = VERDAD["CONCEPTO"] + VERDAD["MODULO"] + VERDAD["AREA"] + 9 + 6
print("\nLAS DOS SUMAS")
print("   %d+%d+%d+%d = %d morfismos  %s" % (VERDAD["DEPENDENCY"],
      VERDAD["TRANSLATION"], VERDAD["ANALOGY"], VERDAD["IDENTITY"], suma,
      "OK" if suma == VERDAD["morfismos"] else "NO CUADRA"))
print("   %d+%d+%d+9+6 = %d nodos  %s" % (VERDAD["CONCEPTO"], VERDAD["MODULO"],
      VERDAD["AREA"], sumas, "OK" if sumas == VERDAD["nodos"] else "NO CUADRA"))

print("\nCIFRAS SOSPECHOSAS QUE SIGUEN EN EL TEXTO")
VIEJAS = ["58,7 %", "40,9 %", "61,2 %", "14 de 20", "18 frente a 14",
          "352 nodos", "1 578", "1 585", "1 349", "1 356", "687", "535",
          "24 750", "341 pares", "25 214", "1219 tests", "1238 tests",
          "1244 tests", "62 suites", "15,7×", "19,0×", "8,8×", "2,28×",
          "0,598", "453 aristas", "3 de 860", "860 pares", "72,2 %", "30,7 %",
          "151 aristas", "109 confirmadas", "1 085 tests", "1089 tests"]
enc = [v for v in VIEJAS if v in todo]
print("  ", enc or "ninguna")

# tests y suites, contados de verdad
try:
    out = subprocess.run([sys.executable, "-m", "pytest", "-o", "addopts=",
                          "--collect-only", "-q"], cwd=R, capture_output=True,
                         text=True, timeout=600).stdout
    m = re.search(r"(\d+) tests? collected", out)
    ntest = int(m.group(1)) if m else None
    import glob as _g
    nsuite = len(_g.glob(R + "tests/test_*.py"))
    print("\nRECUENTOS REALES: %s tests · %d ficheros de test" % (ntest, nsuite))
    for f in ("%d tests" % ntest, "%s tests" % ("%d" % ntest), "%d suites" % nsuite):
        print("   '%s' en el documento: %s" % (f, f in todo))
except Exception as e:
    print("no se pudo contar:", e)
