# -*- coding: utf-8 -*-
"""Si el modelo NO PUDIERA escribir un nombre inexistente, ¿cuánto ganaríamos?

LA PREGUNTA, Y POR QUE ES DISTINTA DE LAS DE ANTES
---------------------------------------------------
Hoy el grafo SUGIERE nombres de Mathlib en el prompt, y eso está medido:
23,9 % de precisión contra un nulo de 1,45 % — dieciséis veces mejor. Pero es
PUNTERÍA, no RESULTADO: que Lean verifique más no se ve (rescata 3, rompe 2,
p = 1,0). Una sugerencia es ignorable, y el modelo la ignora: ve `Irrational`
delante y aun así escribe `tsum_geometric_two`.

La alternativa que este guion evalúa es otra: **restringir la generación** con
el índice de 217 419 nombres, de forma que un identificador que no existe pase
de improbable a IMPOSIBLE. No es meter el grafo en el modelo — es meterlo
dentro del bucle de generación.

QUE SE PUEDE MEDIR SIN API, Y QUE NO
------------------------------------
No podemos decodificar con restricciones contra la API de Claude. Lo que sí
tenemos son 66 formalizaciones YA ESCRITAS por el modelo
(`data/grabaciones/formalizaciones.jsonl`), y con ellas se puede acotar el
TECHO de lo que la restricción podría comprar:

    de los identificadores que el modelo escribió y NO existen,
    ¿cuántos tienen un candidato válido al que un decodificador
    restringido habría caído?

Si casi ninguno lo tiene, restringir sólo cambiaría un nombre malo por otro
nombre malo pero válido, y la ganancia sería ilusoria. Si la mayoría son
cuasi-aciertos de un nombre real, el techo es alto y merece la pena pagar un
modelo local para el paso de formalización.

Esto es un TECHO, no un resultado. Lo dice el nombre del fichero a propósito.

EL MODELO NULO, QUE AQUI ES LA MITAD DEL EXPERIMENTO
----------------------------------------------------
Un decodificador restringido garantiza VALIDEZ, no CORRECCION. Así que el nulo
no es «no hacer nada»: es **sustituir el nombre inventado por un nombre válido
cualquiera**, concretamente uno de los lemas más citados de Mathlib. Si el
índice no bate a eso, lo que aporta la restricción es validez sintáctica y
nada más — y eso ya lo sabíamos sin medirlo.

    real   el candidato que el índice propone por parecido
    nulo   un nombre válido tomado por frecuencia, sin mirar el inventado

LA ALARMA, DECLARADA ANTES DE MIRAR
------------------------------------
  · si el índice no propone candidato para NINGUN inventado, no hay techo que
    medir y el resultado es «restringir no compra nada aquí»;
  · si propone para todos, sospechar: `parecidos` devuelve los k más cercanos
    SIEMPRE, aunque estén lejísimos. Por eso se exige una distancia mínima y
    se informa la distribución, no sólo el recuento;
  · y si el nulo iguala al índice, el índice no está aportando información,
    sólo validez.

No gasta API. El escalón 2 gasta tiempo de Lean, no dinero.

    python -m scripts.techo_de_la_restriccion
    python -m scripts.techo_de_la_restriccion --con-lean   # escalon 2
"""
from __future__ import annotations

import argparse
import collections
import difflib
import io
import json
import os
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

GRABACIONES = os.path.join(RAIZ, "data", "grabaciones", "formalizaciones.jsonl")
SALIDA = os.path.join(RAIZ, "data", "techo_de_la_restriccion.json")

#: Un identificador de Lean tal y como aparece en el codigo. Se piden al menos
#: cuatro caracteres: `h`, `n`, `hx` son hipotesis y variables ligadas, no
#: nombres de Mathlib, y contarlas inflaria el denominador con ruido.
_IDENT = re.compile(r"\b([A-Za-z_][A-Za-z0-9_']*(?:\.[A-Za-z_][A-Za-z0-9_']*)*)\b")

