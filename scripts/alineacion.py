# -*- coding: utf-8 -*-
"""Auditor de alineacion: donde el sistema se contradice a si mismo.

QUE COMPRUEBA Y POR QUE NO LO HACEN LOS TESTS
---------------------------------------------
Los 1094 tests comprueban que cada pieza cumple SU contrato. Esto comprueba
otra cosa: que las piezas dicen lo MISMO entre si. Son fallos que no rompen
nada al ejecutar y por eso no los caza una suite:

  1. un id retirado que sigue vivo en el codigo de otro script
  2. un `data/*.json` generado del grafo que se quedo en una version anterior
  3. un documento publicado que nombra nodos que ya no existen
  4. algo DECLARADO y nunca APLICADO — `FUSIONES` llevaba ocho declaradas y
     cero aplicadas, y nadie se habia dado cuenta porque ningun test
     preguntaba «¿y esto se hizo?»

LA DISTINCION QUE SOSTIENE TODO EL AUDITOR: HISTORIA vs REFERENCIA VIVA.
Un id retirado NO es un error en cualquier sitio. `interpretacion.py` conserva
la fila de `cardinal-arithmetic` a proposito —el veredicto es un dato
editorial— y `conjeturas_etiquetas.py` guarda las conjeturas de la primera
pasada, que hablan de un pasado real. Borrarlas seria perder la trazabilidad
que este proyecto cuida.

Lo que si es un error es que el codigo BUSQUE ese id en el grafo de hoy. Asi
que el auditor no busca texto: parsea cada fichero con `ast` y mira solo los
literales que estan FUERA de docstrings y comentarios. Un id en prosa es
historia; un id en un `dict` que alguien consulta es una referencia rota.

    python -m scripts.alineacion          informe
    python -m scripts.alineacion --fallar  ademas sale con codigo 1 si hay algo
"""
from __future__ import annotations

import argparse
import ast
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)

#: Ficheros donde un id retirado es HISTORIA y debe quedarse.
#:
#: `interpretacion.py` conserva la fila del retirado con la marca que le puso
#: el autor: es lo que impide que renombrar un nodo mueva su recuento
#: publicado. Los tests comprueban precisamente eso. Y `conjeturas_*` guarda
#: lo que se penso antes de medir, que es el dato con el que se juzga si medir
#: sirvio de algo.
HISTORIA = {
    os.path.join("nucleo", "graph", "interpretacion.py"),
    os.path.join("scripts", "alineacion.py"),
    os.path.join("tests", "test_interpretacion.py"),
    os.path.join("tests", "test_funtor.py"),
}

#: Documentos que son un ACTA y no un estado: describen lo que se decidio en
#: una fecha, citando el grafo de esa fecha. Se quedan como estan.
ACTAS = {
    #: el registro de una verificacion con Lean en una fecha: dice que
    #: `#check` acepto estos nombres ese dia. Regenerarlo cuesta una corrida
    #: de Lean entera y no cambiaria lo que afirma — que es un hecho fechado,
    #: no un estado.
    os.path.join("data", "teoria_faltante_verificada.json"),
    os.path.join("docs", "curacion_interna_veredicto.md"),
    os.path.join("docs", "curacion_interna_veredicto.pdf"),
    os.path.join("docs", "CURACION_RAMAS.md"),
    os.path.join("docs", "CURACION_RAMAS.tex"),
    os.path.join("docs", "CURACION_PENDIENTE.md"),
    os.path.join("docs", "CURACION_PENDIENTE.tex"),
}

#: Declaraciones hechas a proposito y todavia sin aplicar, con el motivo.
#: Sin esta tabla el auditor gritaria por seis fusiones que estan declaradas
#: para documentar una equivalencia, no para ejecutarse ya.
SIN_APLICAR_A_PROPOSITO = {
    "homological-algebra-cat": "declarada; el nodo sigue por su papel en los "
                               "colimites de algebra homologica",
    "differential-geometry": "declarada; fundirla con smooth-manifolds "
                             "perderia el area `geometry`",
    "differential-topology": "declarada; mismo caso",
    "proof-theory": "NO se aplica: el veredicto sobre las 48 la declara RAMA "
                    "con `fol-deduction` de hijo, y fundirla perderia el "
                    "enrutado. Gana el veredicto, que es posterior",
    "schemes": "declarada; el nodo sostiene la cadena de geometria algebraica",
    "algebraic-topology": "declarada; fundirla colapsaria el area `topology`",
}


