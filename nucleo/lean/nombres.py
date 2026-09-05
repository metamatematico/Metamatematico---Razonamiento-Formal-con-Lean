# -*- coding: utf-8 -*-
"""¿Existe este nombre en Mathlib? Y: ¿es verdad lo que la respuesta afirma?

DE DONDE SALE ESTE MODULO
-------------------------
El sistema respondio a «todo espacio vectorial tiene una base» con esta nota:

    «El error es claro: la constante `Module.Basis.exists_basis` no existe en
     Mathlib con ese nombre — es una invencion o un nombre desactualizado.»

Y es FALSO. `#check` sobre el Mathlib instalado devuelve:

    Module.Basis.exists_basis : ∀ (K V) [DivisionRing K] [AddCommGroup V]
      [Module K V], ∃ s, Nonempty (Module.Basis (↑s) K V)

El error de Lean tampoco decia eso. Decia:

    Application type mismatch: the argument `s` has type `Set V` … expected
    `Type u_3`  in the application  Exists.intro s

O sea: el lema existe, y lo que no encaja es el ENUNCIADO que se intento
probar con el. El traductor invento un diagnostico y lo presento como «el
error es claro».

POR QUE ESO ES GRAVE AQUI Y NO EN OTRO SISTEMA
----------------------------------------------
La tesis de este proyecto es que la verdad matematica la produce Lean y el
modelo es solo la boca. Una nota que contradice al verificador —y de paso
contradice a los 183 351 nombres que el propio repositorio tiene en
`data/lemas_mathlib.jsonl`— rompe esa tesis en el unico sitio donde el usuario
la puede comprobar.

Y manda a quien lea la nota a buscar el nombre correcto de un lema que ya
tenia el nombre correcto.

LO QUE HACE ESTE MODULO
-----------------------
    existe(nombre)            ¿esta en Mathlib? Sobre los 183 351, no sobre
                              los 34 084 sustantivos —`sustantivos.existe`
                              solo conoce tipos y clases, y para un LEMA
                              tambien diria que no—.
    parecidos(nombre)         los nombres reales mas cercanos, para cuando de
                              verdad falta
    revisar_afirmaciones(t)   busca en un texto las frases que niegan la
                              existencia de un nombre y comprueba cada una

LO QUE NO HACE. No corrige matematicas ni juzga si el lema es el adecuado:
solo comprueba si el NOMBRE existe. Una nota puede seguir estando equivocada
sobre todo lo demas.
"""
from __future__ import annotations

import difflib
import io
import json
import pathlib
import re
from typing import Iterable, Optional

RAIZ = pathlib.Path(__file__).resolve().parent.parent.parent
BANCO = RAIZ / "data" / "lemas_mathlib.jsonl"

_NOMBRES: Optional[frozenset] = None
_CORTOS: Optional[dict] = None


#: Los sustantivos —tipos, clases, estructuras— viven en OTRO fichero.
#:
#: LOS DOS INDICES SON COMPLEMENTARIOS Y NINGUNO BASTA SOLO. Medido:
#:
#:     Module.Basis                lemas=NO   sustantivos=SI   (es una estructura)
#:     Module.Basis.exists_basis   lemas=SI   sustantivos=NO   (es un teorema)
#:
#: La primera version de este modulo leia solo los lemas, asi que habria dicho
#: que `Module.Basis` no existe — exactamente el error que existe para cazar.
_SUSTANTIVOS = RAIZ / "data" / "sustantivos_mathlib.jsonl"


