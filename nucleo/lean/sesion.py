# -*- coding: utf-8 -*-
"""Una sesión de Lean que se queda viva entre tácticas.

POR QUE
-------
`LeanClient.check_code` lanza `lake env lean fichero --json` en cada llamada, y
lo medido es ~15,5 s por compilación con el coste en arrancar Lean y elaborar
la cabecera, no en la táctica. Eso hace que **un paso cueste lo mismo que una
prueba entera**, y con ello un lazo por pasos es inviable: veinte pasos son
cinco minutos antes de pensar en el modelo.

Con el entorno cargado una vez, medido en esta máquina con este toolchain:

    `import Mathlib`, una vez            119,1 s
    un teorema con `sorry` sobre él        0,1 s
    `nlinarith [sq_nonneg (a-b)]`          0,63 s   (cierra)
    `linarith`                             0,02 s   (falla)
    `ring_nf`                              0,11 s   (progresa)

La cifra que importa es la última columna de las tres: **una táctica que FALLA
cuesta 0,02 s en vez de 15,5**. Explorar deja de ser caro, que es la condición
de que exista un lazo por pasos.

QUE ESTE MODULO NO HACE, Y ES DELIBERADO
-----------------------------------------
**No certifica.** El veredicto sigue saliendo de `LeanClient.check_code` sobre
la prueba ensamblada, como hoy. Esta sesión BUSCA; el fichero DECIDE. No es
desconfianza abstracta: el REPL tiene registrado un caso en que aceptó pruebas
incorrectas (leanprover-community/repl, issue 44). Un buscador que se equivoca
cuesta un camino perdido; un certificador que se equivoca cuesta un sello de
«verificado» sobre algo falso, que es lo único que este sistema no puede
permitirse.

EL PROTOCOLO
------------
JSON por stdin, JSON por stdout, y una línea en blanco cierra cada mensaje.

    {"cmd": "import Mathlib"}                   -> {"env": 1}
    {"cmd": "theorem t : P := by sorry",
     "env": 1}                                  -> {"sorries": [{"proofState": 0,
                                                    "goal": "⊢ P"}], "env": 2}
    {"tactic": "nlinarith", "proofState": 0}    -> {"proofState": 1, "goals": []}

`goals == []` es el objeto terminal de la categoría de estados: no quedan
objetivos. Ver `nucleo/graph/estados.py`.

WINDOWS
-------
Nada de `asyncio`: este repositorio ya tiene documentado que `asyncio.run()`
cierra el ProactorEventLoop y deja procesos de Lean huérfanos. Se usa
`subprocess` con un hilo lector y tiempo límite, y al cerrar se mata el árbol
de procesos con el mismo mecanismo que `lean/client.py`.
"""
from __future__ import annotations

import json
import logging
import os
import subprocess
import threading
import time
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

#: donde `scripts/construir_repl.py` deja el binario. Se puede cambiar con
#: METAMAT_REPL, que es lo que usan los bancos para probar otra version.
def _ruta_repl() -> str:
    de_entorno = os.environ.get("METAMAT_REPL", "").strip()
    if de_entorno:
        return de_entorno
    from nucleo.rutas import RAIZ
    return str(RAIZ / ".lake" / "repl" / ".lake" / "build" / "bin" / "repl.exe")


#: `import Mathlib` entero. Caro una vez y gratis siempre despues.
CABECERA_AMPLIA = ["Mathlib"]

#: cuanto se espera a una respuesta, por clase de peticion. El `cmd` puede ser
#: `import Mathlib`; una tactica no deberia pasar de unos segundos.
TOPE_CMD = 1800
TOPE_TACTICA = 120

#: «no me has dicho nada», que NO es lo mismo que «sin entorno». Ver `comando`.
GUARDADO = object()


@dataclass
class Respuesta:
    """Lo que la sesión devolvió, ya clasificado.

    `clase` es lo que el mediador necesita para decidir, y sale del contenido
    de la respuesta, no de buscar subcadenas en un mensaje de error — el mismo
    criterio que `LeanResult.error_kinds` documenta en `lean/client.py`.
    """
    clase: str                       # cierra · progresa · error · vacia
    proof_state: Optional[int] = None
    objetivos: list = field(default_factory=list)
    mensajes: list = field(default_factory=list)
    env: Optional[int] = None
    sorries: list = field(default_factory=list)
    segundos: float = 0.0
    crudo: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return self.clase in ("cierra", "progresa")

    @property
    def error(self) -> str:
        for m in self.mensajes:
            if (m or {}).get("severity") == "error":
                return str(m.get("data") or "")[:400]
        return ""


