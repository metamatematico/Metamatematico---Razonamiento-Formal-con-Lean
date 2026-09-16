# -*- coding: utf-8 -*-
"""
De concepto a modulo: el puente que le faltaba al grafo para elegir imports.

El grafo sabe que `ring-theory` es `RingCat` y que `ideals-quotient-rings` es
`Ideal` — 95% de esos nombres verificados con `#check`. Pero un import no pide
un identificador, pide un MODULO: `Mathlib.Algebra.Category.Ring.Basic`. Este
script construye ese mapa recorriendo el fuente y anotando en que fichero se
declara cada nombre.

POR QUE IMPORTA. `_normalize_code` descarta `import Mathlib` —cargarlo entero
se medio en 742 s, muy por encima del timeout— y lo sustituye por una cabecera
estrecha mas imports elegidos POR PALABRAS CLAVE del enunciado. Ese es hoy el
punto donde se decide que ve Lean, y lo decide un diccionario de terminos, no
la estructura de conceptos que el sistema ya tiene.

El mapa se guarda en disco: recorrer Mathlib entero tarda, y no cambia hasta
que cambie la version.

    python -m scripts.mapa_modulos_mathlib
"""
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

RAIZ = "E:/Metamatematico"
MATHLIB = RAIZ + "/.lake/packages/mathlib/Mathlib"
SALIDA = RAIZ + "/data/mathlib_modulos.json"

#: MODULOS PUESTOS A MANO, y solo cuando el nombre EXISTE y el indice no lo ve.
#:
#: `DECL` reconoce `structure/def/abbrev/class/inductive` con el nombre pegado
#: a la palabra clave. Se le escapan declaraciones que Mathlib escribe de otra
#: forma —`MeasureTheory.integral` es la integral de Bochner, definida con la
#: firma partida en varias lineas— y entonces el nodo se queda sin nada que
#: importar aunque su nombre sea perfectamente bueno: `#check` los acepta con
#: Mathlib entero.
#:
#: Es curacion, no parche: cada uno lo decidio el autor en la hoja, mirando
#: cual de los modulos candidatos usan los enunciados. NO SE USA para tapar un
#: nombre que no existe —para eso la decision es reescribir el nombre o
#: quitarlo— y `main()` comprueba contra el disco que el fichero este.
MODULO_A_MANO = {
    "conditional-expectation": [
        "Mathlib.MeasureTheory.Function.ConditionalExpectation.Basic"],
    # La de Bochner, no la de Lebesgue: los enunciados usan la primera. La de
    # Lebesgue a valores en [0, inf] es `MeasureTheory.lintegral`, en
    # Mathlib.MeasureTheory.Integral.Lebesgue.Basic.
    "lebesgue-integration": [
        "Mathlib.MeasureTheory.Integral.Bochner.Basic"],
    # `AlgebraicGeometry.Proj` es correcto y no hay mejor: Mathlib no tiene
    # «variedad proyectiva», solo el Proj de un algebra graduada.
    "projective-varieties": [
        "Mathlib.AlgebraicGeometry.ProjectiveSpectrum.Scheme"],
}

DECL = re.compile(
    r"^\s*(?:@\[[^\]]*\]\s*)?(?:private\s+|protected\s+|noncomputable\s+)*"
    r"(?:structure|def|abbrev|class|inductive)\s+([A-Za-z_][\w.']*)")
NS = re.compile(r"^\s*namespace\s+([A-Za-z_][\w.']*)")
END = re.compile(r"^\s*end\s+([A-Za-z_][\w.']*)")


def modulo_de(ruta):
    """`.../Mathlib/Algebra/Ring/Basic.lean` -> `Mathlib.Algebra.Ring.Basic`."""
    rel = os.path.relpath(ruta, os.path.dirname(MATHLIB))
    return rel[:-5].replace(os.sep, ".").replace("/", ".")


