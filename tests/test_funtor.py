"""
Tests del funtor cociente pi: Skills -> Agentes.

Las tres categorias que el diseño describe son en realidad dos: los skills
L1-L3 y las teorias/subteorias son el MISMO grafo. La categoria distinta es la
de agentes, y con 172 objetos frente a 15 no puede haber isomorfismo. Lo que
si hay es una proyeccion, y estos tests fijan que sea un FUNTOR — que es lo
que hace falta para que la estructura de Ehresmann baje de un nivel al otro.

Las contrapartes formales estan en
MetamathProver/CategoryFoundations/QuotientFunctor.lean (0 sorry).
"""
import pytest

from nucleo.graph.category import SkillCategory
from nucleo.graph.functor import (
    OBJETO_BASE,
    construir_funtor,
    verificar_functorialidad,
    verificar_preservacion_colimites,
)
from nucleo.types import MorphismType, PillarType, Skill


def _skill(sid, categoria=None):
    md = {"category": categoria} if categoria else {}
    return Skill(id=sid, name=sid, description=sid,
                 pillar=PillarType.SET, level=1, metadata=md)


@pytest.fixture
def grafo():
    """Grafo minimo con dos categorias y un fundacional sin categoria."""
    g = SkillCategory()
    for sid, cat in [("anillos", "algebra"), ("cuerpos", "algebra"),
                     ("variedades", "geometry"), ("zfc", None)]:
        g.add_skill(_skill(sid, cat))
    g.add_morphism("anillos", "cuerpos", MorphismType.DEPENDENCY)
    g.add_morphism("cuerpos", "variedades", MorphismType.DEPENDENCY)
    g.add_morphism("zfc", "anillos", MorphismType.DEPENDENCY)
    return g


class TestConstruccion:

    def test_todo_skill_tiene_imagen(self, grafo):
        """pi debe ser TOTAL: si no, no es funtor y nada de lo demas aplica."""
        pi = construir_funtor(grafo)
        for s in grafo.skills:
            assert s.id in pi.en_objetos, f"{s.id} sin imagen"

    def test_los_sin_categoria_van_al_objeto_base(self, grafo):
        """Excluir los fundacionales dejaria pi parcial. Van a un objeto real."""
        pi = construir_funtor(grafo)
        assert pi("zfc") == OBJETO_BASE
        assert OBJETO_BASE in pi.codominio.objetos

    def test_los_intra_categoria_colapsan_a_identidad(self, grafo):
        """anillos -> cuerpos vive dentro de 'algebra': su imagen es id."""
        pi = construir_funtor(grafo)
        assert pi.colapsados >= 1
        assert ("algebra", "algebra") not in pi.codominio.morfismos

    def test_los_que_cruzan_inducen_morfismo(self, grafo):
        """Es justo lo que faltaba: los cruces ya tienen destino."""
        pi = construir_funtor(grafo)
        assert pi.codominio.hay_flecha("algebra", "geometry")
        assert pi.codominio.hay_flecha(OBJETO_BASE, "algebra")

    def test_translation_no_entra_en_el_orden(self, grafo):
        """
        TRANSLATION va de las ramas a `lean-tactics`, que no es una rama sino
        COMO se demuestra. Arrastrarla produce las mismas uniones espurias que
        ORDER_MORPHISMS existe para evitar.
        """
        grafo.add_morphism("variedades", "anillos", MorphismType.TRANSLATION)
        pi = construir_funtor(grafo, solo_jerarquia=True)
        assert not pi.codominio.hay_flecha("geometry", "algebra")


