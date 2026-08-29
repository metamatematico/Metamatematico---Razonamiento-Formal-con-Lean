"""
Tests de la salida de la delgadez.

QUE SE COMPRUEBA
----------------
Los teoremas de `Complexificacion.lean §9-§10` y `MorfismosGrupoAnillo.lean`,
sobre el codigo que los realiza:

  · `Hom(a,b)` puede tener mas de un elemento — indexado por CONSTRUCCION;
  · `cota_superior_no_implica_cocono` — el caso donde el cociente delgado
    concede un co-cono que no lo es;
  · `delgado_cocono_automatico` — y por que con un solo enlace nunca discrepan;
  · los tres morfismos certificados de group-theory a ring-theory.
"""
import pytest

from nucleo.types import Skill, MorphismType, PillarType
from nucleo.graph.category import SkillCategory
from nucleo.mes.patterns import PatternManager, ColimitBuilder
from nucleo.graph.no_delgado import (
    multiplicidad, caminos, es_cocono_libre, hay_cocono_libre,
    comparar_cocono, registrar_morfismos_certificados,
    MORFISMOS_CERTIFICADOS,
    Congruencia, LIBRE, DELGADA, hay_cocono_cong, es_cocono_cong,
    espectro, congruencia_respeta_certificados,
    congruencia_automatica, pendientes_de_decidir, informe_pendientes,
    TIPO_REFUTADO, TIPO_GENERICO, TIPO_COMPUESTO,
    MorfismoCertificado, RETIRADOS, VARIANZA, INTERPRETACION,
    respeta_convencion, violaciones_de_convencion,
)


def _g(*ids: str) -> SkillCategory:
    g = SkillCategory(name="NoDelgado")
    for sid in ids:
        g.add_skill(Skill(id=sid, name=sid, pillar=PillarType.SET, level=0))
    return g


# ---------------------------------------------------------------------------
# Hom deja de ser un booleano
# ---------------------------------------------------------------------------

class TestHomComoConjunto:

    def test_dos_construcciones_son_dos_morfismos(self):
        g = _g("a", "b")
        m1 = g.add_morphism("a", "b", MorphismType.DEPENDENCY,
                            construccion="grupo-aditivo")
        m2 = g.add_morphism("a", "b", MorphismType.DEPENDENCY,
                            construccion="grupo-unidades")
        assert m1.id != m2.id
        assert multiplicidad(g).pares_multiples == 1
        assert not multiplicidad(g).es_delgado

    def test_la_misma_construccion_no_se_duplica(self):
        g = _g("a", "b")
        m1 = g.add_morphism("a", "b", MorphismType.DEPENDENCY, construccion="x")
        m2 = g.add_morphism("a", "b", MorphismType.DEPENDENCY, construccion="x")
        assert m1.id == m2.id
        assert multiplicidad(g).es_delgado

    def test_grafo_sin_multiplicidad_es_delgado(self):
        g = _g("a", "b", "c")
        g.add_morphism("a", "b", MorphismType.DEPENDENCY)
        g.add_morphism("b", "c", MorphismType.DEPENDENCY)
        assert multiplicidad(g).es_delgado


# ---------------------------------------------------------------------------
# El co-cono deja de ser "cota superior"
# ---------------------------------------------------------------------------

