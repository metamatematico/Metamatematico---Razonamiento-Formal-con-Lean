"""
Prompts Matematicos para el Nucleo
==================================

Coleccion de prompts especializados para:
- Demostracion de teoremas
- Seleccion de tacticas
- Explicacion de conceptos
- Traduccion entre pilares
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Any
from enum import Enum, auto


class PromptType(Enum):
    """Tipos de prompts."""
    TACTIC_SUGGESTION = auto()
    PROOF_EXPLANATION = auto()
    CONCEPT_EXPLANATION = auto()
    FORMALIZATION = auto()
    ERROR_DIAGNOSIS = auto()
    SKILL_RECOMMENDATION = auto()


@dataclass
class MathPrompt:
    """
    Prompt matematico estructurado.

    Attributes:
        type: Tipo de prompt
        template: Template con placeholders
        variables: Variables requeridas
        pillar: Pilar asociado (opcional)
    """
    type: PromptType
    template: str
    variables: list[str] = field(default_factory=list)
    pillar: Optional[str] = None

    def format(self, **kwargs) -> str:
        """Formatear prompt con variables."""
        missing = set(self.variables) - set(kwargs.keys())
        if missing:
            raise ValueError(f"Missing variables: {missing}")
        return self.template.format(**kwargs)


class PromptManager:
    """
    Gestor de prompts matematicos.

    Proporciona prompts predefinidos para diferentes tareas.
    """

    # =========================================================================
    # PROMPTS DE TACTICAS
    # =========================================================================

    TACTIC_SUGGESTION = MathPrompt(
        type=PromptType.TACTIC_SUGGESTION,
        template="""Analiza el siguiente estado de prueba en Lean 4:

## Hipotesis
{hypotheses}

## Goal
{goal}

## Tacticas Disponibles
{tactics}

## Instrucciones
1. Analiza la estructura del goal
2. Considera que tacticas son aplicables
3. Elige la mas apropiada

Responde con:
- **Tactica**: [nombre de la tactica]
- **Razon**: [breve explicacion]""",
        variables=["hypotheses", "goal", "tactics"],
        pillar="TYPE"
    )

    TACTIC_CHAIN = MathPrompt(
        type=PromptType.TACTIC_SUGGESTION,
        template="""Dado el teorema y el estado actual, sugiere una secuencia de tacticas:

## Teorema
{theorem}

## Estado Actual
{state}

## Historial de Tacticas
{history}

Sugiere las proximas 3 tacticas mas probables en orden de prioridad.""",
        variables=["theorem", "state", "history"],
        pillar="TYPE"
    )

    # =========================================================================
    # PROMPTS DE EXPLICACION
    # =========================================================================

    PROOF_EXPLANATION = MathPrompt(
        type=PromptType.PROOF_EXPLANATION,
        template="""Explica la siguiente prueba de forma clara y pedagogica:

## Teorema
{theorem}

## Prueba (Lean 4)
```lean
{proof}
```

## Nivel de Detalle
{detail_level}

Proporciona:
1. **Intuicion**: Que dice el teorema intuitivamente
2. **Estrategia**: Cual es la idea principal de la prueba
3. **Pasos**: Explicacion de cada paso importante
4. **Conexiones**: Relacion con otros conceptos""",
        variables=["theorem", "proof", "detail_level"],
        pillar="TYPE"
    )

    CONCEPT_EXPLANATION = MathPrompt(
        type=PromptType.CONCEPT_EXPLANATION,
        template="""Explica el siguiente concepto matematico:

## Concepto
{concept}

## Pilar
{pillar}

## Contexto
{context}

Incluye:
1. Definicion formal
2. Intuicion
3. Ejemplos
4. Propiedades importantes
5. Conexiones con otros conceptos""",
        variables=["concept", "pillar", "context"]
    )

    # =========================================================================
    # PROMPTS DE FORMALIZACION
    # =========================================================================

    FORMALIZE_STATEMENT = MathPrompt(
        type=PromptType.FORMALIZATION,
        template="""Traduce el siguiente enunciado a Lean 4:

