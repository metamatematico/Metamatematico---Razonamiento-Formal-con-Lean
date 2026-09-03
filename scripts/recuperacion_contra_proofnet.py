# -*- coding: utf-8 -*-
"""¿Sirven de algo los nombres que el grafo inyecta? Juzgado contra la verdad.

LA PREGUNTA QUE BLOQUEABA TODO. El grafo actua en dos puntos: mete nombres de
Mathlib verificados en el prompt de formalizacion, y elige que modulos importa
Lean. Se ha medido si acierta el AREA de la consulta —un proxy flojo, y encima
contra MATH, que es matematica de concurso y no el dominio de este sistema—
pero nunca si los nombres que ofrece son los que hacen falta.

AHORA SE PUEDE, y sin gastar un centimo: ProofNet trae 186 ejercicios con el
enunciado en lenguaje natural Y su formalizacion Lean escrita por matematicos.

    nl_statement      "If $r$ is rational $(r \\neq 0)$ and $x$ is irrational,
                       prove that $rx$ is irrational."
    formal_statement  theorem exercise_1_1b (x : ℝ) (y : ℚ) ... : irrational ...

Asi que la formalizacion de oro dice QUE identificadores hacian falta de
verdad. Y la pregunta se vuelve medible:

    de los nombres que el grafo inyecta para ese enunciado,
    ¿cuantos aparecen en la formalizacion correcta?

TRES MEDIDAS:
  precision  de lo que el grafo ofrece, cuanto se usa
  cobertura  de lo que hacia falta, cuanto ofrecio el grafo
  y las mismas para el emparejador SEMANTICO, para comparar con el lexico

MODELO NULO: ofrecer los nombres mas frecuentes de Mathlib, sin mirar la
consulta. Si el grafo no lo supera, no esta aportando nada especifico.

No gasta API.
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

PROOFNET = ("E:/MetamatematicoDataSet/ProofNet/ProofNet-main/benchmark/%s.jsonl")
SALIDA = "E:/Metamatematico/data/recuperacion_proofnet.json"
MODELO = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

#: Identificadores de la formalizacion.
#:
#: La primera version solo cogia CamelCase o nombres con punto, y ProofNet esta
#: en LEAN 3, donde casi todo va en minuscula y sin punto: `irrational`,
#: `partial_order`, `is_linear_order`. O sea que el conjunto de oro se quedaba
#: SIN los nombres que importan —del ejemplo `irrational x -> irrational (x*y)`
#: no extraia ninguno— y las tres variantes salian planas. Segundo instrumento
#: roto de esta misma medida.
#:
#: Ahora entra cualquier identificador y las variables ligadas del enunciado
#: (x, y, h₀, n) se filtran por forma: un nombre de Mathlib tiene 4 caracteres
#: o mas, o lleva `_` o `.`.
IDENT = re.compile(r"\b([A-Za-z_][A-Za-z0-9_']*(?:\.[A-Za-z_][A-Za-z0-9_']*)*)\b")
#: Palabras de la sintaxis de Lean, que no son vocabulario matematico.
SINTAXIS = {"theorem", "lemma", "def", "by", "sorry", "fun", "have", "show",
            "from", "let", "in", "if", "then", "else", "match", "with",
            "Type", "Prop", "Sort", "forall", "exists"}


def cargar():
    filas = []
    for split in ("test", "valid"):
        p = PROOFNET % split
        if not os.path.exists(p):
            continue
        for l in io.open(p, encoding="utf-8"):
            d = json.loads(l)
            nl, fs = d.get("nl_statement"), d.get("formal_statement")
            if nl and fs:
                filas.append((d.get("id", "?"), nl, fs))
    return filas


def _norm(n):
    """Puente entre mathlib3 y Mathlib 4.

    ProofNet esta escrito en LEAN 3: `irrational`, `partial_order`,
    `set.nonempty`, `is_linear_order`. El grafo tiene nombres de Mathlib 4:
    `Irrational`, `PartialOrder`, `Set.Nonempty`. Comparados en crudo la
    interseccion es SIEMPRE vacia, y la primera version de este script dio
    0,0 % en las tres variantes —incluido el modelo nulo—, que es la firma de
    un instrumento roto y no de un resultado.

    El renombrado de mathlib3 a 4 fue en su mayoria snake_case ->
    UpperCamelCase, asi que quitar mayusculas y separadores reconcilia la mayor
    parte: `partial_order` y `PartialOrder` caen los dos en `partialorder`.

    APROXIMACION, y se dice: los renombrados semanticos —los que cambiaron de
    nombre, no de estilo— no los recupera. Esto da una cota INFERIOR del
    solapamiento real.
    """
    return n.replace("_", "").replace(".", "").replace("'", "").lower()


def nombres_de_oro(formal):
    """Los identificadores de Mathlib que la formalizacion correcta usa."""
    out = set()
    for m in IDENT.finditer(formal):
        n = m.group(1)
        if n in SINTAXIS or n.startswith("exercise"):
            continue
        if len(n) < 4 and "_" not in n and "." not in n:
            continue                      # variable ligada, no un nombre
        out.add(_norm(n.split(".")[0]))   # el namespace raiz: Set, Real...
        out.add(_norm(n))
    return out


def main(k):
    from nucleo.core import Nucleo
    from nucleo.graph.category import SkillCategory
    from nucleo.graph.interpretacion import nombres_de_trabajo

    filas = cargar()
    print("ProofNet: %d ejercicios con enunciado y formalizacion" % len(filas))
    if not filas:
        print("  ATENCION: no se leyo nada — revisa %s" % (PROOFNET % "test"))
        return 1

    n = Nucleo.__new__(Nucleo)
    n._graph = SkillCategory()
    Nucleo._load_foundational_skills(n)
    g = n._graph

    def ofrecidos(skills):
        """Misma regla que core._nombres_mathlib: k plazas CON NOMBRES.

        Si el medidor y el runtime no llenan las plazas igual, la cifra no
        habla del sistema sino del medidor.
        """
        out = set()
        llenas = 0
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

    #: MODELO NULO: los nombres mas comunes del grafo, sin mirar la consulta.
    todos = collections.Counter()
    for s in g.skill_ids:
        for pieza in re.split(r"[,+]", nombres_de_trabajo(s) or ""):
            p = pieza.strip()
            if p:
                todos[p] += 1
    nulo = {_norm(p) for p, _ in todos.most_common(3 * k)}
    nulo |= {_norm(p.split(".")[0]) for p, _ in todos.most_common(3 * k)}

    # emparejador semantico, para comparar con el lexico
    try:
        import numpy as np
        from sentence_transformers import SentenceTransformer
        from scripts.emparejador_semantico import texto_de
        modelo = SentenceTransformer(MODELO)
        skills = g.skills
        ids = [s.id for s in skills]
        M = modelo.encode([texto_de(s) for s in skills],
                          normalize_embeddings=True, show_progress_bar=False)
        Q = modelo.encode([f[1] for f in filas], normalize_embeddings=True,
                          batch_size=32, show_progress_bar=False)
        sem = [[ids[i] for i in np.argsort(-fila)[:k]] for fila in Q @ M.T]
    except Exception as e:
        print("  sin emparejador semantico (%s)" % type(e).__name__)
        sem = None

    res = {}
    for etiqueta in ("lexico", "lexico+puerta", "semantico", "nulo"):
        if etiqueta == "semantico" and sem is None:
            continue
        tp = fp = fn = 0
        con_algo = 0
        for idx, (_id, nl, formal) in enumerate(filas):
            oro = nombres_de_oro(formal)
            if not oro:
                continue
            if etiqueta == "lexico":
                ofr = ofrecidos(Nucleo._match_skills_to_query(n, nl, g))
            elif etiqueta == "lexico+puerta":
                # LA PUERTA SOLO ACTUA DONDE EL LEXICO CALLA, igual que en
                # `_find_relevant_context`. Aqui se replica ese camino para
                # poder medirlo por separado: el brazo `lexico` es la linea
                # base y este dice lo que aporta el reconocedor de forma.
                m = Nucleo._match_skills_to_query(n, nl, g)
                if not m:
                    from nucleo.graph.reconocedor import areas_de
                    puertas = [a for a in areas_de(nl) if g.get_skill(a)]
                    hijos = [h for a in puertas for h in g.dependents(a)]
                    m = (puertas + hijos)[:8]
                ofr = ofrecidos(m)
            elif etiqueta == "semantico":
                ofr = ofrecidos(sem[idx])
            else:
                ofr = set(nulo)
            if ofr:
                con_algo += 1
            aciertos = ofr & oro
            tp += len(aciertos)
            fp += len(ofr - oro)
            fn += len(oro - ofr)
        prec = 100.0 * tp / max(1, tp + fp)
        cob = 100.0 * tp / max(1, tp + fn)
        res[etiqueta] = {"precision": prec, "cobertura": cob,
                         "con_algo": con_algo, "tp": tp, "fp": fp, "fn": fn}
        print("\n  %-11s precision %5.1f %%  ·  cobertura %5.1f %%  ·  "
              "ofrece algo en %d de %d"
              % (etiqueta, prec, cob, con_algo, len(filas)))

    print("\n  LECTURA")
    print("    precision = de lo que el grafo ofrece, cuanto se usa de verdad")
    print("    cobertura = de lo que hacia falta, cuanto ofrecio el grafo")
    if "nulo" in res:
        for e in ("lexico", "lexico+puerta", "semantico"):
            if e in res:
                d = res[e]["cobertura"] - res["nulo"]["cobertura"]
                print("    %s vs modelo nulo en cobertura: %+.1f puntos"
                      % (e, d))

    json.dump({"n": len(filas), "k": k, "resultados": res},
              io.open(SALIDA, "w", encoding="utf-8"), indent=1,
              ensure_ascii=False)
    print("\n-> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", type=int, default=6,
                    help="cuantas skills se consultan por enunciado")
    a = ap.parse_args()
    sys.exit(main(a.k))
