# -*- coding: utf-8 -*-
"""φ (paso 5) y las partes de D1 denso que no necesitan el modelo."""
import asyncio

from nucleo.lazo import phi
from nucleo.lazo.densa import D1Denso, escribible, plantillas

IX = {"Subgroup": {"group-theory"}, "orderOf": {"group-theory", "order"},
      "Real": {"real-analysis"}, "Finset.sum": {"combinatorics"}}


class TestPhi:
    def test_el_texto_casa_nombres_exactos_y_no_prefijos(self):
        assert phi.phi_texto("H : Subgroup G ⊢ orderOf x ∣ 5", IX) == {"group-theory", "order"}
        # `Subgroup.mk` no es `Subgroup`: la regla de L4, sin expandir espacios
        assert phi.phi_texto("⊢ Subgroup.mk = x", IX) == set()

    def test_la_notacion_esconde_lo_que_las_constantes_ven(self):
        """∑ y ℝ no son identificadores: el texto no los ve."""
        assert phi.phi_texto("⊢ ∑ i ∈ s, (i : ℝ) = 0", IX) == set()
        assert phi.conceptos(["Finset.sum", "Real"], IX) == {"combinatorics", "real-analysis"}

    def test_lee_el_mensaje_de_la_tactica(self):
        m = [{"severity": "info", "data": "METAMAT_CONSTANTES [Real, HAdd.hAdd, LE.le]"}]
        assert phi.leer_constantes(m) == ["Real", "HAdd.hAdd", "LE.le"]
        assert phi.leer_constantes([{"data": "otra cosa"}]) == []
        assert phi.leer_constantes(None) == []

    def test_los_portadores_se_quitan(self):
        assert phi.sin_portadores(["Real", "Nat", "orderOf", "Complex"]) == ["orderOf"]

    def test_explicar_dice_lo_que_aparece_y_lo_que_se_va(self):
        ls = phi.explicar(["intro h", "simp"], [{"a"}, {"b"}, set()])
        assert ls[0] == "Paso 1 · `intro h` — el objetivo habla de a; aparece b; deja de estar a"
        assert ls[1] == "Paso 2 · `simp` — el objetivo habla de b; y queda demostrado"

    def test_explicar_sin_cambio_y_sin_etiquetas(self):
        ls = phi.explicar(["ring_nf", "rfl"], [{"a"}, {"a"}])
        assert "sin cambiar de conceptos" in ls[0]
        assert phi.explicar(["rfl"], []) == ["Paso 1 · `rfl` — y queda demostrado"]

    def test_explicar_usa_el_nombre_legible(self):
        ls = phi.explicar(["simp"], [{"group-theory"}], nombre_de=lambda c: c.upper())
        assert "GROUP-THEORY" in ls[0]


class TestDensa:
    def test_escribible(self):
        assert escribible("Nat.add_comm") and escribible("mul_pos'")
        assert not escribible("Foo.«bar baz»")
        assert not escribible("Nat.foo.match_1") and not escribible("_private.X.y")

    def test_plantillas_por_premisa_y_simp_al_final(self):
        t = plantillas(["a", "b"])
        assert t == ["exact a", "apply a", "rw [a]", "exact b", "apply b", "rw [b]",
                     "simp [a, b]"]
        assert plantillas([]) == []

    def test_sin_ficheros_no_propone(self):
        class _Nada:
            def disponible(self):
                return False

        class _Nodo:
            objetivos = ["⊢ True"]
        assert asyncio.run(D1Denso(_Nada()).proponer(_Nodo())) == []

    def test_propone_lo_que_el_indice_encuentra(self):
        class _Uno:
            def disponible(self):
                return True

            def buscar(self, estado, k):
                return [("le_refl", 0.9)]

        class _Nodo:
            objetivos = ["x : ℝ\n⊢ x ≤ x"]
        assert asyncio.run(D1Denso(_Uno()).proponer(_Nodo()))[0] == "exact le_refl"
