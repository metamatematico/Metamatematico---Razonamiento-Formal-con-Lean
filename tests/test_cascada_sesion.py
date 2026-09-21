# -*- coding: utf-8 -*-
"""La cascada por estado: leer quién ganó, y escribir la prueba que se verifica.

`ensamblar` es la pieza que convierte lo que la sesión encontró en el fichero
que decide (invariante I2). Si sustituyera mal —otro `sorry`, otra línea, una
prueba a medias— el fichero juzgaría una prueba distinta de la encontrada. Los
casos de aquí salen de la sonda contra el REPL real (posiciones incluidas).

La concordancia contra Lean no se prueba aquí: la mide
`scripts/cascada_por_estado.py`.
"""
from nucleo.lean.cascada_sesion import (CierrePorEstado, cerrar_sorries,
                                        ensamblar, ganadora_de)
from nucleo.lean.solver_cascade import _MARCA
from tests.test_sesion_lean import _sesion_falsa

COD = ("theorem a1 (a b : Nat) : a + b = b + a := by\n"
       "  sorry\n"
       "\n"
       "theorem a2 (x : Nat) (h : x = 2) : x * x = 4 := by\n"
       "  have hx : x = 2 := sorry\n"
       "  subst hx\n"
       "  sorry\n")


def _c(linea, col, g="linarith", motivo="cierra"):
    return CierrePorEstado(motivo, ganadora=g, linea=linea, columna=col)


class TestGanadora:

    def test_la_marca_da_la_tactica(self):
        ms = [{"severity": "info", "data": _MARCA + "ring"}]
        assert ganadora_de(ms) == "ring"

    def test_sin_marca_no_se_inventa(self):
        assert ganadora_de([{"severity": "info", "data": "Try this: ring_nf"}]) == ""
        assert ganadora_de(None) == ""


class TestEnsamblar:

    def test_cada_sorry_en_su_sitio(self):
        """Posiciones de la sonda real, que el REPL devolvió DESORDENADAS."""
        out = ensamblar(COD, [_c(2, 2), _c(7, 2, "norm_num"), _c(5, 21)])
        assert "sorry" not in out
        assert out.split("\n")[1] == "  linarith"
        assert out.split("\n")[6] == "  norm_num"

    def test_el_sorry_de_termino_va_con_by(self):
        out = ensamblar(COD, [_c(2, 2), _c(7, 2), _c(5, 21)])
        assert out.split("\n")[4] == "  have hx : x = 2 := (by linarith)"

    def test_una_prueba_a_medias_no_se_ensambla(self):
        """No se manda a verificar como entera una prueba con huecos."""
        abierto = CierrePorEstado("no_cierra", linea=7, columna=2)
        assert ensamblar(COD, [_c(2, 2), abierto, _c(5, 21)]) is None

    def test_sin_cierres_no_hay_prueba(self):
        assert ensamblar(COD, []) is None

    def test_una_posicion_que_no_es_un_sorry_no_se_toca(self):
        """Si el REPL y el texto no casan, None — no sustituir otra cosa."""
        assert ensamblar(COD, [_c(2, 0)]) is None          # columna del sangrado
        assert ensamblar(COD, [_c(99, 2)]) is None         # línea inexistente

    def test_sin_marca_se_escribe_el_bloque_que_cerro(self):
        c = CierrePorEstado("sin_marca", linea=2, columna=2)
        out = ensamblar("theorem t : True := by\n  sorry", [c],
                        bloque="first | (trivial ; done)")
        assert out.endswith("  first | (trivial ; done)")

    def test_sin_marca_y_sin_bloque_no_se_inventa(self):
        c = CierrePorEstado("sin_marca", linea=2, columna=2)
        assert ensamblar("theorem t : True := by\n  sorry", [c]) is None

    def test_la_flecha_de_un_caso_no_se_envuelve(self):
        """`| zero => sorry` es modo táctica en `induction … with`."""
        cod = "theorem t (n : Nat) : True := by\n  induction n with\n  | zero => sorry"
        c = CierrePorEstado("cierra", ganadora="trivial", linea=3, columna=12)
        assert ensamblar(cod, [c]).endswith("| zero => trivial")


