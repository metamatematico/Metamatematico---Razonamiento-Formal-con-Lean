# -*- coding: utf-8 -*-
"""Dos fallos que una consulta real destapó, medidos antes de arreglarlos.

EL PRIMERO · «the» es evidencia
-------------------------------
Ante «Is **the** square root of 2 irrational?» el grafo activaba
`different-ideal`, `upper-half-plane`, `simplex-category` y `unit-circle`.
Ninguno tiene una sola palabra clave que hable de raíces ni de
irracionalidad. Lo que casaba era la palabra `the`, que está en el nombre de
esos cuatro nodos —«The Different Ideal»…— y NO está en `_GENERICAS`.

O sea: **cualquier** consulta en inglés que contenga «the» activa esos cuatro
nodos, diga lo que diga. Es ruido puro, y de los 4 337 tokens del grafo sólo
`the` y `and` son palabras de parada — y `and` ya estaba en la lista.

EL SEGUNDO · el desempate es una constante disfrazada
-----------------------------------------------------
`classify_query` cuenta coincidencias por área y hace `max(scores, ...)`.
Ante la misma consulta:

    algebra        1   por «root»
    number-theory  1   por «irrational»

Empatan, y `max` devuelve la PRIMERA del diccionario, que es `algebra`. No
hay ningún criterio detrás: es el orden de una lista. Y `algebra` es además la
clase mayoritaria del banco (88,6 % en crudo), así que ese desempate infla la
exactitud cruda y hunde la equilibrada — exactamente la forma de fallo contra
la que existe la regla de medir con nulo.

Además casa por SUBCADENA: `if kw in text_lower`, sin límites de palabra.

QUE SE PRUEBA, Y CONTRA QUE
---------------------------
Cuatro variantes del clasificador y dos del emparejador, todas sobre la misma
muestra y la misma semilla que `medir_emparejamiento.py`, y todas contra el
mismo nulo: responder siempre la clase mayoritaria.

La medida que manda es la EQUILIBRADA. La cruda sobre un banco 88,6 % álgebra
premia justamente el fallo que se está corrigiendo.

No gasta API.
"""
import collections
import io
import json
import os
import random
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

DATOS = "E:/datadeentrenamientovalidacion_test/all_test.jsonl"
SALIDA = "E:/Metamatematico/data/parada_y_desempate.json"
MUESTRA = 3000
SEMILLA = 20260901

MAPA = {
    "algebra": "algebra", "intermediate_algebra": "algebra",
    "prealgebra": "algebra", "geometry": "geometry",
    "number_theory": "number-theory",
    "counting_and_probability": "combinatorics",
    "precalculus": "analysis", "gsm8k": None,
}


def cargar():
    filas = []
    for linea in io.open(DATOS, encoding="utf-8"):
        d = json.loads(linea)
        p, c = d.get("problem"), d.get("category")
        if p and c:
            filas.append((p, c))
    return filas


def equilibrada(pares):
    """Media de los aciertos DENTRO de cada clase.

    Es la única que sobrevive a un banco 88,6 % álgebra: la cruda mide el
    desequilibrio, no el clasificador.
    """
    por = collections.defaultdict(lambda: [0, 0])
    for esperada, pred in pares:
        por[esperada][1] += 1
        if esperada == pred:
            por[esperada][0] += 1
    if not por:
        return 0.0
    return 100.0 * sum(o / t for o, t in por.values()) / len(por)


# ═══════════════════════════════════════════════════════════════════════════
# LAS VARIANTES DEL CLASIFICADOR
# ═══════════════════════════════════════════════════════════════════════════
def _aciertos(kws, texto, con_limites):
    if con_limites:
        return [k for k in kws
                if re.search(r"\b%s\b" % re.escape(k), texto)]
    return [k for k in kws if k in texto]


