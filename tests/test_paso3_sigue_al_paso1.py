# -*- coding: utf-8 -*-
"""El paso 3 es aguas abajo del 1, y el medidor tiene que reproducirlo.

QUÉ SE DOCUMENTABA MAL
----------------------
El diagrama de flujo dibujaba los pasos 1 y 3 como dos actuaciones HERMANAS del
grafo. No lo son: el paso 3 no consulta el grafo por su cuenta, reusa el
`context` que produjo el paso 1 —`core.py` llama `_modulos_mathlib(context)` y
ese `context` sale de `_find_relevant_context`—.

Consecuencia: si el emparejamiento del paso 1 falla, el 3 hereda el fallo sin
forma de recuperarse. Y los dos veredictos publicados —«aporta» e «inerte»— no
son independientes entre sí.

POR QUÉ ESTE TEST Y NO OTRO
---------------------------
La prosa no se puede verificar mecánicamente, pero sí una cosa que la sostiene:
que el MEDIDOR del paso 3 alimente a `_modulos_mathlib` igual que el runtime.

  runtime   `_find_relevant_context` guarda `matched[:5]` en `relevant_skills`
  medidor   `imports_del_grafo_contra_lean.py` le pasa el top-10 entero
  y ambos   `_modulos_mathlib` sólo mira `skills[:4]`

Las cuatro primeras coinciden, así que hoy miden lo mismo. Este test lo fija:
si alguien sube el corte de `_modulos_mathlib` por encima de 5, o baja el de
`_find_relevant_context` por debajo de 4, el medidor y el runtime dejarían de
coincidir EN SILENCIO — y la cifra publicada del paso 3 hablaría del medidor y
no del sistema. Es el defecto que este proyecto lleva entero cazando.
"""
import io
import pathlib
import re

#: Derivada del propio fichero, NUNCA absoluta: el proyecto ya se movió una vez
#: de sitio, y una ruta fija deja el test verde midiendo otro repositorio.
RAIZ = pathlib.Path(__file__).resolve().parent.parent


def _fuente(rel: str) -> str:
    return io.open(RAIZ / rel, encoding="utf-8").read()


class TestElAcoplamiento:

    def test_el_paso3_consume_el_context_del_paso1(self):
        """No debe abrir su propia consulta al grafo.

        Si algún día lo hace, los dos veredictos pasan a ser independientes y
        hay que decirlo en el diagrama, en el README y en el reporte — hoy los
        tres dicen que el 3 reusa el 1.
        """
        s = _fuente("nucleo/core.py")
        assert "self._lean.sugerir_imports(self._modulos_mathlib(context))" in s, (
            "el paso 3 ya no consume el `context` del paso 1 — si es a "
            "propósito, actualiza el diagrama, el README y el reporte")

    def test_modulos_mathlib_solo_mira_las_primeras(self):
        """El corte que hace que medidor y runtime coincidan."""
        s = _fuente("nucleo/core.py")
        i = s.index("def _modulos_mathlib")
        m = re.search(r"for s in skills\[:(\d+)\]", s[i:i + 2000])
        assert m, "cambió la forma de recortar en _modulos_mathlib"
        assert int(m.group(1)) <= 5, (
            "_modulos_mathlib mira %s skills, pero el runtime sólo le pasa 5. "
            "El medidor le pasa 10: dejarían de medir lo mismo." % m.group(1))

    def test_el_runtime_pasa_al_menos_esas(self):
        s = _fuente("nucleo/core.py")
        m = re.search(r'"relevant_skills":\s*matched\[:(\d+)\]', s)
        assert m, "cambió cómo _find_relevant_context guarda relevant_skills"
        assert int(m.group(1)) >= 4, (
            "el runtime pasa sólo %s skills y _modulos_mathlib mira 4: el "
            "medidor, que pasa 10, mediría más de lo que el sistema usa"
            % m.group(1))


class TestLasDosCapasNoSeHablan:
    """Y es una decisión medida, no una deuda.

    `classify_query` acierta el área en el 61,2 % de 3 000 consultas; la
    primera skill del grafo, en el 47,3 %. Conectar el índice de premisas al
    grafo sería cambiar el clasificador bueno por el malo.
    """

    def test_premisas_no_conoce_el_grafo(self):
        s = _fuente("nucleo/lean/premisas.py")
        for marca in ("SkillCategory", "self._graph", "skill_ids"):
            assert marca not in s, (
                "premisas.py ha empezado a mirar el grafo (%s). Si es a "
                "propósito, mide antes: hoy classify_query gana 61,2 %% "
                "contra 47,3 %%." % marca)
