"""
Funtor cociente pi: Skills -> Agentes.

QUE ES
------
El sistema tiene DOS categorias, no tres. Los skills L1-L3 y las
teorias/subteorias son el MISMO grafo: el objeto «teoria de anillos» y el
skill «experto en teoria de anillos» son el mismo nodo. La categoria
genuinamente distinta es la de agentes: 14 objetos, uno por categoria
matematica.

No puede haber isomorfismo entre ellas: 172 objetos frente a 14 es una
obstruccion de cardinalidad, no un defecto de implementacion. Lo que si
existe es una PROYECCION

    pi(s) = categoria(s)

sobreyectiva en objetos y muy lejos de inyectiva. Este modulo la construye
como FUNTOR, que es lo que hace falta para que la estructura de Ehresmann
—co-conos y co-conos limite— baje coherentemente de un nivel al otro.

POR QUE NO ERA FUNTOR
---------------------
Medido sobre el grafo real (172 skills, 556 morfismos):

    dentro de una categoria   286   51,4 %
    CRUZAN de categoria       202   36,3 %   <- sin destino en Agentes
    tocan un fundacional L0    68   12,2 %   <- pi ni siquiera definida

Los cruces no son errores: `commutative-algebra -> algebraic-geometry` es
matematicamente correcto, y es justo el morfismo que produce el colimite
`join(functors, commutative-algebra) = algebraic-geometry`. El problema era
que la categoria de agentes es DISCRETA —14 nombres en una lista— y no tiene
donde recibirlos.

LA CONSTRUCCION
---------------
Se define Agentes como la IMAGEN de pi, con los morfismos INDUCIDOS:

    Obj(A) = pi(Obj(S))
    Hom(A) = { pi(f) : f in Hom(S), pi(f) no identidad }

Asi pi es funtor por construccion, no por suerte: todo morfismo de S tiene
imagen porque su imagen es, por definicion, un morfismo de A.

Los 10 skills fundacionales (L0) no llevan categoria. Se mandan a un objeto
TERMINAL en lugar de excluirlos: excluirlos dejaria pi parcial, y con ella
todo enunciado sobre preservacion. Ver OBJETO_BASE.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from nucleo.graph.category import SkillCategory

#: Imagen de los skills fundacionales, que no tienen categoria matematica.
#: Es un objeto real de la categoria de agentes, no un centinela: los 56
#: morfismos jerarquicos que tocan un L0 necesitan destino para que pi sea
#: total.
OBJETO_BASE = "fundacional"


@dataclass(frozen=True)
class MorfismoAgente:
    """Morfismo inducido entre dos agentes."""
    source_id: str
    target_id: str
    #: cuantos morfismos de Skills se proyectan sobre este
    multiplicidad: int = 1
    #: tipos de morfismo de origen que lo inducen
    tipos: frozenset = frozenset()

    def __repr__(self) -> str:
        return f"{self.source_id} -> {self.target_id} (x{self.multiplicidad})"


@dataclass
class CategoriaAgentes:
    """Categoria de agentes: la imagen de pi, con morfismos inducidos."""
    objetos: set = field(default_factory=set)
    morfismos: dict = field(default_factory=dict)

    def hom(self, a: str, b: str) -> Optional[MorfismoAgente]:
        return self.morfismos.get((a, b))

    def hay_flecha(self, a: str, b: str) -> bool:
        return a == b or (a, b) in self.morfismos

    def alcanzables_desde(self, a: str) -> set:
        """Clausura transitiva: los objetos b con un camino a -> ... -> b."""
        vistos, pila = {a}, [a]
        while pila:
            x = pila.pop()
            for (s, t) in self.morfismos:
                if s == x and t not in vistos:
                    vistos.add(t)
                    pila.append(t)
        return vistos

    def __repr__(self) -> str:
        return (f"CategoriaAgentes({len(self.objetos)} objetos, "
                f"{len(self.morfismos)} morfismos)")


@dataclass
class Funtor:
    """pi: Skills -> Agentes, junto con su codominio."""
    en_objetos: dict
    codominio: CategoriaAgentes
    #: morfismos de Skills que pi manda a una identidad (los intra-categoria)
    colapsados: int = 0

    def __call__(self, skill_id: str) -> str:
        return self.en_objetos[skill_id]


def construir_funtor(graph, solo_jerarquia: bool = True) -> Funtor:
    """
    Construye pi y su codominio a partir del grafo de skills.

    Args:
        graph: la categoria de skills.
        solo_jerarquia: si True (por defecto) solo inducen morfismos los de
            ORDER_MORPHISMS. Es lo correcto para la estructura de orden:
            TRANSLATION va de las ramas matematicas a `lean-tactics`, que no
            es una rama sino COMO se demuestra, y arrastrarla al codominio
            produce las mismas uniones espurias que ORDER_MORPHISMS existe
            para evitar (ver category.py).
    """
    from nucleo.graph.category import SkillCategory

    en_objetos = {}
    for s in graph.skills:
        cat = (s.metadata or {}).get("category")
        en_objetos[s.id] = cat if cat else OBJETO_BASE

    cod = CategoriaAgentes(objetos=set(en_objetos.values()))

    agrupados = defaultdict(list)
    colapsados = 0
    for m in graph.morphisms:
        if solo_jerarquia and m.morphism_type not in SkillCategory.ORDER_MORPHISMS:
            continue
        a = en_objetos.get(m.source_id)
        b = en_objetos.get(m.target_id)
        if a is None or b is None:
            continue
        if a == b:
            colapsados += 1          # pi(f) = id, no hace falta registrarlo
            continue
        agrupados[(a, b)].append(m)

    for (a, b), ms in agrupados.items():
        cod.morfismos[(a, b)] = MorfismoAgente(
            source_id=a, target_id=b, multiplicidad=len(ms),
            tipos=frozenset(str(m.morphism_type).split(".")[-1] for m in ms),
        )

    return Funtor(en_objetos=en_objetos, codominio=cod, colapsados=colapsados)


def verificar_functorialidad(pi: Funtor, graph, solo_jerarquia: bool = True) -> dict:
    """
    Comprueba las dos leyes de funtor sobre el grafo real.

      (F1) identidades:  pi(id_s) = id_{pi(s)}, lo que exige que pi este
           definida en todo objeto del dominio.
      (F2) composicion:  si f: a->b y g: b->c estan en S, entonces
           pi(g) o pi(f) tiene que existir en A, es decir pi(a) debe
           alcanzar pi(c).

    (F2) se comprueba sobre la clausura transitiva porque el codominio es un
    preorden: la composicion de dos flechas es la flecha compuesta, y basta
    con que exista un camino.
    """
    from nucleo.graph.category import SkillCategory

    fallos_f1 = [s.id for s in graph.skills if s.id not in pi.en_objetos]

    total = definidos = 0
    aristas = []
    for m in graph.morphisms:
        if solo_jerarquia and m.morphism_type not in SkillCategory.ORDER_MORPHISMS:
            continue
        total += 1
        a = pi.en_objetos.get(m.source_id)
        b = pi.en_objetos.get(m.target_id)
        if a is None or b is None:
            continue
        definidos += 1
        aristas.append((m.source_id, m.target_id, a, b))

    salientes = defaultdict(list)
    for sid, tid, _, _ in aristas:
        salientes[sid].append(tid)

    # Cachear la clausura evita recalcularla por cada composicion.
    cache = {}

    def alcanza(x):
        if x not in cache:
            cache[x] = pi.codominio.alcanzables_desde(x)
        return cache[x]

    comps = fallos_f2 = 0
    for sid, tid, a, b in aristas:
        for uid in salientes.get(tid, []):
            comps += 1
            c = pi.en_objetos.get(uid)
            if c is None or (a != c and c not in alcanza(a)):
                fallos_f2 += 1

    return {
        "objetos_del_dominio": len(graph.skills),
        "objetos_sin_imagen": len(fallos_f1),
        "morfismos_considerados": total,
        "morfismos_con_imagen": definidos,
        "F1_identidades_ok": not fallos_f1,
        "composiciones_comprobadas": comps,
        "F2_fallos": fallos_f2,
        "F2_composicion_ok": fallos_f2 == 0,
        "es_funtor": (not fallos_f1) and definidos == total and fallos_f2 == 0,
    }


def verificar_preservacion_colimites(pi: Funtor, graph, colimites: list) -> dict:
    """
    Comprueba si pi preserva los colimites descubiertos.

    Un funtor preserva el CO-CONO de J sobre {c_1..c_n} si pi(J) sigue siendo
    cota superior de {pi(c_i)}. La MINIMALIDAD es otra cosa: un funtor
    cociente no tiene por que preservarla, y aqui casi nunca lo hace. Es la
    diferencia entre preservar co-conos y preservar co-conos LIMITE, y los dos
    numeros se reportan por separado porque miden cosas distintas.

    Args:
        colimites: lista de (component_ids, join_id).
    """
    cocono_ok = limite_ok = colapsado = 0
    detalle = []
    cache = {}

    def alcanza(x):
        if x not in cache:
            cache[x] = pi.codominio.alcanzables_desde(x)
        return cache[x]

    for componentes, jid in colimites:
        pj = pi.en_objetos.get(jid)
        pcs = [pi.en_objetos.get(c) for c in componentes]
        if pj is None or any(p is None for p in pcs):
            continue

        es_cocono = all(p == pj or pj in alcanza(p) for p in pcs)
        es_colapso = all(p == pj for p in pcs)

        if es_colapso:
            colapsado += 1
        es_limite = False
        if es_cocono:
            cocono_ok += 1
            arriba = [x for x in pi.codominio.objetos
                      if all(p == x or x in alcanza(p) for p in pcs)]
            es_limite = all(pj == x or x in alcanza(pj) for x in arriba)
            if es_limite:
                limite_ok += 1

        detalle.append({
            "componentes": componentes, "join": jid,
            "pi_componentes": pcs, "pi_join": pj,
            "cocono": es_cocono, "limite": es_limite, "colapsado": es_colapso,
        })

    return {
        "colimites": len(detalle),
        "cocono_preservado": cocono_ok,
        "colimite_preservado": limite_ok,
        "colapsados_a_un_punto": colapsado,
        "detalle": detalle,
    }
