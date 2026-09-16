# -*- coding: utf-8 -*-
"""Que la subred del alumno se VEA sobre el fondo oscuro.

POR QUE ESTO ES UN TEST Y NO UNA NOTA DE ESTILO
-----------------------------------------------
La pagina de visualizaciones dibuja sobre `#0d1117`, casi negro. Un color
oscuro ahi no queda feo: DESAPARECE. Y lo que estaba desapareciendo era lo mas
importante del dibujo — las aristas de dependencia iban en `#4a5568`, que da
2,51:1 contra el fondo, y son las mas numerosas de las tres clases: la
estructura entera del subgrafo era lo que peor se veia.

No lo caza ningun test de los otros porque la figura se genera sin error y el
`.png` sale. Solo se nota mirandolo, y solo si uno sabe que tenia que haber
algo ahi.

Ademas las aristas de analogia usaban el MISMO verde que los nodos-tactica.
Dos cosas distintas con el mismo significado visual es peor que un color feo:
el alumno lee una relacion que no existe.

EL UMBRAL. 3,0:1 es el minimo de WCAG 2.1 para elementos graficos —criterio
1.4.11, «Non-text Contrast»—. Para texto pide 4,5:1; aqui se aplica el de
graficos porque son nodos y aristas, no parrafos.
"""
import ast
import io
import os

import pytest

_PAGINA = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "pages", "1_Visualizaciones.py")


def _paleta_declarada():
    """`BG` y `COLOR_SUBRED` leidos del fuente, sin importar la pagina.

    Importarla ejecutaria Streamlit entero —y el Nucleo detras—, que es caro y
    ademas convierte un test de color en un test de arranque. Se lee con `ast`,
    que da exactamente los literales declarados.
    """
    arbol = ast.parse(io.open(_PAGINA, encoding="utf-8").read())
    fuera = {}
    for nodo in arbol.body:
        if not isinstance(nodo, ast.Assign):
            continue
        for t in nodo.targets:
            if isinstance(t, ast.Name) and t.id in ("BG", "COLOR_SUBRED"):
                fuera[t.id] = ast.literal_eval(nodo.value)
    assert "BG" in fuera and "COLOR_SUBRED" in fuera, (
        "no se encontraron `BG` y `COLOR_SUBRED` en %s" % _PAGINA)
    return fuera["BG"], fuera["COLOR_SUBRED"]


BG, COLOR_SUBRED = _paleta_declarada()

#: Minimo de WCAG 2.1 para elementos graficos (criterio 1.4.11).
MINIMO = 3.0


def _luminancia(hexcol: str) -> float:
    h = hexcol.lstrip("#")
    canales = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    lineal = [(c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4)
              for c in canales]
    return 0.2126 * lineal[0] + 0.7152 * lineal[1] + 0.0722 * lineal[2]


def contraste(a: str, b: str) -> float:
    la, lb = _luminancia(a), _luminancia(b)
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


def test_el_calculo_de_contraste_es_el_de_wcag():
    """Que el instrumento sepa medir antes de creerle.

    Sin esto, un error en la formula dejaria pasar cualquier color y el test
    diria que todo esta bien — que es justo el fallo que este fichero existe
    para impedir, un nivel mas abajo.
    """
    assert contraste("#ffffff", "#000000") == pytest.approx(21.0, abs=0.01)
    assert contraste("#000000", "#000000") == pytest.approx(1.0, abs=0.01)
    assert contraste("#ffffff", "#ffffff") == pytest.approx(1.0, abs=0.01)


@pytest.mark.parametrize("papel", sorted(COLOR_SUBRED))
def test_cada_color_se_ve_sobre_el_fondo(papel):
    color = COLOR_SUBRED[papel]
    r = contraste(color, BG)
    assert r >= MINIMO, (
        "`%s` es %s y da %.2f:1 contra el fondo %s, por debajo del minimo de "
        "%.1f:1. Sobre un fondo casi negro un color oscuro no queda feo: no "
        "se dibuja." % (papel, color, r, BG, MINIMO))


def test_ningun_color_es_mas_oscuro_que_el_fondo():
    """Un color por debajo del fondo no es un color: es un agujero."""
    fondo = _luminancia(BG)
    oscuros = {k: v for k, v in COLOR_SUBRED.items()
               if _luminancia(v) <= fondo}
    assert not oscuros, "mas oscuros que el fondo: %s" % oscuros


def test_ninguna_arista_repite_el_color_de_un_nodo():
    """Dos cosas distintas con el mismo color dicen que son la misma.

    Las aristas de analogia iban en `#4ade80`, el verde de los nodos-tactica.
    Quien mira el dibujo concluye que una analogia «es» una tactica, y no es
    un fallo de estetica sino de lectura.
    """
    nodos = {k: v for k, v in COLOR_SUBRED.items() if k.startswith("nodo_")}
    aristas = {k: v for k, v in COLOR_SUBRED.items() if k.startswith("arista_")}
    choques = [(na, nn) for na, ca in aristas.items()
               for nn, cn in nodos.items() if ca == cn]
    assert not choques, "arista y nodo con el mismo color: %s" % choques


def test_los_papeles_de_la_paleta_estan_todos():
    """Si alguien añade una clase de nodo o arista, que declare su color aqui
    y no lo escriba suelto en la figura — que es como se colo `#4a5568`."""
    faltan = {"nodo_activado", "nodo_dependencia", "nodo_tactica",
              "arista_dependencia", "arista_traduccion", "arista_analogia",
              "texto"} - set(COLOR_SUBRED)
    assert not faltan, "papeles sin color declarado: %s" % faltan


def test_la_figura_no_escribe_colores_sueltos():
    """La paleta solo sirve si la figura la usa.

    Un `#rrggbb` a mano dentro del dibujo de nodos o aristas se escapa de
    todos los tests de arriba, porque estos miran la paleta y no el lienzo.
    """
    import re

    # CON `ast`, NO CON TEXTO. La primera version quitaba los comentarios con
    # `linea.split("#")[0]` — y un color hexadecimal EMPIEZA POR `#`, asi que
    # se borraba justo lo que venia a buscar. Encontraba cero colores siempre
    # y pasaba siempre: un guardian que no puede disparar.
    arbol = ast.parse(io.open(_PAGINA, encoding="utf-8").read())
    cuerpo = None
    for nodo in ast.walk(arbol):
        if (isinstance(nodo, ast.FunctionDef)
                and nodo.name == "fig_proof_trace"):
            cuerpo = nodo
    assert cuerpo is not None, "no se encontro `fig_proof_trace`"

    hexa = re.compile(r"^#[0-9a-fA-F]{6}$")
    declarados = set(COLOR_SUBRED.values()) | {BG, "#ffffff"}
    # el marco de la leyenda es decoracion, no contenido: va aparte
    declarados |= {"#161b22", "#30363d"}
    # las lineas divisorias de nivel son guias a alpha 0,12
    declarados |= {"#ef5350", "#42a5f5", "#f48fb1", "#80cbc4"}
    sueltos = sorted({
        n.value for n in ast.walk(cuerpo)
        if isinstance(n, ast.Constant) and isinstance(n.value, str)
        and hexa.match(n.value) and n.value not in declarados})
    assert not sueltos, (
        "colores escritos a mano en `fig_proof_trace`: %s. Declararlos en "
        "`COLOR_SUBRED` para que el contraste se compruebe." % sueltos)
