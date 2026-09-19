# -*- coding: utf-8 -*-
"""«Unknown constant» no significa «no existe»: significa «no está importado».

EL FALLO, salido de una consulta real
-------------------------------------
    «Demuestra el teorema fundamental del cálculo diferencial»

Lean contestó `Unknown constant intervalIntegral.integral_eq_sub_of_hasDerivAt`
y el diagnóstico tradujo eso, de una tabla de subcadenas, a:

    «ese nombre no existe en Mathlib; usa `exact?` o busca el lema real»

Es falso, y el sistema tenía delante las tres pruebas de que lo era:
`nombres.existe()` decía True, `modulo_de()` daba
`Mathlib.MeasureTheory.Integral.IntervalIntegral.FundThmCalculus`, y
`enunciados_de()` devolvía el enunciado entero. En la misma pantalla el
verificador de nombres le decía al alumno lo contrario que el diagnóstico.

EL DAÑO ES DOBLE, y la segunda mitad es la cara. Al alumno se le afirma una
falsedad; y al BUCLE DE REPARACIÓN se le dice que tire un lema correcto,
porque el prompt de revisión lleva escrito «si un lema no existe bajo ese
nombre, usa otro de Mathlib o deja `sorry`». El sistema se autoconvence de
abandonar la pieza buena.

Y NO ES UNA PUERTA ABIERTA. Un nombre de verdad inventado tiene que seguir
diagnosticándose como inexistente; si no, el diagnóstico deja de distinguir y
vuelve a no informar de nada.
"""
import re

import pytest

#: existe en Mathlib, y su módulo no está en la cabecera por defecto
REAL = "intervalIntegral.integral_eq_sub_of_hasDerivAt"
INVENTADO = "no_existe_este_lema_jamas_de_los_jamases"

#: las tres formas en que Lean escribe el MISMO fallo. La tercera es la que
#: `repair_imports` no reconocía, aunque `_ERRORES_MECANICOS` de core.py ya
#: documentaba que Lean alterna entre ellas.
FORMAS = [
    "Unknown constant %s",
    "Unknown constant `%s`",
    "The identifier `%s` is unknown, y autoImplicit esta activo",
]


@pytest.fixture(scope="module")
def n():
    import sys
    sys.argv = ["x"]
    from nucleo.core import Nucleo
    return Nucleo.__new__(Nucleo)


@pytest.fixture(scope="module")
def cliente_lean():
    """Un cliente sin arrancar Lean: `repair_imports` solo lee las fuentes."""
    import pathlib
    from nucleo.lean.client import LeanClient
    from nucleo.rutas import RAIZ
    c = LeanClient.__new__(LeanClient)
    c.project_path = pathlib.Path(RAIZ)
    c._pistas_reparacion = set()
    c._namespaces_detectados = {}
    if not c._mathlib_lean_files():
        pytest.skip("sin fuentes de Mathlib en disco")
    return c


@pytest.fixture(scope="module")
def indice():
    from nucleo.lean import nombres
    if not nombres.existe(REAL):
        pytest.skip("el índice de nombres no tiene %s: el caso pierde sentido"
                    % REAL)
    return nombres


class TestElDiagnosticoNoAfirmaFalsedades:

    @pytest.mark.parametrize("forma", FORMAS)
    def test_un_nombre_que_existe_no_se_declara_inexistente(
            self, n, indice, forma):
        from nucleo.core import Nucleo
        hint = Nucleo._lean_hint(n, forma % REAL)
        assert "no existe" not in hint.lower(), (
            "el diagnóstico afirma que un lema de Mathlib no existe. El "
            "sistema sabe que sí: `nombres.existe()` es True y `modulo_de()` "
            "da su módulo. Además de mentirle al alumno, le dice al bucle de "
            "reparación que abandone un lema correcto")

    @pytest.mark.parametrize("forma", FORMAS)
    def test_y_dice_lo_que_falta_de_verdad(self, n, indice, forma):
        from nucleo.core import Nucleo
        hint = Nucleo._lean_hint(n, forma % REAL)
        assert "import" in hint.lower(), (
            "«Unknown constant» es casi siempre un import que falta; el "
            "diagnóstico tiene que decir eso, que es accionable")
        assert indice.modulo_de(REAL) in hint, (
            "y con el módulo concreto, que el sistema ya conoce")

    def test_un_nombre_inventado_sigue_siendo_inexistente(self, n):
        """El arreglo no puede volverse un «todo existe»."""
        from nucleo.core import Nucleo
        hint = Nucleo._lean_hint(n, "Unknown constant %s" % INVENTADO)
        assert "no existe" in hint.lower()

    def test_los_demas_errores_no_se_tocan(self, n):
        from nucleo.core import Nucleo
        assert "tipos no coinciden" in Nucleo._lean_hint(
            n, "type mismatch: expected Prop")


