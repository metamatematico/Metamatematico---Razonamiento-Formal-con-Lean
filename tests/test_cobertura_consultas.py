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


# ═══════════════════════════════════════════════════════════════════════════
# EL BUCLE QUE NO CUESTA DINERO
#
# Cada pregunta importante sobre este sistema costaba API, y por eso la mas
# importante —¿el nucleo mejora la respuesta?— llevaba dias sin contestar. La
# grabacion rompe esa dependencia: el modelo formaliza UNA vez, se guarda, y
# todo lo que el sistema hace despues —imports, cascada, premisas— se puede
# reejecutar con Lean de juez y coste cero.
#
# Estas guardias protegen la frontera, que es lo unico delicado: lo que se
# graba tiene que ser el codigo del LLM ANTES de que el sistema lo toque. Si
# alguien mueve el gancho detras de la normalizacion, el replay medira el
# sistema contra si mismo y dara siempre lo mismo.
# ═══════════════════════════════════════════════════════════════════════════


def test_la_grabacion_esta_apagada_por_defecto():
    """No debe cambiar el comportamiento de quien no la pida."""
    import os
    from nucleo import grabacion
    grabacion._ACTIVA = None                      # olvidar lo que se decidio
    antes = os.environ.pop("METAMAT_GRABAR", None)
    try:
        assert grabacion.activa() is False
    finally:
        grabacion._ACTIVA = None
        if antes is not None:
            os.environ["METAMAT_GRABAR"] = antes


def test_grabar_nunca_lanza():
    """Grabar no puede tumbar una respuesta al usuario.

    Se le pasa algo que no serializa; debe tragarlo y seguir.
    """
    from nucleo import grabacion
    grabacion._ACTIVA = True
    try:
        grabacion.grabar(consulta="x", codigo="theorem t : True := trivial",
                         extra={"no_serializable": object()})
    finally:
        grabacion._ACTIVA = None


def test_el_gancho_graba_antes_de_que_lean_vea_el_codigo():
    """LA FRONTERA. Si se mueve, el replay deja de medir nada.

    El gancho tiene que estar ANTES de `check_code`: lo que se graba es lo que
    escribio el LLM, y todo lo que viene despues es del sistema y por tanto
    reejecutable. Grabar despues mediria el sistema contra su propia salida.
    """
    import re
    from nucleo.rutas import RAIZ
    src = (RAIZ / "nucleo" / "core.py").read_text(encoding="utf-8")
    i_grab = src.find("from nucleo.grabacion import grabar")
    assert i_grab > 0, "el gancho de grabacion desaparecio de core.py"
    # el primer check_code del pipeline principal, despues del gancho
    m = re.search(r"result = await self\._lean\.check_code\(lean_code\)",
                  src[i_grab:])
    assert m, "no se encontro la verificacion despues del gancho"


