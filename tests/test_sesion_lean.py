# -*- coding: utf-8 -*-
"""La sesión de Lean: lo que se puede testear sin arrancar Lean, y lo que no.

QUE SE TESTEA AQUI
------------------
Casi todo lo que puede romperse en `nucleo/lean/sesion.py` no es Lean: es la
CLASIFICACION de la respuesta —de ella sale la decisión del mediador— y el
ENCUADRE del protocolo —una línea en blanco cierra cada mensaje—. Las dos se
prueban con un proceso de mentira que contesta lo que se le diga, y corren en
milisegundos.

QUE NO SE TESTEA AQUI, Y HAY QUE DECIRLO
-----------------------------------------
Que la sesión y el fichero ACEPTEN LO MISMO no se prueba con un doble: eso es
precisamente lo que el doble no sabe. Lo mide
`scripts/sesion_contra_fichero.py` contra Lean de verdad, y su resultado vive
en `data/sesion_contra_fichero.json`. Un test verde aquí no dice nada sobre
esa concordancia.

Hay un test al final que sí arranca Lean; se salta solo si no está el REPL.
"""
import json
import os

import pytest

from nucleo.lean.sesion import (CABECERA_AMPLIA, Respuesta, SesionLean,
                                _clasificar, _ruta_repl)


# ── el doble ─────────────────────────────────────────────────────────────
class _Stdin:
    def __init__(self):
        self.escrito = []

    def write(self, s):
        self.escrito.append(s)

    def flush(self):
        pass


class _Proceso:
    """Contesta las respuestas que se le den, en orden, con su línea blanca.

    Imita lo único del proceso real que `_pide` toca: `stdin.write/flush`,
    iterar `stdout` línea a línea, y `poll()` devolviendo None mientras vive.
    """

    def __init__(self, respuestas):
        self.stdin = _Stdin()
        self.stderr = None
        self.pid = -1
        texto = ""
        for r in respuestas:
            cuerpo = r if isinstance(r, str) else json.dumps(r)
            texto += cuerpo + "\n\n"
        self.stdout = iter(texto.splitlines(keepends=True))

    def poll(self):
        return None

    def kill(self):
        pass


def _sesion_falsa(respuestas):
    s = SesionLean.__new__(SesionLean)       # sin abrir proceso de verdad
    s.raiz, s.repl = ".", "(doble)"
    s.env, s.llamadas, s.segundos = None, 0, 0.0
    s.p = _Proceso(respuestas)
    return s


# ── la clasificación, que es de donde sale la decisión ───────────────────
class TestClasificar:
    """`cierra · progresa · error · vacia`. El orden de las reglas importa."""

    def test_sin_objetivos_es_cierre(self):
        assert _clasificar({"goals": [], "proofState": 3}) == "cierra"

    def test_con_objetivos_es_progreso(self):
        assert _clasificar({"goals": ["⊢ P"], "proofState": 3}) == "progresa"

    def test_un_mensaje_de_error_manda_sobre_todo(self):
        """Aunque la táctica dejara la lista de objetivos vacía.

        Es el caso que hace falsos cierres: `goals == []` con un error de
        elaboración detrás NO es una prueba. Si esta regla se invirtiera, la
        sesión daría por cerrado algo que el fichero rechaza.
        """
        d = {"goals": [], "messages": [{"severity": "error", "data": "boom"}]}
        assert _clasificar(d) == "error"

    def test_un_aviso_no_es_un_error(self):
        d = {"goals": [], "messages": [{"severity": "warning",
                                        "data": "uses 'sorry'"}]}
        assert _clasificar(d) == "cierra"

    def test_un_sorry_abierto_es_progreso(self):
        """La respuesta típica de plantar el teorema: ni cierra ni falla."""
        d = {"sorries": [{"proofState": 0, "goal": "⊢ P"}], "env": 2}
        assert _clasificar(d) == "progresa"

    def test_un_entorno_nuevo_es_progreso(self):
        assert _clasificar({"env": 1}) == "progresa"

    def test_una_respuesta_sin_nada_es_vacia(self):
        assert _clasificar({}) == "vacia"


class TestRespuesta:

    def test_ok_solo_para_cierra_y_progresa(self):
        assert Respuesta("cierra").ok and Respuesta("progresa").ok
        assert not Respuesta("error").ok and not Respuesta("vacia").ok

    def test_error_saca_el_primer_mensaje_grave(self):
        r = Respuesta("error", mensajes=[{"severity": "info", "data": "hola"},
                                         {"severity": "error", "data": "boom"}])
        assert r.error == "boom"

    def test_sin_mensaje_grave_el_error_es_vacio(self):
        assert Respuesta("cierra", mensajes=[{"severity": "info"}]).error == ""


