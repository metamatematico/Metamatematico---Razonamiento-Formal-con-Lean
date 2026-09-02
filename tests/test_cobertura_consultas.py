# -*- coding: utf-8 -*-
"""El grafo tiene que ENGANCHAR con las consultas reales, y eso nadie lo medía.

Medido cuando se busco: de las 24 consultas del banco, **15 no activaban
ninguna skill**. `(a+b)^2 = a^2+2ab+b^2`, `P -> (Q -> P)`, `n^2 par <-> n par`:
nada. Y los 10 nodos fundacionales no se activaban NUNCA, en ninguna.

Eso significa que los dos unicos puntos donde el grafo actua en caliente —los
nombres de Mathlib que van al prompt, y los modulos que importa Lean— no
ocurrian en mas de la mitad de las consultas. El sistema respondia igual, y por
eso nadie lo noto: los 771 tests de entonces comprobaban que el grafo es
CORRECTO, no que se USE.

Estas guardias miden el enganche y fijan el listado de lo que hoy falla, para
que se vea cuando mejore y para que no empeore sin avisar.
"""
import pytest


@pytest.fixture(scope="module")
def sistema():
    from nucleo.core import Nucleo
    from nucleo.graph.category import SkillCategory
    n = Nucleo.__new__(Nucleo)
    n._graph = SkillCategory()
    Nucleo._load_foundational_skills(n)
    return n, n._graph


@pytest.fixture(scope="module")
def consultas():
    from scripts.banco_fidelidad import CASOS
    return [c["pregunta"] if isinstance(c, dict) else c[1] for c in CASOS]


def _activa(n, g, q):
    from nucleo.core import Nucleo
    return Nucleo._match_skills_to_query(n, q, g)


#: Cuantas consultas del banco DEBEN activar alguna skill. Es el numero de hoy,
#: no un objetivo: sirve de trinquete. Si alguien mejora el emparejador, se
#: sube; si algo lo rompe, este test lo caza.
MINIMO_CON_SKILL = 9


def test_el_grafo_engancha_con_las_consultas_reales(sistema, consultas):
    n, g = sistema
    con = [q for q in consultas if _activa(n, g, q)]
    assert len(con) >= MINIMO_CON_SKILL, (
        "el emparejador engancha con %d de %d consultas y antes eran %d: "
        "algo lo ha empeorado" % (len(con), len(consultas), MINIMO_CON_SKILL))


def test_el_mapa_de_modulos_esta_donde_se_espera():
    """Si falta, el grafo deja de elegir que importa Lean.

    Era una ruta absoluta a E:/Metamatematico dentro de un `except` mudo que
    dejaba el cache en `{}` y no reintentaba nunca. El proyecto ya se movio una
    vez de sitio.
    """
    import json
    from nucleo.rutas import dato
    ruta = dato("mathlib_modulos.json")
    assert ruta.exists(), (
        "falta %s — el grafo no podra elegir modulos. Regenerar con "
        "python -m scripts.mapa_modulos_mathlib" % ruta)
    d = json.loads(ruta.read_text(encoding="utf-8"))
    assert d.get("por_skill"), "el mapa de modulos esta vacio"


def test_no_quedan_rutas_absolutas_en_el_runtime():
    """Una ruta absoluta en `nucleo/` es un fallo silencioso esperando a que
    alguien mueva el proyecto. Los scripts pueden tenerlas; el runtime no."""
    import os
    import re
    from nucleo.rutas import RAIZ

    #: Exenciones, con su motivo. Explícitas y no por heurística: una lista
    #: dice qué se perdona y por qué; una heurística perdona lo que no debe y
    #: nadie se entera.
    EXENTOS = {
        # documenta en su docstring las rutas absolutas que se eliminaron
        "rutas.py",
        # `_find_arial` PRUEBA varias rutas de sistema con os.path.exists y
        # devuelve None si ninguna está. Eso no es un fallo silencioso: es la
        # forma correcta de buscar una fuente en tres sistemas distintos.
        "pdf_export.py",
    }
    patron = re.compile(r"[\"'][A-Za-z]:[/\\]")
    malos = []
    for raiz, _d, fs in os.walk(RAIZ / "nucleo"):
        for f in fs:
            if not f.endswith(".py") or f in EXENTOS:
                continue
            ruta = os.path.join(raiz, f)
            try:
                txt = open(ruta, encoding="utf-8").read()
            except Exception:
                continue
            for i, l in enumerate(txt.splitlines(), 1):
                if l.strip().startswith("#"):
                    continue          # los comentarios pueden citarlas
                if patron.search(l):
                    malos.append("%s:%d" % (os.path.relpath(ruta, RAIZ), i))
    assert not malos, "rutas absolutas en el runtime: %s" % ", ".join(malos)


def test_los_modulos_que_salen_son_de_las_skills_activadas(sistema, consultas):
    """El paso 3 del flujo: de skills a modulos de Mathlib.

    Comprueba que cuando SI hay skills, la cadena entera llega hasta los
    modulos — que es lo que se rompia en silencio con la ruta absoluta.
    """
    from nucleo.core import Nucleo
    n, g = sistema
    llegaron = 0
    for q in consultas:
        skills = _activa(n, g, q)
        if not skills:
            continue
        mods = Nucleo._modulos_mathlib(n, {"relevant_skills": skills})
        if mods:
            llegaron += 1
            assert all(m.startswith("Mathlib.") for m in mods), mods
    assert llegaron > 0, (
        "ninguna consulta llego a producir modulos: la cadena "
        "skills -> modulos esta rota")
