# -*- coding: utf-8 -*-
"""Qué capacidades se ejecutan para una consulta, y por qué.

EL PROBLEMA QUE RESUELVE
------------------------
El sistema tiene una docena de capacidades —inyectar nombres de Mathlib,
elegir premisas, ordenar la cascada, buscar ejemplos, revisar la sintaxis— y
hasta aquí la decisión de cuál corre estaba repartida en `if`s por mil líneas
de `core.py`. Eso tiene dos consecuencias malas: nadie puede decir de un
vistazo qué corre para una consulta dada, y —peor— una capacidad que se midió
PEOR QUE NO HACER NADA se sigue ejecutando porque su `if` sigue ahí.

LA REGLA, Y ES UNA SOLA
-----------------------
Una capacidad se ejecuta si y sólo si:

    1. su guarda dice que aplica a esta consulta, Y
    2. su EVIDENCIA gana a su MODELO NULO.

La condición 2 no se negocia y no depende de la consulta. Una capacidad que
mide peor que su nulo está APAGADA siempre, aunque su guarda diga que sí,
aunque alguien esté convencido de que ayuda. Y una capacidad SIN evidencia
sólo corre si es gratis: si cuesta una llamada al modelo o una compilación de
Lean, no se gasta en algo que nadie ha medido.

Esto hace al decisor honesto POR CONSTRUCCIÓN. No puede encender algo que
mide peor que no hacer nada, porque lee el veredicto de los ficheros de
medición en vez de llevarlo escrito a mano.

LO QUE ESTO YA APAGA, HOY
-------------------------
Al leer la evidencia que hay en `data/` salen cuatro capacidades que están en
producción y NO baten a su nulo. La más cara de las cuatro:

    orden de la cascada por área   posición media 1,262
    el nulo (simp primero)         posición media 1,091

O sea que la regla que hoy decide en qué orden probar las tácticas hace falta
MÁS invocaciones de Lean que probar `simp` y seguir por frecuencia. Eso lo
midió `scripts/modelo_en_la_cascada.py` justo porque la medición anterior
—`efecto_orden_cascada.py`— comparaba dos reglas entre sí y ninguna contra el
suelo. Comparar dos versiones de la misma idea no es una medición.

UNA GUARDA NO ES UN ADORNO: PARTE EL PROMEDIO
---------------------------------------------
La condición 1 hace más trabajo del que parece. Los rasgos del árbol de la
consulta suman +0,8 puntos sobre los n-gramas EN PROMEDIO — poco. Pero en el
5,9 % de consultas donde los n-gramas no aciertan ni un lema, la estructura
sola cubre el 12,9 % contra el 3,4 % del nulo. El promedio diluía eso entre el
94 % de casos donde el léxico ya funciona.

Por eso hay DOS capacidades de sintaxis y no una: la de siempre, justificada
por el promedio, y la que sólo entra cuando el léxico calla, justificada por
el estrato. Sintaxis y semántica no compiten por el mismo puesto.

EL MODELO NULO DEL PROPIO DECISOR
---------------------------------
Es «ejecutarlo todo», y está implementado en `decidir_todo()`. Sin él, decir
que el decisor ahorra no significaría nada. Lo que se compara es COSTE:
llamadas al modelo y compilaciones de Lean por consulta. La calidad no se
compara aquí —haría falta gastar API y Lean— y el argumento de que no baja es
el de la regla: lo que se apaga se apagó porque se midió que no batía a no
hacerlo.
"""
from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass, field
from typing import Callable, Optional

RAIZ = pathlib.Path(__file__).resolve().parent.parent
DATOS = RAIZ / "data"

#: Lo que cuesta ejecutar una capacidad. Es lo que decide qué pasa cuando no
#: hay evidencia: lo gratis se ejecuta, lo caro no.
LOCAL = "local"
LLAMADA = "llamada al modelo"
COMPILADO = "compilado de Lean"