# ── el encuadre del protocolo ────────────────────────────────────────────
class TestElProtocolo:

    def test_manda_json_y_lo_cierra_con_linea_en_blanco(self):
        s = _sesion_falsa([{"env": 1}])
        s._pide({"cmd": "import Mathlib"}, tope=5)
        escrito = "".join(s.p.stdin.escrito)
        assert json.loads(escrito.strip()) == {"cmd": "import Mathlib"}
        assert escrito.endswith("\n\n")

    def test_lee_una_respuesta_de_varias_lineas(self):
        """El REPL imprime JSON indentado; el mensaje son todas sus líneas."""
        s = _sesion_falsa(['{\n "goals": [],\n "proofState": 7\n}'])
        r = s._pide({"tactic": "ring", "proofState": 6}, tope=5)
        assert r.clase == "cierra" and r.proof_state == 7

    def test_dos_peticiones_no_se_pisan(self):
        s = _sesion_falsa([{"env": 1}, {"goals": ["⊢ P"], "proofState": 0}])
        assert s._pide({"cmd": "x"}, 5).env == 1
        assert s._pide({"tactic": "y", "proofState": 0}, 5).objetivos == ["⊢ P"]

    def test_una_respuesta_que_no_es_json_no_revienta(self):
        """Lean puede escupir texto suelto; eso es un error, no una excepción."""
        s = _sesion_falsa(["esto no es json"])
        r = s._pide({"cmd": "x"}, 5)
        assert r.clase == "error" and "no es JSON" in r.error

    def test_el_timeout_da_error_y_no_cuelga(self):
        s = _sesion_falsa([])                # no contesta nunca
        r = s._pide({"cmd": "x"}, tope=1)
        assert r.clase == "error" and "TIMEOUT" in r.error

    def test_cuenta_llamadas_y_segundos(self):
        """El banco necesita el coste de la sesión, no sólo el resultado."""
        s = _sesion_falsa([{"env": 1}, {"env": 2}])
        s._pide({"cmd": "a"}, 5)
        s._pide({"cmd": "b"}, 5)
        assert s.llamadas == 2 and s.segundos >= 0.0

    def test_pedir_con_la_sesion_cerrada_falla_claro(self):
        s = _sesion_falsa([])
        s.p = None
        with pytest.raises(RuntimeError):
            s._pide({"cmd": "x"}, 5)


class TestLosTresMetodos:
    """`cabecera`, `comando`, `tactica`: qué mandan exactamente."""

    def test_la_cabecera_manda_imports_y_guarda_el_entorno(self):
        s = _sesion_falsa([{"env": 1}])
        assert s.cabecera(["Mathlib.Tactic"]) == 1
        assert s.env == 1
        assert json.loads("".join(s.p.stdin.escrito))["cmd"] == \
            "import Mathlib.Tactic"

    def test_la_cabecera_por_defecto_es_mathlib_entero(self):
        s = _sesion_falsa([{"env": 1}])
        s.cabecera()
        assert json.loads("".join(s.p.stdin.escrito))["cmd"] == \
            "\n".join("import " + m for m in CABECERA_AMPLIA)

    def test_el_comando_reutiliza_el_entorno_guardado(self):
        s = _sesion_falsa([{"env": 1}, {"sorries": [], "env": 2}])
        s.cabecera(["Mathlib"])
        s.comando("theorem t : True := trivial")
        assert json.loads(s.p.stdin.escrito[-1])["env"] == 1

    def test_env_none_explicito_pide_entorno_nuevo(self):
        """El caso del banco de concordancia, y por qué hay centinela.

        Si `env=None` cayera al entorno guardado, la sesión vería MAS
        biblioteca que el fichero y aceptaría cosas que el fichero no puede:
        el desacuerdo medido sería de la cabecera, no del motor. La medida de
        seguridad del paso 1 quedaría inflada sin que nadie lo notara.
        """
        s = _sesion_falsa([{"env": 1}, {"env": 2}])
        s.cabecera(["Mathlib"])
        s.comando("import Mathlib\ntheorem t : True := trivial", env=None)
        assert "env" not in json.loads(s.p.stdin.escrito[-1])

    def test_un_env_concreto_se_respeta(self):
        s = _sesion_falsa([{"env": 1}, {"env": 9}])
        s.cabecera(["Mathlib"])
        s.comando("theorem t : True := trivial", env=7)
        assert json.loads(s.p.stdin.escrito[-1])["env"] == 7

    def test_sin_cabecera_el_comando_va_sin_entorno(self):
        s = _sesion_falsa([{"env": 1}])
        s.comando("import Mathlib\ntheorem t : True := trivial")
        assert "env" not in json.loads(s.p.stdin.escrito[-1])

    def test_la_tactica_manda_tactic_y_proofstate(self):
        s = _sesion_falsa([{"goals": []}])
        s.tactica("nlinarith [sq_nonneg (a-b)]", 4)
        d = json.loads("".join(s.p.stdin.escrito))
        assert d == {"tactic": "nlinarith [sq_nonneg (a-b)]", "proofState": 4}


class TestElCicloDeVida:

    def test_abrir_sin_repl_dice_como_construirlo(self):
        s = SesionLean(repl="C:/no/existe/repl.exe")
        with pytest.raises(FileNotFoundError) as e:
            s.abrir()
        assert "construir_repl" in str(e.value)

    def test_cerrar_dos_veces_no_revienta(self):
        s = _sesion_falsa([])
        s.cerrar()
        s.cerrar()
        assert not s.viva

    def test_la_variable_de_entorno_manda_sobre_la_ruta_por_defecto(self, monkeypatch):
        """Los bancos la usan para probar OTRA versión del REPL."""
        monkeypatch.setenv("METAMAT_REPL", "D:/otro/repl.exe")
        assert _ruta_repl() == "D:/otro/repl.exe"

    def test_sin_variable_la_ruta_sale_de_la_raiz_del_proyecto(self, monkeypatch):
        monkeypatch.delenv("METAMAT_REPL", raising=False)
        r = _ruta_repl()
        assert r.endswith("repl.exe") and ".lake" in r


# ── el único que arranca Lean ────────────────────────────────────────────
@pytest.mark.skipif(not os.path.exists(_ruta_repl()),
                    reason="no hay REPL construido (scripts/construir_repl.py)")
def test_contra_lean_de_verdad():
    """Un teorema trivial, sin Mathlib, para que tarde segundos y no minutos.

    No comprueba concordancia —eso es `scripts/sesion_contra_fichero.py`—.
    Comprueba que el proceso arranca, habla el protocolo y muere.
    """
    with SesionLean() as s:
        r = s.comando("theorem trivialito : True := by trivial")
        assert r.clase != "error", r.error
    assert not s.viva
