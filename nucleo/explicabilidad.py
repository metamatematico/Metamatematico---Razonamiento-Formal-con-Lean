# -*- coding: utf-8 -*-
"""Lo que el sistema hizo con tu consulta, y por qué. Para el alumno.

EL HUECO QUE CIERRA
-------------------
Este repositorio calcula una cantidad enorme de rastro y no le enseña casi
nada a quien pregunta. `decisor.py` decide POR CONSULTA qué capacidades
corren, con la evidencia de cada una contra su modelo nulo y el coste en
llamadas al modelo y compilaciones de Lean. El emparejador sabe si los skills
vinieron del chat, del emparejador o de las palabras. `Viaje` y
`Levantamiento` devuelven su motivo cuando no hay respuesta. La revisión de
notación guarda qué tramos reconoció.

Todo eso existe, se calcula en cada consulta, y termina en la página de
ANÁLISIS o en un script de informe. Al alumno le llega un veredicto y una
explicación en prosa. Es la misma forma de los tres fallos que este sistema ya
se comió: el dato estaba y no se pasaba.

QUE ESTE MODULO NO HACE
-----------------------
No calcula nada nuevo y no explica la MATEMÁTICA —de eso se encarga la
respuesta—. Explica el PROCESO: qué se entendió, qué se activó, qué se ofreció
al modelo, qué se decidió y qué contestó Lean.

LA REGLA: CADA AFIRMACION CON SU RESPALDO, Y EL SILENCIO TAMBIEN SE CUENTA
--------------------------------------------------------------------------
Dos cosas que un panel de explicabilidad hace mal por omisión y aquí no:

  · Una capacidad APAGADA se enseña igual que una encendida, con su motivo.
    «El reconocedor de área no corrió porque mide peor que su nulo» le dice al
    alumno más sobre este sistema que cualquier lista de lo que sí corrió.

  · Una cifra va con su modelo nulo o no va. Decir «el vocabulario acierta el
    23,9 %» sin decir que el azar acierta el 1,45 % no explica nada: no se
    sabe si 23,9 es mucho o poco.

Si una parte del rastro no está disponible, el paso lo dice —«no consta»— en
vez de desaparecer. Un panel que oculta sus huecos enseña un sistema que no
existe.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional


#: Las tres procedencias que puede tener un skill activado, en castellano.
PROCEDENCIA = {
    "chat": "de tu consulta, por el camino real del chat",
    "emparejador": "del emparejador de palabras sobre el grafo",
    "palabras": "de las palabras sueltas, sin emparejador",
}


@dataclass
class Paso:
    """Un tramo del proceso, tal y como se le cuenta al alumno."""
    clave: str
    titulo: str
    #: qué pasó, en una o dos frases
    detalle: str = ""
    #: la lista concreta —skills, nombres, tácticas—, si la hay
    items: list = field(default_factory=list)
    #: la cifra que respalda este paso, SIEMPRE con su nulo cuando existe
    respaldo: str = ""

    def __bool__(self) -> bool:
        return bool(self.detalle or self.items)


@dataclass
class Explicacion:
    pasos: list = field(default_factory=list)
    #: capacidades que NO corrieron, con su motivo
    apagadas: list = field(default_factory=list)
    #: llamadas al modelo y compilaciones de Lean que costó esta consulta
    coste: dict = field(default_factory=dict)

    def a_dict(self) -> dict:
        return {
            "pasos": [{"clave": p.clave, "titulo": p.titulo,
                       "detalle": p.detalle, "items": p.items,
                       "respaldo": p.respaldo}
                      for p in self.pasos if p],
            "apagadas": self.apagadas,
            "coste": self.coste,
        }


def _nombre_legible(sid: str) -> str:
    return sid.replace("-", " ")


def explicar(*, consulta: str = "", area: str = "", lectura: str = "",
             contexto: Optional[dict] = None, plan: Any = None,
             revision: Any = None, rondas: int = 0,
             estado_lean: str = "", error_lean: str = "",
             veredicto: str = "") -> Explicacion:
    """Monta la explicación del proceso con lo que el pipeline ya tiene.

    Todos los argumentos son opcionales a propósito: este módulo se llama
    desde varios puntos del camino y ninguno tiene todo el rastro. Lo que
    falta no se inventa ni se omite — el paso dice que no consta.
    """
    ctx = contexto or {}
    e = Explicacion()

    # ── 1 · qué entendí de tu consulta ──────────────────────────────────
    partes = []
    if area:
        partes.append("la coloqué en **%s**" % area)
    if lectura:
        partes.append("y de las lecturas posibles el formalizador declaró "
                      "«%s»" % lectura)
    rasgos = getattr(revision, "rasgos", None) or {}
    if rasgos.get("relacion"):
        partes.append("la relación principal del enunciado es `%s`"
                      % rasgos["relacion"])
    e.pasos.append(Paso(
        "entendi", "Qué entendí de tu consulta",
        detalle=("; ".join(partes) + "." if partes
                 else "no consta el área ni la lectura: la consulta entró "
                      "por un camino que no las calcula."),
    ))

    # ── 2 · qué se activó del grafo ─────────────────────────────────────
    skills = list(ctx.get("relevant_skills") or [])
    proc = ctx.get("procedencia") or ""
    e.pasos.append(Paso(
        "grafo", "Qué activó el grafo de conocimiento",
        detalle=("%d concepto(s), %s."
                 % (len(skills), PROCEDENCIA.get(proc, "por coincidencia de "
                                                 "palabras sobre los 353 nodos"))
                 if skills else
                 "ningún concepto se activó: el emparejador no encontró "
                 "coincidencia, y el modelo trabajó sin vocabulario del grafo."),
        items=[_nombre_legible(s) for s in skills[:8]],
    ))

    # ── 3 · qué vocabulario se le ofreció al modelo ─────────────────────
    #
    # ES LA CAPACIDAD QUE MEJOR MIDE DE TODO EL SISTEMA, y por eso lleva su
    # respaldo pegado: sin el nulo, un 23,9 % no significa nada.
    ofrecidos = ctx.get("mathlib_verificado") or {}
    planos = []
    for _sid, v in ofrecidos.items():
        planos.extend(v if isinstance(v, (list, tuple)) else [v])
    e.pasos.append(Paso(
        "vocabulario", "Qué nombres de Mathlib se le pasaron al modelo",
        detalle=("comprobados uno a uno con `#check` antes de ofrecerlos."
                 if planos else
                 "ninguno: el prompt salió sin vocabulario del grafo."),
        items=[str(x) for x in planos[:8]],
        respaldo=("de lo que el grafo ofrece contra ProofNet se usa de verdad "
                  "el 23,9 %, frente al 1,45 % de ofrecer los identificadores "
                  "más frecuentes sin mirar la consulta" if planos else ""),
    ))

    # ── 4 · qué decidió el sistema, y qué dejó fuera ────────────────────
    if plan is not None:
        activas = getattr(plan, "activas", []) or []
        apagadas = getattr(plan, "apagadas", []) or []
        motivos = getattr(plan, "motivos", {}) or {}
        e.pasos.append(Paso(
            "decisor", "Qué capacidades corrieron",
            detalle=("cada una corre sólo si su evidencia gana a su modelo "
                     "nulo; las que miden peor que no hacer nada están "
                     "apagadas siempre."),
            items=["%s — %s" % (getattr(c, "nombre", "?"),
                                getattr(c, "que_hace", ""))
                   for c in activas],
        ))
        # LAS APAGADAS SE ENSEÑAN. Es la parte que más dice de este sistema:
        # que una capacidad exista y NO se use porque se midió y perdió.
        e.apagadas = [
            {"nombre": getattr(c, "nombre", "?"),
             "que_hace": getattr(c, "que_hace", ""),
             "por_que": motivos.get(getattr(c, "nombre", ""), "")}
            for c in apagadas
        ]
        try:
            coste = plan.coste
            e.coste = {str(k): v for k, v in coste.items() if v}
        except Exception:                                       # noqa: BLE001
            e.coste = {}

    # ── 5 · qué dijo Lean ───────────────────────────────────────────────
    if estado_lean or veredicto:
        if veredicto == "verificado":
            det = ("Lean 4 compiló la formalización contra Mathlib y la "
                   "aceptó. Eso es lo que hace que la respuesta no sea una "
                   "opinión.")
        elif error_lean:
            det = ("Lean 4 la rechazó: %s" % error_lean[:220])
        else:
            det = "Lean devolvió `%s`." % (estado_lean or "sin estado")
        if rondas:
            det += (" El sistema reintentó %d vez/veces realimentando el "
                    "error al generador." % rondas)
        e.pasos.append(Paso("lean", "Qué dijo el verificador", detalle=det))

    return e


#: cuántas apagadas y cuánto motivo caben en el panel del alumno
TOPE_APAGADAS = 4
TOPE_MOTIVO = 180


def _recorta(texto: str, tope: int) -> str:
    """Corta por la primera frase que quepa, no a mitad de palabra."""
    t = " ".join((texto or "").split())
    if len(t) <= tope:
        return t
    corte = t[:tope]
    punto = max(corte.rfind(". "), corte.rfind("; "))
    return (corte[:punto + 1] if punto > tope // 2
            else corte.rsplit(" ", 1)[0] + "…")


def en_markdown(exp: Explicacion, breve: bool = True) -> str:
    """El panel, listo para pintar en el chat.

    `breve` es el valor por defecto Y ESO IMPORTA. El rastro entero son once
    capacidades apagadas con motivos de párrafo —ahí está escrito por qué el
    emparejador semántico perdió contra el léxico, con sus dos bancos—, y eso
    es material para quien audita el sistema, no para quien acaba de preguntar
    por la irracionalidad de raíz de 2. Enterrar la explicación en un muro es
    otra forma de no explicar.

    El dict completo viaja igual en los metadatos: la página de análisis lo
    pinta entero, y aquí se enseña lo que cabe leer.
    """
    if not exp.pasos:
        return ""
    out = []
    for p in exp.pasos:
        if not p:
            continue
        out.append("**%s** — %s" % (p.titulo, p.detalle))
        if p.items:
            tope = 5 if breve else len(p.items)
            out.append("".join("\n  - %s" % i for i in p.items[:tope]))
            if len(p.items) > tope:
                out.append("\n  - …y %d más" % (len(p.items) - tope))
        if p.respaldo:
            out.append("\n  <sub>%s</sub>" % p.respaldo)
        out.append("\n\n")

    if exp.apagadas:
        # LAS APAGADAS PRIMERO LAS MEDIDAS. Una capacidad que existe y no se
        # usa PORQUE SE MIDIO Y PERDIO dice mas del sistema que una cuya
        # guarda simplemente no aplicaba a esta consulta.
        def _peso(a):
            return 0 if "nulo" in (a.get("por_que") or "").lower() else 1
        orden = sorted(exp.apagadas, key=_peso)
        tope = TOPE_APAGADAS if breve else len(orden)
        out.append("**Qué NO se usó, y por qué**\n")
        for a in orden[:tope]:
            motivo = (_recorta(a["por_que"], TOPE_MOTIVO) if breve
                      else a["por_que"])
            out.append("  - `%s` — %s\n" % (a["nombre"], motivo))
        if len(orden) > tope:
            out.append("  - …y %d capacidades más apagadas\n"
                       % (len(orden) - tope))
        out.append("\n")

    if exp.coste:
        out.append("**Lo que costó**: "
                   + ", ".join("%s %s" % (v, k) for k, v in exp.coste.items())
                   + "\n")
    return "".join(out)