def construir():
    """nombre cualificado -> modulo donde se declara."""
    mapa, ficheros = {}, 0
    for raiz, _d, fs in os.walk(MATHLIB):
        for f in fs:
            if not f.endswith(".lean"):
                continue
            ruta = os.path.join(raiz, f)
            ficheros += 1
            try:
                lineas = io.open(ruta, encoding="utf-8",
                                 errors="replace").read().splitlines()
            except Exception:
                continue
            mod, pila = modulo_de(ruta), []
            for l in lineas:
                m = NS.match(l)
                if m:
                    pila.append(m.group(1))
                    continue
                m = END.match(l)
                if m:
                    if pila and pila[-1] == m.group(1):
                        pila.pop()
                    continue
                m = DECL.match(l)
                if m:
                    largo = ".".join(pila + [m.group(1)]) if pila else m.group(1)
                    # el primero gana: los ficheros `Basic` suelen ir antes y
                    # son los que uno quiere importar
                    # Los ficheros de `Mathlib.Tactic.*` declaran nombres de
                    # teoria de paso (`Continuous` aparece en Tactic.FunProp) y
                    # con la regla «el primero gana» se quedaban con el nombre.
                    # Importar una tactica para hablar de topologia no es util:
                    # lo que se busca es donde vive la TEORIA.
                    if mod.startswith("Mathlib.Tactic."):
                        continue
                    mapa.setdefault(largo, mod)
    return mapa, ficheros


def _lean_existe(mod):
    """¿`Mathlib.Data.Set.Basic` es un fichero de verdad, o solo una carpeta?"""
    return os.path.exists(os.path.join(
        os.path.dirname(MATHLIB), mod.replace(".", os.sep) + ".lean"))


def _hijos_lean(mod):
    """Los modulos importables que cuelgan de este, si es un directorio."""
    d = os.path.join(os.path.dirname(MATHLIB), mod.replace(".", os.sep))
    if not os.path.isdir(d):
        return []
    fuera = []
    for r, _s, fs in os.walk(d):
        for f in fs:
            if f.endswith(".lean"):
                rel = os.path.relpath(os.path.join(r, f),
                                      os.path.dirname(MATHLIB))
                fuera.append(rel[:-5].replace(os.sep, ".").replace("/", "."))
    return fuera


def _hechos_por_modulo():
    """modulo -> cuantos hechos declara, segun el indice de lemas."""
    cnt = {}
    ruta = RAIZ + "/data/lemas_mathlib.jsonl"
    if not os.path.exists(ruta):
        return cnt
    for linea in io.open(ruta, encoding="utf-8"):
        try:
            d = json.loads(linea)
        except ValueError:
            continue
        m = d.get("modulo") or d.get("module")
        if m:
            cnt[m] = cnt.get(m, 0) + 1
    return cnt


def modulos_de_los_derivados(hechos):
    """Los nodos que saben su modulo, resueltos a algo IMPORTABLE.

    POR QUE HACE FALTA ESTA SEGUNDA FUENTE. El mapa de arriba se construye
    resolviendo los NOMBRES verificados de cada skill al fichero donde se
    declaran, y los 125 nodos MODULO y los 22 AREA no tienen nombres. Se
    quedaban fuera los 147: el mapa conocia 76 de 320 nodos, y
    `_modulos_mathlib` —que es quien elige los imports— devolvia vacio en
    cuanto las primeras skills eran de esas.

    Pero esos nodos SI saben su modulo: lo llevan en `metadata["modulo"]`,
    puesto por el generador desde la ruta real del fichero.

    Y NO SE PUEDE USAR TAL CUAL. `Mathlib.Data.Set` es un DIRECTORIO:
    `import Mathlib.Data.Set` NO COMPILA. Medido sobre los 147, solo 8 son
    importables directamente. Asi que se resuelve al fichero de verdad:

        1. `<modulo>.Basic`  — la convencion de Mathlib     96 de 147
        2. `<modulo>.Defs`   — cuando no hay Basic           7
        3. el hijo con MAS HECHOS, del indice de lemas      41
        4. si no hay ningun hijo utilizable, se queda fuera  3

    El paso 3 no es una convencion, es un dato. Y todo lo que sale de aqui se
    comprueba contra el disco antes de escribirse: un import inventado no
    ralentiza la compilacion, la rompe.
    """
    from nucleo.core import Nucleo
    from nucleo.graph.category import SkillCategory

    n = Nucleo.__new__(Nucleo)
    n._graph = SkillCategory()
    Nucleo._load_foundational_skills(n)

    #: Nombres de area que NO son un directorio de Mathlib.
    #:
    #: `areas.py` toma los nombres de la presentacion de Mathlib, y 21 de los
    #: 22 son directorios reales. `OrderTheory` es la excepcion: la rama se
    #: llama `Mathlib/Order`. Va como tabla explicita y no como heuristica
    #: —quitar el sufijo «Theory»— porque `RingTheory`, `MeasureTheory`,
    #: `ModelTheory`, `NumberTheory`, `SetTheory` y `RepresentationTheory` SI
    #: son directorios, y la heuristica los romperia todos.
    ALIAS = {"Mathlib.OrderTheory": "Mathlib.Order"}

    fuera, motivos, sin_resolver = {}, {}, []
    for s in n._graph.skills:
        mod = (s.metadata or {}).get("modulo")
        if not mod:
            continue
        mod = ALIAS.get(mod, mod)
        if _lean_existe(mod):
            fuera[s.id], motivos[s.id] = [mod], "directo"
            continue
        hijos = _hijos_lean(mod)
        if not hijos:
            sin_resolver.append((s.id, mod))
            continue
        if mod + ".Basic" in hijos:
            elegido, por = mod + ".Basic", "Basic"
        elif mod + ".Defs" in hijos:
            elegido, por = mod + ".Defs", "Defs"
        else:
            elegido = max(hijos, key=lambda h: (hechos.get(h, 0), -len(h)))
            por = "mas-hechos"
            if hechos.get(elegido, 0) == 0:
                sin_resolver.append((s.id, mod))
                continue
        fuera[s.id], motivos[s.id] = [elegido], por
    return fuera, motivos, sin_resolver


