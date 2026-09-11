# -*- coding: utf-8 -*-
"""¿Predicen los rasgos del ÁRBOL DE LA CONSULTA la estrategia de la prueba?

LA PREGUNTA, Y DE DÓNDE SALE
----------------------------
El grafo tiene 6 nodos `strategy-*` y 9 `tactic-*`, y el recorrido de
`_find_relevant_context` los recoge. La idea original era ensamblar con ellos
un BOCETO de prueba en sintaxis de Lean —el esquema de Draft-Sketch-Prove—
que el modelo rellenara y las tácticas de Lean cerraran.

Ese ensamblador no llegó a construirse, y hay un motivo medible por el que no
podría funcionar tal como está el recorrido hoy: sobre los 371 enunciados de
ProofNet, `proof_strategies` devuelve TRES conjuntos distintos y uno solo
—{cases, forward, inductive}— cubre el 82 %. Un boceto necesita saber CUÁL, y
el recorrido contesta casi siempre lo mismo.

La causa es estructural: las estrategias cuelgan de las TÁCTICAS, que son
sumideros con 453 aristas entrantes. Se llega a ellas desde casi cualquier
concepto, así que casi cualquier consulta produce el mismo conjunto.

LA HIPÓTESIS QUE SE PRUEBA AQUÍ
-------------------------------
Que la estrategia no se decide por el CONCEPTO («esto es teoría de grupos»)
sino por la FORMA DEL ENUNCIADO («para todo n» -> inducción, «supongamos que
no» -> contradicción, «existe» -> construcción).

Y que esa forma ya se puede leer antes de llamar al modelo, con
`nucleo.sintaxis.rasgos`, cuyo propio precedente dice que 68 rasgos
estructurales GANAN a 40 000 n-gramas prediciendo qué táctica cierra un
objetivo (61,1 % contra 60,5 %) —pero medido sobre enunciados de LEAN, que no
existen todavía en el paso 1—.

EL BANCO
--------
`data/lean_examples.json`: 240 ejemplos de LeanWorkbook con las tres cosas
que hacen falta a la vez:

    nl          el enunciado en prosa      <- la entrada, disponible en el paso 1
    statement   el enunciado en Lean
    tactics     la prueba REAL que cerró   <- de aquí sale la etiqueta

MODELOS NULOS. Dos, y los dos honestos:
    mayoritaria   responder siempre la clase más frecuente
    n-gramas      TF-IDF de caracteres sobre la misma prosa

El segundo es el que importa: si los rasgos del árbol no baten a contar
caracteres, no aportan estructura, aportan léxico.

No gasta API ni Lean.

    python -m scripts.rasgos_predicen_estrategia
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

EJEMPLOS = "E:/Metamatematico/data/lean_examples.json"
PROOFNET = "E:/MetamatematicoDataSet/ProofNet/ProofNet-main/benchmark/%s.jsonl"
SALIDA = "E:/Metamatematico/data/rasgos_predicen_estrategia.json"
SEMILLA = 20260901

#: EL BANCO DE LEANWORKBOOK NO SIRVE PARA ESTA PREGUNTA, Y ESTÁ MEDIDO.
#:
#: Se probó primero con `data/lean_examples.json` (240 ejemplos) y el reparto
#: de estrategias salió así:
#:
#:     forward        195  (81,2 %)   <- el cajón por defecto
#:     construction    37  (15,4 %)
#:     backward         4 · cases 3 · contradiction 1 · inductive 0
#:
#: Al retener las clases con al menos cinco ejemplos quedaban DOS. LeanWorkbook
#: son desigualdades y cálculos que cierra `nlinarith`: no hay inducción, ni
#: contradicción, ni análisis por casos. Un banco sin variedad en la variable
#: que se quiere predecir no puede contestar, y el +1,9 puntos que daba sobre
#: un problema binario al 50 % era ruido.
#:
#: ProofNet sí sirve: 369 ejercicios de Rudin, Dummit-Foote y Munkres con la
#: prueba informal escrita por matemáticos, y cinco estrategias con masa.

#: De la PRUEBA INFORMAL a la estrategia. El orden va de lo específico a lo
#: genérico: una prueba que dice «suppose not» y luego «two cases» es por
#: contradicción, que es la que gobierna la forma del argumento.
ESTRATEGIA_NL = [
    ("inductive",     r"\binduct"),
    ("contradiction", r"suppose not|contradiction|contrary|assume\b.{0,20}\bnot\b"),
    ("cases",         r"\bcases?\b|either|otherwise"),
    ("construction",  r"\bconstruct|\bdefine\b|\bchoose\b|\blet\b.{0,30}\bbe\b"),
]
DIRECTA = "directa"


def cargar_proofnet():
    """(enunciado en prosa, estrategia de la prueba informal).

    LA ETIQUETA SALE DE LA PRUEBA, LA ENTRADA DEL ENUNCIADO. Es la separación
    que hace la pregunta honesta: en el paso 1 se tiene el enunciado y no la
    prueba, así que predecir la estrategia DESDE el enunciado es exactamente
    lo que un generador de bocetos tendría que hacer.
    """
    filas = []
    for split in ("test", "valid"):
        ruta = PROOFNET % split
        if not os.path.exists(ruta):
            continue
        for linea in io.open(ruta, encoding="utf-8"):
            d = json.loads(linea)
            nl, pr = d.get("nl_statement"), d.get("nl_proof")
            if not (nl and pr):
                continue
            p = pr.lower()
            et = DIRECTA
            for nombre, patron in ESTRATEGIA_NL:
                if re.search(patron, p):
                    et = nombre
                    break
            filas.append({"nl": nl.strip(), "area": d.get("id", "?"),
                          "estrategia": et, "primera": et})
    return filas

#: De la prueba real a una de las seis estrategias del grafo.
#:
#: EL ORDEN IMPORTA: se comprueba de la más específica a la más genérica. Una
#: prueba que hace `by_contra` y luego `rcases` es por contradicción, no por
#: casos: la contradicción es la que gobierna la forma del argumento.
ESTRATEGIA = [
    ("inductive",     r"\binduction\b|\bNat\.rec\b|\binduction'\b"),
    ("contradiction", r"\bby_contra\b|\babsurd\b|\bpush_neg\b|\bfalse_or\b"),
    ("cases",         r"\brcases\b|\bobtain\b|\bcases\b|\brintro\b|\bmatch\b|"
                      r"\binterval_cases\b"),
    ("construction",  r"\bconstructor\b|\brefine\b|\buse\b|\bexact\s*<|"
                      r"\bexists\b"),
    ("backward",      r"\bapply\b"),
]
POR_DEFECTO = "forward"


def etiqueta(tacticas) -> str:
    """La estrategia que gobierna esta prueba."""
    texto = " ".join(tacticas or [])
    for nombre, patron in ESTRATEGIA:
        if re.search(patron, texto):
            return nombre
    return POR_DEFECTO


def cargar():
    d = json.load(io.open(EJEMPLOS, encoding="utf-8"))
    filas = []
    for area, ejemplos in d.items():
        for x in ejemplos:
            nl = (x.get("nl") or "").strip()
            tac = x.get("tactics") or []
            if nl and tac:
                filas.append({"nl": nl, "area": area,
                              "estrategia": etiqueta(tac),
                              "primera": _primera(tac)})
    return filas


def _primera(tacticas) -> str:
    m = re.match(r"\s*([a-zA-Z_][a-zA-Z_0-9.]*)", (tacticas or [""])[0])
    return m.group(1) if m else "(vacio)"


def vector_de_rasgos(filas):
    """Los rasgos del árbol de cada consulta, como vectores numéricos."""
    from nucleo.sintaxis.rasgos import rasgos_de_consulta
    crudos = []
    for f in filas:
        try:
            crudos.append(rasgos_de_consulta(f["nl"]) or {})
        except Exception:                                       # noqa: BLE001
            crudos.append({})
    # vocabulario de rasgos: clave o clave=valor para los no numéricos
    claves = set()
    for r in crudos:
        for k, v in r.items():
            claves.add(k if isinstance(v, (int, float, bool)) else
                       "%s=%s" % (k, v))
    claves = sorted(claves)
    idx = {k: i for i, k in enumerate(claves)}
    import numpy as np
    X = np.zeros((len(crudos), len(claves)))
    for i, r in enumerate(crudos):
        for k, v in r.items():
            if isinstance(v, (int, float, bool)):
                if k in idx:
                    X[i, idx[k]] = float(v)
            else:
                kk = "%s=%s" % (k, v)
                if kk in idx:
                    X[i, idx[kk]] = 1.0
    return X, claves


def main(objetivo: str, banco: str, n_perm: int) -> int:
    import numpy as np
    from sklearn.linear_model import LogisticRegression
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.model_selection import StratifiedKFold, cross_val_predict
    from sklearn.dummy import DummyClassifier
    from sklearn.metrics import accuracy_score, balanced_accuracy_score

    if banco == "proofnet":
        filas = cargar_proofnet()
        print("banco: %d ejercicios de ProofNet con enunciado y prueba informal"
              % len(filas))
    else:
        filas = cargar()
        print("banco: %d ejemplos de LeanWorkbook (ver la nota: no discrimina)"
              % len(filas))
    y = np.array([f[objetivo] for f in filas])
    print("objetivo: %s\n" % objetivo)

    dist = collections.Counter(y)
    print("DISTRIBUCIÓN DE CLASES")
    for k, v in dist.most_common():
        print("   %-16s %3d  (%4.1f %%)" % (k, v, 100.0 * v / len(y)))
    mayoritaria = dist.most_common(1)[0]
    print("   -> la clase mayoritaria es %s con %.1f %%\n"
          % (mayoritaria[0], 100.0 * mayoritaria[1] / len(y)))

    # clases con menos de 3 ejemplos no se pueden validar cruzado
    validas = {k for k, v in dist.items() if v >= 5}
    keep = np.array([v in validas for v in y])
    filas = [f for f, k in zip(filas, keep) if k]
    y = y[keep]
    print("se retienen las clases con >=5 ejemplos: %d ejemplos, %d clases\n"
          % (len(y), len(set(y))))

    X_rasgos, claves = vector_de_rasgos(filas)
    textos = [f["nl"] for f in filas]
    print("rasgos del árbol: %d dimensiones" % X_rasgos.shape[1])

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=SEMILLA)

    def evalua(nombre, modelo, X):
        pred = cross_val_predict(modelo, X, y, cv=cv)
        return (nombre, accuracy_score(y, pred),
                balanced_accuracy_score(y, pred))

    res = []
    res.append(evalua("nulo: clase mayoritaria",
                      DummyClassifier(strategy="most_frequent"), X_rasgos))

    vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5),
                          max_features=40000, sublinear_tf=True)
    X_ngr = vec.fit_transform(textos)
    print("n-gramas de carácter: %d dimensiones\n" % X_ngr.shape[1])
    res.append(evalua("nulo: n-gramas de la prosa",
                      LogisticRegression(max_iter=2000, C=1.0), X_ngr))

    res.append(evalua("RASGOS DEL ÁRBOL",
                      LogisticRegression(max_iter=2000, C=1.0), X_rasgos))

    from scipy.sparse import hstack, csr_matrix
    X_ambos = hstack([X_ngr, csr_matrix(X_rasgos)])
    res.append(evalua("rasgos + n-gramas",
                      LogisticRegression(max_iter=2000, C=1.0), X_ambos))

    print("RESULTADO (validación cruzada estratificada, 5 pliegues)")
    print("   %-28s %10s %12s" % ("", "acierto", "equilibrado"))
    for nombre, acc, bal in res:
        print("   %-28s %8.1f %% %10.1f %%" % (nombre, 100 * acc, 100 * bal))

    # ── PRUEBA DE PERMUTACIÓN ────────────────────────────────────────────
    #
    # Comparar contra la clase mayoritaria no basta cuando el acierto
    # equilibrado ronda el azar: con cinco clases el azar es 20 % y cualquier
    # clasificador arañará algo por encima. La pregunta honesta es si el
    # resultado cae fuera de la nube que se obtiene BARAJANDO la etiqueta.
    print("\nprueba de permutación (%d barajados)..." % n_perm)
    rng = np.random.default_rng(SEMILLA)
    mod = LogisticRegression(max_iter=2000)
    nulos = []
    for _ in range(n_perm):
        yp = rng.permutation(y)
        nulos.append(balanced_accuracy_score(
            yp, cross_val_predict(mod, X_rasgos, yp, cv=cv)))
    nulos = np.array(nulos)
    real_bal = res[2][2]
    p_perm = (np.sum(nulos >= real_bal) + 1) / (n_perm + 1)
    print("   azar: media %.3f  desv %.3f  máximo %.3f"
          % (nulos.mean(), nulos.std(), nulos.max()))
    print("   real: %.3f      p = %.4f" % (real_bal, p_perm))

    nulo_may = res[0][2]
    nulo_ngr = res[1][2]
    rasgos = res[2][2]
    print("\nLECTURA (acierto equilibrado, que es el que no premia la clase grande)")
    print("   rasgos frente a la mayoritaria : %+.1f puntos"
          % (100 * (rasgos - nulo_may)))
    print("   rasgos frente a los n-gramas   : %+.1f puntos"
          % (100 * (rasgos - nulo_ngr)))
    # EL VEREDICTO EXIGE LAS TRES COSAS, Y LA SEGUNDA ES LA QUE MANDA.
    #
    # Un clasificador que gana en acierto EQUILIBRADO pero pierde en acierto
    # CRUDO contra la clase mayoritaria sería peor que una constante si se
    # desplegara. Ese caso hay que llamarlo por su nombre, no «aporta».
    crudo_may, crudo_rasgos = res[0][1], res[2][1]
    if p_perm >= 0.05:
        veredicto = "sin señal: no se distingue del azar"
    elif crudo_rasgos <= crudo_may:
        veredicto = ("señal real pero DEMASIADO DÉBIL para desplegar: gana al "
                     "azar (p=%.3f) y pierde en acierto crudo contra la clase "
                     "mayoritaria (%.1f %% contra %.1f %%)"
                     % (p_perm, 100 * crudo_rasgos, 100 * crudo_may))
    else:
        veredicto = "los rasgos del árbol aportan y baten a la mayoritaria"
    print("   VEREDICTO: %s" % veredicto)

    json.dump({"objetivo": objetivo, "banco": banco, "n": len(y),
               "clases": {k: int(v) for k, v in collections.Counter(y).items()},
               "dimensiones_rasgos": X_rasgos.shape[1],
               "resultados": [{"variante": n, "acierto": a, "equilibrado": b}
                              for n, a, b in res],
               "permutacion": {"n": n_perm, "media": float(nulos.mean()),
                               "desv": float(nulos.std()),
                               "max": float(nulos.max()), "p": float(p_perm)},
               "veredicto": veredicto},
              io.open(SALIDA, "w", encoding="utf-8"), indent=1,
              ensure_ascii=False)
    print("\n-> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--objetivo", default="estrategia",
                    choices=["estrategia", "primera"],
                    help="qué predecir: la estrategia o la primera táctica")
    ap.add_argument("--banco", default="proofnet",
                    choices=["proofnet", "leanworkbook"],
                    help="proofnet tiene variedad de estrategias; "
                         "leanworkbook no (ver la nota del módulo)")
    ap.add_argument("--permutaciones", type=int, default=200)
    a = ap.parse_args()
    raise SystemExit(main(a.objetivo, a.banco, a.permutaciones))
