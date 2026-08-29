"""
Tests de la complexificacion de Ehresmann (paso K -> K').

QUE SE COMPRUEBA
----------------
Las cuatro propiedades que `Complexificacion.lean` demuestra, sobre el codigo
que las realiza:

  · eta_es_colimite            -> el hueco queda cerrado: eta(P) ES el colimite
  · eta_eq_iota_of_isLUB       -> lo que ya tenia colimite no recibe objeto nuevo
  · SC_homologos_mismo_colimite-> dos huecos con las mismas cotas comparten objeto
  · (preservacion, §9.4)       -> los colimites previos siguen siendolo, o se revierte

Y la terminacion, que es lo que hizo que se retirara la fabricacion de nodos en
su momento: complexificar es UN paso explicito, no un bucle.
"""
import pytest

from nucleo.types import Skill, MorphismType, PillarType
from nucleo.graph.category import SkillCategory
from nucleo.mes.patterns import PatternManager, ColimitBuilder
from nucleo.graph.complexity import (
    build_hierarchy_to_fixpoint, build_join_for_pattern,
    find_colimit, ConceptGap,
)
from nucleo.graph.complexificacion import complexificar, ObjetoEmergente


def _grafo(*ids: str) -> SkillCategory:
    g = SkillCategory(name="ComplTest")
    for sid in ids:
        g.add_skill(Skill(id=sid, name=sid, pillar=PillarType.SET, level=0))
    return g


def _dep(g, a, b):
    g.add_morphism(a, b, MorphismType.DEPENDENCY)


def _hueco(g, comps):
    """Construye el ConceptGap del patron, comprobando que de verdad lo es."""
    pm = PatternManager()
    cb = ColimitBuilder(pm)
    r = build_join_for_pattern(pm.create_pattern(list(comps), [], graph=g), g, cb)
    assert isinstance(r, ConceptGap), f"no es hueco: {r!r}"
    return pm, cb, r


# ---------------------------------------------------------------------------
# El hueco se cierra
# ---------------------------------------------------------------------------

class TestCierreDeHuecos:

    def test_hueco_con_dos_cotas_incomparables_se_cierra(self):
        """A,B ≤ X y A,B ≤ Y con X,Y incomparables: no hay minima en K.

        En K' se inserta eta(P) por debajo de ambas y por encima de A y B, y
        pasa a ser el colimite. Es `eta_es_colimite`.
        """
        g = _grafo("A", "B", "X", "Y")
        for s in ("A", "B"):
            _dep(g, s, "X"); _dep(g, s, "Y")
        pm, cb, gap = _hueco(g, ["A", "B"])
        assert find_colimit(["A", "B"], g, cb) is None      # en K no hay

        r = complexificar(g, pm, cb, [gap])

        assert len(r.nuevos) == 1
        assert r.huecos_cerrados == 1
        nuevo = r.nuevos[0].skill_id
        assert find_colimit(["A", "B"], g, cb) == nuevo     # en K' si

    def test_el_objeto_nuevo_esta_entre_las_componentes_y_las_cotas(self):
        """Las aristas son las que hacen de eta(P) la MINIMA cota superior."""
        g = _grafo("A", "B", "X", "Y")
        for s in ("A", "B"):
            _dep(g, s, "X"); _dep(g, s, "Y")
        pm, cb, gap = _hueco(g, ["A", "B"])

        nuevo = complexificar(g, pm, cb, [gap]).nuevos[0].skill_id
        ORD = SkillCategory.ORDER_MORPHISMS

        for c in ("A", "B"):
            assert g.is_preorder_leq(c, nuevo, ORD), "cota superior"
        for x in ("X", "Y"):
            assert g.is_preorder_leq(nuevo, x, ORD), "minimal entre las cotas"
        assert not g.is_preorder_leq("X", nuevo, ORD), "no puede estar por encima"

    def test_hueco_sin_cotas_no_se_cierra_en_un_paso(self):
        """Sin ninguna cota superior, eta(P) seria el maximo del grafo entero.

        Se deja abierto y se dice, en vez de colgar un nodo de todo.
        """
        g = _grafo("A", "B")
        pm, cb, gap = _hueco(g, ["A", "B"])
        assert gap.cocones == []

        r = complexificar(g, pm, cb, [gap])

        assert r.nuevos == []
        assert len(g.skills) == 2


# ---------------------------------------------------------------------------
# Preservacion
# ---------------------------------------------------------------------------

