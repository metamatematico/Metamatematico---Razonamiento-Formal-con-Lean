"""
Pilar IV: Teoria de Tipos (F_Type)
==================================

El cluster F_Type incluye:
- STLC (lambda→): Solo tipos funcion
- System F (lambda2): Polimorfismo parametrico
- CC (lambdaC): Calculo de Construcciones
- CIC: CC + tipos inductivos (base de Lean 4)
- MLTT: Teoria de Tipos de Martin-Lof

Propiedades clave:
- Curry-Howard: proposiciones = tipos, pruebas = programas
- Jerarquia de universos: Prop : Type_0 : Type_1 : ...
- Normalizacion fuerte: toda prueba termina
- Extraccion de programas

Conexion con Lean 4:
- Lean implementa CIC con universos predicativos
- translate: F_Log.IL x F_Type.CIC -> Lean4.Kernel
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Optional, Union

from nucleo.pillars.base import Pillar, PillarSkill


class TypeSystem(Enum):
    """Sistemas de tipos en el Cubo de Barendregt."""
    STLC = auto()      # lambda→: tipos funcion
    SYSTEM_F = auto()  # lambda2: polimorfismo
    SYSTEM_FW = auto() # lambdaω: constructores de tipos
    LF = auto()        # lambdaP: tipos dependientes
    CC = auto()        # lambdaC: Calculo de Construcciones
    CIC = auto()       # CC + inductivos


@dataclass
class Universe:
    """
    Universo en la jerarquia de tipos.

    Prop : Type_0 : Type_1 : Type_2 : ...
    con Type_i : Type_{i+1}
    """
    level: int
    is_prop: bool = False

    def __str__(self) -> str:
        if self.is_prop:
            return "Prop"
        return f"Type_{self.level}"

    def __lt__(self, other: Universe) -> bool:
        if self.is_prop and not other.is_prop:
            return True
        if not self.is_prop and other.is_prop:
            return False
        return self.level < other.level


# Universos comunes
PROP = Universe(level=0, is_prop=True)
TYPE_0 = Universe(level=0, is_prop=False)
TYPE_1 = Universe(level=1, is_prop=False)


@dataclass
class Type:
    """
    Representacion de un tipo en CIC.

    Tipos basicos:
    - Prop, Type_i (universos)
    - A -> B (funcion)
    - (x : A) -> B x (Pi, funcion dependiente)
    - (x : A) × B x (Sigma, par dependiente)
    - Inductivos (Nat, List, etc.)
    """
    name: str
    universe: Universe = field(default_factory=lambda: TYPE_0)
    params: list[Type] = field(default_factory=list)
    is_inductive: bool = False

    def __str__(self) -> str:
        if self.params:
            params_str = " ".join(str(p) for p in self.params)
            return f"({self.name} {params_str})"
        return self.name


@dataclass
class Term:
    """
    Representacion de un termino tipado.

    En Curry-Howard:
    - Term de tipo A = prueba de proposicion A
    """
    name: str
    type: Type
    body: Optional[str] = None  # Definicion del termino

    def __str__(self) -> str:
        return f"{self.name} : {self.type}"


class CurryHoward:
    """
    Correspondencia Curry-Howard.

    Traduce entre logica intuicionista y teoria de tipos:

    | Logica          | Tipos                |
    |-----------------|----------------------|
    | Proposicion φ   | Tipo τ               |
    | Prueba de φ     | Termino de tipo τ    |
    | φ → ψ           | τ₁ → τ₂              |
    | φ ∧ ψ           | τ₁ × τ₂              |
    | φ ∨ ψ           | τ₁ + τ₂              |
    | ∀x. φ(x)        | Π(x:A). B(x)         |
    | ∃x. φ(x)        | Σ(x:A). B(x)         |
    | Normalizacion   | β-reduccion          |
    """

    @staticmethod
    def implication_to_function(
        premise: Type,
        conclusion: Type
    ) -> Type:
        """φ → ψ  ↦  τ₁ → τ₂"""
        return Type(
            name="Arrow",
            params=[premise, conclusion],
            universe=max(premise.universe, conclusion.universe)
        )

    @staticmethod
    def conjunction_to_product(
        left: Type,
        right: Type
    ) -> Type:
        """φ ∧ ψ  ↦  τ₁ × τ₂"""
        return Type(
            name="Prod",
            params=[left, right],
            universe=max(left.universe, right.universe)
        )

    @staticmethod
    def disjunction_to_sum(
        left: Type,
        right: Type
    ) -> Type:
        """φ ∨ ψ  ↦  τ₁ + τ₂"""
        return Type(
            name="Sum",
            params=[left, right],
            universe=max(left.universe, right.universe)
        )

    @staticmethod
    def forall_to_pi(
        var_type: Type,
        body_type: Type
    ) -> Type:
        """∀x. φ(x)  ↦  Π(x:A). B(x)"""
        return Type(
            name="Pi",
            params=[var_type, body_type],
            universe=max(var_type.universe, body_type.universe)
        )

    @staticmethod
    def exists_to_sigma(
        var_type: Type,
        body_type: Type
    ) -> Type:
        """∃x. φ(x)  ↦  Σ(x:A). B(x)"""
        return Type(
            name="Sigma",
            params=[var_type, body_type],
            universe=max(var_type.universe, body_type.universe)
        )


class TypeTheoryPillar(Pillar):
    """
    Pilar de Teoria de Tipos (F_Type).

    Implementa el cluster de teoria de tipos con:
    - Skills para cada sistema de tipos
    - Jerarquia de universos
    - Correspondencia Curry-Howard
    - Traduccion a Lean 4
    """

    def __init__(self):
        super().__init__(
            name="F_Type",
            description="Teoria de Tipos: STLC, System F, CC, CIC, MLTT"
        )
        self._initialize_skills()

    def _initialize_skills(self) -> None:
        """Inicializar skills del pilar."""
        skills = [
            PillarSkill(
                id="stlc",
                name="Simply Typed Lambda Calculus",
                description="λ→: Solo tipos funcion, base del calculo tipado",
                dependencies=[],
            ),
            PillarSkill(
                id="system-f",
                name="System F",
                description="λ2: Polimorfismo parametrico (∀α. τ)",
                dependencies=["stlc"],
            ),
            PillarSkill(
                id="dependent-types",
                name="Dependent Types",
                description="λP: Tipos que dependen de valores",
                dependencies=["stlc"],
            ),
            PillarSkill(
                id="cc",
                name="Calculus of Constructions",
                description="λC: Vertice del Cubo de Barendregt",
                dependencies=["system-f", "dependent-types"],
            ),
            PillarSkill(
                id="cic",
                name="Calculus of Inductive Constructions",
                description="CIC: CC + tipos inductivos (base de Lean/Coq)",
                dependencies=["cc"],
            ),
            PillarSkill(
                id="universes",
                name="Universe Hierarchy",
                description="Prop : Type_0 : Type_1 : ... (evita paradoja de Girard)",
                dependencies=["cic"],
            ),
            PillarSkill(
                id="curry-howard",
                name="Curry-Howard Correspondence",
                description="Isomorfismo proposiciones-tipos, pruebas-programas",
                dependencies=["cic"],
            ),
            PillarSkill(
                id="lean-kernel",
                name="Lean 4 Kernel",
                description="Nucleo de verificacion de Lean 4",
                dependencies=["cic", "universes"],
            ),
        ]

        for skill in skills:
            self.add_skill(skill)

    def get_skills(self) -> list[PillarSkill]:
        """Obtener todos los skills del pilar."""
        return list(self._skills.values())

    def validate(self) -> bool:
        """
        Verificar consistencia del pilar.

        Checks:
        - Todos los skills tienen dependencias validas
        - No hay ciclos en dependencias
        """
        skill_ids = set(self._skills.keys())

        for skill in self._skills.values():
            for dep in skill.dependencies:
                if dep not in skill_ids:
                    return False

        # TODO: Verificar ausencia de ciclos
        return True

    def translate_to_lean(self, type_: Type) -> str:
        """
        Traducir tipo a sintaxis Lean 4.

        Args:
            type_: Tipo a traducir

        Returns:
            Representacion en Lean 4
        """
        if type_.name == "Arrow":
            left = self.translate_to_lean(type_.params[0])
            right = self.translate_to_lean(type_.params[1])
            return f"({left} → {right})"

        if type_.name == "Prod":
            left = self.translate_to_lean(type_.params[0])
            right = self.translate_to_lean(type_.params[1])
            return f"({left} × {right})"

        if type_.name == "Sum":
            left = self.translate_to_lean(type_.params[0])
            right = self.translate_to_lean(type_.params[1])
            return f"({left} ⊕ {right})"

        if type_.name == "Pi":
            var_type = self.translate_to_lean(type_.params[0])
            body = self.translate_to_lean(type_.params[1])
            return f"(∀ _ : {var_type}, {body})"

        if type_.name == "Sigma":
            var_type = self.translate_to_lean(type_.params[0])
            body = self.translate_to_lean(type_.params[1])
            return f"(Σ _ : {var_type}, {body})"

        # Tipo basico
        return type_.name
