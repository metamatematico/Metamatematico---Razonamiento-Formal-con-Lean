# -*- coding: utf-8 -*-
"""El panel que le dice al alumno qué hizo el sistema con su consulta.

QUE SE VIGILA
-------------
No la redacción, que cambiará. Las cuatro reglas que hacen que un panel de
explicabilidad explique algo en vez de decorar:

  1. lo que NO se usó se enseña igual que lo que sí, con su motivo;
  2. una cifra va con su modelo nulo o no va;
  3. lo que falta se dice, no desaparece;
  4. el panel breve cabe en una pantalla, y el completo no se pierde.

Y el ida y vuelta por el diccionario, que es el camino real: el núcleo mete
`a_dict()` en los metadatos y `app.py` lo reconstruye para pintarlo. Si las
claves dejan de encajar, el alumno deja de ver el panel y nada más falla.
"""
import pytest

from nucleo.explicabilidad import (Explicacion, Paso, en_markdown, explicar)


class _Cap:
    def __init__(self, nombre, que_hace):
        self.nombre = nombre
        self.que_hace = que_hace


class _Plan:
    """Un plan del decisor, con lo justo que `explicar` le pide."""
    def __init__(self):
        self.activas = [_Cap("nombres_de_mathlib_en_el_prompt",
                             "inyecta nombres verificados")]
        self.apagadas = [_Cap("emparejador_semantico",
                              "empareja por embeddings")]
        self.motivos = {"emparejador_semantico":
                        "NO bate a su nulo: 13,2 % contra 23,9 % del lexico"}
        self.veredictos = {}
        self.coste = {"llamada": 1, "compilado": 1}


@pytest.fixture
def exp():
    return explicar(
        area="LinearAlgebra", lectura="",
        contexto={"relevant_skills": ["linear-algebra"],
                  "mathlib_verificado": {"linear-algebra": ["Module.Basis"]},
                  "procedencia": "emparejador"},
        plan=_Plan(), rondas=2, estado_lean="ERROR",
        error_lean="type mismatch", veredicto="no_verificado")


class TestLoQueNoSeUsaTambienSeCuenta:
    """La regla que más dice de este sistema."""

    def test_una_capacidad_apagada_aparece_con_su_motivo(self, exp):
        nombres = [a["nombre"] for a in exp.apagadas]
        assert "emparejador_semantico" in nombres
        a = next(x for x in exp.apagadas if x["nombre"] == "emparejador_semantico")
        assert "nulo" in a["por_que"], (
            "una capacidad apagada sin decir por qué es ruido: lo que explica "
            "es que se midió y perdió")

    def test_el_panel_las_pinta(self, exp):
        md = en_markdown(exp)
        assert "Qué NO se usó" in md
        assert "emparejador_semantico" in md

    def test_las_medidas_van_antes_que_las_que_no_aplicaban(self):
        """«Se midió y perdió» enseña más que «su guarda no aplicaba»."""
        e = Explicacion(
            pasos=[Paso("x", "X", detalle="d")],
            apagadas=[{"nombre": "guarda", "que_hace": "", "por_que":
                       "su guarda no aplica a esta consulta"},
                      {"nombre": "medida", "que_hace": "", "por_que":
                       "NO bate a su nulo: 0,4 contra 0,9"}])
        md = en_markdown(e)
        assert md.index("medida") < md.index("guarda")


class TestCadaCifraConSuNulo:

    def test_el_vocabulario_no_se_publica_sin_su_nulo(self, exp):
        p = next(p for p in exp.pasos if p.clave == "vocabulario")
        assert p.items, "la fixture ofrece un nombre"
        assert "1,45" in p.respaldo and "23,9" in p.respaldo, (
            "un 23,9 % sin decir que el azar da 1,45 % no explica nada: no se "
            "sabe si es mucho o poco")

    def test_sin_nombres_no_se_inventa_respaldo(self):
        e = explicar(contexto={})
        p = next(p for p in e.pasos if p.clave == "vocabulario")
        assert not p.respaldo, (
            "si no se ofreció ningún nombre, citar la precisión del "
            "vocabulario es citar una cifra que no se usó aquí")


class TestLoQueFaltaSeDice:

    def test_sin_area_ni_lectura_lo_dice(self):
        p = next(p for p in explicar().pasos if p.clave == "entendi")
        assert "no consta" in p.detalle

    def test_sin_skills_lo_dice(self):
        p = next(p for p in explicar(contexto={}).pasos if p.clave == "grafo")
        assert "ningún concepto" in p.detalle

    def test_sin_plan_no_hay_paso_de_decisor_pero_no_revienta(self):
        e = explicar(contexto={"relevant_skills": ["x"]}, plan=None)
        assert [p.clave for p in e.pasos]
        assert not e.apagadas and not e.coste


class TestElPanelBreve:

    def test_el_breve_es_mas_corto_que_el_completo(self):
        e = Explicacion(
            pasos=[Paso("x", "X", detalle="d", items=["i%d" % i
                                                      for i in range(12)])],
            apagadas=[{"nombre": "c%d" % i, "que_hace": "",
                       "por_que": "NO bate a su nulo. " + "y " * 200}
                      for i in range(9)])
        breve, largo = en_markdown(e), en_markdown(e, breve=False)
        assert len(breve) < len(largo) / 2

    def test_el_breve_dice_cuantas_se_deja(self):
        e = Explicacion(
            pasos=[Paso("x", "X", detalle="d")],
            apagadas=[{"nombre": "c%d" % i, "que_hace": "", "por_que": "m"}
                      for i in range(9)])
        assert "5 capacidades más apagadas" in en_markdown(e)

    def test_no_corta_a_mitad_de_palabra(self):
        e = Explicacion(
            pasos=[Paso("x", "X", detalle="d")],
            apagadas=[{"nombre": "c", "que_hace": "",
                       "por_que": "palabra " * 80}])
        md = en_markdown(e)
        assert "palabr\n" not in md and "palabr —" not in md


class TestElCaminoReal:
    """Núcleo -> metadatos -> app.py. Si esto se rompe, el panel desaparece."""

    def test_el_dict_reconstruye_la_explicacion(self, exp):
        d = exp.a_dict()
        rehecha = Explicacion(pasos=[Paso(**p) for p in d["pasos"]],
                              apagadas=d["apagadas"], coste=d["coste"])
        assert en_markdown(rehecha) == en_markdown(exp), (
            "`app.py` reconstruye el panel con `Paso(**d)` desde los "
            "metadatos; si las claves de `a_dict` dejan de encajar con el "
            "constructor, el alumno deja de ver el panel y nada mas falla")

    def test_el_nucleo_mete_la_clave_en_los_metadatos(self):
        """Que nadie quite el cable sin enterarse."""
        import ast
        import io
        import os
        ruta = os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), "nucleo", "core.py")
        arbol = ast.parse(io.open(ruta, encoding="utf-8").read())
        claves = {n.value for n in ast.walk(arbol)
                  if isinstance(n, ast.Constant) and isinstance(n.value, str)}
        assert "explicabilidad" in claves, (
            "core.py ya no mete `explicabilidad` en los metadatos de la "
            "respuesta: el panel del chat se queda vacio")