@dataclass(frozen=True)
class Evidencia:
    """De dónde sale el veredicto de una capacidad.

    `ruta` es el camino de claves dentro del JSON hasta el número. Se guarda
    el CAMINO y no el número para que el veredicto se recalcule al volver a
    medir: un número copiado a mano envejece en silencio, que es exactamente
    lo que este módulo existe para impedir.
    """
    fichero: str
    metrica: str
    ruta_real: tuple
    ruta_nulo: tuple
    #: fichero del nulo, si vive en otra medición
    fichero_nulo: Optional[str] = None
    #: en «posición media de la táctica que cierra», menos es mejor
    mas_es_mejor: bool = True
    #: qué se comparó, en una línea, para el informe
    contra: str = "el modelo nulo"


@dataclass
class Veredicto:
    real: Optional[float] = None
    nulo: Optional[float] = None
    gana: Optional[bool] = None
    motivo: str = ""


@dataclass
class Capacidad:
    nombre: str
    que_hace: str
    coste: str
    evidencia: Optional[Evidencia] = None
    #: cuándo APLICA a una consulta. None = siempre.
    guarda: Optional[Callable[["Contexto"], bool]] = None
    #: dónde vive en el código, para poder ir a mirarlo
    donde: str = ""
    #: ¿es el PROPOSITO del sistema en vez de un extra?
    #:
    #: La regla «sin evidencia y cara -> apagada» es la correcta para un
    #: anadido, cuyo nulo es no hacerlo. Para el nucleo no: el nulo de
    #: «verificar con Lean» seria «responder sin verificar», que es otro
    #: sistema, no una version mas barata de este. Marcarlo aqui no lo exime
    #: de medicion —`banco_fidelidad.py` y `ablacion_nucleo.py` son sus
    #: medidas— sino que dice que esta decision no es del decisor.
    nucleo: bool = False
    #: por que no hay evidencia comparable, cuando la hay pero no encaja
    sin_evidencia_porque: str = ""


@dataclass
class Contexto:
    """Lo que se sabe de la consulta ANTES de gastar nada."""
    consulta: str = ""
    es_matematica: bool = True
    area: str = ""
    #: los rasgos de `nucleo.sintaxis.revisar`, si se calcularon
    rasgos: dict = field(default_factory=dict)
    #: ¿el emparejador léxico no encontró NADA para esta consulta?
    #:
    #: Es el corte que separa las dos capacidades de sintaxis: en el promedio
    #: los rasgos del árbol suman poco, pero en el estrato donde el léxico
    #: calla suman mucho. Una guarda que mira este campo es lo que permite
    #: encender la segunda sin encender la primera de más.
    lexico_mudo: bool = False
    hay_lean: bool = True
    hay_modelo: bool = True


@dataclass
class Decision:
    activas: list = field(default_factory=list)
    apagadas: list = field(default_factory=list)
    motivos: dict = field(default_factory=dict)
    veredictos: dict = field(default_factory=dict)

    @property
    def coste(self) -> dict:
        """Cuántas llamadas y compilados implica esta decisión."""
        c = {LLAMADA: 0, COMPILADO: 0, LOCAL: 0}
        for cap in self.activas:
            c[cap.coste] = c.get(cap.coste, 0) + 1
        return c


# ═══════════════════════════════════════════════════════════════════════════
# EL CATALOGO
# ═══════════════════════════════════════════════════════════════════════════
def _tiene_notacion(ctx: Contexto) -> bool:
    return not ctx.rasgos.get("sin_notacion", 1)


def _lexico_mudo_y_hay_notacion(ctx: Contexto) -> bool:
    return ctx.lexico_mudo and _tiene_notacion(ctx)


