# -*- coding: utf-8 -*-
"""Las aristas que no hay que curar: `viejo -> nuevo`, cosechadas de Mathlib.

DE DONDE SALE ESTA IDEA
-----------------------
`scripts/techo_de_la_restriccion.py` midio que el modelo casi no ALUCINA
nombres: CITA VERSIONES ANTERIORES de Mathlib. De las seis invenciones
distintas que encontro en 66 formalizaciones grabadas, cuatro eran renombrados
reales de la biblioteca:

    Real.not_summable_one_div_nat_cast  ->  ...natCast
    Nat.prime_of_mem_factors            ->  ...prime_of_mem_primeFactors
    Real.not_summable_iff_tendsto_nat_  ->  sin el namespace `Real`
    isCyclic_of_subgroup_isCyclic       ->  ...isDomain

Y Mathlib lleva esa tabla escrita: 2 507 `alias`, de los cuales 1 766 van
marcados `@[deprecated]`. Es una arista `viejo -> nuevo` por cada uno, exacta,
y que NADIE tiene que curar a mano. Es el grafo creciendo por observacion en
vez de por juicio — el mismo movimiento que dio el mejor resultado de esta
familia (L4: coocurrencia sobre 40 025 teoremas que Lean acepto).

QUE SE MIDE, Y CONTRA QUE
-------------------------
La pregunta no es «¿cuantos alias hay?» sino «¿cubren lo que el modelo
escribe mal?». Y el nulo NO es no hacer nada: ya existe una via que acierta el
38,5 % de esas invenciones, `nombres.parecidos`, por distancia de edicion.

    real   la tabla de renombrados: `viejo` esta, luego `nuevo`
    nulo   la distancia de edicion, que ya esta medida en 38,5 %

Si la tabla no bate a la distancia de edicion, no aporta: el parecido
ortografico ya estaba capturando el renombrado, porque un renombrado SE
PARECE a su original. Esa es justo la sospecha que hay que despejar, y es la
razon de que este guion exista en vez de dar por buena la idea.

LA ALARMA, DECLARADA ANTES DE MIRAR
------------------------------------
  · si la cobertura de la tabla sobre las invenciones reales es 0, la cosecha
    es grande y no sirve para este fallo;
  · si es identica a la de la distancia de edicion, no aporta informacion
    nueva — el renombrado se parece a su original por construccion;
  · y si la tabla propone un destino que TAMPOCO existe en el indice, esta
    mal cosechada: un alias apunta a algo que Mathlib define.

No gasta API ni Lean.
"""
from __future__ import annotations

import collections
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

MATHLIB = os.path.join(RAIZ, ".lake", "packages", "mathlib", "Mathlib")
SALIDA = os.path.join(RAIZ, "data", "renombrados.json")

#: `alias viejo := nuevo`, con el `@[deprecated ...]` de la linea anterior si
#: lo lleva. Se aceptan las dos formas que Mathlib usa —`:=` y `=`— y varios
#: nombres a la izquierda separados por comas.
_ALIAS = re.compile(
    r"^\s*alias\s+([A-Za-z_][\w'.]*(?:\s*,\s*[A-Za-z_][\w'.]*)*)"
    r"\s*:?=\s*([A-Za-z_][\w'.]*)", re.M)
#: el atributo puede ir en su propia linea justo encima
_DEPRECADO = re.compile(r"@\[deprecated")

#: `@[to_additive nombre]` sobre un teorema multiplicativo GENERA el aditivo.
#:
#: Y ESE NOMBRE NO ESTA EN NINGUNA DECLARACION DEL FUENTE: lo crea el
#: elaborador. El indice de 217 419 nombres se construye escaneando
#: declaraciones, asi que se los pierde TODOS. Medido: de los 826 nombres que
#: Mathlib escribe explicitamente en este atributo, el indice no conoce 686
#: —el 83 %—, y esos son solo la punta: hay 14 273 atributos `to_additive` en
#: total, y la mayoria no lleva el nombre escrito porque Lean lo deriva.
#:
#: Consecuencia en produccion: el sistema puede decirle al alumno que
#: `finsum_pos` no existe en Mathlib. Existe — lo genera `@[to_additive
#: finsum_pos]` sobre `one_lt_finprod`.
_TO_ADDITIVE = re.compile(
    r"@\[to_additive\s+(?:existing\s+)?([a-zA-Z_][A-Za-z0-9_'.]*)")
