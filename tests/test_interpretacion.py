"""
Guardia de la interpretacion del grafo.

El veredicto del autor sobre las 172 etiquetas es un dato editorial: si el
grafo cambia y la tabla no, o al reves, el desajuste tiene que saltar aqui y no
descubrirse tres pasos despues.
"""
import sys

import pytest

from nucleo.graph.interpretacion import (
    VEREDICTO, DUPLICADOS, MORFISMO_SIN_FIJAR, VERTICES,
    C, S, F, O, T, marca, vertices, aristas, recuento,
    forma_de, admite_colimite, FORMA_COPRODUCTO, FORMA_PUSHOUT,
    SIN_PUSHOUT, PUSHOUT_SI_DETERMINISTA, RESTRICCIONES,
    DEGRADADAS, FUSIONES, SUBCATEGORIA_PLENA, NOTA_FUSION,
    cambia_de_valor, resolver, vertices_tras_fusionar,
    APICE_FALTANTE, ARISTA_FALTANTE, NO_SON_DOS_COCIENTES,
    VERTICES_ANADIDOS, LAS_DEL_AUTOR,
)


@pytest.fixture(scope="module")
def grafo():
    sys.argv = ["x"]
    from nucleo.graph.category import SkillCategory
    from nucleo.pillars.math_domains import load_math_domains
    from nucleo.core import Nucleo
    n = Nucleo.__new__(Nucleo)
    g = SkillCategory(name="Interp")
    n._graph = g
    Nucleo._load_foundational_skills(n)
    load_math_domains(g)
    return g


class TestCobertura:

    def test_todas_las_etiquetas_tienen_veredicto(self, grafo):
        faltan = sorted(set(grafo.skill_ids) - set(VEREDICTO))
        assert not faltan, f"sin veredicto: {faltan}"

    def test_no_hay_veredictos_inventados(self, grafo):
        """Salvo los que el propio grafo obligo a añadir, y esos estan
        declarados aparte precisamente para que esta guardia siga sirviendo."""
        sobran = sorted(set(VEREDICTO) - set(grafo.skill_ids) - VERTICES_ANADIDOS)
        assert not sobran, f"no estan en el grafo: {sobran}"

    def test_los_vertices_anadidos_no_estan_en_el_grafo(self, grafo):
        """Ese es el hallazgo, no un fallo: el grafo detecto un vertice que
        FALTA. Cuando se añadan al grafo, este test cae y hay que borrarlo."""
        assert not (VERTICES_ANADIDOS & set(grafo.skill_ids))

    def test_el_recuento_cuadra_con_el_documento(self):
        """Las cifras del veredicto, tal como las publico el autor: sobre sus
        172, sin contar los dos vertices que el grafo obligo a añadir."""
        del_autor = {k: v for k, v in VEREDICTO.items()
                     if k not in VERTICES_ANADIDOS}
        assert len(del_autor) == LAS_DEL_AUTOR
        cuenta: dict = {}
        for v in del_autor.values():
            cuenta[v.marca] = cuenta.get(v.marca, 0) + 1
        assert cuenta == {C: 73, S: 14, F: 28, O: 4, T: 53}

    def test_87_vertices_28_aristas(self):
        """87 son los del autor; los dos añadidos van aparte."""
        assert len(set(vertices()) - VERTICES_ANADIDOS) == 87
        assert len(vertices()) == 89
        assert len(aristas()) == 28