class TestCoconoNoDelgado:

    def _testigo(self):
        """
        Dos enlaces distinguidos PARALELOS `A ⇉ B`, y un apice `C` por encima
        de ambos.

            A ══(x, y)══> B
             \\           /
              \\         /
               v       v
                   C

        El cociente delgado dice «C es cota superior de {A,B}» y concede
        co-cono. La condicion de Ehresmann exige `x ; f_B = f_A` Y
        `y ; f_B = f_A`, luego `x ; f_B = y ; f_B`, que con `x ≠ y` es falso.

        Contraparte formal: `cota_superior_no_implica_cocono`.
        """
        g = _g("A", "B", "C")
        x = g.add_morphism("A", "B", MorphismType.DEPENDENCY, construccion="x")
        y = g.add_morphism("A", "B", MorphismType.DEPENDENCY, construccion="y")
        g.add_morphism("A", "C", MorphismType.DEPENDENCY)
        g.add_morphism("B", "C", MorphismType.DEPENDENCY)
        pm = PatternManager()
        p = pm.create_pattern(["A", "B"], [x.id, y.id], graph=g)
        return g, pm, p, x, y

    def test_los_enlaces_paralelos_no_colapsan(self):
        """La categoria de indices tambien tiene que dejar de ser delgada.

        `create_pattern` indexaba por `d_{i}_{j}`, asi que el segundo enlace
        paralelo sobreescribia al primero: el grafo podia ser no delgado y el
        indice seguia siendolo.
        """
        _, _, p, _, _ = self._testigo()
        assert len(p.index_morphisms) == 2

    def test_delgado_concede_lo_que_libre_niega(self):
        """El caso que separa las dos lecturas."""
        g, _, p, _, _ = self._testigo()
        r = comparar_cocono(p, "C", g)

        assert r["delgado"] is True, "C es cota superior de A y B"
        assert r["libre"] is False, "pero ninguna eleccion conmuta"
        assert r["discrepan"] is True

    def test_con_un_solo_enlace_nunca_discrepan(self):
        """Con un enlace la familia queda determinada por propagacion.

        Es la razon de que sobre el grafo real, hoy, no haya ninguna
        discrepancia: los patrones con enlaces distinguidos tienen uno solo.
        Contraparte formal: `delgado_cocono_automatico`.
        """
        g = _g("A", "B", "C")
        x = g.add_morphism("A", "B", MorphismType.DEPENDENCY, construccion="x")
        g.add_morphism("A", "C", MorphismType.DEPENDENCY)
        g.add_morphism("B", "C", MorphismType.DEPENDENCY)
        pm = PatternManager()
        p = pm.create_pattern(["A", "B"], [x.id], graph=g)

        r = comparar_cocono(p, "C", g)
        assert r["delgado"] is True
        assert r["libre"] is True
        assert r["discrepan"] is False

    def test_sin_enlaces_distinguidos_la_condicion_es_vacua(self):
        """Un diagrama DISCRETO no impone nada: es el estado anterior."""
        g = _g("A", "B", "C")
        g.add_morphism("A", "C", MorphismType.DEPENDENCY)
        g.add_morphism("B", "C", MorphismType.DEPENDENCY)
        pm = PatternManager()
        p = pm.create_pattern(["A", "B"], [], graph=g)

        assert p.index_morphisms == {}
        assert es_cocono_libre(p, {"A": (), "B": ()}, g) is True

    def test_sin_cota_no_hay_cocono(self):
        g = _g("A", "B", "C")
        pm = PatternManager()
        p = pm.create_pattern(["A", "B"], [], graph=g)
        assert hay_cocono_libre(p, "C", g) is False


# ---------------------------------------------------------------------------
# Caminos: Hom en la categoria libre
# ---------------------------------------------------------------------------

class TestCaminos:

    def test_dos_paralelos_dan_dos_caminos(self):
        g = _g("a", "b")
        g.add_morphism("a", "b", MorphismType.DEPENDENCY, construccion="x")
        g.add_morphism("a", "b", MorphismType.DEPENDENCY, construccion="y")
        assert len(caminos(g, "a", "b")) == 2

    def test_identidad_es_el_camino_vacio(self):
        g = _g("a")
        assert caminos(g, "a", "a") == [()]

    def test_se_respeta_la_cota_de_longitud(self):
        g = _g("a", "b", "c", "d")
        g.add_morphism("a", "b", MorphismType.DEPENDENCY)
        g.add_morphism("b", "c", MorphismType.DEPENDENCY)
        g.add_morphism("c", "d", MorphismType.DEPENDENCY)
        assert caminos(g, "a", "d", max_longitud=2) == []
        assert len(caminos(g, "a", "d", max_longitud=3)) == 1