def _grafo():
    import warnings
    import logging
    warnings.filterwarnings("ignore")
    logging.disable(logging.WARNING)
    from nucleo.core import Nucleo
    from nucleo.graph.category import SkillCategory
    n = Nucleo.__new__(Nucleo)
    n._graph = SkillCategory()
    Nucleo._load_foundational_skills(n)
    return n._graph


#: Nombres de tabla que son un REGISTRO y no una consulta.
#:
#: Una tabla llamada `RESUELTAS_POR_EL_VEREDICTO` existe justamente para
#: guardar ids que ya no estan: es su contenido, no su fallo. Silenciar el
#: fichero entero seria demasiado —ahi mismo puede haber una referencia rota—
#: asi que se silencia LA TABLA, por su nombre.
#:
#: El nombre es el contrato: si alguien mete un lookup dentro de una tabla
#: que se llama «resueltas», el problema es el nombre.
TABLAS_DE_REGISTRO = re.compile(
    r"^(RESUELTAS|RETIRADAS|DECIDIDOS|CONJETURAS|HISTORIA|ACTAS|"
    r"NOTA|MOTIVOS|SIN_APLICAR|SIN_VERIFICAR|NUNCA_CADUCA)")


def _literales_de_codigo(ruta):
    """Los literales de cadena que NO son docstring ni tabla de registro.

    Es la unica forma de separar «este script habla de un nodo retirado» de
    «este script busca un nodo retirado». La primera es historia y la segunda
    esta rota, y a grep le parecen iguales.
    """
    try:
        arbol = ast.parse(io.open(ruta, encoding="utf-8").read())
    except (SyntaxError, UnicodeDecodeError):
        return []
    docstrings = set()
    for nodo in ast.walk(arbol):
        if not isinstance(nodo, (ast.Assign, ast.AnnAssign)):
            continue
        objetivos = (nodo.targets if isinstance(nodo, ast.Assign)
                     else [nodo.target])
        if not any(isinstance(t, ast.Name) and TABLAS_DE_REGISTRO.match(t.id)
                   for t in objetivos):
            continue
        for dentro in ast.walk(nodo.value):
            if isinstance(dentro, ast.Constant) and isinstance(dentro.value, str):
                docstrings.add(id(dentro))
    for nodo in ast.walk(arbol):
        if isinstance(nodo, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef,
                             ast.ClassDef)):
            d = ast.get_docstring(nodo, clean=False)
            if d is not None and nodo.body:
                primero = nodo.body[0]
                if isinstance(primero, ast.Expr):
                    docstrings.add(id(primero.value))
    fuera = []
    for nodo in ast.walk(arbol):
        if (isinstance(nodo, ast.Constant) and isinstance(nodo.value, str)
                and id(nodo) not in docstrings):
            fuera.append((nodo.lineno, nodo.value))
    return fuera


def _es_id_de_nodo(etiqueta):
    """Si la etiqueta solo puede ser un id de nodo, o tambien una palabra.

    LA PRIMERA VERSION DEL AUDITOR DIO DOCE FALSOS POSITIVOS y todos eran el
    mismo: `homology` y `cohomology` aparecian en `areas.py`, en las keywords
    de `math_domains.py` y en el vocabulario de `embeddings.py`. Ahi no son
    referencias a un nodo: son PALABRAS, y son las palabras con las que un
    usuario pregunta por homologia. Borrarlas romperia el emparejador.

    Los ids de este grafo llevan guion —`cardinal-arithmetic`,
    `sequent-calculus`— y una palabra suelta nunca es inequivoca. Asi que las
    de una sola palabra pasan a aviso y no a fallo: un auditor que se dispara
    con codigo correcto entrena a ignorarlo, que es peor que no tenerlo.
    """
    return "-" in etiqueta