def _cargar() -> None:
    """Carga los nombres una vez. ~1 s y ~7 MB sobre los dos ficheros."""
    global _NOMBRES, _CORTOS
    if _NOMBRES is not None:
        return
    nombres, cortos = set(), {}

    def _mete(n: str) -> None:
        if n:
            nombres.add(n)
            cortos.setdefault(n.rsplit(".", 1)[-1], []).append(n)

    for ruta in (BANCO, _SUSTANTIVOS):
        try:
            with io.open(ruta, encoding="utf-8") as fh:
                for linea in fh:
                    try:
                        d = json.loads(linea)
                    except Exception:                          # noqa: BLE001
                        continue
                    # SOLO EL NOMBRE CUALIFICADO. `sustantivos.existe` acepta
                    # tambien el corto —legitimo para su uso, que es la puerta
                    # previa a Lean bajo un `open`— pero aqui se DESMIENTE a
                    # alguien, y para eso el corto es demasiado laxo: `Basis` a
                    # pelo da «unknown identifier», asi que quien diga que no
                    # existe tiene razon y corregirle seria mentir.
                    _mete(d.get("nombre") or d.get("name") or "")
        except FileNotFoundError:
            continue
    _NOMBRES, _CORTOS = frozenset(nombres), cortos


def disponible() -> bool:
    _cargar()
    return bool(_NOMBRES)


def cuantos() -> int:
    _cargar()
    return len(_NOMBRES or ())


def existe(nombre: str) -> bool:
    """¿Este identificador es un nombre real de Mathlib?

    Se comprueba tal cual y tambien sin el prefijo de espacio de nombres, para
    que `Basis.exists_basis` no se declare inexistente cuando lo que hay es
    `Module.Basis.exists_basis` y un `open Module` delante.
    """
    _cargar()
    if not nombre or not _NOMBRES:
        return False
    n = nombre.strip().strip("`").lstrip("@")
    if n in _NOMBRES:
        return True
    # sufijo: `Basis.exists_basis` contra `Module.Basis.exists_basis`
    return any(x.endswith("." + n) for x in _CORTOS.get(n.rsplit(".", 1)[-1], ()))


def nombre_completo(nombre: str) -> str:
    """El nombre completo si lo que se dio era un sufijo. Cadena vacia si no."""
    _cargar()
    if not _NOMBRES:
        return ""
    n = nombre.strip().strip("`").lstrip("@")
    if n in _NOMBRES:
        return n
    for x in _CORTOS.get(n.rsplit(".", 1)[-1], ()):
        if x.endswith("." + n):
            return x
    return ""


def parecidos(nombre: str, k: int = 5) -> list:
    """Los nombres reales mas cercanos. Para cuando el nombre SI falta."""
    _cargar()
    if not _NOMBRES:
        return []
    n = nombre.strip().strip("`").lstrip("@")
    corto = n.rsplit(".", 1)[-1]
    # primero los que comparten el nombre corto: son los candidatos de verdad
    directos = list(_CORTOS.get(corto, ()))[:k]
    if len(directos) >= k:
        return directos
    resto = difflib.get_close_matches(n, list(_CORTOS.keys()), n=k, cutoff=0.72)
    for c in resto:
        for x in _CORTOS.get(c, ()):
            if x not in directos:
                directos.append(x)
            if len(directos) >= k:
                return directos
    return directos


# ═══════════════════════════════════════════════════════════════════════════
# COMPROBAR LO QUE UNA RESPUESTA AFIRMA
# ═══════════════════════════════════════════════════════════════════════════
#: Las maneras en que una explicacion niega que un nombre exista. Se buscan
#: por FRASE: dentro de la frase que lleva una de estas marcas se miran los
#: identificadores, y solo esos. Buscar en todo el texto marcaria nombres
#: citados en frases que no niegan nada.
_NIEGA = (
    "no existe", "no existen", "no esta en mathlib", "no está en mathlib",
    "no aparece en mathlib", "es una invencion", "es una invención",
    "inventado", "inventada", "nombre desactualizado", "no es un lema real",
    "does not exist", "doesn't exist", "unknown constant", "no such",
)

#: Un identificador de Lean: `Module.Basis.exists_basis`, `Nat.succ_le_iff`.
#: Se exige al menos un punto o una mayuscula inicial para no coger palabras
#: sueltas del castellano.
_IDENT = re.compile(
    r"`([A-Za-z_][A-Za-z0-9_'!?]*(?:\.[A-Za-z_][A-Za-z0-9_'!?]*)+)`"
    r"|\b([A-Z][A-Za-z0-9_']*(?:\.[A-Za-z_][A-Za-z0-9_'!?]*)+)\b")

