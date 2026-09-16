# -*- coding: utf-8 -*-
"""Cuantas veces el grafo ofrece un nombre que Lean NO va a poder resolver.

EL FALLO QUE LO MOTIVA
----------------------
Consulta real del chat: «demuestra que todo espacio vectorial tiene una base».

El grafo hizo su trabajo BIEN. Emparejo `bases-and-dimension` y ofrecio
`Module.Basis`, que es el nombre correcto. El modelo lo uso. Y Lean contesto
`invalid binder annotation, type is not a class instance`, porque la cabecera
del fichero era esta:

    import Mathlib.Tactic.Ring · Linarith · NormNum · Positivity
    import Mathlib.Algebra.Order.Field.Basic
    import Mathlib.Data.Real.Basic

y `Module.Basis` vive en `Mathlib.LinearAlgebra.Basis.Defs`, que no esta ni
se alcanza desde ahi.

POR QUE PASA, Y POR QUE NO ES UN DESPISTE
-----------------------------------------
Son DOS capacidades medidas por separado, y el decisor las gobierna por
separado:

    nombres_de_mathlib_en_el_prompt   ENCENDIDA   22,8 % contra 1,45 %
    eleccion_de_imports               APAGADA     18 de 20 contra 18 de 20

La segunda se apago por no batir a su nulo —un conjunto fijo de tres
modulos— y la decision es correcta DENTRO DE SU BANCO. Lo que nadie midio es
la INTERACCION: la primera mete en el prompt nombres que solo la segunda sabe
importar. Apagar la segunda con la primera encendida produce exactamente este
fallo, y el banco de 20 casos no lo vio porque sus nombres si estaban en la
cabecera generica.

No son dos capacidades: son una partida en dos por un accidente de
implementacion. Ofrecer un nombre y poder importarlo es el mismo acto.

QUE MIDE ESTE SCRIPT
--------------------
Sobre las 371 consultas de ProofNet, cuantas reciben del grafo al menos un
nombre cuyo modulo NO esta en la cabecera generica ni se alcanza desde ella
por el DAG de imports. Es determinista, no gasta API y no necesita Lean.

    python -m scripts.nombre_sin_import
"""
from __future__ import annotations

import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)


def cabecera_generica():
    """Los modulos que el cliente de Lean pone SIEMPRE, sin mirar la consulta.

    Se leen del propio cliente y no se copian aqui: una copia se queda vieja
    en cuanto alguien toque `_SAFE_HEADER`, y entonces este medidor mediria
    un sistema que ya no existe — el fallo que `test_ningun_medidor_fija_k_a_mano`
    existe para cazar, con otro disfraz.
    """
    from nucleo.lean.client import LeanClient
    mods = set()
    for linea in LeanClient._SAFE_HEADER.splitlines():
        linea = linea.strip()
        if linea.startswith("import "):
            mods.add(linea[len("import "):].strip())
    # LOS `_TOPIC_IMPORTS` NO ENTRAN, y meterlos fue un error mio que hacia
    # la medida DEMASIADO BENIGNA. Son condicionales: cada uno se dispara por
    # palabras que aparezcan en el codigo YA GENERADO, asi que ninguna
    # consulta los recibe todos. Sumarlos da una cabecera que nadie tiene —
    # y una de ellas, `InnerProductSpace.PiL2`, arrastra media algebra lineal
    # y hacia parecer visible `LinearAlgebra.Basis.Defs`, que es justo el
    # modulo que faltaba en el fallo que motivo este script.
    #
    # Se mide contra el SUELO: los seis que van siempre. Los condicionales
    # pueden salvar algun caso, y por eso la cifra de aqui es una cota
    # inferior del agujero, no una exageracion.
    return mods


