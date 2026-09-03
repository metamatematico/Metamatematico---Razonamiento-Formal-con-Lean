# -*- coding: utf-8 -*-
"""Las consultas llegan en español; todo lo demás del sistema está en inglés.

QUE HAY DEBAJO. Los alumnos preguntan en español. El grafo compara contra 3 839
palabras clave mayormente inglesas, los 183 433 hechos de Mathlib son inglés,
los ejemplos few-shot de miniF2F son inglés y el reconocedor de área se entrenó
con MATH, que es inglés. Medido:

    el emparejador léxico se queda mudo en  27 %  de las consultas en español
                                y sólo en   8,4 % de las de ProofNet (inglesas)

Así que el español se traduce ANTES de entrar, y el inglés pasa directo.

EL TRADUCTOR ES LOCAL. `Helsinki-NLP/opus-mt-es-en`, 74 M de parámetros,
preparado por `scripts/preparar_traductor.py`. Sin API, sin coste por consulta,
sin red una vez convertido.

LA NOTACION SE PROTEGE, Y NO ES OPCIONAL. Medido sobre el modelo desnudo:

    $x^2 - 5x + 6$        ->  $x^2 - 5x + $6        (el delimitador se mueve)
    \\mathbb{R}$           ->  \\mathbb{R$            (se pierde la llave)
    \\int_0^\\infty ... dx$ ->  int_0=infty ... dx$   (destruido)
    \\sin x                ->  \\without x            (!)

El último lo explica todo: `\\sin` es el seno, pero «sin» en español es una
preposición y el traductor la traduce. Un modelo de traducción general no
distingue notación de prosa, así que la notación se saca del texto antes, se
sustituye por marcas que sobreviven al tokenizador, y se vuelve a poner después.
"""
from __future__ import annotations

import logging
import os
import re
from typing import Optional

logger = logging.getLogger(__name__)

MODELO = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "data", "traductor-es-en")

#: Lo que NO se traduce. En este orden: primero los bloques delimitados, luego
#: los comandos sueltos, para que `\int` dentro de `$...$` no se marque dos
#: veces. Se incluyen los comandos fuera de `$` porque los alumnos escriben
#: `demuestra que \sin x < x` sin dólares.
NOTACION = re.compile(
    r"\$\$.+?\$\$"           # $$ ... $$
    r"|\$[^$\n]+?\$"         # $ ... $
    r"|\\\[.+?\\\]"          # \[ ... \]
    r"|\\\(.+?\\\)"          # \( ... \)
    r"|\\[A-Za-z]+"          # \sin, \int, \mathbb ...
    r"|\b\d+(?:[.,]\d+)?\s*[+\-*/^=<>≤≥≠]\s*\S+",   # 2+2, x^2 = 4
    re.S)

#: La marca tiene que sobrevivir al tokenizador de SentencePiece sin partirse
#: ni traducirse. Probadas siete sobre una frase con cinco marcas: `«%d»` se
#: convierte en comillas simples y las pierde las cinco; `QQ%dQQ`, `@%d@`,
#: `[%d]`, `xx%dxx` y ésta vuelven las cinco.
#:
#: Se elige `MTH<n>MTH` y se lee con un patrón TOLERANTE, porque el modelo
#: duplica letras en los bordes: con `QQ%dQQ` salía `$p$Q order group`, una Q
#: suelta metida en el texto. Con tres letras distintas el patrón las absorbe
#: sin ambigüedad, y lo que quede de una marca rota se borra en vez de quedarse.
_MARCA = "MTH%dMTH"
_MARCA_RE = re.compile(r"M+T+H+\s*(\d+)\s*M*T*H+")
_RESTO_RE = re.compile(r"M+T+H+\d*|M*T*H+\d+M*T*H*")

#: Señales de castellano, en DOS PESOS. No se adivina el idioma en general: se
#: pregunta si ESTE texto trae señales de español, que es lo único que hay que
#: decidir aquí.
#:
#: FUERTES: no existen en inglés, y una sola basta. Hizo falta separarlas
#: porque `Calcula $\int_0^\infty ...$` se quedaba sin traducir — al quitar la
#: notación sólo sobrevivía una palabra y el umbral de dos no se alcanzaba.
_ES_FUERTE = re.compile(
    r"[¿¡ñáéíóúÁÉÍÓÚÑ]"
    r"|\b(?:demuestra|demostrar|demuestre|prueba|probar|pruebe|calcula"
    r"|calcular|calcule|encuentra|encontrar|halla|hallar|resuelve|resolver"
    r"|cuantos|cuantas|cuales|donde|entonces|numero|numeros|grupo|grupos"
    r"|anillo|cuerpo|conjunto|conjuntos|funcion|ecuacion|teorema|dado|dada"
    r"|sea|sean|siendo|tambien|ademas|raiz|suma|resta|producto)\b", re.I)