class TestLeyesDeFuntor:

    def test_es_funtor(self, grafo):
        r = verificar_functorialidad(construir_funtor(grafo), grafo)
        assert r["F1_identidades_ok"], "falla la ley de identidades"
        assert r["F2_composicion_ok"], "falla la ley de composicion"
        assert r["es_funtor"]

    def test_ningun_morfismo_se_queda_sin_imagen(self, grafo):
        r = verificar_functorialidad(construir_funtor(grafo), grafo)
        assert r["morfismos_con_imagen"] == r["morfismos_considerados"]

    def test_sobre_el_grafo_real(self):
        """La verificacion que importa: el grafo que el sistema usa de verdad."""
        import sys
        sys.argv = ["x"]
        from scripts.train_gnn_ppo import build_skill_graph
        g = build_skill_graph()
        r = verificar_functorialidad(construir_funtor(g), g)
        assert r["objetos_sin_imagen"] == 0
        assert r["F2_fallos"] == 0
        assert r["es_funtor"], f"pi no es funtor sobre el grafo real: {r}"


class TestPreservacion:
    """
    Un funtor preserva CO-CONOS siempre, y la MINIMALIDAD casi nunca. Son dos
    propiedades distintas y los tests las separan igual que el codigo, porque
    confundirlas es afirmar que un cociente conserva colimites.
    """

    def test_el_cocono_se_preserva(self, grafo):
        pi = construir_funtor(grafo)
        r = verificar_preservacion_colimites(
            pi, grafo, [(["anillos", "cuerpos"], "variedades")])
        assert r["cocono_preservado"] == 1

    def test_componentes_de_la_misma_categoria_colapsan(self, grafo):
        pi = construir_funtor(grafo)
        r = verificar_preservacion_colimites(
            pi, grafo, [(["anillos", "cuerpos"], "cuerpos")])
        assert r["colapsados_a_un_punto"] == 1

    def test_la_minimalidad_puede_perderse(self):
        """
        Contraparte del contraejemplo de Lean. Hacen falta DOS representantes
        de la misma categoria: uno abre en el codominio un atajo que en el
        dominio no existe, y con el se cuela una cota superior menor que la
        imagen del join.
        """
        g = SkillCategory()
        for sid, cat in [("a", "A"), ("a2", "A"), ("b", "B"),
                         ("j", "J"), ("m", "M")]:
            g.add_skill(_skill(sid, cat))
        g.add_morphism("a", "j", MorphismType.DEPENDENCY)
        g.add_morphism("b", "j", MorphismType.DEPENDENCY)
        g.add_morphism("a2", "m", MorphismType.DEPENDENCY)
        g.add_morphism("b", "m", MorphismType.DEPENDENCY)

        pi = construir_funtor(g)
        r = verificar_preservacion_colimites(pi, g, [(["a", "b"], "j")])
        assert r["cocono_preservado"] == 1, "el co-cono siempre sobrevive"
        assert r["colimite_preservado"] == 0, (
            "M es cota superior de {A,B} y J no la alcanza: la minimalidad "
            "se pierde, tal como demuestra functor_not_preserves_join"
        )


