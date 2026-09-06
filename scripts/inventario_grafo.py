# -*- coding: utf-8 -*-
"""Inventario completo del grafo de conocimiento, leido del runtime.

Todo lo que hace falta para describirlo: objetos, flechas, procedencia,
vocabulario, nombres de Mathlib, estructura y propiedades categoricas.
"""
import collections
import io
import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, "E:/Metamatematico")

SALIDA = "E:/Metamatematico/data/inventario_grafo.json"

ACENTOS = "áéíóúñüÁÉÍÓÚÑ"


def main():
    from nucleo.core import Nucleo
    from nucleo.graph.category import SkillCategory
    from nucleo.graph.interpretacion import nombres_de_trabajo

    n = Nucleo.__new__(Nucleo)
    n._graph = SkillCategory()
    Nucleo._load_foundational_skills(n)
    g = n._graph
    S = list(g.skills)
    meta = {s.id: (s.metadata or {}) for s in S}
    R = {}

    def nivel(s):
        lv = getattr(s, "level", None)
        return int(lv if lv is not None else meta[s.id].get("level", 2))

    nuestro = lambda i: meta[i].get("origen") is None          # noqa: E731

    # ── 1 · objetos ───────────────────────────────────────────────────────
    R["n_nodos"] = len(S)
    R["n_morfismos"] = len(g.morphisms)
    R["por_sort"] = dict(collections.Counter(meta[s.id].get("sort") for s in S))
    R["por_origen"] = dict(collections.Counter(
        str(meta[s.id].get("origen")) for s in S))
    R["por_nivel"] = dict(collections.Counter(nivel(s) for s in S))
    R["por_area"] = dict(collections.Counter(
        meta[s.id].get("category") or "(sin área)" for s in S))

    # ── 2 · los diez fundacionales, con ficha ─────────────────────────────
    l0 = [s for s in S if nivel(s) == 0]
    R["fundacionales"] = [{
        "id": s.id, "n": s.name, "d": s.description or "",
        "m": [p.strip() for p in re.split(r"[,+]", nombres_de_trabajo(s.id) or "")
              if p.strip()],
        "dep": sorted(g.dependencies(s.id)),
        "sal": sum(1 for x in g.morphisms
                   if x.source_id == s.id and x.morphism_type.name != "IDENTITY"),
    } for s in sorted(l0, key=lambda x: x.id)]

    # ── 3 · los curados, por area ─────────────────────────────────────────
    cur = collections.defaultdict(list)
    for s in S:
        if nuestro(s.id) and meta[s.id].get("sort") == "CONCEPTO":
            cur[meta[s.id].get("category") or "(sin área)"].append(
                (s.id, s.name, nivel(s)))
    R["curados_por_area"] = {k: sorted(v) for k, v in
                             sorted(cur.items(), key=lambda kv: -len(kv[1]))}

    # ── 4 · los nodos de area ─────────────────────────────────────────────
    R["areas"] = sorted(
        [{"id": s.id, "n": s.name,
          "kw": len([k for k in (meta[s.id].get("keywords") or []) if k.strip()]),
          "hijos": sum(1 for x in g.morphisms if x.source_id == s.id
                       and x.morphism_type.name != "IDENTITY")}
         for s in S if meta[s.id].get("sort") == "AREA"],
        key=lambda d: -d["hijos"])

    # ── 5 · flechas ───────────────────────────────────────────────────────
    R["por_tipo"] = dict(collections.Counter(
        m.morphism_type.name for m in g.morphisms))
    cruz = collections.Counter()
    constr = collections.Counter()
    cuota = collections.Counter()
    lean_certif = []
    for m in g.morphisms:
        md = getattr(m, "metadata", None) or {}
        if m.morphism_type.name != "IDENTITY":
            cruz[(m.morphism_type.name,
                  "nuestro" if nuestro(m.source_id) else "mathlib",
                  "nuestro" if nuestro(m.target_id) else "mathlib")] += 1
        if md.get("construccion"):
            constr[md["construccion"]] += 1
        if "cuota_mathlib" in md:
            cuota[bool(md["cuota_mathlib"])] += 1
        if md.get("teorema_lean"):
            lean_certif.append({"o": m.source_id, "d": m.target_id,
                                "t": md["teorema_lean"],
                                "a": md.get("afirma", "")})
    R["cruce"] = [{"t": k[0], "de": k[1], "a": k[2], "n": v}
                  for k, v in sorted(cruz.items(), key=lambda kv: -kv[1])]
    R["construcciones_distintas"] = len(constr)
    R["construcciones_top"] = constr.most_common(14)
    R["cuota_mathlib"] = {str(k): v for k, v in cuota.items()}
    R["certificadas_lean"] = lean_certif

    # ── 6 · vocabulario ───────────────────────────────────────────────────
    kw_sort = collections.Counter()
    n_sort = collections.Counter()
    es = en = frases = 0
    todas = []
    for s in S:
        so = meta[s.id].get("sort")
        ks = [k for k in (meta[s.id].get("keywords") or []) if k.strip()]
        kw_sort[so] += len(ks)
        n_sort[so] += 1
        todas.extend(ks)
        for k in ks:
            if " " in k.strip():
                frases += 1
            if any(c in k for c in ACENTOS):
                es += 1
    R["kw_por_sort"] = [{"s": k, "nodos": n_sort[k], "kw": kw_sort[k],
                         "media": round(kw_sort[k] / max(1, n_sort[k]), 1)}
                        for k, _ in kw_sort.most_common()]
    R["kw_total"] = len(todas)
    R["kw_distintas"] = len(set(x.lower() for x in todas))
    R["kw_frases"] = frases
    R["kw_con_acento"] = es
    R["kw_repetidas"] = [(w, c) for w, c in
                         collections.Counter(x.lower() for x in todas).most_common(10)]
    R["sin_kw"] = sorted(s.id for s in S
                         if not [k for k in (meta[s.id].get("keywords") or [])
                                 if k.strip()])

    # ── 7 · nombres de Mathlib ────────────────────────────────────────────
    nom, ids = {}, set()
    for s in S:
        p = [x.strip() for x in
             re.split(r"[,+]", nombres_de_trabajo(s.id) or "") if x.strip()]
        if p:
            nom[s.id] = p
            ids.update(p)
    R["nodos_con_nombres"] = len(nom)
    R["plazas_nombres"] = sum(len(v) for v in nom.values())
    R["nombres_distintos"] = len(ids)
    R["nombres_tipo"] = sorted(i for i in ids if i[:1].isupper())
    R["nombres_lema"] = sorted(i for i in ids if not i[:1].isupper())
    R["namespaces"] = collections.Counter(
        i.split(".")[0] for i in ids).most_common(12)
    R["conceptos_sin_nombres"] = sorted(
        s.id for s in S
        if meta[s.id].get("sort") == "CONCEPTO" and s.id not in nom)

    # ── 8 · estructura ────────────────────────────────────────────────────
    sal, ent = collections.Counter(), collections.Counter()
    ady = collections.defaultdict(set)
    for m in g.morphisms:
        if m.morphism_type.name == "IDENTITY":
            continue
        sal[m.source_id] += 1
        ent[m.target_id] += 1
        ady[m.source_id].add(m.target_id)
    R["sumideros"] = sum(1 for s in S if sal[s.id] == 0)
    R["fuentes"] = sum(1 for s in S if ent[s.id] == 0)
    R["aislados"] = sum(1 for s in S if sal[s.id] == 0 and ent[s.id] == 0)
    R["mas_reciben"] = [(k, ent[k], sal[k], meta[k].get("sort"))
                        for k, _ in ent.most_common(8)]
    R["mas_emiten"] = [(k, sal[k], ent[k], meta[k].get("sort"))
                       for k, _ in sal.most_common(8)]

    # alcance por dependencia desde cada fundacional
    def alcanza(raiz):
        vis, cola = set(), [raiz]
        while cola:
            x = cola.pop()
            for y in ady[x]:
                if y not in vis:
                    vis.add(y)
                    cola.append(y)
        return vis
    R["alcance_pilares"] = sorted(
        [(s.id, len(alcanza(s.id))) for s in l0], key=lambda t: -t[1])

    # ciclos (solo DEPENDENCY, que es el orden)
    dep = collections.defaultdict(set)
    for m in g.morphisms:
        if m.morphism_type.name == "DEPENDENCY":
            dep[m.source_id].add(m.target_id)
    color, ciclos = {}, [0]

    def dfs(u):
        color[u] = 1
        for v in dep[u]:
            if color.get(v, 0) == 1:
                ciclos[0] += 1
            elif color.get(v, 0) == 0:
                dfs(v)
        color[u] = 2
    sys.setrecursionlimit(6000)
    for s in S:
        if color.get(s.id, 0) == 0:
            dfs(s.id)
    R["aristas_de_retorno_dep"] = ciclos[0]

    # ── 9 · lo medido sobre el grafo ──────────────────────────────────────
    med = {}
    for f, cl in [("recuperacion_proofnet", None), ("funtor_mathlib", None),
                  ("fibracion_del_grafo", None), ("emparejamiento", None),
                  ("cobertura_taxonomia", None)]:
        try:
            med[f] = json.load(io.open("E:/Metamatematico/data/%s.json" % f,
                                       encoding="utf-8"))
        except Exception:
            pass
    R["medido"] = {
        "vocabulario": med.get("recuperacion_proofnet", {}).get("resultados", {}),
        "funtor": {k: v for k, v in med.get("funtor_mathlib", {}).items()
                   if not isinstance(v, list)},
        "fibracion": {k: v for k, v in med.get("fibracion_del_grafo", {}).items()
                      if not isinstance(v, list)},
        "emparejamiento": {k: v for k, v in med.get("emparejamiento", {}).items()
                           if not isinstance(v, (list, dict))},
        "taxonomia": {k: v for k, v in med.get("cobertura_taxonomia", {}).items()
                      if not isinstance(v, (list, dict))},
    }

    io.open(SALIDA, "w", encoding="utf-8").write(
        json.dumps(R, ensure_ascii=False, indent=1))

    # resumen por pantalla
    print("nodos %d · morfismos %d" % (R["n_nodos"], R["n_morfismos"]))
    print("sorts:", R["por_sort"])
    print("origen:", R["por_origen"])
    print("niveles:", R["por_nivel"])
    print("tipos:", R["por_tipo"])
    print("construcciones distintas:", R["construcciones_distintas"])
    print("cuota_mathlib:", R["cuota_mathlib"])
    print("certificadas con teorema Lean:", len(R["certificadas_lean"]))
    print("kw total %d · distintas %d · frases %d · con acento %d"
          % (R["kw_total"], R["kw_distintas"], R["kw_frases"], R["kw_con_acento"]))
    print("nombres: %d nodos, %d plazas, %d distintos (%d tipos / %d lemas)"
          % (R["nodos_con_nombres"], R["plazas_nombres"], R["nombres_distintos"],
             len(R["nombres_tipo"]), len(R["nombres_lema"])))
    print("lemas:", R["nombres_lema"])
    print("namespaces:", R["namespaces"][:8])
    print("sumideros %d · fuentes %d · aislados %d"
          % (R["sumideros"], R["fuentes"], R["aislados"]))
    print("aristas de retorno en DEPENDENCY:", R["aristas_de_retorno_dep"])
    print("alcance de los pilares:", R["alcance_pilares"])
    print("conceptos CURADOS sin nombres de Mathlib:",
          len(R["conceptos_sin_nombres"]))
    print("-> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
