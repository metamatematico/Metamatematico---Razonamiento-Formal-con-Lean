"""
El sistema tiene que saber lo que cuesta.

El cliente LLM capturaba `input_tokens` y `output_tokens` de cada llamada y los
tiraba: nada los sumaba, nada los persistía. Se notó cuando una tanda del banco
de fidelidad se comió el saldo de la API sin que nadie pudiera decir en qué.

Es el mismo patrón contra el que este repo ya tiene una suite entera
(`test_ui_coherencia`): una cifra que importa y que nadie mide. Aquí la cifra
son dólares.
"""
import io
import json
import os

import pytest

from nucleo.llm.contador import Contador, PRECIOS, precio_de, RUTA


@pytest.fixture(autouse=True)
def _limpio():
    """Cada test parte de cero y deja el disco como estaba."""
    previo = io.open(RUTA, encoding="utf-8").read() if os.path.exists(RUTA) else None
    Contador.reiniciar()
    yield
    Contador.reiniciar()
    if previo is not None:
        io.open(RUTA, "w", encoding="utf-8").write(previo)


class TestPrecios:

    def test_los_modelos_actuales_tienen_tarifa(self):
        for m in ("claude-opus-5", "claude-sonnet-5", "claude-haiku-4-5"):
            assert precio_de(m) != (0.0, 0.0), f"{m} sin tarifa"

    def test_la_salida_cuesta_mas_que_la_entrada(self):
        """Importa porque los tokens de PENSAMIENTO se facturan como salida, y
        los modelos actuales piensan por defecto."""
        for m, (entrada, salida) in PRECIOS.items():
            assert salida > entrada, m

    def test_un_id_con_sufijo_de_fecha_cae_al_prefijo(self):
        assert precio_de("claude-opus-5-20260101") == precio_de("claude-opus-5")

    def test_un_modelo_desconocido_no_inventa_precio(self):
        """Devolver 0 es honesto; inventar una tarifa sería peor que no medir."""
        assert precio_de("modelo-que-no-existe") == (0.0, 0.0)


class TestContador:

    def test_calcula_el_coste_de_una_llamada(self):
        # 1M de entrada y 1M de salida en Opus 5 = 5 + 25
        c = Contador.registrar("claude-opus-5", entrada=1_000_000,
                               salida=1_000_000)
        assert c == pytest.approx(30.0)
        assert Contador.total() == pytest.approx(30.0)

    def test_acumula_entre_llamadas_y_modelos(self):
        Contador.registrar("claude-opus-5", 1_000_000, 0)      # 5
        Contador.registrar("claude-sonnet-5", 1_000_000, 0)    # 2
        assert Contador.total() == pytest.approx(7.0)
        assert "claude-opus-5" in Contador.resumen()
        assert "claude-sonnet-5" in Contador.resumen()

    def test_persiste_en_disco(self):
        """De proceso, no de sesión: lo que importa es la factura, no una
        ejecución."""
        Contador.registrar("claude-opus-5", 1_000_000, 0)
        d = json.load(io.open(RUTA, encoding="utf-8"))
        assert d["por_modelo"]["claude-opus-5"]["dolares"] == pytest.approx(5.0)

    def test_el_resumen_cuadra_con_las_partes(self):
        Contador.registrar("claude-opus-5", 500_000, 200_000)
        Contador.registrar("claude-sonnet-5", 300_000, 100_000)
        lineas = Contador.resumen().splitlines()
        total = float(lineas[-1].split()[-1])
        assert total == pytest.approx(Contador.total())

    def test_un_contador_roto_no_tumba_el_sistema(self, monkeypatch):
        """La contabilidad es secundaria: si falla, la respuesta sale igual."""
        monkeypatch.setattr(Contador, "_guardar",
                            classmethod(lambda cls: (_ for _ in ()).throw(IOError)))
        with pytest.raises(IOError):
            Contador._guardar()
        # y el cliente lo envuelve en try/except
        import inspect
        from nucleo.llm import client
        fuente = inspect.getsource(client.LLMClient.generate)
        i = fuente.index("Contador.registrar")
        assert "except Exception" in fuente[i:i + 400]


class TestElEsfuerzoEsUnaPalanca:
    """Los modelos actuales traen pensamiento adaptativo ACTIVO y esfuerzo
    `high` por defecto, y los tokens de pensamiento se facturan como salida.

    Sin fijar `effort`, cada formalización y cada traducción piensan al máximo
    — y ninguna de las dos es una tarea de razonamiento profundo: el trabajo
    duro lo hace Lean, que es gratis.
    """

    def test_hay_campo_effort_con_valor_barato(self):
        from nucleo.llm.client import LLMConfig
        assert hasattr(LLMConfig, "effort")
        assert LLMConfig().effort in ("low", "medium")

    def test_se_pasa_a_la_api(self):
        import inspect
        from nucleo.llm import client
        fuente = inspect.getsource(client.LLMClient.generate)
        assert '"output_config"' in fuente
        assert '"effort"' in fuente

    def test_va_dentro_de_output_config_no_al_nivel_de_arriba(self):
        """`effort` suelto en la llamada es un 400."""
        import inspect
        from nucleo.llm import client
        fuente = inspect.getsource(client.LLMClient.generate)
        assert '_kw["output_config"] = {"effort"' in fuente
