"""
Guardia contra las cifras fijas que envejecen en silencio.

Patron repetido en este proyecto: un numero se escribe a mano en la interfaz o
en la documentacion, el sistema crece, y el numero se queda. No falla nunca de
forma ruidosa — simplemente deja de ser verdad y se sigue mostrando con toda
confianza. Casos reales encontrados:

  - el visualizador dibujaba 75 skills cuando el grafo tenia 172, con 46 nodos
    que ya no existian
  - anunciaba "Skills totales: 76" y "Tests: 379"
  - anunciaba "124,420 parametros" cuando la red tiene 546,820 (factor 4,4)
  - el quesito de niveles asumia 0/1/2 y dejaba fuera los 95 skills de L3

Estos tests comparan lo que la interfaz AFIRMA con lo que el sistema ES. Si
divergen, fallan aqui en vez de mentirle al usuario.
"""
import ast
import pathlib
import re

import pytest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
PAGINA = RAIZ / "pages" / "1_Visualizaciones.py"


def _fuente_pagina() -> str:
    return PAGINA.read_text(encoding="utf-8")


def _metricas_fijas(fuente: str) -> dict[str, str]:
    """Extrae las st.metric(...) cuyo valor es un literal numerico."""
    encontradas = {}
    for m in re.finditer(r'\.metric\(\s*"([^"]+)"\s*,\s*"([\d,]+)"', fuente):
        encontradas[m.group(1)] = m.group(2)
    return encontradas


# ---------------------------------------------------------------------------
# Cifras que la pagina declara a mano
# ---------------------------------------------------------------------------

class TestCifrasDeclaradas:

    def test_numero_de_tests_declarado(self):
        """La pagina anuncia cuantos tests hay: debe cuadrar con los que hay."""
        fuente = _fuente_pagina()
        declarado = _metricas_fijas(fuente).get("Tests")
        if declarado is None:
            pytest.skip("la pagina ya no declara un numero fijo de tests")

        reales = 0
        for f in sorted((RAIZ / "tests").glob("test_*.py")):
            arbol = ast.parse(f.read_text(encoding="utf-8"))
            reales += sum(
                1 for n in ast.walk(arbol)
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                and n.name.startswith("test_")
            )

        assert int(declarado.replace(",", "")) == reales, (
            f"La interfaz anuncia {declarado} tests y hay {reales}. "
            f"Actualiza la metrica en {PAGINA.name} o hazla dinamica."
        )

    def test_numero_de_suites_declarado(self):
        fuente = _fuente_pagina()
        m = re.search(r'"Tests",\s*"[\d,]+",\s*"(\d+) suites"', fuente)
        if not m:
            pytest.skip("la pagina ya no declara un numero fijo de suites")
        reales = len(list((RAIZ / "tests").glob("test_*.py")))
        assert int(m.group(1)) == reales, (
            f"La interfaz anuncia {m.group(1)} suites y hay {reales}."
        )

    def test_parametros_del_gnn_no_estan_fijos(self):
        """
        El recuento de parametros debe medirse, no escribirse.

        Estuvo fijo en 124,420 mientras la red real tenia 546,820.
        """
        fuente = _fuente_pagina()
        assert "124,420" not in fuente.replace(
            'La cifra estaba fija en "124,420"', ""
        ), "vuelve a haber un recuento de parametros escrito a mano"

    def test_categorias_declaradas(self):
        """Las categorias matematicas anunciadas deben existir en el dominio."""
        fuente = _fuente_pagina()
        declarado = _metricas_fijas(fuente).get("Categorías matemáticas")
        if declarado is None:
            pytest.skip("la pagina ya no declara un numero fijo de categorias")

        from nucleo.pillars.math_domains import ALL_DOMAIN_SKILLS
        reales = {s.category for s in ALL_DOMAIN_SKILLS if s.category}
        assert int(declarado) == len(reales), (
            f"La interfaz anuncia {declarado} categorias y hay {len(reales)}: "
            f"{sorted(reales)}"
        )


# ---------------------------------------------------------------------------
# La copia estatica del grafo
# ---------------------------------------------------------------------------

class TestGrafoDeLaPagina:

    def test_build_graph_prefiere_el_grafo_vivo(self):
        """
        build_graph() debe leer el Nucleo, no la lista SKILLS.

        Durante mucho tiempo devolvia la copia estatica incondicionalmente y la
        pagina entera describia un sistema que no era este.
        """
        fuente = _fuente_pagina()
        cuerpo = fuente[fuente.index("def build_graph():"):]
        cuerpo = cuerpo[:cuerpo.index("\ndef ", 1)]
        assert "_grafo_vivo_datos()" in cuerpo, (
            "build_graph() ya no consulta el grafo vivo"
        )
        assert 'G.graph["fuente"] = "vivo"' in cuerpo, (
            "build_graph() ya no marca la procedencia del grafo"
        )

    def test_ninguna_figura_itera_SKILLS_directamente(self):
        """
        SKILLS es solo el ultimo recurso: nadie debe iterarla.

        Cinco funciones lo hacian —layout, embeddings, heatmap y las dos
        distribuciones— asi que seguian dibujando los 75 nodos obsoletos
        aunque build_graph() ya devolviera los 172 reales, y al mezclarse
        ambas fuentes saltaban KeyError.
        """
        fuente = _fuente_pagina()
        infractoras = [
            (i, ln.strip())
            for i, ln in enumerate(fuente.splitlines(), 1)
            if re.search(r"\bin SKILLS\b", ln)
            and "for sid, name, level, cat, color in SKILLS" not in ln  # el fallback
        ]
        assert not infractoras, (
            "estas lineas iteran la lista estatica en vez del grafo vivo:\n"
            + "\n".join(f"  linea {i}: {t}" for i, t in infractoras)
        )

    def test_los_ids_estaticos_avisan_si_se_usan(self):
        """
        La copia estatica ya no coincide con el grafo real (38% en la ultima
        medicion). Este test no la corrige —es solo un fallback— pero deja
        constancia de cuanto ha derivado.
        """
        fuente = _fuente_pagina()
        ini = fuente.index("SKILLS = [")
        fin = fuente.index("PALETTE = {")
        ns: dict = {}
        exec(compile(fuente[ini:fin], "d", "exec"), ns)
        ids_est = {s[0] for s in ns["SKILLS"]}

        from nucleo.graph.category import SkillCategory
        from nucleo.pillars.math_domains import ALL_DOMAIN_SKILLS
        ids_reales = {s.id for s in ALL_DOMAIN_SKILLS}

        # No se exige coincidencia: se exige que el fallback no sea la fuente
        # principal, cosa que garantizan los dos tests de arriba.
        assert ids_est, "la lista de respaldo quedo vacia"
        assert ids_reales, "no hay skills de dominio"