# ---------------------------------------------------------------------------
# Los morfismos certificados en Lean
# ---------------------------------------------------------------------------

class TestMorfismosCertificados:

    def test_se_registran_los_tres(self):
        g = _g("group-theory", "ring-theory")
        registrar_morfismos_certificados(g)

        hs = [h for h in g.hom("group-theory", "ring-theory")
              if h.morphism_type != MorphismType.IDENTITY]
        constrs = {h.metadata.get("construccion") for h in hs}
        assert constrs == {"grupo-aditivo", "grupo-unidades", "grupo-trivial"}

    def test_cada_uno_cita_su_teorema(self):
        g = _g("group-theory", "ring-theory")
        registrar_morfismos_certificados(g)
        for h in g.hom("group-theory", "ring-theory"):
            if h.metadata.get("certificado"):
                assert "." in h.metadata["teorema_lean"]

    def test_el_par_deja_de_ser_delgado(self):
        g = _g("group-theory", "ring-theory")
        assert multiplicidad(g).es_delgado
        registrar_morfismos_certificados(g)
        assert not multiplicidad(g).es_delgado

    def test_es_idempotente(self):
        g = _g("group-theory", "ring-theory")
        registrar_morfismos_certificados(g)
        n1 = len(g.morphisms)
        registrar_morfismos_certificados(g)
        assert len(g.morphisms) == n1

    def test_no_falla_si_faltan_los_skills(self):
        g = _g("otra-cosa")
        assert registrar_morfismos_certificados(g) == []

    def test_el_mapeo_declara_teorema_para_cada_uno(self):
        for mc in MORFISMOS_CERTIFICADOS:
            assert mc.origen and mc.destino and mc.construccion
            # El namespace ya no es unico: hay dos archivos de certificados.
            # Que el teorema EXISTA lo comprueba
            # test_todos_citan_un_teorema_existente, que es la guardia buena.
            assert "." in mc.teorema
            assert mc.afirma


# ---------------------------------------------------------------------------
# El espectro: libre <= declarada <= delgada
# ---------------------------------------------------------------------------

class TestCongruencia:

    def _testigo(self):
        """Dos enlaces paralelos `A ⇉ B` y apice `C`. Igual que arriba."""
        g = _g("A", "B", "C")
        x = g.add_morphism("A", "B", MorphismType.DEPENDENCY, construccion="x")
        y = g.add_morphism("A", "B", MorphismType.DEPENDENCY, construccion="y")
        g.add_morphism("A", "C", MorphismType.DEPENDENCY)
        g.add_morphism("B", "C", MorphismType.DEPENDENCY)
        pm = PatternManager()
        return g, pm.create_pattern(["A", "B"], [x.id, y.id], graph=g), x, y

    def test_los_dos_extremos_difieren(self):
        """Si coincidieran, no habria nada que elegir. `el_espectro_no_es_trivial`."""
        g, p, _, _ = self._testigo()
        assert hay_cocono_cong(p, "C", g, LIBRE) is False
        assert hay_cocono_cong(p, "C", g, DELGADA) is True

    def test_declarar_una_relacion_mueve_el_resultado(self):
        """Y lo mueve en la direccion que dice el teorema de monotonia."""
        g, p, x, y = self._testigo()
        c = Congruencia()
        assert hay_cocono_cong(p, "C", g, c) is False
        c.declarar((x.id,), (y.id,))
        assert hay_cocono_cong(p, "C", g, c) is True

    def test_monotonia(self):
        """Mas identificaciones nunca quitan co-conos.

        `cocono_monotono_en_la_congruencia`.
        """
        g, p, x, y = self._testigo()
        e = espectro(p, "C", g, Congruencia().declarar((x.id,), (y.id,)))
        # libre <= declarada <= delgada, como implicaciones
        assert not (e["libre"] and not e["declarada"])
        assert not (e["declarada"] and not e["delgada"])

    def test_declarar_es_idempotente(self):
        g, p, x, y = self._testigo()
        c = Congruencia().declarar((x.id,), (y.id,)).declarar((x.id,), (y.id,))
        assert len(c.relaciones) == 1

    def test_la_relacion_es_simetrica(self):
        g, p, x, y = self._testigo()
        c = Congruencia().declarar((x.id,), (y.id,))
        assert c.iguales((x.id,), (y.id,))
        assert c.iguales((y.id,), (x.id,))

    def test_cierre_por_contexto(self):
        """Si `x = y`, entonces `x·f = y·f`: la congruencia respeta composicion."""
        g, p, x, y = self._testigo()
        f = g.hom("B", "C")[0]
        c = Congruencia().declarar((x.id,), (y.id,))
        assert c.iguales((x.id, f.id), (y.id, f.id))