class TestPreservacion:

    def test_lo_que_ya_tenia_colimite_no_recibe_objeto_nuevo(self):
        """`eta_eq_iota_of_isLUB`: si P ya tenia join, no aparece nada."""
        g = _grafo("A", "B", "C")
        _dep(g, "A", "C"); _dep(g, "B", "C")
        pm = PatternManager(); cb = ColimitBuilder(pm)
        cn, gaps = build_hierarchy_to_fixpoint(g, pm, cb)
        assert find_colimit(["A", "B"], g, cb) == "C"

        antes = len(g.skills)
        r = complexificar(g, pm, cb, gaps)

        assert r.nuevos == []
        assert len(g.skills) == antes

    def test_los_colimites_previos_se_reverifican(self):
        """La insercion puede quitarle minimalidad a otro colimite (§9.4)."""
        g = _grafo("A", "B", "X", "Y", "P", "Q", "R")
        for s in ("A", "B"):
            _dep(g, s, "X"); _dep(g, s, "Y")
        _dep(g, "P", "R"); _dep(g, "Q", "R")
        pm = PatternManager(); cb = ColimitBuilder(pm)
        cn, gaps = build_hierarchy_to_fixpoint(g, pm, cb)

        r = complexificar(g, pm, cb, gaps)

        # R sigue siendo el join de {P,Q}: la insercion no lo toca
        assert "R" in r.colimites_preservados
        assert r.colimites_rotos == []
        assert r.preserva

    def test_preservar_revierte_el_paso_entero(self):
        """Con preservar=True un colimite roto deja el grafo intacto."""
        g = _grafo("A", "B", "X", "Y")
        for s in ("A", "B"):
            _dep(g, s, "X"); _dep(g, s, "Y")
        pm, cb, gap = _hueco(g, ["A", "B"])

        # Se falsea un colimite previo que la insercion va a romper: se declara
        # que X es el join de {A,B}, cosa que dejara de ser cierta en cuanto
        # eta(P) se meta por debajo.
        pat = pm.create_pattern(["A", "B"], [], graph=g)
        cb._register_existing_join(pat, "X", g)

        antes_skills = len(g.skills)
        antes_morf = len(g.morphisms)
        r = complexificar(g, pm, cb, [gap], preservar=True)

        assert r.revertida
        assert r.nuevos == []
        assert len(g.skills) == antes_skills
        assert len(g.morphisms) == antes_morf

    def test_sin_preservar_se_aplica_y_se_reporta(self):
        g = _grafo("A", "B", "X", "Y")
        for s in ("A", "B"):
            _dep(g, s, "X"); _dep(g, s, "Y")
        pm, cb, gap = _hueco(g, ["A", "B"])
        pat = pm.create_pattern(["A", "B"], [], graph=g)
        cb._register_existing_join(pat, "X", g)

        r = complexificar(g, pm, cb, [gap], preservar=False)

        assert not r.revertida
        assert len(r.nuevos) == 1
        assert "X" in r.colimites_rotos


# ---------------------------------------------------------------------------
# Condicion suplementaria (SC)
# ---------------------------------------------------------------------------

class TestCondicionSuplementaria:

    def test_dos_huecos_con_las_mismas_cotas_comparten_objeto(self):
        """`SC_homologos_mismo_colimite`, en el codigo.

        El id del objeto se deriva del CONJUNTO DE COTAS, no de las
        componentes. Si dependiera de las componentes, dos patrones homologos
        recibirian objetos distintos — la deficiencia (b) de §3.2.
        """
        g = _grafo("A", "B", "C", "D", "X", "Y")
        for s in ("A", "B", "C", "D"):
            _dep(g, s, "X"); _dep(g, s, "Y")
        pm = PatternManager(); cb = ColimitBuilder(pm)
        g1 = build_join_for_pattern(pm.create_pattern(["A", "B"], [], graph=g), g, cb)
        g2 = build_join_for_pattern(pm.create_pattern(["C", "D"], [], graph=g), g, cb)
        assert isinstance(g1, ConceptGap) and isinstance(g2, ConceptGap)
        assert set(g1.cocones) == set(g2.cocones)

        r = complexificar(g, pm, cb, [g1, g2])

        assert len(r.nuevos) == 1, "homologos deben compartir el colimite"
        assert set(r.nuevos[0].component_ids) == {"A", "B", "C", "D"}

    def test_huecos_con_cotas_distintas_reciben_objetos_distintos(self):
        g = _grafo("A", "B", "C", "D", "X", "Y", "Z", "W")
        for s in ("A", "B"):
            _dep(g, s, "X"); _dep(g, s, "Y")
        for s in ("C", "D"):
            _dep(g, s, "Z"); _dep(g, s, "W")
        pm = PatternManager(); cb = ColimitBuilder(pm)
        g1 = build_join_for_pattern(pm.create_pattern(["A", "B"], [], graph=g), g, cb)
        g2 = build_join_for_pattern(pm.create_pattern(["C", "D"], [], graph=g), g, cb)

        r = complexificar(g, pm, cb, [g1, g2])

        assert len(r.nuevos) == 2
        assert r.nuevos[0].skill_id != r.nuevos[1].skill_id


