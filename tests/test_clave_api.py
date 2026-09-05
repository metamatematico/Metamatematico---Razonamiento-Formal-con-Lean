# -*- coding: utf-8 -*-
"""Guardianes de la resolución de la clave de API.

DE DONDE SALE ESTE FICHERO. El sistema respondía en modo demo teniendo una
clave válida de 108 caracteres en `.env`. Dos fallos encadenados, y ninguno de
los dos daba error:

  1. NADIE LEÍA EL `.env`. No había una sola llamada a `load_dotenv` en todo el
     repositorio: el fichero existía y nadie lo abría.

  2. UN SECRETO VACÍO BORRABA LA CLAVE BUENA. `secrets.toml` traía
     `ANTHROPIC_API_KEY = ""` —así queda el fichero de ejemplo si no se
     rellena— y Streamlit no se limita a LEER ese fichero: INYECTA cada
     secreto en `os.environ`. Medido: 108 caracteres antes de tocar
     `st.secrets`, 0 después.

     Encima, la resolución era `try: st.secrets[...] except: os.environ[...]`,
     y el `except` sólo salta si hay EXCEPCIÓN. La cadena vacía no lanza nada,
     así que la rama de las variables de entorno no se ejecutaba nunca.

El síntoma —modo demo con la clave puesta— no apunta a ninguna de las dos
causas, y por eso estos tests miran el MECANISMO y no el resultado.
"""
from __future__ import annotations

import pathlib
import re

RAIZ = pathlib.Path(__file__).resolve().parent.parent
APP = RAIZ / "app.py"


def _fuente() -> str:
    return APP.read_text(encoding="utf-8")


def test_el_env_se_carga():
    """Sin esto, una clave en `.env` no llega a ninguna parte."""
    src = _fuente()
    assert "load_dotenv" in src, "app.py no carga el .env"
    # y tiene que ir ANTES de importar el nucleo: NucleoConfig lee os.environ
    # al construirse, asi que cargarlo despues no serviria de nada.
    i_dotenv = src.index("load_dotenv")
    for marca in ("from nucleo", "import nucleo"):
        j = src.find(marca)
        if j != -1:
            assert i_dotenv < j, (
                "el .env se carga DESPUES de importar el nucleo (%s)" % marca)


def test_hay_una_foto_de_las_claves_antes_de_streamlit():
    """Streamlit inyecta `secrets.toml` en `os.environ`. Si el fichero trae un
    valor vacío, machaca la clave buena. La copia tomada antes es lo único que
    sobrevive a eso."""
    src = _fuente()
    assert "_CLAVES_DEL_ENV" in src
    i_snap = src.index("_CLAVES_DEL_ENV = {")
    i_st = src.index("import streamlit as st")
    # la foto va despues del import de streamlit en el fichero, pero lo que
    # importa es que se tome antes de LEER st.secrets
    i_secrets = src.index("st.secrets[")
    assert i_snap < i_secrets, (
        "la foto de las claves se toma despues de leer st.secrets: para "
        "entonces el valor vacio ya la ha borrado")
    assert i_st >= 0


def test_la_cadena_de_fuentes_salta_los_vacios():
    """Un secreto vacío NO es un secreto.

    La versión anterior sólo caía a la siguiente fuente si la anterior lanzaba
    una excepción. Ahora tiene que recorrerlas y quedarse con la primera que
    TENGA ALGO.
    """
    src = _fuente()
    bloque = src[src.index("_secret_map = {"):src.index("api_key = st.text_input")]
    assert "for _fuente in (" in bloque, "no hay cadena de fuentes"
    assert "if _cand:" in bloque, "no se comprueba que la fuente traiga algo"
    assert "_CLAVES_DEL_ENV.get(_sname" in bloque, (
        "la foto del entorno no esta en la cadena: si secrets.toml trae un "
        "vacio, no queda de donde sacar la clave")
    # las tres fuentes, en orden
    for fuente in ("st.secrets[_sname]", "os.environ.get(_sname",
                   "_CLAVES_DEL_ENV.get(_sname"):
        assert fuente in bloque, "falta la fuente %s" % fuente


def test_secrets_de_ejemplo_no_deja_claves_vacias():
    """Si `.streamlit/secrets.toml` existe, ninguna clave puede estar puesta en
    vacío: eso borra la del `.env` al inyectarse en `os.environ`.

    El fichero está en .gitignore, así que en un clon limpio no existe y el
    test no aplica. Donde sí existe —la máquina de quien desarrolla— es justo
    donde el fallo ocurre.
    """
    p = RAIZ / ".streamlit" / "secrets.toml"
    if not p.exists():
        return
    vacias = []
    for linea in p.read_text(encoding="utf-8").splitlines():
        s = linea.strip()
        if not s or s.startswith("#"):
            continue
        m = re.match(r'^([A-Z_]+)\s*=\s*(""|\'\')\s*$', s)
        if m:
            vacias.append(m.group(1))
    assert not vacias, (
        "claves puestas en vacio en secrets.toml: %s. Un `X = \"\"` borra la "
        "variable de entorno al inyectarse; comenta la linea en vez de "
        "dejarla vacia." % ", ".join(vacias))


def test_la_clave_vuelve_a_os_environ_cuando_se_resuelve():
    """El Núcleo construye su config leyendo `os.environ`, no el widget. Si la
    clave se resuelve en la barra lateral y no se escribe de vuelta, el
    pipeline sigue en demo."""
    src = _fuente()
    assert "os.environ[_env_name] = api_key" in src
