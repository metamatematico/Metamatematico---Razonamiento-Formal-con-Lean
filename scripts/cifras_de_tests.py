# -*- coding: utf-8 -*-
"""Pone en todos los sitios publicados cuántos tests y suites hay DE VERDAD.

Seis sitios anuncian la cifra —el badge y dos frases del README, la métrica de
la página de visualizaciones, el pie del índice, la portada y la §17 del
artefacto— y `tests/test_ui_coherencia.py` falla si alguno no cuadra con lo
que pytest recolecta. Hasta ahora se cambiaban a mano, seis veces por cada
test nuevo: así se quedaron «1253» en la versión publicada mientras el
repositorio decía «1255». Esto los reescribe desde la recolección.

    python -m scripts.cifras_de_tests
"""
import glob
import io
import os
import re
import subprocess
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FINO = " "


def contar():
    out = subprocess.run([sys.executable, "-m", "pytest", "-o", "addopts=",
                          "--collect-only", "-q"], cwd=RAIZ,
                         capture_output=True, text=True).stdout
    n = int(re.search(r"(\d+) tests? collected", out).group(1))
    return n, len(glob.glob(os.path.join(RAIZ, "tests", "test_*.py")))


def miles(n):
    return str(n) if n < 1000 else "%d%s%03d" % (n // 1000, FINO, n % 1000)


def main():
    n, s = contar()
    #: (fichero, patrón, sustitución); cada patrón tiene que casar UNA vez
    reglas = [
        ("README.md", r"Tests-\d+_passing", "Tests-%d_passing" % n),
        ("README.md", r"\*\*\d+ tests en \d+ suites\.\*\*", "**%d tests en %d suites.**" % (n, s)),
        ("README.md", r"(tests/\s+)\d+ tests en \d+ suites", r"\g<1>%d tests en %d suites" % (n, s)),
        ("pages/1_Visualizaciones.py", r'col3\.metric\("Tests", "\d+", "\d+ suites"\)',
         'col3.metric("Tests", "%d", "%d suites")' % (n, s)),
        ("docs/arquitectura_nle.html", r"\d+ tests · \d+ suites", "%d tests · %d suites" % (n, s)),
        ("docs/arquitectura_nle.html", r'<div class="n">\d+</div><div class="l">tests en verde',
         '<div class="n">%d</div><div class="l">tests en verde' % n),
        ("docs/arquitectura_nle.html", r"<strong>[\d%s]+ tests en \d+ suites</strong>" % FINO,
         "<strong>%s tests en %d suites</strong>" % (miles(n), s)),
    ]
    por_fichero = {}
    for f, pat, sub in reglas:
        por_fichero.setdefault(f, []).append((pat, sub))
    for f, rs in por_fichero.items():
        ruta = os.path.join(RAIZ, f)
        t = io.open(ruta, encoding="utf-8").read()
        for pat, sub in rs:
            t, k = re.subn(pat, sub, t)
            if k != 1:
                print("NO CASA una vez (%d) en %s: %s" % (k, f, pat))
                return 1
        io.open(ruta, "w", encoding="utf-8", newline="").write(t)
    print("%d tests en %d suites, puestos en %d sitios" % (n, s, len(reglas)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
