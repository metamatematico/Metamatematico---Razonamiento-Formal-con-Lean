"""
Mapeo de Tacticas Lean 4
========================

Catalogo de tacticas de Lean 4 organizadas por categoria,
con metadatos para seleccion inteligente por el agente RL.

Basado en: agents/skills/lean-tp-tactic-selection/
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class TacticCategory(Enum):
    """Categorias de tacticas."""
    # Introduccion/Eliminacion
    INTRO = auto()           # Introducir hipotesis
    ELIM = auto()            # Eliminar/destruir

    # Manipulacion de goals
    APPLY = auto()           # Aplicar lemas/teoremas
    REWRITE = auto()         # Reescritura
    SIMPLIFY = auto()        # Simplificacion

    # Estructural
    SPLIT = auto()           # Dividir goals
    CASES = auto()           # Analisis por casos
    INDUCTION = auto()       # Induccion

    # Automatizacion
    AUTO = auto()            # Tacticas automaticas
    DECISION = auto()        # Procedimientos de decision

    # Finalizacion
    CLOSE = auto()           # Cerrar goals triviales

    # Meta
    CONTROL = auto()         # Control de flujo


@dataclass
class Tactic:
    """
    Definicion de una tactica Lean 4.

    Attributes:
        name: Nombre de la tactica
        category: Categoria de la tactica
        description: Descripcion breve
        syntax: Sintaxis de uso
        examples: Ejemplos de uso
        preconditions: Condiciones para aplicar
        effects: Efectos esperados
        complexity: Complejidad relativa (1-5)
    """
    name: str
    category: TacticCategory
    description: str = ""
    syntax: str = ""
    examples: list[str] = field(default_factory=list)
    preconditions: list[str] = field(default_factory=list)
    effects: list[str] = field(default_factory=list)
    complexity: int = 1

    def matches_goal(self, goal_type: str) -> float:
        """
        Calcular score de match con un tipo de goal.

        Returns:
            Score de 0.0 a 1.0
        """
        # Heuristicas basicas por categoria
        scores = {
            TacticCategory.INTRO: 0.8 if "∀" in goal_type or "→" in goal_type else 0.2,
            TacticCategory.SPLIT: 0.9 if "∧" in goal_type or "↔" in goal_type else 0.1,
            TacticCategory.CASES: 0.8 if "∨" in goal_type else 0.3,
            TacticCategory.REWRITE: 0.7 if "=" in goal_type else 0.3,
            TacticCategory.CLOSE: 0.9 if goal_type in ["True", "trivial"] else 0.1,
            TacticCategory.AUTO: 0.5,  # Siempre una opcion
        }
        return scores.get(self.category, 0.3)


class TacticMapper:
    """
    Mapeador de tacticas Lean 4.

    Proporciona:
    - Catalogo completo de tacticas
    - Seleccion basada en tipo de goal
    - Sugerencias ordenadas por relevancia
    """

    # Catalogo de tacticas principales
    TACTICS: dict[str, Tactic] = {
        # === INTRODUCCION ===
        "intro": Tactic(
            name="intro",
            category=TacticCategory.INTRO,
            description="Introduce una variable o hipotesis",
            syntax="intro x | intro h | intros",
            examples=["intro n", "intro h", "intros x y z"],
            preconditions=["Goal es ∀ o →"],
            effects=["Añade variable/hipotesis al contexto", "Simplifica goal"],
            complexity=1,
        ),
        "intros": Tactic(
            name="intros",
            category=TacticCategory.INTRO,
            description="Introduce multiples variables/hipotesis",
            syntax="intros | intros x y z",
            examples=["intros", "intros a b c"],
            preconditions=["Goal tiene ∀ o → anidados"],
            effects=["Introduce todas las variables posibles"],
            complexity=1,
        ),

        # === APLICACION ===
        "apply": Tactic(
            name="apply",
            category=TacticCategory.APPLY,
            description="Aplica un lema o hipotesis",
            syntax="apply lemma | apply h",
            examples=["apply Nat.add_comm", "apply h"],
            preconditions=["Conclusion del lema unifica con goal"],
            effects=["Reemplaza goal con premisas del lema"],
            complexity=2,
        ),
        "exact": Tactic(
            name="exact",
            category=TacticCategory.APPLY,
            description="Cierra goal con termino exacto",
            syntax="exact term",
            examples=["exact h", "exact rfl", "exact Nat.zero_add n"],
            preconditions=["Termino tiene exactamente el tipo del goal"],
            effects=["Cierra el goal"],
            complexity=1,
        ),
        "refine": Tactic(
            name="refine",
            category=TacticCategory.APPLY,
            description="Aplica termino con huecos",
            syntax="refine term",
            examples=["refine ⟨_, _⟩", "refine ?a"],
            preconditions=["Termino parcialmente unifica con goal"],
            effects=["Genera nuevos goals para los huecos"],
            complexity=3,
        ),

        # === REESCRITURA ===
        "rw": Tactic(
            name="rw",
            category=TacticCategory.REWRITE,
            description="Reescribe usando igualdad",
            syntax="rw [eq] | rw [eq1, eq2] | rw [← eq]",
            examples=["rw [h]", "rw [Nat.add_comm]", "rw [← h]"],
            preconditions=["Ecuacion aplicable al goal"],
            effects=["Reemplaza lado izquierdo por derecho"],
            complexity=2,
        ),
        "simp": Tactic(
            name="simp",
            category=TacticCategory.SIMPLIFY,
            description="Simplifica usando lemas simp",
            syntax="simp | simp [lemmas] | simp only [lemmas]",
            examples=["simp", "simp [h]", "simp only [Nat.add_zero]"],
            preconditions=[],
            effects=["Simplifica goal y/o hipotesis"],
            complexity=2,
        ),
        "ring": Tactic(
            name="ring",
            category=TacticCategory.DECISION,
            description="Decide igualdades de anillos",
            syntax="ring",
            examples=["ring"],
            preconditions=["Goal es igualdad en anillo conmutativo"],
            effects=["Cierra goal si es identidad de anillo"],
            complexity=1,
        ),

        # === ESTRUCTURAL ===
        "constructor": Tactic(
            name="constructor",
            category=TacticCategory.SPLIT,
            description="Aplica constructor del tipo inductivo",
            syntax="constructor",
            examples=["constructor"],
            preconditions=["Goal es tipo inductivo"],
            effects=["Genera goals para argumentos del constructor"],
            complexity=1,
        ),
        "cases": Tactic(
            name="cases",
            category=TacticCategory.CASES,
            description="Analisis por casos",
            syntax="cases h | cases h with | ⟨x, y⟩ | ...",
            examples=["cases h", "cases n with | zero => | succ n => "],
            preconditions=["Hipotesis es tipo inductivo"],
            effects=["Genera un goal por constructor"],
            complexity=2,
        ),
        "induction": Tactic(
            name="induction",
            category=TacticCategory.INDUCTION,
            description="Induccion sobre tipo inductivo",
            syntax="induction n with | zero => | succ n ih =>",
            examples=["induction n with | zero => rfl | succ n ih => simp [ih]"],
            preconditions=["Variable es tipo inductivo"],
            effects=["Genera casos base e inductivo con hipotesis de induccion"],
            complexity=3,
        ),
        "rcases": Tactic(
            name="rcases",
            category=TacticCategory.CASES,
            description="Casos recursivos con patrones",
            syntax="rcases h with ⟨a, b⟩ | ⟨c⟩",
            examples=["rcases h with ⟨x, hx⟩", "rcases h with rfl"],
            preconditions=["Hipotesis es tipo inductivo"],
            effects=["Destructura hipotesis con patron"],
            complexity=2,
        ),
        "obtain": Tactic(
            name="obtain",
            category=TacticCategory.CASES,
            description="Obtiene testigo de existencial",
            syntax="obtain ⟨x, hx⟩ := h",
            examples=["obtain ⟨n, hn⟩ := h"],
            preconditions=["Hipotesis es existencial"],
            effects=["Introduce testigo y prueba"],
            complexity=2,
        ),

        # === AUTOMATIZACION ===
        "trivial": Tactic(
            name="trivial",
            category=TacticCategory.CLOSE,
            description="Cierra goals triviales",
            syntax="trivial",
            examples=["trivial"],
            preconditions=["Goal es trivialmente verdadero"],
            effects=["Cierra goal"],
            complexity=1,
        ),
        "rfl": Tactic(
            name="rfl",
            category=TacticCategory.CLOSE,
            description="Reflexividad de igualdad",
            syntax="rfl",
            examples=["rfl"],
            preconditions=["Goal es a = a (definicionalmente)"],
            effects=["Cierra goal"],
            complexity=1,
        ),
        "decide": Tactic(
            name="decide",
            category=TacticCategory.DECISION,
            description="Decide proposiciones decidibles",
            syntax="decide",
            examples=["decide"],
            preconditions=["Goal es proposicion decidible"],
            effects=["Cierra goal si es verdadero"],
            complexity=1,
        ),
        "omega": Tactic(
            name="omega",
            category=TacticCategory.DECISION,
            description="Decide aritmetica lineal",
            syntax="omega",
            examples=["omega"],
            preconditions=["Goal es formula de aritmetica lineal"],
            effects=["Cierra goal"],
            complexity=1,
        ),
        "aesop": Tactic(
            name="aesop",
            category=TacticCategory.AUTO,
            description="Automatizacion extensible",
            syntax="aesop",
            examples=["aesop"],
            preconditions=[],
            effects=["Intenta cerrar goal automaticamente"],
            complexity=2,
        ),

        # === CONTROL ===
        "have": Tactic(
            name="have",
            category=TacticCategory.CONTROL,
            description="Introduce lema intermedio",
            syntax="have h : P := proof | have h : P := by tactics",
            examples=["have h : n > 0 := by omega"],
            preconditions=[],
            effects=["Añade hipotesis al contexto"],
            complexity=2,
        ),
        "suffices": Tactic(
            name="suffices",
            category=TacticCategory.CONTROL,
            description="Basta probar esto",
            syntax="suffices h : P by tactic",
            examples=["suffices h : n = 0 by simp [h]"],
            preconditions=[],
            effects=["Cambia goal a P, asumiendo P → goal original"],
            complexity=3,
        ),
        "sorry": Tactic(
            name="sorry",
            category=TacticCategory.CONTROL,
            description="Placeholder para prueba pendiente",
            syntax="sorry",
            examples=["sorry"],
            preconditions=[],
            effects=["Cierra goal (inseguro!)"],
            complexity=1,
        ),
    }

    @classmethod
    def get_tactic(cls, name: str) -> Optional[Tactic]:
        """Obtener tactica por nombre."""
        return cls.TACTICS.get(name)

    @classmethod
    def get_by_category(cls, category: TacticCategory) -> list[Tactic]:
        """Obtener tacticas de una categoria."""
        return [t for t in cls.TACTICS.values() if t.category == category]

    @classmethod
    def suggest_for_goal(cls, goal_type: str, top_k: int = 5) -> list[Tactic]:
        """
        Sugerir tacticas para un tipo de goal.

        Args:
            goal_type: Representacion del tipo de goal
            top_k: Numero maximo de sugerencias

        Returns:
            Lista de tacticas ordenadas por relevancia
        """
        scored = [
            (tactic, tactic.matches_goal(goal_type))
            for tactic in cls.TACTICS.values()
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [t for t, _ in scored[:top_k]]

    @classmethod
    def suggest_for_pattern(cls, pattern: str) -> list[Tactic]:
        """
        Sugerir tacticas basadas en patron de goal.

        Patrones comunes:
        - "∀": intro, intros
        - "→": intro, apply
        - "∧": constructor, And.intro
        - "∨": left, right, cases
        - "∃": use, obtain
        - "=": rfl, rw, simp
        """
        suggestions_map = {
            "∀": ["intro", "intros"],
            "→": ["intro", "apply"],
            "∧": ["constructor", "exact"],
            "∨": ["cases", "rcases"],
            "∃": ["obtain", "rcases"],
            "=": ["rfl", "rw", "simp", "ring"],
            "¬": ["intro", "apply"],
            "↔": ["constructor", "rw"],
        }

        tactics = []
        for symbol, names in suggestions_map.items():
            if symbol in pattern:
                for name in names:
                    if name in cls.TACTICS:
                        tactics.append(cls.TACTICS[name])

        # Añadir tacticas automaticas como fallback
        tactics.extend([
            cls.TACTICS["simp"],
            cls.TACTICS["aesop"],
        ])

        # Eliminar duplicados preservando orden
        seen = set()
        unique = []
        for t in tactics:
            if t.name not in seen:
                seen.add(t.name)
                unique.append(t)

        return unique

    def suggest_tactics(self, goal: str) -> list[str]:
        """
        Sugerir tacticas para un goal (metodo de instancia).

        Args:
            goal: String representando el goal

        Returns:
            Lista de nombres de tacticas sugeridas
        """
        # Mapeo de patrones ASCII a tacticas
        pattern_map = {
            "forall": ["intro", "intros"],
            "->": ["intro", "apply"],
            "/\\": ["constructor"],
            "\\/": ["cases", "rcases"],
            "exists": ["obtain", "rcases"],
            "=": ["rfl", "rw", "simp", "ring"],
            "not": ["intro", "apply"],
            "<->": ["constructor", "rw"],
        }

        suggestions = set()

        for pattern, tactics in pattern_map.items():
            if pattern in goal.lower():
                suggestions.update(tactics)

        # Siempre agregar tacticas automaticas
        suggestions.update(["simp", "aesop"])

        return list(suggestions)
