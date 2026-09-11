# -*- coding: utf-8 -*-
"""La campaña que cierra la única pregunta que sigue abierta.

LA PREGUNTA
-----------
El grafo mete nombres de Mathlib verificados en el prompt de formalización, y
eso está medido contra ProofNet: 21,6 % de precisión y 18,3 % de cobertura
contra un nulo de 1,5 % / 3,3 %. Catorce veces mejor.

Pero eso mide PUNTERÍA, no RESULTADO. Que el grafo ofrezca los nombres que la
formalización de oro usa no demuestra que Lean verifique más. Y esa —¿el
núcleo mejora la respuesta?— es la pregunta que este repositorio lleva sin
contestar desde el principio.

POR QUÉ NO SE PUEDE CONTESTAR GRATIS
------------------------------------
`scripts/replay.py` reproduce las formalizaciones ya escritas contra todo lo
que el sistema hace DESPUÉS: imports, reparación, cascada, premisas. Coste
cero. Pero el vocabulario actúa ANTES del modelo, así que replay no lo alcanza
— su propio docstring lo dice: «Lo que NO puede medir es si otro prompt habría
hecho al modelo escribir mejor».

Y las 9 grabaciones que hay no sirven: TODAS tienen `skills=[]`. Son
aritmética y álgebra básica donde el emparejador no activa nada, así que las
dos ramas serían la misma ejecución. Es el mismo fallo que invalidó la primera
medición de imports, donde 14 de 20 casos eran idénticos entre ramas.

LO QUE HACE ESTA CAMPAÑA
------------------------
Graba los 23 casos DONDE EL GRAFO SÍ HABLA —verificado uno a uno: cada uno
recibe nombres de Mathlib— en varias configuraciones. A partir de ahí la
comparación queda hecha para siempre y `replay.py` la repite gratis.

    completo          el sistema como está
    sin-vocabulario   sin el bloque «VERIFIED Mathlib names». SÓLO eso: los
                      imports, las premisas y la cascada siguen igual. Es el
                      cuchillo fino que falta — `ablacion_nucleo.py` apagaba
                      `_find_relevant_context` ENTERO y con él se iban también
                      los imports, así que no aislaba el vocabulario
    con-estructura    completo MÁS el bloque estructural que hoy está apagado
                      (prerrequisitos, tácticas y competencia emergente), que
                      es la otra capacidad sin evidencia

Con tres configuraciones el mismo gasto contesta DOS preguntas: si el
vocabulario paga, y si las aristas pagan.

NO GASTA NADA SIN QUE SE LO PIDAN
---------------------------------
Por defecto hace una pasada EN SECO: dice qué va a correr y cuánto va a
costar, con el precio real leído de `nucleo/llm/contador.py`, y no llama a
nadie. Para gastar de verdad hay que escribir `--ejecutar`.

    python -m scripts.campana_de_grabacion                  # en seco
    python -m scripts.campana_de_grabacion --ejecutar
    python -m scripts.campana_de_grabacion --ejecutar --casos 6
"""
import argparse
import asyncio
import io
import json
import os
import re
import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SALIDA = "E:/Metamatematico/data/campana_de_grabacion.json"