def _clasificar(d: dict) -> str:
    """En qué clase cae una respuesta del REPL.

    EL ORDEN IMPORTA y no es arbitrario. Un `sorry` en la respuesta significa
    que el comando elaboró y abrió objetivos, aunque traiga avisos; un error de
    verdad manda sobre todo lo demás; y `goals == []` sólo es cierre si no hubo
    error, porque una táctica puede vaciar los objetivos y dejar un error de
    elaboración detrás.
    """
    # EL REPL TIENE DOS CANALES DE ERROR, y el segundo no está en `messages`.
    # Una táctica que falla, un proofState o un entorno que no existen,
    # vuelven como `{"message": "Lean error: …"}` en el primer nivel, sin
    # `messages`, `goals` ni `env`. Sin esta línea caían en `vacia`, y el banco
    # de concordancia del paso 1 contaba como ACEPTADO todo lo que no fuera
    # `error`. No se coló ningún caso —ninguna de sus 20 filas es `vacia`—,
    # pero la trampa solo podía inflar lo aceptado, que es la dirección que
    # este módulo no se puede permitir. Visto en la sonda del paso 2.
    if isinstance(d.get("message"), str) and "proofState" not in d \
            and "env" not in d:
        return "error"
    if any((m or {}).get("severity") == "error" for m in d.get("messages") or []):
        return "error"
    g = d.get("goals")
    if g == []:
        return "cierra"
    if g:
        return "progresa"
    if d.get("sorries") or d.get("env") is not None:
        return "progresa"
    return "vacia"


