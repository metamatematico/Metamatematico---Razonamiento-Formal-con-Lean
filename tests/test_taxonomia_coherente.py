"""
Guardian de la taxonomia de categorias matematicas.

POR QUE
-------
La misma lista de 14 categorias estaba escrita a mano en CINCO sitios de tres
subsistemas distintos:

    nucleo/multi_agent/specialized_agent.py   CATEGORIES      (canonica)
    nucleo/multi_agent/colimit_agents.py      CATEGORIES
    scripts/balance_datasets.py               CATEGORIES_14
    scripts/split_by_category.py              CATEGORIES
    scripts/train_multiagent.py               CATEGORIES

y una sexta vez, habilidad por habilidad, como `category="algebra"` en
nucleo/pillars/math_domains.py. Coincidian, pero por nada mas que por haberse
escrito bien: ni un import ni una comprobacion las ataba.

Es el mismo patron que ya ha mordido a este sistema varias veces: la copia
congelada que envejece en silencio y no falla al hacerlo. Estos tests hacen que
falle.

QUE NO ENTRA
------------
`scripts/evaluate_benchmark.py` define MATH_CATEGORIES con `prealgebra`,
`intermediate_algebra` y guiones bajos: son las etiquetas del dataset MATH, una
taxonomia legitimamente distinta. Se excluye a proposito.
"""
import re
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent

#: Los ficheros que antes declaraban su propia copia y ahora deben importarla.
COPIAS = [
    ("nucleo/multi_agent/specialized_agent.py", "CATEGORIES"),
    ("nucleo/multi_agent/colimit_agents.py", "CATEGORIES"),
    ("scripts/balance_datasets.py", "CATEGORIES_14"),
    ("scripts/split_by_category.py", "CATEGORIES"),
    ("scripts/train_multiagent.py", "CATEGORIES"),
]


def _extraer(ruta: str, nombre: str):
    """
    Devuelve la lista literal de categorias declarada en un fichero, o None si
    no hay ninguna —que es lo que se espera ahora que todos importan.
    """
    s = (RAIZ / ruta).read_text(encoding="utf-8")
    for linea in s.splitlines():
        if not linea.startswith(nombre):
            continue
        # `NOMBRE = [` abre una lista literal; `NOMBRE = OTRA_COSA` es un alias.
        if "[" not in linea.split("=", 1)[-1]:
            continue
        bloque = s[s.index(linea):]
        bloque = bloque[: bloque.index("]") + 1]
        cats = set(re.findall(r'"([a-z][a-z-]+)"', bloque))
        if cats:
            return cats
    return None


@pytest.fixture(scope="module")
def canonica() -> set[str]:
    from nucleo.multi_agent.specialized_agent import CATEGORIES
    return set(CATEGORIES)


class TestFuenteUnica:

    def test_la_canonica_se_deriva_de_las_habilidades(self, canonica):
        """
        CATEGORIES debe ser la IMAGEN de pi sobre las habilidades de dominio,
        no una lista escrita aparte. Si este test falla, alguien añadio una
        categoria en un sitio y no en el otro.
        """
        from nucleo.pillars.math_domains import ALL_DOMAIN_SKILLS
        derivada = {d.category for d in ALL_DOMAIN_SKILLS
                    if getattr(d, "category", None)}
        assert derivada == canonica, (
            f"la taxonomia declarada y la imagen de pi divergen: "
            f"solo declarada={sorted(canonica - derivada)}, "
            f"solo en habilidades={sorted(derivada - canonica)}"
        )

    def test_el_orden_es_determinista(self):
        """
        `classify_query` puntua recorriendo CATEGORIES; un orden inestable
        haria que los empates se resolvieran de forma distinta entre
        ejecuciones.
        """
        from nucleo.multi_agent.specialized_agent import CATEGORIES
        assert list(CATEGORIES) == sorted(CATEGORIES)

    @pytest.mark.parametrize("ruta,nombre", COPIAS)
    def test_nadie_vuelve_a_declararla_a_mano(self, ruta, nombre):
        """
        Invariante mas fuerte que comparar copias: que no HAYA copias. Cada uno
        de estos ficheros debe importar la taxonomia, no reescribirla.

        Comparar listas literales solo detecta la divergencia despues de que
        ocurra; esto impide que vuelva a haber dos fuentes.
        """
        literal = _extraer(ruta, nombre)
        assert literal is None, (
            f"{ruta} declara {nombre} como lista literal de {len(literal)} "
            "categorias. Debe importar CATEGORIAS_DE_DOMINIO de "
            "nucleo.pillars.math_domains."
        )

    @pytest.mark.parametrize("ruta,nombre", COPIAS)
    def test_cada_consumidor_recibe_la_canonica(self, ruta, nombre, canonica):
        """Y lo que importan es, de hecho, la taxonomia buena."""
        s = (RAIZ / ruta).read_text(encoding="utf-8")
        assert "CATEGORIAS_DE_DOMINIO" in s, (
            f"{ruta} no importa la taxonomia canonica"
        )


