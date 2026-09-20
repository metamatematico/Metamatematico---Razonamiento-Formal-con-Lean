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


def _lineas_que_importan(codigo: str, tope: int = 6) -> list:
    """Las líneas del código que dicen algo, sin el encabezado.

    Un `import` le dice al alumno dónde vive una definición, no qué se
    demostró. Si al quitarlos no queda nada —que puede pasar—, se devuelve
    lo que había: enseñar el encabezado es peor que enseñarlo todo, pero
    mucho mejor que dejar el hueco en blanco sin explicar por qué.
    """
    lineas = [l for l in (codigo or "").strip().split("\n") if l.strip()]
    cuerpo = [l for l in lineas
              if not l.lstrip().startswith(("import ", "open ", "set_option",
                                            "namespace ", "end "))]
    return (cuerpo or lineas)[:tope]


#: los ocho veredictos, dichos para quien pregunta y no para quien programa
VEREDICTO = {
    "verificado": ("Lean compiló la formalización contra Mathlib y la aceptó, "
                   "y además el enunciado no era vacío ni era la negación de "
                   "lo que preguntaste. Por eso la respuesta no es una "
                   "opinión."),
    "parcial": ("la estructura de la prueba compila, pero quedó un `sorry` "
                "—un hueco— que la cascada de tácticas no pudo cerrar. Lo que "
                "se demostró es menos de lo que se enunció."),
    "refutado": ("Lean verificó la NEGACIÓN del enunciado: lo que preguntaste "
                 "es falso, y eso está demostrado, no supuesto."),
    "sin_teorema": ("Lean aceptó el archivo, pero el archivo no contiene "
                    "ningún teorema. Compilar no es demostrar: un fichero que "
                    "sólo comprueba tipos también compila."),
    "vacuo": ("hay teorema y compila, pero su conclusión es exactamente "
              "`True`. No afirma nada, así que no vale como respuesta."),
    "no_verificado": ("Lean rechazó el código y los reintentos no lo "
                      "arreglaron. Lo que sigue abajo es una explicación, no "
                      "algo comprobado."),
    "timeout": ("Lean no terminó dentro del límite de tiempo. No es que el "
                "enunciado sea falso: es que no se llegó a saber."),
    "sin_entorno": ("no hay un Lean instalado con el que comprobar, así que "
                    "nada de esto pasó por el verificador. No es un fallo de "
                    "la matemática."),
}