CAPACIDADES: list[Capacidad] = [
    Capacidad(
        nombre="revision_de_sintaxis",
        que_hace="mira si la notación de la consulta está bien escrita y avisa"
                 " de delimitadores descasados antes de formalizar",
        coste=LOCAL,
        donde="nucleo/sintaxis/revision.py",
        evidencia=Evidencia(
            fichero="sintaxis_falsos_positivos.json",
            metrica="caza de roturas (%)",
            ruta_real=("tasa_caza",), ruta_nulo=("nulo_moneda",),
            contra="una moneda que rechaza a la misma tasa"),
    ),
    Capacidad(
        nombre="rasgos_de_sintaxis_para_lemas",
        que_hace="añade los rasgos del árbol de la consulta a los n-gramas"
                 " para elegir qué lemas ofrecer",
        coste=LOCAL,
        donde="nucleo/sintaxis/rasgos.py",
        guarda=_tiene_notacion,
        evidencia=Evidencia(
            fichero="sintaxis_de_consulta_contra_lemas.json",
            metrica="cobertura de lemas (%)",
            ruta_real=("resultados", "las dos", 0),
            ruta_nulo=("resultados", "n-gramas", 0),
            contra="los n-gramas solos, que es lo que ya había"),
    ),
    Capacidad(
        nombre="rasgos_de_sintaxis_cuando_el_lexico_calla",
        que_hace="ofrece lemas a partir del arbol SOLO en las consultas donde"
                 " el emparejador lexico no encuentra nada",
        coste=LOCAL,
        donde="nucleo/sintaxis/rasgos.py",
        guarda=_lexico_mudo_y_hay_notacion,
        # POR QUE ESTA CAPACIDAD EXISTE APARTE DE LA DE ARRIBA. En el
        # PROMEDIO los rasgos del arbol suman +0,8 puntos sobre los n-gramas,
        # que es real pero poco. Ese promedio esconde el reparto: en el 5,9 %
        # de consultas donde los n-gramas no aciertan NI UN lema, la
        # estructura sola cubre el 12,9 % contra el 3,4 % del nulo, y las dos
        # juntas el 21,1 %. Sintaxis y semantica no compiten por el mismo
        # puesto: se reparten el trabajo, y el reparto solo se ve estratificando.
        evidencia=Evidencia(
            fichero="sintaxis_de_consulta_contra_lemas.json",
            metrica="cobertura donde el lexico no acierta nada (%)",
            ruta_real=("estrato_sin_lexico", "resultados", "ESTRUCTURA", 0),
            ruta_nulo=("estrato_sin_lexico", "resultados", "nulo", 0),
            contra="los lemas mas frecuentes, en ese mismo estrato"),
    ),
    Capacidad(
        nombre="reconocedor_de_area",
        que_hace="clasifica el área de la consulta para elegir el contexto",
        coste=LOCAL,
        donde="nucleo/multi_agent/specialized_agent.py::classify_query",
        evidencia=Evidencia(
            fichero="reconocedor_area.json",
            metrica="acierto de área",
            ruta_real=("combinado_equilibrado",), ruta_nulo=("nulo",),
            contra="siempre el área más frecuente"),
    ),
    Capacidad(
        nombre="nombres_de_mathlib_en_el_prompt",
        que_hace="inyecta nombres de Mathlib verificados en el prompt de"
                 " formalización",
        coste=LOCAL,
        donde="nucleo/core.py::_find_relevant_context",
        evidencia=Evidencia(
            fichero="recuperacion_proofnet.json",
            metrica="precisión de los nombres (%)",
            ruta_real=("resultados", "lexico", "precision"),
            ruta_nulo=("resultados", "nulo", "precision"),
            contra="ofrecer los nombres más frecuentes de Mathlib"),
    ),
    Capacidad(
        nombre="premisas_hibridas",
        que_hace="elige qué premisas de Mathlib ofrecer combinando léxico y"
                 " frecuencia",
        coste=LOCAL,
        donde="scripts/premisas_sin_simp.py",
        evidencia=Evidencia(
            fichero="premisas_sin_simp.json",
            metrica="precisión de premisas",
            ruta_real=("global", "HIBRIDO", "precision"),
            ruta_nulo=("global", "nulo", "precision"),
            contra="las premisas más frecuentes"),
    ),
    Capacidad(
        nombre="orden_de_cascada_por_area",
        que_hace="ordena las tácticas de la cascada según el área detectada",
        coste=COMPILADO,
        donde="nucleo/multi_agent/colimit_agents.py::domain_tactic_order",
        evidencia=Evidencia(
            fichero="modelo_en_la_cascada.json",
            metrica="posición de la táctica que cierra",
            ruta_real=("resultados", "regla", 0),
            ruta_nulo=("resultados", "NULO", 0),
            mas_es_mejor=False,
            contra="`simp` primero y el resto por frecuencia"),
    ),
    Capacidad(
        nombre="modelo_de_orden_de_cascada",
        que_hace="ordena las tácticas con el modelo entrenado sobre 9 488"
                 " pares state_before->tactic de LeanWorkbook",
        coste=LOCAL,
        # OJO: la evidencia NO es `modelo_en_la_cascada.json`, aunque ahi haya
        # una columna que se llama «modelo». Ese modelo se entreno sobre
        # pruebas de una linea de Mathlib y este sobre LeanWorkbook: son dos
        # modelos distintos sobre datos distintos, y usar el numero de uno
        # para respaldar al otro seria justo el error que este modulo existe
        # para impedir. La medicion propia de ESTE es tactic_ranker_report.
        donde="nucleo/lean/solver_cascade.py::TacticRanker",
        evidencia=Evidencia(
            fichero="tactic_ranker_report.json",
            metrica="acierto de la tactica",
            ruta_real=("accuracy",), ruta_nulo=("baseline_mayoritaria",),
            contra="responder siempre la tactica mayoritaria (nlinarith)"),
    ),
    Capacidad(
        nombre="dos_etapas_localizar_y_elegir",
        que_hace="localiza el área y luego elige premisas dentro de ella",
        coste=LOCAL,
        donde="scripts/dos_etapas_localizar_y_elegir.py",
        evidencia=Evidencia(
            fichero="dos_etapas.json",
            metrica="precisión de premisas",
            ruta_real=("resultados", "real", "precision"),
            ruta_nulo=("resultados", "nulo", "precision"),
            contra="las premisas más frecuentes, sin localizar nada"),
    ),
    Capacidad(
        nombre="recuperacion_lexica_de_lemas",
        que_hace="busca lemas por solapamiento léxico con la consulta",
        coste=LOCAL,
        donde="scripts/medir_recuperacion_lemas.py",
        evidencia=Evidencia(
            fichero="recuperacion_lemas.json",
            metrica="precisión de lemas",
            ruta_real=("resultados", "lexico_nl", "precision"),
            ruta_nulo=("resultados", "nulo", "precision"),
            contra="los lemas más frecuentes"),
    ),
    Capacidad(
        nombre="emparejador_semantico",
        que_hace="empareja la consulta con skills por embeddings",
        coste=LLAMADA,
        # NUNCA LLEGO A PRODUCCION: vive solo como script. Se queda en el
        # catalogo a proposito, porque un candidato evaluado y descartado es
        # informacion —dice que ya se probo— y borrarlo invita a reinventarlo.
        donde="scripts/emparejador_semantico.py",
        evidencia=None,
        sin_evidencia_porque=(
            "evaluado y descartado, nunca se adopto: en"
            " emparejador_semantico.json acierta el area en el 12 % (285 de"
            " 2385) contra el 61 % del emparejador lexico"
            " (emparejamiento.json). El fichero no guarda un nulo en forma"
            " comparable, asi que aqui cuenta como sin evidencia; y ademas"
            " cuesta una llamada"),
    ),
    Capacidad(
        nombre="verificacion_con_lean",
        que_hace="formaliza el enunciado y lo verifica con Mathlib",
        coste=COMPILADO,
        donde="nucleo/core.py::_math_via_lean",
        guarda=lambda ctx: ctx.es_matematica and ctx.hay_lean,
        evidencia=None,
        nucleo=True,
    ),
]


