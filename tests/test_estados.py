# -*- coding: utf-8 -*-
"""La categoría de estados de prueba: objetos = estados, morfismos = tácticas.

Se testea sobre grafos sintéticos: el corpus real son 25 206 transiciones y un
dataset de 2 GB, y lo que hay que vigilar aquí son las LEYES, que no dependen
del tamaño. Las cifras del corpus las mide `scripts/categoria_de_estados.py` y
las guarda en `data/categoria_de_estados.json`.
"""
import pytest

from nucleo.graph.estados import (TERMINAL, CategoriaDeEstados, Flecha,
                                  construir, normalizar, tactica_de)


@pytest.fixture
def cadena():
    """Dos pasos que cierran: A --intro--> B --ring--> no goals."""
    return construir([
        ("h : x = 1\n⊢ x + 1 = 2", "intro h", "h : x = 1\n⊢ 1 + 1 = 2"),
        ("h : x = 1\n⊢ 1 + 1 = 2", "ring", TERMINAL),
    ])


class TestLaIdentidadDeObjeto:
    """Cuándo dos estados son EL MISMO. Es lo que decide si hay categoría."""

    def test_los_nombres_de_hipotesis_no_distinguen(self):
        """Lean genera `h`, `h₁`, `a✝`; el objeto matemático es el mismo."""
        assert normalizar("h : p\n⊢ q") == normalizar("hab : p\n⊢ q")

    def test_el_objetivo_si_distingue(self):
        assert normalizar("h : p\n⊢ q") != normalizar("h : p\n⊢ r")

    def test_el_espacio_sobrante_no_distingue(self):
        assert normalizar("h : p\n\n  ⊢ q") == normalizar("h : p ⊢ q")


class TestLaTactica:

    def test_se_queda_el_nombre_sin_argumentos(self):
        assert tactica_de("nlinarith [sq_nonneg (a-b)]") == "nlinarith"
        assert tactica_de("  simp  ") == "simp"

    def test_una_linea_sin_tactica_no_es_morfismo(self):
        assert tactica_de("") == "" and tactica_de("<;>") == ""


class TestLasLeyesDeCategoria:

    def test_la_identidad_existe_para_todo_objeto(self, cadena):
        for o in cadena.objetos:
            i = cadena.identidad(o)
            assert i.origen == i.destino == o

    def test_componer_encaja_o_devuelve_none(self, cadena):
        f, g = cadena.flechas[0], cadena.flechas[1]
        assert cadena.componer(f, g) == [f, g]
        assert cadena.componer(g, f) is None, (
            "no se puede aplicar una táctica a un estado que no es el suyo")

    def test_la_composicion_es_la_secuencia_y_no_se_colapsa(self, cadena):
        """El morfismo compuesto ES la secuencia de tácticas.

        Colapsarlo en una flecha nueva perdería justo lo que se quiere
        aprender: qué pasos se dieron y en qué orden.
        """
        comp = cadena.componer(cadena.flechas[0], cadena.flechas[1])
        assert [f.tactica for f in comp] == ["intro", "ring"]


class TestElObjetoTerminal:

    def test_no_goals_es_terminal(self, cadena):
        assert cadena.es_terminal(TERMINAL)
        assert not cadena.salientes.get(TERMINAL), (
            "de `no goals` no sale ninguna táctica: no queda nada que hacer")

    def test_una_flecha_que_cierra_lo_dice(self, cadena):
        assert cadena.flechas[1].cierra and not cadena.flechas[0].cierra


class TestRecorrer:

    def test_el_camino_llega_al_terminal(self, cadena):
        r = cadena.raices()
        assert len(r) == 1
        cam = cadena.camino(r[0])
        assert [f.tactica for f in cam] == ["intro", "ring"]
        assert cam[-1].cierra

    def test_el_tope_corta_y_no_cuelga(self):
        """El dato viene de fuera: un ciclo no debe colgar al que recorra."""
        c = construir([("⊢ a", "simp", "⊢ b"), ("⊢ b", "simp", "⊢ a")])
        assert len(c.camino("⊢ a", tope=5)) <= 5


class TestLasParalelas:
    """Lo único que esta categoría afirma y un árbol no podría."""

    def test_dos_tacticas_al_mismo_sitio_son_paralelas(self):
        c = construir([("⊢ a = a", "ring", TERMINAL),
                       ("⊢ a = a", "ring_nf", TERMINAL)])
        par = c.paralelas()
        assert len(par) == 1
        _o, destino, tacs = par[0]
        assert destino == TERMINAL and tacs == ["ring", "ring_nf"]

    def test_la_misma_tactica_repetida_no_es_una_paralela(self):
        """Es el error que me comí contando: 341 en vez de 16.

        Dos filas del corpus con el mismo origen, la misma táctica y el mismo
        destino son la MISMA flecha vista dos veces, no dos morfismos
        distintos. Contarlas infla la única cifra que esta categoría aporta.
        """
        c = construir([("⊢ a = a", "ring", TERMINAL),
                       ("⊢ a = a", "ring", TERMINAL)])
        assert c.paralelas() == []

    def test_dos_tacticas_a_sitios_distintos_no_son_paralelas(self):
        c = construir([("⊢ a", "simp", "⊢ b"), ("⊢ a", "norm_num", "⊢ c")])
        assert c.paralelas() == []


class TestConstruir:

    def test_se_descarta_lo_que_no_es_transicion(self):
        c = construir([
            ("sin turnstile", "simp", TERMINAL),   # sin objetivo
            ("⊢ a", "", TERMINAL),                 # sin tactica
            ("⊢ a", "simp", TERMINAL),             # buena
        ])
        assert len(c.flechas) == 1

    def test_una_categoria_vacia_no_revienta(self):
        c = CategoriaDeEstados()
        assert c.paralelas() == [] and c.raices() == []
        assert "0 objetos" in repr(c)