def explicar(*, consulta: str = "", area: str = "", lectura: str = "",
             contexto: Optional[dict] = None, plan: Any = None,
             revision: Any = None, rondas: int = 0,
             estado_lean: str = "", error_lean: str = "",
             veredicto: str = "",
             consulta_original: str = "", traducida: bool = False,
             modulos: Optional[list] = None,
             reparacion: str = "", nombres_dudosos: Optional[list] = None,
             nombres_desmentidos: Optional[list] = None,
             codigo: str = "", nota_veredicto: str = "") -> Explicacion:
    """Monta la explicación del proceso con lo que el pipeline ya tiene.

    Todos los argumentos son opcionales a propósito: este módulo se llama
    desde varios puntos del camino y ninguno tiene todo el rastro. Lo que
    falta no se inventa ni se omite — el paso dice que no consta.

    EL ORDEN ES EL DEL RECORRIDO, NO EL DE LA IMPORTANCIA
    -----------------------------------------------------
    Los pasos van como le pasaron a la consulta: entra, se traduce, se lee,
    se busca, se formaliza, se compila, se repara, se vuelve a compilar y
    sale. Ordenarlos por interés —primero lo que mejor mide— produciría un
    panel más lucido y le quitaría lo único que lo hace útil, que es poder
    seguir el hilo de la propia pregunta de principio a fin.
    """
    ctx = contexto or {}
    e = Explicacion()

    # ── 0 · la frontera del idioma, a la entrada ────────────────────────
    #
    # ES EL PRIMER PASO Y EL MAS INVISIBLE. Si preguntaste en castellano, lo
    # que el resto del sistema leyo NO fue tu frase: fue una traduccion. Un
    # panel que empieza en «que entendi» se salta el punto exacto donde se
    # pudo perder algo, y es el punto donde mas facil es perderlo.
    if traducida and consulta_original:
        e.pasos.append(Paso(
            "idioma", "Lo primero: tu pregunta se tradujo al inglés",
            detalle=("todo el aparato es inglés —las palabras clave del grafo, "
                     "los 183 433 hechos de Mathlib y el propio Lean—, así que "
                     "la consulta se traduce **una sola vez, al entrar**, con "
                     "un modelo local que no cuesta nada por consulta. La "
                     "notación matemática se extrae antes y se vuelve a poner "
                     "después, porque un traductor general convierte `\\sin x` "
                     "en `\\without x`."),
            items=(["escribiste: %s" % consulta_original.strip()[:160],
                    "el sistema leyó: %s" % (consulta or "").strip()[:160]]),
            respaldo=("sobre 200 enunciados con notación se protegieron 15 014 "
                      "caracteres y se expusieron 653, con hueco en 21 de los "
                      "200: la protección no es perfecta y por eso se dice"),
        ))
    elif consulta_original:
        e.pasos.append(Paso(
            "idioma", "Tu pregunta no se tradujo",
            detalle=("entró ya en inglés, que es el idioma en el que trabajan "
                     "el grafo, Mathlib y Lean, así que pasó directa."),
        ))

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
        respaldo=("el área se acierta el 62,1 % de las veces con exactitud "
                  "equilibrada, frente al 33,3 % de responder siempre la clase "
                  "mayoritaria" if area else ""),
    ))

    # ── 1b · si la notación estaba mal escrita, se avisa ────────────────
    #
    # Sólo el delimitador descasado, y el motivo es de medida: avisar de los
    # cinco motivos daría 3,6 % de falsos positivos sobre enunciados
    # correctos, o sea uno de cada veintiocho alumnos aprendiendo a ignorar
    # los avisos. Un guardián que salta con el codigo bueno se desactiva solo.
    avisos = [a for a in (getattr(revision, "avisos", None) or []) if a]
    if avisos:
        e.pasos.append(Paso(
            "notacion", "Algo de la notación no cuadra",
            detalle=("un delimitador sin cerrar hace que se formalice OTRA "
                     "fórmula, y Lean verifica esa otra tan contento: el sello "
                     "saldría puesto sobre un enunciado que no preguntaste."),
            items=[str(a)[:160] for a in avisos[:4]],
            respaldo=("este aviso tiene 0,6 % de falsos positivos sobre 23 243 "
                      "enunciados correctos y caza el 99 % de las roturas "
                      "reales; los otros cuatro motivos no se avisan porque "
                      "fallan el 2,3 % y sólo cazan la mitad"),
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

    # ── 3b · qué módulos de Mathlib vio Lean ────────────────────────────
    #
    # VA CON SU VEREDICTO DE «INERTE», y eso es lo interesante de enseñarlo:
    # el grafo hace aqui trabajo real —bate al azar 18/20 contra 14/20— y aun
    # asi no aporta, porque un conjunto fijo de tres modulos consigue los
    # mismos 18. Ensenar solo lo que gana seria publicidad, no explicacion.
    mods = [m for m in (modulos or []) if m]
    if mods:
        e.pasos.append(Paso(
            "modulos", "Qué trozos de Mathlib se le dieron a Lean",
            detalle=("`import Mathlib` entero tarda 742 segundos —más que el "
                     "tiempo límite—, así que se importa sólo lo que hace "
                     "falta."),
            items=[str(m) for m in mods[:8]],
            respaldo=("esta elección es **inerte**: elabora 18 de 20 "
                      "enunciados, exactamente los mismos 18 que un conjunto "
                      "fijo de tres módulos. Gana al azar (14 de 20) pero no "
                      "gana a la constante"),
        ))

    # ── 3c · qué se arregló antes de compilar ───────────────────────────
    dudosos = [n for n in (nombres_dudosos or []) if n]
    if reparacion or dudosos:
        det = []
        if reparacion:
            det.append("se corrigió el encabezado y se volvió a compilar: %s"
                       % reparacion)
        if dudosos:
            det.append("estos identificadores no aparecen en el índice de "
                       "217 419 nombres reales de Mathlib, así que o no "
                       "existen o están mal cualificados")
        e.pasos.append(Paso(
            "reparacion", "Qué se arregló antes de darlo por malo",
            detalle="; ".join(det) + ".",
            items=[str(n) for n in dudosos[:6]],
            respaldo=("el reparador es deliberadamente conservador: sobre las "
                      "241 pruebas de miniF2F que ya compilaban no modifica "
                      "ninguna. Sólo actúa donde hay algo roto"),
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

    # ── 5 · qué dijo Lean, y cuál de los ocho veredictos salió ──────────
    #
    # EL VEREDICTO SE NOMBRA Y SE EXPLICA, los dos. «no_verificado» a secas
    # no le dice nada a nadie, y es justo el caso en el que el alumno mas
    # necesita saber que lo que va a leer debajo no esta comprobado.
    if estado_lean or veredicto:
        det = VEREDICTO.get(veredicto, "")
        if det:
            det = "el veredicto es **%s**: %s" % (veredicto, det)
        elif error_lean:
            det = "Lean 4 la rechazó: %s" % error_lean[:220]
        else:
            det = "Lean devolvió `%s`." % (estado_lean or "sin estado")
        if error_lean and veredicto not in ("verificado", "refutado"):
            det += " Lo que dijo exactamente: «%s»." % error_lean[:200]
        if rondas:
            det += (" Antes de darlo por bueno o por malo, el sistema cerró "
                    "el lazo %d vez/veces: le devolvió a quien escribió el "
                    "código el error de Lean, y sólo aceptó el reintento si "
                    "**mejoraba** el resultado anterior." % rondas)
        e.pasos.append(Paso(
            "lean", "Qué dijo el verificador",
            detalle=det,
            # EL TEOREMA, NO LOS IMPORTS. Cortando por las seis primeras
            # lineas el alumno veia seis `import Mathlib.…` y ni una linea de
            # matematicas: justo lo unico que no le dice nada de su pregunta.
            items=(_lineas_que_importan(codigo)
                   if veredicto == "verificado" else []),
            respaldo=("hay ocho veredictos y no dos porque compilar no es "
                      "demostrar: tres de ellos —`vacuo`, `sin_teorema` y "
                      "`refutado`— nombran casos en que Lean acepta el archivo "
                      "y aun así no se demostró lo que preguntaste"),
        ))

    # ── 6 · la frontera del idioma, a la salida ─────────────────────────
    #
    # Cierra el recorrido por donde lo abrio. Y hay una razon para decirlo
    # en vez de darlo por hecho: el enunciado que el modelo tiene delante ya
    # esta en ingles, asi que «responde en el idioma del usuario» le haria
    # contestar en ingles. Que salga en castellano es una decision, no una
    # consecuencia.
    desmentidos = [n for n in (nombres_desmentidos or []) if n]
    if traducida or desmentidos:
        det = []
        if traducida:
            det.append("la respuesta vuelve a tu idioma, y lo que se le "
                       "enseña como «pregunta original» es la tuya, no la "
                       "traducción")
        if desmentidos:
            det.append("además se desmintió al traductor en %d nombre(s): "
                       "dijo que no existían y el índice dice que sí"
                       % len(desmentidos))
        e.pasos.append(Paso(
            "salida", "Cómo sale la respuesta",
            detalle="; ".join(det) + ".",
            items=[str(n) for n in desmentidos[:5]],
        ))

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
        out.append("**Lo que costó**: " + coste_en_palabras(exp.coste) + "\n")
    return "".join(out)


#: singular y plural de cada clase de coste, porque «6 local» no es castellano
#: y «local» a secas no le dice al alumno lo que importa: que fue gratis.
COSTE = {
    "llamada al modelo": ("1 llamada al modelo", "%d llamadas al modelo"),
    "compilado de Lean": ("1 compilado de Lean", "%d compilados de Lean"),
    "local": ("1 paso local, que no cuesta nada",
              "%d pasos locales, que no cuestan nada"),
}


def coste_en_palabras(coste: dict) -> str:
    """«1 compilado de Lean, 6 pasos locales, que no cuestan nada»."""
    partes = []
    for clave, n in (coste or {}).items():
        if not n:
            continue
        uno, varios = COSTE.get(clave, ("1 %s" % clave, "%%d %s" % clave))
        partes.append(uno if n == 1 else varios % n)
    return ", ".join(partes)