#: Palabras del lenguaje y de las tacticas: no son nombres de Mathlib y
#: preguntarle al indice por ellas solo produce falsos inventados.
_LENGUAJE = frozenset("""
theorem lemma example def abbrev instance structure class where by with at
import open namespace end section variable universe noncomputable private
protected partial mutual deriving extends if then else let fun do match
have show from suffices calc this sorry admit
intro intros apply exact refine rintro rcases obtain use exists cases induction
constructor ext simp simpa norm_num norm_cast push_cast ring ring_nf field_simp
linarith nlinarith positivity omega decide rfl trivial aesop tauto gcongr
unfold rw rwa subst specialize contrapose by_contra push_neg interval_cases
using generalizing only inferInstance trivial native_decide first done repeat
all_goals any_goals focus case next try skip assumption exfalso left right
Type Prop Sort True False Nat Int Real Rat Complex Bool List Set Finset Fin
And Or Not Iff Eq Ne forall exists le lt ge gt add mul sub div neg inv pow
""".split())

MIN_LARGO = 4
#: `difflib` devuelve SIEMPRE los k mas parecidos, aunque esten lejisimos. Sin
#: un corte, «candidato encontrado» significaria «el indice no esta vacio».
CORTE = 0.78


def _cargar():
    filas = []
    for linea in io.open(GRABACIONES, encoding="utf-8"):
        linea = linea.strip()
        if not linea:
            continue
        try:
            filas.append(json.loads(linea))
        except Exception:                                      # noqa: BLE001
            continue
    return filas


#: `theorem X`, `lemma X`, `def X`… X se esta DECLARANDO aqui. Preguntarle al
#: indice si existe en Mathlib y contar que no como «inventado» es contar el
#: acierto como fallo: el modelo no lo invento, lo definio.
_DECLARA = re.compile(
    r"^\s*(?:private\s+|protected\s+|noncomputable\s+)*"
    r"(?:theorem|lemma|def|abbrev|instance|structure|class|inductive)"
    r"\s+([A-Za-z_][A-Za-z0-9_'.]*)", re.M)


def sin_comentarios(codigo: str) -> str:
    """El codigo sin comentarios ni cadenas.

    LA PRIMERA VERSION DE ESTO NO LO HACIA, y el resultado fue un instrumento
    roto de manual: los «identificadores inventados» mas frecuentes eran
    `ambos`, `cualquier`, `entonces`, `monoide` — palabras CASTELLANAS de los
    comentarios que el modelo escribe en español. Con eso el 51 % de los
    identificadores salia inexistente, que es una cifra sobre la prosa y no
    sobre el codigo.
    """
    t = re.sub(r"/-[\s\S]*?-/", " ", codigo or "")
    t = re.sub(r"--[^\n]*", " ", t)
    t = re.sub(r'"[^"\n]*"', " ", t)
    return t


def identificadores(codigo: str) -> list:
    """Los identificadores candidatos a ser nombres de Mathlib.

    Se quitan, en este orden y cada uno por su motivo:
      · los comentarios y las cadenas — ahi hay prosa, no codigo;
      · los `import` — ahi los nombres son MODULOS, no declaraciones;
      · los nombres que el propio fichero DECLARA;
      · las palabras del lenguaje y de las tacticas.
    """
    limpio = sin_comentarios(codigo)
    declarados = set(_DECLARA.findall(limpio))
    cuerpo = "\n".join(l for l in limpio.split("\n")
                       if not l.lstrip().startswith("import "))
    fuera = set()
    for m in _IDENT.finditer(cuerpo):
        t = m.group(1)
        if len(t) < MIN_LARGO or t in declarados:
            continue
        if t in _LENGUAJE or (t.split(".")[0] in _LENGUAJE and "." not in t):
            continue
        fuera.add(t)
    return sorted(fuera)


