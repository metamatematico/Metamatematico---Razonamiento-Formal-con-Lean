# -*- coding: utf-8 -*-
"""Mide si siete nodos-rama estaban enrutando o solo estorbando.

DE DONDE SALEN LOS SIETE
------------------------
El veredicto sobre las 48 declara 33 nodos-rama: marca `T` —no son objetos— y
rol `rama` —si son estructura de enrutamiento—. En 26 de ellos «rama» es
evidente. En SIETE es discutible, y por dos motivos distintos:

    una sola palabra clave      una rama con una palabra no enruta: no
                                reparte, solo captura
    un solo hijo                una rama con un hijo encadena en vez de
                                ramificar, que es otra figura

Ninguno de los siete aporta nombre —son `T`— asi que retirarlos NO puede
quitar vocabulario del prompt. Lo unico que pueden estar haciendo es ganar una
de las plazas del emparejador y pasarsela a su hijo, o gastarla.

POR QUE ESTA MEDICION ES BARATA, Y LAS DE ANADIR NO
---------------------------------------------------
La asimetria la fijo el propio veredicto: quitar un nombre casi nunca baja la
precision, anadirlo si puede. Aqui ni siquiera hay nombres que quitar, asi que
el riesgo esta acotado por construccion y los siete caben en una sola tanda.

LA REGLA DE DECISION, ESCRITA ANTES DE MIRAR EL RESULTADO:

    si los bancos NO se mueven  ->  se retiran: no estaban enrutando
    si baja la cobertura        ->  se quedan: estaban enrutando

    python -m scripts.tanda_de_retirada
"""
from __future__ import annotations

import os
import sys

sys.stdout.reconfigure(encoding="utf-8")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

#: Los siete, con el motivo por el que su rol es discutible.
LOS_SIETE = {
    "algebraic-combinatorics": "1 palabra clave",
    "probabilistic-method": "1 palabra clave",
    "ramsey-theory": "1 palabra clave",
    "analytic-number-theory": "1 palabra clave",
    "discrete-optimization": "1 hijo: encadena, no ramifica",
    "linear-programming": "1 hijo: encadena, no ramifica",
    "variational-methods": "1 hijo: encadena, no ramifica",
}


def _medir(quitar=()):
    """Precision y cobertura lexicas contra ProofNet, sin los `quitar`."""
    import warnings
    import logging
    warnings.filterwarnings("ignore")
    logging.disable(logging.WARNING)

    from nucleo.core import Nucleo
    from nucleo.graph.category import SkillCategory
    # `PLAZAS_CON_NOMBRES` y no un 2 a mano: el guardian
    # `test_ningun_medidor_fija_k_a_mano` existe justo para esto, y tiene
    # razon — un medidor con la k fijada mide otro sistema.
    from nucleo.core import PLAZAS_CON_NOMBRES as K
    from scripts.recuperacion_contra_proofnet import (
        cargar, nombres_de_oro, ofrecidos_de)

    filas = cargar()
    n = Nucleo.__new__(Nucleo)
    n._graph = SkillCategory()
    Nucleo._load_foundational_skills(n)
    g = n._graph
    for sid in quitar:
        g.remove_skill(sid)

    # EL MISMO CAMINO QUE EL BRAZO `lexico` DEL BANCO, linea por linea. La
    # primera version se salto dos detalles —no descartaba las filas sin oro,
    # y volvia a normalizar lo que ya venia normalizado— y daba 23,1 % donde
    # el banco da 23,9 %. La comparacion pareada habria salido igual, pero un
    # medidor que no reproduce la cifra publicada no se puede citar junto a
    # ella.
    tp = fp = fn = 0
    con_algo = 0
    for _nombre, informal, formal in filas:
        oro = nombres_de_oro(formal)
        if not oro:
            continue
        skills = Nucleo._match_skills_to_query(n, informal, g)
        ofre = ofrecidos_de(n, skills, K, informal)
        if ofre:
            con_algo += 1
        tp += len(ofre & oro)
        fp += len(ofre - oro)
        fn += len(oro - ofre)
    prec = 100.0 * tp / (tp + fp) if tp + fp else 0.0
    cob = 100.0 * tp / (tp + fn) if tp + fn else 0.0
    return prec, cob, con_algo, len(filas)


