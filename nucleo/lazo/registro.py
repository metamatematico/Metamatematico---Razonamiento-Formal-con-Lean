# -*- coding: utf-8 -*-
"""Cada intento del lazo, aceptado o no, a `data/transiciones_vivas.jsonl`.

Es lo que le faltaba a la categoría de estados: construida desde LeanWorkbook
registra la prueba que alguien escribió y no las que descartó —sólo 72 de
24 752 estados tienen dos tácticas distintas—. El lazo produce justo eso:
alternativas en el mismo estado, con su veredicto. Y con la retroalimentación
partida en campos, la ablación de qué campo explica la mejora sale de aquí.
"""
from __future__ import annotations

import datetime
import io
import json
import os
from typing import Optional


class Registro:
    def __init__(self, ruta: Optional[str] = None, problema: str = ""):
        if ruta is None:
            from nucleo.rutas import RAIZ
            ruta = os.path.join(str(RAIZ), "data", "transiciones_vivas.jsonl")
        self.ruta = ruta
        self.problema = problema
        self.filas: list = []

    def anota(self, **campos) -> None:
        fila = {"problema": self.problema,
                "fecha": datetime.datetime.now().isoformat(timespec="seconds")}
        fila.update(campos)
        self.filas.append(fila)
        try:
            with io.open(self.ruta, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(fila, ensure_ascii=False) + "\n")
        except OSError:
            # sin disco no se pierde la búsqueda: las filas quedan en memoria
            pass


class RegistroEnMemoria(Registro):
    """Para los tests: no toca disco."""

    def __init__(self, problema: str = ""):
        self.ruta = ""
        self.problema = problema
        self.filas = []

    def anota(self, **campos) -> None:
        fila = {"problema": self.problema}
        fila.update(campos)
        self.filas.append(fila)