class TestLaReparacionReconoceLasTresFormas:
    """`repair_imports` no reparaba nada con la forma larga."""

    @pytest.mark.parametrize("forma", FORMAS)
    def test_extrae_el_nombre_de_las_tres(self, forma):
        from nucleo.lean.client import LeanClient
        err = forma % REAL
        hallados = [m.group(1) for p in LeanClient._RE_UNKNOWN
                    for m in p.finditer(err)]
        assert REAL in hallados, (
            "si la regex no extrae el nombre, `repair_imports` no repara nada "
            "aunque el lema exista y su módulo sea localizable: exactamente "
            "el fallo que ya estaba documentado para `_ERRORES_MECANICOS` y "
            "que aquí nadie había aplicado")

    @pytest.mark.parametrize("forma", FORMAS)
    def test_repara_con_el_modulo_bueno(self, cliente_lean, indice, forma):
        from nucleo.lean.client import LeanClient
        code = "import Mathlib.Data.Real.Basic\ntheorem t : True := by\n  exact %s\n" % REAL
        out = LeanClient.repair_imports(cliente_lean, code, [forma % REAL])
        assert out, "no reparó nada"
        assert indice.modulo_de(REAL) in out


def test_el_prompt_de_revision_no_invita_a_tirar_un_lema_bueno():
    """La otra mitad del daño, y la cara.

    El prompt dice «si un lema no existe bajo ese nombre, usa otro o deja
    sorry». Con un diagnóstico que declaraba inexistente lo que sí existe,
    esa instrucción hacía que el modelo abandonara la pieza correcta. La
    instrucción está bien; lo que tenía que arreglarse era el diagnóstico, y
    este test fija que los dos viajan juntos.
    """
    import io
    import os
    ruta = os.path.join(os.path.dirname(os.path.dirname(
        os.path.abspath(__file__))), "nucleo", "core.py")
    src = io.open(ruta, encoding="utf-8").read()
    assert "does not exist under that name" in src or \
           "lemma does not exist" in src, (
        "cambió el prompt de revisión: comprobar que el diagnóstico de "
        "nombres desconocidos sigue siendo coherente con lo que se le pide "
        "al modelo")
    assert re.search(r"_nom\.existe|nombres\s+as\s+_nom", src), (
        "`_lean_hint` ya no consulta el índice de nombres: vuelve a poder "
        "afirmar que un lema de Mathlib no existe")


NS = "intervalIntegral"


class TestUnNamespaceNoEsUnaDeclaracion:
    """La misma familia de fallo, una capa mas abajo.

    Tras arreglar «Unknown constant», la misma consulta devolvio

        unknown namespace intervalIntegral

    y el diagnostico se cayo al generico «revisa la sintaxis Lean 4 y los
    imports de Mathlib», que no es accionable. Un namespace no se declara: se
    abre, asi que buscarlo entre las declaraciones no lo encuentra.

    Y el import que si se encontraba era el EQUIVOCADO: `intervalIntegral`
    aparece declarado en `...IntervalIntegral.Basic` —donde se abre el
    namespace— mientras que el lema que el codigo usaba vive en
    `...IntervalIntegral.FundThmCalculus`. Import correcto de un modulo
    inutil: Lean volvia a fallar y parecia que reparar no servia.
    """

    def test_el_indice_sabe_de_namespaces(self, indice):
        assert indice.existe_namespace(NS)
        assert indice.modulos_del_namespace(NS)
        assert not indice.existe_namespace("noExisteEsteNamespaceJamas")

    def test_el_diagnostico_deja_de_ser_generico(self, n, indice):
        from nucleo.core import Nucleo
        hint = Nucleo._lean_hint(n, "unknown namespace %s" % NS)
        assert "revisa la sintaxis" not in hint, (
            "seguia cayendo al mensaje generico, que no dice que hacer")
        assert "import" in hint.lower() and NS in hint

    def test_un_namespace_inventado_no_se_afirma(self, n):
        from nucleo.core import Nucleo
        hint = Nucleo._lean_hint(n, "unknown namespace noExisteEsteNamespaceJamas")
        assert "SI existe" not in hint

    def test_se_importa_el_modulo_DEL_LEMA_y_no_el_del_namespace(
            self, cliente_lean, indice):
        """El codigo dice que lema del namespace se esta usando: ese manda."""
        from nucleo.lean.client import LeanClient
        code = "\n".join([
            "import Mathlib.Data.Real.Basic",
            "open " + NS,
            "theorem t : True := by",
            "  have := " + REAL,
            "  trivial",
            "",
        ])
        out = LeanClient.repair_imports(cliente_lean, code,
                                        ["unknown namespace %s" % NS])
        assert out, "no reparo nada"
        imports = [l for l in out.splitlines() if l.startswith("import")]
        del_lema = indice.modulo_de(REAL)
        assert any(del_lema in l for l in imports), (
            "no importo el modulo del lema que el codigo usa: %s" % imports)
        # y va DELANTE del modulo donde solo se abre el namespace
        pos_lema = next(i for i, l in enumerate(imports) if del_lema in l)
        otros = [i for i, l in enumerate(imports)
                 if NS.lower() in l.lower() and del_lema not in l]
        assert all(pos_lema < o for o in otros), (
            "el modulo que resuelve de verdad tiene que ir primero")

