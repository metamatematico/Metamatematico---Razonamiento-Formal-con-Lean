# -*- coding: utf-8 -*-
"""El traductor es→en: lo que NO puede romper.

Los alumnos preguntan en español y todo lo que el grafo compara está en inglés.
La traducción es la lente para consultarlo, y tiene dos formas de estropear más
de lo que arregla:

  · traducir un texto que ya venía en inglés
  · destrozar la notación

Lo segundo está medido sobre el modelo desnudo, sin protección:

    $x^2 - 5x + 6$          ->  $x^2 - 5x + $6
    \mathbb{R}$             ->  \mathbb{R$
    \int_0^\infty ... dx$   ->  int_0=infty ... dx$   (destruido)
    \sin x                  ->  \without x

El último es el que lo explica: `\sin` es el seno, y «sin» en español es una
preposición. Estas guardias no necesitan el modelo —van sobre la protección y
la detección, que es donde estuvieron los fallos— así que corren siempre.
"""
import pytest

from nucleo.graph.traductor import (NOTACION, es_espanol, proteger, restaurar)


class TestDeteccion:

    @pytest.mark.parametrize("texto", [
        "¿Es 17 un número primo?",
        "Demuestra que un grupo de orden primo es cíclico",
        r"Calcula $\int_0^\infty \frac{\sin x}{x}\,dx$.",
        "Sea G un grupo finito",
    ])
    def test_reconoce_el_castellano(self, texto):
        assert es_espanol(texto)

    @pytest.mark.parametrize("texto", [
        "Prove that if $r$ is rational and $x$ is irrational then $r+x$ is irrational.",
        "Let $G$ be a group of order $p$ with $p$ prime. Show that $G$ is cyclic.",
        "Compute the sum of the first 100 positive integers.",
        r"Show that $\sin x < x$ for all $x > 0$.",
    ])
    def test_el_ingles_pasa_directo(self, texto):
        r"""Traducir de inglés a inglés sólo mete ruido.

        El último caso es el que importa: `\sin` trae dentro la palabra «sin»,
        que en español es una preposición. Si la detección mirase el texto CON
        la notación, ese enunciado inglés se marcaría como español.
        """
        assert not es_espanol(texto)

    def test_una_senal_fuerte_basta(self):
        r"""`Calcula $\int...$` se quedaba sin traducir.

        Al quitar la notación sólo sobrevivía una palabra española, y el umbral
        pedía dos señales. Por eso las señales van en dos pesos.
        """
        assert es_espanol(r"Calcula $\int_0^\infty f(x)\,dx$.")


class TestProteccion:

    @pytest.mark.parametrize("texto", [
        r"Sea $f(x) = x^2 - 5x + 6$. Encuentra las raíces.",
        r"Demuestra que $(a+b)^2 = a^2 + 2ab + b^2$ para todo $a,b \in \mathbb{R}$.",
        r"Calcula $\int_0^\infty \frac{\sin x}{x}\,dx$.",
        r"Si $G$ es un grupo de orden $p$ primo, entonces $G$ es cíclico.",
    ])
    def test_la_notacion_vuelve_intacta(self, texto):
        """Proteger y restaurar sin traducir por medio tiene que ser la identidad."""
        protegido, piezas = proteger(texto)
        assert piezas, "no se detectó notación en %r" % texto
        vuelto = restaurar(protegido, piezas)
        for p in piezas:
            assert p in vuelto, "se perdió %r" % p

    def test_lo_que_el_traductor_pierda_se_pega_detras(self):
        """Perder notación EN SILENCIO sería peor que no traducir."""
        _, piezas = proteger(r"Calcula $\int_0^1 x\,dx$ y $\sum_{n=1}^5 n$.")
        assert len(piezas) >= 2
        # el traductor devuelve una frase sin ninguna marca
        vuelto = restaurar("Calculate and .", piezas)
        for p in piezas:
            assert p in vuelto

    def test_no_quedan_restos_de_marca_en_el_texto(self):
        """Con `QQ%dQQ` salía `$p$Q order group`: una Q suelta metida dentro.

        El modelo duplica letras en los bordes de la marca, así que el patrón
        es tolerante y lo que sobre se borra.
        """
        _, piezas = proteger("Sea $G$ un grupo de orden $p$.")
        vuelto = restaurar("Let MTHH0MTH be a group of order MTH1MTHH.", piezas)
        assert "$G$" in vuelto and "$p$" in vuelto
        assert "MTH" not in vuelto and not any(
            c in vuelto.replace("$G$", "").replace("$p$", "")
            for c in ("MTHH", "MTHH"))

    def test_la_notacion_suelta_tambien_se_protege(self):
        r"""Los alumnos escriben `\sin x < x` sin dólares, y `\sin` se traducía."""
        assert NOTACION.search(r"demuestra que \sin x < x")
