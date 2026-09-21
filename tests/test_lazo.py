# -*- coding: utf-8 -*-
"""El lazo por pasos: filtros, retroalimentación y la búsqueda del mediador.

El mediador se prueba con una SESIÓN DE MENTIRA de transiciones guionizadas:
`(estado, táctica) -> resultado`. Lo que se vigila aquí es la lógica de la
búsqueda —frontera, confluencias, ciclos, tope agotado, presupuesto,
ensamblado— y no Lean. Que las flechas sean reales lo decide Lean: lo mide
`scripts/lazo_por_pasos.py`.
"""
import asyncio

import pytest

from nucleo.lazo import filtros, retro
from nucleo.lazo.mediador import Mediador, Nodo, Presupuesto, clave_de
from nucleo.lazo.proponentes import Guionado
from nucleo.lazo.registro import RegistroEnMemoria
from nucleo.lean.sesion import Respuesta


# ── filtros ──────────────────────────────────────────────────────────────
class TestFiltros:

    @pytest.mark.parametrize("c", ["sorry", "exact sorry", "admit", "apply?",
                                   "native_decide", "rw?"])
    def test_los_atajos_no_llegan_a_lean(self, c):
        assert filtros.revisar(c).motivo == "atajo"

    def test_una_palabra_que_contiene_sorry_no_es_un_atajo(self):
        assert filtros.revisar("exact my_sorry_lemma") is None

    def test_una_tactica_por_linea(self):
        assert filtros.revisar("intro h\nsimp").motivo == "varias_lineas"

    def test_el_nombre_inexistente_se_para(self):
        r = filtros.revisar("exact Nat.lemma_inventado n", existe=lambda n: False)
        assert r.motivo == "nombre" and r.detalle == "Nat.lemma_inventado"

    def test_el_acceso_a_una_hipotesis_no_es_un_nombre(self):
        estado = "a b : ℝ\nhab : a < b\n⊢ a ≤ b"
        assert filtros.revisar("exact hab.le", estado, existe=lambda n: False) is None

    def test_los_locales_del_estado(self):
        assert filtros.locales_de("a b : ℝ\nh : 0 ≤ a\n⊢ P") == {"a", "b", "h"}


# ── retroalimentación ────────────────────────────────────────────────────
class TestRetro:

    def _nodo(self):
        n = Nodo(id=3, raiz=0, objetivos=["a b : ℝ\n⊢ 2 * a * b ≤ a ^ 2 + b ^ 2"],
                 camino=["intro"], profundidad=1)
        n.fallos.append({"tactica": "linarith", "clase": "fallo",
                         "lean": "linarith failed" + "x" * 1000})
        return n

    def test_los_campos_de_la_propuesta(self):
        r = retro.construir(self._nodo(), k=4, firmas={"sq_nonneg": "(a : R) : 0 ≤ a ^ 2"},
                            ranker=[("nlinarith", 0.41)])
        assert r["estado"]["id"] == 3 and r["camino"] == ["intro"]
        assert r["fallidos_aqui"][0]["tactica"] == "linarith"
        assert len(r["fallidos_aqui"][0]["lean"]) <= retro.RECORTE
        assert r["firmas"] and r["ranker"] == [["nlinarith", 0.41]]

    def test_cada_campo_se_puede_quitar(self):
        """Sin esto no habría ablación de qué campo explica la mejora."""
        r = retro.construir(self._nodo(), campos=("objetivos",))
        assert "camino" not in r and "fallidos_aqui" not in r

    def test_lee_el_json_pedido(self):
        t = '{"candidatos": [{"tactica": "nlinarith [sq_nonneg (a - b)]", "razon": "x"}]}'
        assert retro.leer(t) == ["nlinarith [sq_nonneg (a - b)]"]

    def test_lee_aunque_no_respete_el_formato(self):
        """Perder una respuesta por su formato es perder una llamada pagada."""
        t = "Try these:\n```lean\n- nlinarith\n- positivity\n```"
        assert retro.leer(t) == ["nlinarith", "positivity"]

    def test_no_repite_y_respeta_k(self):
        t = '{"candidatos": ["ring", "ring", "simp", "omega", "linarith", "aesop"]}'
        assert retro.leer(t, k=3) == ["ring", "simp", "omega"]


