# -*- coding: utf-8 -*-
"""La cascada en un compilado, y los dos fallos que casi la dan por buena.

QUE CAMBIO
----------
Cada tactica costaba un proceso de Lean entero. El coste no esta en la
tactica: esta en arrancar Lean y elaborar los imports, ~15 s cada vez. Con
`first | t1 | t2 | ...` las doce caben en un compilado.

Medido de punta a punta contra Lean, mismos casos por las dos vias:

    posicion de la ganadora    bucle      un compilado
    1a  (rfl)                   15,8 s        15,9 s     sin ganancia
    4a  (ring)                  63,6 s        15,9 s     4,0x
    7a  (linarith)             111,4 s        16,5 s     6,8x
    agotada (12)               203,3 s        29,1 s     7,0x

y con VEREDICTO IDENTICO en los cuatro: mismo solver, mismo `solvers_tried`.

LOS DOS FALLOS QUE ESTE FICHERO VIGILA
--------------------------------------
Los dos producian resultados creibles, que es lo que los hacia peligrosos.

1. `first` NO se queda con la primera que cierra: se queda con la primera que
   no lanza excepcion. `norm_num` sobre `a + b = b + a` progresa sin cerrar,
   `first` la acepta y el fichero queda con `unsolved goals`. La cascada
   declaraba agotados casos que el bucle cerraba. `done` lo arregla.

2. `LeanClient._normalize_code` reescribe `"ring_nf;"` metiendo un salto de
   linea. Con `(ring_nf; trace ...)` partia el bloque en dos y Lean daba
   «unexpected identifier». Solo aparecia con la cascada entera, porque
   `ring_nf` es la quinta: probar tactica a tactica no lo delataba.
"""
import pytest

from nucleo.lean.solver_cascade import (
    SOLVER_CASCADE, _MARCA, _bloque_first, CASCADA_EN_UN_COMPILADO)


class TestElBloque:

    def test_esta_activa(self):
        """Si alguien la apaga, que sea a proposito y se vea en el diff."""
        assert CASCADA_EN_UN_COMPILADO is True

    def test_una_rama_por_solver(self):
        b = _bloque_first(SOLVER_CASCADE)
        assert b.count(_MARCA) == len(SOLVER_CASCADE)
        for t, _ in SOLVER_CASCADE:
            assert _MARCA + t in b, "falta la marca de %s" % t

    def test_va_en_una_sola_linea(self):
        """El `sorry` que se sustituye vive dentro de un `by` indentado.

        Un reemplazo de una linea por otra no puede romper la estructura;
        uno multilinea si, y Lean es sensible al espaciado.
        """
        assert "\n" not in _bloque_first(SOLVER_CASCADE)

    def test_toda_rama_exige_cerrar(self):
        """EL FALLO 1. Sin `done`, `first` acepta la primera que no falla.

        `norm_num` sobre `a + b = b + a` progresa sin cerrar el objetivo.
        Sin `done`, `first` se queda con ella y el teorema sale con
        `unsolved goals` — o sea, la cascada declara agotado un caso que el
        bucle cerraba con `ring`. Mismo tiempo, mismo formato, veredicto
        distinto.
        """
        b = _bloque_first(SOLVER_CASCADE)
        for rama in b.replace("first | ", "").split(" | "):
            assert " done ; " in rama, (
                "rama sin `done`, aceptara tacticas que no cierran: %s" % rama)

    def test_sobrevive_a_la_normalizacion_del_cliente(self):
        """EL FALLO 2. `_normalize_code` reescribe `ring_nf;` con un salto.

        Si este test falla es porque alguien añadio una regla a
        `_DEPRECATED_LEMMAS` que vuelve a partir el bloque. El sintoma en
        produccion seria «unexpected identifier» solo cuando la cascada corre
        entera, que es dificil de atribuir.
        """
        from nucleo.lean.client import LeanClient
        bloque = _bloque_first(SOLVER_CASCADE)
        code = ("import Mathlib.Tactic\n\n"
                "theorem _t : (2 : Nat) + 2 = 4 := by\n  %s\n" % bloque)
        salida = LeanClient()._normalize_code(code)
        conas = [l for l in salida.splitlines() if "first |" in l]
        assert len(conas) == 1, (
            "el bloque quedo partido en %d lineas por _normalize_code"
            % len(conas))
        assert conas[0].count(_MARCA) == len(SOLVER_CASCADE), (
            "se perdieron ramas al normalizar: %d de %d"
            % (conas[0].count(_MARCA), len(SOLVER_CASCADE)))

    def test_ninguna_rama_choca_con_las_reescrituras(self):
        """Generaliza el fallo 2 a toda la tabla, no solo a `ring_nf;`."""
        from nucleo.lean.client import LeanClient
        bloque = _bloque_first(SOLVER_CASCADE)
        for viejo, nuevo in LeanClient._DEPRECATED_LEMMAS:
            if "\n" not in nuevo:
                continue
            assert viejo not in bloque, (
                "la rama contiene %r, que _normalize_code parte en lineas"
                % viejo)


class TestElParseoDelGanador:

    def test_se_lee_del_mensaje_y_no_del_json(self):
        """`output` son lineas JSON: partirlas por la marca daba basura.

        El nombre de la tactica salia como `rfl","endPos":{"column":22,...`.
        El mensaje trae el texto limpio en `data`.
        """
        import asyncio
        from nucleo.lean.client import LeanResult, LeanResultStatus
        from nucleo.lean.solver_cascade import SolverCascade

        class _Falso:
            async def check_code(self, code):
                return LeanResult(
                    status=LeanResultStatus.SUCCESS,
                    messages=[{"severity": "information",
                               "data": _MARCA + "linarith"}],
                    output='{"data":"%slinarith","endPos":{"column":22}}'
                           % _MARCA)

        casc = SolverCascade(_Falso())
        code = "theorem _t : True := by\n  sorry\n"
        r = asyncio.run(casc.try_fill_sorry(code, 2))
        assert r.success
        assert r.solver == "linarith", "solver mal parseado: %r" % r.solver
        assert r.solvers_tried == [t for t, _ in SOLVER_CASCADE].index(
            "linarith") + 1