class TestCoherencia:

    def test_toda_marca_es_valida(self):
        assert {e.marca for e in VEREDICTO.values()} <= {C, S, F, O, T}

    def test_los_vertices_declaran_objetos_y_morfismos(self):
        """Un vertice sin morfismos declarados no sirve: la categoria son las
        flechas tanto como los objetos."""
        for k, e in VEREDICTO.items():
            if e.marca in VERTICES:
                assert e.objeto, f"{k} es vertice y no dice que es un objeto"

    def test_las_aristas_declaran_su_funtor(self):
        for k, e in VEREDICTO.items():
            if e.marca == F:
                assert e.morfismos, f"{k} es arista y no dice que funtor es"

    def test_los_duplicados_tienen_veredicto(self, grafo):
        for nombre, ids in DUPLICADOS:
            for i in ids:
                assert i in VEREDICTO, f"{i} en DUPLICADOS sin veredicto"
                assert i in grafo.skill_ids, f"{i} no esta en el grafo"

    def test_las_marcas_dentro_de_un_grupo_pueden_diferir(self):
        """DUPLICADOS agrupa etiquetas que DENOTAN la misma categoria, no
        que compartan marca.

        `proof-theory` denota la categoria deductiva pero es T —nombra
        una rama—; `nat-trans` denota [C,D] pero es F —nombra la capa
        de flechas—. Confundir las dos relaciones fue un error de este
        test, no de la tabla.
        """
        grupos = {n: ids for n, ids in DUPLICADOS}
        assert marca("proof-theory") == T
        assert marca("fol-deduction") == C
        assert {"proof-theory", "fol-deduction"} <= set(
            grupos["categoria deductiva"])
        assert marca("nat-trans") == F
        assert marca("functors") == C

    def test_cuantos_vertices_redundantes_hay(self):
        """El hallazgo: hay grupos con MAS DE UN vertice legitimo.

        Un colimite sobre dos vertices que nombran la misma categoria sale
        degenerado. Esta cifra es la medida del problema, y el test existe para
        que no cambie en silencio.
        """
        redundantes = sum(
            max(0, sum(1 for i in ids if marca(i) in VERTICES) - 1)
            for _, ids in DUPLICADOS
        )
        assert redundantes == 8

    def test_las_de_morfismo_sin_fijar_son_vertices(self):
        for i in MORFISMO_SIN_FIJAR:
            assert marca(i) in VERTICES, (
                f"{i} no es vertice; no tiene sentido decir que le falta el morfismo"
            )


class TestHallazgos:
    """Las tres cosas que el veredicto descubrio y que conviene no perder."""

    def test_homotopy_type_theory_es_la_unica_imposible_por_fundamento(self):
        e = VEREDICTO["homotopy-type-theory"]
        assert e.lean is None
        assert "IMPOSIBLE en Lean 4" in e.nota

    def test_fol_deduction_no_es_tema(self):
        """Un sistema deductivo es una categoria (Lambek), y es el domicilio de
        las quince tacticas."""
        assert marca("fol-deduction") == C
        assert VEREDICTO["fol-deduction"].lean is None, "Mathlib no lo tiene"

    def test_las_tacticas_y_estrategias_estan_fuera(self, grafo):
        tacticas = [i for i in grafo.skill_ids
                    if i.startswith(("tactic-", "strategy-"))]
        assert len(tacticas) == 15
        assert all(marca(i) == T for i in tacticas)

    def test_homology_y_limits_son_aristas(self):
        """Eran los dos vertices del bloque 1 que resultaron ser funtores."""
        assert marca("homology") == F
        assert marca("limits") == F


class TestLasDosDecisiones:
    """
    Las dos elecciones de morfismos que el autor tomo, y su precio.

    Ninguna la podia tomar el codigo: cambian QUE colimites existen, no como
    se calculan.
    """

    def test_measure_theory_usa_nucleos(self):
        e = VEREDICTO["measure-theory"]
        assert "nucleo" in e.morfismos.lower()
        assert "MEDIBLE" in e.objeto, "el objeto ya no es un espacio de medida"

    def test_probability_es_subcategoria_ancha_de_measure(self):
        """Mismos objetos, nucleos de Markov contenidos en los nucleos."""
        assert "ancha" in VEREDICTO["probability-theory"].nota.lower()
        assert marca("probability-theory") == C
        assert marca("measure-theory") == C

    def test_homotopy_theory_es_la_localizacion(self):
        """Top[W^-1], no hTop. Lo imponen las aristas que ya salen del vertice.

        Todas —homology, cohomology, fundamental-group— invierten W, luego
        factorizan por la localizacion, que es el vertice inicial con esa
        propiedad.
        """
        e = VEREDICTO["homotopy-theory"]
        assert "RELATIVA" in e.objeto
        assert e.lean is None, "sin estructura de Quillen sobre Top en Mathlib"
        for arista in ("homology", "cohomology", "fundamental-group"):
            assert marca(arista) == F

    def test_solo_quedan_dos_sin_fijar(self):
        assert set(MORFISMO_SIN_FIJAR) == {"metric-spaces", "banach-spaces"}


