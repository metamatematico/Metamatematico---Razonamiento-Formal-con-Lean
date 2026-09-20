# -*- coding: utf-8 -*-
"""Dos fallos que sólo se vieron probando el modelo con una consulta real.

Los dos son de la misma familia y es la más difícil de cazar: nada falla, no
salta ningún error, y el sistema contesta otra cosa.

  1. El DESEMPATE del clasificador de área era `max()` sobre un diccionario,
     que ante un empate devuelve la primera clave. Y la primera es `algebra`,
     que además es la clase mayoritaria del banco. Un desempate que es una
     constante disfrazada de criterio.

  2. La palabra `the` no estaba en `_GENERICAS` y sí está en el nombre de
     cuatro nodos —«The Different Ideal», «The Upper Half Plane»…—, así que
     CUALQUIER consulta en inglés que la contuviera activaba esos cuatro,
     dijera lo que dijera.

Lo que se vigila no son las cifras del banco, que cambiarán: es que el
mecanismo no vuelva. Las cifras viven en `data/parada_y_desempate.json`.
"""
import pytest

from nucleo.multi_agent.specialized_agent import (CATEGORIES,
                                                  _CATEGORY_KEYWORDS,
                                                  classify_query)


class TestElDesempateNoEsUnaConstante:

    def test_la_raiz_de_2_irracional_no_es_algebra(self):
        """El caso exacto que lo destapó, en una consulta real."""
        assert classify_query("Is the square root of 2 irrational?") == \
            "number-theory"

    def test_gana_la_coincidencia_mas_larga_y_no_la_primera_de_la_lista(self):
        """`irrational` (10 letras) pesa más que `root` (4).

        Es el criterio entero: una coincidencia larga es evidencia más
        específica que una corta, que sale en media biblioteca.
        """
        t = "is the square root of 2 irrational?"
        alg = [k for k in _CATEGORY_KEYWORDS["algebra"] if k in t]
        nt = [k for k in _CATEGORY_KEYWORDS["number-theory"] if k in t]
        assert len(alg) == len(nt) == 1, (
            "si este empate deja de existir el test ya no prueba el "
            "desempate: hay que buscar otro caso empatado")
        assert max(map(len, nt)) > max(map(len, alg))
        assert classify_query(t) == "number-theory"

    def test_algebra_no_gana_solo_por_ir_primera(self):
        """El orden de CATEGORIES no puede decidir nada por su cuenta."""
        assert CATEGORIES[0] == "algebra", (
            "el test se apoya en que algebra va primera; si cambia el orden "
            "hay que revisar que el desempate siga sin depender de el")
        t = "is the square root of 2 irrational?"
        assert classify_query(t) != CATEGORIES[0]

    def test_sin_ninguna_coincidencia_responde_la_mayoritaria(self):
        """El suelo va declarado, y es el modelo nulo. No es un acierto."""
        assert classify_query("qwerty zxcvbn") == "algebra"

    def test_una_mayoria_clara_sigue_ganando(self):
        """El desempate sólo actúa en el empate: no reordena lo demás."""
        assert classify_query("compute the derivative and the integral "
                              "of this function") == "analysis"


