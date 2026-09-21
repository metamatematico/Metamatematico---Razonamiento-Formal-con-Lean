# -*- coding: utf-8 -*-
"""Lo que se rechaza antes de gastar una llamada a Lean.

Son los dos invariantes gratuitos de la propuesta:

    I6 · Sin atajos. Un candidato con `sorry`, `admit`, `axiom` o
         `native_decide` no llega a Lean. Tampoco `apply?`: cuando no encuentra
         prueba ADMITE el objetivo con `sorry` —medido sobre `n * n ≠ 2`, el
         REPL devuelve `goals: []` con `proofStatus: "Incomplete: contains
         sorry"`—. Su uso legítimo es leer sus «Try this», que es D2, no un
         candidato del lazo.

    I4 · Ningún nombre inexistente llega a Lean. Todo identificador
         CUALIFICADO del candidato se comprueba contra el índice de Mathlib,
         salvo los que empiezan por una hipótesis del estado (`h.1`, `hab.le`),
         que son locales. Es la clase de fallo más frecuente: el modelo inventa
         21 de cada 28 nombres de memoria.

Un candidato también tiene que ser UNA táctica en UNA línea: es lo que la
retroalimentación pide, y lo que el ensamblado sabe escribir en el sitio de un
`sorry` sin romper el sangrado.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

#: I6. Por palabra, no por subcadena: `sorry_lemma` no es `sorry`.
_ATAJOS = re.compile(r"(?<![\w.'])(sorry|admit|axiom|native_decide|apply\?|rw\?|"
                     r"exact\?\s*says|decide\s*:=\s*true)(?![\w'])")

#: Un identificador cualificado: `Nat.succ_le_iff`, `h.1`, `Real.sqrt_nonneg`.
_CUALIFICADO = re.compile(r"(?<![\w.'])([A-Za-z_][\w']*(?:\.[A-Za-z_\d][\w']*)+)")

#: Nombres de hipótesis en un estado impreso por Lean: `h : …`, `a b : ℝ`.
_HIPOTESIS = re.compile(r"^\s*([^\s:⊢][^:⊢]*?)\s*:", re.M)


@dataclass
class Rechazo:
    motivo: str        # atajo · varias_lineas · vacio · nombre
    detalle: str = ""


def locales_de(estado: str) -> set:
    """Los nombres que el estado declara: hipótesis y variables."""
    fuera = set()
    for m in _HIPOTESIS.finditer(estado or ""):
        for n in m.group(1).split():
            n = n.strip()
            if n and not n.startswith(("⊢", "case")):
                fuera.add(n)
    return fuera


def revisar(candidato: str, estado: str = "",
            existe=None) -> Optional[Rechazo]:
    """None si el candidato puede ir a Lean; si no, por qué no.

    `existe` es la comprobación de nombres (`nucleo.lean.nombres.existe`); se
    pasa para poder probar esto sin cargar el índice de 217 419 nombres.
    """
    c = (candidato or "").strip()
    if not c:
        return Rechazo("vacio")
    if "\n" in c:
        return Rechazo("varias_lineas", c.split("\n", 1)[0][:60])
    m = _ATAJOS.search(c)
    if m:
        return Rechazo("atajo", m.group(1))
    if existe is not None:
        locales = locales_de(estado)
        for n in _CUALIFICADO.findall(c):
            cabeza = n.split(".", 1)[0]
            if cabeza in locales:
                continue          # `h.1`, `hab.le`: acceso a una hipótesis
            if not existe(n):
                return Rechazo("nombre", n)
    return None
