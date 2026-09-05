# -*- coding: utf-8 -*-
"""Lo que va al elaborador va en inglés; lo que va al alumno, en castellano.

LA REGLA, y viene de una instrucción explícita: Mathlib está en inglés — los
217 419 nombres, los mensajes del elaborador, la documentación y todos los
ejemplos con los que el modelo aprendió a escribir Lean. Dictarle en castellano
lo obliga a cruzar un idioma en cada nombre que escribe.

Y había algo peor que el idioma: UN SOLO `LEAN_SYSTEM_PROMPT` servía para dos
trabajos opuestos —escribir Lean y explicarle el resultado al alumno—, así que
terminaba en «Responde en el mismo idioma que el usuario», que en el paso de
formalización es una instrucción contraproducente. Ahora son dos prompts, y
estos tests fijan cuál va en cada paso.

LO QUE ESTO NO DICE: que la calidad mejore. Eso haría falta medirlo contra un
banco gastando API y Lean, y no está medido. Lo que sí está es que la
instrucción se cumple.
"""
from __future__ import annotations

import pathlib
import re

from nucleo.llm.client import LLMClient

RAIZ = pathlib.Path(__file__).resolve().parent.parent
CORE = (RAIZ / "nucleo" / "core.py").read_text(encoding="utf-8")

#: Palabras funcionales que SÓLO son castellano. Se buscan como palabra
#: entera para no cazar `la` dentro de `lambda`.
#:
#: FUERA `no`, `si` y `como`: son palabras de los dos idiomas. La primera
#: versión las incluía y marcaba como castellano el prompt INGLÉS, que dice
#: «no prose, no explanation» — un detector de idioma que se equivoca de
#: idioma es justo el tipo de instrumento roto que este repositorio cataloga.
_CASTELLANO = re.compile(
    r"\b(el|la|los|las|que|para|con|una|unas|del|este|esta|debe|"
    r"escribe|usa|devuelve|codigo|idioma)\b|[áéíóúñ¿¡]", re.I)


def _es_castellano(texto: str) -> bool:
    return len(_CASTELLANO.findall(texto)) >= 3


class TestLosDosPromptsDeSistema:

    def test_el_que_escribe_lean_va_en_ingles(self):
        p = LLMClient.LEAN_SYSTEM_PROMPT
        assert not _es_castellano(p), "el prompt de formalizar está en castellano"
        assert "Lean 4" in p and "Mathlib" in p

    def test_y_dice_por_que(self):
        """Sin la frase, el próximo que lo lea lo «arregla» traduciéndolo."""
        assert "English" in LLMClient.LEAN_SYSTEM_PROMPT

    def test_el_que_habla_al_alumno_va_en_castellano(self):
        p = LLMClient.EXPLICACION_SYSTEM_PROMPT
        assert _es_castellano(p)
        assert "mismo idioma que el usuario" in p

    def test_no_son_el_mismo(self):
        assert LLMClient.LEAN_SYSTEM_PROMPT != LLMClient.EXPLICACION_SYSTEM_PROMPT


class TestQuePromptVaEnCadaPaso:

    def test_formalizar_revisar_y_reintentar_usan_el_de_lean(self):
        """Los tres pasos que PRODUCEN código Lean."""
        assert CORE.count("formalize_prompt, system=lean_system") == 1
        assert CORE.count("retry_prompt, system=lean_system") == 1
        assert CORE.count("revise_prompt, system=lean_system") == 1

    def test_traducir_y_explicar_usan_el_del_alumno(self):
        """Los dos pasos cuya salida LEE EL USUARIO. Usaban `lean_system`, que
        ahora dice «output Lean code only» — justo lo contrario."""
        assert "translate_prompt, system=LLMClient.EXPLICACION_SYSTEM_PROMPT" in CORE
        assert "explain_prompt, system=LLMClient.EXPLICACION_SYSTEM_PROMPT" in CORE

    def test_ningun_paso_de_lean_se_quedo_con_el_castellano(self):
        """El cuerpo de los prompts, no sólo el prompt de sistema."""
        for etiqueta, ini, fin in (
            ("formalizacion", "formalize_prompt = (", "lean_gen = await"),
            ("reintento", "retry_prompt = (", "lean_gen2 = await"),
            ("revision", "revise_prompt = (", "gen = await"),
        ):
            a = CORE.index(ini)
            b = CORE.index(fin, a)
            lineas = [l.strip() for l in CORE[a:b].splitlines()
                      if l.strip().startswith(('"', 'f"', '+ "'))]
            malas = [l for l in lineas if _es_castellano(l)]
            assert not malas, "%s sigue en castellano: %s" % (etiqueta, malas[:3])


class TestElMarcadorDeRefutacion:

    def test_se_aceptan_las_dos_grafias(self):
        """El prompt pide `REFUTATION`, pero hay código grabado con
        `REFUTACION`. Un detector que dejara de reconocerlo devolvería en
        silencio el fallo que este canal existe para evitar: Lean verifica la
        negación y la insignia dice «verificado»."""
        assert "REFUTATION" in CORE and "REFUTACI[OÓ]N" in CORE
        i = CORE.index('re.search(r"REFUTATION')
        patron = CORE[i:i + 120]
        assert "REFUTATION" in patron and "REFUTACI" in patron
