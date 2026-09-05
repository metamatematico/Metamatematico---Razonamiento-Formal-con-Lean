# -*- coding: utf-8 -*-
"""¿Cuánta notación se le escapa al escudo que la protege del traductor?

QUE HAY EN JUEGO
----------------
Las consultas en español se traducen antes de entrar al sistema, y la notación
se saca del texto para que el traductor no la toque. Sin eso, medido en su día
sobre el modelo desnudo:

    \\sin x   ->  \\without x     («sin» es preposición en español)
    $x^2 - 5x + 6$  ->  $x^2 - 5x + $6

El escudo es `traductor.NOTACION`, una regex. Y una regex no reconoce una
expresión, así que lo que no encaje en sus seis alternativas pasa al traductor
sin protección — y el alumno recibe su fórmula rota sin que nadie avise.

LA ASIMETRIA IMPORTA, Y POR ESO LA MEDIDA NO ES SIMETRICA
--------------------------------------------------------
Proteger de más es casi inocuo: un trozo de prosa que no se traduce. Proteger
de menos destruye la fórmula. Así que lo que se cuenta es sólo lo que el
escudo DEJA FUERA de lo que el árbol reconoce como notación.

DOS PARTES
----------
  1. EL MECANISMO, sobre los 23 243 enunciados reales: cuánta notación queda
     expuesta. Es una propiedad de la regex, no depende del idioma.

  2. LA CONSECUENCIA, con el traductor de verdad cargado, sobre consultas en
     español escritas a mano. ESTAS LAS ESCRIBI YO: sirven para enseñar que el
     daño ocurre, no para estimar cada cuánto. La frecuencia sale de (1).
"""
from __future__ import annotations

import argparse
import io
import json
import pathlib
import sys

RAIZ = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))
sys.stdout.reconfigure(encoding="utf-8")

from nucleo.graph.traductor import NOTACION
from nucleo.sintaxis.lexico import extraer

BANCO = RAIZ / "data" / "banco_lemas.jsonl"
SALIDA = RAIZ / "data" / "proteccion_de_notacion.json"

#: Consultas en español con notación, escritas a mano para ver el daño. No son
#: una muestra de nada: son una demostración.
EN_ESPANOL = [
    "Demuestra que ∀x ∈ ℝ, x² ≥ 0",
    "Calcula ∫_0^1 x² dx",
    "Prueba que si a ∣ b y b ∣ c entonces a ∣ c",
    "Sea A ⊆ B y B ⊆ C, demuestra A ⊆ C",
    "Demuestra que ∑_{i=1}^n i = n(n+1)/2",
    "Si f: ℝ → ℝ es continua y f(0) < 0 < f(1), hay un cero",
    "Demuestra que √2 ∉ ℚ",
    "Prueba que (a+b)² = a² + 2ab + b²",
]


def _cubiertos(texto: str) -> set:
    """Los índices de carácter que el escudo protege."""
    fuera = set()
    for m in NOTACION.finditer(texto):
        fuera.update(range(m.start(), m.end()))
    return fuera


def mecanismo(n: int) -> dict:
    textos = []
    with io.open(BANCO, encoding="utf-8") as fh:
        for linea in fh:
            if n and len(textos) >= n:
                break
            nl = (json.loads(linea).get("nl") or "").strip()
            if nl:
                textos.append(nl)

    con_notacion = 0
    con_hueco = 0
    car_notacion = 0
    car_expuestos = 0
    ejemplos: list = []
    for t in textos:
        tramos = extraer(t)
        if not tramos:
            continue
        con_notacion += 1
        prot = _cubiertos(t)
        expuesto = 0
        for tr in tramos:
            idx = set(range(tr.inicio, tr.fin))
            car_notacion += len(idx)
            fuera = idx - prot
            car_expuestos += len(fuera)
            expuesto += len(fuera)
        if expuesto:
            con_hueco += 1
            if len(ejemplos) < 8:
                sueltos = [tr.texto for tr in tramos
                           if set(range(tr.inicio, tr.fin)) - prot]
                ejemplos.append({"consulta": t[:110], "sin_proteger": sueltos[:3]})

    print("MECANISMO — sobre %d enunciados reales" % len(textos))
    print("  con notación reconocida       %6d  (%.1f %%)"
          % (con_notacion, 100 * con_notacion / max(1, len(textos))))
    print("  con notación SIN proteger     %6d  (%.1f %% de los que tienen)"
          % (con_hueco, 100 * con_hueco / max(1, con_notacion)))
    print("  caracteres de notación        %6d" % car_notacion)
    print("  caracteres expuestos          %6d  (%.1f %%)"
          % (car_expuestos, 100 * car_expuestos / max(1, car_notacion)))
    print()
    for e in ejemplos[:5]:
        print("    %s" % e["consulta"])
        print("      -> sin proteger: %s" % e["sin_proteger"])
    return {
        "enunciados": len(textos), "con_notacion": con_notacion,
        "con_hueco": con_hueco, "caracteres_notacion": car_notacion,
        "caracteres_expuestos": car_expuestos,
        "ejemplos": ejemplos,
    }


def consecuencia() -> dict:
    from nucleo.graph.traductor import traducir

    print()
    print("CONSECUENCIA — con el traductor es→en cargado de verdad")
    print("  (estas ocho consultas las escribí yo: enseñan el daño, no su"
          " frecuencia)")
    print()
    filas = []
    rotas = 0
    for q in EN_ESPANOL:
        prot = _cubiertos(q)
        expuestos = [tr.texto for tr in extraer(q)
                     if set(range(tr.inicio, tr.fin)) - prot]
        salida = traducir(q)
        # ¿sobrevivió cada tramo expuesto, carácter a carácter?
        perdidos = [tr for tr in expuestos
                    if tr.replace(" ", "") not in salida.replace(" ", "")]
        if perdidos:
            rotas += 1
        filas.append({"consulta": q, "traducida": salida,
                      "sin_proteger": expuestos, "perdidos": perdidos})
        marca = "ROTA " if perdidos else "  ok "
        print("  %s %s" % (marca, q))
        print("        -> %s" % salida)
        if perdidos:
            print("        se perdió: %s" % perdidos)
    print()
    print("  %d de %d consultas perdieron notación por no estar protegida"
          % (rotas, len(EN_ESPANOL)))
    return {"rotas": rotas, "total": len(EN_ESPANOL), "filas": filas}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--n", type=int, default=0, help="0 = todos")
    ap.add_argument("--sin-traductor", action="store_true")
    ap.add_argument("--salida", default=str(SALIDA))
    a = ap.parse_args()

    fuera = {"mecanismo": mecanismo(a.n)}
    if not a.sin_traductor:
        try:
            fuera["consecuencia"] = consecuencia()
        except Exception as exc:                              # noqa: BLE001
            print("\n  (traductor no disponible: %s)" % exc)
    pathlib.Path(a.salida).write_text(
        json.dumps(fuera, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\nescrito -> %s" % a.salida)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
