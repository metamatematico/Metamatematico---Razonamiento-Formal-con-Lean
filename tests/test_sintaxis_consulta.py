# -*- coding: utf-8 -*-
r"""Guardianes de la capa de sintaxis DE LA CONSULTA (`nucleo/sintaxis/`).

No confundir con `test_sintaxis.py`, que guarda los rasgos estructurales sobre
enunciados de LEAN —los que existen después de formalizar—. Éstos son sobre lo
que el alumno escribe, que es lo que hay antes de llamar a nadie.

Los que importan son los DOS ÚLTIMOS: uno fija el techo de falsos positivos
sobre enunciados reales y el otro el suelo de detección. Cualquier cambio que
apriete el parser para cazar un caso más tiene que pasar por ahí, que es
exactamente lo que hizo falta cuando la primera versión rechazaba el 22,3 % de
los enunciados correctos de LeanWorkbook.
"""
from __future__ import annotations

import io
import json
import pathlib
import random

import pytest

from nucleo.sintaxis.arbol import bien_formada, parsear
from nucleo.sintaxis.lexico import extraer, tokenizar
from nucleo.sintaxis.rasgos import rasgos_de_consulta

RAIZ = pathlib.Path(__file__).resolve().parent.parent
BANCO = RAIZ / "data" / "banco_lemas.jsonl"


# ═══════════════════════════════════════════════════════════════════════════
# ENCONTRAR LA NOTACIÓN
# ═══════════════════════════════════════════════════════════════════════════
@pytest.mark.parametrize("consulta, dentro", [
    ("(a+b)^2 = a^2 + 2ab + b^2", "(a+b)^2"),
    ("f(x) = x^2 + 1", "f(x)"),
    (r"\int_0^\infty e^{-x} dx", r"\int"),
    ("n^2 es par si y sólo si n es par", "n^2"),
    ("¿Es 17 un número primo?", "17"),
    ("∀x ∈ ℝ, x² ≥ 0", "∀x"),
])
def test_encuentra_lo_que_la_regex_perdia(consulta, dentro):
    """Los seis casos que `traductor.NOTACION` fallaba, uno por uno."""
    juntos = " ".join(t.texto for t in extraer(consulta))
    assert dentro in juntos, "no encontró «%s» en %r" % (dentro, juntos)


def test_la_prosa_no_es_notacion():
    """«Cauchy-Schwarz» tiene un guion, y un guion suelto no es una fórmula."""
    assert extraer("By Cauchy-Schwarz we get a non-negative bound") == []


def test_delimitador_explicito_manda():
    tramos = extraer(r"tenemos $a^2+b^2$ y también $c=1$")
    assert [t.texto for t in tramos] == ["a^2+b^2", "c=1"]
    assert all(t.explicito for t in tramos)


# ═══════════════════════════════════════════════════════════════════════════
# LATEX Y UNICODE SON LA MISMA CONSULTA
# ═══════════════════════════════════════════════════════════════════════════
@pytest.mark.parametrize("en_latex, en_unicode", [
    (r"Calcula \int_0^1 x^2 dx", "Calcula ∫_0^1 x^2 dx"),
    (r"Si x \in \mathbb{R} y x \geq 0", "Si x ∈ ℝ y x ≥ 0"),
    (r"Demuestra \forall x, x^2 \geq 0", "Demuestra ∀x, x² ≥ 0"),
    (r"$a \cup b \subseteq c$", "$a ∪ b ⊆ c$"),
])
def test_las_dos_escrituras_dan_los_mismos_rasgos(en_latex, en_unicode):
    """Media clase escribe `\\int` y la otra media `∫`. Si dieran rasgos
    distintos, el sistema aprendería dos veces la misma cosa."""
    def utiles(q):
        r = rasgos_de_consulta(q)
        return {k: v for k, v in r.items()
                if k.startswith(("rel=", "conec=", "tipo_", "op_"))}
    assert utiles(en_latex) == utiles(en_unicode)


