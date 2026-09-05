# -*- coding: utf-8 -*-
"""La lista de sustantivos, y el negativo que impide volver a cablearla.

QUE HAY AQUI
------------
Dos cosas distintas, y conviene no confundirlas:

  · la LISTA es correcta y se guarda. 34 084 sustantivos leidos de la
    declaracion en el fuente de Mathlib, no deducidos de la ruta. Verificado
    con `#check`: 200 de 200 existen, frente al 77,4 % de los deducidos.

  · la VIA de inyectarlos —los sustantivos del modulo de cada nodo— se midio
    y PIERDE. A volumen igualado contra ProofNet:

        volumen ~1 800-2 000   sin: 14,0 % / 17,8 %   con: 11,5 % / 16,5 %
        volumen ~2 800-3 100   sin:  9,5 % / 18,9 %   con:  8,5 % / 19,1 %

El ultimo test de este fichero existe para que nadie vuelva a enchufarla sin
volver a medir. No dice «esto no sirve»: dice «esto se midio asi, y si lo
cambias, mide otra vez».
"""
import io
import json

import pytest

from nucleo.rutas import dato


@pytest.fixture(scope="module")
def lista():
    try:
        with io.open(dato("sustantivos_mathlib.jsonl"), encoding="utf-8") as fh:
            return [json.loads(l) for l in fh if l.strip()]
    except OSError:
        pytest.skip("sin data/sustantivos_mathlib.jsonl; "
                    "construir con scripts/construir_lista_sustantivos.py")


class TestLaLista:

    def test_tiene_volumen(self, lista):
        """Si baja de golpe, el extractor se rompio en silencio."""
        assert len(lista) > 30000, "solo %d sustantivos" % len(lista)

    def test_los_campos_estan(self, lista):
        for r in lista[:200]:
            for c in ("nombre", "corto", "tipo", "firma", "modulo",
                      "concepto", "citas"):
                assert c in r, "falta %s en %r" % (c, r.get("nombre"))

    def test_solo_sustantivos(self, lista):
        """`instance` NO entra: ya esta en la lista de hechos.

        Si las dos listas se solapan, la cobertura medida cuenta dos veces lo
        mismo y deja de significar nada.
        """
        tipos = {r["tipo"] for r in lista}
        assert tipos <= {"def", "structure", "class", "abbrev", "inductive"}, (
            "tipos inesperados: %s" % sorted(tipos - {
                "def", "structure", "class", "abbrev", "inductive"}))

    def test_ningun_nombre_es_una_variable_ligada(self, lista):
        """El fallo de `the` como lema mas citado, en su version sustantivo.

        Al contar citas sin filtrar, los mas citados salian `f`, `x`, `s` y
        `h` — variables ligadas de los enunciados, no declaraciones. El
        filtro es «4+ caracteres, o con `_` o `.`», el mismo que usa
        `nombres_de_oro`.
        """
        # QUE SE VIGILA, exactamente. No «que ningun nombre sea corto»: `Set`,
        # `Ab`, `log` y `Rel` son sustantivos legitimos de Mathlib con nombre
        # corto, y `Polynomial.X` es una cita cualificada perfectamente valida
        # aunque su `corto` sea una letra.
        #
        # Lo que delataba el fallo era la CIMA del ranking: con el conteo sin
        # filtrar, los mas citados eran `f`, `x`, `s` y `h`. Asi que el
        # invariante es que arriba no haya nombres DESNUDOS de una o dos
        # letras, que es la firma de haber contado variables ligadas.
        top = sorted(lista, key=lambda r: -r["citas"])[:100]
        malos = [r["nombre"] for r in top
                 if r["nombre"] == r["corto"] and len(r["corto"]) <= 2]
        assert not malos, (
            "nombres desnudos de 1-2 letras en la cima del ranking: %s "
            "— se estan contando variables ligadas" % malos[:10])

    def test_los_mas_citados_son_reconocibles(self, lista):
        """Cordura: los sustantivos que Mathlib mas usa deben ser los obvios.

        Si `Finset` y `Set` dejan de estar arriba, el conteo de citas se
        rompio — y se rompio de una forma que produce cifras creibles.
        """
        top = {r["corto"] for r in sorted(lista, key=lambda r: -r["citas"])[:40]}
        assert {"Finset", "Set"} & top, "los mas citados son raros: %s" % sorted(top)[:12]

    def test_el_orden_lo_mandan_las_citas(self):
        from nucleo.lean import sustantivos as S
        if not S.disponible():
            pytest.skip("lista no cargable")
        from nucleo.lean.sustantivos import _POR_MODULO, _cargar
        _cargar()
        grande = max(_POR_MODULO, key=lambda m: len(_POR_MODULO[m]))
        citas = [r.get("citas", 0) for r in _POR_MODULO[grande][:10]]
        assert citas == sorted(citas, reverse=True), (
            "%s no esta ordenado por citas: %s" % (grande, citas))


class TestElNegativoMedido:

    def test_los_generados_siguen_sin_inyectar_nombres(self):
        """MIDE ANTES DE CAMBIAR ESTO.

        Enchufar los sustantivos del modulo a los nodos generados se probo y
        pierde a volumen igualado. El motivo se ve sin estadistica: el modulo
        de un nodo generado es un RINCON de su area —`mathlib-analysis-real`
        ofrecia `Hyperreal.Infinite` y `Real.ofDigits`— mientras que `Real` y
        `Real.sqrt` viven en `Data/Real/Basic`.

        Si este test falla es porque alguien volvio a cablearlo. Bien, pero
        entonces hay que re-medir con `scripts/politica_emparejador.py
        --curva`, que compara A VOLUMEN IGUALADO: sin eso, mas cobertura con
        menos precision parece una mejora y no lo es.
        """
        from nucleo.graph.interpretacion import nombres_de_trabajo
        assert nombres_de_trabajo("mathlib-analysis-real") == ""
        assert nombres_de_trabajo("mathlib-topology-compactness") == ""

    def test_los_curados_si_inyectan(self):
        """Lo que si esta comprobado a mano sigue en pie."""
        from nucleo.graph.interpretacion import nombres_de_trabajo
        assert "Subgroup" in nombres_de_trabajo("group-theory")