class TestLaReglaDeLaForma:
    """La regla mira la FORMA del diagrama, no su contenido."""

    class _P:
        def __init__(self, links):
            self.index_morphisms = links

    def test_diagrama_discreto_es_coproducto(self):
        assert forma_de(self._P({})) == FORMA_COPRODUCTO

    def test_con_enlaces_distinguidos_es_pushout(self):
        assert forma_de(self._P({"d_0_1": ("0", "1")})) == FORMA_PUSHOUT

    def test_el_coproducto_existe_siempre(self):
        """Hom(coproducto, X) = producto de Hom(A_i, TX): sobrevive en nucleos."""
        for apex in ("homotopy-theory", "measure-theory", "cualquiera"):
            ok, _ = admite_colimite(self._P({}), apex)
            assert ok

    def test_el_pushout_no_existe_en_el_vertice_homotopico(self):
        """Ni hTop ni Top[W^-1] tienen pushouts.

        Y el resultado correcto no es «el colimite vale X» sino «este vertice
        no admite la operacion»: el colimite homotopico es otra operacion.
        """
        ok, motivo = admite_colimite(self._P({"d": ("0", "1")}), "homotopy-theory")
        assert ok is False
        assert "no admite la operacion" in motivo
        assert "homotopico" in motivo.lower()

    def test_el_pushout_en_medida_pide_flechas_deterministas(self):
        ok, motivo = admite_colimite(self._P({"d": ("0", "1")}), "measure-theory")
        assert ok is True
        assert "determinista" in motivo


class TestFormaDelGrafoReal:
    """Lo medido: las dos decisiones no invalidan nada de lo que ya habia."""

    @pytest.fixture(scope="class")
    def descomposiciones(self):
        sys.argv = ["x"]
        from nucleo.graph.category import SkillCategory
        from nucleo.pillars.math_domains import load_math_domains
        from nucleo.mes.patterns import PatternManager, ColimitBuilder
        from nucleo.graph.complexity import build_hierarchy_to_fixpoint
        from nucleo.graph.no_delgado import registrar_morfismos_certificados
        from nucleo.core import Nucleo
        n = Nucleo.__new__(Nucleo)
        g = SkillCategory(name="Forma")
        n._graph = g
        Nucleo._load_foundational_skills(n)
        load_math_domains(g)
        registrar_morfismos_certificados(g)
        pm = PatternManager()
        cb = ColimitBuilder(pm)
        build_hierarchy_to_fixpoint(g, pm, cb)
        out = []
        for p in pm.all_patterns:
            col = cb.get_colimit_for_pattern(p.id)
            if col:
                out.append((p, col.skill_id))
        return out

    def test_casi_todas_son_coproducto(self, descomposiciones):
        """24 de 27 siguen siendo coproductos, y eso NO es neutral.

        Las cifras anteriores —29 de 31— median dos defectos a la vez:

          · la rama de descomposiciones alternativas recogia las PATAS del
            co-cono en vez de los enlaces entre componentes, asi que sus
            subpatrones salian discretos por un bug, no por su forma;
          · `find_colimit` solo pedia cota superior, asi que cuatro patrones
            de `homological-algebra-cat` registraban colimite sin que ninguna
            eleccion de flechas conmutara.

        Corregidos los dos, quedan 27 colimites de los que 3 tienen estructura.
        Que 24 sigan siendo discretos importa: el colimite de un diagrama
        discreto es un COPRODUCTO, y un coproducto de coproductos vuelve a ser
        un coproducto — se aplana sea la categoria delgada o no. O sea que
        salir de la delgadez es NECESARIO para el orden >= 2 pero no
        suficiente: hacen falta diagramas con enlaces.
        """
        formas = [forma_de(p) for p, _ in descomposiciones]
        assert len(descomposiciones) == 27
        assert formas.count(FORMA_COPRODUCTO) == 24
        assert formas.count(FORMA_PUSHOUT) == 3

    def test_ninguna_pierde_su_colimite_por_las_decisiones(self, descomposiciones):
        """Las cuatro que tocan un vertice decidido son de forma coproducto,
        luego las dos elecciones no cuestan ningun colimite de los que habia."""
        decididos = SIN_PUSHOUT | PUSHOUT_SI_DETERMINISTA
        for p, apex in descomposiciones:
            if (set(p.component_ids) | {apex}) & decididos:
                ok, _ = admite_colimite(p, apex)
                assert ok, f"{sorted(p.component_ids)} -> {apex} deja de admitir"