#: DEBILES: aparecen sueltas en textos ingleses —`no`, `si`, `a`, `la`— así que
#: hacen falta dos DISTINTAS para que cuenten.
_ES_DEBIL = re.compile(
    r"\b(?:el|la|los|las|un|una|unos|unas|del|que|para|con|por|sin|es|son"
    r"|todo|toda|todos|todas|si|no|al|se|su|sus|mas|menos|de|y|o)\b", re.I)

_CACHE = None
_INTENTADO = False


def es_espanol(texto: str, minimo_debiles: int = 2) -> bool:
    """¿Trae este texto señales de castellano?

    Una señal FUERTE basta: no existen en inglés. De las débiles hacen falta
    dos distintas, porque `no`, `si`, `a` y `la` aparecen sueltas en textos
    ingleses y traducir de inglés a inglés estropea más de lo que arregla.

    Se mira el texto SIN la notación: `$\\sin x$` trae una «sin» que no es la
    preposición, y ese mismo choque es el que hace que el traductor convierta
    `\\sin x` en `\\without x` si no se protege.
    """
    limpio = NOTACION.sub(" ", texto or "")
    if _ES_FUERTE.search(limpio):
        return True
    debiles = set(m.group(0).lower() for m in _ES_DEBIL.finditer(limpio))
    return len(debiles) >= minimo_debiles


def _cargar():
    global _CACHE, _INTENTADO
    if _INTENTADO:
        return _CACHE
    _INTENTADO = True
    try:
        from transformers import MarianMTModel, MarianTokenizer
        tok = MarianTokenizer.from_pretrained(MODELO)
        mod = MarianMTModel.from_pretrained(MODELO)
        mod.eval()
        _CACHE = (tok, mod)
    except Exception as exc:                      # noqa: BLE001
        # Sin traductor el sistema funciona como antes: peor en español.
        logger.info("traductor es→en no disponible: %s", exc)
        _CACHE = None
    return _CACHE


def proteger(texto: str) -> tuple[str, list[str]]:
    """Saca la notación y deja marcas en su sitio."""
    piezas: list[str] = []

    def guarda(m):
        piezas.append(m.group(0))
        return " " + (_MARCA % (len(piezas) - 1)) + " "

    return NOTACION.sub(guarda, texto or ""), piezas


def restaurar(texto: str, piezas: list[str]) -> str:
    """Devuelve la notación a su sitio. Lo que falte se añade al final.

    Un traductor puede PERDER una marca. Perder notación en silencio sería
    peor que no traducir, así que lo que no vuelva se pega detrás: el
    emparejador y el LLM lo siguen viendo.
    """
    vistas = set()

    def pon(m):
        i = int(m.group(1))
        vistas.add(i)
        return piezas[i] if 0 <= i < len(piezas) else ""

    fuera = _MARCA_RE.sub(pon, texto)
    fuera = _RESTO_RE.sub("", fuera)   # restos de marca rota
    perdidas = [p for i, p in enumerate(piezas) if i not in vistas]
    if perdidas:
        fuera = fuera.rstrip() + " " + " ".join(perdidas)
    return re.sub(r"\s{2,}", " ", fuera).strip()


def traducir(texto: str) -> Optional[str]:
    """El texto en inglés, o None si no hay traductor."""
    m = _cargar()
    if not m or not (texto or "").strip():
        return None
    tok, mod = m
    protegido, piezas = proteger(texto)
    try:
        import torch
        lote = tok([protegido], return_tensors="pt", padding=True,
                   truncation=True, max_length=512)
        with torch.no_grad():
            salida = mod.generate(**lote, max_new_tokens=256, num_beams=4)
        crudo = tok.batch_decode(salida, skip_special_tokens=True)[0]
    except Exception as exc:                      # noqa: BLE001
        logger.debug("traducción falló: %s", exc)
        return None
    return restaurar(crudo, piezas)


def al_ingles(texto: str) -> tuple[str, bool]:
    """El texto listo para el resto del sistema, y si se tradujo.

    Si ya viene en inglés pasa directo: traducir de inglés a inglés sólo mete
    ruido. Si no hay traductor, también pasa directo — peor, pero igual que
    antes de que esto existiera.
    """
    if not es_espanol(texto):
        return texto, False
    fuera = traducir(texto)
    if not fuera:
        return texto, False
    return fuera, True


def disponible() -> bool:
    return _cargar() is not None