def main():
    print("recorriendo el fuente de Mathlib...")
    mapa, ficheros = construir()
    print("  %d ficheros, %d nombres cualificados" % (ficheros, len(mapa)))
    if not mapa:
        print("  ATENCION: mapa vacio — revisa MATHLIB=%s" % MATHLIB)
        return 1

    # cobertura sobre el vocabulario del grafo
    # `nombres_de_trabajo` y no `e.lean`: para group-theory `e.lean` es
    # `GrpCat`, la categoria — correcta como identidad y pesima como import,
    # porque `Algebra.Category.Grp.Basic` esta arriba del DAG de Mathlib. Lo
    # que hay que importar para hablar de grupos es `Subgroup`, `MonoidHom`.
    #
    # AQUI NO SE FILTRA POR LA MARCA, Y ANTES SI.  Habia un
    # `if e.marca not in VERTICES: continue`, y era un error de tipo.
    #
    # La marca contesta «¿esta etiqueta es un objeto o una flecha DEL GRAFO?».
    # Este mapa contesta «¿en que fichero de Mathlib se declara este nombre?».
    # La segunda pregunta no depende de la primera: `TensorProduct` vive en
    # `Mathlib.LinearAlgebra.TensorProduct` tanto si `tensor-products` es
    # vertice como si es arista. Y que puede ser vertice —en la categoria de
    # funtores— esta demostrado en `FlechasComoObjetos.lean`.
    #
    # LO QUE COSTABA, medido: las 28 etiquetas marcadas `F` SI inyectan su
    # nombre en el prompt (`nombres_de_trabajo` no mira la marca), y el mapa
    # les negaba el modulo. O sea: el sistema le ofrecia `TensorProduct` al
    # modelo y luego no tenia como importarlo. De las 28, DIEZ resuelven a un
    # modulo que la cabecera fija NO alcanza transitivamente —character-theory,
    # cohomology, conformal-maps, fundamental-group, generating-functions,
    # graph-coloring, homology, ideal-class-group, kan-extensions,
    # random-variables—; las otras 15 ya se alcanzaban y 3 no resuelven nombre.
    # Diez casos de `unknown identifier` garantizado, por un filtro que
    # contestaba a otra pregunta.
    from nucleo.graph.interpretacion import (
        VEREDICTO, nombres_de_trabajo, RETIRADAS_DEL_GRAFO)
    invalidos = {"EuclideanGeometry", "Ideal.Quotient", "QuotientGroup",
                 "RelCWComplex", "Turing.TM0", "Turing.TM1"}
    # SE ANOTA LA CAUSA, porque el hueco es curacion y quien lo cure
    # necesita saber por que falla cada uno. Antes los nombres de `invalidos`
    # se saltaban en silencio y no aparecian en ninguna cuenta.
    por_skill, sin_modulo = {}, []
    for k, e in VEREDICTO.items():
        # LAS RETIRADAS NO ENTRAN EN EL MAPA. Siguen en `VEREDICTO` a
        # proposito —el veredicto es un dato editorial y borrar una fila
        # moveria el recuento publicado del autor— pero este mapa contesta
        # «que modulo importar para este NODO», y un nodo retirado no se
        # empareja con ninguna consulta: su entrada seria un import que
        # nadie puede pedir.
        if k in RETIRADAS_DEL_GRAFO:
            continue
        nombres = nombres_de_trabajo(k)
        if not nombres:
            continue
        mods, fallos = [], []
        for pieza in re.split(r"[,+]", nombres):
            n = pieza.strip()
            if not n:
                continue
            if n in invalidos:
                fallos.append((n, "en la lista `invalidos` del mapa"))
                continue
            m = mapa.get(n)
            if m:
                mods.append(m)
            else:
                fallos.append((n, "el indice de Mathlib no lo declara"))
        # la curacion a mano entra ANTES de dar el hueco por perdido
        mods.extend(MODULO_A_MANO.get(k, []))
        if mods:
            por_skill[k] = sorted(dict.fromkeys(mods))[:3]
        else:
            # los que se quedan SIN NINGUN modulo: estos son los que rompen
            # consultas, porque su nombre si llega al prompt
            for n, causa in fallos:
                sin_modulo.append({"skill": k, "marca": e.marca,
                                   "nombre": n, "causa": causa})

    print("\n=== COBERTURA SOBRE EL GRAFO ===")
    print("  skills con al menos un modulo: %d" % len(por_skill))
    huerfanas = sorted({x["skill"] for x in sin_modulo})
    print("  dan nombre y NO dan modulo   : %d" % len(huerfanas))
    for x in sin_modulo:
        print("     %-28s %-2s %-40s %s"
              % (x["skill"], x["marca"], x["nombre"], x["causa"]))

    print("\n  ejemplos:")
    for k in list(por_skill)[:6]:
        print("     %-26s -> %s" % (k, ", ".join(por_skill[k])))

    # ── SEGUNDA FUENTE: los nodos que saben su propio modulo ──────────────
    print("\n=== NODOS QUE SABEN SU MODULO (los generados) ===")
    hechos = _hechos_por_modulo()
    print("  indice de lemas: %d modulos con hechos" % len(hechos))
    derivados, motivos, sin_resolver = modulos_de_los_derivados(hechos)
    cuenta = {}
    for v in motivos.values():
        cuenta[v] = cuenta.get(v, 0) + 1
    print("  resueltos: %d   (%s)"
          % (len(derivados),
             " · ".join("%s %d" % kv for kv in sorted(cuenta.items()))))
    if sin_resolver:
        print("  sin resolver: %d" % len(sin_resolver))
        for k, m in sin_resolver[:5]:
            print("     %-30s %s" % (k, m))

    nuevos = {k: v for k, v in derivados.items() if k not in por_skill}
    por_skill.update(nuevos)
    print("  se anaden %d skills que el mapa no conocia" % len(nuevos))

    # ── LA GUARDA: nada que no sea un fichero real llega al disco ─────────
    #
    # Un import inventado no ralentiza la compilacion: la rompe, y lo haria en
    # TODAS las consultas a la vez. Se comprueba contra el disco.
    malos = []
    for sid, mods in por_skill.items():
        for m in mods:
            if not _lean_existe(m):
                malos.append((sid, m))
    if malos:
        print("\n  ABORTADO: %d modulos que no existen como fichero" % len(malos))
        for sid, m in malos[:10]:
            print("     %-30s %s" % (sid, m))
        return 1
    print("  comprobado contra el disco: los %d modulos existen"
          % sum(len(v) for v in por_skill.values()))

    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    io.open(SALIDA, "w", encoding="utf-8").write(json.dumps(
        {"por_skill": por_skill, "nombres": len(mapa),
         # QUEDA ESCRITO PARA QUE SE PUEDA CURAR. Cada entrada es una etiqueta
         # que inyecta su nombre en el prompt y no tiene con que importarlo:
         # `scripts/hoja_de_curacion.py` las publica como tarea pendiente.
         "sin_modulo": sin_modulo},
        ensure_ascii=False, indent=2))
    print("\n  skills en el mapa: %d  (%d por nombre verificado + %d por modulo propio)"
          % (len(por_skill), len(por_skill) - len(nuevos), len(nuevos)))
    print("  -> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    sys.exit(main())