def ids_retirados_vivos(retirados):
    """CHEQUEO 1 · un id retirado consultado desde codigo vivo."""
    fallos, avisos = [], []
    for base, _dirs, ficheros in os.walk(RAIZ):
        if any(p in base for p in (".lake", ".git", "__pycache__", "node_modules")):
            continue
        for f in ficheros:
            if not f.endswith(".py"):
                continue
            ruta = os.path.join(base, f)
            rel = os.path.relpath(ruta, RAIZ)
            if rel in HISTORIA:
                continue
            for linea, texto in _literales_de_codigo(ruta):
                if texto in retirados:
                    (fallos if _es_id_de_nodo(texto)
                     else avisos).append((rel, linea, texto))
    return fallos, avisos


def datos_derivados_al_dia(g):
    """CHEQUEO 2 · un `data/*.json` que cita nodos que ya no existen.

    Estos ficheros se generan del grafo. Si nombran un nodo retirado es que
    nadie los regenero, y entonces cualquier cifra que salga de ellos —o
    cualquier documento que las cite— esta describiendo un grafo anterior.
    """
    vivos = set(g.skill_ids)
    fallos = []
    carpeta = os.path.join(RAIZ, "data")
    for f in sorted(os.listdir(carpeta)):
        if not f.endswith(".json"):
            continue
        rel = os.path.join("data", f)
        if rel in ACTAS:
            continue
        ruta = os.path.join(carpeta, f)
        try:
            crudo = io.open(ruta, encoding="utf-8").read()
        except (OSError, UnicodeDecodeError):
            continue
        muertos = set()
        # se buscan ids con la forma de los del grafo, entre comillas
        for m in re.finditer(r'"([a-z][a-z0-9]*(?:-[a-z0-9]+)+)"', crudo):
            cand = m.group(1)
            if cand in RETIRADAS_GLOBALES() and cand not in vivos:
                muertos.add(cand)
        if muertos:
            fallos.append((os.path.join("data", f), sorted(muertos)))
    return fallos


def publicados_con_ids_muertos(g):
    """CHEQUEO 3 · un documento publicado que nombra nodos retirados."""
    vivos = set(g.skill_ids)
    fallos, avisos = [], []
    for carpeta, exts in ((RAIZ, (".md",)), (os.path.join(RAIZ, "docs"),
                                             (".html", ".md"))):
        for f in sorted(os.listdir(carpeta)):
            if not f.endswith(exts):
                continue
            rel = os.path.relpath(os.path.join(carpeta, f), RAIZ)
            if rel in ACTAS:
                continue
            try:
                crudo = io.open(os.path.join(carpeta, f),
                                encoding="utf-8").read()
            except (OSError, UnicodeDecodeError):
                continue
            muertos = sorted({x for x in RETIRADAS_GLOBALES()
                              if x in crudo and x not in vivos})
            duros = [x for x in muertos if _es_id_de_nodo(x)]
            blandos = [x for x in muertos if not _es_id_de_nodo(x)]
            if duros:
                fallos.append((rel, duros))
            if blandos:
                avisos.append((rel, blandos))
    return fallos, avisos