# ── el mediador, con una sesión de mentira ───────────────────────────────
class _Sesion:
    """Estados por nombre; `trans[(estado, tactica)] -> ('progresa', [objs])`,
    ('cierra',) o ('error', mensaje). Un proofState es un índice a un estado."""

    def __init__(self, raices, trans):
        self.raices = raices          # [(goal, line, col)]
        self.trans = trans
        self.estados = []
        self.cerrada = False

    def _ps(self, objetivos):
        self.estados.append(list(objetivos))
        return len(self.estados) - 1

    def comando(self, codigo, env=None):
        sorries = [{"proofState": self._ps([g]), "goal": g,
                    "pos": {"line": l, "column": c}} for g, l, c in self.raices]
        return Respuesta("progresa", sorries=sorries, env=2)

    def tactica(self, t, ps, tope=None):
        objs = self.estados[ps]
        r = self.trans.get((objs[0], t))
        if r is None:
            return Respuesta("error", mensajes=[{"severity": "error", "data": "falla"}])
        if r[0] == "cierra":
            return Respuesta("cierra", proof_state=self._ps([]))
        if r[0] == "progresa":
            return Respuesta("progresa", proof_state=self._ps(r[1]), objetivos=list(r[1]))
        return Respuesta("error", mensajes=[{"severity": "error", "data": r[1]}])

    def cerrar(self):
        self.cerrada = True


class _Cliente:
    def __init__(self, ok=True):
        self.ok, self.compilado = ok, None

    def _normalize_code(self, c):
        return c

    async def check_code(self, codigo):
        from nucleo.lean.client import LeanResult, LeanResultStatus
        self.compilado = codigo
        return LeanResult(status=LeanResultStatus.SUCCESS if self.ok else LeanResultStatus.ERROR,
                          messages=[] if self.ok else [{"severity": "error", "data": "no"}])


def _corre(sesion, guion, cliente=None, p=None):
    cliente = cliente or _Cliente()
    reg = RegistroEnMemoria("t")
    m = Mediador(lambda cab: (sesion, 1), cliente, [Guionado(guion)],
                 p or Presupuesto(), registro=reg)
    codigo = "theorem t : P := by\n  sorry"
    r = asyncio.new_event_loop().run_until_complete(m.resolver(codigo))
    return r, reg, cliente


