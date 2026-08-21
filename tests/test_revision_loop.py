"""
Tests del bucle de revision: el veredicto de Lean se realimenta al generador.

Antes, el diagnostico de un error de Lean (tipo, mensaje, pista de tactica) se
calculaba y solo se IMPRIMIA para el usuario. Nunca volvia al LLM, asi que un
rechazo por `type mismatch` o `tactic failed` terminaba el intento. Estos tests
fijan el lazo generador -> verificador -> revisor.
"""
import asyncio
import types

import pytest

from nucleo.core import Nucleo
from nucleo.lean.client import LeanResult, LeanResultStatus


# ---------------------------------------------------------------------------
# Dobles de prueba
# ---------------------------------------------------------------------------

def _res_error(*mensajes: str) -> LeanResult:
    return LeanResult(
        status=LeanResultStatus.ERROR,
        messages=[{"severity": "error", "data": m} for m in mensajes],
        output="\n".join(mensajes),
    )


def _res_ok() -> LeanResult:
    return LeanResult(status=LeanResultStatus.SUCCESS, messages=[], output="")


class _LLMFalso:
    """Devuelve codigos predefinidos, uno por llamada, y guarda los prompts."""

    def __init__(self, *respuestas: str):
        self.respuestas = list(respuestas)
        self.prompts: list[str] = []

    async def generate(self, prompt, system=None, context=None):
        self.prompts.append(prompt)
        code = self.respuestas.pop(0) if self.respuestas else "-- sin mas"
        return types.SimpleNamespace(content=f"```lean\n{code}\n```")


class _LeanFalso:
    """Devuelve resultados predefinidos, uno por check_code."""

    def __init__(self, *resultados: LeanResult):
        self.resultados = list(resultados)
        self.codigos: list[str] = []

    async def check_code(self, code: str) -> LeanResult:
        self.codigos.append(code)
        return self.resultados.pop(0) if self.resultados else _res_ok()


def _nucleo(llm, lean) -> Nucleo:
    """Nucleo sin initialize(): el bucle solo necesita _llm y _lean."""
    n = Nucleo.__new__(Nucleo)
    Nucleo.__init__(n)
    n._llm, n._lean = llm, lean
    return n


def _correr(coro):
    return asyncio.new_event_loop().run_until_complete(coro)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestRevisarConLean:

    def test_error_semantico_se_revisa_y_recupera(self):
        """ERROR -> el LLM ve el fallo -> Lean acepta la correccion."""
        llm = _LLMFalso("theorem t : True := trivial")
        lean = _LeanFalso(_res_ok())
        n = _nucleo(llm, lean)

        code, res, rondas = _correr(n._revisar_con_lean(
            "theorem t : True := by exact LEMA_FALSO",
            _res_error("type mismatch: expected True"),
            "PROMPT", "SYS", {},
        ))

        assert res.status == LeanResultStatus.SUCCESS
        assert rondas == 1
        assert code.strip() == "theorem t : True := trivial"

    def test_el_prompt_lleva_el_error_exacto_de_lean(self):
        """La realimentacion debe contener el mensaje literal, no solo la pista."""
        llm = _LLMFalso("theorem t : True := trivial")
        n = _nucleo(llm, _LeanFalso(_res_ok()))

        _correr(n._revisar_con_lean(
            "codigo roto",
            _res_error("unsolved goals ⊢ False"),
            "PROMPT ORIGINAL", "SYS", {},
        ))

        p = llm.prompts[0]
        assert "PROMPT ORIGINAL" in p          # conserva el encargo original
        assert "unsolved goals" in p           # el error literal de Lean
        assert "codigo roto" in p              # lo que se envio antes
        assert "faltan casos" in p             # la pista de _LEAN_HINTS

    def test_no_acepta_una_revision_peor(self):
        """Si la revision empeora, se conserva el resultado anterior."""
        llm = _LLMFalso("peor")
        lean = _LeanFalso(_res_error("e1", "e2", "e3"))   # 3 errores > 1
        n = _nucleo(llm, lean)

        original = _res_error("un solo error")
        code, res, _ = _correr(n._revisar_con_lean(
            "original", original, "P", "S", {},
        ))

        assert code == "original"
        assert res is original

    def test_cota_de_rondas(self):
        """Nunca mas de max_rondas llamadas al LLM: cada una cuesta Lean."""
        llm = _LLMFalso("v1", "v2", "v3", "v4")
        lean = _LeanFalso(_res_error("a"), _res_error("b"), _res_error("c"))
        n = _nucleo(llm, lean)

        _correr(n._revisar_con_lean(
            "orig", _res_error("x", "y", "z"), "P", "S", {}, max_rondas=2,
        ))

        assert len(llm.prompts) <= 2

    def test_no_se_revisa_lo_que_no_es_error(self):
        """SUCCESS y SORRY no se tocan: SORRY lo cubre SolverCascade."""
        for estado in (LeanResultStatus.SUCCESS, LeanResultStatus.SORRY):
            llm = _LLMFalso("no deberia usarse")
            n = _nucleo(llm, _LeanFalso())
            r = LeanResult(status=estado, messages=[], output="")

            code, res, rondas = _correr(
                n._revisar_con_lean("c", r, "P", "S", {})
            )

            assert rondas == 0
            assert res is r
            assert llm.prompts == []


class TestTriajePorSeveridad:
    """El triaje decide QUE reparador entra, sobre el veredicto de Lean."""

    def test_errores_mecanicos_no_van_al_revisor(self):
        """Los de modulo los arregla repair_imports, no una reformulacion."""
        for err in ("unknown identifier `foo`",
                    "unknown constant `Bar.baz`"):
            assert any(m in err.lower() for m in Nucleo._ERRORES_MECANICOS)

    def test_errores_semanticos_si_van_al_revisor(self):
        for err in ("type mismatch", "tactic failed", "unsolved goals",
                    "failed to synthesize"):
            assert not any(m in err.lower() for m in Nucleo._ERRORES_MECANICOS)

    def test_cada_error_tiene_pista(self):
        n = Nucleo.__new__(Nucleo)
        for err in ("type mismatch: x", "tactic failed at y", "unsolved goals ⊢ P",
                    "unknown constant `Z`", "algo nunca visto"):
            assert n._lean_hint(err)