class TestLasClasesDeAristaNoSeMezclan:
    """El error de categoria que casi cambia una cifra publicada.

    Al arreglar el mapa de modulos —de 76 a 223 skills— las dependencias
    medibles contra el DAG de Mathlib pasaron de 73 a 282 y la tasa de
    confirmadas parecio caer del 78,1 % al 61,3 %. La conclusion facil era
    "el grafo estaba peor de lo que creiamos". Es FALSA, y el motivo es que
    las 209 aristas nuevas NO son de la misma clase que las 73 viejas:

        curada     237 aristas, todas skill -> skill    AFIRMA PRERREQUISITO
        jerarquia  221: area->mathlib, area->skill, skill->area
        cobertura  125, todas skill -> mathlib-*        AFIRMA COBERTURA

    Separadas por clase (scripts/funtor_dag_mathlib.py, seccion 6), la fila
    `curada` da 73 medibles / 57 confirmadas / 6 invertidas: los MISMOS
    numeros de antes. El 78,1 % nunca fue obsoleto; solo estaba escondido
    entre aristas de otra clase.

    Lo que si cambio es el NULO. El viejo se calculaba sobre todos los pares
    de skills medibles, una poblacion que ahora incluye nodos area-* y
    mathlib-*; el emparejado —fuentes de la clase x destinos de la clase— da
    40,1 %, y el factor baja de 2,4x a 1,95x. Sigue aportando, menos de lo
    que se publicaba.

    Estos tests fijan la composicion por clase. Si alguien anade aristas de
    una clase a otra, caen, y obligan a volver a correr el script en vez de
    dejar en pie una lectura que ya no vale.
    """

    @staticmethod
    def _clase(m):
        md = getattr(m, "metadata", None) or {}
        c = md.get("construccion") or "curada"
        return c if c in ("jerarquia", "cobertura") else "curada"

    @pytest.fixture(scope="class")
    def deps(self):
        from nucleo.core import Nucleo
        from nucleo.types import MorphismType as MT
        n = Nucleo.__new__(Nucleo)
        n._graph = SkillCategory()
        Nucleo._load_foundational_skills(n)
        return [m for m in n._graph.morphisms
                if m.morphism_type is MT.DEPENDENCY]

    def test_las_curadas_son_todas_entre_skills_de_verdad(self, deps):
        """Es la condicion que hace legitimo juzgarlas con el DAG de imports.

        Una arista `area-analysis -> banach-spaces` no afirma orden de
        imports sino pertenencia a la rama; medirla contra el DAG es un error
        de categoria. Si una arista curada empieza a tocar un nodo area-* o
        mathlib-*, la fila `curada` deja de ser comparable con el 78,1 %.
        """
        malas = [(m.source_id, m.target_id) for m in deps
                 if self._clase(m) == "curada"
                 and (m.source_id.startswith(("area-", "mathlib-"))
                      or m.target_id.startswith(("area-", "mathlib-")))]
        assert not malas, (
            "hay %d aristas curadas que tocan un nodo de etiqueta: %s. El "
            "DAG de imports no las puede juzgar y contaminan el 78,1 %%."
            % (len(malas), malas[:5]))

    def test_la_composicion_por_clase_no_ha_cambiado(self, deps):
        import collections
        c = collections.Counter(self._clase(m) for m in deps)
        assert dict(c) == {"curada": 238, "jerarquia": 221, "cobertura": 125}, (
            "la composicion por clase cambio a %s. Vuelve a correr "
            "scripts/funtor_dag_mathlib.py: las cifras por clase del README "
            "y de los tres artefactos pueden haber dejado de valer." % dict(c))

    def test_la_costura_de_cobertura_no_puede_servir_de_evidencia(self):
        """9 de 9 confirmadas suena perfecto, y no dice absolutamente nada.

        Su nulo emparejado es del 100 %: TODO par de esa forma sale
        confirmado, asi que confirmarlas no distingue un grafo bueno de uno
        cualquiera. Factor 1,00x. Este test existe para que nadie cite ese
        100 % como si fuera un logro del grafo.
        """
        import io
        import json
        import os
        p = "E:/Metamatematico/data/funtor_mathlib.json"
        if not os.path.exists(p):
            pytest.skip("falta la medicion; correr scripts/funtor_dag_mathlib.py")
        d = json.load(io.open(p, encoding="utf-8")).get("por_clase", {})
        if not d:
            pytest.skip("medicion anterior al desglose por clase")
        cob = d.get("cobertura")
        if cob:
            assert cob["nulo_pct"] > 95, (
                "el nulo de `cobertura` bajo a %.1f %%: ahora SI discrimina y "
                "habria que publicarla como evidencia." % cob["nulo_pct"])
        cur = d["curada"]
        assert cur["medibles"] == 73 and cur["confirmadas"] == 57, (
            "la fila curada cambio a %d/%d; el 78,1 %% del README ya no vale"
            % (cur["confirmadas"], cur["medibles"]))
        assert 1.5 < cur["factor"] < 2.4, (
            "el factor de las curadas es %.2fx, fuera del rango medido"
            % cur["factor"])


