"""
Tests de la extraccion de identificadores de los errores de Lean.

`repair_imports` es la reparacion mas util del pipeline: busca en las fuentes
de Mathlib el identificador que Lean dice no conocer, deduce su modulo y
reintenta. Pero sus patrones solo aceptaban identificadores entre COMILLAS
SIMPLES, y Lean 4 los encomilla con ACENTO GRAVE:

    Unknown identifier `le_div_iff`

Resultado: no extraia nada de los mensajes reales y la reparacion no se
disparaba nunca. Medido auditando LeanWorkbookProofs — 0 rescates sobre una
muestra en la que los lemas existian y su modulo era localizable.
"""
import pytest

from nucleo.lean.client import LeanClient


def _extraer(mensaje: str) -> set[str]:
    encontrados: set[str] = set()
    for rx in LeanClient._RE_UNKNOWN:
        encontrados.update(rx.findall(mensaje))
    return encontrados


class TestExtraccionDeIdentificadores:

    @pytest.mark.parametrize("mensaje,esperado", [
        # El formato que Lean 4 usa de verdad.
        ("Unknown identifier `le_div_iff`", "le_div_iff"),
        ("Unknown constant `Nat.chineseRemainder`", "Nat.chineseRemainder"),
        ("unknown namespace `Topology`", "Topology"),
        # Comillas simples: formato antiguo, debe seguir funcionando.
        ("unknown identifier 'foo'", "foo"),
        ("unknown constant 'Real.sqrt'", "Real.sqrt"),
    ])
    def test_reconoce_ambos_encomillados(self, mensaje, esperado):
        assert esperado in _extraer(mensaje), (
            f"no se extrajo {esperado!r} de {mensaje!r}; "
            "repair_imports no podra reparar este error"
        )

    def test_identificadores_cualificados(self):
        """Los nombres con punto deben salir enteros, no partidos."""
        assert "Mathlib.Data.Nat" in _extraer("Unknown constant `Mathlib.Data.Nat`")

    def test_no_inventa_sobre_mensajes_ajenos(self):
        for m in ("type mismatch", "unsolved goals ⊢ False", "expected token"):
            assert not _extraer(m), f"extrajo algo espurio de {m!r}"


class TestClasificacionDeErrores:
    """El triaje decide si un error es de modulo o de matematicas."""

    def test_los_de_modulo_son_mecanicos(self):
        for err in ("Unknown identifier `le_div_iff`",
                    "Unknown constant `Nat.foo`",
                    "unknown identifier 'bar'"):
            from nucleo.core import Nucleo
            assert any(m in err.lower() for m in Nucleo._ERRORES_MECANICOS), (
                f"{err!r} deberia tratarse como error de modulo"
            )

    def test_los_semanticos_no(self):
        from nucleo.core import Nucleo
        for err in ("type mismatch", "tactic failed", "unsolved goals"):
            assert not any(m in err.lower() for m in Nucleo._ERRORES_MECANICOS)


class TestSubindicesDeMathlib:
    """
    Mathlib renombra al generalizar: `div_le_div_iff` -> `div_le_div_iff₀`.

    La clase de caracteres de _RE_DECL no incluia los subindices, asi que la
    captura se cortaba y `div_le_div_iff₀` se registraba como
    `div_le_div_iff`. find_module_for_identifier daba por HALLADO un lema
    inexistente, repair_imports anadia el modulo correcto, y Lean seguia
    diciendo "Unknown identifier": un falso positivo que impedia distinguir
    "falta el import" de "el lema se renombro".
    """

    @pytest.mark.parametrize("linea,esperado", [
        ("lemma div_le_div_iff₀ (hb : 0 < b) : True", "div_le_div_iff₀"),
        ("theorem le_div_iff₀ (h : 0 < c) : True", "le_div_iff₀"),
        ("lemma mul_inv_le_iff₀' (hc : 0 < c) : True", "mul_inv_le_iff₀'"),
        ("theorem foo_bar : True", "foo_bar"),
        ("protected theorem Nat.baz₁ : True", "Nat.baz₁"),
    ])
    def test_captura_el_nombre_completo(self, linea, esperado):
        m = LeanClient._RE_DECL.match(linea)
        assert m is not None, f"no reconoce la declaracion: {linea!r}"
        assert m.group(1) == esperado, (
            f"capturo {m.group(1)!r} en vez de {esperado!r}: el nombre se "
            "trunca y se confunde con el lema antiguo"
        )

    def test_los_sufijos_de_renombre_estan_declarados(self):
        assert "₀" in LeanClient._SUFIJOS_RENOMBRE, (
            "el sufijo de subindice cero es el mas comun en Mathlib"
        )


class TestNamespacesDeMathlib:
    """
    Un identificador puede EXISTIR, estar su modulo importado, y aun asi no
    resolverse: porque vive dentro de un `namespace`.

    Caso real: `Basis` se movio a `Module.Basis` y no quedo alias en la raiz.
    Lean respondia "Function expected at Basis but this term has type ?m.1"
    —autoImplicit lo tomaba por variable libre— y repair_imports, que solo sabia
    de modulos, añadia QuaternionBasis y una libreria de asintotica sin resolver
    nada.
    """

    def test_detecta_el_namespace_de_un_identificador(self):
        from nucleo.lean.client import LeanClient
        c = LeanClient(project_path=".")
        c.find_modules_for_identifiers(["Basis"])
        ns = getattr(c, "_namespaces_detectados", {})
        assert ns.get("Basis") == "Module", (
            f"esperaba Basis -> Module, obtuve {ns}"
        )

    def test_repair_abre_el_namespace(self):
        from nucleo.lean.client import LeanClient
        codigo = (
            "import Mathlib.LinearAlgebra.Basis.Defs\n"
            "\n"
            "theorem t : True := trivial\n"
        )
        c = LeanClient(project_path=".")
        rep = c.repair_imports(codigo, ["Unknown identifier `Basis`"])
        assert rep is not None, "repair_imports no intento nada"
        assert "open Module" in rep, f"no abrio el namespace:\n{rep[:200]}"

    def test_no_añade_imports_si_el_fallo_es_de_namespace(self):
        """
        El modulo ya estaba importado. Añadir mas es ruido, y ademas alarga el
        tiempo de compilacion sin arreglar el error.
        """
        from nucleo.lean.client import LeanClient
        codigo = (
            "import Mathlib.LinearAlgebra.Basis.Defs\n"
            "\n"
            "theorem t : True := trivial\n"
        )
        c = LeanClient(project_path=".")
        rep = c.repair_imports(codigo, ["Unknown identifier `Basis`"])
        assert "QuaternionBasis" not in rep, (
            "sigue añadiendo modulos irrelevantes para un error de namespace"
        )