# ---------------------------------------------------------------------------
# Lean tambien dice que relaciones NO se pueden declarar
# ---------------------------------------------------------------------------

class TestCertificadosVsCongruencia:

    def _g_certificado(self):
        g = _g("group-theory", "ring-theory")
        registrar_morfismos_certificados(g)
        return g

    def test_la_libre_no_viola_nada(self):
        assert congruencia_respeta_certificados(LIBRE, self._g_certificado()) == []

    def test_la_delgada_viola_los_certificados(self):
        """El diagnostico del sistema actual, hecho test.

        La congruencia total identifica los tres morfismos group-theory ->
        ring-theory, y `no_hay_iso` demuestra que son distintos. No es una
        simplificacion conveniente: es una identificacion FALSA.
        """
        v = congruencia_respeta_certificados(DELGADA, self._g_certificado())
        assert len(v) == 3
        assert all(o == "group-theory" and d == "ring-theory" for o, d, _ in v)
        assert all("MorfismosGrupoAnillo." in m for _, _, m in v)

    def test_declarar_una_relacion_falsa_se_detecta(self):
        g = self._g_certificado()
        hs = {h.metadata.get("construccion"): h
              for h in g.hom("group-theory", "ring-theory")
              if h.metadata.get("certificado")}
        c = Congruencia().declarar(
            (hs["grupo-aditivo"].id,), (hs["grupo-unidades"].id,)
        )
        v = congruencia_respeta_certificados(c, g)
        assert len(v) == 1
        assert "grupo-aditivo" in v[0][2] and "grupo-unidades" in v[0][2]

    def test_una_congruencia_inocua_no_se_marca(self):
        g = self._g_certificado()
        g.add_skill(Skill(id="otro", name="otro", level=0))
        m = g.add_morphism("ring-theory", "otro", MorphismType.DEPENDENCY)
        c = Congruencia().declarar((m.id,), (m.id,))
        assert congruencia_respeta_certificados(c, g) == []


# ---------------------------------------------------------------------------
# Los cinco pares certificados
# ---------------------------------------------------------------------------