# ═══════════════════════════════════════════════════════════════════════════
# BIEN Y MAL FORMADAS
# ═══════════════════════════════════════════════════════════════════════════
@pytest.mark.parametrize("consulta", [
    "(a+b)^2 = a^2 + 2ab + b^2",           # yuxtaposición: 2ab
    "f(x) = x^2 + 1",
    "∀x ∈ ℝ, x² ≥ 0",                       # coma de primer nivel
    "∑_{i=1}^n i = n(n+1)/2",              # límites del operador grande
    r"Calcula \int_0^1 x^2 dx",
    r"Let a,b,c \in \mathbb{R^+} such that a+b+c=3",    # el exponente-marca
    r"El dominio es $[0,\infty)$",          # intervalo medio abierto
    r"$x+y+z=9\;,$ halla el máximo",        # espaciado y coma de la frase
    r"$\frac{a^2}{b}$ $\geq$ $2a-b$",       # la fórmula partida en tres
    "Demuestra que en un grupo el neutro es único",      # sin notación
    "n^2 es par si y sólo si n es par",
])
def test_notacion_correcta_se_acepta(consulta):
    d = bien_formada(consulta)
    assert d.ok, "rechazó %r por %s %s" % (consulta, d.fallos, d.detalle)


@pytest.mark.parametrize("consulta, codigo", [
    ("(a+b^2 = c", "delimitador_sin_cerrar"),
    ("$(a+b))$", "sobra_texto"),
    ("x + = 3", "token_inesperado"),
    ("$a^2 + $", "operador_sin_operando"),
])
def test_notacion_rota_se_caza(consulta, codigo):
    d = bien_formada(consulta)
    assert not d.ok
    assert d.fallos[0] == codigo, "%r dio %s" % (consulta, d.fallos)
    assert d.detalle and d.detalle[0], "un fallo sin detalle no ayuda a nadie"


def test_el_operador_del_borde_es_de_la_prosa():
    """`2 + + ` suelto en una frase SE ACEPTA, y es a proposito.

    Bajar los falsos positivos del 22,3 % al 3,6 % exigio recortar los
    operadores del borde de una racha: son el guion de «Cauchy-Schwarz» y el
    parentesis de «(AM-GM)», no parte de la formula. El precio es que un
    operador colgando al final de una racha SIN delimitar deja de cazarse.

    Dentro de `$...$` si se caza —ahi el alumno dijo donde empieza y donde
    acaba la formula—, que es el caso del test de arriba. Se escribe para que
    nadie lo lea como un descuido.
    """
    assert bien_formada("2 + + ").ok
    assert not bien_formada("$2 + + $").ok


def test_sin_notacion_es_bien_formada():
    """Media biblioteca de enunciados no tiene ni una fórmula. Decir que están
    mal escritos sería peor que no mirar."""
    d = bien_formada("Demuestra que todo grupo de orden primo es cíclico")
    assert d.ok and d.arbol is None


# ═══════════════════════════════════════════════════════════════════════════
# EL ÁRBOL
# ═══════════════════════════════════════════════════════════════════════════
def test_la_relacion_principal_es_la_que_manda():
    """En `(a+b)^2 = a^2` un buscador de texto ve `^` antes que `=`. El árbol
    dice que la raíz es `=` y que las potencias cuelgan de ella."""
    r = rasgos_de_consulta("(a+b)^2 = a^2 + 2ab + b^2")
    assert r["rel=="] == 1
    assert r["op_^"] == 1


def test_la_potencia_asocia_a_la_derecha():
    a = parsear("a^b^c").arbol
    assert a.valor == "^" and a.hijos[1].valor == "^"


def test_superindice_unicode_es_potencia():
    assert rasgos_de_consulta("x² ≥ 0")["op_^"] == 1


def test_cuantificador_al_final_de_la_frase():
    r = rasgos_de_consulta(r"$|z| \geq 0 \ \forall z \in \mathbb{C}$")
    assert r["conec=∀"] == 1
    assert r["tipo_C"] == 1


# ═══════════════════════════════════════════════════════════════════════════
# LAS DOS CIFRAS QUE NO PUEDEN EMPEORAR
# ═══════════════════════════════════════════════════════════════════════════
def _muestra_del_banco(n=1200):
    if not BANCO.exists():                                # pragma: no cover
        pytest.skip("falta data/banco_lemas.jsonl")
    fuera = []
    with io.open(BANCO, encoding="utf-8") as fh:
        for linea in fh:
            if len(fuera) >= n:
                break
            nl = (json.loads(linea).get("nl") or "").strip()
            if nl:
                fuera.append(nl)
    return fuera


