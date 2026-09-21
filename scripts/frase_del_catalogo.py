# -*- coding: utf-8 -*-
"""Reescribe la frase del catálogo del decisor (§12 del artefacto) desde el decisor.

La frase decía «doce capacidades» con dieciséis en el catálogo: una cifra que
nadie releía cada vez que entraba una capacidad. Ahora se regenera: cada vez
que se añade una, se corre esto, y `scripts/auditar_artefacto.py` comprueba
que el número publicado es el del decisor.

    python -m scripts.frase_del_catalogo
"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

NUM = {1: "una", 2: "dos", 3: "tres", 4: "cuatro", 5: "cinco", 6: "seis",
       7: "siete", 8: "ocho", 9: "nueve", 10: "diez", 11: "once", 12: "doce",
       13: "trece", 14: "catorce", 15: "quince", 16: "dieciséis",
       17: "diecisiete", 18: "dieciocho", 19: "diecinueve", 20: "veinte",
       21: "veintiuna", 22: "veintidós"}


def frase():
    from nucleo.decisor import CAPACIDADES, Contexto, decidir, leer_veredicto
    d = decidir(Contexto(consulta="x", es_matematica=True))
    off = d.apagadas
    por_medicion = [c for c in off if leer_veredicto(c).gana is False]
    sin_cablear = [c for c in off if c.fuera_del_camino and leer_veredicto(c).gana]
    sin_evidencia = [c for c in off if c.evidencia is None]
    por_guarda = [c for c in off if c not in por_medicion + sin_cablear + sin_evidencia]
    assert len(d.activas) + len(off) == len(CAPACIDADES)
    assert (len(por_medicion) + len(sin_cablear) + len(sin_evidencia)
            + len(por_guarda)) == len(off), "los grupos no suman el catálogo"
    w = lambda n: NUM.get(n, str(n))
    s = lambda n, uno, varios: uno if n == 1 else varios
    return (f"""    <p>El catálogo tiene {w(len(CAPACIDADES))} capacidades. Ante una consulta matemática
    con Lean disponible corren {w(len(d.activas))}; {w(len(por_medicion))} {s(len(por_medicion), 'está apagada', 'están apagadas')}
    porque no {s(len(por_medicion), 'bate', 'baten')} a su nulo; {w(len(sin_cablear))} {s(len(sin_cablear), 'bate al suyo y no está cableada', 'baten al suyo y no están cableadas')},
    porque por el camino real no {s(len(sin_cablear), 'paga', 'pagan')}; {w(len(por_guarda))} {s(len(por_guarda), 'depende', 'dependen')} de
    la consulta, porque su guarda sólo aplica a algunas; y {w(len(sin_evidencia))}
    no tienen medición contra un nulo —entre ellas el emparejador semántico, que nunca
    llegó a producción y se conserva a propósito: <strong>un candidato evaluado
    y descartado es información</strong>, y borrarlo invita a reinventarlo—, y
    <code>lazo_por_pasos</code>, el paso 3 del lazo (<a href="#lazo">§18</a>), cuya
    puerta con modelo no se ha corrido.</p>""")


def main():
    f = os.path.join(RAIZ, "docs", "arquitectura_nle.html")
    t = io.open(f, encoding="utf-8").read()
    patron = re.compile(r"    <p>El catálogo tiene [\s\S]*?</p>")
    if len(patron.findall(t)) != 1:
        print("no se encuentra exactamente una frase del catálogo")
        return 1
    t = patron.sub(lambda m: frase(), t)
    io.open(f, "w", encoding="utf-8", newline="").write(t)
    print(frase())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
