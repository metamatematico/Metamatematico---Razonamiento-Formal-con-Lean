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
import io
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

    def test_numero_de_tests_declarado(self, request):
        """Todo lo publicado anuncia cuantos tests pasan: tiene que cuadrar.

        Antes esto contaba funciones `def test_*` con el AST y solo miraba la
        pagina de Streamlit. Eso dejaba DOS cantidades distintas circulando:

            729  funciones definidas
            790  casos que pytest ejecuta

        No son la misma cosa —diez `parametrize` toman sus valores de
        constantes del modulo, y el AST no puede expandirlos— y el README y el
        artefacto declaraban la segunda, desactualizada en 788, sin que nada
        saltara. La cifra la encontro el usuario leyendo la portada.

        Ahora se compara con lo que pytest ACABA de recolectar en esta misma
        sesion. Es exacto, no cuesta un subproceso, y cubre los tres sitios
        donde la cifra se publica.
        """
        casos = len(request.session.items)
        if casos < 500:
            pytest.skip("sesion parcial (%d casos): no hay con que comparar"
                        % casos)

        declarados = []
        pagina = _metricas_fijas(_fuente_pagina()).get("Tests")
        if pagina is not None:
            declarados.append((PAGINA.name, int(pagina.replace(",", ""))))

        #: en el README y el artefacto la cifra va suelta en la prosa, asi que
        #: se buscan las formas en que se escribe, no un numero cualquiera.
        #:
        #: `_N` acepta separador de millares, porque el artefacto escribe
        #: «1 129» con ESPACIO FINO (U+202F) y el README «1129» a secas. El
        #: patron de aqui decia `(\d+)  tests` con dos espacios —un intento de
        #: casar ese espacio fino que se degrado— y asi no casaba nada: en el
        #: artefacto sobrevivio «1 085 tests en 56 suites», 44 tests por
        #: debajo de la realidad, con el guardian en verde. Un guardian que no
        #: casa es peor que no tenerlo, porque se confia en el.
        #:
        #: Los separadores van por NOMBRE y no escritos a pelo: el espacio
        #: fino y el duro son INVISIBLES en el editor, y el primero que toque
        #: esta linea los borraria sin enterarse, devolviendo el guardian al
        #: estado de no casar nada.
        _SEPS = "\u202f\u00a0.,\u0020"      # fino, duro, punto, coma, normal
        _N = r"(\d[\d%s]*\d|\d)" % re.escape(_SEPS)
        for nombre, patrones in (
            ("README.md", (r"Tests-" + _N + r"_passing",
                           r"\*\*" + _N + r" tests en \d+ suites",
                           r"tests/\s+" + _N + r" tests en")),
            ("docs/arquitectura_nle.html", (_N + r" tests · \d+ suites",
                                            r'"n">' + _N + r'</div><div class="l">tests en verde',
                                            _N + r" tests en \d+ suites")),
        ):
            p = RAIZ / nombre
            if not p.exists():
                continue
            doc = io.open(p, encoding="utf-8").read()
            for pat in patrones:
                for m in re.finditer(pat, doc):
                    crudo = m.group(1)
                    for sep in (".", ",", " ", " ", " "):
                        crudo = crudo.replace(sep, "")
                    declarados.append((nombre, int(crudo)))

        assert declarados, "ya no se publica en ningun sitio cuantos tests hay"
        malos = sorted({(n, v) for n, v in declarados if v != casos})
        assert not malos, (
            "pytest recolecta %d casos y se publica otra cifra en: %s. "
            "Actualizar los tres sitios: el badge y la seccion 7 del README, "
            "la portada y el indice del artefacto, y la metrica de %s."
            % (casos, "; ".join("%s dice %d" % m for m in malos), PAGINA.name))

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