# ═══════════════════════════════════════════════════════════════════════════
# LEER EL VEREDICTO DE LOS FICHEROS
# ═══════════════════════════════════════════════════════════════════════════
def _busca(d, ruta):
    for k in ruta:
        if d is None:
            return None
        d = d[k] if isinstance(k, int) else d.get(k)
    return d


def leer_veredicto(cap: Capacidad, datos: pathlib.Path = DATOS) -> Veredicto:
    """El veredicto de una capacidad, recalculado desde el fichero de medición.

    Si el fichero no está, el veredicto es None y NO «gana»: una medición que
    no se puede releer no respalda nada.
    """
    if cap.evidencia is None:
        return Veredicto(motivo="sin evidencia con modelo nulo")
    ev = cap.evidencia
    try:
        d = json.loads((datos / ev.fichero).read_text(encoding="utf-8"))
        dn = (json.loads((datos / ev.fichero_nulo).read_text(encoding="utf-8"))
              if ev.fichero_nulo else d)
    except Exception:                                       # noqa: BLE001
        return Veredicto(motivo="falta %s" % ev.fichero)
    real, nulo = _busca(d, ev.ruta_real), _busca(dn, ev.ruta_nulo)
    if real is None or nulo is None:
        return Veredicto(motivo="la ruta ya no existe en %s" % ev.fichero)
    gana = real > nulo if ev.mas_es_mejor else real < nulo
    return Veredicto(real=float(real), nulo=float(nulo), gana=gana,
                     motivo="%s %.3f contra %.3f (%s)"
                            % (ev.metrica, real, nulo, ev.contra))