def test_techo_de_falsos_positivos():
    """Sobre enunciados de LeanWorkbook —todos correctos: los formalizó
    alguien y Lean los aceptó— el revisor no puede rechazar más del 6 %.

    Medido en su día: 3,6 % sobre los 23 243. El margen hasta el 6 % es para
    que el test no sea frágil, no para gastarlo.
    """
    textos = _muestra_del_banco()
    malos = [t for t in textos if not bien_formada(t).ok]
    tasa = len(malos) / len(textos)
    assert tasa <= 0.06, ("%.1f %% de falsos positivos; ejemplo: %r"
                          % (100 * tasa, malos[0] if malos else ""))


def test_suelo_de_deteccion_en_delimitadores():
    """Y con la misma muestra rota a propósito, tiene que cazar.

    Se prueba con delimitadores porque es la rotura que de verdad importa: un
    paréntesis sin cerrar hace que el modelo formalice una fórmula que no es
    la que el alumno escribió, y eso Lean lo verifica tan campante.
    """
    rng = random.Random(20260904)
    rotos, cazados = 0, 0
    for t in _muestra_del_banco():
        pos = [i for i, c in enumerate(t) if c in "([{"]
        if not pos:
            continue
        i = rng.choice(pos)
        rotos += 1
        cazados += not bien_formada(t[:i] + t[i + 1:]).ok
    assert rotos > 100, "la muestra no tiene delimitadores que romper"
    assert cazados / rotos >= 0.95, "sólo cazó %.1f %%" % (100 * cazados / rotos)


def test_no_se_atraganta_con_nada():
    """Ninguna consulta puede hacer estallar la capa: es lo primero que toca
    la entrada del usuario, y ahí entra cualquier cosa."""
    for t in ["", "   ", "$", "$$", "\\", "((((((((((", "))))", "^^^", "∀",
              r"\frac", "x" * 5000, "$" + "(" * 200 + "$", "😀 = 1"]:
        tokenizar(t)
        d = bien_formada(t)
        assert isinstance(d.ok, bool)


# ═══════════════════════════════════════════════════════════════════════════
# LO QUE EL RESTO DEL SISTEMA PIDE
# ═══════════════════════════════════════════════════════════════════════════
def test_solo_se_avisa_de_delimitadores():
    """De los seis motivos, sólo dos llegan al alumno.

    Los delimitadores fallan poco (0,6 % de falsos positivos) y cazan mucho
    (99 %). Los otros cuatro fallan cuatro veces más y cazan la mitad: avisar
    de ésos enseñaría a ignorar los avisos.
    """
    from nucleo.sintaxis import revisar

    con = revisar("Demuestra que (a+b^2 = c")
    assert not con.ok and con.codigo == "delimitador_sin_cerrar"
    assert con.aviso and "delimitadores" in con.aviso

    sin = revisar("x + = 3")
    assert not sin.ok and sin.codigo == "token_inesperado"
    assert sin.aviso == "", "sólo se avisa de delimitadores"


def test_la_revision_nunca_bloquea():
    """Devuelve un aviso, no un veredicto que corte la consulta."""
    from nucleo.sintaxis import Revision, revisar

    r = revisar("(((")
    assert isinstance(r, Revision)
    assert isinstance(r.rasgos, dict) and r.rasgos, "los rasgos salen siempre"


def test_el_resumen_lleva_la_relacion_principal():
    from nucleo.sintaxis import revisar

    d = revisar("Prueba que ∀x ∈ ℝ, x² ≥ 0").resumen()
    assert d["bien_formada"] is True
    assert d["relacion"] == "≥" and d["conectiva"] == "∀"


def test_core_pone_el_aviso_delante_y_guarda_el_resumen():
    """El aviso va ANTES de la respuesta, incluso de un «verificado».

    Se comprueba sobre la fuente y no ejecutando el pipeline porque éste
    necesita clave de API y Lean; lo que se guarda aquí es que el cableado no
    desaparezca en una reescritura.
    """
    fuente = (RAIZ / "nucleo" / "core.py").read_text(encoding="utf-8")
    assert "from nucleo.sintaxis import revisar" in fuente
    linea = next((l for l in fuente.splitlines()
                  if "_revision.aviso}" in l and "{content}" in l), "")
    assert linea, "no se ensambla el aviso con el contenido"
    assert linea.index("_revision.aviso}") < linea.index("{content}"), (
        "el aviso tiene que ir DELANTE del contenido, no detrás")
    assert '"sintaxis": (_revision.resumen()' in fuente