class TestParesCertificados:
    """
    `agotar los pares certificados` significa: todos aquellos donde (1) la
    arista ya existe, (2) hay dos construcciones clasicas y (3) un invariante
    finito las separa. Los que fallan (3) quedan fuera y se dice por que.
    """

    PARES = {
        ("group-theory", "ring-theory"),
        ("ring-theory", "field-theory"),
    }

    def test_son_los_pares_declarados(self):
        assert {(m.origen, m.destino) for m in MORFISMOS_CERTIFICADOS} == self.PARES

    def test_cada_par_tiene_al_menos_dos_construcciones(self):
        """Dos bastan para romper la delgadez del par."""
        por_par = {}
        for m in MORFISMOS_CERTIFICADOS:
            por_par.setdefault((m.origen, m.destino), set()).add(m.construccion)
        for par, cs in por_par.items():
            assert len(cs) >= 2, f"{par} solo tiene {len(cs)}"

    def test_la_convencion_se_cumple(self):
        """Todo certificado va en el sentido que (A) exige: I(b) -> I(a).

        Los primeros seis pares se escribieron sin esta comprobacion y cuatro
        iban al reves — de ahi que `dominio` y `codominio` sean ahora campos
        explicitos y no algo que se supone.
        """
        assert VARIANZA == "contravariante"
        assert violaciones_de_convencion() == []

    def test_cada_certificado_declara_su_funtor(self):
        for m in MORFISMOS_CERTIFICADOS:
            assert m.dominio and m.codominio
            if m.destino in INTERPRETACION:
                assert m.dominio == INTERPRETACION[m.destino]
            if m.origen in INTERPRETACION:
                assert m.codominio == INTERPRETACION[m.origen]

    def test_los_retirados_dicen_por_que(self):
        """Un certificado retirado no se borra: se explica.

        Los cuatro siguen siendo teoremas verdaderos. Lo que ya no son es
        evidencia de multiplicidad de Hom para esa arista.
        """
        assert len(RETIRADOS) == 4
        vigentes = {(m.origen, m.destino) for m in MORFISMOS_CERTIFICADOS}
        for origen, destino, motivo in RETIRADOS:
            assert (origen, destino) not in vigentes
            assert len(motivo) > 40, "el motivo tiene que explicar algo"

    def test_hay_un_par_que_participa_en_colimites(self):
        """El que de verdad puede cambiar un resultado.

        Los cinco primeros son dependencias que ningun patron de convergencia
        usa: su multiplicidad no toca ningun colimite. Este si:
        `algebraic-geometry` es colimite de `{commutative-algebra, functors}`,
        luego esa arista es una PATA DEL CO-CONO — y ahora hay tres patas
        distintas donde antes habia una.

        Al fijar la convencion (A) este par se RETIRO: Spec es contravariante
        en el espacio, luego no es un funtor `I(algebraic-geometry) ->
        I(commutative-algebra)`. Con el se fue la unica multiplicidad que
        tocaba un colimite.
        """
        assert ("commutative-algebra", "algebraic-geometry") not in self.PARES
        assert any(o == "commutative-algebra" and d == "algebraic-geometry"
                   for o, d, _ in RETIRADOS)

    def test_las_construcciones_no_se_repiten_entre_pares(self):
        cs = [m.construccion for m in MORFISMOS_CERTIFICADOS]
        assert len(cs) == len(set(cs))

    def test_todos_citan_un_teorema_existente(self):
        """Guardia contra teoremas fantasma en el mapeo."""
        import pathlib, re
        raiz = pathlib.Path(__file__).resolve().parent.parent
        lean = " ".join(
            f.read_text(encoding="utf-8")
            for f in (raiz / "MetamathProver" / "CategoryFoundations").glob("*.lean")
        )
        for mc in MORFISMOS_CERTIFICADOS:
            nombre = mc.teorema.split(".")[-1]
            assert re.search(rf"(theorem|lemma|def)\s+{re.escape(nombre)}\b", lean), (
                f"'{mc.teorema}' no existe en el corpus Lean"
            )

    def test_registrar_no_mueve_el_preorden(self):
        """Añadir morfismos PARALELOS a aristas existentes no cambia el orden.

        Es la condicion que hace seguro certificar: la multiplicidad se añade
        sin tocar la alcanzabilidad, luego colimites, huecos y cn no se mueven.
        """
        from nucleo.graph.complexity import build_hierarchy_to_fixpoint

        def _medir(g):
            pm = PatternManager()
            cb = ColimitBuilder(pm)
            cn, gaps = build_hierarchy_to_fixpoint(g, pm, cb)
            return g.stats["num_joins"], len(gaps), sorted(cn.items())

        ids = [m.origen for m in MORFISMOS_CERTIFICADOS]
        ids += [m.destino for m in MORFISMOS_CERTIFICADOS]
        g = _g(*sorted(set(ids)))
        for o, d in sorted(self.PARES):
            g.add_morphism(o, d, MorphismType.DEPENDENCY)

        antes = _medir(g)
        registrar_morfismos_certificados(g)
        assert _medir(g) == antes

    def test_los_paralelos_llegan_al_indice_del_patron(self):
        """Y con ellos el patron deja de tener un indice delgado."""
        g = _g("group-theory", "ring-theory", "X")
        g.add_morphism("group-theory", "ring-theory", MorphismType.DEPENDENCY)
        g.add_morphism("group-theory", "X", MorphismType.DEPENDENCY)
        g.add_morphism("ring-theory", "X", MorphismType.DEPENDENCY)
        registrar_morfismos_certificados(g)

        enlaces = [m.id for m in g.hom("group-theory", "ring-theory")
                   if m.morphism_type != MorphismType.IDENTITY]
        pm = PatternManager()
        p = pm.create_pattern(["group-theory", "ring-theory"], enlaces, graph=g)
        assert len(p.index_morphisms) == len(enlaces) >= 4

    def test_la_delgada_viola_todos_los_certificados(self):
        """Cuantos mas pares se certifican, mas falsa es la congruencia actual."""
        ids = [m.origen for m in MORFISMOS_CERTIFICADOS]
        ids += [m.destino for m in MORFISMOS_CERTIFICADOS]
        g = _g(*sorted(set(ids)))
        registrar_morfismos_certificados(g)
        v = congruencia_respeta_certificados(DELGADA, g)
        # dos pares con 3 construcciones cada uno -> C(3,2) = 3 por par
        assert len(v) == 6
        assert congruencia_respeta_certificados(LIBRE, g) == []


