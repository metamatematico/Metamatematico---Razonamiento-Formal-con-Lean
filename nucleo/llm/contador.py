# -*- coding: utf-8 -*-
"""
Cuanto cuesta el sistema, medido — no estimado.

El cliente LLM ya capturaba `input_tokens` y `output_tokens` de cada llamada y
los tiraba: nada los sumaba, nada los persistia. El sistema no sabia lo que
costaba, y eso se noto cuando una tanda del banco de fidelidad se comio el
saldo sin que nadie pudiera decir en que.

Es el mismo patron contra el que este repo ya tiene una suite entera: una cifra
que importa y que nadie mide. Aqui la cifra son dolares.

QUE HACE FALTA SABER, y por que no basta con contar llamadas

Los modelos actuales traen PENSAMIENTO ADAPTATIVO activo por defecto, y sus
tokens se facturan como SALIDA. Una llamada corta puede costar diez veces mas
que otra igual de corta si penso mas. Contar llamadas no dice nada; hay que
contar tokens.

    from nucleo.llm.contador import Contador
    Contador.registrar("claude-opus-5", entrada=3200, salida=1800)
    print(Contador.resumen())
"""
from __future__ import annotations

import io
import json
import os
import threading
from dataclasses import dataclass, field

#: Precio por millon de tokens, (entrada, salida). Los de pensamiento van en
#: salida. Fuente: tarifas de la API de Anthropic.
PRECIOS: dict[str, tuple[float, float]] = {
    "claude-fable-5":    (10.0, 50.0),
    "claude-opus-5":     (5.0,  25.0),
    "claude-opus-4-8":   (5.0,  25.0),
    "claude-opus-4-7":   (5.0,  25.0),
    "claude-opus-4-6":   (5.0,  25.0),
    "claude-sonnet-5":   (2.0,  10.0),
    "claude-sonnet-4-6": (3.0,  15.0),
    "claude-haiku-4-5":  (1.0,   5.0),
}

# Ruta relativa al paquete: era absoluta a E:/Metamatematico, y si el proyecto
# se mueve —ya paso una vez— la contabilidad del gasto deja de escribirse sin
# que nadie se entere. Saber lo que cuesta cada consulta fue lo que permitio
# bajarla de $0,59 a $0,096; perderlo en silencio seria caro en los dos
# sentidos.
from nucleo.rutas import dato as _dato

RUTA = str(_dato("uso_llm.json"))


def precio_de(modelo: str) -> tuple[float, float]:
    """Tarifa del modelo. Los IDs con sufijo de fecha caen al prefijo."""
    if modelo in PRECIOS:
        return PRECIOS[modelo]
    for k, v in PRECIOS.items():
        if modelo.startswith(k):
            return v
    return (0.0, 0.0)          # desconocido: no se inventa un precio


@dataclass
class _Uso:
    llamadas: int = 0
    entrada: int = 0
    salida: int = 0
    dolares: float = 0.0


class Contador:
    """Acumulador de gasto, con persistencia y por modelo.

    Es de proceso, no de sesion: los totales se guardan en disco y se suman
    entre arranques, porque lo que importa es la factura, no una ejecucion.
    """

    _lock = threading.Lock()
    _por_modelo: dict[str, _Uso] = {}
    _cargado = False

    # ── persistencia ──────────────────────────────────────────────────────

    @classmethod
    def _cargar(cls) -> None:
        if cls._cargado:
            return
        cls._cargado = True
        if not os.path.exists(RUTA):
            return
        try:
            d = json.load(io.open(RUTA, encoding="utf-8"))
            for m, u in d.get("por_modelo", {}).items():
                cls._por_modelo[m] = _Uso(**u)
        except Exception:
            pass                # un contador roto no puede tumbar el sistema

    @classmethod
    def _guardar(cls) -> None:
        try:
            os.makedirs(os.path.dirname(RUTA), exist_ok=True)
            io.open(RUTA, "w", encoding="utf-8").write(json.dumps(
                {"por_modelo": {m: vars(u) for m, u in cls._por_modelo.items()}},
                ensure_ascii=False, indent=2))
        except Exception:
            pass

    # ── API ───────────────────────────────────────────────────────────────

    @classmethod
    def registrar(cls, modelo: str, entrada: int, salida: int) -> float:
        """Suma una llamada. Devuelve lo que costo, en dolares."""
        pe, ps = precio_de(modelo)
        coste = entrada / 1e6 * pe + salida / 1e6 * ps
        with cls._lock:
            cls._cargar()
            u = cls._por_modelo.setdefault(modelo, _Uso())
            u.llamadas += 1
            u.entrada += entrada
            u.salida += salida
            u.dolares += coste
            cls._guardar()
        return coste

    @classmethod
    def total(cls) -> float:
        with cls._lock:
            cls._cargar()
            return sum(u.dolares for u in cls._por_modelo.values())

    @classmethod
    def resumen(cls) -> str:
        with cls._lock:
            cls._cargar()
            if not cls._por_modelo:
                return "sin llamadas registradas"
            lineas = ["%-20s %7s %10s %10s %9s"
                      % ("modelo", "llamadas", "entrada", "salida", "USD")]
            for m, u in sorted(cls._por_modelo.items()):
                lineas.append("%-20s %7d %10d %10d %9.4f"
                              % (m, u.llamadas, u.entrada, u.salida, u.dolares))
            lineas.append("%-20s %7d %10d %10d %9.4f" % (
                "TOTAL",
                sum(u.llamadas for u in cls._por_modelo.values()),
                sum(u.entrada for u in cls._por_modelo.values()),
                sum(u.salida for u in cls._por_modelo.values()),
                sum(u.dolares for u in cls._por_modelo.values())))
            return "\n".join(lineas)

    @classmethod
    def reiniciar(cls) -> None:
        """Pone el contador a cero. Solo a peticion explicita."""
        with cls._lock:
            cls._por_modelo = {}
            cls._cargado = True
            cls._guardar()