# ---------------------------------------------------------------------------
# Terminacion
# ---------------------------------------------------------------------------

class TestTerminacion:

    def test_complexificar_es_un_paso_no_un_bucle(self):
        """La razon por la que se retiro la fabricacion de nodos era que cada
        nodo nuevo era un punto de convergencia nuevo y el bucle crecia. Aqui
        no hay bucle: se añade un objeto por clase de huecos y se para.
        """
        g = _grafo("A", "B", "X", "Y")
        for s in ("A", "B"):
            _dep(g, s, "X"); _dep(g, s, "Y")
        pm, cb, gap = _hueco(g, ["A", "B"])

        r = complexificar(g, pm, cb, [gap])
        assert len(g.skills) == 5

        # repetirlo con los MISMOS huecos no vuelve a crecer: el objeto ya existe
        r2 = complexificar(g, pm, cb, [gap])
        assert len(g.skills) == 5

    def test_el_objeto_nuevo_no_entra_en_cn_como_componente_de_si_mismo(self):
        """La aciclicidad se mantiene tras complexificar."""
        g = _grafo("A", "B", "X", "Y")
        for s in ("A", "B"):
            _dep(g, s, "X"); _dep(g, s, "Y")
        pm, cb, gap = _hueco(g, ["A", "B"])
        complexificar(g, pm, cb, [gap])

        pm2 = PatternManager(); cb2 = ColimitBuilder(pm2)
        build_hierarchy_to_fixpoint(g, pm2, cb2)

        for col in cb2.all_colimits:
            pat = pm2.get_pattern(col.pattern_id)
            if pat:
                assert col.skill_id not in pat.component_ids


# ---------------------------------------------------------------------------
# El segundo paso: la complexificacion enchufada, y lo que NO consigue
# ---------------------------------------------------------------------------