#: LOS CASOS, Y POR QUÉ ESTOS.
#:
#: Verificado uno a uno con `_nombres_mathlib`: los 23 reciben vocabulario del
#: grafo. Eso es el requisito que las grabaciones que había no cumplían, y sin
#: él la medición no puede detectar una diferencia aunque exista.
#:
#: Cubren siete áreas a propósito —grupos, números, análisis, topología,
#: álgebra lineal, anillos, geometría algebraica— porque el vocabulario del
#: grafo es desigual por área y una muestra de una sola rama mediría esa rama.
CASOS = [
    # grupos
    "Demuestra que todo subgrupo de un grupo cíclico es cíclico",
    "Demuestra que un grupo de orden primo es cíclico",
    "Demuestra que la intersección de subgrupos es un subgrupo",
    "Demuestra que el orden de un elemento divide al orden del grupo",
    "Demuestra que un grupo abeliano finito es producto de cíclicos",
    # números
    "Demuestra que la raíz de 2 es irracional",
    "Demuestra que los números racionales son numerables",
    "Demuestra que todo entero se factoriza en primos de forma única",
    "Demuestra que el conjunto de partes de N no es numerable",
    # análisis
    "Demuestra que toda sucesión de Cauchy en R converge",
    "Demuestra que la serie armónica diverge",
    "Demuestra que la derivada de una constante es cero",
    "Demuestra que toda función derivable es continua",
    "Demuestra que toda función continua en un compacto alcanza su máximo",
    # topología
    "Demuestra que un espacio métrico compacto es completo",
    "Demuestra que la unión de dos conjuntos abierto es abierto",
    # álgebra lineal
    "Demuestra que todo espacio vectorial tiene una base",
    "Demuestra que dos matrices semejantes tienen el mismo determinante",
    # anillos
    "Demuestra que los polinomios irreducibles generan ideales maximales",
    "Demuestra que todo anillo finito sin divisores de cero es un cuerpo",
    # geometría algebraica y homológica
    "Demuestra que toda variedad afín es un esquema",
    "Demuestra que la cohomología de un complejo es un objeto graduado",
    "Demuestra que el anillo de enteros de un cuerpo de números es de Dedekind",
]

CONFIGS = ("completo", "sin-vocabulario", "con-estructura")

#: Llamadas al modelo por caso, medidas sobre las tandas anteriores:
#: formalizar + traducir, y una ronda de revisión en algo menos de la mitad.
#: Se redondea HACIA ARRIBA — un presupuesto que se queda corto es peor que
#: uno que sobra.
LLAMADAS_POR_CASO = 2.5


def _cargar_clave() -> bool:
    if os.environ.get("ANTHROPIC_API_KEY"):
        return True
    ruta = "E:/Metamatematico/.env"
    if not os.path.exists(ruta):
        return False
    m = re.search(r'ANTHROPIC_API_KEY\s*=\s*["\']?([^"\'\r\n]+)',
                  io.open(ruta, encoding="utf-8-sig").read())
    if not m:
        return False
    os.environ["ANTHROPIC_API_KEY"] = m.group(1).strip()
    return True


def _apagar(n, config):
    """Aplica una configuración. Devuelve cómo restaurarla.

    EL CUCHILLO ES FINO A PROPÓSITO. `sin-vocabulario` quita del contexto
    SÓLO la clave `mathlib_verificado`, que es la que alimenta el bloque
    «VERIFIED Mathlib names». Todo lo demás —`relevant_skills`, que elige los
    imports; el pilar; las skills que se graban— sigue igual, así que la
    diferencia entre ramas es el vocabulario y nada más.
    """
    if config == "completo":
        return lambda: None

    if config == "sin-vocabulario":
        orig = n._find_relevant_context

        def sin_nombres(*a, **k):
            ctx = orig(*a, **k)
            if isinstance(ctx, dict):
                ctx.pop("mathlib_verificado", None)
            return ctx

        n._find_relevant_context = sin_nombres
        return lambda: setattr(n, "_find_relevant_context", orig)

    if config == "con-estructura":
        # La capacidad la gobierna el decisor y está apagada por falta de
        # evidencia. Aquí se enciende A MANO y sólo para esta rama: es
        # justamente la evidencia que falta la que se viene a producir.
        from nucleo import decisor as _d
        orig = _d.decidir

        def con_extra(ctx, *a, **k):
            plan = orig(ctx, *a, **k)
            for cap in list(plan.apagadas):
                if cap.nombre == "contexto_estructural_en_el_prompt":
                    plan.apagadas.remove(cap)
                    plan.activas.append(cap)
                    plan.motivos[cap.nombre] = "encendida por la campaña"
            return plan

        _d.decidir = con_extra
        return lambda: setattr(_d, "decidir", orig)

    if config == "sin-reparacion":
        # LA PIEZA QUE LA EVIDENCIA SEÑALA COMO LA QUE CARGA EL PESO.
        #
        # `replay.py` reproduce las formalizaciones ya escritas contra todo lo
        # que viene después —imports, premisas, cascada— y da 42 %. En vivo el
        # sistema llega al 60 %. La diferencia entre esas dos cifras es, casi
        # toda, el bucle de reparación: devolverle al modelo el error de Lean
        # y dejarle una segunda oportunidad.
        #
        # «Casi toda» no es una medición. Esta rama la convierte en una:
        # apaga SÓLO la reparación —los imports, las premisas, la cascada y el
        # vocabulario siguen— y se parea contra `completo`.
        orig = n._revisar_con_lean

        async def sin_revisar(lean_code, result, *a, **k):
            # Devuelve lo que ya había, con cero rondas: la firma que espera
            # el llamante es (codigo, resultado, rondas_usadas).
            return lean_code, result, 0

        n._revisar_con_lean = sin_revisar
        return lambda: setattr(n, "_revisar_con_lean", orig)

    raise ValueError(config)


