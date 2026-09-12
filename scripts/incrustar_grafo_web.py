# -*- coding: utf-8 -*-
"""Incrusta `data/grafo_web.json` dentro del explorador publicado.

El explorador es un solo fichero HTML sin dependencias externas: los datos van
DENTRO, en un `<script type="application/json">`. Ese es el motivo — un
artefacto publicado no puede hacer `fetch` de un fichero suelto, asi que si los
datos no viajan con el HTML el explorador sale vacio.

Para regenerarlo entero cuando el grafo cambie:

    python scripts/exportar_grafo_web.py     # lee el grafo, calcula posiciones
    python scripts/incrustar_grafo_web.py    # mete el JSON en el HTML

El HTML conserva su marca `MARCA` la primera vez y, a partir de ahi, se
sustituye el bloque de datos anterior. Asi el ciclo es repetible sin tener que
acordarse de restaurar nada.
"""
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(RAIZ, "docs", "explorador_grafo.html")
DATOS = os.path.join(RAIZ, "data", "grafo_web.json")
MARCA = '<script id="datos-grafo" type="application/json">'


def main():
    if not os.path.exists(DATOS):
        print("falta %s — ejecuta antes scripts/exportar_grafo_web.py" % DATOS)
        return 1
    crudo = io.open(DATOS, encoding="utf-8").read()
    d = json.loads(crudo)                      # que reviente aqui si no es JSON

    # `</script` dentro de una cadena JSON cerraria la etiqueta antes de tiempo.
    # No pasa hoy —son identificadores de Mathlib— pero comprobarlo cuesta nada
    # y el fallo seria mudo: el explorador saldria en blanco.
    if "</script" in crudo.lower():
        print("el JSON contiene '</script': habria que escaparlo")
        return 1

    html = io.open(HTML, encoding="utf-8").read()
    i = html.find(MARCA)
    if i < 0:
        print("no se encontro el bloque de datos en %s" % HTML)
        return 1
    j = html.find("</script>", i)
    nuevo = html[:i + len(MARCA)] + crudo + html[j:]

    # LAS CIFRAS DEL ENCABEZADO TAMBIEN, o se pudren en cada regeneracion.
    # Estaban escritas a mano y este script solo cambiaba el bloque de datos:
    # la pagina cargaba 352 nodos y seguia anunciando 321. Una pagina que dice
    # mal su propio tamano es el fallo mas barato de evitar.
    def mil(n):
        return "%d" % n if n < 1000 else "%d %03d" % (n // 1000, n % 1000)

    def cuenta(sort):
        return sum(1 for x in d["nodos"] if x.get("s") == sort)

    parches = [
        (r"(<span><b>)\d+(</b> identidades</span>)", str(d["identidades"])),
        (r"(<b>)[\d ]+ nodos, [\d ]+ morfismos(</b>)",
         "%s nodos, %s morfismos" % (mil(len(d["nodos"])),
                                     mil(len(d["aristas"])))),
        (r'(font-weight:600">)\d+\s*\n?\s*(CONCEPTO</span>)', str(cuenta("CONCEPTO"))),
        (r'(font-weight:600">)\d+ (MODULO</span>)', str(cuenta("MODULO"))),
        (r'(font-weight:600">)\d+ (TACTICA</span>)', str(cuenta("TACTICA"))),
    ]
    for patron, valor in parches:
        nuevo, k = re.subn(patron, lambda m, v=valor: m.group(1) + v + (
            " " if not m.group(2).startswith(("CONCEPTO", "</b>")) else
            ("\n        " if m.group(2).startswith("CONCEPTO") else "")
        ) + m.group(2), nuevo, count=1)
        if not k:
            print("  AVISO: no se pudo actualizar la cifra %r del encabezado"
                  % patron)

    io.open(HTML, "w", encoding="utf-8").write(nuevo)

    print("nodos %d · aristas %d · identidades %d · sectores %d"
          % (len(d["nodos"]), len(d["aristas"]), d["identidades"],
             len(d["sectores"])))
    print("-> %s  (%.0f KB)" % (HTML, len(nuevo.encode("utf-8")) / 1024))
    print()
    print("Publicar con la herramienta de artefactos sobre la MISMA url para")
    print("que el enlace que ya se compartio siga sirviendo.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
