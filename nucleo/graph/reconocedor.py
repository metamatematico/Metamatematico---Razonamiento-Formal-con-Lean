# -*- coding: utf-8 -*-
"""Qué área del grafo abre un enunciado, decidido por su forma y sus palabras.

El emparejador léxico compara la consulta con 3 839 palabras clave escritas a
mano, y 15 de 24 consultas reales no activan nada: `(a+b)^2 = a^2+2ab+b^2` no
contiene ni una de esas palabras. Toda su señal está en la FORMA.

Aquí entra el reconocedor entrenado en `scripts/entrenar_reconocedor.py`. Sobre
los 7 temas reales de MATH, con el peso elegido en validación:

    modelo nulo                     23,8 %
    sólo símbolos                   60,4 %
    sólo palabras                   73,9 %
    los dos, w=0,4                  75,4 %   (equilibrada 75,9 %)

Y los símbolos no llevan idioma: el corpus es inglés y las consultas del sistema
son español.

QUE HACE Y QUE NO. Devuelve un ÁREA, no una skill. El área es la puerta: desde
ella se navega el grafo, que después de arreglarla poda a 10 nodos de mediana en
vez de a 127. Nunca sustituye al emparejador léxico —que está medido en 17,1 %
de precisión contra ProofNet frente a un nulo de 1,1 %—: sólo actúa donde aquel
se queda mudo.

EL MAPA TEMA -> ÁREA ES UN JUICIO. Los temas de MATH y las áreas del grafo son
taxonomías distintas hechas por gente distinta; que `math_precalculus` abra
análisis y álgebra lineal es una decisión, no un dato. Va marcada como tal, igual
que `_AREA_DE_DATA`.
"""
from __future__ import annotations

import io
import logging
import os
import pickle
from typing import Optional

logger = logging.getLogger(__name__)

MODELO = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__)))), "data", "reconocedor_area.pkl")

#: Tema de MATH -> áreas del grafo que abre. JUICIO CURADO, no derivado.
#: Un tema puede abrir más de una puerta: los problemas de precálculo de MATH
#: mezclan trigonometría, vectores y matrices, y eso vive en dos áreas.
TEMA_A_AREAS = {
    "math_algebra": ("area-algebra",),
    "math_intermediate_algebra": ("area-algebra", "area-ringtheory"),
    "math_prealgebra": ("area-numbertheory", "area-algebra"),
    "math_number_theory": ("area-numbertheory",),
    "math_precalculus": ("area-analysis", "area-linearalgebra"),
    "math_counting_and_probability": ("area-combinatorics", "area-probability"),
    "math_geometry": ("area-geometry",),
}

_CACHE = None
_INTENTADO = False


def _cargar():
    """El modelo, una vez. Si no está, el sistema sigue sin él."""
    global _CACHE, _INTENTADO
    if _INTENTADO:
        return _CACHE
    _INTENTADO = True
    try:
        with io.open(MODELO, "rb") as fh:
            _CACHE = pickle.load(fh)
    except Exception as exc:                      # noqa: BLE001
        # Entrenarlo necesita el corpus en E:, que no está en el despliegue.
        # Sin modelo el emparejador léxico funciona igual que antes.
        logger.info("reconocedor de área no disponible: %s", exc)
        _CACHE = None
    return _CACHE


