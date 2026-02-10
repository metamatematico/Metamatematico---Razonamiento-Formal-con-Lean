"""
Pilar III: Logica (F_Log)
=========================

El cluster F_Log incluye:
- FOL= (Logica de Primer Orden con Igualdad)
- SOL (Logica de Segundo Orden)
- HOL (Logica de Orden Superior)
- IL (Logica Intuicionista)

Propiedades metalogicas clave:

| Sistema  | Completitud | Compacidad | L-S | Semi-decidible |
|----------|-------------|------------|-----|----------------|
| FOL=     | ✓           | ✓          | ✓   | ✓              |
| SOL_std  | ✗           | ✗          | ✗   | ✗              |
| SOL_Hen  | ✓           | ✓          | ✓   | ✓              |
| IL       | ✓*          | ✓          | ✓   | ✓              |

FOL= es el "punto dulce": completo + compacto + L-S.
Estas propiedades se pierden en SOL con semantica estandar.

IL produce computo robusto:
- Testigos constructivos
- Extraccion de programas via Curry-Howard
- Normalizacion fuerte
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Optional

from nucleo.pillars.base import Pillar, PillarSkill


class LogicSystem(Enum):
    """Sistemas logicos."""
    FOL = auto()       # Primer orden clasico
    SOL_STD = auto()   # Segundo orden, semantica estandar
    SOL_HEN = auto()   # Segundo orden, semantica Henkin
    HOL = auto()       # Orden superior
    IL = auto()        # Intuicionista


class Connective(Enum):
    """Conectivos logicos."""
    NOT = "¬"
    AND = "∧"
    OR = "∨"
    IMPLIES = "→"
    IFF = "↔"
    FORALL = "∀"
    EXISTS = "∃"
    EQUALS = "="


@dataclass
class Term:
    """
    Termino de FOL.

    Definicion inductiva:
    (T1) Variables: x ∈ Var es termino
    (T2) Constantes: c_i es termino
    (T3) Funciones: f(t_1, ..., t_n) es termino
    """
    name: str
    args: list[Term] = field(default_factory=list)
    is_variable: bool = False

    def __str__(self) -> str:
        if not self.args:
            return self.name
        args_str = ", ".join(str(a) for a in self.args)
        return f"{self.name}({args_str})"

    @classmethod
    def var(cls, name: str) -> Term:
        """Crear variable."""
        return cls(name=name, is_variable=True)

    @classmethod
    def const(cls, name: str) -> Term:
        """Crear constante."""
        return cls(name=name, is_variable=False)

    @classmethod
    def func(cls, name: str, *args: Term) -> Term:
        """Crear aplicacion de funcion."""
        return cls(name=name, args=list(args))


@dataclass
class Formula:
    """
    Formula de FOL.

    Definicion inductiva:
    (F1) Atomicas: t_1 = t_2, P(t_1, ..., t_n)
    (F2) Compuestas: ¬φ, φ ∧ ψ, φ ∨ ψ, φ → ψ
    (F3) Cuantificadas: ∀x φ, ∃x φ
    """
    connective: Optional[Connective]
    subformulas: list[Formula] = field(default_factory=list)
    terms: list[Term] = field(default_factory=list)
    bound_var: Optional[str] = None  # Para cuantificadores
    predicate: Optional[str] = None  # Para atomicas

    def __str__(self) -> str:
        if self.predicate:
            # Atomica
            if self.predicate == "=":
                return f"{self.terms[0]} = {self.terms[1]}"
            args = ", ".join(str(t) for t in self.terms)
            return f"{self.predicate}({args})"

        if self.connective == Connective.NOT:
            return f"¬{self.subformulas[0]}"

        if self.connective in [Connective.AND, Connective.OR,
                               Connective.IMPLIES, Connective.IFF]:
            op = self.connective.value
            left = str(self.subformulas[0])
            right = str(self.subformulas[1])
            return f"({left} {op} {right})"

        if self.connective in [Connective.FORALL, Connective.EXISTS]:
            q = self.connective.value
            return f"{q}{self.bound_var}. {self.subformulas[0]}"

        return "?"

    @classmethod
    def atomic(cls, predicate: str, *terms: Term) -> Formula:
        """Crear formula atomica."""
        return cls(connective=None, predicate=predicate, terms=list(terms))

    @classmethod
    def equals(cls, left: Term, right: Term) -> Formula:
        """Crear igualdad."""
        return cls.atomic("=", left, right)

    @classmethod
    def neg(cls, phi: Formula) -> Formula:
        """Negacion."""
        return cls(connective=Connective.NOT, subformulas=[phi])

    @classmethod
    def conj(cls, phi: Formula, psi: Formula) -> Formula:
        """Conjuncion."""
        return cls(connective=Connective.AND, subformulas=[phi, psi])

    @classmethod
    def disj(cls, phi: Formula, psi: Formula) -> Formula:
        """Disyuncion."""
        return cls(connective=Connective.OR, subformulas=[phi, psi])

    @classmethod
    def implies(cls, phi: Formula, psi: Formula) -> Formula:
        """Implicacion."""
        return cls(connective=Connective.IMPLIES, subformulas=[phi, psi])

    @classmethod
    def forall(cls, var: str, phi: Formula) -> Formula:
        """Cuantificador universal."""
        return cls(
            connective=Connective.FORALL,
            subformulas=[phi],
            bound_var=var
        )

    @classmethod
    def exists(cls, var: str, phi: Formula) -> Formula:
        """Cuantificador existencial."""
        return cls(
            connective=Connective.EXISTS,
            subformulas=[phi],
            bound_var=var
        )


class IntuitionisticLogic:
    """
    Logica Intuicionista (IL).

    Rechaza:
    - Ley del tercero excluido: φ ∨ ¬φ
    - Eliminacion de doble negacion: ¬¬φ → φ

    Una proposicion es verdadera solo si tenemos
    una construccion (prueba) de ella.

    Semantica de Kripke:
    - W: mundos (estados de conocimiento)
    - ≤: preorden sobre W
    - V: valuacion con persistencia
    """

    @staticmethod
    def is_constructive(formula: Formula) -> bool:
        """
        Verificar si una formula es constructivamente valida.

        Heuristica: detectar usos de LEM o DNE.
        """
        # TODO: Implementar verificacion completa
        # Por ahora, rechazar patrones clasicos obvios

        def has_lem_pattern(f: Formula) -> bool:
            """Detectar φ ∨ ¬φ"""
            if f.connective == Connective.OR:
                left, right = f.subformulas
                if (right.connective == Connective.NOT and
                    str(right.subformulas[0]) == str(left)):
                    return True
            return any(has_lem_pattern(sf) for sf in f.subformulas)

        return not has_lem_pattern(formula)


class LogicPillar(Pillar):
    """
    Pilar de Logica (F_Log).

    Implementa el cluster de logica con:
    - Skills para FOL, SOL, IL
    - Deteccion de perdidas metalogicas
    - Verificacion de constructividad
    """

    def __init__(self):
        super().__init__(
            name="F_Log",
            description="Logica: FOL=, SOL, HOL, IL"
        )
        self._initialize_skills()

    def _initialize_skills(self) -> None:
        """Inicializar skills del pilar."""
        skills = [
            PillarSkill(
                id="propositional",
                name="Propositional Logic",
                description="Logica proposicional: ¬, ∧, ∨, →, ↔",
                dependencies=[],
            ),
            PillarSkill(
                id="fol-syntax",
                name="FOL Syntax",
                description="Terminos, formulas, variables libres/ligadas",
                dependencies=["propositional"],
            ),
            PillarSkill(
                id="fol-semantics",
                name="FOL Semantics",
                description="Estructuras, interpretaciones, satisfaccion",
                dependencies=["fol-syntax"],
            ),
            PillarSkill(
                id="fol-deduction",
                name="FOL Deduction",
                description="Sistemas de deduccion natural y secuentes",
                dependencies=["fol-syntax"],
            ),
            PillarSkill(
                id="fol-metatheory",
                name="FOL Metatheory",
                description="Completitud, compacidad, Lowenheim-Skolem",
                dependencies=["fol-semantics", "fol-deduction"],
            ),
            PillarSkill(
                id="sol",
                name="Second Order Logic",
                description="SOL: cuantificacion sobre predicados",
                dependencies=["fol-metatheory"],
                metadata={"warning": "SOL_std pierde completitud y compacidad"}
            ),
            PillarSkill(
                id="intuitionistic",
                name="Intuitionistic Logic",
                description="IL: sin LEM, testigos constructivos",
                dependencies=["fol-deduction"],
            ),
            PillarSkill(
                id="kripke",
                name="Kripke Semantics",
                description="Semantica de mundos posibles para IL",
                dependencies=["intuitionistic"],
            ),
        ]

        for skill in skills:
            self.add_skill(skill)

    def get_skills(self) -> list[PillarSkill]:
        """Obtener todos los skills del pilar."""
        return list(self._skills.values())

    def validate(self) -> bool:
        """Verificar consistencia del pilar."""
        skill_ids = set(self._skills.keys())
        for skill in self._skills.values():
            for dep in skill.dependencies:
                if dep not in skill_ids:
                    return False
        return True

    def check_metalogical_properties(
        self,
        system: LogicSystem
    ) -> dict[str, bool]:
        """
        Verificar propiedades metalogicas de un sistema.

        Returns:
            Dict con propiedades y su estado
        """
        properties = {
            LogicSystem.FOL: {
                "completeness": True,
                "compactness": True,
                "lowenheim_skolem": True,
                "semi_decidable": True,
                "lem": True,
            },
            LogicSystem.SOL_STD: {
                "completeness": False,  # Perdida!
                "compactness": False,   # Perdida!
                "lowenheim_skolem": False,  # Perdida!
                "semi_decidable": False,  # Perdida!
                "lem": True,
            },
            LogicSystem.SOL_HEN: {
                "completeness": True,
                "compactness": True,
                "lowenheim_skolem": True,
                "semi_decidable": True,
                "lem": True,
            },
            LogicSystem.IL: {
                "completeness": True,  # Respecto a Kripke
                "compactness": True,
                "lowenheim_skolem": True,
                "semi_decidable": True,
                "lem": False,  # Rechazado
                "program_extraction": True,  # Curry-Howard
                "strong_normalization": True,
            },
        }
        return properties.get(system, {})

    def warn_if_sol_standard(self, formula: Formula) -> Optional[str]:
        """
        Advertir si formula requiere SOL con semantica estandar.

        Detecta cuantificacion de segundo orden.
        """
        # TODO: Implementar deteccion de cuantificacion de segundo orden
        return None
