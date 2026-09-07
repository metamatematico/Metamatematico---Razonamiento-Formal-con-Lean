# -*- coding: utf-8 -*-
"""La confirmación formal del colímite con el KERNEL de Lean.

`nucleo/graph/lean_proof_generator.py` estuvo escrito y sin que nadie lo
llamara. La docstring de `ColimitBuilder` mandaba usarlo «para verificación
formal» y ningún módulo lo importaba: los dos únicos «imports» que se le veían
estaban dentro de docstrings.

Y al probarlo devolvía `False` para TODO, porque no compilaba. Un verificador
que dice que no a todo no distingue un colímite de algo que no lo es —
exactamente igual de inútil que uno que dice que sí a todo.

Tenía cuatro fallos, y el cuarto no era de sintaxis:

  1. `[0,1].map (fun i => ⟨i, by omega⟩)`: ahí `i` es una variable ligada y
     `omega` no puede acotarla. Ahora se emiten literales de `Fin n`, que Lean
     resuelve por `OfNat` sin táctica ninguna.
  2. `Fin.univ.toList` no existe sin Mathlib, y este fichero se compila con
     `lean` a secas a propósito: con Mathlib tardaría minutos.
  3. `native_decide` metía al compilador de Lean en la base de confianza. Con
     `decide` lo cierra el kernel, que es lo que da derecho a decir que Lean
     lo verificó.
  4. EL ÁPICE ES CO-CONO DE SÍ MISMO, así que la propiedad universal le exige
     un mediador hacia sí mismo, y ese mediador es la IDENTIDAD. Como la lista
     de morfismos no lleva identidades, un colímite CORRECTO salía refutado.

Estos tests fijan que DISCRIMINA, que es lo único que hace útil a un
verificador, y que un fallo suyo no se disfraza de resultado sobre el grafo.
"""
from __future__ import annotations

import pytest

from nucleo.graph.category import SkillCategory
from nucleo.mes.patterns import ColimitBuilder, PatternManager
from nucleo.types import MorphismType, PillarType, Skill


def _hay_lean() -> bool:
    from nucleo.graph.lean_proof_generator import _lean_cmd
    return _lean_cmd() is not None


SIN_LEAN = pytest.mark.skipif(not _hay_lean(),
                              reason="no hay lean en el PATH")


@pytest.fixture
def cuadrado():
    """s1, s2 y un B al que llegan los dos.

    Al construir el colímite de {s1, s2}, el ápice tiene que mediar hacia B.
    Es el caso mínimo con un co-cono no trivial.
    """
    g = SkillCategory(name="Cuadrado")
    for i in ("s1", "s2", "B"):
        g.add_skill(Skill(id=i, name=i, pillar=PillarType.SET, level=0))
    g.add_morphism("s1", "B", MorphismType.DEPENDENCY)
    g.add_morphism("s2", "B", MorphismType.DEPENDENCY)
    return g


class TestElEnunciadoQueSeLeDaALean:
    """Sobre el código generado, sin necesidad de tener Lean instalado."""

    def test_lo_cierra_el_kernel_y_no_el_compilador(self):
        from nucleo.graph.lean_proof_generator import generate_colimit_proof
        c = generate_colimit_proof(["a", "b"], "i", ["a", "b", "i", "x"],
                                   [("a", "i"), ("b", "i"), ("i", "x")])
        # se mira LA TACTICA, no una subcadena en cualquier sitio: el fichero
        # generado explica en un comentario por que no usa la otra
        lineas = [l.strip() for l in c.splitlines()
                  if l.strip() and not l.strip().startswith("--")]
        i = next(k for k, l in enumerate(lineas)
                 if l.startswith("theorem apex_is_finite_colimit"))
        tactica = lineas[i + 1] if lineas[i].endswith("by") else lineas[i]
        assert tactica == "decide", (
            "el teorema se cierra con %r. Si es native_decide, eso mete al "
            "compilador de Lean en la base de confianza, y para un enunciado "
            "de este tamaño no hace ninguna falta" % tactica)
        imports = [l for l in lineas if l.startswith("import ")]
        assert not imports, (
            "el fichero generado importa %s. Se compila con lean a secas a "
            "proposito: con Mathlib tardaria minutos en vez de segundos"
            % imports)

    def test_el_apice_se_media_a_si_mismo_por_la_identidad(self):
        """El fallo matemático que hacía fallar a los colímites correctos."""
        from nucleo.graph.lean_proof_generator import generate_colimit_proof
        c = generate_colimit_proof(["a", "b"], "i", ["a", "b", "i"],
                                   [("a", "i"), ("b", "i")])
        assert "x == apexNode" in c, (
            "se ha quitado la identidad como mediador del apice sobre si "
            "mismo. Sin ella hasMediator apexNode es falso siempre y NINGUN "
            "colimite se puede confirmar")

    def test_solo_viajan_los_morfismos_que_el_enunciado_consulta(self):
        """No es una poda heurística: es el conjunto exacto que se mira.

        `isCocone` pregunta por aristas que salen del diagrama y
        `hasMediator` por las que salen del ápice. Ninguna otra aparece en
        ninguna de las dos. Con las 1029 del grafo real el kernel agotaba
        `maxHeartbeats` a los 25 s en los casos VERDADEROS; con la rebanada
        relevante, segundos.
        """
        from nucleo.graph.lean_proof_generator import generate_colimit_proof
        c = generate_colimit_proof(
            ["a"], "i", ["a", "i", "x", "y"],
            [("a", "i"), ("i", "x"), ("x", "y"), ("y", "x")])
        assert "(2, 3)" not in c and "(3, 2)" not in c, (
            "viajan a Lean morfismos que el enunciado no consulta (x->y, "
            "y->x): encarecen la reduccion del kernel sin poder cambiar el "
            "resultado")
        assert "allNodes : List (Fin 4)" in c, (
            "el universo del cuantificador tiene que seguir siendo los 4 "
            "nodos: lo que se recorta es la tabla, nunca el para-todo")

    def test_el_limite_de_recursion_va_puesto(self):
        """Sin él, el grafo real agota la profundidad por defecto (512) y el
        fallo llega como si fuera una refutación."""
        from nucleo.graph.lean_proof_generator import generate_colimit_proof
        c = generate_colimit_proof(["a"], "i", ["a", "i"], [("a", "i")])
        assert "maxRecDepth" in c