# ---------------------------------------------------------------------------
# La congruencia automatica y lo que deja pendiente
# ---------------------------------------------------------------------------

class TestCongruenciaAutomatica:
    """
    Separa lo que se DERIVA de lo que hay que DECIDIR.

    Derivable: dos aristas paralelas que solo difieren en el TIPO y no tienen
    construccion. No es una decision matematica — es la semantica que el propio
    sistema declara en `is_preorder_leq`: «los distintos tipos de morfismo son
    etiquetas en el unico morfismo, no morfismos categoricamente distintos».

    No derivable, y por eso se reporta:
      · si dos RUTAS compuestas dan el mismo morfismo (teorema del dominio);
      · que representaba la arista generica antes de las construcciones.
    """

    def _g(self):
        g = _g_base = SkillCategory(name="Auto")
        for sid in ("A", "B", "C"):
            g.add_skill(Skill(id=sid, name=sid, pillar=PillarType.SET, level=0))
        return g

    def test_identifica_aristas_que_solo_difieren_en_el_tipo(self):
        g = self._g()
        g.add_morphism("A", "B", MorphismType.DEPENDENCY)
        g.add_morphism("A", "B", MorphismType.TRANSLATION)
        cong = congruencia_automatica(g)

        assert len(cong.relaciones) == 1
        ms = [m.id for m in g.hom("A", "B")
              if m.morphism_type != MorphismType.IDENTITY]
        assert cong.iguales((ms[0],), (ms[1],))

    def test_NO_identifica_construcciones_certificadas(self):
        """Lean demostro que son distintas: declararlas iguales seria falso."""
        g = _g("group-theory", "ring-theory")
        registrar_morfismos_certificados(g)
        cong = congruencia_automatica(g)

        assert congruencia_respeta_certificados(cong, g) == []
        cs = [m.id for m in g.hom("group-theory", "ring-theory")
              if m.metadata.get("construccion")]
        assert not cong.iguales((cs[0],), (cs[1],))

    def test_NO_identifica_rutas_compuestas(self):
        """Que dos rutas conmuten es un teorema, no una convencion."""
        g = self._g()
        directa = g.add_morphism("A", "C", MorphismType.DEPENDENCY)
        g.add_morphism("A", "B", MorphismType.DEPENDENCY)
        via = g.add_morphism("B", "C", MorphismType.DEPENDENCY)
        cong = congruencia_automatica(g)

        ab = [m.id for m in g.hom("A", "B")
              if m.morphism_type != MorphismType.IDENTITY][0]
        assert not cong.iguales((directa.id,), (ab, via.id))

    def test_la_pregunta_refutada_por_lean_no_es_una_pregunta(self):
        """Dos construcciones certificadas sobre la misma arista ya estan
        decididas: son distintas. No cuentan como decision abierta."""
        g = _g("group-theory", "ring-theory")
        registrar_morfismos_certificados(g)
        pm = PatternManager()
        cb = ColimitBuilder(pm)
        p = pm.create_pattern(["group-theory"], [], graph=g)
        cb._register_existing_join(p, "ring-theory", g)

        pend = pendientes_de_decidir(g, pm, cb)
        refutadas = [x for x in pend if x.tipo == TIPO_REFUTADO]
        assert refutadas, "las certificadas deben salir como refutadas"
        assert all(not x.es_pregunta for x in refutadas)

    def test_el_informe_distingue_lo_refutado_de_lo_abierto(self):
        g = _g("group-theory", "ring-theory")
        registrar_morfismos_certificados(g)
        pm = PatternManager()
        cb = ColimitBuilder(pm)
        p = pm.create_pattern(["group-theory"], [], graph=g)
        cb._register_existing_join(p, "ring-theory", g)

        txt = informe_pendientes(g, pendientes_de_decidir(g, pm, cb))
        assert "refutadas por Lean" in txt


