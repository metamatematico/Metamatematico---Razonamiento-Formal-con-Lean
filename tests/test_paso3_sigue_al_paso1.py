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
        # SE COMPRUEBA LA INVARIANTE, NO LA ORTOGRAFÍA.
        #
        # Esto exigía la cadena literal
        # `self._lean.sugerir_imports(self._modulos_mathlib(context))`, y
        # saltó cuando esa línea se partió en dos para que el módulo del
        # nombre OFRECIDO fuese siempre —ver `test_nombre_con_import.py`—.
        # La invariante no se había roto: las dos llamadas siguen recibiendo
        # `context`. Un guardián que se dispara con código correcto enseña a
        # ignorarlo, que es el fallo que este fichero persigue en otros.
        import ast
        arbol = ast.parse(_fuente("nucleo/core.py"))

        proveedores = []
        for nodo in ast.walk(arbol):
            if not isinstance(nodo, ast.Call):
                continue
            f = nodo.func
            if not (isinstance(f, ast.Attribute)
                    and f.attr in ("_modulos_mathlib",
                                   "_modulos_de_los_nombres")):
                continue
            proveedores.append((f.attr, [ast.dump(a) for a in nodo.args]))

        assert proveedores, (
            "nadie elige los módulos que importa Lean: el paso 3 desapareció")
        for nombre, args in proveedores:
            assert any("id='context'" in a for a in args), (
                "`%s` ya no recibe el `context` del paso 1: si abre su propia "
                "consulta al grafo, los dos veredictos pasan a ser "
                "independientes y hay que decirlo en el diagrama, el README y "
                "el reporte" % nombre)

    def test_modulos_mathlib_solo_mira_las_primeras(self):
        """El corte que hace que medidor y runtime coincidan.

        LA VENTANA SE DELIMITA POR EL CUERPO DE LA FUNCIÓN, no por un número
        de caracteres. La primera versión miraba los 2 000 siguientes al
        `def`, y al crecer la docstring —al anotar la remedición del paso 3—
        la línea del corte quedó fuera de la ventana: el guardián falló
        diciendo «cambió la forma de recortar» cuando no había cambiado nada.
        Un guardián que se dispara por su propia ventana enseña a ignorarlo.
        """
        s = _fuente("nucleo/core.py")
        i = s.index("def _modulos_mathlib")
        # hasta el siguiente método del mismo nivel de indentación
        sig = re.search(r"\n    def ", s[i:])
        cuerpo = s[i:i + sig.start()] if sig else s[i:]
        m = re.search(r"for s in skills\[:(\d+)\]", cuerpo)
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

    Con exactitud equilibrada —la única que sobrevive a un banco 89 % álgebra—
    `classify_query` acierta el 62,1 % y la primera skill del grafo el 38,9 %,
    sobre un azar del 33,3 %. Conectar el índice de premisas al grafo sería
    cambiar el clasificador bueno por el malo.
    """

    def test_premisas_no_conoce_el_grafo(self):
        s = _fuente("nucleo/lean/premisas.py")
        for marca in ("SkillCategory", "self._graph", "skill_ids"):
            assert marca not in s, (
                "premisas.py ha empezado a mirar el grafo (%s). Si es a "
                "propósito, mide antes: en exactitud equilibrada hoy "
                "classify_query gana 62,1 %% contra 38,9 %%." % marca)


class TestElDecisorGobiernaLoQueDice:
    """El respaldo del decisor decia «se ejecuta todo» y traia un solo nombre.

    Cualquier capacidad cableada despues quedaba apagada JUSTO cuando el
    decisor fallaba. Un respaldo que apaga cosas en silencio es peor que no
    tenerlo: el sistema degrada y nadie se entera.
    """

    def test_el_respaldo_cubre_todas_las_gobernadas(self):
        import re
        from nucleo.core import _TODAS_LAS_GOBERNADAS
        s = _fuente("nucleo/core.py")
        # los `"nombre" in _corre` que hay de verdad en el codigo
        usados = set(re.findall(r'"([a-z_]+)" in _corre', s))
        assert usados, "ya no hay ninguna capacidad gobernada por el decisor"
        faltan = usados - set(_TODAS_LAS_GOBERNADAS)
        assert not faltan, (
            "estas capacidades miran a _corre y NO estan en "
            "_TODAS_LAS_GOBERNADAS, asi que el respaldo las apagaria: %s"
            % sorted(faltan))
        sobran = set(_TODAS_LAS_GOBERNADAS) - usados
        assert not sobran, (
            "_TODAS_LAS_GOBERNADAS nombra capacidades que ya nadie consulta: "
            "%s" % sorted(sobran))

    def test_las_gobernadas_existen_en_el_catalogo(self):
        from nucleo.core import _TODAS_LAS_GOBERNADAS
        from nucleo.decisor import CAPACIDADES
        catalogo = {c.nombre for c in CAPACIDADES}
        fuera = set(_TODAS_LAS_GOBERNADAS) - catalogo
        assert not fuera, (
            "el codigo consulta capacidades que el decisor no conoce, asi que "
            "nunca estarian activas: %s" % sorted(fuera))

    def test_el_decisor_apaga_los_imports_por_empate(self):
        """18 de 20 el grafo y 18 de 20 el conjunto fijo: un empate no gana.

        Y ademas cuesta un 11 % mas de tiempo por consulta. Si alguien vuelve
        a medirlo y gana, este test falla y hay que actualizarlo — que es
        justo lo que se quiere.
        """
        from nucleo.decisor import Contexto, decidir
        plan = decidir(Contexto(consulta="demuestra que 2+2=4",
                                es_matematica=True, area="algebra", rasgos={}))
        activas = {c.nombre for c in plan.activas}
        assert "eleccion_de_imports" not in activas, (
            "el decisor deja correr la eleccion de imports; su medicion decia "
            "empate contra el conjunto fijo. ¿Se volvio a medir?")