class TestDegradaciones:
    """`limits` y `nat-trans` no se borran: se degradan."""

    def test_las_dos_estan_degradadas(self):
        assert set(DEGRADADAS) == {"limits", "nat-trans"}

    def test_ninguna_era_vertice(self):
        """Por eso degradarlas no baja el recuento de vertices."""
        for k in DEGRADADAS:
            assert marca(k) == F

    def test_cada_una_dice_que_hacer_con_sus_aristas(self):
        for k, d in DEGRADADAS.items():
            assert d["entrantes"] and d["salientes"], (
                f"{k}: hay que repartir las aristas incidentes por direccion"
            )

    def test_limits_nombra_la_operacion_del_propio_grafo(self):
        """La razon de fondo: no fallaba por estar mal poblado."""
        assert "confusion de nivel" in VEREDICTO["limits"].nota


class TestFusiones:

    def test_los_alias_resuelven_a_un_superviviente(self):
        for retirada, superviviente in FUSIONES.items():
            assert resolver(retirada) == resolver(superviviente)
            assert superviviente not in FUSIONES or resolver(superviviente) != retirada

    def test_ninguna_etiqueta_se_borra(self, grafo):
        """Las retiradas quedan como alias: si se borraran, las 172 dejarian
        de mapear sobre el grafo."""
        for retirada in FUSIONES:
            assert retirada in VEREDICTO
            assert retirada in grafo.skill_ids

    def test_el_recuento_de_vertices(self):
        """87 -> 81. No 79 ni 76.

        De las once etiquetas que se retiran o degradan, CUATRO no eran
        vertices en el propio veredicto: proof-theory y recursion-theory son T,
        nat-trans y limits son F. Nunca estuvieron en los 87.
        """
        assert len(set(vertices()) - VERTICES_ANADIDOS) == 87
        assert len(set(vertices_tras_fusionar()) - VERTICES_ANADIDOS) == 81
        no_eran = [k for k in list(FUSIONES) + list(DEGRADADAS)
                   if marca(k) not in VERTICES]
        assert set(no_eran) == {"proof-theory", "recursion-theory",
                                "nat-trans", "limits"}


class TestNoFusionar:
    """La regla condicional, y por que se activo en dos de los tres grupos."""

    def test_las_dos_distinciones_se_respetan(self):
        assert set(SUBCATEGORIA_PLENA) == {"arithmetic-geometry", "number-fields"}

    def test_ninguna_subcategoria_plena_esta_fusionada(self):
        """Retirar la etiqueta y meter la inclusion arreglan igual el colimite;
        lo que no se puede es hacer las dos cosas."""
        for sub in SUBCATEGORIA_PLENA:
            assert sub not in FUSIONES

    def test_cada_una_declara_su_ambiente(self):
        for sub, (ambiente, porque) in SUBCATEGORIA_PLENA.items():
            assert marca(ambiente) in VERTICES
            assert porque