def alcanzables(semilla):
    """Los modulos que Lean ve al importar `semilla`, por el DAG de imports.

    OJO CON EL SENTIDO. En `data/mathlib_imports.dot` la arista `"A" -> "B"`
    significa **B importa A**. Asi que lo que se ve al importar B son los A
    que apuntan hacia el — los antecesores, no los sucesores. Leerlo al reves
    da la respuesta contraria y parece razonable.
    """
    ruta = os.path.join(RAIZ, "data", "mathlib_imports.dot")
    importa = {}
    pat = re.compile(r'"([^"]+)"\s*->\s*"([^"]+)"')
    for linea in io.open(ruta, encoding="utf-8"):
        m = pat.search(linea)
        if m:
            a, b = m.group(1), m.group(2)
            importa.setdefault(b, set()).add(a)
    vistos = set(semilla)
    pila = list(semilla)
    while pila:
        x = pila.pop()
        for padre in importa.get(x, ()):
            if padre not in vistos:
                vistos.add(padre)
                pila.append(padre)
    return vistos


def main() -> int:
    import warnings
    import logging
    warnings.filterwarnings("ignore")
    logging.disable(logging.WARNING)

    from nucleo.core import Nucleo, PLAZAS_CON_NOMBRES
    from nucleo.graph.category import SkillCategory
    from scripts.recuperacion_contra_proofnet import cargar

    n = Nucleo.__new__(Nucleo)
    n._graph = SkillCategory()
    Nucleo._load_foundational_skills(n)
    g = n._graph

    semilla = cabecera_generica()
    visibles = alcanzables(semilla)
    print("cabecera generica: %d modulos declarados · %d alcanzables por el DAG"
          % (len(semilla), len(visibles)))

    mapa = json.load(io.open(os.path.join(RAIZ, "data", "mathlib_modulos.json"),
                             encoding="utf-8"))
    por_skill = mapa.get("por_skill", mapa)

    filas = cargar()
    con_nombre = huerfanas = huerfanas_con_arreglo = 0
    ejemplos = []
    cuenta = {}
    for _id, informal, _formal in filas:
        ids = [getattr(x, "id", x)
               for x in Nucleo._match_skills_to_query(n, informal, g)]
        noms = n._nombres_mathlib(ids, informal, g)
        if not noms:
            continue
        con_nombre += 1

        # DOS BRAZOS. Antes: solo la cabecera generica. Despues: la cabecera
        # mas los modulos de los nombres que el prompt SI ofrecio, que es lo
        # que `_modulos_de_los_nombres` manda ahora siempre.
        ctx = {"relevant_skills": ids, "mathlib_verificado": noms}
        con_arreglo = set(visibles) | set(n._modulos_de_los_nombres(ctx))

        fuera, fuera_arreglo = [], []
        for sid in noms:
            for mod in (por_skill.get(sid) or []):
                if mod not in visibles:
                    fuera.append((sid, mod))
                if mod not in con_arreglo:
                    fuera_arreglo.append((sid, mod))
        if fuera:
            huerfanas += 1
            for sid, mod in fuera:
                cuenta[mod] = cuenta.get(mod, 0) + 1
            if len(ejemplos) < 6:
                ejemplos.append((informal[:64], fuera[0]))
        if fuera_arreglo:
            huerfanas_con_arreglo += 1

    print("\nCONSULTAS DE PROOFNET: %d" % len(filas))
    print("  reciben algun nombre del grafo      : %d" % con_nombre)
    print("  y ALGUNO no se puede importar       : %d  (%.1f %% de las que "
          "reciben)" % (huerfanas,
                        100.0 * huerfanas / max(1, con_nombre)))
    print("  y con el arreglo —el modulo del nombre OFRECIDO, siempre—: "
          "%d  (%.1f %%)"
          % (huerfanas_con_arreglo,
             100.0 * huerfanas_con_arreglo / max(1, con_nombre)))
    print("\n  los modulos que mas faltan SIN el arreglo:")
    for mod, k in sorted(cuenta.items(), key=lambda kv: -kv[1])[:8]:
        print("     %4d x  %s" % (k, mod))
    print("\n  ejemplos:")
    for texto, (sid, mod) in ejemplos:
        print("     %-66s %s -> %s" % (texto, sid, mod))

    print("\n  (k = PLAZAS_CON_NOMBRES = %d)" % PLAZAS_CON_NOMBRES)
    if huerfanas:
        print("\nLECTURA: en esas consultas el sistema le da al modelo un "
              "nombre\nque el fichero que compila NO puede resolver. El grafo "
              "acierta y Lean\nfalla, y el fallo se lee como un error del "
              "alumno o del modelo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