def _cuantas_veces_salen():
    """Cuantas consultas de ProofNet emparejan con cada uno de los siete.

    Sin esto, un cero de diferencia es ambiguo: puede querer decir «no
    enrutaban» o «este banco no los ve». Son cosas opuestas.
    """
    import warnings
    import logging
    warnings.filterwarnings("ignore")
    logging.disable(logging.WARNING)

    from nucleo.core import Nucleo
    from nucleo.graph.category import SkillCategory
    from scripts.recuperacion_contra_proofnet import cargar

    n = Nucleo.__new__(Nucleo)
    n._graph = SkillCategory()
    Nucleo._load_foundational_skills(n)
    g = n._graph
    veces = {sid: 0 for sid in LOS_SIETE}
    for _nombre, informal, _formal in cargar():
        for s in Nucleo._match_skills_to_query(n, informal, g):
            sid = s if isinstance(s, str) else getattr(s, "id", None)
            if sid in veces:
                veces[sid] += 1
    return veces


def main() -> int:
    print("LA TANDA DE RETIRADA · %d nodos-rama discutibles\n" % len(LOS_SIETE))
    for sid, motivo in sorted(LOS_SIETE.items()):
        print("   %-26s %s" % (sid, motivo))
    print()

    # ── LA ALARMA DE INSTRUMENTO ROTO ───────────────────────────────────
    #
    # ProofNet son 371 ejercicios de Rudin, Artin, Munkres y Dummit-Foote: no
    # trae ni un ejercicio de Ramsey ni de programacion lineal. Si ninguna de
    # sus consultas llega a estos siete nodos, la diferencia SIEMPRE va a
    # salir cero y el cero no significa «no enrutaban» sino «aqui no se les
    # ve». Es exactamente el error que costo la primera tanda, del reves.
    #
    # Asi que primero se pregunta si el instrumento los ve, y solo despues se
    # mira el numero.
    veces = _cuantas_veces_salen()
    total = sum(veces.values())
    print("   ¿LOS VE ESTE BANCO? consultas de ProofNet que emparejan con cada uno:")
    for sid, n_veces in sorted(veces.items(), key=lambda kv: -kv[1]):
        print("      %-26s %3d" % (sid, n_veces))
    print()
    if total == 0:
        print("   INSTRUMENTO CIEGO PARA ESTOS SIETE: ninguna consulta de "
              "ProofNet\n   llega a ellos, asi que la diferencia va a ser cero "
              "por construccion\n   y no dice nada. Hace falta un banco que "
              "vea sus temas.\n")

    con = _medir()
    sin = _medir(quitar=tuple(LOS_SIETE))
    print("                        precision   cobertura   ofrece algo")
    print("   con los siete          %5.1f %%     %5.1f %%     %d de %d"
          % (con[0], con[1], con[2], con[3]))
    print("   sin los siete          %5.1f %%     %5.1f %%     %d de %d"
          % (sin[0], sin[1], sin[2], sin[3]))
    print("   diferencia             %+5.1f       %+5.1f       %+d"
          % (sin[0] - con[0], sin[1] - con[1], sin[2] - con[2]))
    print()

    # LA REGLA ESTABA ESCRITA ANTES. Se aplica tal cual, sin reinterpretarla
    # a la vista del numero — que es la unica forma de que una regla sirva.
    # Pero se aplica SOLO A LOS QUE EL BANCO VE: para los demas el cero no es
    # un resultado, es la ausencia de uno.
    vistos = sorted(k for k, v in veces.items() if v)
    ciegos = sorted(k for k, v in veces.items() if not v)
    if sin[1] < con[1] - 0.05:
        print("   SE QUEDAN. La cobertura baja %.1f puntos al quitarlos, "
              "luego estaban\n   enrutando: alguna consulta llegaba a su hijo "
              "por ellos." % (con[1] - sin[1]))
        return 0
    if vistos:
        print("   DECIDIDOS (%d de %d) · SE RETIRAN: %s"
              % (len(vistos), len(LOS_SIETE), ", ".join(vistos)))
        print("   ProofNet los ve —los empareja en alguna consulta— y "
              "quitarlos no mueve\n   ni la precision ni la cobertura: no "
              "estaban enrutando nada.\n")
    if ciegos:
        print("   SIN DECIDIR (%d de %d): %s"
              % (len(ciegos), len(LOS_SIETE), ", ".join(ciegos)))
        print("   NINGUNA consulta de ProofNet llega a ellos, asi que su cero "
              "no dice «no\n   enrutaban» sino «aqui no se les ve». Decidirlos "
              "con esta cifra seria el\n   mismo error que la primera tanda, "
              "del reves: entonces ProofNet solo podia\n   medir el COSTE de "
              "unos nodos y se uso para juzgar su beneficio. Faltan\n   "
              "`banco_docstrings` y `banco_herald`, que si ven sus temas.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