#: palabras que son OPCIONES del atributo, no nombres generados
_NO_ES_NOMBRE = frozenset({"existing", "self", "attr", "reorder", "simp",
                           "norm_cast", "elab_as_elim", "gcongr", "aesop"})


def cosechar_to_additive() -> set:
    """Los nombres que `@[to_additive]` genera y el indice no tiene."""
    fuera = set()
    for raiz, _, ficheros in os.walk(MATHLIB):
        for f in ficheros:
            if not f.endswith(".lean"):
                continue
            try:
                txt = io.open(os.path.join(raiz, f), encoding="utf-8").read()
            except OSError:
                continue
            if "to_additive" not in txt:
                continue
            for m in _TO_ADDITIVE.finditer(txt):
                n = m.group(1)
                if n not in _NO_ES_NOMBRE:
                    fuera.add(n)
    return fuera


def _namespace_vigente(txt: str, pos: int) -> str:
    """El `namespace` abierto en ese punto del fichero.

    UN ALIAS DENTRO DE `namespace Nat` DECLARA `Nat.viejo`, NO `viejo`. Sin
    esto la tabla queda con las claves a medias y no casa con lo que el modelo
    escribe, que sí va cualificado.
    """
    pila = []
    for m in re.finditer(r"^\s*(namespace|end)\s+([A-Za-z_][\w'.]*)",
                         txt[:pos], re.M):
        if m.group(1) == "namespace":
            pila.append(m.group(2))
        elif pila and pila[-1] == m.group(2):
            pila.pop()
    return ".".join(pila)


def cosechar() -> tuple:
    pares, deprecados = {}, 0
    n_fich = 0
    for raiz, _, ficheros in os.walk(MATHLIB):
        for f in ficheros:
            if not f.endswith(".lean"):
                continue
            n_fich += 1
            try:
                txt = io.open(os.path.join(raiz, f), encoding="utf-8").read()
            except OSError:
                continue
            if "alias" not in txt:
                continue
            for m in _ALIAS.finditer(txt):
                ns = _namespace_vigente(txt, m.start())
                nuevo = m.group(2)
                # el destino tambien se cualifica si no lleva punto
                if ns and "." not in nuevo:
                    nuevo = ns + "." + nuevo
                #: 200 caracteres hacia atras: el atributo va en la linea de
                #: encima o en la misma, nunca mas lejos.
                dep = bool(_DEPRECADO.search(txt[max(0, m.start() - 200):
                                                 m.start()]))
                for viejo in re.split(r"\s*,\s*", m.group(1)):
                    v = (ns + "." + viejo) if (ns and "." not in viejo) else viejo
                    if v == nuevo:
                        continue
                    pares[v] = {"nuevo": nuevo, "deprecado": dep}
                    deprecados += 1 if dep else 0
    return pares, deprecados, n_fich