class TestElDotDeLakeVaAlReves:
    """La trampa que invirtio una medicion entera, y que hay que dejar fijada.

    `data/mathlib_imports.dot` lo produce `lake exe graph`, y escribe

        "A" -> "B"     queriendo decir     B IMPORTA A

    o sea la flecha va de la dependencia al dependiente: al REVES de como se
    lee un import. Medido: de sus 21 378 aristas, 19 894 son el reverso exacto
    de una arista del escaneo de los .lean, y NINGUNA coincide en el mismo
    sentido. Cero solapamiento.

    Leerlo al derecho da un resultado creible y falso, porque invertir un DAG
    no rompe nada visible: sigue siendo aciclico y sigue teniendo caminos,
    solo que los de vuelta. En una medicion de estas dependencias, leerlo al
    reves dio 31,5 % de aciertos donde el instrumento bueno da 61,3 %.

    Por eso `scripts/funtor_dag_mathlib.py` no lo usa: escanea los imports de
    los .lean directamente. Los dos scripts que si lo abren
    —`areas_por_estructura.py` y `conexion_curados_generados.py`— documentan
    la direccion en el propio punto de lectura, y el segundo test de aqui
    obliga a que siga siendo asi.
    """

    @pytest.fixture(scope="class")
    def dot(self):
        import io
        import os
        import re
        p = "E:/Metamatematico/data/mathlib_imports.dot"
        if not os.path.exists(p):
            pytest.skip("no esta el .dot; lo genera `lake exe graph`")
        pat = re.compile(r'"([^"]+)"\s*->\s*"([^"]+)"')
        ar = set()
        for l in io.open(p, encoding="utf-8", errors="replace"):
            m = pat.search(l)
            if m:
                ar.add((m.group(1), m.group(2)))
        return ar

    def test_el_agregador_Mathlib_es_sumidero_no_fuente(self, dot):
        """La comprobacion se hace DENTRO del .dot, sin umbrales inventados.

        `Mathlib.lean` es el fichero raiz que importa la biblioteca entera y
        al que no importa nadie. En la convencion de lake —dependencia ->
        dependiente— tiene que ser un SUMIDERO: entrada enorme, salida cero.
        Si algun dia sale al reves, la convencion cambio.
        """
        import collections
        sal = collections.Counter(a for a, _b in dot)
        ent = collections.Counter(b for _a, b in dot)
        assert ent["Mathlib"] > 1000, (
            "el agregador Mathlib recibe solo %d aristas; el .dot puede estar "
            "truncado o la convencion cambio." % ent["Mathlib"])
        assert sal["Mathlib"] == 0, (
            "el agregador Mathlib es FUENTE de %d aristas. Las flechas del "
            ".dot ya no van de la dependencia al dependiente: toda lectura "
            "que dependa de la direccion hay que revisarla." % sal["Mathlib"])

    def test_quien_abra_el_dot_documenta_la_direccion(self):
        """No se prohibe usarlo: se exige decir hacia donde apunta.

        Los dos que lo abren ya lo hacen —`# importado -> importador` en uno,
        `prerrequisito -> dependiente` en el otro—. Un tercero que lo abriera
        sin decirlo es justo el que se equivocaria.
        """
        import io
        import os
        senal = ("importado", "prerrequisite", "prerrequisito", "dependiente",
                 "al reves", "importador")
        mudos = []
        for base in ("nucleo", "scripts"):
            for r, _d, fs in os.walk(os.path.join("E:/Metamatematico", base)):
                if ".lake" in r or "__pycache__" in r:
                    continue
                for f in fs:
                    if not f.endswith(".py"):
                        continue
                    p = os.path.join(r, f)
                    t = io.open(p, encoding="utf-8", errors="replace").read()
                    if "mathlib_imports.dot" not in t:
                        continue
                    if not any(s in t for s in senal):
                        mudos.append(os.path.relpath(p, "E:/Metamatematico"))
        assert not mudos, (
            "%s abre(n) data/mathlib_imports.dot sin decir en ningun sitio "
            "hacia donde apuntan sus flechas. Van de lo IMPORTADO a lo que "
            "importa; leerlas al derecho invierte la medicion sin que se "
            "note. Documentalo en el punto de lectura." % mudos)
