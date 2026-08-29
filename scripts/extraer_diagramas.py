# -*- coding: utf-8 -*-
"""
Saca los diagramas del artefacto a SVG autonomos, para el README.

En el artefacto los SVG heredan color del documento: usan `currentColor` y las
clases `.e-line`, `.v-fill`, `.dim`… que define la hoja de estilos de la pagina.
Sueltos no valen — GitHub los renderiza dentro de un `<img>` aislado, sin esa
hoja, y saldrian negros sobre negro en tema oscuro.

Asi que cada uno se envuelve con su propio bloque `<style>`:

  · `svg { color: … }` hace que `currentColor` resuelva, que es lo que usan los
    trazos y las puntas de flecha;
  · las clases de color se redeclaran con valores fijos;
  · `prefers-color-scheme` da la variante oscura, que GitHub respeta porque el
    `<img>` hereda la preferencia del sistema.

    python -m scripts.extraer_diagramas
"""
import io
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8")

FUENTE = "E:/Metamatematico/docs/arquitectura_nle.html"
DESTINO = "E:/Metamatematico/docs/img"

#: Un nombre por figura, en el orden en que aparecen en el documento.
NOMBRES = [
    "01-flujo-consulta",
    "02-ciclo-secuencia",
    "03-co-reguladores",
    "04-multi-agente",
    "05-estado-compartido",
    "06-lean-fuente-verdad",
    "07-complexificacion",
    "08-capas-delgadez",
    "09-apice-derived-category",
]

ESTILO = """<style>
  svg { color: #1f2328; font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; }
  text { fill: currentColor; }
  .lbl  { font-family: ui-sans-serif, -apple-system, "Segoe UI", Helvetica, sans-serif; font-weight: 500; }
  .dim  { opacity: .62; }
  .e-line { stroke: #5b4cc4; } .e-fill { fill: #5b4cc4; }
  .v-line { stroke: #0f766e; } .v-fill { fill: #0f766e; }
  .l-line { stroke: #a16207; } .l-fill { fill: #a16207; }
  .g-line { stroke: #b91c1c; } .g-fill { fill: #b91c1c; }
  @media (prefers-color-scheme: dark) {
    svg { color: #c9d1d9; }
    .e-line { stroke: #a78bfa; } .e-fill { fill: #a78bfa; }
    .v-line { stroke: #2dd4bf; } .v-fill { fill: #2dd4bf; }
    .l-line { stroke: #fbbf24; } .l-fill { fill: #fbbf24; }
    .g-line { stroke: #f87171; } .g-fill { fill: #f87171; }
  }
</style>
"""


def main():
    os.makedirs(DESTINO, exist_ok=True)
    html = io.open(FUENTE, encoding="utf-8").read()

    svgs = re.findall(r"<svg\b.*?</svg>", html, re.S)
    if len(svgs) != len(NOMBRES):
        print("x hay %d svg y %d nombres: revisa NOMBRES"
              % (len(svgs), len(NOMBRES)))
        sys.exit(1)

    for nombre, svg in zip(NOMBRES, svgs):
        # El id del marcador debe ser unico DENTRO del archivo, y lo es; pero
        # varios archivos comparten `id="f1a"` y GitHub los sirve aislados, asi
        # que no colisionan. Se deja como esta.
        cuerpo = svg.replace(">", ">\n" + ESTILO, 1)
        cuerpo = ('<?xml version="1.0" encoding="UTF-8"?>\n'
                  + cuerpo.replace("<svg ", '<svg xmlns="http://www.w3.org/2000/svg" ', 1))
        ruta = os.path.join(DESTINO, nombre + ".svg")
        io.open(ruta, "w", encoding="utf-8").write(cuerpo)
        vb = re.search(r'viewBox="([^"]+)"', svg)
        print("  %-30s %6.1f KB   viewBox %s"
              % (nombre + ".svg", len(cuerpo) / 1024, vb.group(1) if vb else "?"))

    print("\n%d diagramas -> %s" % (len(svgs), DESTINO))


if __name__ == "__main__":
    main()