class TestComplexificacionEnchufada:
    """El paso deja de ser inerte, y se mide honestamente que produce."""

    @pytest.fixture(scope="class")
    def corrida(self):
        import sys as _s
        _s.argv = ["x"]
        from nucleo.graph.category import SkillCategory
        from nucleo.pillars.math_domains import load_math_domains
        from nucleo.mes.patterns import PatternManager, ColimitBuilder
        from nucleo.graph.complexity import build_hierarchy_to_fixpoint
        from nucleo.graph.complexificacion import complexificar
        from nucleo.graph.no_delgado import (registrar_morfismos_certificados,
                                             congruencia_automatica)
        from nucleo.core import Nucleo
        n = Nucleo.__new__(Nucleo)
        g = SkillCategory(name="CxE")
        n._graph = g
        Nucleo._load_foundational_skills(n)
        load_math_domains(g)
        registrar_morfismos_certificados(g)
        pm = PatternManager()
        cb = ColimitBuilder(pm)
        cong = congruencia_automatica(g)
        cn0, gaps0 = build_hierarchy_to_fixpoint(g, pm, cb, cong=cong)
        antes = (len(g.skill_ids), len(cb.all_colimits), len(gaps0))
        res = complexificar(g, pm, cb, gaps0, preservar=True, cong=cong)
        cn1, gaps1 = build_hierarchy_to_fixpoint(g, pm, cb, cong=cong)
        return g, pm, cb, cong, antes, res, cn1, gaps1

    def test_el_paso_ya_no_es_inerte(self, corrida):
        """Con rollback todo-o-nada, 8 objetos cerraban 8 huecos y los 8 se
        tiraban por culpa de 1. La retirada selectiva quita solo al culpable.
        """
        *_, res, _cn, _gaps = corrida
        assert not res.revertida
        assert len(res.nuevos) == 2
        assert res.huecos_cerrados == 2
        # Ya no hay culpables que retirar: los objetos que robaban minimalidad
        # nacian de patrones mal formados, y esos patrones ya no se emiten.
        assert len(res.retirados) == 0

    def test_ningun_colimite_previo_se_rompe(self, corrida):
        """El objetivo (iii) de la opcion: preservar lo que ya existia."""
        *_, res, _cn, _gaps = corrida
        assert res.colimites_rotos == []
        assert res.preserva
        assert len(res.colimites_preservados) == 22

    def test_los_huecos_bajan(self, corrida):
        _g, _pm, _cb, _cong, antes, _res, _cn, gaps1 = corrida
        assert antes[2] == 3
        assert len(gaps1) == 1

    def test_declara_la_congruencia_constitutiva(self, corrida):
        """Un colimite viene CON su co-cono: que las patas de eta(P) conmuten
        con los enlaces del patron no es una conjetura sobre el dominio, es lo
        que significa el objeto insertado. Sin declararlo, eta(P) falla su
        propio test de co-cono.
        """
        *_, res, _cn, _gaps = corrida
        assert res.relaciones_nuevas
        for (a, b) in res.relaciones_nuevas:
            assert len(a) == 2 and len(b) == 1

    def test_los_objetos_nuevos_son_colimites_de_verdad(self, corrida):
        """No basta con que sean alcanzables: tienen que admitir co-cono."""
        from nucleo.graph.no_delgado import hay_cocono_cong
        g, pm, cb, cong, _a, res, _cn, _gaps = corrida
        for obj in res.nuevos:
            pats = [pm.get_pattern(p) for p in obj.patrones]
            pats = [p for p in pats if p is not None]
            assert any(
                hay_cocono_cong(p, obj.skill_id, g, cong) is True for p in pats
            ), f"{obj.skill_id} no admite co-cono sobre ninguno de sus patrones"

    # ── LO QUE NO CONSIGUE, dicho con la misma claridad ──────────────────

    def test_no_produce_ni_un_solo_objeto_emergente(self, corrida):
        """El resultado honesto, y hay que dejarlo escrito.

        `eta(P)` se inserta justo encima de las componentes de P, luego su
        orden irreducible es `1 + max(orden de las componentes)`. Con todas las
        componentes en orden 0 sale orden 1, siempre. La complexificacion
        cierra huecos; no crea emergencia.
        """
        from nucleo.graph.complexity import orden_irreducible
        g, _pm, cb, _c, _a, res, _cn, _gaps = corrida
        orden = orden_irreducible(g, cb)
        for obj in res.nuevos:
            assert orden.get(obj.skill_id) <= 1, (
                f"{obj.skill_id} salio de orden {orden.get(obj.skill_id)}: si "
                "la complexificacion empieza a producir emergencia, este test "
                "hay que reescribirlo, que seria una buena noticia"
            )

    def test_los_emergentes_siguen_siendo_los_dos_del_grafo_curado(self, corrida):
        """Antes y despues del paso: los mismos dos, y ninguno es emergente."""
        from nucleo.graph.complexity import objetos_emergentes
        g, _pm, cb, *_ = corrida
        em = objetos_emergentes(g, cb)
        assert set(em) == {"arithmetic-geometry", "affine-varieties",
                           "sheafed-space-complexes", "graded-objects"}
        for k in em:
            sk = g.get_skill(k)
            assert not sk.metadata.get("emergente"), (
                f"{k} lo produjo la complexificacion: si eso pasa, el paso SI "
                "genera emergencia y hay que reescribir este test"
            )

    def test_la_palanca_esta_identificada(self, corrida):
        """Donde estaria el orden >= 2, y por que no se alcanza hoy.

        Un hueco da orden >= 2 solo si alguna componente ya es colimite. De los
        12 que quedan, la mayoria cumple eso — pero no tienen NINGUNA cota
        superior, luego no se pueden cerrar insertando un minimo entre ellas:
        `eta(P)` seria el objeto maximo y colgaria de todo el grafo.

        Esos huecos necesitan un concepto NOMBRADO, que lo aporta la
        matematica. Es exactamente el limite que el modulo ya declaraba.
        """
        from nucleo.graph.complexity import find_cocones, orden_irreducible
        g, _pm, cb, _c, _a, _res, _cn, gaps = corrida
        orden = orden_irreducible(g, cb)
        darian_2, sin_cotas = 0, 0
        for gap in gaps:
            ords = [orden.get(c, 0) for c in gap.component_ids]
            if ords and 1 + max(ords) >= 2:
                darian_2 += 1
                if not find_cocones(list(gap.component_ids), g):
                    sin_cotas += 1
        # Antes eran 8 con 6 sin cotas. Al exigir que las componentes sean
        # objetos, casi todos aquellos huecos resultaron ser patrones mal
        # formados y desaparecieron: quedan muy pocos, y el unico sin cotas es
        # el que el veredicto ya declaro ESPURIO —`{algebraic-geometry,
        # functors, homological-algebra, operator-theory}`, donde dos patas de
        # cuatro no son canonicas—.
        #
        # Lo que el test sigue vigilando es la forma del limite: si un hueco
        # que daria orden >= 2 GANARA cotas superiores, el paso si produciria
        # emergencia y habria que reescribir esto.
        assert sin_cotas == darian_2, (
            "un hueco que daria orden >= 2 tiene ahora cotas superiores: la "
            "complexificacion podria cerrarlo y producir emergencia"
        )
