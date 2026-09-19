# -*- coding: utf-8 -*-
"""La categoría de estados de prueba: objetos = estados, morfismos = tácticas.

POR QUE ESTA Y NO EL GRAFO DE SKILLS
------------------------------------
El grafo de skills es un ÍNDICE DE VOCABULARIO y como tal funciona: ofrece
nombres de Mathlib al prompt y bate a su nulo 16,5×. Lo que no es, y las
mediciones lo dicen, es el sustrato de un lazo generador-verificador: la
fibración sobre áreas mide 0,1 % contra un nulo de 4,3 %, y el viaje entre
áreas 1,1× sobre el azar.

El lazo que este sistema persigue —el modelo propone un paso, Lean lo evalúa,
la respuesta condiciona el paso siguiente— opera sobre otro objeto: el ESTADO
DE PRUEBA. Esta es su categoría.

    objetos    estados de prueba: hipótesis arriba, `⊢ objetivo` abajo
    morfismos  una táctica aplicada: `state_before --tactic--> state_after`
    identidad  no aplicar nada
    composición   encadenar tácticas; asociativa porque aplicar tácticas lo es

LA FORMA REAL, MEDIDA, Y NO ES LA QUE PARECE
--------------------------------------------
Sobre las 25 206 transiciones usables de LeanWorkbook:

    objetos distintos                            24 750
    flechas por objeto                             1,02
    transiciones que COMPONEN                    46,4 %
    estados con más de una táctica distinta          72
    pares de tácticas con mismo origen Y destino    341

Y una cifra que hay que leer con cuidado, porque yo mismo la leí mal primero:
en bruto sale UNA componente conexa con el 99,9 % de los objetos, que parece
una red riquísima. No lo es. `no goals` recibe 13 511 de las 25 206 flechas
—el 53,6 %— y lo pega todo. Quitando ese sumidero quedan **13 189 componentes**
y la mayor tiene 108 objetos.

O sea: trece mil cadenas de prueba disjuntas que terminan todas en el mismo
sitio. La conexión es entera a través del objeto terminal.

QUE SE PUEDE Y QUE NO SE PUEDE SACAR DE AQUI
--------------------------------------------
SE PUEDE:
  · `no goals` es un OBJETO TERMINAL de verdad, y eso es el enunciado
    categórico de «una prueba acaba cuando no quedan objetivos»;
  · las cadenas dan SECUENCIAS: qué táctica tiende a seguir a cuál;
  · los 341 pares paralelos —dos tácticas distintas, mismo origen y mismo
    destino— dicen «estas dos hacen aquí lo mismo», que es contenido real y es
    lo único que esta categoría afirma y un árbol no podría.

NO SE PUEDE:
  · aprender a ELEGIR entre alternativas. Sólo 72 estados de 24 750 registran
    dos tácticas distintas: el corpus casi nunca muestra dos opciones en el
    mismo punto, porque recoge la prueba que alguien escribió, no las que
    descartó;
  · reutilizar entre pruebas: las cadenas no comparten estados intermedios.

Quien quiera la parte de elegir tendrá que generarla —probando tácticas contra
estados reales— y eso cuesta compilaciones de Lean, no lectura de un fichero.
"""
from __future__ import annotations

import collections
import re
from dataclasses import dataclass, field
from typing import Iterable, Optional

#: el objeto terminal: no quedan objetivos que demostrar
TERMINAL = "no goals"

#: primer identificador de la línea: la táctica, sin sus argumentos
_TACTICA = re.compile(r"[a-zA-Z_][\w'!?]*")

#: LOS NOMBRES DE HIPOTESIS SON ARBITRARIOS. Lean los genera (`h`, `h₁`, `a✝`)
#: y dos estados que sólo difieren en cómo se llama una hipótesis son el mismo
#: objeto matemático. Normalizarlos sube los estados con más de una táctica de
#: 53 a 72 — poco, pero es la identidad correcta y no cuesta nada.
_HIPOTESIS = re.compile(r"^\s*([\w✠¹²³₀-₉']+)\s*:", re.M)


def normalizar(estado: str) -> str:
    """La identidad de objeto: mismo estado salvo nombres de hipótesis."""
    return " ".join(_HIPOTESIS.sub("_ :", estado or "").split())