#: Tokens que consume UN caso completo. TERCERA CIFRA, Y LAS DOS ANTERIORES
#: ESTABAN MAL POR EL MISMO MOTIVO: muestra de uno.
#:
#:   1ª  supuesta      2,5 llamadas de 2100/550   ->  $0,020/caso
#:   2ª  de la prueba de humo (UN caso)           ->  $0,031/caso
#:   3ª  de la tanda real de 20 casos             ->  $0,088/caso
#:
#: La segunda salía de medir el caso 1, que resulta ser de los baratos. El
#: reparto es de COLA MUY PESADA —mínimo $0,017, mediana $0,026, máximo
#: $0,314— porque los casos difíciles gastan rondas de reparación. La media
#: es 3,4 veces la mediana, así que presupuestar con la mediana o con un caso
#: suelto se queda corto por un factor de tres.
#:
#: Es el mismo error que este repositorio documenta en otros sitios: medir n=1
#: y llamarlo medición. Aquí costó que la rama de control no llegara a correr.
TOKENS_POR_CASO = (18000, 3900)

#: Y TAMPOCO SON LOS MISMOS TOKENS EN TODAS LAS RAMAS. Los 18 000 de arriba
#: incluyen las rondas de reparacion, que arrastran el error de Lean y el
#: codigo anterior. `sin-reparacion` no las tiene: una formalizacion y una
#: traduccion. Medido en la prueba de humo: $0,025 el caso.
TOKENS_POR_CASO_POR_RAMA = {
    "sin-reparacion": (7000, 1500),
}

#: El caso más caro observado. El tope se comprueba ANTES de empezar cada
#: caso reservando esto: si no cabe el peor caso, se para. Comprobarlo sólo
#: después es cerrar la puerta con el gasto ya hecho — la tanda de 20 se pasó
#: $0,054 del tope justo así.
PEOR_CASO = 0.32

#: El peor caso NO es el mismo en todas las ramas, y usar el de la mas cara
#: para todas deja dinero sin gastar por prudencia mal calibrada.
#:
#: Los $0,32 son de `completo`, donde una consulta dificil encadena dos rondas
#: de reparacion. En `sin-reparacion` esa cola no existe por construccion: la
#: rama hace una formalizacion y una traduccion y se acabo. Medido en la
#: prueba de humo: $0,025.
PEOR_CASO_POR_RAMA = {
    "sin-reparacion": 0.08,
}

#: Y EL MODELO NO SE DEDUCE DEL YAML.
#:
#: `nucleo_config.yaml` dice `claude-sonnet-5`, pero ese fichero sólo lo lee
#: la interfaz: `Nucleo()` construido a pelo usa el defecto del dataclass, que
#: es `claude-opus-5` en LOS DOS `LLMConfig`. La prueba de humo se facturó a
#: Opus mientras la pasada en seco anunciaba Sonnet — o sea que el presupuesto
#: mentía por 2,5×. Aquí el modelo se pasa explícito y se fija en el Núcleo.
MODELO_POR_DEFECTO = "claude-sonnet-5"