def parece_local(nombre: str) -> bool:
    """`hirr`, `hmax`, `hl'` son hipótesis; no son nombres de Mathlib.

    LA TERCERA FUGA, cazada por la alarma de este mismo guion. Un nombre de
    Mathlib real es snake_case con al menos un `_`, o lleva `.`, o es
    CamelCase con mayúscula inicial. Una palabra suelta en minúscula sin
    separador es, por convención de Lean, una hipótesis o una variable ligada
    — y preguntarle al índice si existe sólo produce falsos inventados.

    Se acepta que esta regla es una CONVENCION, no una garantía: `deriv` y
    `card` son nombres reales que la cumplen. Por eso se cuentan aparte y se
    informan, en vez de tirarlos en silencio.
    """
    if "." in nombre or "_" in nombre:
        return False
    return nombre[:1].islower()


def es_notacion_de_punto(nombre: str, N) -> bool:
    """`hf.continuous` NO es un nombre inventado: es notación de punto.

    LA SEGUNDA FUGA DEL INSTRUMENTO, y ésta la comparte con producción. En
    Lean, si `hf : Continuous f`, escribir `hf.continuous` resuelve a
    `Continuous.continuous hf`. El nombre `hf.continuous` no está ni tiene que
    estar en el índice de Mathlib — pero el índice lo marca como desconocido,
    y `core.py` se lo enseña al alumno como «identificador que no aparece».

    La distinción es limpia y el índice ya la sabe: si lo que va antes del
    primer punto NO es un espacio de nombres conocido, es una variable local.

        hf.continuous      hf     no es namespace  ->  notación de punto
        Basis.exists_basis Basis  SI es namespace  ->  nombre de verdad
    """
    if "." not in nombre:
        return False
    try:
        return not N.existe_namespace(nombre.split(".")[0])
    except Exception:                                          # noqa: BLE001
        return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--con-lean", action="store_true",
                    help="escalon 2: recompila con el nombre sustituido")
    ap.add_argument("--corte", type=float, default=CORTE)
    args = ap.parse_args()

    from nucleo.lean import nombres as N
    if not N.disponible():
        print("el indice de nombres no esta disponible: no hay nada que medir")
        return 1

    filas = _cargar()
    print("%d formalizaciones grabadas\n" % len(filas))

    # ── el nulo: nombres validos por frecuencia, sin mirar el inventado ────
    #
    # Se toman del propio banco de lemas: los mas citados en pruebas reales.
    # Es lo que un decodificador restringido produce en el peor caso — algo
    # valido, elegido sin informacion sobre lo que el modelo queria decir.
    frecuentes = []
    banco = os.path.join(RAIZ, "data", "banco_lemas.jsonl")
    if os.path.exists(banco):
        cnt = collections.Counter()
        for i, linea in enumerate(io.open(banco, encoding="utf-8")):
            if i > 40000:
                break
            try:
                d = json.loads(linea)
            except Exception:                                  # noqa: BLE001
                continue
            for lem in (d.get("lemas") or d.get("premisas") or []):
                cnt[lem] += 1
        frecuentes = [k for k, _ in cnt.most_common(20)]
    print("nulo: los %d lemas mas citados (%s...)\n"
          % (len(frecuentes), ", ".join(frecuentes[:3]) or "sin banco"))

    total_id = inexistentes = punto_local = locales = 0
    ejemplos_punto, ejemplos_local = [], []
    con_candidato = nulo_acierta = 0
    distancias = []
    detalle = []
    por_caso = collections.Counter()

    for f in filas:
        ids = identificadores(f.get("codigo") or "")
        malos = []
        for t in ids:
            total_id += 1
            try:
                if N.existe(t):
                    continue
            except Exception:                                  # noqa: BLE001
                continue
            # LA NOTACION DE PUNTO NO ES UN NOMBRE INVENTADO. Se cuenta
            # aparte porque es una cifra util por si misma: es lo que
            # produccion le esta ensenando al alumno como «no existe».
            if es_notacion_de_punto(t, N):
                punto_local += 1
                ejemplos_punto.append(t)
                continue
            if parece_local(t):
                locales += 1
                ejemplos_local.append(t)
                continue
            inexistentes += 1
            malos.append(t)
            # el candidato del INDICE, con corte declarado
            cands = []
            try:
                cands = N.parecidos(t, k=5) or []
            except Exception:                                  # noqa: BLE001
                cands = []
            mejor, dist = "", 0.0
            for c in cands:
                nom = c if isinstance(c, str) else (c.get("nombre") if
                                                    isinstance(c, dict) else str(c))
                r = difflib.SequenceMatcher(None, t, nom).ratio()
                if r > dist:
                    mejor, dist = nom, r
            hay = dist >= args.corte
            con_candidato += 1 if hay else 0
            distancias.append(round(dist, 3))
            # el NULO: ¿acierta por casualidad el mas frecuente?
            nulo_acierta += 1 if (frecuentes and frecuentes[0] == mejor) else 0
            detalle.append({"consulta": (f.get("consulta") or "")[:70],
                            "inventado": t, "candidato": mejor if hay else "",
                            "distancia": round(dist, 3)})
        if malos:
            por_caso[len(malos)] += 1

    print("=== ESCALON 1 · EL TECHO ===\n")
    print("  identificadores escritos por el modelo   %5d" % total_id)
    print("  de esos, notacion de punto sobre local   %5d  (%.1f %%)"
          % (punto_local, 100.0 * punto_local / max(1, total_id)))
    print("     -> %s" % ", ".join(sorted(set(ejemplos_punto))[:6]))
    print("  de esos, hipotesis y variables locales   %5d  (%.1f %%)"
          % (locales, 100.0 * locales / max(1, total_id)))
    print("     -> %s" % ", ".join(sorted(set(ejemplos_local))[:6]))
    print("  de esos, NO existen en Mathlib           %5d  (%.1f %%)"
          % (inexistentes, 100.0 * inexistentes / max(1, total_id)))
    if not inexistentes:
        print("\n  NO HAY NADA QUE MEDIR: el modelo no escribio un solo nombre")
        print("  inexistente en estas 66 grabaciones. Restringir la generacion")
        print("  no puede comprar nada que no este ya comprado.")
    else:
        print("  con candidato del indice (>= %.2f)       %5d  (%.1f %%)"
              % (args.corte, con_candidato,
                 100.0 * con_candidato / inexistentes))
        print("  que el NULO por frecuencia acierta       %5d  (%.1f %%)"
              % (nulo_acierta, 100.0 * nulo_acierta / inexistentes))
        distancias.sort()
        if distancias:
            med = distancias[len(distancias) // 2]
            print("\n  distancia al mejor candidato: mediana %.3f · "
                  "min %.3f · max %.3f" % (med, distancias[0], distancias[-1]))
        print("\n  los primeros inventados, con su candidato:")
        for d in detalle[:12]:
            print("     %-34s -> %-34s %.2f"
                  % (d["inventado"][:34], d["candidato"][:34] or "(ninguno)",
                     d["distancia"]))

    # ── la alarma, declarada antes de mirar ───────────────────────────────
    print("\n=== LA ALARMA ===\n")
    avisos = []
    if inexistentes and con_candidato == 0:
        avisos.append("el indice no propone candidato para NINGUN inventado: "
                      "restringir no compra nada en este corpus")
    if inexistentes and con_candidato == inexistentes:
        avisos.append("propone para TODOS: sospechar del corte, `parecidos` "
                      "devuelve siempre los k mas cercanos")
    if inexistentes and nulo_acierta >= con_candidato:
        avisos.append("el NULO por frecuencia iguala o bate al indice: lo que "
                      "aporta la restriccion es validez, no informacion")
    # LA FUGA DE PROSA, QUE YA PASO UNA VEZ. Un nombre de Mathlib casi siempre
    # lleva `_` o `.`; una palabra suelta en minusculas y sin ninguno de los
    # dos es casi seguro castellano de un comentario. Esta alarma no existia
    # en la primera version, y por eso el instrumento midio la prosa.
    sueltas = [d["inventado"] for d in detalle
               if "_" not in d["inventado"] and "." not in d["inventado"]
               and d["inventado"].islower()]
    if inexistentes and len(sueltas) > 0.25 * inexistentes:
        avisos.append("el %.0f %% de los inventados son palabras sueltas en "
                      "minuscula sin `_` ni `.` (%s...): se esta colando prosa "
                      "de los comentarios, el extractor esta roto"
                      % (100.0 * len(sueltas) / inexistentes,
                         ", ".join(sueltas[:4])))
    if total_id and inexistentes / total_id < 0.02:
        avisos.append("menos del 2 %% de los identificadores son inventados: "
                      "el fallo que esto ataca casi no aparece en el corpus "
                      "grabado, asi que el techo es bajo por prevalencia "
                      "aunque fuera alto por precision")
    print("  " + ("\n  ".join("· " + a for a in avisos) if avisos
                  else "ninguna salta"))

    # ── ESCALON 2 · ¿ES PUNTERIA O ES RESULTADO? ──────────────────────────
    #
    # Que el indice sepa nombrar el candidato NO demuestra que Lean elabore.
    # Es la misma distincion que hundio al vocabulario del prompt: 16,5x de
    # punteria y p = 1,0 de resultado. Aqui se compila antes y despues.
    escalon2 = {}
    if args.con_lean and detalle:
        import subprocess
        import time
        sust = {d["inventado"]: d["candidato"] for d in detalle if d["candidato"]}
        print("\n=== ESCALON 2 · CON LEAN DE JUEZ ===\n")
        print("  %d sustituciones distintas" % len(sust))
        afectadas = [f for f in filas
                     if any(k in (f.get("codigo") or "") for k in sust)]
        print("  %d grabaciones afectadas · %d compilados\n"
              % (len(afectadas), 2 * len(afectadas)))
        ruta = os.path.join(RAIZ, "_techo.lean")

        def compila(codigo):
            io.open(ruta, "w", encoding="utf-8").write(codigo)
            t0 = time.time()
            try:
                p = subprocess.run(["lake", "env", "lean", ruta], cwd=RAIZ,
                                   capture_output=True, text=True, timeout=120,
                                   encoding="utf-8", errors="replace")
                sal = (p.stdout or "") + (p.stderr or "")
                ok = p.returncode == 0 or ("declaration uses 'sorry'" in sal
                                           and "error:" not in sal)
            except Exception:                                  # noqa: BLE001
                ok, sal = False, "TIMEOUT"
            return ok, round(time.time() - t0, 1), sal[:200]

        rescata = rompe = igual = 0
        for f in afectadas:
            cod = f.get("codigo") or ""
            nuevo = cod
            for k, v in sust.items():
                nuevo = nuevo.replace(k, v)
            a, sa, _ = compila(cod)
            b, sb, err = compila(nuevo)
            marca = ("RESCATA" if (b and not a) else
                     "ROMPE" if (a and not b) else "igual")
            rescata += 1 if (b and not a) else 0
            rompe += 1 if (a and not b) else 0
            igual += 1 if a == b else 0
            print("  %-46s antes=%-3s despues=%-3s %s"
                  % ((f.get("consulta") or "")[:46],
                     "OK" if a else "--", "OK" if b else "--", marca))
        try:
            os.remove(ruta)
        except OSError:
            pass
        escalon2 = {"afectadas": len(afectadas), "rescata": rescata,
                    "rompe": rompe, "igual": igual}
        print("\n  rescata %d · rompe %d · igual %d" % (rescata, rompe, igual))
        if rescata == 0:
            print("\n  PUNTERIA SIN RESULTADO, otra vez: el indice nombra el")
            print("  candidato correcto y Lean sigue sin elaborar. El nombre")
            print("  no era lo unico que estaba mal.")

    json.dump({"escalon2": escalon2,
               "grabaciones": len(filas), "identificadores": total_id,
               "inexistentes": inexistentes, "con_candidato": con_candidato,
               "nulo_acierta": nulo_acierta, "corte": args.corte,
               "distancias": distancias, "detalle": detalle[:200],
               "avisos": avisos},
              io.open(SALIDA, "w", encoding="utf-8"), ensure_ascii=False,
              indent=1)
    print("\n-> %s" % SALIDA)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
