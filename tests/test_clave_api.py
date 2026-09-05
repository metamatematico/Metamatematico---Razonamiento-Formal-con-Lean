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


def test_vaciar_el_campo_borra_la_clave_de_verdad():
    """Borrar el campo tiene que borrar la clave que USA el pipeline.

    Los tres sitios donde se guardaba llevaban `if api_key:`, asi que vaciar
    el campo no borraba nada: la copia persistente sobrevivia a la navegacion
    entre paginas y —lo grave— `os.environ` seguia con la clave vieja, que es
    de donde la lee el Nucleo. Se podia vaciar el campo, ver el hueco, y
    seguir gastando la clave anterior en cada consulta.
    """
    fuente = _fuente()
    bloque = fuente[fuente.index("_persist_key = f\"_apikey_persist_"):
                    fuente.index("st.session_state[\"_api_key\"]")]
    assert "else:" in bloque, "no hay rama para el campo vacio"
    assert "st.session_state.pop(_persist_key, None)" in bloque, (
        "vaciar el campo no borra la copia persistente")
    assert "os.environ.pop(_env_name, None)" in bloque, (
        "vaciar el campo no borra la variable de entorno, que es de donde el "
        "Nucleo lee la clave")


def test_se_dice_de_donde_salio_la_clave_que_se_ve():
    """Encontrarse el campo relleno sin saber por que es desconcertante: la
    clave puede venir del `.env`, de `secrets.toml` o de esta misma sesion."""
    fuente = _fuente()
    assert "cargada de `.env` al arrancar" in fuente
    assert "escrita en esta sesión" in fuente
    assert "volverá al reiniciar" in fuente, (
        "hay que avisar de que el .env la repone, o el usuario cree que la "
        "borro y vuelve sola")


def test_un_401_se_traduce_a_algo_accionable():
    """Sin esto, una clave mala sale como «El Núcleo encontró un error» y
    parece un fallo del sistema."""
    fuente = _fuente()
    assert "La clave de API no es válida" in fuente
    # las cuatro redacciones: `authentication_error` es la de Anthropic, y el
    # 401 lo unico comun a los cuatro proveedores
    for marca in ("authentication_error", "invalid x-api-key", '"401" in b'):
        assert marca in fuente, "falta reconocer %s" % marca


class TestLasDosLLMConfig:
    """Hay DOS clases `LLMConfig` con el mismo nombre y distinta forma.

        nucleo.config.LLMConfig      model, max_tokens, temperature,
                                     embedding_dim, api_key
        nucleo.llm.client.LLMConfig  ... + effort, PROVIDER

    El Nucleo se construye con la PRIMERA al arrancar, asi que los seis sitios
    que leen `self.config.provider` lanzaban `AttributeError` hasta que la
    interfaz llamaba a `reconfigure_llm` con la segunda.

    Y ese fallo se lo tragaba el `except` del indicador de la barra lateral,
    que se quedaba sin pintar NADA —ni «activo» ni «demo»—. Sin señal, la
    lectura natural es «la clave no ha conectado». Habia conectado: en el log
    habia llamadas con 200 OK y hasta una prueba cerrada.
    """

    def test_siguen_teniendo_formas_distintas(self):
        """Si algun dia se unifican, este test sobra — pero hay que enterarse,
        no descubrirlo por un AttributeError en produccion."""
        import dataclasses
        from nucleo.config import LLMConfig as A
        from nucleo.llm.client import LLMConfig as B
        ca = {f.name for f in dataclasses.fields(A)}
        cb = {f.name for f in dataclasses.fields(B)}
        assert "provider" in cb
        assert "provider" not in ca, (
            "ya tienen la misma forma: se puede quitar la normalizacion")

    def test_el_cliente_normaliza_la_config_que_le_falta_provider(self):
        from nucleo.config import LLMConfig as ConfigDelNucleo
        from nucleo.llm.client import LLMClient, LLMProvider
        c = LLMClient(ConfigDelNucleo(api_key="sk-ant-loquesea"))
        assert getattr(c.config, "provider", None) is not None
        assert c.config.provider == LLMProvider.ANTHROPIC

    def test_sin_clave_se_deduce_demo(self):
        import os
        from nucleo.config import LLMConfig as ConfigDelNucleo
        from nucleo.llm.client import LLMClient, LLMProvider
        previo = os.environ.pop("ANTHROPIC_API_KEY", None)
        try:
            c = LLMClient(ConfigDelNucleo(api_key=""))
            assert c.config.provider == LLMProvider.DEMO
        finally:
            if previo is not None:
                os.environ["ANTHROPIC_API_KEY"] = previo

    def test_get_client_ya_no_revienta(self):
        """Era el sintoma: `_get_client()` lanzaba y el indicador callaba."""
        from nucleo.config import LLMConfig as ConfigDelNucleo
        from nucleo.llm.client import LLMClient
        c = LLMClient(ConfigDelNucleo(api_key="sk-ant-loquesea"))
        assert type(c._get_client()).__name__ != ""


def test_el_indicador_no_se_calla_si_no_puede_leer_el_estado():
    """Un indicador que no pinta nada se lee como «no ha conectado». Si no
    puede saberlo, tiene que decir que no puede saberlo."""
    fuente = _fuente()
    bloque = fuente[fuente.index("Estado REAL del cliente LLM"):
                    fuente.index('model = st.selectbox("Modelo"')]
    assert "except Exception:\n                pass" not in bloque, (
        "el indicador vuelve a tragarse el fallo")
    assert "no se puede leer el estado del LLM" in bloque
