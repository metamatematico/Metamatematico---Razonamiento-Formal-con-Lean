# -*- coding: utf-8 -*-
"""Guardianes de la Fase 0: la base canonica de areas y los sorts.

QUE IMPIDEN QUE VUELVA A PASAR
------------------------------
El grafo tenia DOS taxonomias de area compitiendo y nada que las atara:

  · 22 nodos `area-*` en CamelCase leidos de Mathlib;
  · 15 valores de `metadata["category"]` en kebab, curados a mano, de los
    cuales CINCO no nombraban un area (`lean-tactics`, `proof-strategies`,
    `area`, `optimization`, `computation`).

Y `construir_funtor` proyectaba sobre la segunda, asi que el funtor aterrizaba
en una base donde `lean-tactics` era un objeto al mismo nivel que `topology`.
Nada fallaba: el funtor era funtorial y las cifras eran creibles.

Estos tests hacen que falle.
"""
import pytest

from nucleo.pillars import areas as A


@pytest.fixture(scope="module")
def grafo():
    from nucleo.core import Nucleo
    from nucleo.graph.category import SkillCategory
    n = Nucleo.__new__(Nucleo)
    n._graph = SkillCategory()
    Nucleo._load_foundational_skills(n)
    return n._graph


class TestLaBase:

    def test_el_puente_aterriza_en_la_base(self):
        """Un typo en el puente produce un area fantasma que nada delata."""
        fuera = set(A.CATEGORIA_A_AREA.values()) - A.AREAS_CANONICAS
        assert not fuera, f"areas del puente que no estan en la base: {sorted(fuera)}"

    def test_toda_categoria_curada_esta_resuelta(self):
        """
        Cada etiqueta curada tiene que ir a un area O a un sort. Una que no
        vaya a ninguno se queda muda: ni entra en la base ni se declara como
        lo que no es.
        """
        from nucleo.pillars.math_domains import ALL_DOMAIN_SKILLS
        cats = {d.category for d in ALL_DOMAIN_SKILLS if d.category}
        huerfanas = [c for c in cats
                     if not A.area_de_categoria(c) and not A.sort_de_categoria(c)]
        assert not huerfanas, f"etiquetas sin resolver: {sorted(huerfanas)}"

    def test_las_areas_llevan_keywords(self):
        """
        LA PUERTA ESTABA CERRADA: `0 de 22`. El area es la via de entrada al
        grafo y el emparejador compara contra id, nombre y keywords — el id
        `area-numbertheory` no casa con «numeros primos» ni con «number
        theory», asi que sin keywords ninguna consulta entraba por ahi.
        """
        faltan = sorted(a for a in A.AREAS_CANONICAS if not A.keywords_de_area(a))
        assert not faltan, f"areas sin keywords: {faltan}"

    def test_las_keywords_no_se_repiten_entre_areas(self):
        """
        Una keyword en dos areas hace que la consulta abra las dos, y la
        puerta deja de discriminar. `anillo` en Algebra y en RingTheory es
        deliberado —son la misma cosa a dos granularidades— asi que se permite
        el solape pero se acota: ninguna keyword en tres o mas areas.
        """
        import collections
        c = collections.Counter()
        for a in A.AREAS_CANONICAS:
            for kw in A.keywords_de_area(a):
                c[kw.lower()] += 1
        muy_repetidas = {k: v for k, v in c.items() if v >= 3}
        assert not muy_repetidas, f"keywords en 3+ areas: {muy_repetidas}"