#: Cuanto texto se mira alrededor de un identificador para decidir si la
#: frase lo esta negando.
#:
#: NO SE PARTE POR FRASES, y el motivo es que partir por `.` es exactamente el
#: error que este modulo persigue: `Module.Basis.exists_basis` LLEVA PUNTOS, y
#: cortar ahi deja «exists_basis no existe en Mathlib» sin identificador que
#: comprobar. La primera version de esta funcion hacia eso y detectaba cero
#: afirmaciones falsas sobre el texto que la motivo.
#: Se deja corta a proposito: el patron que se persigue es «`X` no existe» o
#: «no existe `X`», que caben de sobra en 80 caracteres. Con 180 se marcaba
#: como falsa una frase donde el nombre aparecia como PROPUESTA —«algo como
#: `Basis.exists_basis` en el namespace adecuado»— y la negacion estaba en la
#: frase anterior, hablando de otro nombre.
VENTANA = 80


def _sin_acentos_min(s: str) -> str:
    import unicodedata
    return "".join(c for c in unicodedata.normalize("NFD", s.lower())
                   if unicodedata.category(c) != "Mn")


def revisar_afirmaciones(texto: str) -> list:
    """Las afirmaciones FALSAS de no-existencia que hay en un texto.

    Devuelve una lista de `{"nombre", "completo", "frase"}`: identificadores
    que el texto declara inexistentes y que SI estan en Mathlib.

    Solo se informa de lo demostrablemente falso. Si el texto dice que
    `Basis.exists_basis` no existe y de verdad no existe, aqui no sale: eso es
    correcto y corregirlo seria peor.
    """
    _cargar()
    if not texto or not _NOMBRES:
        return []
    marcas = [_sin_acentos_min(x) for x in _NIEGA]
    fuera, vistos = [], set()
    for mi in _IDENT.finditer(texto):
        nombre = mi.group(1) or mi.group(2)
        if not nombre or nombre in vistos:
            continue
        vistos.add(nombre)
        a = max(0, mi.start() - VENTANA)
        b = min(len(texto), mi.end() + VENTANA)
        ventana = _sin_acentos_min(texto[a:b])
        if not any(m in ventana for m in marcas):
            continue
        # SOLO LA COINCIDENCIA EXACTA REFUTA.
        #
        # `existe` acepta tambien el sufijo, porque con `open Module` delante
        # `Basis.exists_basis` resuelve. Pero para DESMENTIR a alguien que
        # dice que un nombre no existe, el sufijo no basta: `#check
        # Basis.exists_basis` a pelo devuelve «Unknown identifier», asi que
        # ahi quien lo negaba tenia razon. Corregir eso seria cambiar un error
        # por otro.
        if nombre.strip().strip("`").lstrip("@") in _NOMBRES:
            fuera.append({"nombre": nombre,
                          "completo": nombre_completo(nombre),
                          "frase": texto[a:b].strip()})
    return fuera


def aviso_de_correccion(fallos: Iterable) -> str:
    """El aviso que se antepone a la respuesta cuando la nota se equivoca."""
    fallos = list(fallos)
    if not fallos:
        return ""
    if len(fallos) == 1:
        f = fallos[0]
        completo = f["completo"] or f["nombre"]
        return (
            "⚠ **Corrección automática.** La explicación de abajo dice que "
            "`%s` no existe en Mathlib, y sí existe (`%s`). El fallo de Lean "
            "no es de nombre: mira el error literal del verificador, que es lo "
            "único con respaldo formal." % (f["nombre"], completo))
    nombres = ", ".join("`%s`" % f["nombre"] for f in fallos)
    return (
        "⚠ **Corrección automática.** La explicación de abajo dice que estos "
        "nombres no existen en Mathlib, y sí existen: %s. El fallo de Lean no "
        "es de nombre: mira el error literal del verificador." % nombres)