class TestMediador:

    def test_un_camino_de_dos_pasos_y_se_ensambla(self):
        s = _Sesion([("⊢ P", 2, 2)], {("⊢ P", "intro h"): ("progresa", ["h : A\n⊢ Q"]),
                                       ("h : A\n⊢ Q", "exact h"): ("cierra",)})
        r, reg, cl = _corre(s, {"⊢ P": ["intro h"], "⊢ Q": ["exact h"]})
        assert r.veredicto == "verificado" and r.caminos == {0: ["intro h", "exact h"]}
        assert cl.compilado.endswith("  intro h; exact h")

    def test_el_fichero_manda_sobre_la_sesion(self):
        """I2: la sesión cerró y el fichero dice que no -> no hay sello."""
        s = _Sesion([("⊢ P", 2, 2)], {("⊢ P", "simp"): ("cierra",)})
        r, _, _ = _corre(s, {"⊢ P": ["simp"]}, cliente=_Cliente(ok=False))
        assert r.veredicto == "rechazado_por_fichero"

    def test_volver_al_mismo_estado_no_avanza(self):
        s = _Sesion([("⊢ P", 2, 2)], {("⊢ P", "skip"): ("progresa", ["⊢ P"])})
        r, reg, _ = _corre(s, {"⊢ P": ["skip"]})
        assert [f["clase"] for f in reg.filas] == ["no_avanza"] and r.nodos == 1

    def test_dos_caminos_al_mismo_estado_confluyen(self):
        s = _Sesion([("⊢ P", 2, 2)], {("⊢ P", "a"): ("progresa", ["⊢ Q"]),
                                       ("⊢ P", "b"): ("progresa", ["⊢ Q"])})
        r, reg, _ = _corre(s, {"⊢ P": ["a", "b"]})
        assert [f["clase"] for f in reg.filas] == ["progresa", "confluye"]
        assert r.confluencias == 1 and r.nodos == 2

    def test_los_atajos_se_filtran_sin_gastar_lean(self):
        s = _Sesion([("⊢ P", 2, 2)], {})
        r, reg, _ = _corre(s, {"⊢ P": ["sorry", "apply?"]})
        assert all(f["clase"] == "filtro:atajo" for f in reg.filas)
        assert r.llamadas_lean == 1          # sólo plantar el teorema

    def test_el_presupuesto_de_lean_se_respeta(self):
        s = _Sesion([("⊢ P", 2, 2)], {})
        r, _, _ = _corre(s, {"⊢ P": ["t%d" % i for i in range(50)]},
                         p=Presupuesto(lean=10))
        assert r.llamadas_lean <= 10 and r.veredicto == "agotado"

    def test_un_tope_agotado_rehace_la_sesion_y_reconstruye_el_nodo(self):
        """El agujero de heartbeats: tras un TIMEOUT se replanta y se sigue."""
        s = _Sesion([("⊢ P", 2, 2)], {("⊢ P", "lenta"): ("error", "TIMEOUT tras 20 s"),
                                       ("⊢ P", "rapida"): ("cierra",)})
        r, reg, _ = _corre(s, {"⊢ P": ["lenta", "rapida"]})
        assert [f["clase"] for f in reg.filas] == ["cara", "cierra"]
        assert r.veredicto == "verificado"

    def test_una_raiz_resuelta_no_se_sigue_buscando(self):
        s = _Sesion([("⊢ P", 2, 2)], {("⊢ P", "a"): ("progresa", ["⊢ Q"]),
                                       ("⊢ P", "b"): ("cierra",),
                                       ("⊢ Q", "c"): ("cierra",)})
        r, reg, _ = _corre(s, {"⊢ P": ["a", "b"], "⊢ Q": ["c"]})
        assert r.caminos == {0: ["b"]}
        assert "c" not in [f["tactica"] for f in reg.filas]

    def test_si_no_elabora_no_se_busca(self):
        class _Rota(_Sesion):
            def comando(self, codigo, env=None):
                return Respuesta("error", mensajes=[{"severity": "error", "data": "x"}])
        r, _, _ = _corre(_Rota([], {}), {})
        assert r.veredicto == "no_elabora"

    def test_la_clave_iguala_nombres_de_hipotesis(self):
        """I3 descansa en `estados.normalizar`: `h` y `hab` son el mismo objeto."""
        assert clave_de(["h : p\n⊢ q"]) == clave_de(["hab : p\n⊢ q"])


def test_un_estado_de_otra_raiz_no_confluye():
    """Dos raíces que pasan por el mismo estado: cada una necesita su camino.

    Con `vistos` común, la segunda raíz marcaba «confluye», no expandía, y se
    quedaba sin cerrar aunque el mismo camino la cerraba.
    """
    s = _Sesion([("⊢ P", 2, 2), ("⊢ R", 3, 2)],
                {("⊢ P", "a"): ("progresa", ["⊢ Q"]), ("⊢ R", "a"): ("progresa", ["⊢ Q"]),
                 ("⊢ Q", "c"): ("cierra",)})
    r, _, _ = _corre(s, {"⊢ P": ["a"], "⊢ R": ["a"], "⊢ Q": ["c"]})
    assert r.cerradas == 2 and r.caminos == {0: ["a", "c"], 1: ["a", "c"]}