def clasificar(texto, kw_por_area, orden, con_limites, por_especificidad):
    """Un clasificador de palabras clave, con las dos perillas del experimento.

    `con_limites`      : `\\bprime\\b` en vez de `"prime" in texto`.
    `por_especificidad`: el empate lo gana la coincidencia MÁS LARGA, en vez
                         de la primera de la lista.
    """
    t = (texto or "").lower()
    marcador = {}
    for cat, kws in kw_por_area.items():
        hits = _aciertos(kws, t, con_limites)
        marcador[cat] = hits
    mejor = max((len(v) for v in marcador.values()), default=0)
    if mejor == 0:
        # EL SUELO VA DECLARADO. Sin ninguna coincidencia se responde la clase
        # mayoritaria, que es lo que hace el modelo nulo. Eso no es un acierto
        # del clasificador y no se disfraza de tal.
        return "algebra"
    empatadas = [c for c in orden if len(marcador[c]) == mejor]
    if len(empatadas) == 1 or not por_especificidad:
        return empatadas[0]
    # UNA COINCIDENCIA LARGA ES MAS ESPECIFICA QUE UNA CORTA. «irrational»
    # dice mucho mas que «root», que sale en media biblioteca.
    return max(empatadas,
               key=lambda c: (max(len(k) for k in marcador[c]),
                              sum(len(k) for k in marcador[c])))