class TestLasPalabrasDeParadaNoSonEvidencia:

    @pytest.fixture(scope="class")
    def grafo(self):
        from nucleo.core import Nucleo
        from nucleo.graph.category import SkillCategory
        n = Nucleo.__new__(Nucleo)
        n._graph = SkillCategory()
        Nucleo._load_foundational_skills(n)
        return n, n._graph

    def test_the_esta_en_genericas(self):
        from nucleo.core import _GENERICAS
        assert "the" in _GENERICAS, (
            "`the` esta en el nombre de cuatro nodos, asi que sin esto "
            "cualquier consulta en ingles que la contenga los activa")

    def test_ninguna_palabra_de_parada_queda_suelta(self, grafo):
        """El guardián general: si mañana entra un nodo «The …» o «A …».

        No comprueba una lista fija de nodos, que cambiará: comprueba que
        ninguna palabra de parada quede fuera de `_GENERICAS` estando dentro
        de algún nombre del grafo.
        """
        from nucleo.core import _GENERICAS
        from nucleo.texto import tokens as _tok
        _, g = grafo
        PARADA = {"the", "of", "a", "an", "and", "or", "in", "on", "to", "is",
                  "for", "with", "by", "from", "as", "that", "this", "it",
                  "el", "la", "los", "las", "un", "una", "de", "del", "y",
                  "en", "con", "por", "para", "que", "se", "su", "al", "lo"}
        presentes = set()
        for s in g.skills:
            presentes |= (_tok(s.id) | _tok(s.name)) & PARADA
        sueltas = sorted(presentes - set(_GENERICAS))
        assert not sueltas, (
            "estas palabras de parada estan en el nombre de algun nodo y NO "
            "en _GENERICAS, asi que abren la puerta ellas solas: %s" % sueltas)

    def test_la_consulta_real_ya_no_activa_los_cuatro_espurios(self, grafo):
        from nucleo.core import Nucleo
        n, g = grafo
        activadas = set(Nucleo._match_skills_to_query(
            n, "Is the square root of 2 irrational?", g))
        espurios = {"different-ideal", "upper-half-plane", "simplex-category",
                    "unit-circle"}
        assert not (activadas & espurios), (
            "ninguno de estos cuatro tiene una palabra clave que hable de "
            "raices ni de irracionalidad: casaban por `the`")

    def test_the_acompanada_sigue_valiendo(self, grafo):
        """Quitar ruido no puede cerrar la puerta a lo legítimo.

        `_GENERICAS` rechaza sólo cuando TODAS las coincidencias son
        genéricas. «the unit circle» casa por `unit` y `circle`, así que el
        nodo sigue entrando — y eso es lo que separa este arreglo de
        romperlo.
        """
        from nucleo.core import Nucleo
        n, g = grafo
        assert "unit-circle" in Nucleo._match_skills_to_query(
            n, "the unit circle is compact", g)
        assert "simplex-category" in Nucleo._match_skills_to_query(
            n, "the simplex category", g)


class TestLaNotacionDePuntoNoEsUnaInvencion:
    """`hf.continuous` es idiomático, y se le enseñaba al alumno como error.

    En Lean, si `hf : Continuous f`, escribir `hf.continuous` resuelve a
    `Continuous.continuous hf`. Ese nombre no esta en el indice de Mathlib y
    no tiene por que estarlo. Medido sobre las 66 formalizaciones grabadas:
    33 de los nombres que `revisar_codigo` marcaba son notacion de punto y 26
    son invenciones de verdad — mas falsos positivos que verdaderos.
    """

    def test_el_indice_distingue_las_dos_familias(self):
        from nucleo.lean import nombres as N
        if not N.disponible():
            import pytest
            pytest.skip("sin indice de nombres")
        # prefijo que NO es namespace -> variable local
        for n in ("hf.continuous", "s.Nonempty", "P.det", "hU.union"):
            assert not N.existe_namespace(n.split(".")[0]), (
                "%s deberia ser notacion de punto sobre una local" % n)
        # prefijo que SI es namespace -> nombre de verdad
        for n in ("Nat.prime_of_mem_factors", "Basis.exists_basis"):
            assert N.existe_namespace(n.split(".")[0]), (
                "%s lleva un namespace real: si falla, es una invencion" % n)

    def test_core_filtra_la_notacion_de_punto(self):
        """Que nadie quite el filtro sin enterarse."""
        import io
        import os
        ruta = os.path.join(os.path.dirname(os.path.dirname(
            os.path.abspath(__file__))), "nucleo", "core.py")
        s = io.open(ruta, encoding="utf-8").read()
        assert "_es_punto_local" in s, (
            "core.py ya no filtra la notacion de punto: el panel vuelve a "
            "decirle al alumno que `hf.continuous` no existe en Mathlib")
        i = s.index("_desconocidos = [f for f in")
        assert "_es_punto_local" in s[i:i + 300], (
            "el filtro existe pero ya no se aplica donde se construye "
            "`_desconocidos`, que es lo que llega al panel")