class SesionLean:
    """Un proceso `repl` vivo, con su entorno cargado.

    Uso:
        with SesionLean() as s:
            env = s.cabecera(["Mathlib"])
            r = s.comando("theorem t : ... := by sorry", env)
            r2 = s.tactica("nlinarith", r.sorries[0]["proofState"])
    """

    def __init__(self, raiz: Optional[str] = None, repl: Optional[str] = None):
        from nucleo.rutas import RAIZ
        self.raiz = str(raiz or RAIZ)
        self.repl = repl or _ruta_repl()
        self.p: Optional[subprocess.Popen] = None
        self.env: Optional[int] = None
        #: para el banco: cuanto ha costado la sesion, en llamadas y segundos
        self.llamadas = 0
        self.segundos = 0.0

    # ── ciclo de vida ────────────────────────────────────────────────────
    def abrir(self) -> "SesionLean":
        if not os.path.exists(self.repl):
            raise FileNotFoundError(
                "no existe el REPL en %s. Constrúyelo con "
                "`python -m scripts.construir_repl`" % self.repl)
        self.p = subprocess.Popen(
            ["lake", "env", self.repl], cwd=self.raiz,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, text=True, encoding="utf-8",
            errors="replace", bufsize=1)
        return self

    def cerrar(self) -> None:
        """Mata el árbol, no sólo el proceso.

        `lake env repl` arranca `repl.exe` como HIJO, así que matar a `lake`
        deja el REPL vivo con Mathlib entero en memoria. Es el mismo fallo que
        `lean/client.py` ya documenta con `_kill_process_tree`.
        """
        if not self.p:
            return
        pid = self.p.pid
        try:
            # es un @staticmethod de LeanClient, no una funcion de modulo:
            # importarla suelta falla y el arbol se queda vivo en silencio.
            from nucleo.lean.client import LeanClient
            LeanClient._kill_process_tree(pid)
        except Exception:                                      # noqa: BLE001
            logger.debug("no se pudo matar el arbol de %s", pid, exc_info=True)
        try:
            self.p.kill()
        except Exception:                                      # noqa: BLE001
            pass
        self.p = None

    def __enter__(self):
        return self.abrir()

    def __exit__(self, *_):
        self.cerrar()

    @property
    def viva(self) -> bool:
        return self.p is not None and self.p.poll() is None

    # ── el protocolo ─────────────────────────────────────────────────────
    def _pide(self, obj: dict, tope: int) -> Respuesta:
        if not self.viva:
            raise RuntimeError("la sesión no está abierta")
        t0 = time.time()
        try:
            self.p.stdin.write(json.dumps(obj) + "\n\n")
            self.p.stdin.flush()
        except Exception as e:                                 # noqa: BLE001
            return Respuesta(clase="error", segundos=time.time() - t0,
                             mensajes=[{"severity": "error",
                                        "data": "stdin: %s" % e}])
        lineas: list = []

        def leer():
            #: el REPL cierra cada mensaje con una linea en blanco. Se ignoran
            #: las blancas de ANTES por si quedo una del mensaje anterior.
            for linea in self.p.stdout:
                if linea.strip() == "":
                    if lineas:
                        break
                    continue
                lineas.append(linea)

        h = threading.Thread(target=leer, daemon=True)
        h.start()
        h.join(tope)
        seg = time.time() - t0
        self.llamadas += 1
        self.segundos += seg
        if not lineas:
            # NO SE MATA LA SESION POR UN TIMEOUT. El hilo lector sigue vivo y
            # puede cerrar el mensaje despues; lo que no se puede es seguir
            # mandando, asi que el mediador debe tratar `agotada` como final.
            return Respuesta(clase="error", segundos=seg,
                             mensajes=[{"severity": "error",
                                        "data": "TIMEOUT tras %.0f s" % seg}])
        try:
            d = json.loads("".join(lineas))
        except Exception:                                      # noqa: BLE001
            return Respuesta(clase="error", segundos=seg,
                             mensajes=[{"severity": "error",
                                        "data": "respuesta no es JSON"}],
                             crudo={"texto": "".join(lineas)[:400]})
        mensajes = list(d.get("messages") or [])
        if isinstance(d.get("message"), str):
            # el canal de primer nivel, para que `.error` lo enseñe
            mensajes.append({"severity": "error", "data": d["message"]})
        return Respuesta(
            clase=_clasificar(d), proof_state=d.get("proofState"),
            objetivos=d.get("goals") or [], mensajes=mensajes,
            env=d.get("env"), sorries=d.get("sorries") or [],
            segundos=seg, crudo=d)

    # ── lo que el mediador usa ───────────────────────────────────────────
    def cabecera(self, modulos: Optional[list] = None) -> Optional[int]:
        """Carga los imports una vez y devuelve el id del entorno."""
        mods = list(modulos or CABECERA_AMPLIA)
        texto = "\n".join("import " + m for m in mods)
        r = self._pide({"cmd": texto}, TOPE_CMD)
        self.env = r.env
        logger.info("Lean: cabecera de %d modulo(s) en %.1f s -> env=%s",
                    len(mods), r.segundos, r.env)
        return r.env

    def comando(self, codigo: str, env=GUARDADO) -> Respuesta:
        """Elabora un comando —un teorema con `sorry`, típicamente.

        `env` distingue TRES cosas, y la distinción no es cosmética:

            comando(cod)             el entorno de `cabecera()`, si lo hay
            comando(cod, env=None)   NINGUNO: que elabore sus propios imports
            comando(cod, env=7)      ese

        Sin el centinela, `env=None` caía al entorno guardado. Eso rompería en
        silencio a `scripts/sesion_contra_fichero.py`, que pide entorno nuevo
        por caso justamente para que la sesión vea LA MISMA biblioteca que el
        fichero: con Mathlib entero cargado de antes, la sesión aceptaría cosas
        que el fichero no puede, y el desacuerdo medido sería de la cabecera y
        no del motor. Hoy sobrevive sólo porque ese guion nunca llama a
        `cabecera()`; eso es suerte, no diseño.
        """
        pet = {"cmd": codigo}
        e = self.env if env is GUARDADO else env
        if e is not None:
            pet["env"] = e
        return self._pide(pet, TOPE_CMD)

    def tactica(self, tactica: str, proof_state: int,
                tope: int = TOPE_TACTICA) -> Respuesta:
        """Aplica una táctica a un estado. Es la flecha de la categoría E."""
        return self._pide({"tactic": tactica, "proofState": proof_state}, tope)