def test_el_replay_declara_sus_configuraciones():
    """Cada configuración dice qué apaga, y `completo` no apaga nada."""
    import importlib.util
    from nucleo.rutas import RAIZ
    spec = importlib.util.spec_from_file_location(
        "replay", RAIZ / "scripts" / "replay.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.CONFIGS["completo"] == {"imports": True, "premisas": True}
    assert mod.CONFIGS["desnudo"] == {"imports": False, "premisas": False}
    for nombre, cfg in mod.CONFIGS.items():
        assert set(cfg) == {"imports", "premisas"}, nombre


# ═══════════════════════════════════════════════════════════════════════════
# LOS DOS GRAFOS SON UNO, Y NO DEBEN VOLVER A SEPARARSE
#
# Medido antes del esqueleto de areas: CERO aristas entre los 173 curados y los
# 125 generados sin contar el enganche al pilar, y los 125 colgando directos de
# `zfc-axioms`. `mathlib-linearalgebra-basis` alcanzaba 81 nodos hacia arriba y
# ni uno era curado — no pasaba por `linear-algebra` ni por `ring-theory`, que
# existen. No habia un grafo de 298 nodos: habia dos que compartian el suelo.
# ═══════════════════════════════════════════════════════════════════════════


def test_los_dos_grafos_estan_cosidos(sistema):
    """Sin esto, el grafo generado y el curado son universos paralelos."""
    n, g = sistema
    gen = {s.id for s in g.skills
           if (s.metadata or {}).get("origen") == "mathlib"}
    L0 = {s.id for s in g.skills if s.level == 0}
    cruzan = 0
    for m in g.morphisms:
        a, b = m.source_id, m.target_id
        if a in L0:
            continue                      # la costura al pilar no cuenta
        if (a in gen) != (b in gen):
            cruzan += 1
    assert cruzan >= 50, (
        "solo %d aristas cruzan entre curados y generados. Antes del esqueleto "
        "de areas eran 0 y los dos grafos eran universos paralelos." % cruzan)


def test_casi_todo_generado_comparte_area_con_algun_curado(sistema):
    """Un nodo que sólo alcanza ZFC no hereda contexto de nada.

    OJO CON LO QUE ESTO AFIRMA, porque la primera versión de este test exigía
    algo que el diseño no da y fallaba con 125 de 125.

    Los generados NO son descendientes de los curados: son HERMANOS bajo un
    nodo de área. `mathlib-linearalgebra-basis` y `linear-algebra` cuelgan los
    dos de `area-algebra`, en paralelo. Y no se puede derivar cuál es más
    general, porque la profundidad del módulo no ordena la generalidad:
    `LinearAlgebra.Basis` está a profundidad 2 y `LinearAlgebra.Matrix.Defs` a
    3, y sin embargo el álgebra lineal es más general que la noción de base.

    Lo que sí se exige, en dos partes:

    1. que TODO generado tenga área. Sin excepciones — antes ni se pedía, y
       al retirar los imports agregados se vio que 37 no la tenían.
    2. que los que no alcanzan un área con miembros curados sean pocos, y por
       una razón nombrada: `computability`, `logic` y `ordertheory` no tienen
       NINGÚN nodo curado. Eso es un hueco de los 173 hechos a mano —no hay
       teoría del orden, ni lógica como dominio, ni computabilidad— y no un
       defecto de la conexión. Relajar el umbral para taparlo sería esconderlo.
    """
    from collections import deque
    n, g = sistema
    gen = {s.id for s in g.skills
           if (s.metadata or {}).get("origen") == "mathlib"}
    areas = {s.id for s in g.skills
             if (s.metadata or {}).get("category") == "area"}
    L0 = {s.id for s in g.skills if s.level == 0}
    curados = {s.id for s in g.skills
               if (s.metadata or {}).get("origen") is None} - L0
    assert areas, "no hay nodos de área: el esqueleto no se cargó"

    def cierre(sid):
        q, v = deque([sid]), set()
        while q:
            u = q.popleft()
            for d in g.dependencies(u):
                if d not in v:
                    v.add(d)
                    q.append(d)
        return v

    #: las áreas que además son ancestro de algún curado — las que cosen
    utiles = {a for a in areas if any(a in cierre(c) for c in curados)}
    assert utiles, "ningún área es ancestro de un curado: no cose nada"

    #: 1 · todos tienen área. Es lo que el esqueleto sí garantiza.
    todas = {a for a in areas}
    sin_area = [s for s in gen if not (cierre(s) & todas)]
    assert not sin_area, (
        "%d nodos generados no alcanzan ningún área: %s. "
        "Revisar `_AREA_DE_DATA` y `_RENOMBRA_AREA` en math_domains.py"
        % (len(sin_area), sorted(sin_area)[:8]))

    #: 2 · los que no llegan a un área CON CURADOS, y por qué
    huerfanos = [s for s in gen if not (cierre(s) & utiles)]
    vacias = sorted(a.replace("area-", "") for a in areas - utiles)
    assert len(huerfanos) <= 20, (
        "%d nodos generados no comparten área con ningún curado. Las áreas sin "
        "curados son %s: si la lista creció, el grafo hecho a mano tiene un "
        "hueco nuevo." % (len(huerfanos), vacias))


def test_la_logica_es_prerrequisito_de_zfc(sistema):
    """ZFC es una teoría de primer orden — el ejemplo canónico.

    Sin esta arista la lógica alcanzaba 158 de 315 nodos: media matemática del
    grafo sin la lógica detrás. Con ella, 284 sólo por dependencia.
    """
    from collections import deque
    from nucleo.types import MorphismType
    n, g = sistema
    assert g.has_morphism("fol-deduction", "zfc-axioms"), (
        "falta `fol-deduction -> zfc-axioms`: ZFC es una teoria de primer "
        "orden y sin esa arista la logica no sostiene la matematica del grafo")

    ady = {}
    for m in g.morphisms:
        if m.morphism_type == MorphismType.DEPENDENCY:
            ady.setdefault(m.source_id, set()).add(m.target_id)
    q, v = deque(["fol-deduction"]), set()
    while q:
        u = q.popleft()
        for x in ady.get(u, ()):
            if x not in v:
                v.add(x)
                q.append(x)
    assert len(v) >= 250, (
        "la logica solo alcanza %d nodos por dependencia; eran 284 cuando se "
        "puso la arista a ZFC" % len(v))


def test_una_palabra_generica_no_activa_una_skill():
    """UNA PALABRA GENERICA NO ES EVIDENCIA POR SI SOLA.

    Ante «demuestra el teorema de punto fijo» el emparejador activaba
    `prime-number-theorem`, `residue-theorem` y `compactness-theorem` —los tres
    por la palabra «theorem»— y `point-set-topology` por «point». Ninguno tiene
    que ver con puntos fijos.

    Es la misma familia que el fallo de `the` del §12.1: contar una
    coincidencia en una palabra que sale en media biblioteca y presentarla como
    señal.

    MEDIDO con `scripts/medir_emparejamiento.py` sobre las mismas 3000
    consultas etiquetadas: la primera skill acierta el area el 52,1 % frente al
    47,3 % de antes, sin ofrecer menos (8,40 -> 8,31 skills por consulta).
    """
    from nucleo.core import Nucleo
    from nucleo.graph.category import SkillCategory
    n = Nucleo.__new__(Nucleo)
    n._graph = SkillCategory()
    Nucleo._load_foundational_skills(n)

    sk = Nucleo._match_skills_to_query(n, "prove the fixed point theorem", n._graph)
    for espurio in ("prime-number-theorem", "residue-theorem",
                    "compactness-theorem", "point-set-topology"):
        assert espurio not in sk, (
            "«%s» casa por una palabra generica, no por el tema" % espurio)


def test_pero_la_frase_entera_sigue_casando():
    """Las genericas no se eliminan del texto: sólo se les niega el poder de
    abrir la puerta ELLAS SOLAS. «prime number theorem» tiene que seguir
    encontrando su skill."""
    from nucleo.core import Nucleo
    from nucleo.graph.category import SkillCategory
    n = Nucleo.__new__(Nucleo)
    n._graph = SkillCategory()
    Nucleo._load_foundational_skills(n)
    sk = Nucleo._match_skills_to_query(n, "prove the prime number theorem", n._graph)
    assert "prime-number-theorem" in sk