class TestNoConfundirUnFalloConUnaRefutacion:

    def test_quedarse_sin_recursion_no_es_que_el_grafo_falle(self, monkeypatch):
        """La distinción que impide que un instrumento roto pase por resultado.

        A escala real el kernel agotaba la profundidad de recursión, y eso
        salía como `verified=False`, o sea «el grafo no cumple la propiedad
        universal». Son afirmaciones opuestas: una habla del grafo y la otra
        habla del verificador.
        """
        from nucleo.graph import lean_proof_generator as lpg
        monkeypatch.setattr(lpg, "_lean_cmd", lambda: "lean")
        monkeypatch.setattr(lpg, "_run_lean", lambda code, timeout=30: (
            False, "error: maximum recursion depth has been reached"))
        r = lpg.verify_colimit_in_lean(["a"], "i", ["a", "i"], [("a", "i")])
        assert r["verified"] is None, (
            "un fallo de recursos se esta reportando como refutacion")
        assert r["refutado"] is False

    def test_una_refutacion_de_verdad_no_se_pierde(self, monkeypatch):
        from nucleo.graph import lean_proof_generator as lpg
        monkeypatch.setattr(lpg, "_lean_cmd", lambda: "lean")
        monkeypatch.setattr(lpg, "_run_lean", lambda code, timeout=30: (
            False, "error: Tactic decide proved that the proposition\n"
                   "  universalPropertyHolds = true\nis false"))
        r = lpg.verify_colimit_in_lean(["a"], "i", ["a", "i"], [("a", "i")])
        assert r["verified"] is False
        assert r["refutado"] is True

    def test_sin_lean_el_veredicto_es_desconocido_no_falso(self, monkeypatch):
        from nucleo.graph import lean_proof_generator as lpg
        monkeypatch.setattr(lpg, "_lean_cmd", lambda: None)
        r = lpg.verify_colimit_in_lean(["a"], "i", ["a", "i"], [("a", "i")])
        assert r["verified"] is None


class TestElCableado:
    """Que el veredicto llegue hasta el objeto `Colimit`."""

    def test_sin_pedirlo_no_se_gasta_un_compilado(self, cuadrado):
        """El valor por defecto no puede meter Lean en un camino que hoy no
        lo tiene: cuesta entre uno y quince segundos por colímite."""
        cb = ColimitBuilder(PatternManager())
        pm = cb._pattern_manager
        pat = pm.create_pattern(["s1", "s2"], [], graph=cuadrado)
        _skill, col = cb.build_colimit(pat, cuadrado)
        assert col.lean_verified is None
        assert col.lean_claim == ""

    @SIN_LEAN
    def test_el_kernel_confirma_un_colimite_de_verdad(self, cuadrado):
        cb = ColimitBuilder(PatternManager())
        pm = cb._pattern_manager
        pat = pm.create_pattern(["s1", "s2"], [], graph=cuadrado)
        _skill, col = cb.build_colimit(pat, cuadrado, con_lean=True)
        assert col.universal_property_verified is True
        assert col.lean_verified is True, (
            "Python acepta la propiedad universal y el kernel de Lean no la "
            "confirma: hay que mirar la salida de Lean antes que el test")
        assert col.lean_claim, "el claim tiene que quedar guardado para citarlo"

    @SIN_LEAN
    def test_el_kernel_sabe_decir_que_NO(self):
        """Sin esto, el test de arriba no valdría nada.

        a, b llegan a i y también a x, pero i NO llega a x: x es un co-cono
        sin mediador, así que i no es colímite. Añadiendo sólo esa arista,
        pasa a serlo. Un verificador que no separe estos dos casos no está
        verificando nada.
        """
        from nucleo.graph.lean_proof_generator import verify_colimit_in_lean
        skills = ["a", "b", "i", "x"]
        mor = [("a", "i"), ("b", "i"), ("a", "x"), ("b", "x")]
        r = verify_colimit_in_lean(["a", "b"], "i", skills, mor, timeout=180)
        assert r["verified"] is False and r["refutado"] is True, (
            "el verificador no sabe decir que no: %s"
            % (r["output"] or "")[:200])
        r2 = verify_colimit_in_lean(["a", "b"], "i", skills,
                                    mor + [("i", "x")], timeout=180)
        assert r2["verified"] is True, (
            "y con el mediador puesto tampoco sabe decir que si")