def tactica_de(linea: str) -> str:
    """El nombre de la táctica, sin argumentos. Cadena vacía si no la hay."""
    m = _TACTICA.match((linea or "").strip())
    return m.group(0) if m else ""


@dataclass
class Flecha:
    """Una táctica aplicada: `origen --tactica--> destino`."""
    origen: str
    tactica: str
    destino: str

    @property
    def cierra(self) -> bool:
        return self.destino == TERMINAL

    def __repr__(self) -> str:
        return "%s --%s--> %s" % (self.origen[:28], self.tactica,
                                  "⊤" if self.cierra else self.destino[:20])


@dataclass
class CategoriaDeEstados:
    """Los estados y las tácticas que van de unos a otros."""
    objetos: set = field(default_factory=set)
    flechas: list = field(default_factory=list)
    #: origen -> [Flecha]
    salientes: dict = field(default_factory=lambda: collections.defaultdict(list))
    #: destino -> cuántas llegan
    entrantes: collections.Counter = field(default_factory=collections.Counter)

    # ── la estructura categórica ────────────────────────────────────────
    def identidad(self, objeto: str) -> Flecha:
        """`id_A`: no aplicar nada. Existe para todo objeto, por definición."""
        return Flecha(objeto, "", objeto)

    def componer(self, f: Flecha, g: Flecha) -> Optional[list]:
        """`g ∘ f`, o None si no encajan.

        Se devuelve la LISTA de flechas y no una flecha nueva a propósito: en
        esta categoría el morfismo compuesto ES la secuencia de tácticas, y
        colapsarlo perdería justo lo que se quiere aprender.
        """
        return [f, g] if f.destino == g.origen else None

    def es_terminal(self, objeto: str) -> bool:
        return objeto == TERMINAL

    # ── recorrer ────────────────────────────────────────────────────────
    def siguientes(self, estado: str) -> list:
        """Las tácticas que se aplicaron a este estado."""
        return list(self.salientes.get(normalizar(estado), ()))

    def camino(self, estado: str, tope: int = 60) -> list:
        """La cadena desde `estado` hasta donde llegue.

        `tope` corta por si el corpus trajera un ciclo: aplicar tácticas no
        debería producirlos —un estado no vuelve a sí mismo— pero el dato es
        de fuera y una cadena infinita cuelga al que la recorra.
        """
        cur, out, visto = normalizar(estado), [], set()
        while cur in self.salientes and cur not in visto and len(out) < tope:
            visto.add(cur)
            f = self.salientes[cur][0]
            out.append(f)
            cur = f.destino
        return out

    def raices(self) -> list:
        """Estados donde empieza una prueba: nadie llega a ellos."""
        return [o for o in self.objetos if not self.entrantes[o]]

    def paralelas(self) -> list:
        """Pares de tácticas DISTINTAS con el mismo origen y el mismo destino.

        Es lo único que esta categoría afirma y un árbol no podría: que dos
        morfismos distintos tengan el mismo dominio y codominio. Leído en
        matemáticas: «aquí estas dos tácticas hacen lo mismo».
        """
        out = []
        for origen, fs in self.salientes.items():
            por_destino = collections.defaultdict(set)
            for f in fs:
                por_destino[f.destino].add(f.tactica)
            for destino, tacs in por_destino.items():
                if len(tacs) > 1:
                    out.append((origen, destino, sorted(tacs)))
        return out

    def __repr__(self) -> str:
        return ("CategoriaDeEstados(%d objetos, %d flechas, %d cierran)"
                % (len(self.objetos), len(self.flechas),
                   sum(1 for f in self.flechas if f.cierra)))


def construir(transiciones: Iterable) -> CategoriaDeEstados:
    """Monta la categoría desde `(state_before, tactic, state_after)`.

    Se descarta lo que no es una transición: sin `⊢` en el estado de partida
    no hay objetivo, y sin táctica reconocible no hay morfismo.
    """
    c = CategoriaDeEstados()
    for sb, tac, sa in transiciones:
        t = tactica_de(tac)
        if not t or "⊢" not in (sb or ""):
            continue
        origen, destino = normalizar(sb), normalizar(sa)
        f = Flecha(origen, t, destino)
        c.flechas.append(f)
        c.objetos.add(origen)
        c.objetos.add(destino)
        c.salientes[origen].append(f)
        c.entrantes[destino] += 1
    return c
