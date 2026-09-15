# -*- coding: utf-8 -*-
"""Exporta el grafo ENTERO del runtime a JSON, con posiciones ya calculadas.

Nodos: id, nombre, descripcion, sort, area, nivel, keywords, nombres de
Mathlib, dependencias y vecinos. Aristas: origen, destino, tipo. Y (x, y).

LA DISPOSICION es radial por AREA, no por pilar: el area es la base de la
proyeccion pi y es lo que una persona busca cuando mira el grafo («enseñame
el algebra»). Cada area recibe un sector proporcional a su tamaño, y dentro
del sector el radio lo da el nivel — los fundacionales al centro, las
sub-ramas fuera. Asi dos nodos no pueden caer encima porque cada uno tiene su
porcion de angulo, y se comprueba al final.

Las 9 tacticas y las 6 estrategias van en su propio sector: no son de ningun
area (`area=None`) y meterlas dentro seria afirmar que lo son.

No gasta API.
"""
import collections
import io
import json
import math
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "E:/Metamatematico")

SALIDA = "E:/Metamatematico/data/grafo_web.json"
#: El explorador publicado incrusta este JSON. Para regenerarlo:
#:     python scripts/exportar_grafo_web.py
#:     python scripts/incrustar_grafo_web.py

R0, R_MAX = 62.0, 470.0


def main():
    from nucleo.core import Nucleo
    from nucleo.graph.category import SkillCategory
    from nucleo.graph.interpretacion import marca, nombres_de_trabajo

    n = Nucleo.__new__(Nucleo)
    n._graph = SkillCategory()
    Nucleo._load_foundational_skills(n)
    g = n._graph
    S = list(g.skills)
    meta = {s.id: (s.metadata or {}) for s in S}

    def area_de(sid):
        """El sector en que se dibuja el nodo.

        Los 22 nodos AREA van JUNTOS y no repartidos por su propia rama: son
        la base de la proyeccion pi, y verlos como un anillo es lo que hace
        legible que las demas fibras se proyectan sobre ellos. Repartidos,
        cada uno abria un sector de un solo nodo y el dibujo se deshacia en
        quince cuñas vacias.
        """
        so = meta[sid].get("sort")
        if so == "AREA":
            return "· la base: 22 áreas"
        if so in ("TACTICA", "ESTRATEGIA"):
            return "· tácticas y estrategias"
        return meta[sid].get("category") or "· fundacional"

    # ── agrupar y ordenar los sectores por tamaño ────────────────────────
    grupos = collections.defaultdict(list)
    for s in S:
        grupos[area_de(s.id)].append(s.id)
    orden = sorted(grupos, key=lambda k: (-len(grupos[k]), k))

    total = len(S)
    pos, ang_area = {}, {}
    a0 = -math.pi / 2
    for area in orden:
        ids = grupos[area]
        span = 2 * math.pi * len(ids) / total
        ang_area[area] = (a0, a0 + span)
        # dentro del sector: por nivel, y dentro del nivel por id
        porniv = collections.defaultdict(list)
        for i in ids:
            sk = g.get_skill(i)
            lv = getattr(sk, "level", None)
            if lv is None:
                lv = meta[i].get("level", 2)
            porniv[int(lv)].append(i)
        # el angulo se reparte entre TODOS los del sector, nivel a nivel
        k = 0
        for lv in sorted(porniv):
            for i in sorted(porniv[lv]):
                # margen del 6 % a cada lado para que los sectores se separen
                t = (k + 0.5) / max(1, len(ids))
                ang = a0 + span * (0.06 + 0.88 * t)
                rad = R0 + (R_MAX - R0) * (min(lv, 3) / 3.0) ** 0.82
                # Desplazamiento radial en 5 carriles, no en 3: con sectores
                # de 96 nodos tres carriles dejaban vecinos a menos de 3 px.
                rad += ((k % 5) - 2) * 15.0
                pos[i] = (round(600 + rad * math.cos(ang), 1),
                          round(560 + rad * math.sin(ang), 1))
                k += 1
        a0 += span

    # ── comprobacion: nadie encima de nadie ─────────────────────────────
    encimados = 0
    ps = list(pos.items())
    for i in range(len(ps)):
        for j in range(i + 1, len(ps)):
            dx = ps[i][1][0] - ps[j][1][0]
            dy = ps[i][1][1] - ps[j][1][1]
            if dx * dx + dy * dy < 9:
                encimados += 1
    print("nodos colocados: %d · encimados (<3 px): %d" % (len(pos), encimados))

    # ── nodos ────────────────────────────────────────────────────────────
    ent = collections.Counter()
    sal = collections.Counter()
    for m in g.morphisms:
        if m.morphism_type.name == "IDENTITY":
            continue
        sal[m.source_id] += 1
        ent[m.target_id] += 1

    nodos = []
    for s in S:
        nm = [p.strip() for p in
              re.split(r"[,+]", nombres_de_trabajo(s.id) or "") if p.strip()]
        lv = getattr(s, "level", None)
        if lv is None:
            lv = meta[s.id].get("level", 2)
        nodos.append({
            "id": s.id,
            "n": s.name or s.id,
            "d": (s.description or "")[:240],
            "s": meta[s.id].get("sort") or "CONCEPTO",
            "a": meta[s.id].get("category"),
            "ar": area_de(s.id),
            "lv": int(lv),
            "k": [k for k in (meta[s.id].get("keywords") or []) if k.strip()],
            "m": nm,
            # LA MARCA DEL VEREDICTO, que es lo unico del grafo que no se
            # puede deducir mirandolo. Falto aqui desde el principio: el
            # explorador ensenaba los 352 nodos sin distinguir los 105 que
            # son vertices legitimos de los 43 que son aristas disfrazadas,
            # y esa distincion es la que sostiene la categoria. `null` en los
            # 147 que no llevan marca —125 modulos de Mathlib y 22 areas—,
            # que no son del autor y no les toca tenerla.
            "mc": marca(s.id),
            "x": pos[s.id][0], "y": pos[s.id][1],
            "ent": ent[s.id], "sal": sal[s.id],
        })

    aristas = []
    for m in g.morphisms:
        t = m.morphism_type.name
        if t == "IDENTITY":
            continue
        aristas.append({"o": m.source_id, "d": m.target_id, "t": t[:3]})

    datos = {
        "nodos": nodos,
        "aristas": aristas,
        "identidades": sum(1 for m in g.morphisms
                           if m.morphism_type.name == "IDENTITY"),
        "sectores": [{"a": a, "d": round(ang_area[a][0], 4),
                      "h": round(ang_area[a][1], 4), "n": len(grupos[a])}
                     for a in orden],
    }
    io.open(SALIDA, "w", encoding="utf-8").write(
        json.dumps(datos, ensure_ascii=False, separators=(",", ":")))
    import os
    print("nodos %d · aristas dibujables %d · identidades %d"
          % (len(nodos), len(aristas), datos["identidades"]))
    print("sectores: %s" % ", ".join("%s(%d)" % (s["a"], s["n"])
                                     for s in datos["sectores"]))
    print("-> %s  (%.0f KB)" % (SALIDA, os.path.getsize(SALIDA) / 1024))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