class TestCerrarSorries:
    """Con la sesión de mentira: qué se manda y cómo se lee."""

    def test_un_codigo_que_no_elabora_vuelve_con_su_error(self):
        s = _sesion_falsa([{"messages": [{"severity": "error", "data": "boom"}]}])
        cierres, err = cerrar_sorries(s, "theorem t : x := by sorry", "rfl")
        assert cierres == [] and "boom" in err

    def test_cierra_y_dice_quien(self):
        s = _sesion_falsa([
            {"sorries": [{"proofState": 0, "pos": {"line": 1, "column": 22},
                          "goal": "⊢ True"}], "env": 1},
            {"proofState": 1, "goals": [],
             "messages": [{"severity": "info", "data": _MARCA + "trivial"}]},
        ])
        cierres, err = cerrar_sorries(s, "theorem t : True := by sorry",
                                      [("trivial", 1)])
        assert not err and len(cierres) == 1
        assert cierres[0].cerrado and cierres[0].ganadora == "trivial"
        assert (cierres[0].linea, cierres[0].columna) == (1, 22)

    def test_el_fallo_de_primer_nivel_no_es_cierre(self):
        """La respuesta real de un `first |` que falla: `message` suelto."""
        s = _sesion_falsa([
            {"sorries": [{"proofState": 0, "pos": {"line": 1, "column": 22}}],
             "env": 1},
            {"message": "Lean error:\nTactic `rfl` failed"},
        ])
        cierres, _ = cerrar_sorries(s, "theorem t : 1 = 2 := by sorry", "rfl")
        assert cierres[0].motivo == "no_cierra" and not cierres[0].cerrado
        assert "rfl" in cierres[0].error

    def test_un_bloque_ya_hecho_se_manda_tal_cual(self):
        s = _sesion_falsa([
            {"sorries": [{"proofState": 0, "pos": {"line": 1, "column": 22}}],
             "env": 1},
            {"goals": []},
        ])
        cerrar_sorries(s, "theorem t : True := by sorry", "first | (trivial ; done)")
        import json
        assert json.loads(s.p.stdin.escrito[-1])["tactic"] == "first | (trivial ; done)"


class TestPorComando:
    """El modo del camino servido: el teorema con el bloque, como comando."""

    _COD = "theorem t : 1 = 1 := by\n  sorry"
    _R0 = {"sorries": [{"proofState": 0, "pos": {"line": 2, "column": 2},
                        "goal": "⊢ 1 = 1"}], "env": 1,
           "messages": [{"severity": "warning", "data": "declaration uses 'sorry'"}]}

    def _corre(self, respuesta):
        from nucleo.lean.cascada_sesion import cerrar_sorries_por_comando
        s = _sesion_falsa([self._R0, respuesta])
        cierres, err = cerrar_sorries_por_comando(s, self._COD, "first | (rfl ; done)")
        return s, cierres, err

    def test_manda_el_codigo_con_el_bloque_en_el_sitio(self):
        import json
        s, _, _ = self._corre({"env": 2})
        enviado = json.loads(s.p.stdin.escrito[-1])["cmd"]
        assert enviado == "theorem t : 1 = 1 := by\n  first | (rfl ; done)"

    def test_cierra_si_no_hay_error(self):
        _, c, err = self._corre({"env": 2, "messages": [
            {"severity": "info", "data": _MARCA + "rfl"}]})
        assert not err and c[0].cerrado and c[0].ganadora == "rfl"

    def test_un_error_no_es_cierre(self):
        _, c, _ = self._corre({"env": 2, "messages": [
            {"severity": "error", "data": "first failed"}]})
        assert not c[0].cerrado

    def test_apply_que_admite_con_sorry_no_es_cierre(self):
        """Medido sobre `n * n ≠ 2`: el bloque «ganaba» con `apply?`, que
        cierra con `sorry` cuando no encuentra prueba. El aviso sigue ahí."""
        _, c, _ = self._corre({"env": 2, "messages": [
            {"severity": "info", "data": _MARCA + "apply?"},
            {"severity": "warning", "data": "declaration uses 'sorry'"}]})
        assert not c[0].cerrado and "admitió" in c[0].error

    def test_apply_que_cierra_de_verdad_si_cuenta(self):
        """Si el aviso de sorry desaparece, `apply?` cerró de verdad."""
        _, c, _ = self._corre({"env": 2, "messages": [
            {"severity": "info", "data": _MARCA + "apply?"}]})
        assert c[0].cerrado and c[0].ganadora == "apply?"

    def test_si_no_elabora_no_se_busca(self):
        from nucleo.lean.cascada_sesion import cerrar_sorries_por_comando
        s = _sesion_falsa([{"messages": [{"severity": "error", "data": "boom"}]}])
        cierres, err = cerrar_sorries_por_comando(s, self._COD, "rfl")
        assert cierres == [] and "boom" in err