def presupuesto(n_casos: int, configs, modelo: str) -> tuple:
    """Lo que va a costar, con el precio real. Ninguna llamada."""
    from nucleo.llm.contador import precio_de
    pe, ps = precio_de(modelo)
    entrada, salida = TOKENS_POR_CASO
    if len(configs) == 1:
        entrada, salida = TOKENS_POR_CASO_POR_RAMA.get(
            configs[0], TOKENS_POR_CASO)
    por_caso = entrada / 1e6 * pe + salida / 1e6 * ps
    n = n_casos * len(configs)
    return modelo, n, n * por_caso, por_caso


async def main(n_casos: int, configs, ejecutar: bool, tope: float,
               modelo: str) -> int:
    casos = CASOS[:n_casos]
    modelo, ejecuciones, coste, por_caso = presupuesto(
        len(casos), configs, modelo)

    print("=== CAMPAÑA DE GRABACIÓN ===")
    print("  casos          : %d" % len(casos))
    print("  configuraciones: %s" % ", ".join(configs))
    print("  modelo         : %s" % modelo)
    print("  ejecuciones    : %d  ($%.3f cada una, medido)"
          % (ejecuciones, por_caso))
    print("  COSTE ESTIMADO : $%.2f" % coste)
    print("  TOPE DURO      : $%.2f  (se para al pasarlo)" % tope)
    print("  + tiempo de Lean: ~%d verificaciones" % ejecuciones)
    if coste > tope:
        print("\n  AVISO: el estimado PASA del tope. El tope manda: la tanda")
        print("  se cortará a medias y quedará desequilibrada entre ramas.")
        print("  Baja --casos o quita una configuración.")

    if not ejecutar:
        print("\n  PASADA EN SECO: no se ha llamado a nadie.")
        print("  Para gastar de verdad: --ejecutar")
        return 0

    if not _cargar_clave():
        print("\n  No hay ANTHROPIC_API_KEY ni .env. No se ejecuta.")
        return 1

    import logging
    logging.disable(logging.INFO)
    os.environ["METAMAT_GRABAR"] = "1"
    from nucleo.core import Nucleo
    from nucleo import grabacion
    from nucleo.llm.contador import Contador

    # EL TOPE NO SE FIA DE LA ESTIMACION.
    #
    # `presupuesto()` multiplica una media de llamadas por caso, y una media
    # se equivoca hacia arriba tanto como hacia abajo. El contador lleva el
    # gasto REAL —lo registra cada llamada—, asi que el tope se comprueba
    # contra eso: se toma el total al empezar y se para en cuanto lo gastado
    # en esta tanda pasa del limite. Es la diferencia entre un presupuesto y
    # una promesa.
    gasto_inicial = Contador.total()

    def gastado() -> float:
        return Contador.total() - gasto_inicial

    filas = []
    for config in configs:
        print("\n--- %s ---" % config)
        n = Nucleo()
        await n.initialize()
        # EL MODELO, EXPLÍCITO. Ver la nota de `MODELO_POR_DEFECTO`: sin esto
        # el Núcleo arranca en Opus por el defecto del dataclass y la tanda
        # cuesta 2,5 veces lo presupuestado.
        n.reconfigure_llm("anthropic", modelo,
                          os.environ["ANTHROPIC_API_KEY"], max_tokens=4096)
        if getattr(n._llm.config, "model", "") != modelo:
            print("  NO SE PUDO FIJAR EL MODELO (%s). Se aborta."
                  % getattr(n._llm.config, "model", "?"))
            return 1
        restaurar = _apagar(n, config)
        try:
            grabacion.activar(config)
            for i, q in enumerate(casos, 1):
                # SE RESERVA EL PEOR CASO. Comprobar `gastado() >= tope`
                # deja pasar un caso que puede costar $0,31, y así la tanda
                # anterior acabó $0,054 por encima del tope.
                reserva = PEOR_CASO_POR_RAMA.get(config, PEOR_CASO)
                if gastado() + reserva > tope:
                    print("\n  TOPE DE $%.2f: quedan $%.3f y el peor caso "
                          "cuesta $%.2f. Se para ($%.3f gastados)."
                          % (tope, tope - gastado(), reserva, gastado()))
                    break
                t0 = time.time()
                codigo = ""
                try:
                    r = await n.process(q)
                    # EL VEREDICTO VIVE EN `lean_result.status`.
                    #
                    # Aqui ponia `getattr(r, "lean_status", "")`, que NO existe
                    # en `NucleoResponse` —tiene `lean_result`— y devolvia ""
                    # siempre. La tanda entera habria grabado veredictos vacios
                    # y el gasto se habria perdido sin que nada fallara. Es la
                    # familia de fallo contra la que este repositorio tiene una
                    # suite: el instrumento roto que no protesta.
                    lr = getattr(r, "lean_result", None)
                    veredicto = str(getattr(lr, "status", "")) if lr else ""
                    # `codigo_verificado` es el que Lean vio DE VERDAD, no el
                    # que se le pasó: `check_code` normaliza antes de compilar.
                    codigo = getattr(lr, "codigo_verificado", "") or ""
                    err = None
                except Exception as exc:                        # noqa: BLE001
                    veredicto, err = "", "%s: %s" % (type(exc).__name__, exc)
                seg = time.time() - t0
                filas.append({"consulta": q, "config": config,
                              "veredicto": str(veredicto), "seg": round(seg, 1),
                              "error": err, "gastado": round(gastado(), 4),
                              "nchars": len(codigo)})
                print("  [%2d/%2d] %-42s %-10s %5.1fs  $%.3f%s"
                      % (i, len(casos), q[:42], veredicto, seg, gastado(),
                         "  ERROR" if err else ""))
                if err and "credit balance" in err.lower():
                    print("\n  SALDO AGOTADO. Se para y se guarda lo que hay.")
                    break
        finally:
            restaurar()

    # SE ACUMULA, NO SE SOBRESCRIBE.
    #
    # Esto hacía `json.dump` a pelo, y como las ramas se corren en tandas
    # separadas —la de control se lanzó después, en su propia ejecución— la
    # segunda tanda BORRABA la primera. O sea que el fichero habría perdido
    # los 20 casos de `completo` que ya estaban pagados, y con ellos la mitad
    # de la comparación. Se conservan las filas de las configuraciones que
    # esta tanda NO ha tocado.
    previo = {}
    try:
        previo = json.load(io.open(SALIDA, encoding="utf-8"))
    except Exception:                                          # noqa: BLE001
        previo = {}
    viejas = [f for f in (previo.get("filas") or [])
              if f.get("config") not in configs]
    gasto_previo = float(previo.get("gastado") or 0.0)
    json.dump({"modelo": modelo, "tope": tope,
               "gastado": round(gasto_previo + gastado(), 4),
               "gastado_esta_tanda": round(gastado(), 4),
               "filas": viejas + filas},
              io.open(SALIDA, "w", encoding="utf-8"),
              indent=1, ensure_ascii=False)
    print("\n  GASTO REAL DE ESTA TANDA: $%.3f  (estimado $%.2f, tope $%.2f)"
          % (gastado(), coste, tope))
    print("\n-> %s" % SALIDA)
    print("   y las formalizaciones en data/grabaciones/formalizaciones.jsonl,")
    print("   desde donde `python -m scripts.replay` las repite gratis.")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--casos", type=int, default=len(CASOS))
    ap.add_argument("--configs", default=",".join(CONFIGS))
    ap.add_argument("--ejecutar", action="store_true",
                    help="gastar de verdad; sin esto sólo dice cuánto costaría")
    ap.add_argument("--tope", type=float, default=1.70,
                    help="tope duro en dólares; se para al pasarlo (def. 1.70)")
    ap.add_argument("--modelo", default=MODELO_POR_DEFECTO,
                    help="se FIJA en el Núcleo; el defecto del dataclass es "
                         "opus-5 y cuesta 2,5x (def. %s)" % MODELO_POR_DEFECTO)
    a = ap.parse_args()
    raise SystemExit(asyncio.run(
        main(a.casos, tuple(a.configs.split(",")), a.ejecutar, a.tope,
             a.modelo)))