# ═══════════════════════════════════════════════════════════════════════════
# DECIDIR
# ═══════════════════════════════════════════════════════════════════════════
def decidir(ctx: Contexto, capacidades: Optional[list] = None,
            datos: pathlib.Path = DATOS) -> Decision:
    """Qué se ejecuta para esta consulta, y por qué cada cosa sí o no."""
    d = Decision()
    for cap in (capacidades if capacidades is not None else CAPACIDADES):
        v = leer_veredicto(cap, datos)
        d.veredictos[cap.nombre] = v

        if v.gana is False:
            d.apagadas.append(cap)
            d.motivos[cap.nombre] = "NO bate a su nulo: " + v.motivo
            continue
        if v.gana is None and cap.coste != LOCAL and not cap.nucleo:
            d.apagadas.append(cap)
            d.motivos[cap.nombre] = (
                cap.sin_evidencia_porque
                or "sin medición contra un nulo y cuesta %s: no se gasta"
                % cap.coste)
            continue
        if cap.guarda is not None and not cap.guarda(ctx):
            d.apagadas.append(cap)
            d.motivos[cap.nombre] = "su guarda no aplica a esta consulta"
            continue
        d.activas.append(cap)
        if v.gana:
            d.motivos[cap.nombre] = v.motivo
        elif cap.nucleo:
            d.motivos[cap.nombre] = "es el proposito del sistema, no un extra"
        else:
            d.motivos[cap.nombre] = "gratis y sin contraindicación"
    return d


def decidir_todo(ctx: Contexto, capacidades: Optional[list] = None) -> Decision:
    """EL MODELO NULO DEL DECISOR: ejecutarlo todo, sin mirar nada.

    Es contra esto que hay que comparar. Un decisor que no ahorra respecto a
    «hazlo todo» y no mejora la calidad no está decidiendo: está adornando.
    """
    d = Decision()
    d.activas = list(capacidades if capacidades is not None else CAPACIDADES)
    d.motivos = {c.nombre: "el nulo lo ejecuta todo" for c in d.activas}
    return d
