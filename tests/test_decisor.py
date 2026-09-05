# -*- coding: utf-8 -*-
"""Tests del decisor: qué corre para una consulta, y por qué.

EL TEST QUE MÁS IMPORTA es `test_ninguna_ruta_de_evidencia_esta_rota`. El
decisor lee el veredicto de los ficheros de `data/`; si una ruta deja de
resolver —porque el script cambió el nombre de una clave— el veredicto pasa a
ser «no se puede leer» y la capacidad se apaga EN SILENCIO. Un decisor que
apaga cosas sin que nadie se entere es peor que no tener decisor.

El segundo que más importa es `test_lo_que_pierde_contra_su_nulo_no_corre`:
es la regla entera del módulo, y está escrito con una capacidad de mentira
para que no dependa de qué diga la evidencia real de hoy.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from nucleo.decisor import (CAPACIDADES, COMPILADO, Capacidad, Contexto,
                            Evidencia, LLAMADA, LOCAL, decidir, decidir_todo,
                            leer_veredicto)

RAIZ = pathlib.Path(__file__).resolve().parent.parent
DATOS = RAIZ / "data"


# ═══════════════════════════════════════════════════════════════════════════
# LA REGLA
# ═══════════════════════════════════════════════════════════════════════════
def _falsa(tmp_path, real, nulo, mas_es_mejor=True, coste=LOCAL, nucleo=False):
    (tmp_path / "f.json").write_text(json.dumps({"r": real, "n": nulo}),
                                     encoding="utf-8")
    return Capacidad(
        nombre="falsa", que_hace="prueba", coste=coste, nucleo=nucleo,
        evidencia=Evidencia(fichero="f.json", metrica="m",
                            ruta_real=("r",), ruta_nulo=("n",),
                            mas_es_mejor=mas_es_mejor))


def test_lo_que_gana_a_su_nulo_corre(tmp_path):
    cap = _falsa(tmp_path, 0.8, 0.3)
    d = decidir(Contexto(), [cap], datos=tmp_path)
    assert [c.nombre for c in d.activas] == ["falsa"]


def test_lo_que_pierde_contra_su_nulo_no_corre(tmp_path):
    """La regla entera del módulo. Da igual lo que diga la guarda."""
    cap = _falsa(tmp_path, 0.2, 0.3)
    cap.guarda = lambda ctx: True
    d = decidir(Contexto(), [cap], datos=tmp_path)
    assert [c.nombre for c in d.apagadas] == ["falsa"]
    assert "NO bate a su nulo" in d.motivos["falsa"]


def test_menos_es_mejor_cuando_la_metrica_es_una_posicion(tmp_path):
    """«Posición de la táctica que cierra»: 1,06 es mejor que 1,09."""
    cap = _falsa(tmp_path, 1.062, 1.091, mas_es_mejor=False)
    assert leer_veredicto(cap, tmp_path).gana is True
    cap2 = _falsa(tmp_path, 1.262, 1.091, mas_es_mejor=False)
    assert leer_veredicto(cap2, tmp_path).gana is False


def test_sin_evidencia_y_caro_no_se_gasta(tmp_path):
    cap = Capacidad(nombre="cara", que_hace="", coste=LLAMADA)
    d = decidir(Contexto(), [cap], datos=tmp_path)
    assert cap in d.apagadas


def test_sin_evidencia_pero_gratis_si_corre(tmp_path):
    cap = Capacidad(nombre="gratis", que_hace="", coste=LOCAL)
    d = decidir(Contexto(), [cap], datos=tmp_path)
    assert cap in d.activas


def test_el_nucleo_no_lo_decide_el_decisor(tmp_path):
    """Verificar con Lean no es un extra cuyo nulo sea no hacerlo: el nulo de
    «verificar» es «no verificar», que es otro sistema."""
    cap = Capacidad(nombre="lean", que_hace="", coste=COMPILADO, nucleo=True)
    d = decidir(Contexto(), [cap], datos=tmp_path)
    assert cap in d.activas
    assert "proposito del sistema" in d.motivos["lean"]


def test_la_guarda_solo_decide_entre_las_que_ganan(tmp_path):
    cap = _falsa(tmp_path, 0.8, 0.3)
    cap.guarda = lambda ctx: bool(ctx.rasgos.get("hay"))
    assert cap in decidir(Contexto(rasgos={"hay": 1}), [cap], tmp_path).activas
    assert cap in decidir(Contexto(rasgos={}), [cap], tmp_path).apagadas


def test_el_veredicto_se_relee_no_se_recuerda(tmp_path):
    """El número vive en el fichero, no en el código. Si alguien vuelve a
    medir y el resultado cambia, el decisor cambia con él —que es la única
    manera de que una conclusión vieja no siga mandando."""
    cap = _falsa(tmp_path, 0.8, 0.3)
    assert leer_veredicto(cap, tmp_path).gana is True
    (tmp_path / "f.json").write_text(json.dumps({"r": 0.1, "n": 0.3}),
                                     encoding="utf-8")
    assert leer_veredicto(cap, tmp_path).gana is False


def test_una_medicion_que_falta_no_cuenta_como_que_gana(tmp_path):
    cap = _falsa(tmp_path, 0.8, 0.3)
    (tmp_path / "f.json").unlink()
    v = leer_veredicto(cap, tmp_path)
    assert v.gana is None and "falta" in v.motivo


# ═══════════════════════════════════════════════════════════════════════════
# EL CATALOGO REAL
# ═══════════════════════════════════════════════════════════════════════════
@pytest.mark.parametrize("cap", [c for c in CAPACIDADES if c.evidencia],
                         ids=lambda c: c.nombre)
def test_ninguna_ruta_de_evidencia_esta_rota(cap):
    """EL TEST QUE MÁS IMPORTA.

    Si una ruta deja de resolver, el veredicto pasa a «no se puede leer» y la
    capacidad se apaga sin que nadie se entere. Un decisor que apaga cosas en
    silencio es peor que no tener decisor.
    """
    v = leer_veredicto(cap)
    assert v.gana is not None, "%s: %s" % (cap.nombre, v.motivo)
    assert v.real is not None and v.nulo is not None


@pytest.mark.parametrize("cap", CAPACIDADES, ids=lambda c: c.nombre)
def test_el_codigo_que_dice_estar_ahi_esta(cap):
    """`donde` tiene que apuntar a un fichero real: si no, el catálogo habla
    de una capacidad que ya no existe."""
    if not cap.donde:
        return
    fichero = cap.donde.split("::")[0]
    assert (RAIZ / fichero).exists(), "%s -> %s" % (cap.nombre, cap.donde)


def test_una_capacidad_sin_evidencia_tiene_que_explicarse():
    """Callar por qué no hay evidencia deja al lector sin saber si es que
    nadie midió o es que la medición no encaja."""
    for cap in CAPACIDADES:
        if cap.evidencia is None and not cap.nucleo:
            assert cap.sin_evidencia_porque, (
                "%s no dice por que no tiene evidencia" % cap.nombre)


def test_el_decisor_apaga_algo_que_hoy_esta_en_produccion():
    """Si el decisor no apagara nada, sería decoración.

    Hoy apaga el orden de cascada por área (1,262 contra 1,091 del nulo), la
    localización en dos etapas (0,42 contra 0,93) y la recuperación léxica de
    lemas (0,065 contra 7,78).
    """
    d = decidir(Contexto(rasgos={"sin_notacion": 0}))
    perdedoras = [c.nombre for c in d.apagadas
                  if "NO bate a su nulo" in d.motivos[c.nombre]]
    assert "orden_de_cascada_por_area" in perdedoras
    assert len(perdedoras) >= 3


def test_el_decisor_cuesta_menos_que_su_nulo():
    """El nulo del decisor es «ejecútalo todo». Si no ahorra, no decide."""
    ctx = Contexto(rasgos={"sin_notacion": 0})
    d, todo = decidir(ctx), decidir_todo(ctx)
    assert d.coste[COMPILADO] < todo.coste[COMPILADO]
    assert d.coste[LLAMADA] <= todo.coste[LLAMADA]


def test_core_consulta_al_decisor():
    """Sin esto el decisor sería un informe bonito que nadie lee."""
    fuente = (RAIZ / "nucleo" / "core.py").read_text(encoding="utf-8")
    assert "from nucleo.decisor import" in fuente
    assert '"orden_de_cascada_por_area" in _corre' in fuente


def test_la_guarda_del_estrato_parte_el_promedio():
    """Los rasgos del árbol suman +0,8 puntos en PROMEDIO —poco— pero en el
    estrato donde los n-gramas no aciertan ni un lema cubren el 12,9 % contra
    el 3,4 % del nulo. Son dos capacidades, no una: sintaxis y semántica no
    compiten por el mismo puesto, se reparten el trabajo.

    Si esta guarda desaparece, la segunda correría siempre y el número que la
    justifica dejaría de aplicar: está medido en un estrato, no en el todo.
    """
    n = "rasgos_de_sintaxis_cuando_el_lexico_calla"
    con_ruta = decidir(Contexto(rasgos={"sin_notacion": 0}, lexico_mudo=False))
    mudo = decidir(Contexto(rasgos={"sin_notacion": 0}, lexico_mudo=True))
    assert n not in [c.nombre for c in con_ruta.activas]
    assert n in [c.nombre for c in mudo.activas]
    # y sin notación no entra ni aunque el léxico calle: no habría de qué hablar
    sin_notacion = decidir(Contexto(rasgos={"sin_notacion": 1}, lexico_mudo=True))
    assert n not in [c.nombre for c in sin_notacion.activas]


def test_apagar_el_orden_no_vacia_la_etiqueta_de_la_memoria():
    """`_domain_tactic` NO llega a la cascada: va como etiqueta al reportar el
    resultado a la memoria de aprendizaje (`report_lean_result`).

    Al cablear el decisor la dejé en blanco junto con `_domain_order`, y eso
    no apagaba nada —la cascada recibe `_tactica_aprendida`— pero sí metía una
    táctica vacía en la memoria, que es peor que la que había. El guardián fija
    que sólo se apague el orden.
    """
    fuente = (RAIZ / "nucleo" / "core.py").read_text(encoding="utf-8")
    assert "_domain_tactic = domain_default_tactic(_area)" in fuente
    assert '_domain_tactic = ""' not in fuente, (
        "la etiqueta que va a la memoria no puede quedarse vacia")
    # y el orden sí depende del decisor
    assert '"orden_de_cascada_por_area" in _corre else []' in fuente