# ---------------------------------------------------------------------------
# La migracion: de cota superior a co-cono
# ---------------------------------------------------------------------------

class TestMigracionACocono:
    """`find_colimit` preguntaba por vertices; `find_colimit_cong` por flechas.

    La diferencia solo existe fuera de la delgadez. Con `Hom(a,b)` booleano,
    elegida una flecha por componente la conmutacion se cumple sola
    (`cocono_delgado_siempre`), asi que cota superior y co-cono coinciden. En
    cuanto hay dos flechas paralelas distintas dejan de coincidir, y el testigo
    es `Mon = {1,e}` (`cota_superior_no_implica_cocono`).
    """

    @pytest.fixture(scope="class")
    def sistema(self):
        import sys as _s
        _s.argv = ["x"]
        from nucleo.graph.category import SkillCategory
        from nucleo.pillars.math_domains import load_math_domains
        from nucleo.mes.patterns import PatternManager, ColimitBuilder
        from nucleo.graph.complexity import build_hierarchy_to_fixpoint
        from nucleo.core import Nucleo
        n = Nucleo.__new__(Nucleo)
        g = SkillCategory(name="Mig")
        n._graph = g
        Nucleo._load_foundational_skills(n)
        load_math_domains(g)
        registrar_morfismos_certificados(g)
        pm = PatternManager()
        cb = ColimitBuilder(pm)
        build_hierarchy_to_fixpoint(g, pm, cb)
        return g, pm, cb

    def _descs(self, sistema):
        _, pm, cb = sistema
        out = []
        for p in pm.all_patterns:
            c = cb.get_colimit_for_pattern(p.id)
            if c:
                out.append((p, c.skill_id))
        return out

    def test_todo_colimite_registrado_es_un_cocono_de_verdad(self, sistema):
        """Lo que la migracion garantiza y antes no: cada colimite registrado
        admite una eleccion de flechas que conmuta con los enlaces del patron.
        """
        g, _, _ = sistema
        cong = congruencia_automatica(g)
        for p, apex in self._descs(sistema):
            assert hay_cocono_cong(p, apex, g, cong) is True, (
                f"{sorted(p.component_ids)} -> {apex} esta registrado como "
                "colimite pero no admite co-cono: es solo cota superior"
            )

    def test_la_migracion_costo_exactamente_cuatro(self, sistema):
        """31 -> 27, y los cuatro caidos se identifican con precision.

        Todos apuntaban a `homological-algebra-cat` y todos contenian
        `functors`, que es justo la componente de la que salian los enlaces
        (`functors -> algebraic-geometry`, `-> homological-algebra`,
        `-> limits`). Eran minimales entre las cotas superiores, pero ninguna
        eleccion de flechas conmutaba con esos enlaces: existian solo porque la
        delgadez regalaba la conmutacion.

        Los hermanos SIN `functors` sobreviven, y deben: son discretos, luego
        su condicion de co-cono es vacua y no hay nada que puedan incumplir.
        """
        descs = self._descs(sistema)
        assert len(descs) == 31

        hac = {frozenset(p.component_ids) for p, a in descs
               if a == "homological-algebra-cat"}
        assert all("functors" not in c for c in hac), (
            "sobrevive una descomposicion con `functors`: la conmutacion no "
            "se esta comprobando"
        )
        assert hac == {
            frozenset({"algebraic-geometry", "limits"}),
            frozenset({"homological-algebra", "limits"}),
            frozenset({"algebraic-geometry", "homological-algebra", "limits"}),
        }

    def test_sobreviven_incluso_en_la_categoria_libre(self, sistema):
        """La cota inferior honesta. Por `cocono_monotono_en_la_congruencia`
        mas identificaciones solo AÑADEN co-conos, asi que lo que aguanta con
        LIBRE aguanta con cualquier congruencia.
        """
        g, _, _ = sistema
        for p, apex in self._descs(sistema):
            assert hay_cocono_cong(p, apex, g, LIBRE) is True

    def test_el_hueco_dice_por_que(self, sistema):
        """«no existe» y «no se sabe» no son lo mismo, y el codigo no puede
        confundirlos: un hueco por cota agotada no es un hueco conceptual.
        """
        from nucleo.graph.complexity import find_colimit_cong
        g, pm, cb = sistema
        vistos = set()
        for p in pm.all_patterns:
            if cb.get_colimit_for_pattern(p.id) is None:
                apex, motivo = find_colimit_cong(p, g, cb)
                if apex is None and motivo:
                    vistos.add(motivo)
        assert vistos <= {"sin cotas superiores", "minimal sin co-cono",
                          "indecidible"}

    def test_la_congruencia_automatica_no_inventa_nada(self, sistema):
        """Solo identifica aristas paralelas que difieren en el TIPO y no
        declaran construccion. Nunca identifica construcciones distintas: Lean
        demostro que son morfismos distintos.
        """
        g, _, _ = sistema
        cong = congruencia_automatica(g)
        for a, b in cong.relaciones:
            assert len(a) == 1 and len(b) == 1, "no debe tocar caminos compuestos"
            ma, mb = g.get_morphism(a[0]), g.get_morphism(b[0])
            assert (ma.source_id, ma.target_id) == (mb.source_id, mb.target_id)
            assert not ma.metadata.get("construccion")
            assert not mb.metadata.get("construccion")

    def test_los_subpatrones_ya_no_salen_discretos_por_un_bug(self, sistema):
        """La rama de descomposiciones alternativas recogia `pred -> apex` —las
        PATAS del co-cono— en vez de los enlaces entre componentes, y
        `create_pattern` los descartaba en silencio. Resultado: subpatrones
        discretos por defecto de recoleccion, no por su forma.
        """
        from nucleo.types import MorphismType
        g, pm, _ = sistema
        for p in pm.all_patterns:
            comps = list(p.component_ids)
            hay = any(
                m.morphism_type != MorphismType.IDENTITY
                for a in comps for b in comps if a != b
                for m in g.hom(a, b)
            )
            if hay:
                assert p.index_morphisms, (
                    f"{sorted(comps)} tiene aristas entre componentes pero "
                    "sale como diagrama discreto"
                )
