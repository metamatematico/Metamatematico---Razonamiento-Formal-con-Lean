# -*- coding: utf-8 -*-
"""Normalizacion de texto para emparejar consultas con el grafo.

POR QUE EXISTE ESTE MODULO
--------------------------
El emparejador consulta->concepto era una bolsa de palabras que partia por
espacios y comparaba en crudo. Fallaba en dos sitios, los dos medidos:

  · la PUNTUACION. `primo?` no es `primo`, asi que «¿Es 17 un numero primo?»
    no casaba con ninguna skill que declarase `primo` entre sus keywords.
  · los ACENTOS. Las keywords se escribieron sin acentuar —`teoria`,
    `numeros`, `algebra`— y el alumno escribe con ellos. `teoría` no es
    `teoria`.

Las dos fallas comparten causa: se comparaban dos alfabetos distintos. La
correccion no es tocar un lado, es NORMALIZAR LOS DOS con la misma funcion.
Normalizar solo la consulta empeora las cosas, porque entonces `teoria` de la
consulta deja de casar con una keyword que si llevara acento.

QUE NO HACE
-----------
No hace stemming ni lematizacion. `primos` seguira sin casar con `primo`. Eso
es un cambio con efecto medible sobre la precision y necesita su propia
medicion; aqui solo se arregla lo que es puro ruido de codificacion.
"""
from __future__ import annotations

import re
import unicodedata

#: Todo lo que no sea letra o digito separa palabras. Incluye la apertura de
#: interrogacion y exclamacion del español, que `str.split()` dejaba pegada.
_SEPARADOR = re.compile(r"[^0-9a-zñ]+")


def sin_acentos(texto: str) -> str:
    """`teoría` -> `teoria`. Descompone y tira las marcas combinantes.

    La `ñ` se conserva: es una letra del alfabeto español, no una `n` con
    tilde, y `año` -> `ano` cambia la palabra. Se protege antes de descomponer
    y se restituye despues.
    """
    protegido = (texto or "").replace("ñ", "\x00").replace("Ñ", "\x01")
    plano = "".join(
        c for c in unicodedata.normalize("NFKD", protegido)
        if not unicodedata.combining(c)
    )
    return plano.replace("\x00", "ñ").replace("\x01", "Ñ")


def normalizar(texto: str) -> str:
    """Minusculas y sin acentos. La forma en que se comparan los dos lados."""
    return sin_acentos((texto or "").lower())


def tokens(texto: str, minimo: int = 3) -> set[str]:
    """Los tokens comparables de un texto.

    `minimo` conserva el criterio que ya tenia el emparejador —descartar
    tokens de 1 y 2 caracteres— porque bajarlo mete `de`, `la` y `en` en cada
    comparacion y eso si mueve la precision.
    """
    return {t for t in _SEPARADOR.split(normalizar(texto)) if len(t) >= minimo}


def contiene_frase(texto_normalizado: str, frase: str) -> bool:
    """¿Aparece `frase` como frase completa, en limites de palabra?

    Se compara sobre texto YA normalizado para no repetir el trabajo en el
    bucle del emparejador, que lo llama una vez por keyword y por skill.
    """
    f = normalizar(frase).strip()
    if not f:
        return False
    return re.search(r"(?<![0-9a-zñ])%s(?![0-9a-zñ])" % re.escape(f),
                     texto_normalizado) is not None