## Enunciado Natural
"{statement}"

## Hints
- Contexto: {context}
- Imports sugeridos: {imports}

Responde con:
```lean
-- Formalizacion
{formalization_placeholder}
```""",
        variables=["statement", "context", "imports", "formalization_placeholder"],
        pillar="TYPE"
    )

    FORMALIZE_PROOF_SKETCH = MathPrompt(
        type=PromptType.FORMALIZATION,
        template="""Dado el siguiente bosquejo de prueba, genera codigo Lean 4:

## Teorema
{theorem}

## Bosquejo de Prueba
{sketch}

## Lemas Disponibles
{lemmas}

Genera una prueba completa en Lean 4.""",
        variables=["theorem", "sketch", "lemmas"],
        pillar="TYPE"
    )

    # =========================================================================
    # PROMPTS DE DIAGNOSTICO
    # =========================================================================

    ERROR_DIAGNOSIS = MathPrompt(
        type=PromptType.ERROR_DIAGNOSIS,
        template="""Analiza el siguiente error de Lean 4:

## Codigo
```lean
{code}
```

## Error
{error}

## Contexto
{context}

Proporciona:
1. **Causa**: Por que ocurre el error
2. **Solucion**: Como corregirlo
3. **Prevencion**: Como evitarlo en el futuro""",
        variables=["code", "error", "context"],
        pillar="TYPE"
    )

    # =========================================================================
    # PROMPTS DE SKILLS
    # =========================================================================

    SKILL_RECOMMENDATION = MathPrompt(
        type=PromptType.SKILL_RECOMMENDATION,
        template="""Dado el objetivo del usuario, recomienda skills relevantes:

## Objetivo
{goal}

## Skills Disponibles
{skills}

## Pilar Preferido
{pillar}

Recomienda hasta 5 skills ordenados por relevancia, con justificacion.""",
        variables=["goal", "skills", "pillar"]
    )

    SKILL_PATH = MathPrompt(
        type=PromptType.SKILL_RECOMMENDATION,
        template="""Diseña un camino de aprendizaje:

## Skill Objetivo
{target_skill}

## Skills Actuales
{current_skills}

## Grafo de Dependencias
{dependencies}

Sugiere el camino optimo de skills a dominar.""",
        variables=["target_skill", "current_skills", "dependencies"]
    )

    # =========================================================================
    # PROMPTS ENTRE PILARES (Curry-Howard)
    # =========================================================================

    CURRY_HOWARD_TRANSLATE = MathPrompt(
        type=PromptType.FORMALIZATION,
        template="""Traduce usando la correspondencia Curry-Howard:

## Direccion
{direction}  # "logic_to_type" o "type_to_logic"

## Entrada
{input}

## Tabla de Correspondencia
- Proposicion <-> Tipo
- Prueba <-> Termino
- P -> Q <-> Funcion P -> Q
- P /\\ Q <-> Producto P x Q
- P \\/ Q <-> Suma P + Q
- forall x. P(x) <-> (x : A) -> P x
- exists x. P(x) <-> Sigma (x : A), P x

Proporciona la traduccion con explicacion.""",
        variables=["direction", "input"],
        pillar="TYPE"
    )

    # =========================================================================
    # METODOS
    # =========================================================================

    @classmethod
    def get_prompt(cls, prompt_type: PromptType) -> list[MathPrompt]:
        """Obtener prompts de un tipo."""
        prompts = []
        for name in dir(cls):
            attr = getattr(cls, name)
            if isinstance(attr, MathPrompt) and attr.type == prompt_type:
                prompts.append(attr)
        return prompts

    @classmethod
    def all_prompts(cls) -> list[MathPrompt]:
        """Obtener todos los prompts."""
        prompts = []
        for name in dir(cls):
            attr = getattr(cls, name)
            if isinstance(attr, MathPrompt):
                prompts.append(attr)
        return prompts