class TestElCocienteNoMueveNingunValor:
    """
    El aviso: una fusion es un cociente del diagrama indice, y el colimite del
    cociente no es el del original. Donde dos etiquetas fusionadas coexistian,
    lo que era un coproducto pasa a ser un coigualador.

    Aplicada la regla condicional, ninguna descomposicion queda en ese caso —
    que es precisamente para lo que sirve la regla.
    """

    @pytest.fixture(scope="class")
    def descomposiciones(self):
        sys.argv = ["x"]
        from nucleo.graph.category import SkillCategory
        from nucleo.pillars.math_domains import load_math_domains
        from nucleo.mes.patterns import PatternManager, ColimitBuilder
        from nucleo.graph.complexity import build_hierarchy_to_fixpoint
        from nucleo.graph.no_delgado import registrar_morfismos_certificados
        from nucleo.core import Nucleo
        n = Nucleo.__new__(Nucleo)
        g = SkillCategory(name="Cociente")
        n._graph = g
        Nucleo._load_foundational_skills(n)
        load_math_domains(g)
        registrar_morfismos_certificados(g)
        pm = PatternManager()
        cb = ColimitBuilder(pm)
        build_hierarchy_to_fixpoint(g, pm, cb)
        return [(p, cb.get_colimit_for_pattern(p.id).skill_id)
                for p in pm.all_patterns if cb.get_colimit_for_pattern(p.id)]

    def test_ninguna_cambia_de_valor(self, descomposiciones):
        movidas = [(sorted(p.component_ids), ap, cambia_de_valor(p, ap))
                   for p, ap in descomposiciones if cambia_de_valor(p, ap)]
        assert movidas == [], (
            f"estas cambian de valor al fusionar y hay que recalcularlas: {movidas}"
        )

    def test_si_se_fusionara_arithmetic_geometry_si_cambiarian(self, descomposiciones):
        """Contraprueba: la regla no es decorativa.

        Con `arithmetic-geometry` fusionado en `algebraic-geometry`, tres
        descomposiciones tendrian el apice colapsado dentro de sus propias
        componentes.
        """
        colapsan = 0
        for p, ap in descomposiciones:
            nodos = set(p.component_ids) | {ap}
            if {"algebraic-geometry", "arithmetic-geometry"} <= nodos:
                colapsan += 1
        assert colapsan == 3