class TestElGrafoTipado:

    def test_todo_nodo_tiene_sort(self, grafo):
        """Sin sort no se sabe en que fibra vive un nodo."""
        sin = [i for i in grafo.skill_ids
               if not (grafo.get_skill(i).metadata or {}).get("sort")]
        assert not sin, f"nodos sin sort: {sorted(sin)[:10]}"

    def test_los_sorts_son_los_declarados(self, grafo):
        usados = {(grafo.get_skill(i).metadata or {}).get("sort")
                  for i in grafo.skill_ids}
        assert usados <= A.SORTS, f"sorts no declarados: {sorted(usados - A.SORTS)}"

    def test_toda_area_asignada_esta_en_la_base(self, grafo):
        """Un area escrita a mano que no este en la base es un area fantasma."""
        malas = {(grafo.get_skill(i).metadata or {}).get("area")
                 for i in grafo.skill_ids}
        malas = {a for a in malas if a and a not in A.AREAS_CANONICAS}
        assert not malas, f"areas fuera de la base: {sorted(malas)}"

    def test_lo_que_no_es_matematica_no_tiene_area(self, grafo):
        """
        Una tactica no es de topologia ni de algebra. `area=None` ahi es una
        RESPUESTA, no un hueco — y volver a darles area es exactamente el
        fallo que este modulo existe para cerrar.
        """
        con_area = []
        for i in grafo.skill_ids:
            md = grafo.get_skill(i).metadata or {}
            if md.get("sort") in A.SIN_AREA and md.get("area"):
                con_area.append((i, md.get("area")))
        assert not con_area, f"no-matematicas con area: {con_area}"

    def test_los_nodos_de_area_son_su_propia_area(self, grafo):
        for i in grafo.skill_ids:
            if not i.startswith("area-"):
                continue
            md = grafo.get_skill(i).metadata or {}
            assert md.get("sort") == A.AREA, f"{i} no tiene sort AREA"
            assert md.get("area") == A.area_de_id(i), (
                f"{i} dice area={md.get('area')!r}")


class TestElEmparejadorNormalizado:
    """
    La puntuacion y los acentos hacian que dos alfabetos distintos se
    compararan entre si. Medido antes: «¿Es 17 un numero primo?» no casaba con
    NADA.
    """

    def _match(self, grafo, q):
        from nucleo.core import Nucleo
        n = Nucleo.__new__(Nucleo)
        return Nucleo._match_skills_to_query(n, q, grafo)

    @pytest.mark.parametrize("consulta,esperado", [
        ("¿Es 17 un número primo?", "area-numbertheory"),
        ("Demuestra que la teoría de anillos es difícil", "area-ringtheory"),
        ("teoria de conjuntos", "area-settheory"),
    ])
    def test_la_puntuacion_y_los_acentos_no_cierran_la_puerta(
            self, grafo, consulta, esperado):
        assert esperado in self._match(grafo, consulta), (
            f"{consulta!r} no alcanza {esperado}")

    def test_el_area_no_desplaza_a_los_concretos(self, grafo):
        """
        El area declara 389 keywords y cada una vale +2, asi que ganaba el
        ranking casi siempre — y no aporta ningun identificador de Mathlib.
        Medido: la cobertura de nombres contra ProofNet caia de 13,6 % a
        13,3 % por puro desplazamiento en el corte a top-10.

        Un match de area es MAS GRUESO que uno de concepto. Va detras.
        """
        m = self._match(grafo, "Demuestra que la teoría de anillos es difícil")
        concretos = [s for s in m if not s.startswith("area-")]
        assert concretos, "solo areas: los concretos fueron desplazados"
        primer_area = next(i for i, s in enumerate(m) if s.startswith("area-"))
        ultimo_concreto = max(i for i, s in enumerate(m)
                              if not s.startswith("area-"))
        assert primer_area > ultimo_concreto, (
            f"un area va delante de un concreto: {m}")


class TestElNormalizador:

    def test_la_enye_no_es_una_ene(self):
        """`año` -> `ano` cambia la palabra."""
        from nucleo.texto import normalizar
        assert normalizar("año") == "año"
        assert normalizar("Teoría") == "teoria"

    def test_los_dos_lados_se_normalizan_igual(self):
        """
        Normalizar solo la consulta EMPEORA las cosas: una keyword acentuada
        dejaria de casar. La comprobacion es que la funcion es la misma.
        """
        from nucleo.texto import tokens
        assert tokens("¿Es primo?") == tokens("es primo")
        assert "teoria" in tokens("teoría de categorías")

    def test_no_casa_dentro_de_otra_palabra(self):
        """El fallo de `prime` dentro de `primer`, que ya estaba visto."""
        from nucleo.texto import contiene_frase, normalizar
        assert not contiene_frase(normalizar("los primeros pasos"), "primo")
        assert contiene_frase(normalizar("un número primo"), "primo")