def declarado_sin_aplicar(g):
    """CHEQUEO 4 · lo que se declaro y nunca se hizo.

    `FUSIONES` llevaba OCHO declaradas y CERO aplicadas: los ocho seguian
    siendo nodo vivo. No lo caza ningun test porque cada pieza cumplia su
    contrato — la tabla declaraba y el grafo cargaba— y nadie preguntaba si
    una cosa correspondia con la otra.

    Una declaracion sin aplicar no es un error POR SI MISMA: puede estar ahi
    para documentar una equivalencia. Lo que es un error es que no se sepa
    cual es cual, asi que las que se quedan llevan su motivo escrito.
    """
    from nucleo.graph import interpretacion as I
    vivos = set(g.skill_ids)
    fallos = []
    for retirada, superviviente in sorted(I.FUSIONES.items()):
        aplicada = retirada not in vivos
        if aplicada:
            if retirada not in I.FUSIONES_APLICADAS:
                fallos.append((retirada, "no esta en el grafo y NO figura en "
                                         "FUSIONES_APLICADAS"))
            if superviviente not in vivos:
                fallos.append((retirada, "fundida en `%s`, que tampoco esta "
                                         "en el grafo" % superviviente))
            continue
        if retirada in I.FUSIONES_APLICADAS:
            fallos.append((retirada, "figura como aplicada y sigue siendo "
                                     "nodo vivo"))
        elif retirada not in SIN_APLICAR_A_PROPOSITO:
            fallos.append((retirada, "declarada en FUSIONES, sin aplicar y "
                                     "sin motivo escrito"))
    return fallos


def veredicto_contra_grafo(g):
    """CHEQUEO 5 · la tabla y el grafo se nombran igual."""
    from nucleo.graph import interpretacion as I
    vivos = set(g.skill_ids)
    fallos = []
    permitidos = (set(I.RETIRADAS_DEL_GRAFO) | I.VERTICES_ANADIDOS
                  | I.DEGRADADAS_A_FLECHA)
    for k in sorted(set(I.VEREDICTO) - vivos - permitidos):
        fallos.append((k, "tiene veredicto y no es nodo ni esta declarado "
                          "retirado"))
    for sid in sorted(vivos - set(I.VEREDICTO)):
        md = g.get_skill(sid).metadata or {}
        if md.get("interpretado") is False or md.get("sort") in (
                "MODULO", "AREA"):
            continue
        fallos.append((sid, "es nodo curado y no tiene veredicto"))
    return fallos


def ramas_mudas():
    """CHEQUEO 6 · la regla del rol: una rama no toma nombre nunca."""
    from nucleo.graph import interpretacion as I
    return [(k, I.nombres_de_trabajo(k)) for k in sorted(I.RAMAS_DECLARADAS)
            if (I.nombres_de_trabajo(k) or "").strip()]


def RETIRADAS_GLOBALES():
    """Todo lo que ya no es nodo: retiradas del grafo y degradadas a flecha.

    Era un global que `main()` rellenaba, y desde un test salia vacio — o sea
    que la guardia habria pasado siempre sin comprobar nada. El fallo mas
    barato de cometer al sacar un script a un test, y el mas mudo.
    """
    from nucleo.graph import interpretacion as I
    return set(I.RETIRADAS_DEL_GRAFO) | set(I.DEGRADADAS_A_FLECHA)


#: Los ficheros de medicion que la documentacion cita como cifras actuales.
MEDICIONES = (
    "recuperacion_proofnet.json",
    "banco_docstrings.json",
    "banco_herald.json",
    "funtor_mathlib.json",
)