INVENTADO_REAL = "Bool.RingHom"


class TestUnNombreInventadoNoEsUnFalloDeModulo:
    """El triaje decidia mal quien podia arreglar el fallo.

    `Unknown constant Bool.RingHom` —en Mathlib `Bool` es un algebra de Boole,
    no un anillo, asi que el nombre es una invencion del modelo—. El triaje lo
    daba por MECANICO, que significa «esto lo arregla `repair_imports` solo»,
    y con eso SE SALTABA EL BUCLE DE REVISION. Luego `repair_imports` no
    encontraba modulo, porque no hay tal declaracion, y el alumno recibia el
    error en crudo.

    El unico camino capaz de arreglarlo —que el modelo elija otro lema— era
    justo el que el triaje apagaba.
    """

    @staticmethod
    def _res(texto, kinds=None):
        class R:
            def __init__(self):
                self.error_kinds = kinds or []

            def get_first_error(self):
                return texto
        return R()

    def test_un_nombre_inventado_va_a_revision(self, n, indice):
        from nucleo.core import Nucleo
        assert not indice.existe(INVENTADO_REAL), (
            "la premisa: %s no existe en Mathlib" % INVENTADO_REAL)
        assert not Nucleo._es_error_mecanico(
            n, self._res("Unknown constant " + INVENTADO_REAL)), (
            "un nombre inventado se daba por mecanico, se saltaba la revision, "
            "y ningun import podia arreglarlo")

    def test_un_nombre_real_sigue_siendo_de_modulo(self, n, indice):
        from nucleo.core import Nucleo
        assert Nucleo._es_error_mecanico(
            n, self._res("Unknown constant " + REAL)), (
            "un lema que existe y no esta importado SI lo arregla "
            "`repair_imports`: mandarlo a revision gastaria una llamada al "
            "modelo para nada")

    def test_un_modulo_desconocido_no_necesita_indice(self, n):
        from nucleo.core import Nucleo
        assert Nucleo._es_error_mecanico(
            n, self._res("unknown module Mathlib.NoExisteEsto"))

    def test_los_errores_semanticos_no_se_tocan(self, n):
        from nucleo.core import Nucleo
        assert not Nucleo._es_error_mecanico(n, self._res("type mismatch"))

    def test_tambien_por_el_tipo_estructurado(self, n, indice):
        """El `kind` del JSON no dice si el nombre existe: hay que mirarlo."""
        from nucleo.core import Nucleo
        assert not Nucleo._es_error_mecanico(
            n, self._res("Unknown constant " + INVENTADO_REAL,
                         ["lean.unknownConstant"]))


class TestElDiagnosticoOfreceLoQueSiExiste:
    """Decir «no existe» es cierto e inutil si el indice sabe que hay cerca."""

    def test_ofrece_candidatos_parecidos(self, n, indice):
        from nucleo.core import Nucleo
        hint = Nucleo._lean_hint(n, "Unknown constant " + INVENTADO_REAL)
        assert "BoolRing" in hint, (
            "`nombres.parecidos()` devuelve `BoolRing`, que es casi con "
            "seguridad lo que se buscaba, y el diagnostico mandaba a buscar a "
            "mano lo que el sistema ya sabia")

    def test_los_candidatos_se_presentan_como_candidatos(self, n, indice):
        """Semejanza de cadenas, no de matematicas."""
        from nucleo.core import Nucleo
        hint = Nucleo._lean_hint(n, "Unknown constant " + INVENTADO_REAL)
        assert "candidatos" in hint.lower() and "no una respuesta" in hint, (
            "presentar un parecido de nombre como la solucion seria inventar "
            "con otro disfraz")

    def test_dice_que_el_namespace_si_existe(self, n, indice):
        from nucleo.core import Nucleo
        hint = Nucleo._lean_hint(n, "Unknown constant " + INVENTADO_REAL)
        assert "Bool" in hint and "no declara" in hint

    def test_sin_parecidos_no_se_inventa_una_lista(self, n):
        from nucleo.core import Nucleo
        hint = Nucleo._lean_hint(
            n, "Unknown constant zzqqxx_no_se_parece_a_nada_de_nada_jamas")
        assert "no existe" in hint.lower()
        assert "parecido" not in hint.lower() or "exact?" in hint
