"""
Cliente Lean 4
==============

Cliente bidireccional para comunicacion con Lean 4.
Utiliza el REPL de Lake para enviar comandos y recibir feedback.

Flujo:
    Usuario -> LLM -> Nucleo -> LeanClient -> Lean 4
                                    |
                              LeanResult
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import tempfile
import urllib.request
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)


class LeanResultStatus(Enum):
    """Estado del resultado de Lean."""
    SUCCESS = auto()        # Prueba completada
    ERROR = auto()          # Error de compilacion/tipo
    TIMEOUT = auto()        # Timeout excedido
    INCOMPLETE = auto()     # Prueba incompleta (goals pendientes)
    SORRY = auto()          # Contiene sorry
    NOT_AVAILABLE = auto()  # lake/lean no instalado en este entorno


@dataclass
class LeanGoal:
    """Un goal de Lean pendiente de resolver."""
    index: int
    hypothesis: list[str]
    target: str

    def __str__(self) -> str:
        hyps = "\n".join(f"  {h}" for h in self.hypothesis)
        return f"Goal {self.index}:\n{hyps}\n⊢ {self.target}"


@dataclass
class LeanResult:
    """
    Resultado de ejecutar codigo Lean.

    Attributes:
        status: Estado del resultado
        goals: Lista de goals pendientes (si hay)
        messages: Mensajes de Lean (errores, warnings, info)
        output: Output completo de Lean
        elapsed_ms: Tiempo de ejecucion en ms
    """
    status: LeanResultStatus
    goals: list[LeanGoal] = field(default_factory=list)
    messages: list[dict[str, Any]] = field(default_factory=list)
    output: str = ""
    elapsed_ms: float = 0.0

    @property
    def is_success(self) -> bool:
        return self.status == LeanResultStatus.SUCCESS

    @property
    def has_errors(self) -> bool:
        return any(m.get("severity") == "error" for m in self.messages)

    @property
    def error_messages(self) -> list[str]:
        # Lean emite el texto en "data"; "message" es de otros formatos. Leer
        # solo "message" devolvia [''] siempre, lo que dejaba ciego todo el
        # diagnostico de errores (incluidos los _LEAN_HINTS del nucleo).
        return [
            (m.get("data") or m.get("message") or "")
            for m in self.messages
            if m.get("severity") == "error"
        ]

    def get_first_error(self) -> Optional[str]:
        errors = self.error_messages
        return errors[0] if errors else None

    # Backwards-compat aliases used across codebase
    @property
    def success(self) -> bool:
        return self.is_success

    @property
    def errors(self) -> list[str]:
        return self.error_messages

    @property
    def error_message(self) -> Optional[str]:
        return self.get_first_error()


class LeanClient:
    """
    Cliente para comunicacion bidireccional con Lean 4.

    Metodos principales:
    - check_code: Verificar codigo Lean
    - check_theorem: Verificar un teorema
    - get_goal_state: Obtener estado de goals
    - apply_tactic: Aplicar una tactica

    Example:
        client = LeanClient(project_path="./")
        result = await client.check_theorem(
            name="my_theorem",
            statement="∀ n : Nat, n + 0 = n",
            proof="intro n; rfl"
        )
        if result.is_success:
            print("Prueba verificada!")
    """

    def __init__(
        self,
        project_path: Optional[Path | str] = None,
        lean_path: str = "lake",
        timeout_ms: int = 360000,
    ):
        """
        Inicializar cliente Lean.

        Args:
            project_path: Ruta al proyecto Lean (con lakefile.toml)
            lean_path: Ruta al ejecutable lake
            timeout_ms: Timeout en milisegundos
        """
        self.project_path = Path(project_path) if project_path else Path.cwd()
        self.lean_path = self._resolve_lake(lean_path)
        self.timeout_s = timeout_ms / 1000.0

    @staticmethod
    def _resolve_lake(lean_path: str) -> str:
        """Resolver ruta real de lake: PATH → elan default → argumento original."""
        import shutil
        if Path(lean_path).is_absolute() and Path(lean_path).exists():
            return lean_path
        found = shutil.which(lean_path)
        if found:
            return found
        candidates = [
            Path.home() / ".elan" / "bin" / "lake",
            Path.home() / ".elan" / "bin" / "lake.exe",
            Path("/usr/local/bin/lake"),
        ]
        for c in candidates:
            if c.exists():
                logger.info(f"lake encontrado en: {c}")
                return str(c)
        logger.warning(f"lake no encontrado — usando '{lean_path}' (puede fallar)")
        return lean_path

    # Header mínimo garantizado para tácticas y tipos básicos
    _SAFE_HEADER = (
        "import Mathlib.Tactic.Ring\n"
        "import Mathlib.Tactic.Linarith\n"
        "import Mathlib.Tactic.NormNum\n"
        "import Mathlib.Tactic.Positivity\n"
        "import Mathlib.Algebra.Order.Field.Basic\n"
        "import Mathlib.Data.Real.Basic\n"
    )

    # Imports adicionales disparados por palabras clave en el código
    _TOPIC_IMPORTS: list[tuple[list[str], str]] = [
        # Producto interno / normas
        (["inner", "⟪", "InnerProductSpace", "norm_sq", "inner_self"],
         "import Mathlib.Analysis.InnerProductSpace.Basic"),
        (["inner", "⟪", "InnerProductSpace"],
         "import Mathlib.Analysis.InnerProductSpace.PiL2"),
        # Análisis real / complejo
        (["Continuous", "continuous", "IsOpen", "isClosed", "Filter"],
         "import Mathlib.Topology.Basic"),
        (["deriv", "HasDerivAt", "differentiable"],
         "import Mathlib.Analysis.Calculus.Deriv.Basic"),
        (["integral", "MeasureTheory", "∫"],
         "import Mathlib.MeasureTheory.Integral.IntervalIntegral"),
        # Álgebra lineal. Determinant se movio a un subdirectorio: el modulo
        # antiguo no existe, y al inyectarlo Lean abortaba con "object file
        # ... does not exist" antes de mirar el teorema.
        (["LinearMap", "Matrix", "det", "eigenvalue"],
         "import Mathlib.LinearAlgebra.Matrix.Determinant.Basic"),
        (["trace", "Matrix.trace"],
         "import Mathlib.LinearAlgebra.Matrix.Trace"),
        # Números
        (["Nat.Prime", "prime", "Finset.sum"],
         "import Mathlib.Data.Nat.Prime.Basic"),
        # Factorizacion en primos: aqui viven primeFactorsList y sus lemas
        (["primeFactorsList", "factors", "factorization"],
         "import Mathlib.Data.Nat.Factors"),
        (["Complex", "re ", "im ", "Complex.abs"],
         "import Mathlib.Analysis.SpecialFunctions.Complex.Circle"),
        # Teorema fundamental del algebra: aqui vive Complex.exists_root, y
        # tambien la instancia IsAlgClosed de C. Sin este import, al sustituir
        # `import Mathlib` por el header estrecho el lema quedaba inaccesible.
        (["exists_root", "IsRoot", "IsAlgClosed", "ℂ[X]", "raiz", "root"],
         "import Mathlib.Analysis.Complex.Polynomial.Basic"),
        # Grupos / anillos abstractos
        (["Group", "Subgroup", "QuotientGroup"],
         "import Mathlib.GroupTheory.QuotientGroup.Basic"),
        (["Polynomial", "polynomial"],
         "import Mathlib.RingTheory.Polynomial.Basic"),
    ]

    # Nombres de lemas obsoletos → reemplazo actual en Mathlib 4
    _DEPRECATED_LEMMAS: list[tuple[str, str]] = [
        ("inner_self_eq_norm_sq_to_K",   "real_inner_self_eq_norm_sq"),
        ("inner_self_eq_norm_mul_norm",   "real_inner_self_eq_norm_sq"),
        ("sq_abs",                         "sq_abs"),          # sigue igual, forzar import
        ("norm_sq_eq_inner",               "real_inner_self_eq_norm_sq"),
        ("abs_sq",                         "sq_abs"),
        ("real_inner_comm",                "inner_comm"),
        ("inner_add_left",                 "inner_add_left"),
        ("inner_smul_left",                "inner_smul_left"),
        ("norm_add_sq_real",               "norm_add_sq_real"),
        ("norm_sub_sq_real",               "norm_sub_sq_real"),
        # Tácticas renombradas
        ("ring_nf;",                       "ring_nf\n  "),
        ("nlinarith [sq_nonneg",           "nlinarith [sq_nonneg"),
        # Factorizacion en primos: `Nat.factors` ya no existe en Mathlib
        # (verificado en Mathlib/Data/Nat/Factors.lean de este proyecto).
        # El orden importa: la sustitucion es textual y secuencial, asi que
        # los nombres largos van antes que los cortos.
        ("Nat.prime_of_mem_factors",       "Nat.prime_of_mem_primeFactorsList"),
        ("Nat.prod_factors",               "Nat.prod_primeFactorsList"),
        ("Nat.factors_unique",             "Nat.primeFactorsList_unique"),
        ("Nat.factors",                    "Nat.primeFactorsList"),
        # Notacion de proyeccion (`n.factors`). Va la ultima: para entonces
        # los nombres cualificados ya son `primeFactorsList` y no reaparecen.
        # Riesgo acotado: `.factorization` y `.primeFactorsList` no contienen
        # `.factors`, asi que no se corrompen.
        (".factors",                       ".primeFactorsList"),
    ]

    def _mathlib_src_root(self) -> Optional[Path]:
        """Raiz de las fuentes de Mathlib, o None si no esta disponible."""
        if not hasattr(self, "_ml_root_cache"):
            root = self.project_path / ".lake" / "packages" / "mathlib"
            self._ml_root_cache = root if (root / "Mathlib").is_dir() else None
        return self._ml_root_cache

    def _is_unknown_mathlib_import(self, line: str) -> bool:
        """True si la linea importa un modulo `Mathlib.*` que no existe.

        Se valida contra el arbol de fuentes: `Mathlib.Data.Nat.Factors`
        corresponde a `Mathlib/Data/Nat/Factors.lean`. Solo se juzgan los
        imports de Mathlib; `Init`, `Std`, `Batteries` y demas se respetan.
        Si Mathlib no esta instalado (despliegue en la nube) no se descarta
        nada, para no romper entornos donde no se puede comprobar.
        """
        s = line.strip()
        if not s.startswith("import Mathlib"):
            return False
        root = self._mathlib_src_root()
        if root is None:
            return False
        module = s[len("import "):].strip()
        if not module or module == "Mathlib":
            return False
        rel = Path(*module.split("."))
        return not (root / rel.with_suffix(".lean")).is_file()

    # ── Reparacion de imports a partir del error de Lean ───────────────────
    #
    # Un LLM escribiendo Lean falla una y otra vez por lo mismo: usa un lema
    # que existe pero no importa su modulo. En vez de mantener a mano una
    # tabla de parches por area, se busca la declaracion en las fuentes de
    # Mathlib y se deduce el modulo. Medido: 2,2 s de escaneo frente a los
    # ~15 s que cuesta una ejecucion de Lean, asi que reintentar sale a cuenta.

    # Lean nombra un identificador ausente de varias formas segun el contexto
    # en que aparezca. Con solo "unknown identifier" se escapaban los casos en
    # que el nombre se usa como tipo o como funcion.
    _RE_UNKNOWN = [
        re.compile(r"unknown (?:identifier|constant)\s+'([^']+)'", re.I),
        re.compile(r"unknown (?:identifier|constant)\s+([A-Za-z_][\w.']*)", re.I),
        re.compile(r"Function expected at\s*\n\s*([A-Za-z_][\w.']*)"),
        re.compile(r"unknown namespace\s+'?([A-Za-z_][\w.']*)'?", re.I),
    ]
    _RE_DECL = re.compile(
        r"^\s*(?:@\[[^\]]*\]\s*)?"
        r"(?:private\s+|protected\s+|noncomputable\s+|nonrec\s+)*"
        r"(?:theorem|lemma|def|abbrev|structure|class|instance|opaque)\s+"
        r"([A-Za-z_][A-Za-z0-9_'!?.]*)"
    )
    _RE_NS = re.compile(r"^namespace\s+([A-Za-z_][A-Za-z0-9_'.]*)")

    def _mathlib_lean_files(self) -> list[Path]:
        """Lista cacheada de fuentes .lean de Mathlib."""
        if getattr(self, "_ml_files_cache", None) is None:
            root = self._mathlib_src_root()
            self._ml_files_cache = (
                sorted((root / "Mathlib").rglob("*.lean")) if root else []
            )
        return self._ml_files_cache

    def find_modules_for_identifiers(
        self, cualificados: list[str]
    ) -> dict[str, str]:
        """Localiza varios identificadores en UNA sola pasada por las fuentes.

        Escanear Mathlib cuesta ~2 s; hacerlo una vez por identificador seria
        lineal en el numero de errores. Se resuelven todos a la vez.

        Se prefiere el candidato cuyo `namespace` coincide con el prefijo del
        identificador (`Complex.exists_root` -> namespace `Complex`); si
        ninguno coincide, se devuelve el primero hallado.
        """
        ficheros = self._mathlib_lean_files()
        if not ficheros or not cualificados:
            return {}

        # base -> lista de identificadores cualificados que la piden
        por_base: dict[str, list[str]] = {}
        for q in cualificados:
            por_base.setdefault(q.split(".")[-1], []).append(q)

        # base -> [(namespace, modulo)]
        hallados: dict[str, list[tuple[str, str]]] = {b: [] for b in por_base}
        raiz = self._mathlib_src_root()

        for f in ficheros:
            try:
                texto = f.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            bases_aqui = [b for b in por_base if b in texto]
            if not bases_aqui:
                continue                          # descarte rapido
            pila: list[str] = []
            for linea in texto.splitlines():
                m_ns = self._RE_NS.match(linea)
                if m_ns:
                    pila.append(m_ns.group(1))
                    continue
                if linea.startswith("end "):
                    if pila:
                        pila.pop()
                    continue
                m = self._RE_DECL.match(linea)
                if m and m.group(1) in bases_aqui:
                    modulo = ".".join(
                        f.with_suffix("").relative_to(raiz).parts
                    )
                    hallados[m.group(1)].append((".".join(pila), modulo))

        resultado: dict[str, str] = {}
        for base, quals in por_base.items():
            candidatos = hallados.get(base) or []
            if not candidatos:
                continue
            for q in quals:
                *prefijo, _ = q.split(".")
                ns_buscado = ".".join(prefijo)
                elegido = None
                if ns_buscado:
                    elegido = next(
                        (mod for ns, mod in candidatos if ns == ns_buscado), None
                    )
                resultado[q] = elegido or candidatos[0][1]
        return resultado

    def find_module_for_identifier(self, qualified: str) -> Optional[str]:
        """Modulo de Mathlib que declara `qualified`, o None."""
        return self.find_modules_for_identifiers([qualified]).get(qualified)

    def repair_imports(self, code: str, errores: list[str]) -> Optional[str]:
        """Añade los imports que faltan segun los errores de Lean.

        Devuelve el codigo con los imports nuevos, o None si no hay nada que
        reparar (ni identificadores desconocidos, ni modulo localizable).
        """
        desconocidos: list[str] = []
        for err in errores:
            for patron in self._RE_UNKNOWN:
                for m in patron.finditer(err or ""):
                    ident = m.group(1).strip(" '\"")
                    # Los nombres muy cortos son casi siempre variables de los
                    # propios mensajes de Lean ("where C is a constant"), y
                    # arrastran imports irrelevantes que solo cuestan tiempo
                    # de compilacion.
                    if len(ident.split(".")[-1]) < 3:
                        continue
                    if ident and ident not in desconocidos:
                        desconocidos.append(ident)
        if not desconocidos:
            return None

        ya = {l.strip() for l in code.splitlines() if l.strip().startswith("import")}
        nuevos: list[str] = []
        # cota: no perseguir 40 errores en cascada, y una sola pasada por las
        # fuentes para todos los candidatos
        modulos = self.find_modules_for_identifiers(desconocidos[:8])
        for ident in desconocidos[:8]:
            modulo = modulos.get(ident)
            if not modulo:
                logger.debug(f"Lean: sin modulo para '{ident}'")
                continue
            linea = f"import {modulo}"
            if linea not in ya and linea not in nuevos:
                nuevos.append(linea)
                logger.info(f"Lean: reparando '{ident}' con '{linea}'")

        if not nuevos:
            return None

        lineas = code.splitlines()
        insert_at = 0
        for i, l in enumerate(lineas):
            s = l.strip()
            if s.startswith("import") or s == "":
                insert_at = i + 1
            else:
                break
        return "\n".join(lineas[:insert_at] + nuevos + lineas[insert_at:])

    def _normalize_code(self, code: str) -> str:
        """
        Normaliza el código Lean antes de verificarlo:
        1. Sustituye `import Mathlib` completo por imports estrechos.
        2. Añade el header mínimo seguro (ring, linarith, etc.).
        3. Detecta el tema del código y añade imports específicos.
        4. Reemplaza nombres de lemas obsoletos por los actuales.
        """
        lines = code.lstrip().splitlines()

        # `import Mathlib` a secas carga los ~1.58 GB de .olean: 742 s medidos,
        # muy por encima del timeout de 360 s, asi que SIEMPRE expiraba. Se
        # descarta esa linea y se deja que el header estrecho la sustituya
        # (~11 s). Si la prueba necesitaba un modulo fuera del header, Lean
        # dara "unknown identifier" en segundos — un error diagnosticable por
        # la cascada de solvers es mejor que un timeout seguro sin resultado.
        if any(l.strip() == "import Mathlib" for l in lines):
            lines = [l for l in lines if l.strip() != "import Mathlib"]
            code = "\n".join(lines)

        # Descartar imports de Mathlib que no existen. El LLM los inventa con
        # frecuencia (p.ej. `Mathlib.GroupTheory.QuotientGroup`, cuando el
        # modulo real es `...QuotientGroup.Basic`) y un modulo inexistente
        # aborta la compilacion entera antes de mirar el teorema. Al quitarlo,
        # los imports tematicos de abajo suelen aportar el modulo correcto.
        dropped = [l for l in lines if self._is_unknown_mathlib_import(l)]
        if dropped:
            for l in dropped:
                logger.debug(f"Lean: descartado import inexistente '{l.strip()}'")
            lines = [l for l in lines if l not in dropped]
            code = "\n".join(lines)

        code_lower = code.lower()

        existing = {l.strip() for l in lines if l.strip().startswith("import")}

        # Header base
        base_imports = [
            ln for ln in self._SAFE_HEADER.splitlines()
            if ln.startswith("import") and ln.strip() not in existing
        ]

        # Imports temáticos según contenido
        topic_imports = []
        for keywords, imp in self._TOPIC_IMPORTS:
            if any(kw in code for kw in keywords):
                if imp.strip() not in existing:
                    topic_imports.append(imp)

        # `open` condicionales. `open Real` va siempre (historico); `open List`
        # solo si el codigo usa permutaciones: la notacion `l ~ l'` es *scoped*
        # al espacio List, asi que sin abrirlo Lean falla con "type expected".
        # No se abre siempre para no introducir ambigüedades de nombres
        # (length, prod, sum...) en pruebas que no lo necesitan.
        extra_opens = ["open Real"]
        if " ~ " in code or "Perm" in code:
            extra_opens.append("open List")

        # Los imports que inyecta el propio sistema pasan por el mismo filtro
        # que los del LLM. Sin esto, un modulo renombrado en _TOPIC_IMPORTS
        # (le paso a Matrix.Determinant) tumba la compilacion entera y el
        # fallo es mucho mas dificil de atribuir, porque no lo escribio nadie
        # a la vista.
        all_new = [
            ln for ln in (base_imports + topic_imports)
            if not self._is_unknown_mathlib_import(ln)
        ]
        if all_new:
            header = "\n".join(all_new) + "\n" + "\n".join(extra_opens) + "\n"
            # Los `import` solo son validos al principio del fichero: hay que
            # detenerse en la primera linea que NO sea vacia ni un import. Si
            # se avanzara tambien sobre los `open`, el header caeria detras de
            # ellos y Lean fallaria con "invalid 'import' command".
            insert_at = 0
            for i, line in enumerate(lines):
                s = line.strip()
                if s.startswith("import") or s == "":
                    insert_at = i + 1
                else:
                    break
            lines = lines[:insert_at] + header.splitlines() + lines[insert_at:]
            code = "\n".join(lines)

        # Reemplazar lemas obsoletos
        for old, new in self._DEPRECATED_LEMMAS:
            if old in code and old != new:
                code = code.replace(old, new)
                logger.debug(f"Lean: reemplazado '{old}' → '{new}'")

        return code

    async def check_code(self, code: str) -> LeanResult:
        """
        Verificar codigo Lean arbitrario.

        Args:
            code: Codigo Lean a verificar

        Returns:
            LeanResult con el estado de verificacion
        """
        import time
        start = time.perf_counter()

        code = self._normalize_code(code)

        # Crear archivo temporal con el codigo
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".lean",
            delete=False,
            dir=self.project_path,
            encoding="utf-8",
        ) as f:
            f.write(code)
            temp_file = Path(f.name)

        try:
            result = await self._run_lean_check(temp_file)
            # Si Lean no está instalado localmente, intentar API HTTP externa
            if result.status == LeanResultStatus.NOT_AVAILABLE:
                http_result = await self._verify_via_http(code)
                if http_result is not None:
                    result = http_result
            result.elapsed_ms = (time.perf_counter() - start) * 1000
            return result
        finally:
            temp_file.unlink(missing_ok=True)

    async def check_theorem(
        self,
        name: str,
        statement: str,
        proof: str,
        imports: Optional[list[str]] = None,
    ) -> LeanResult:
        """
        Verificar un teorema con su prueba.

        Args:
            name: Nombre del teorema
            statement: Enunciado del teorema
            proof: Prueba del teorema
            imports: Lista de imports necesarios

        Returns:
            LeanResult con el estado de verificacion
        """
        # Construir codigo completo
        import_lines = ""
        if imports:
            import_lines = "\n".join(f"import {imp}" for imp in imports) + "\n\n"

        code = f"""{import_lines}theorem {name} : {statement} := by
  {proof}