def main():
    from nucleo.core import Nucleo
    from nucleo.graph.category import SkillCategory
    from nucleo.multi_agent.specialized_agent import (_CATEGORY_KEYWORDS,
                                                      CATEGORIES)
    import nucleo.core as _core

    filas = cargar()
    if not filas:
        print("ATENCION: no se leyo nada de %s" % DATOS)
        return 1
    random.seed(SEMILLA)
    muestra = random.sample(filas, min(MUESTRA, len(filas)))
    print("muestra %d · semilla %d\n" % (len(muestra), SEMILLA))

    n = Nucleo.__new__(Nucleo)
    n._graph = SkillCategory()
    Nucleo._load_foundational_skills(n)
    g = n._graph
    area_de = {s.id: (s.metadata or {}).get("category") for s in g.skills}

    esperadas = [MAPA.get(c, "") for _, c in muestra]
    textos = [t for t, _ in muestra]

    # ── el nulo: responder siempre la clase mayoritaria ────────────────────
    vistas = [e for e in esperadas if e]
    mayoritaria = collections.Counter(vistas).most_common(1)[0][0]
    nulo_pares = [(e, mayoritaria) for e in vistas]
    print("nulo: responder siempre «%s» → equilibrada %.2f %% · cruda %.2f %%"
          % (mayoritaria, equilibrada(nulo_pares),
             100.0 * sum(1 for e in vistas if e == mayoritaria) / len(vistas)))
    print()

    # ── A · las cuatro variantes del clasificador ──────────────────────────
    print("EL CLASIFICADOR DE AREA")
    print("  %-34s %10s %10s" % ("variante", "equilibr.", "cruda"))
    area_res = {}
    for nombre, limites, espec in (
            ("hoy (subcadena · empate→1ª)", False, False),
            ("límites de palabra", True, False),
            ("desempate por especificidad", False, True),
            ("las dos juntas", True, True)):
        pares = []
        for texto, esp in zip(textos, esperadas):
            if not esp:
                continue
            pares.append((esp, clasificar(texto, _CATEGORY_KEYWORDS,
                                          CATEGORIES, limites, espec)))
        eq = equilibrada(pares)
        cr = 100.0 * sum(1 for a, b in pares if a == b) / len(pares)
        area_res[nombre] = {"equilibrada": round(eq, 2), "cruda": round(cr, 2)}
        print("  %-34s %9.2f %% %9.2f %%" % (nombre, eq, cr))
    print()

    # ── B · el emparejador, con y sin «the» ────────────────────────────────
    # LA MUDA CUENTA COMO FALLO, Y NO ES UN DETALLE.
    #
    # La primera version de este experimento saltaba las consultas sin skill
    # (`continue`) y comparaba la equilibrada de las que quedaban. Eso daba
    # «hoy 45,58 % · con the 38,94 %» y la conclusion falsa de que quitar
    # ruido puro empeora. No: al quitar `the` noventa consultas se quedaban
    # mudas y SALIAN DEL DENOMINADOR. Se comparaban dos configuraciones que
    # responden a distinto numero de consultas, que es el mando de volumen
    # disfrazado de mando de calidad contra el que existe la regla 2 del
    # metodo. Una consulta muda no es un caso que no cuenta: es un caso en el
    # que el grafo no ayudo.
    print("EL EMPAREJADOR DE SKILLS")
    print("  %-30s %10s %10s %10s %6s %6s"
          % ("variante", "equilibr.", "de las que", "con suelo",
             "mudas", "skills"))
    print("  %-30s %10s %10s %10s %6s %6s"
          % ("", "muda=fallo", "contestan", "declarado", "", ""))
    # LAS DOS RAMAS SE DEFINEN EXPLICITAMENTE, NO A PARTIR DEL MODULO.
    #
    # La primera version ponia la rama de control en `_GENERICAS` tal y como
    # estuviera, y cuando el arreglo ya estaba aplicado las DOS ramas eran la
    # misma: el experimento comparaba el sistema consigo mismo y daba cifras
    # identicas con toda la cara. La alarma del instrumento lo caz(o —por eso
    # esta— pero la causa es que un control definido como «lo que haya» deja
    # de ser un control en cuanto alguien toca lo que hay.
    origen = _core._GENERICAS
    base = frozenset(x for x in origen if x != "the")
    emp_res = {}
    for nombre, generi in (("sin «the» de parada (antes)", base),
                           ("con «the» de parada (arreglo)", base | {"the"})):
        _core._GENERICAS = generi
        con_mudas, solo_habladas, suelo, mudas, cuantas = [], [], [], 0, []
        for texto, esp in zip(textos, esperadas):
            sk = Nucleo._match_skills_to_query(n, texto, g)
            cuantas.append(len(sk))
            if not esp:
                continue
            a = area_de.get(sk[0]) if sk else None
            if not sk:
                mudas += 1
            #: `None` no es ningun area, asi que nunca iguala a la esperada:
            #: la muda entra como fallo sin inventarle una prediccion.
            con_mudas.append((esp, a))
            if a:
                solo_habladas.append((esp, a))
            # EL TERCER BRAZO, Y ES EL QUE DESHACE LA TRAMPA.
            #
            # `the` no era solo ruido: era un RESPALDO OCULTO A LA CLASE
            # MAYORITARIA. Una consulta que solo casaba por esa palabra
            # devolvia `different-ideal`, cuya area es `algebra` — el 88,9 %
            # del banco. Asi que quitarlo parece empeorar 7 puntos cuando lo
            # que cae es una constante que se estaba cobrando como senal, que
            # es exactamente el fallo del desempate visto en otro sitio.
            #
            # Este brazo separa las dos cosas: quita el ruido Y pone el suelo
            # donde se ve. Si gana, el arreglo es bueno y lo que faltaba era
            # declarar el respaldo en vez de heredarlo de una palabra suelta.
            suelo.append((esp, a or mayoritaria))
        eq, eq2 = equilibrada(con_mudas), equilibrada(solo_habladas)
        eq3 = equilibrada(suelo)
        emp_res[nombre] = {"equilibrada_muda_es_fallo": round(eq, 2),
                           "equilibrada_solo_las_que_hablan": round(eq2, 2),
                           "equilibrada_con_suelo_declarado": round(eq3, 2),
                           "mudas": mudas,
                           "skills_por_consulta": round(
                               sum(cuantas) / len(cuantas), 3)}
        print("  %-30s %9.2f %% %9.2f %% %9.2f %% %6d %6.2f"
              % (nombre, eq, eq2, eq3, mudas, sum(cuantas) / len(cuantas)))
    _core._GENERICAS = origen

    # ── la alarma del instrumento ──────────────────────────────────────────
    #
    # Si las dos variantes del emparejador dan EXACTAMENTE lo mismo en todo,
    # el experimento no midio nada: o el monkeypatch no llego, o «the» no
    # aparecia en la muestra. Un resultado identico es un resultado, pero hay
    # que saber distinguirlo de un instrumento desconectado.
    a, b = (emp_res["sin «the» de parada (antes)"],
            emp_res["con «the» de parada (arreglo)"])
    if a == b:
        print("\n  AVISO: las dos variantes son identicas en las tres cifras.")
        print("  Comprueba que `the` aparece en la muestra antes de creerlo.")

    io.open(SALIDA, "w", encoding="utf-8").write(json.dumps({
        "muestra": len(muestra), "semilla": SEMILLA,
        "nulo": {"area": mayoritaria,
                 "equilibrada": round(equilibrada(nulo_pares), 2)},
        "clasificador": area_res, "emparejador": emp_res,
    }, ensure_ascii=False, indent=2))
    print("\n-> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
