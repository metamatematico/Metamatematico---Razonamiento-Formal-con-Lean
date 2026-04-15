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
import subprocess
import json
import tempfile
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import Optional, Any
import logging

logger = logging.getLogger(__name__)


class LeanResultStatus(Enum):
    """Estado del resultado de Lean."""
    SUCCESS = auto()       # Prueba completada
    ERROR = auto()         # Error de compilacion/tipo
    TIMEOUT = auto()       # Timeout excedido
    INCOMPLETE = auto()    # Prueba incompleta (goals pendientes)
    SORRY = auto()         # Contiene sorry


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
        return [m.get("message", "") for m in self.messages if m.get("severity") == "error"]

    def get_first_error(self) -> Optional[str]:
        errors = self.error_messages
        return errors[0] if errors else None


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
        timeout_ms: int = 30000,
    ):
        """
        Inicializar cliente Lean.

        Args:
            project_path: Ruta al proyecto Lean (con lakefile.toml)
            lean_path: Ruta al ejecutable lake
            timeout_ms: Timeout en milisegundos
        """
        self.project_path = Path(project_path) if project_path else Path.cwd()
        self.lean_path = lean_path
        self.timeout_s = timeout_ms / 1000.0

    # Header mínimo garantizado para tácticas y tipos básicos
    _SAFE_HEADER = (
        "import Mathlib.Tactic.Ring\n"
        "import Mathlib.Tactic.Linarith\n"
        "import Mathlib.Tactic.NormNum\n"
        "import Mathlib.Tactic.Omega\n"
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
        # Álgebra lineal
        (["LinearMap", "Matrix", "det", "eigenvalue"],
         "import Mathlib.LinearAlgebra.Matrix.Determinant"),
        # Números
        (["Nat.Prime", "prime", "Finset.sum"],
         "import Mathlib.Data.Nat.Prime.Basic"),
        (["Complex", "re ", "im ", "Complex.abs"],
         "import Mathlib.Analysis.SpecialFunctions.Complex.Circle"),
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
    ]

    def _normalize_code(self, code: str) -> str:
        """
        Normaliza el código Lean antes de verificarlo:
        1. Si tiene `import Mathlib` completo → no toca nada.
        2. Añade el header mínimo seguro (ring, linarith, etc.).
        3. Detecta el tema del código y añade imports específicos.
        4. Reemplaza nombres de lemas obsoletos por los actuales.
        """
        lines = code.lstrip().splitlines()

        # Si ya importa Mathlib completo, solo aplicar correcciones de nombres
        has_full_mathlib = any(l.strip() == "import Mathlib" for l in lines)

        code_lower = code.lower()

        if not has_full_mathlib:
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

            all_new = base_imports + topic_imports
            if all_new:
                header = "\n".join(all_new) + "\nopen Real\n"
                insert_at = 0
                for i, line in enumerate(lines):
                    s = line.strip()
                    if s.startswith("import") or s.startswith("open") or s == "":
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
            result.elapsed_ms = (time.perf_counter() - start) * 1000
            return result
        finally:
            # Limpiar archivo temporal
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

    async def _run_lean_check(self, file_path: Path) -> LeanResult:
        """
        Ejecutar verificacion de Lean en un archivo.
        """
        try:
            proc = await asyncio.create_subprocess_exec(
                self.lean_path,
                "env",
                "lean",
                str(file_path),
                "--json",
                cwd=self.project_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=self.timeout_s
            )

            output = stdout.decode("utf-8", errors="replace")
            errors = stderr.decode("utf-8", errors="replace")

            return self._parse_lean_output(output, errors, proc.returncode or 0)

        except asyncio.TimeoutError:
            logger.warning(f"Lean timeout after {self.timeout_s}s")
            return LeanResult(
                status=LeanResultStatus.TIMEOUT,
                output=f"Timeout after {self.timeout_s}s"
            )
        except Exception as e:
            logger.error(f"Error running Lean: {e}")
            return LeanResult(
                status=LeanResultStatus.ERROR,
                messages=[{"severity": "error", "message": str(e)}],
                output=str(e)
            )

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