"""
        return await self.check_code(code)

    async def get_goal_state(
        self,
        code: str,
        position: tuple[int, int],
    ) -> list[LeanGoal]:
        """
        Obtener el estado de goals en una posicion del codigo.

        Args:
            code: Codigo Lean
            position: (linea, columna) - 0-indexed

        Returns:
            Lista de goals pendientes
        """
        # Por ahora, parsear desde mensajes de error/info
        result = await self.check_code(code)
        return result.goals

    async def apply_tactic(
        self,
        current_state: str,
        tactic: str,
    ) -> LeanResult:
        """
        Aplicar una tactica al estado actual.

        Args:
            current_state: Codigo Lean hasta el punto actual
            tactic: Tactica a aplicar

        Returns:
            LeanResult con el nuevo estado
        """
        # Añadir la tactica al codigo
        code = f"{current_state}\n  {tactic}"
        return await self.check_code(code)

    async def _verify_via_http(self, code: str) -> Optional[LeanResult]:
        """
        Llama al microservicio externo de verificación Lean (si LEAN_VERIFY_URL
        está configurado).  Retorna None si el servicio no está disponible.
        """
        url = os.environ.get("LEAN_VERIFY_URL", "").rstrip("/")
        if not url:
            return None
        try:
            payload = json.dumps({"code": code, "timeout": int(self.timeout_s)}).encode()
            req = urllib.request.Request(
                f"{url}/verify",
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=self.timeout_s + 10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            result = self._parse_lean_output(
                data.get("stdout", ""),
                data.get("stderr", ""),
                data.get("returncode", 0),
            )
            logger.info("Lean verificado via HTTP API")
            return result
        except Exception as e:
            logger.warning(f"Lean HTTP API no disponible: {e}")
            return None

    @staticmethod
    def _kill_process_tree(pid: int) -> None:
        """Mata el árbol de procesos (padre + hijos) en Windows para evitar zombies de lean.exe."""
        import sys, subprocess as _sp
        if sys.platform == "win32":
            try:
                _sp.run(
                    ["taskkill", "/F", "/T", "/PID", str(pid)],
                    capture_output=True, timeout=10,
                )
            except Exception:
                pass

    def _run_lean_check_sync(self, file_path: Path) -> LeanResult:
        """Usa Popen para poder matar el árbol de procesos en timeout (Windows)."""
        import subprocess, sys
        try:
            proc = subprocess.Popen(
                [self.lean_path, "env", "lean", str(file_path), "--json"],
                cwd=self.project_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except FileNotFoundError:
            logger.info(f"lake no encontrado ({self.lean_path!r})")
            return LeanResult(status=LeanResultStatus.NOT_AVAILABLE,
                              output="lake no está instalado en este entorno")
        except Exception as e:
            err = str(e)
            if any(s in err.lower() for s in ("no such file", "cannot find", "not found")):
                logger.info(f"lake/lean no disponible: {e}")
                return LeanResult(status=LeanResultStatus.NOT_AVAILABLE, output=err)
            logger.error(f"Error al iniciar Lean: {e}")
            return LeanResult(status=LeanResultStatus.ERROR,
                              messages=[{"severity": "error", "message": err}], output=err)

        try:
            stdout_b, stderr_b = proc.communicate(timeout=self.timeout_s)
            output = stdout_b.decode("utf-8", errors="replace")
            errors = stderr_b.decode("utf-8", errors="replace")
            return self._parse_lean_output(output, errors, proc.returncode)
        except subprocess.TimeoutExpired:
            logger.warning(f"Lean timeout after {self.timeout_s}s — matando proceso {proc.pid}")
            self._kill_process_tree(proc.pid)
            try:
                proc.communicate(timeout=5)
            except Exception:
                pass
            try:
                proc.kill()
            except Exception:
                pass
            return LeanResult(status=LeanResultStatus.TIMEOUT,
                              output=f"Timeout after {self.timeout_s}s")
        except Exception as e:
            err = str(e)
            if any(s in err.lower() for s in ("no such file", "cannot find", "not found")):
                logger.info(f"lake/lean no disponible: {e}")
                return LeanResult(status=LeanResultStatus.NOT_AVAILABLE, output=err)
            logger.error(f"Error running Lean: {e}")
            return LeanResult(status=LeanResultStatus.ERROR,
                              messages=[{"severity": "error", "message": err}], output=err)

    async def _run_lean_check(self, file_path: Path) -> LeanResult:
        """
        Ejecutar verificacion de Lean en un archivo.
        Usa thread executor para evitar ProactorEventLoop issues en Windows.
        """
        try:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(None, self._run_lean_check_sync, file_path)
        except Exception as e:
            if "No such file" in str(e) or "cannot find" in str(e).lower() or "not found" in str(e).lower():
                logger.info(f"lake/lean no disponible: {e}")
                return LeanResult(status=LeanResultStatus.NOT_AVAILABLE, output=str(e))
            logger.error(f"Error running Lean: {e}")
            return LeanResult(status=LeanResultStatus.ERROR,
                              messages=[{"severity": "error", "message": str(e)}],
                              output=str(e))

    def _parse_lean_output(
        self,
        stdout: str,
        stderr: str,
        return_code: int
    ) -> LeanResult:
        """Parsear output de Lean."""
        messages = []
        goals = []

        # Parsear lineas JSON
        for line in stdout.strip().split("\n"):
            if not line:
                continue
            try:
                msg = json.loads(line)
                messages.append(msg)

                # Extraer goals si los hay
                if "goals" in msg:
                    for i, goal_str in enumerate(msg["goals"]):
                        goals.append(LeanGoal(
                            index=i,
                            hypothesis=[],  # TODO: parsear hipotesis
                            target=goal_str
                        ))
            except json.JSONDecodeError:
                # Linea no es JSON, ignorar
                pass

        # Determinar estado
        has_errors = any(m.get("severity") == "error" for m in messages)
        has_sorry = "sorry" in stdout.lower()

        if has_errors:
            status = LeanResultStatus.ERROR
        elif has_sorry:
            status = LeanResultStatus.SORRY
        elif goals:
            status = LeanResultStatus.INCOMPLETE
        elif return_code == 0:
            status = LeanResultStatus.SUCCESS
        else:
            status = LeanResultStatus.ERROR

        return LeanResult(
            status=status,
            goals=goals,
            messages=messages,
            output=stdout + stderr
        )

    def check_code_sync(self, code: str) -> LeanResult:
        """Version sincrona de check_code."""
        return asyncio.run(self.check_code(code))

    def check_theorem_sync(
        self,
        name: str,
        statement: str,
        proof: str,
        imports: Optional[list[str]] = None,
    ) -> LeanResult:
        """Version sincrona de check_theorem."""
        return asyncio.run(self.check_theorem(name, statement, proof, imports))
