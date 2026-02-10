"""
Parser de Mensajes Lean 4
=========================

Parsea y estructura mensajes de Lean 4 para facilitar
el analisis de errores y la extraccion de informacion.

Enhanced with structured error classification from:
- lean4-skills/plugins/lean4-theorem-proving/scripts/parseLeanErrors.py
- APOLLO compiler-feedback-driven repair (https://arxiv.org/abs/2505.05758)
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Any


class MessageSeverity(Enum):
    """Severidad de mensaje de Lean."""
    ERROR = auto()
    WARNING = auto()
    INFO = auto()
    HINT = auto()


@dataclass
class Position:
    """Posicion en el codigo fuente."""
    line: int      # 1-indexed
    column: int    # 1-indexed

    @classmethod
    def from_dict(cls, data: dict[str, int]) -> Position:
        return cls(
            line=data.get("line", 1),
            column=data.get("column", 1)
        )


@dataclass
class LeanMessage:
    """
    Mensaje estructurado de Lean.

    Attributes:
        severity: Severidad del mensaje
        message: Texto del mensaje
        position: Posicion en el codigo
        end_position: Posicion final (opcional)
        source: Fuente del mensaje (archivo)
        data: Datos adicionales del mensaje
    """
    severity: MessageSeverity
    message: str
    position: Optional[Position] = None
    end_position: Optional[Position] = None
    source: Optional[str] = None
    data: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LeanMessage:
        """Crear desde diccionario JSON de Lean."""
        severity_str = data.get("severity", "info").lower()
        severity_map = {
            "error": MessageSeverity.ERROR,
            "warning": MessageSeverity.WARNING,
            "info": MessageSeverity.INFO,
            "hint": MessageSeverity.HINT,
        }

        pos = None
        if "pos" in data:
            pos = Position.from_dict(data["pos"])

        end_pos = None
        if "endPos" in data:
            end_pos = Position.from_dict(data["endPos"])

        return cls(
            severity=severity_map.get(severity_str, MessageSeverity.INFO),
            message=data.get("message", ""),
            position=pos,
            end_position=end_pos,
            source=data.get("file"),
            data=data
        )

    @property
    def is_error(self) -> bool:
        return self.severity == MessageSeverity.ERROR

    @property
    def is_warning(self) -> bool:
        return self.severity == MessageSeverity.WARNING


class LeanParser:
    """
    Parser de output de Lean 4.

    Extrae informacion estructurada de mensajes de error,
    goals, tacticas disponibles, etc.
    """

    # Patrones comunes de error
    ERROR_PATTERNS = {
        "type_mismatch": re.compile(
            r"type mismatch\s+(.+?)\s+has type\s+(.+?)\s+but is expected to have type\s+(.+)",
            re.DOTALL
        ),
        "unknown_identifier": re.compile(
            r"unknown identifier '([^']+)'"
        ),
        "unknown_tactic": re.compile(
            r"unknown tactic '([^']+)'"
        ),
        "unsolved_goals": re.compile(
            r"unsolved goals\s+(.+)",
            re.DOTALL
        ),
        "invalid_syntax": re.compile(
            r"expected (.+)"
        ),
        "declaration_uses_sorry": re.compile(
            r"declaration uses 'sorry'"
        ),
    }

    # Patron para extraer goals
    GOAL_PATTERN = re.compile(
        r"case\s+(\w+).*?\n((?:.*?\n)*?)⊢\s*(.+?)(?=\n\ncase|\Z)",
        re.DOTALL
    )

    @classmethod
    def parse_messages(cls, output: str) -> list[LeanMessage]:
        """
        Parsear output de Lean a lista de mensajes.
        """
        messages = []

        # Intentar parsear JSON line by line
        import json
        for line in output.strip().split("\n"):
            if not line:
                continue
            try:
                data = json.loads(line)
                messages.append(LeanMessage.from_dict(data))
            except json.JSONDecodeError:
                # No es JSON, crear mensaje de texto plano
                if line.strip():
                    messages.append(LeanMessage(
                        severity=MessageSeverity.INFO,
                        message=line
                    ))

        return messages

    @classmethod
    def extract_error_type(cls, message: str) -> Optional[str]:
        """
        Extraer el tipo de error de un mensaje.

        Returns:
            Nombre del patron de error o None
        """
        for name, pattern in cls.ERROR_PATTERNS.items():
            if pattern.search(message):
                return name
        return None

    @classmethod
    def parse_type_mismatch(cls, message: str) -> Optional[dict[str, str]]:
        """
        Parsear error de type mismatch.

        Returns:
            Dict con term, actual_type, expected_type
        """
        match = cls.ERROR_PATTERNS["type_mismatch"].search(message)
        if match:
            return {
                "term": match.group(1).strip(),
                "actual_type": match.group(2).strip(),
                "expected_type": match.group(3).strip(),
            }
        return None

    @classmethod
    def parse_unknown_identifier(cls, message: str) -> Optional[str]:
        """Extraer identificador desconocido."""
        match = cls.ERROR_PATTERNS["unknown_identifier"].search(message)
        return match.group(1) if match else None

    @classmethod
    def parse_goals(cls, output: str) -> list[dict[str, Any]]:
        """
        Extraer goals del output de Lean.

        Returns:
            Lista de goals con case, hypotheses, target
        """
        goals = []

        # Buscar patron de goals
        for match in cls.GOAL_PATTERN.finditer(output):
            case_name = match.group(1)
            context = match.group(2).strip()
            target = match.group(3).strip()

            # Parsear hipotesis
            hypotheses = []
            for line in context.split("\n"):
                line = line.strip()
                if line and ":" in line:
                    hypotheses.append(line)

            goals.append({
                "case": case_name,
                "hypotheses": hypotheses,
                "target": target,
            })

        return goals

    @classmethod
    def suggest_fix(cls, error_type: str, details: dict[str, Any]) -> Optional[str]:
        """
        Sugerir correccion para un tipo de error.

        Args:
            error_type: Tipo de error (de extract_error_type)
            details: Detalles parseados del error

        Returns:
            Sugerencia de correccion o None
        """
        suggestions = {
            "type_mismatch": lambda d: f"Intenta convertir con `show {d.get('expected_type', '?')}`",
            "unknown_identifier": lambda d: f"Verifica que '{d.get('name', '?')}' este importado o definido",
            "unknown_tactic": lambda d: f"Tactica '{d.get('name', '?')}' no existe. Revisa la sintaxis",
            "unsolved_goals": lambda d: "Hay goals pendientes. Usa `sorry` temporalmente o completa la prueba",
            "declaration_uses_sorry": lambda d: "Reemplaza `sorry` con una prueba valida",
        }

        if error_type in suggestions:
            return suggestions[error_type](details)
        return None


# =========================================================================
# STRUCTURED ERROR ANALYSIS
# Adapted from parseLeanErrors.py (lean4-skills)
# =========================================================================

# Extended error classification patterns
_EXTENDED_ERROR_PATTERNS = [
    # More specific patterns first to avoid substring matches
    (r"application type mismatch", "app_type_mismatch"),
    (r"type mismatch", "type_mismatch"),
    (r"don't know how to synthesize implicit argument", "synth_implicit"),
    (r"unsolved goals", "unsolved_goals"),
    (r"unknown identifier '([^']+)'", "unknown_ident"),
    (r"unknown tactic", "unknown_tactic"),
    (r"failed to synthesize instance", "synth_instance"),
    (r"tactic 'sorry' has not been implemented", "sorry_present"),
    (r"declaration uses 'sorry'", "sorry_present"),
    (r"maximum recursion depth", "recursion_depth"),
    (r"deterministic timeout", "timeout"),
    (r"expected type", "type_expected"),
]


@dataclass
class StructuredError:
    """
    Structured representation of a Lean error.

    Adapted from parseLeanErrors.py output schema for use
    in the NLE repair and learning pipeline.
    """
    error_hash: str
    error_type: str
    message: str
    file: str = ""
    line: int = 0
    column: int = 0
    goal: Optional[str] = None
    local_context: list[str] = field(default_factory=list)
    suggestion_keywords: list[str] = field(default_factory=list)

    @property
    def is_cascade_compatible(self) -> bool:
        """Whether this error can benefit from solver cascade."""
        return self.error_type not in (
            "unknown_ident", "synth_implicit", "recursion_depth",
            "synth_instance", "timeout",
        )


def classify_error(message: str) -> str:
    """Classify error type from message text."""
    for pattern, error_type in _EXTENDED_ERROR_PATTERNS:
        if re.search(pattern, message, re.IGNORECASE):
            return error_type
    return "unknown"


def extract_goal(error_text: str) -> Optional[str]:
    """Extract goal state from error (if present)."""
    goal_match = re.search(r"⊢\s+(.+)", error_text)
    if goal_match:
        return goal_match.group(1).strip()
    return None


def extract_local_context(error_text: str) -> list[str]:
    """Extract local context (hypotheses) from error."""
    context = []
    in_context = False
    for line in error_text.split("\n"):
        if "⊢" in line:
            in_context = False
        if in_context and ":" in line:
            hyp = line.strip()
            if hyp and not hyp.startswith("case"):
                context.append(hyp)
        if "context:" in line.lower() or line.strip().endswith(":"):
            in_context = True
    return context


def extract_suggestion_keywords(message: str) -> list[str]:
    """Extract relevant keywords for search/suggestions."""
    keywords = []
    keywords.extend(re.findall(r"'([^']+)'", message))
    for term in ["Continuous", "Measurable", "Integrable", "Differentiable",
                 "Fintype", "DecidableEq", "Group", "Ring", "Field"]:
        if term.lower() in message.lower():
            keywords.append(term)
    return list(set(keywords))[:10]


def compute_error_hash(error_type: str, file: str, line: int) -> str:
    """Compute deterministic hash for error tracking."""
    content = f"{error_type}:{file}:{line}"
    return hashlib.sha256(content.encode()).hexdigest()[:12]


def parse_error_structured(message: LeanMessage) -> StructuredError:
    """
    Parse a LeanMessage into a StructuredError.

    This bridges the existing LeanParser with the parseLeanErrors.py
    structured format used by the solver cascade and MES memory.
    """
    text = message.message
    error_type = classify_error(text)
    file = message.source or ""
    line = message.position.line if message.position else 0
    column = message.position.column if message.position else 0

    return StructuredError(
        error_hash=compute_error_hash(error_type, file, line),
        error_type=error_type,
        message=text[:500],
        file=file,
        line=line,
        column=column,
        goal=extract_goal(text),
        local_context=extract_local_context(text),
        suggestion_keywords=extract_suggestion_keywords(text),
    )
