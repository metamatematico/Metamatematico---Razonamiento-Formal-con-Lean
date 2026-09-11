# -*- coding: utf-8 -*-
"""Que una capa MEDIDA este ademas CABLEADA.

POR QUE EXISTE ESTE FICHERO
---------------------------
La arquitectura por capas se puede describir entera, medir entera y aun asi no
correr. Paso: `TacticRanker` estaba entrenado, guardado en disco y medido
—1,57 posiciones frente a 2,44 de su nulo, 3,7x menos invocaciones de Lean que
el orden fijo— y `set_tactic_ranker` NO LO LLAMABA NADIE. El `getattr` de
`_orden_inteligente` devolvia None en todas las consultas y la cascada corria
solo con la heuristica. Lo mismo con L4: `cargar_coocurrencia_verificada`
existia en CR_org y en la fachada, y el paisaje se seguia sembrando con lo que
el emparejador lexico adivinaba.

Ninguna de las dos cosas da error. Los tests pasaban, las mediciones eran
ciertas y la documentacion describia un sistema que no era el que corria. Es
la familia de fallo que este repositorio persigue: el sistema afirma con mas
autoridad de la que tiene.

Estos tests no comprueban que las capas sean buenas —para eso estan sus
mediciones— sino que ESTAN ENCHUFADAS.
"""
from __future__ import annotations

import pytest


# --------------------------------------------------------------------- L3
def test_l3_el_rankeador_llega_a_la_cascada():
    """La cascada tiene que poder recibir el rankeador, y aceptarlo."""
    from nucleo.lean.solver_cascade import SolverCascade, TacticRanker

    c = SolverCascade.__new__(SolverCascade)
    r = TacticRanker()
    c.set_tactic_ranker(r)
    assert getattr(c, "_tactic_ranker", None) is r


def test_l3_se_puede_apagar_con_none():
    """Y tiene que poder DESconectarse.

    La cascada vive entre consultas. Si apagar consistiera en no llamar, el
    rankeador se quedaria puesto desde la primera consulta que lo encendiera
    y la puerta del decisor no significaria nada.
    """
    from nucleo.lean.solver_cascade import SolverCascade, TacticRanker

    c = SolverCascade.__new__(SolverCascade)
    c.set_tactic_ranker(TacticRanker())
    c.set_tactic_ranker(None)
    assert getattr(c, "_tactic_ranker", "ausente") is None


def test_l3_core_construye_el_rankeador_y_lo_fija_por_consulta():
    """`core.py` tiene que hacer las dos cosas, y se comprueba en la FUENTE.

    Construir el objeto no basta: hay que pasarselo a la cascada. Se lee el
    fichero porque instanciar `Nucleo` entero pide entorno de Lean y clave de
    API, y este test tiene que correr sin ninguno de los dos.
    """
    import io
    from pathlib import Path

    src = io.open(Path(__file__).resolve().parent.parent / "nucleo" / "core.py",
                  encoding="utf-8").read()

    assert "self._tactic_ranker = TacticRanker()" in src, (
        "core.py no construye el TacticRanker: L3 no existe en el camino")
    assert "self._solver_cascade.set_tactic_ranker(" in src, (
        "core.py construye el TacticRanker y no se lo pasa a la cascada — "
        "medido y no cableado, que es justo el fallo que este fichero vigila")
    assert '"modelo_de_orden_de_cascada" in _corre' in src, (
        "el rankeador no pasa por el decisor: se encenderia sin que su "
        "evidencia lo gobierne")


def test_l3_esta_entre_las_capacidades_gobernadas():
    """Si no esta en `_TODAS_LAS_GOBERNADAS`, el respaldo lo apaga.

    Cuando el decisor falla, `core.py` cae a `_TODAS_LAS_GOBERNADAS`. Una
    capacidad cableada que falte de ese conjunto queda apagada EXACTAMENTE
    cuando el decisor no esta — degradacion silenciosa.
    """
    from nucleo.core import _TODAS_LAS_GOBERNADAS

    assert "modelo_de_orden_de_cascada" in _TODAS_LAS_GOBERNADAS


def test_l3_el_decisor_lo_enciende():
    """Su evidencia gana a su nulo, asi que el decisor debe activarlo."""
    from nucleo.decisor import Contexto, decidir

    plan = decidir(Contexto(consulta="demuestra que 2 + 2 = 4",
                            es_matematica=True, area="algebra", rasgos={}))
    activas = {c.nombre for c in plan.activas}
    assert "modelo_de_orden_de_cascada" in activas


def test_l3_el_rankeador_devuelve_una_permutacion():
    """SOUNDNESS. Es la hipotesis de `cascade_gnn_iff_exists`.

    Reordenar no puede hacer demostrable lo que no lo es. Si `rank` anadiera o
    quitara tacticas, el teorema de Lean dejaria de aplicar y el orden ya no
    seria libre para optimizar.
    """
    from nucleo.lean.solver_cascade import TacticRanker

    r = TacticRanker()
    if not r.disponible:
        pytest.skip("no hay modelo entrenado en data/tactic_ranker.pkl")

    entrada = [("simp", 2), ("ring", 2), ("linarith", 3), ("nlinarith", 4)]
    salida = r.rank("⊢ a + b = b + a", entrada)
    assert sorted(salida) == sorted(entrada), (
        "rank NO devolvio una permutacion: la soundness deja de estar cubierta")


# --------------------------------------------------------------------- L4
def test_l4_core_siembra_el_paisaje_con_teoremas_verificados():
    """El paisaje no puede alimentarse de las conjeturas del propio grafo."""
    import io
    from pathlib import Path

    src = io.open(Path(__file__).resolve().parent.parent / "nucleo" / "core.py",
                  encoding="utf-8").read()

    assert "cargar_coocurrencia_verificada()" in src, (
        "core.py no siembra L4: los colimites se ligarian sobre lo que el "
        "emparejador lexico adivino, no sobre teoremas que Lean acepto")


def test_l4_la_fachada_delega_en_cr_org():
    from nucleo.mes.co_regulators import CoRegulatorNetwork

    assert hasattr(CoRegulatorNetwork, "cargar_coocurrencia_verificada")


def test_l4_los_pares_traen_su_exceso_corregido():
    """La correccion por frecuencia es lo que hace fiable la coocurrencia.

    En crudo, el cuarto par mas frecuente es `cic + linear-algebra` con 134
    coocurrencias y exceso +0,11: azar puro, porque `cic` declara `Type` y eso
    sale en todos los enunciados. Sin el exceso, L4 mediria que palabras son
    comunes, no que conceptos se relacionan.
    """
    import io
    import json
    from pathlib import Path

    ruta = Path(__file__).resolve().parent.parent / "data" / \
        "l4_coocurrencia_verificada.json"
    if not ruta.exists():
        pytest.skip("no hay medicion de L4")

    d = json.load(io.open(ruta, encoding="utf-8"))
    assert d["pares"], "L4 sin ningun par"
    for p in d["pares"]:
        assert {"a", "b", "juntas", "esperadas", "exceso"} <= set(p)

    crudo = max(d["pares"], key=lambda p: p["juntas"])
    mejor = max(d["pares"], key=lambda p: p["exceso"])
    assert crudo != mejor, (
        "el par mas frecuente coincide con el de mayor exceso: la correccion "
        "no esta cambiando el orden, que es lo unico que aporta")