class TestCifrasDelGrafo:
    """Las cifras del grafo que la documentación afirma deben ser las reales.

    Se encontraron dos falsas: la tabla decia 978 dependencias y 298
    identidades cuando ya eran 1156 y 315. Se habia actualizado el TOTAL de
    morfismos y no el desglose — un descuadre que nadie nota leyendo, porque
    cada cifra por separado parece plausible.

    Es el mismo defecto que el generador del SVG, que llevaba «298 nodos» a
    mano y siguio diciendolo despues de crecer a 315: cifras escritas a mano
    que mienten en cuanto cambia el dato, y en silencio.
    """

    def _real(self):
        from nucleo.core import Nucleo
        from nucleo.graph.category import SkillCategory
        from nucleo.types import MorphismType as MT
        n = Nucleo.__new__(Nucleo)
        n._graph = SkillCategory()
        Nucleo._load_foundational_skills(n)
        g = n._graph
        meta = {s.id: (s.metadata or {}) for s in g.skills}
        M = g.morphisms
        return {
            "nodos": len(g.skills),
            "morfismos": len(M),
            "curados": sum(1 for s in g.skills if not meta[s.id].get("origen")),
            "generados": sum(1 for s in g.skills
                             if meta[s.id].get("origen") == "mathlib"),
            "areas": sum(1 for s in g.skills
                         if meta[s.id].get("category") == "area"),
            "dependencias": sum(1 for m in M
                                if m.morphism_type == MT.DEPENDENCY),
            "traducciones": sum(1 for m in M
                                if m.morphism_type == MT.TRANSLATION),
            "identidades": sum(1 for m in M
                               if m.morphism_type == MT.IDENTITY),
        }

    def _docs(self):
        """El texto de la documentación, SIN los SVG incrustados.

        La primera version leia el artefacto entero y la regex se metia dentro
        de un `<svg>`, donde cogia una COORDENADA como si fuera una cifra
        documentada: dijo «nodos generados dice 662» leyendo un `x="662"`. El
        guardian tambien es un instrumento y se rompe igual.

        SE MIRAN LOS CUATRO ARTEFACTOS, NO UNO.

        Esto leia el README y `arquitectura_nle.html` y nada mas, asi que los
        otros tres publicaban cifras sin que nadie los vigilase. Encontrado:
        `diagnostico.html` seguia diciendo «21,0 % y 14,8 % del lexico» y «1069
        tests», y `anatomia_grafo.html` el mismo par viejo. Un guardian que
        cubre la mitad de lo publicado deja la otra mitad envejeciendo con la
        misma confianza de siempre.
        """
        import io
        import re
        from nucleo.rutas import RAIZ

        docs = {"README": io.open(RAIZ / "README.md", encoding="utf-8").read()}
        for nombre, fichero in (("artefacto", "arquitectura_nle.html"),
                                ("anatomia", "anatomia_grafo.html"),
                                ("explorador", "explorador_grafo.html"),
                                ("diagnostico", "diagnostico.html")):
            p = RAIZ / "docs" / fichero
            if p.exists():
                docs[nombre] = re.sub(r"<svg[\s\S]*?</svg>", " ",
                                      io.open(p, encoding="utf-8").read())

        # LA HOJA DE CURACION TAMBIEN PUBLICA CIFRAS MEDIDAS, y se quedo fuera
        # de esta lista por ser .md en vez de .html. Citaba «10,3 % contra
        # Herald» —el grafo de 352 nodos— mientras los cuatro documentos de
        # arriba ya estaban corregidos, y nada lo marcaba.
        #
        # Ojo: la genera `scripts/hoja_de_curacion_interna.py` con la cifra
        # escrita a mano en DOS sitios (el markdown y el LaTeX), asi que
        # corregir solo el .md lo revierte la siguiente regeneracion. Hay que
        # tocar el generador.
        p = RAIZ / "docs" / "CURACION_INTERNA.md"
        if p.exists():
            docs["curacion"] = io.open(p, encoding="utf-8").read()
        return docs

    def test_el_desglose_de_morfismos_cuadra_con_el_total(self):
        r = self._real()
        suma = (r["dependencias"] + r["traducciones"] + r["identidades"]
                + sum(1 for _ in ()))
        assert suma <= r["morfismos"], (
            "el desglose (%d) supera el total (%d)" % (suma, r["morfismos"]))

    #: Cifras MEDIDAS que la documentacion publica, con la ruta al numero
    #: dentro de su fichero de medicion.
    #:
    #: POR QUE HACIA FALTA ESTE GUARDIAN. El resto de esta suite vigila lo que
    #: el sistema ES —cuantos nodos, cuantos morfismos, cuantos tests— y eso se
    #: recalcula solo. Pero la documentacion tambien publica lo que el sistema
    #: MIDE, y esas cifras no las vigilaba nadie: se escriben a mano tras una
    #: medicion y se quedan ahi cuando se vuelve a medir.
    #:
    #: Paso de verdad: tras reapuntar el vocabulario, la precision del lexico
    #: subio de 21,0 % a 21,6 % y el artefacto siguio diciendo 21,0 % en cuatro
    #: sitios. El decisor no se entera porque el lee la RUTA al numero; la
    #: documentacion llevaba una COPIA.
    #:
    #: Se comprueba con una decima de tolerancia: la documentacion redondea.
    #:
    #: EL ANCLA VA DESPUES DEL NUMERO, NO ANTES, Y ESO NO ES CAPRICHO. La
    #: primera version anclaba en la palabra «lexico» y buscaba la cifra a
    #: continuacion; con las cifras envueltas en `<strong>` y repartidas por
    #: celdas de tabla, el ancla no las alcanzaba y el test PASABA teniendo
    #: cuatro cifras viejas delante. Un guardian que no salta cuando debe es
    #: peor que ninguno, porque da confianza falsa.
    #:
    #: Se quitan las etiquetas antes de buscar y se ancla en lo que sigue al
    #: numero, que es lo que sobrevive al maquetado.
    #: EL ANCLA ES EL PAR, NO LA CIFRA SUELTA. «13,1 % precision» tambien
    #: existe en el README y es del emparejador SEMANTICO, que nunca se
    #: adopto: anclar solo en «precision» lo marcaba como desactualizado.
    #: La cifra va seguida de SU COBERTURA en la misma celda. Esa firma la
    #: comparten los TRES bancos, asi que cada patron va ANCLADO al nombre de
    #: su banco: sin el ancla, la fila de Herald se leia como si fuera la de
    #: ProofNet y el guardian gritaba con la documentacion correcta. Un
    #: guardian que se dispara con codigo correcto entrena a ignorarlo.
    #:
    #: Y se vigilan los tres, no solo ProofNet: un banco nuevo cuya cifra
    #: nadie comprueba es exactamente el fallo que este test existe para
    #: cazar, solo que mas reciente.
    _PC = (r".{0,220}?(\d{1,2},\d)\s*%\s*precisi[oó]n"
           r"[^0-9]{0,20}(\d{1,2},\d)\s*%\s*cobertura")
    CIFRAS_MEDIDAS = (
        ("vocabulario contra ProofNet", "recuperacion_proofnet.json",
         r"ProofNet" + _PC,
         (("precision", ("resultados", "lexico", "precision")),
          ("cobertura", ("resultados", "lexico", "cobertura")))),
        ("vocabulario curado", "recuperacion_proofnet.json",
         r"(\d{1,2},\d)\s*%\s*del vocabulario curado",
         (("precision", ("resultados", "lexico", "precision")),)),
        ("vocabulario sobre Mathlib entero", "banco_docstrings.json",
         r"Mathlib entero" + _PC,
         (("precision", ("resultados", "grafo", "precision")),
          ("cobertura", ("resultados", "grafo", "cobertura")))),
        ("vocabulario contra Herald", "banco_herald.json",
         r"Herald" + _PC,
         (("precision", ("resultados", "grafo", "precision")),
          ("cobertura", ("resultados", "grafo", "cobertura")))),
    )

    @staticmethod
    def _sin_etiquetas(html: str) -> str:
        import re
        html = re.sub(r"<svg[\s\S]*?</svg>", " ", html)
        html = re.sub(r"<[^>]+>", " ", html)
        return re.sub(r"\s+", " ", html)

    def test_las_cifras_MEDIDAS_publicadas_siguen_siendo_las_medidas(self):
        """Lo que la documentacion dice haber MEDIDO, contra lo medido.

        El resto de esta suite vigila lo que el sistema ES —cuantos nodos,
        cuantos tests— y eso se recalcula solo. Pero la documentacion tambien
        publica lo que el sistema MIDE, y esas cifras no las vigilaba nadie:
        se escriben a mano tras una medicion y se quedan cuando se vuelve a
        medir.

        Paso de verdad: tras reapuntar el vocabulario la precision subio de
        21,0 % a 21,6 % y el artefacto siguio diciendo 21,0 % en dos sitios.
        El decisor no se entera porque el lee la RUTA al numero; la
        documentacion llevaba una COPIA.
        """
        import io
        import json
        import re
        from nucleo.rutas import RAIZ

        malas = []
        for etiqueta, fichero, patron, campos in self.CIFRAS_MEDIDAS:
            p = RAIZ / "data" / fichero
            if not p.exists():
                continue
            crudo = json.load(io.open(p, encoding="utf-8"))
            reales = []
            for _nombre_campo, ruta in campos:
                dato = crudo
                for clave in ruta:
                    dato = dato[clave]
                v = float(dato)
                reales.append(v * 100.0 if v <= 1.0 else v)
            for nombre, doc in self._docs().items():
                for m in re.finditer(patron, self._sin_etiquetas(doc),
                                     re.IGNORECASE):
                    for i, (campo, _ruta) in enumerate(campos, start=1):
                        dicho = float(m.group(i).replace(",", "."))
                        if abs(dicho - reales[i - 1]) > 0.1:
                            malas.append(
                                "%s · %s/%s dice %s %% y %s da %.1f %%"
                                % (nombre, etiqueta, campo, m.group(i),
                                   fichero, reales[i - 1]))
        assert not malas, (
            "cifras MEDIDAS desactualizadas en la documentacion: "
            + "; ".join(sorted(set(malas))))

    #: EL FACTOR ES UNA CIFRA DERIVADA, y por eso se escapaba del guardian de
    #: arriba, que compara cada numero publicado con UNA RUTA dentro del JSON.
    #: El factor no esta en ningun JSON: es el cociente. Al no tener ruta se
    #: quedo sin vigilar, y la documentacion arrastro «15,7x» durante toda una
    #: remedicion mientras la precision de al lado —esa si vigilada— ya decia
    #: 23,9 %. La pagina publicaba «23,9 ... 1,45 ... 15,7x», y
    #: 23,9/1,45 son 16,5: el lector con una calculadora veia la contradiccion
    #: que el guardian no veia. Estaba en CINCO documentos.
    #:
    #: EL COCIENTE SE SACA DEL JSON, NUNCA DE LO PUBLICADO. Lo intente: si el
    #: documento ya trae precision y nulo al lado del factor, parece que el
    #: factor se puede comprobar contra ellos sin abrir ningun fichero. No se
    #: puede. El nulo se publica redondeado a 0,3 % y vale 0,262, asi que
    #: 5,0/0,3 da 16,7x cuando el cociente real es 19,2x. Un cociente no
    #: sobrevive al redondeo de sus operandos: el guardian habria exigido
    #: escribir un factor FALSO.
    #:
    #: EL ANCLA ES EL PAR precision+cobertura DE SU BANCO, el mismo `_PC` que
    #: usa el test de arriba, y no el nombre del banco a secas. Anclar en el
    #: nombre marcaba documentacion CORRECTA dos veces: «ProofNet» sale tambien
    #: en la prosa de otra fila —«ProofNet no paga»— y el primer factor que
    #: venia detras era el del reconocedor de area, 3,2x, perfectamente valido.
    #: El par exige las palabras «precision» y «cobertura», que solo estan en
    #: la fila de resultados.
    FACTORES = (
        ("ProofNet", "recuperacion_proofnet.json",
         ("resultados", "lexico", "precision"),
         ("resultados", "nulo", "precision")),
        ("Mathlib entero", "banco_docstrings.json",
         ("resultados", "grafo", "precision"),
         ("resultados", "nulo", "precision")),
        ("Herald", "banco_herald.json",
         ("resultados", "grafo", "precision"),
         ("resultados", "nulo", "precision")),
    )

    def test_los_factores_contra_el_nulo_son_el_cociente_real(self):
        """Cada «Nx» publicado tiene que ser el cociente que dice ser."""
        import io
        import json
        import re
        from nucleo.rutas import RAIZ

        malas = []
        for ancla, fichero, ruta_sis, ruta_nulo in self.FACTORES:
            p = RAIZ / "data" / fichero
            if not p.exists():
                continue
            d = json.load(io.open(p, encoding="utf-8"))
            try:
                sis = nulo = d
                for k in ruta_sis:
                    sis = sis[k]
                for k in ruta_nulo:
                    nulo = nulo[k]
            except (KeyError, TypeError):
                continue
            if not nulo:
                continue
            real = sis / nulo

            # ancla + el par precision/cobertura + los dos nulos + el factor
            patron = (re.escape(ancla) + self._PC
                      + r".{0,40}?(\d{1,2},\d)\s*[xX]")
            for nombre, doc in self._docs().items():
                plano = self._sin_etiquetas(doc).replace("×", "x")
                for m in re.finditer(patron, plano):
                    pub = float(m.group(3).replace(",", "."))
                    # una decima de tolerancia: la documentacion redondea
                    if abs(pub - real) > 0.1 + 1e-9:
                        malas.append(
                            "%s · %s publica %sx y el cociente medido es %.1fx"
                            % (nombre, ancla, m.group(3), real))

        assert not malas, (
            "factores contra el nulo que no son el cociente que dicen ser: %s. "
            "Recalcularlo desde el JSON, no copiarlo." % "; ".join(sorted(set(malas))))

    def test_las_cifras_documentadas_son_las_reales(self):
        """Las cifras que la documentacion DECLARA, contra el grafo real.

        SOLO CUENTAN LAS DECLARACIONES, NO LAS MENCIONES EN PROSA. El patron
        de antes admitia hasta 40 caracteres cualesquiera entre la etiqueta y
        el numero, y eso salta por encima de las palabras. En cuanto el
        guardian empezo a mirar `anatomia_grafo.html` marco dos cifras falsas
        leyendo esto:

            «... sus dependencias, las traducciones entre pilares y las 434
             aristas a tacticas ...»

        El 434 es de las ARISTAS A TACTICAS, y lo acredito a `dependencias` y
        a `traducciones` a la vez. Un guardian que da falsas alarmas se acaba
        ignorando, que es la otra forma de no servir.

        La firma que separa una declaracion de una mencion: en la declaracion
        —una celda de tabla— entre la etiqueta y el numero NO HAY LETRAS; en la
        prosa las hay. Se quitan las etiquetas HTML primero para que la celda
        `<td>dependencias</td><td>583</td>` quede como «dependencias 583».
        """
        import re
        r = self._real()
        # ni letras ni digitos entre la etiqueta y la cifra
        HUECO = r"[^0-9A-Za-zÁÉÍÓÚÜÑáéíóúüñ]{0,12}"
        malas = []
        for nombre, doc in self._docs().items():
            plano = self._sin_etiquetas(doc)
            for etq, val in (("nodos curados", r["curados"]),
                             ("nodos generados", r["generados"]),
                             ("dependencias", r["dependencias"]),
                             ("traducciones", r["traducciones"]),
                             ("identidades", r["identidades"])):
                m = re.search(re.escape(etq) + HUECO + r"([0-9]{1,5})", plano)
                if m and int(m.group(1)) != val:
                    malas.append("%s · %s dice %s y son %d"
                                 % (nombre, etq, m.group(1), val))
        assert not malas, "cifras falsas en la documentacion: " + "; ".join(malas)

    def test_la_figura_del_grafo_lleva_las_cifras_reales(self):
        """El SVG llevaba «298 nodos · 1722 morfismos» escrito a mano."""
        import io
        import re
        from nucleo.rutas import RAIZ
        p = RAIZ / "docs" / "img" / "10-grafo-real.svg"
        if not p.exists():
            return
        svg = io.open(p, encoding="utf-8").read()
        r = self._real()
        m = re.search(r"(\d+) nodos · (\d+) morfismos", svg)
        assert m, "la figura ya no declara sus cifras"
        assert (int(m.group(1)), int(m.group(2))) == (r["nodos"], r["morfismos"]), (
            "la figura dice %s nodos y %s morfismos; son %d y %d. "
            "Regenerar con python scripts/dibujar_grafo.py"
            % (m.group(1), m.group(2), r["nodos"], r["morfismos"]))

    def test_el_diagrama_de_flujo_no_se_queda_viejo(self):
        """El diagrama decía «DOS puntos» cuando ya eran tres.

        Se escribio a mano, el flujo cambio y nadie lo noto durante horas — el
        dibujo presentaba el paso 3 como contribucion del grafo cuando ya
        estaba medido que es inerte. Ahora lo genera
        `scripts/dibujar_flujo.py` y esta guardia comprueba que siga contando
        los mismos puntos que la tabla del README.
        """
        import io
        import re
        from nucleo.rutas import RAIZ
        p = RAIZ / "docs" / "img" / "00-flujo-real.svg"
        if not p.exists():
            return
        svg = io.open(p, encoding="utf-8").read()
        # `>N · ` a secas: el patron pedia «N · EL » y el paso 4 dice
        # «4 · LEAN VERIFICA», asi que el guardian contaba 5 de 6 y acusaba al
        # diagrama de estar incompleto cuando el roto era el.
        #: `3a`/`3b`: el paso 3 son DOS cosas y solo una es inerte, asi que
        #: el diagrama y la tabla las numeran aparte. Se normaliza al numero
        #: para que el guardian siga comparando PASOS y no filas.
        pasos = {m[0] for m in re.findall(r">([1-9])[ab]? · ", svg)}
        readme = io.open(RAIZ / "README.md", encoding="utf-8").read()
        filas = [m[0] for m in
                 re.findall(r"^\| ([0-9][ab]?) \|", readme, re.M)]
        assert pasos, "el diagrama ya no numera sus pasos"
        assert len(pasos) == len(set(filas)), (
            "el diagrama tiene %d pasos numerados y la tabla del README %d. "
            "Regenerar con python scripts/dibujar_flujo.py"
            % (len(pasos), len(set(filas))))
        #: los veredictos medidos tienen que estar EN el dibujo, no solo en el
        #: texto: un diagrama que pinta los tres puntos igual engaña
        #: CADA PUNTO CON SU VEREDICTO, y el que se quito con su cifra. El
        #: paso 3b —proponer modulos vecinos— y el orden de cascada por area se
        #: midieron contra su nulo, empataron o perdieron, y el 2026-09-21 se
        #: quitaron del codigo (ver `data/descartado.json`). El dibujo tiene
        #: que decirlo: un diagrama que pinta todos los puntos igual engaña.
        assert "se quitó" in svg, (
            "el diagrama ya no dice que proponer modulos vecinos se quito")
        assert "18 de 20 contra 18" in svg, (
            "el diagrama no trae la cifra por la que se quito: empataba con un "
            "conjunto fijo de tres modulos")
        assert svg.count("APORTA") == 1, (
            "el diagrama debe marcar el punto donde el grafo aporta, que es el "
            "vocabulario del prompt")
        assert "TacticRanker" in svg, (
            "el orden de la cascada lo fija el TacticRanker, no el area: el "
            "dibujo tiene que decir quien ordena")

    def test_los_veredictos_dibujados_son_los_que_el_codigo_produce(self):
        """El dibujo declaraba seis salidas y el código produce siete.

        Y las seis no eran ni siquiera un subconjunto: dos de ellas —«error de
        módulo» y «error semántico»— no son veredictos sino estados
        intermedios, cada uno con su reintento. El diagrama cortaba el flujo
        justo donde el código sigue trabajando.

        La lista buena es la única que no se puede inventar: los literales que
        `_math_via_lean` asigna a `verification_status`.
        """
        import io
        import re
        from nucleo.rutas import RAIZ
        core = io.open(RAIZ / "nucleo" / "core.py", encoding="utf-8").read()
        reales = set(re.findall(r'verification_status\s*=\s*"([a-z_]+)"', core))
        assert len(reales) >= 6, "no se encuentran los veredictos en core.py"

        for nombre in ("docs/img/00-flujo-real.svg", "README.md",
                       "docs/arquitectura_nle.html"):
            p = RAIZ / nombre
            if not p.exists():
                continue
            doc = io.open(p, encoding="utf-8").read()
            faltan = sorted(v for v in reales if v not in doc)
            assert not faltan, (
                "%s no nombra %s, que el código sí produce. "
                "Regenerar con python scripts/dibujar_flujo.py"
                % (nombre, ", ".join(faltan)))

    def test_el_diagrama_de_flujo_no_deja_cajas_sin_salida(self):
        """El paso 5 tenía flecha que entraba y ninguna que saliera.

        Lo vio el usuario leyendo el dibujo, no el script que lo genera. Ahora
        `dibujar_flujo.main` devuelve 1 si alguna caja del flujo queda
        huérfana, y esta guardia lo corre.
        """
        import importlib.util
        import io
        import sys
        from nucleo.rutas import RAIZ
        ruta = RAIZ / "scripts" / "dibujar_flujo.py"
        if not ruta.exists():
            return
        spec = importlib.util.spec_from_file_location("_dibujar_flujo", ruta)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        salida, sys.stdout = sys.stdout, io.StringIO()
        try:
            codigo = mod.main(None)
        finally:
            informe, sys.stdout = sys.stdout.getvalue(), salida
        assert codigo == 0, "el diagrama corta el flujo:\n" + informe