def main() -> int:
    from nucleo.lean import nombres as N
    if not N.disponible():
        print("sin indice de nombres: no se puede validar la cosecha")
        return 1

    print("cosechando de %s ...\n" % MATHLIB)
    pares, deprecados, n_fich = cosechar()
    print("  ficheros leidos            %5d" % n_fich)
    print("  aristas `viejo -> nuevo`   %5d" % len(pares))
    print("  de esas, `@[deprecated]`   %5d" % deprecados)

    # ── la alarma: un alias apunta a algo que Mathlib define ──────────────
    destino_roto = [v for v, d in pares.items() if not N.existe(d["nuevo"])]
    print("  destinos que NO existen    %5d  (%.1f %%)"
          % (len(destino_roto), 100.0 * len(destino_roto) / max(1, len(pares))))

    # ── ¿cubren lo que el modelo escribe mal? ────────────────────────────
    techo = os.path.join(RAIZ, "data", "techo_de_la_restriccion.json")
    cubre = nulo = 0
    invenciones = []
    if os.path.exists(techo):
        d = json.load(io.open(techo, encoding="utf-8"))
        vistos = set()
        for x in d.get("detalle", []):
            if x["inventado"] in vistos:
                continue
            vistos.add(x["inventado"])
            invenciones.append(x)
        print("\n=== CONTRA LAS INVENCIONES REALES ===\n")
        print("  invenciones distintas      %5d" % len(invenciones))
        for x in invenciones:
            hay = x["inventado"] in pares
            cubre += 1 if hay else 0
            nulo += 1 if x["candidato"] else 0
        print("  cubiertas por la TABLA     %5d  (%.1f %%)"
              % (cubre, 100.0 * cubre / max(1, len(invenciones))))
        print("  cubiertas por el NULO      %5d  (%.1f %%)   distancia de edicion"
              % (nulo, 100.0 * nulo / max(1, len(invenciones))))

    # ── la segunda cosecha, que salio buscando la primera ────────────────
    #
    # LA TABLA DE ALIAS SIRVIO DE SONDA, no de solucion: al comprobar que el
    # 16 % de sus destinos «no existe» aparecio que el hueco no era de la
    # cosecha sino DEL INDICE, y que la causa era `@[to_additive]`.
    print("\n=== LA SEGUNDA COSECHA · to_additive ===\n")
    ta = cosechar_to_additive()
    ta_falta = sorted(n for n in ta if not N.existe(n))
    print("  nombres que `@[to_additive]` genera   %5d" % len(ta))
    print("  de esos, el INDICE no conoce          %5d  (%.1f %%)"
          % (len(ta_falta), 100.0 * len(ta_falta) / max(1, len(ta))))
    print("  ejemplos: %s" % ", ".join(ta_falta[:4]))
    print("\n  y esos son solo los que Mathlib escribe: el atributo aparece")
    print("  14 273 veces, y la mayoria no lleva el nombre porque Lean lo")
    print("  deriva por sus reglas de traduccion multiplicativo -> aditivo.")

    print("\n=== LA ALARMA ===\n")
    avisos = []
    if len(ta_falta) > 0.5 * max(1, len(ta)):
        avisos.append("el %.0f %% de los nombres que `to_additive` genera NO "
                      "esta en el indice: el indice tiene un hueco sistematico "
                      "y el sistema puede decirle al alumno que un nombre real "
                      "no existe" % (100.0 * len(ta_falta) / len(ta)))
    if invenciones and cubre == 0:
        avisos.append("la tabla no cubre NI UNA de las invenciones reales: la "
                      "cosecha es grande y no sirve para este fallo")
    if invenciones and cubre == nulo:
        avisos.append("la tabla cubre exactamente lo mismo que la distancia de "
                      "edicion: no aporta informacion nueva")
    if len(destino_roto) > 0.05 * max(1, len(pares)):
        # ESTA ALARMA SE ESCRIBIO ACUSANDO A LA COSECHA, Y LA COSECHA ERA
        # INOCENTE. Un alias apunta por definicion a algo que Mathlib define,
        # asi que un destino que «no existe» solo puede ser hueco del INDICE.
        # Al tirar del primero —`alias finsum_pos' := finsum_pos`— salio que
        # `finsum_pos` no se declara en ninguna parte: lo genera
        # `@[to_additive finsum_pos]` sobre `one_lt_finprod`. La alarma acerto
        # en saltar y se equivoco de culpable; queda con el culpable correcto.
        avisos.append("el %.0f %% de los DESTINOS no esta en el indice. Un "
                      "alias apunta por definicion a algo que Mathlib define, "
                      "asi que el hueco es del INDICE y no de la cosecha — es "
                      "el mismo `to_additive` de arriba (ej: %s)"
                      % (100.0 * len(destino_roto) / len(pares),
                         ", ".join(d["nuevo"] for v, d in
                                   list(pares.items())[:0] or
                                   [(v, pares[v]) for v in destino_roto[:3]])))
    print("  " + ("\n  ".join("· " + a for a in avisos) if avisos
                  else "ninguna salta"))

    json.dump({"aristas": len(pares), "deprecados": deprecados,
               "to_additive": len(ta), "to_additive_falta": len(ta_falta),
               "to_additive_nombres": ta_falta,
               "destinos_rotos": len(destino_roto),
               "invenciones": len(invenciones), "cubre_tabla": cubre,
               "cubre_nulo": nulo, "avisos": avisos,
               "pares": pares},
              io.open(SALIDA, "w", encoding="utf-8"), ensure_ascii=False,
              indent=1)
    print("\n-> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