class TestCoherenciaConElFuntor:
    """La taxonomia es el codominio de pi; deben cuadrar."""

    def test_la_imagen_de_pi_son_las_categorias_mas_el_objeto_base(self, canonica):
        """
        La proyeccion sobre AGENTES. Se pide por su nombre.

        `construir_funtor` sirve DOS bases distintas sobre el mismo grafo, y
        antes las confundia en una sola: la de agentes —esta— y la de AREAS,
        que es la base de la fibracion. Este test guarda la de agentes, que es
        de la que trata este fichero; la de areas tiene la suya debajo.
        """
        import sys
        sys.argv = ["x"]
        from scripts.train_gnn_ppo import build_skill_graph
        from nucleo.graph.functor import construir_funtor, OBJETO_BASE

        g = build_skill_graph()
        imagen = set(construir_funtor(g, base="category").codominio.objetos)
        assert imagen == canonica | {OBJETO_BASE}, (
            f"el codominio de pi no es la taxonomia + el objeto base: "
            f"diferencia={sorted(imagen ^ (canonica | {OBJETO_BASE}))}"
        )

    def test_la_base_de_areas_no_admite_lo_que_no_es_un_area(self):
        """
        La proyeccion sobre AREAS, que es la base de la fibracion.

        El fallo que este test impide repetir: `construir_funtor` proyectaba
        sobre `category`, que mezcla once ramas matematicas con tres etiquetas
        que no lo son. El codominio tenia `lean-tactics` como objeto al mismo
        nivel que `topology`, y `solo_jerarquia` existia para tapar el sintoma
        por el otro lado.

        Una tactica no pertenece a ninguna rama: va al objeto base, y eso es
        una respuesta, no un hueco.
        """
        import sys
        sys.argv = ["x"]
        from scripts.train_gnn_ppo import build_skill_graph
        from nucleo.graph.functor import construir_funtor, OBJETO_BASE
        from nucleo.pillars.areas import AREAS_CANONICAS

        g = build_skill_graph()
        imagen = set(construir_funtor(g, base="area").codominio.objetos)
        intrusos = imagen - AREAS_CANONICAS - {OBJETO_BASE}
        assert not intrusos, (
            f"objetos en la base que no son areas: {sorted(intrusos)}"
        )

    def test_pi_sigue_siendo_funtor_sobre_la_base_de_areas(self):
        """Cambiar de base no puede romper las leyes de funtor."""
        import sys
        sys.argv = ["x"]
        from scripts.train_gnn_ppo import build_skill_graph
        from nucleo.graph.functor import (
            construir_funtor, verificar_functorialidad)

        g = build_skill_graph()
        r = verificar_functorialidad(construir_funtor(g, base="area"), g)
        assert r["objetos_sin_imagen"] == 0
        assert r["F2_fallos"] == 0
        assert r["es_funtor"], f"pi no es funtor sobre la base de areas: {r}"

    def test_todo_agente_tiene_al_menos_una_habilidad(self, canonica):
        """
        Una categoria sin habilidades seria un agente sin nada que hacer, y
        ademas un objeto del codominio fuera de la imagen de pi.
        """
        from nucleo.pillars.math_domains import ALL_DOMAIN_SKILLS
        con_skills = {d.category for d in ALL_DOMAIN_SKILLS
                      if getattr(d, "category", None)}
        vacias = canonica - con_skills
        assert not vacias, f"categorias sin ninguna habilidad: {sorted(vacias)}"


class TestMapaDePilares:
    """
    PILLAR_FEEDS_CATEGORIES dice que categoria nutre cada pilar. No es una
    copia de la taxonomia sino una relacion sobre ella, pero sus valores tienen
    que ser categorias validas.
    """

    def test_todos_los_valores_son_categorias_validas(self, canonica):
        from nucleo.multi_agent.pillar_agents import PILLAR_FEEDS_CATEGORIES
        usadas = {c for cats in PILLAR_FEEDS_CATEGORIES.values() for c in cats}
        invalidas = usadas - canonica
        assert not invalidas, (
            f"PILLAR_FEEDS_CATEGORIES nombra categorias inexistentes: "
            f"{sorted(invalidas)}"
        )

    def test_documenta_que_categorias_no_nutre_ningun_pilar(self, canonica):
        """
        `geometry` y `optimization` no aparecen en ningun pilar. Puede ser
        deliberado, pero debe estar dicho: si manana se añade una categoria y
        nadie la conecta, este test lo hace visible en vez de dejarlo pasar.
        """
        from nucleo.multi_agent.pillar_agents import PILLAR_FEEDS_CATEGORIES
        nutridas = {c for cats in PILLAR_FEEDS_CATEGORIES.values() for c in cats}
        huerfanas = canonica - nutridas
        assert huerfanas == {"geometry", "optimization"}, (
            f"cambio el conjunto de categorias sin pilar: {sorted(huerfanas)}. "
            "Si es intencionado, actualiza este test; si no, conecta la nueva."
        )