class TestElApiceQueFaltaba:
    """`homology` de apice: el grafo detecto un vertice que FALTA.

    El diagnostico no es el de `limits`. Alli habia un objeto donde debia haber
    una operacion y el patron estaba mal poblado. Aqui las componentes son
    legitimas, la forma es correcta y el co-cono esta bien formado; lo unico
    que falla es que el vertice de llegada se etiqueto con el nombre del
    invariante que ese vertice calcula, porque era la etiqueta mas cercana
    disponible entre las 172.
    """

    @pytest.fixture(scope="class")
    def grafo_patrones(self):
        sys.argv = ["x"]
        from nucleo.graph.category import SkillCategory
        from nucleo.pillars.math_domains import load_math_domains
        from nucleo.mes.patterns import PatternManager, ColimitBuilder
        from nucleo.graph.complexity import build_hierarchy_to_fixpoint
        from nucleo.graph.no_delgado import registrar_morfismos_certificados
        from nucleo.core import Nucleo
        n = Nucleo.__new__(Nucleo)
        g = SkillCategory(name="Apice")
        n._graph = g
        Nucleo._load_foundational_skills(n)
        load_math_domains(g)
        registrar_morfismos_certificados(g)
        pm = PatternManager()
        cb = ColimitBuilder(pm)
        build_hierarchy_to_fixpoint(g, pm, cb)
        descs = [(p, cb.get_colimit_for_pattern(p.id).skill_id)
                 for p in pm.all_patterns if cb.get_colimit_for_pattern(p.id)]
        return g, descs

    # ── EL TEST QUE FALSA LA LECTURA ────────────────────────────────────────

    def test_exact_sequences_emite_luego_no_es_una_cospan(self, grafo_patrones):
        """El test estructural que decide entre las dos lecturas.

        Para que el apice sea el cociente, `exact-sequences` tiene que ser
        FUENTE de flechas. Si solo recibiera, el diagrama seria una cospan, su
        colimite seria trivialmente `homological-algebra`, la deteccion seria
        vacia — y entonces habria que retirar las cuatro y dejar la arista.

        Emite tres. La lectura del cociente sobrevive.
        """
        from nucleo.types import MorphismType
        g, _ = grafo_patrones
        salientes = {m.target_id for m in g.outgoing_morphisms("exact-sequences")
                     if m.morphism_type != MorphismType.IDENTITY}
        assert salientes, (
            "exact-sequences no emite ninguna flecha: el diagrama es una "
            "cospan y la lectura del cociente cae"
        )
        assert len(salientes) == 3

    def test_la_pata_al_apice_no_transporta_informacion(self, grafo_patrones):
        """Segunda comprobacion: la pata de `exact-sequences` es constante.

        Si transportara informacion no seria un cociente. La arista al apice no
        lleva `construccion`, luego es generica: no transporta nada.
        """
        from nucleo.types import MorphismType
        g, _ = grafo_patrones
        al_apice = [m for m in g.outgoing_morphisms("exact-sequences")
                    if m.target_id == "homology"
                    and m.morphism_type != MorphismType.IDENTITY]
        assert al_apice, "no hay pata de exact-sequences al apice"
        assert all(getattr(m, "construccion", None) is None for m in al_apice)

    # ── EL HALLAZGO QUE EL TEST DESTAPO ─────────────────────────────────────

    def test_falta_tambien_la_arista_de_la_inclusion(self, grafo_patrones):
        """El test pasa, pero al mirar CUALES flechas emite aparece otra cosa.

        La arista que el pushout necesita —la inclusion de los aciclicos,
        `exact-sequences -> homological-algebra`— NO EXISTE en el grafo. Emite
        a `abelian-categories`, a `homology` y a `tactic-ring`.

        Al grafo le falta un vertice Y una arista. Lo primero ya se sabia.
        """
        g, _ = grafo_patrones
        fuente, destino, _motivo = ARISTA_FALTANTE
        assert not g.hom(fuente, destino), (
            "la inclusion ya existe: ARISTA_FALTANTE esta obsoleta"
        )
        assert fuente == "exact-sequences"
        assert destino == "homological-algebra"

    def test_no_son_cuatro_niveles_de_cociente_sino_uno_y_sus_subconjuntos(
            self, grafo_patrones):
        """Se esperaba que las cuatro se distinguieran por el nivel al que
        toman el cociente (Ch -> K, K -> D) y colapsaran a dos al regenerarlas.

        No: son UN patron de tres componentes mas sus tres subconjuntos de dos,
        que es lo que emite el detector desde que se habilito la multiplicidad.
        No hay dos cocientes ahi, hay uno y su conjunto potencia.
        """
        _, descs = grafo_patrones
        conjuntos = [frozenset(p.component_ids)
                     for p, ap in descs if ap == "homology"]
        assert len(conjuntos) == 4
        grande = max(conjuntos, key=len)
        assert grande == frozenset(APICE_FALTANTE["homology"]["componentes"])
        pequenos = [c for c in conjuntos if c != grande]
        assert len(pequenos) == 3
        assert all(len(c) == 2 and c < grande for c in pequenos)
        assert NO_SON_DOS_COCIENTES

    # ── LOS VERTICES AÑADIDOS ───────────────────────────────────────────────

    def test_el_apice_correcto_esta_en_la_tabla_y_es_categoria(self):
        assert marca("derived-category") == C
        assert marca("graded-objects") == C
        assert APICE_FALTANTE["homology"]["apice_correcto"] == "derived-category"
        assert APICE_FALTANTE["homology"]["codominio"] == "graded-objects"

    def test_homology_sigue_siendo_arista_pero_ahora_con_dominio(self):
        """Su sitio no cambia —arista, no vertice, como decia el veredicto—.
        Lo que cambia es que ahora tiene dominio propio: H_* : D(A) -> grAb.
        """
        assert marca("homology") == F
        assert "D(A)" in VEREDICTO["homology"].morfismos
        assert "derived-category" in VEREDICTO["homology"].nota

    def test_las_tres_patas_son_distintas_y_ninguna_es_la_homologia(self):
        """Ahi esta el nudo: con apice `grAb` la descomposicion seria circular
        —las patas serian la propia homologia—; con el cociente, las tres patas
        son la inclusion, el colapso y las cadenas singulares.
        """
        patas = APICE_FALTANTE["homology"]["patas"]
        assert set(patas) == set(APICE_FALTANTE["homology"]["componentes"])
        assert "homolog" not in patas["algebraic-topology"].lower()
        assert "cadenas singulares" in patas["algebraic-topology"]

    def test_el_apice_no_es_ninguna_de_sus_componentes(self):
        """`homological-algebra` es componente: no puede ser tambien el vertice
        de llegada. El apice tiene que ser un vertice nuevo.
        """
        apice = APICE_FALTANTE["homology"]["apice_correcto"]
        assert apice not in APICE_FALTANTE["homology"]["componentes"]

    def test_cohomology_no_aparece_de_apice(self, grafo_patrones):
        """Valdria lo mismo sin cambiar nada —mismo cociente, misma arista,
        distinto signo en la graduacion— pero hoy no hace falta.
        """
        _, descs = grafo_patrones
        assert not [p for p, ap in descs if ap == "cohomology"]