def mediciones_del_grafo_de_hoy():
    """CHEQUEO 7 · una medicion mas vieja que el grafo que describe.

    `banco_herald.json` decia «10,3 % de precision» y la documentacion lo
    citaba como la cifra de hoy. Se midio sobre un grafo de 352 nodos que
    todavia tenia `sequent-calculus`, `recursion-theory` y
    `cardinal-arithmetic`.

    Ni el fichero ni la documentacion mentian por separado: el fichero decia
    lo que midio y la documentacion lo copiaba bien. Faltaba la pregunta «¿y
    esto sobre que grafo?», que nadie podia hacerse porque el dato no estaba
    escrito. Ahora cada banco escribe la huella del grafo que uso.
    """
    from nucleo.graph.huella import huella_viva, desajuste
    viva = huella_viva()
    fallos = []
    for f in MEDICIONES:
        ruta = os.path.join(RAIZ, "data", f)
        if not os.path.exists(ruta):
            continue
        try:
            d = json.load(io.open(ruta, encoding="utf-8"))
        except (OSError, ValueError):
            continue
        d = desajuste(d.get("grafo") if isinstance(d, dict) else None, viva)
        if d:
            fallos.append((os.path.join("data", f), d))
    return fallos


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--fallar", action="store_true",
                    help="salir con codigo 1 si hay desalineaciones")
    args = ap.parse_args()

    from nucleo.graph import interpretacion as I
    global RETIRADOS_GLOBAL
    RETIRADOS_GLOBAL = set(I.RETIRADAS_DEL_GRAFO) | set(I.DEGRADADAS_A_FLECHA)

    g = _grafo()
    print("ALINEACION DEL SISTEMA")
    print("grafo vivo: %d nodos · %d morfismos · %d etiquetas con veredicto\n"
          % (len(list(g.skills)), len(g.morphisms), len(I.VEREDICTO)))

    total = 0

    print("1 · IDS RETIRADOS CONSULTADOS DESDE CODIGO VIVO")
    f, av = ids_retirados_vivos(RETIRADAS_GLOBALES())
    total += len(f)
    for rel, linea, texto in f:
        print("   FALLO  %-40s:%-5d %s" % (rel, linea, texto))
    if not f:
        print("   (nada: los que quedan estan en prosa, que es historia)")
    if av:
        print("   %d aviso(s): etiqueta de UNA palabra, que tambien es "
              "vocabulario legitimo" % len(av))
        for rel, linea, texto in av[:4]:
            print("      %-40s:%-5d %s" % (rel, linea, texto))

    print("\n2 · DATOS DERIVADOS QUE CITAN NODOS MUERTOS")
    f = datos_derivados_al_dia(g)
    total += len(f)
    for rel, muertos in f:
        print("   %-44s %s" % (rel, ", ".join(muertos)))
    if not f:
        print("   (nada)")

    print("\n3 · DOCUMENTOS PUBLICADOS QUE NOMBRAN NODOS MUERTOS")
    f, av = publicados_con_ids_muertos(g)
    total += len(f)
    for rel, muertos in f:
        print("   FALLO  %-40s %s" % (rel, ", ".join(muertos)))
    if not f:
        print("   (nada)")
    for rel, muertos in av:
        print("   aviso  %-40s %s  (es palabra, no id)"
              % (rel, ", ".join(muertos)))

    print("\n4 · DECLARADO Y NO APLICADO")
    f = declarado_sin_aplicar(g)
    total += len(f)
    for k, motivo in f:
        print("   %-28s %s" % (k, motivo))
    if not f:
        print("   (nada sin motivo escrito; %d fusiones declaradas a "
              "proposito)" % len(SIN_APLICAR_A_PROPOSITO))

    print("\n5 · VEREDICTO CONTRA GRAFO")
    f = veredicto_contra_grafo(g)
    total += len(f)
    for k, motivo in f:
        print("   %-28s %s" % (k, motivo))
    if not f:
        print("   (se nombran igual)")

    print("\n6 · LA REGLA DEL ROL: una rama no toma nombre nunca")
    f = ramas_mudas()
    total += len(f)
    for k, noms in f:
        print("   %-28s ofrece %s" % (k, noms))
    if not f:
        print("   (ninguna de las %d ramas ofrece nombre)"
              % len(I.RAMAS_DECLARADAS))

    print("\n7 · MEDICIONES MAS VIEJAS QUE EL GRAFO QUE DESCRIBEN")
    f = mediciones_del_grafo_de_hoy()
    total += len(f)
    for rel, motivo in f:
        print("   %-32s %s" % (rel, motivo))
    if not f:
        print("   (las %d miden el grafo de hoy)" % len(MEDICIONES))

    print("\n%s" % ("=" * 62))
    if total:
        print("DESALINEACIONES: %d" % total)
    else:
        print("ALINEADO: ninguna de las siete comprobaciones encuentra nada.")
    return 1 if (total and args.fallar) else 0


if __name__ == "__main__":
    raise SystemExit(main())