def _cobertura_lexica(texto: str, m) -> float:
    """Qué fracción de las palabras del texto conoce el modelo de palabras.

    Es el detector de idioma más honesto que hay aquí: no adivina qué lengua
    es, mide si este modelo concreto tiene algo que decir sobre estas palabras.
    """
    import re
    palabras = [w.lower() for w in
                re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+", texto or "")]
    if not palabras:
        return 0.0
    voc = m["vP"].vocabulary_
    return sum(1 for w in palabras if w in voc) / len(palabras)


def _normaliza(d):
    return (d - d.mean(1, keepdims=True)) / (d.std(1, keepdims=True) + 1e-9)


def tema_de(texto: str) -> Optional[tuple[str, float]]:
    """El tema más probable del enunciado, con su margen sobre el segundo.

    El margen sirve para no abrir una puerta cuando el modelo duda: dos temas
    empatados no informan, y meter un área equivocada en el contexto es peor
    que no meter ninguna.
    """
    m = _cargar()
    if not m or not (texto or "").strip():
        return None
    try:
        from scripts.entrenar_reconocedor import solo_palabras, solo_simbolos
    except Exception:                             # noqa: BLE001
        # el paquete `scripts` no siempre es importable; se repiten aquí
        import re
        _P = re.compile(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]+")
        solo_simbolos = lambda t: _P.sub(" ", t)          # noqa: E731
        solo_palabras = lambda t: " ".join(_P.findall(t))  # noqa: E731
    try:
        dS = _normaliza(m["mS"].decision_function(
            m["vS"].transform([solo_simbolos(texto)])))
        # SI LAS PALABRAS NO SON DEL IDIOMA DEL MODELO, QUE NO VOTEN.
        #
        # El modelo de palabras se entrenó en inglés. Ante una consulta en
        # español casi ningún rasgo se activa, la puntuación se aplana y gana
        # el prior: TODO acababa clasificado como `math_algebra`, que es la
        # clase mayoritaria. Medido, cobertura del vocabulario:
        #
        #     consultas en español       0 % – 29 %
        #     MATH en inglés, mediana         80,6 %   (7 de 400 bajo el 40 %)
        #
        # Por debajo del umbral se usan SOLO los símbolos, que no tienen
        # idioma y valen el 60,4 % por sí solos frente a un nulo del 23,8 %.
        # Es peor que el 75,4 % de las dos vías, y mucho mejor que responder
        # siempre «álgebra».
        if _cobertura_lexica(texto, m) < 0.40:
            d = dS[0]
        else:
            dP = _normaliza(m["mP"].decision_function(
                m["vP"].transform([solo_palabras(texto)])))
            d = (dP + m["w"] * dS)[0]
    except Exception as exc:                      # noqa: BLE001
        logger.debug("reconocedor falló: %s", exc)
        return None
    orden = d.argsort()[::-1]
    margen = float(d[orden[0]] - d[orden[1]]) if len(orden) > 1 else 1.0
    return m["clases"][orden[0]], margen


def areas_de(texto: str, margen_minimo: float = 1.0) -> list[str]:
    """Las áreas del grafo que abre este enunciado, o ninguna.

    `margen_minimo` es la distancia que se le exige al tema ganador sobre el
    segundo. Por debajo, el reconocedor CALLA: un área equivocada en el contexto
    es peor que ninguna, porque el modelo se la cree.

    EL UMBRAL ESTÁ CALIBRADO, no elegido a ojo. Medido sobre las 5 750 de MATH
    con sólo símbolos, que es el caso peor —el que aplica a las consultas en
    español—:

        margen  0,00–0,25    n=  835    35,6 %
        margen  0,25–0,50    n=  767    42,2 %
        margen  0,50–1,00    n= 1332    53,4 %
        margen  >= 1,00      n= 2816    76,0 %   <- aquí

    Con 1,0 habla en la mitad de las consultas y acierta 3 de cada 4, contra un
    modelo nulo del 23,8 %. La primera versión puso 0,25 a ojo, y ahí el modelo
    acierta menos de la mitad de las veces que abre la boca.

    Y hay un patrón detrás: la exactitud sube con la DENSIDAD DE NOTACIÓN —del
    41,8 % en el quinto con más palabras al 72,0 % en el que tiene más
    símbolos—. Es coherente con lo que este modelo es: un lector de la forma.
    Cuando el enunciado no tiene forma que leer, calla, y hace bien.
    """
    r = tema_de(texto)
    if not r:
        return []
    tema, margen = r
    if margen < margen_minimo:
        return []
    return list(TEMA_A_AREAS.get(tema, ()))


def disponible() -> bool:
    return _cargar() is not None
