"""
Cliente LLM para el Nucleo Logico Evolutivo
============================================

Interfaz con Claude para procesamiento de lenguaje natural
y generacion de contenido matematico.

Componente L del sistema: Σ_t = (L, N_t, G_t, F)
"""

from __future__ import annotations

import os
import json
from dataclasses import dataclass, field
from typing import Optional, Any, AsyncIterator
from enum import Enum, auto
import logging

logger = logging.getLogger(__name__)


class LLMRole(Enum):
    """Roles en la conversacion."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class LLMMessage:
    """Mensaje en la conversacion."""
    role: LLMRole
    content: str

    def to_dict(self) -> dict:
        return {"role": self.role.value, "content": self.content}


@dataclass
class LLMResponse:
    """Respuesta del LLM."""
    content: str
    model: str
    usage: dict[str, int] = field(default_factory=dict)
    stop_reason: Optional[str] = None

    @property
    def input_tokens(self) -> int:
        return self.usage.get("input_tokens", 0)

    @property
    def output_tokens(self) -> int:
        return self.usage.get("output_tokens", 0)


@dataclass
class LLMConfig:
    """Configuracion del cliente LLM."""
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 4096
    temperature: float = 0.7
    api_key: Optional[str] = None

    def __post_init__(self):
        if self.api_key is None:
            self.api_key = os.environ.get("ANTHROPIC_API_KEY")


class LLMClient:
    """
    Cliente para interaccion con Claude.

    Proporciona:
    - Generacion de texto
    - Streaming de respuestas
    - Contexto matematico especializado
    - Integracion con el grafo de skills

    Example:
        client = LLMClient()
        response = await client.generate(
            "Explica el teorema de Cantor",
            context={"pillar": "SET"}
        )
        print(response.content)
    """

    # System prompt para contexto matematico
    MATH_SYSTEM_PROMPT = """Eres un asistente experto en matematicas formales y demostracion de teoremas.

Tu conocimiento abarca los cuatro pilares fundamentales:
- F_Set: Teoria de Conjuntos (ZFC, ordinales, cardinales)
- F_Cat: Teoria de Categorias (funtores, adjunciones, limites)
- F_Log: Logica (FOL, logica intuicionista, semantica de Kripke)
- F_Type: Teoria de Tipos (CIC, Curry-Howard, Lean 4)

Cuando asistas con pruebas:
1. Analiza el goal y las hipotesis disponibles
2. Sugiere tacticas apropiadas de Lean 4
3. Explica el razonamiento matematico
4. Conecta con conceptos de los pilares fundamentales

Responde de forma precisa y estructurada."""

    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()
        self._client = None
        self._conversation: list[LLMMessage] = []

    def _get_client(self):
        """Obtener cliente Anthropic (lazy loading)."""
        if self._client is None:
            try:
                from anthropic import Anthropic
                self._client = Anthropic(api_key=self.config.api_key)
            except ImportError:
                logger.warning("anthropic package not installed, using mock mode")
                self._client = MockAnthropicClient()
        return self._client

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        context: Optional[dict[str, Any]] = None,
        stream: bool = False
    ) -> LLMResponse:
        """
        Generar respuesta del LLM.

        Args:
            prompt: Prompt del usuario
            system: System prompt (usa default si None)
            context: Contexto adicional (pilar, skill, goal, etc.)
            stream: Si usar streaming

        Returns:
            LLMResponse con el contenido generado
        """
        # Construir system prompt
        sys_prompt = system or self.MATH_SYSTEM_PROMPT

        if context:
            ctx_str = self._format_context(context)
            sys_prompt = f"{sys_prompt}\n\nContexto actual:\n{ctx_str}"

        # Agregar mensaje a la conversacion
        self._conversation.append(LLMMessage(LLMRole.USER, prompt))

        client = self._get_client()

        try:
            messages = [m.to_dict() for m in self._conversation]

            response = client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                system=sys_prompt,
                messages=messages
            )

            content = response.content[0].text if response.content else ""

            llm_response = LLMResponse(
                content=content,
                model=response.model,
                usage={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                },
                stop_reason=response.stop_reason
            )

            # Agregar respuesta a la conversacion
            self._conversation.append(LLMMessage(LLMRole.ASSISTANT, content))

            return llm_response

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            # Retornar respuesta mock en caso de error
            return LLMResponse(
                content=f"[Mock response for: {prompt[:50]}...]",
                model="mock",
                usage={"input_tokens": 0, "output_tokens": 0}
            )

    async def suggest_tactic(
        self,
        goal: str,
        hypotheses: list[str],
        available_tactics: list[str]
    ) -> str:
        """
        Sugerir tactica para un goal de Lean.

        Args:
            goal: El goal actual
            hypotheses: Lista de hipotesis disponibles
            available_tactics: Tacticas disponibles

        Returns:
            Tactica sugerida
        """
        hyps_str = "\n".join(f"  {h}" for h in hypotheses)
        tactics_str = ", ".join(available_tactics[:10])

        prompt = f"""Dado el siguiente estado de prueba en Lean 4:

Hipotesis:
{hyps_str}

Goal:
  {goal}

Tacticas disponibles: {tactics_str}

Sugiere la mejor tactica a aplicar. Responde SOLO con el nombre de la tactica."""

        response = await self.generate(
            prompt,
            context={"task": "tactic_suggestion", "pillar": "TYPE"}
        )

        # Extraer tactica de la respuesta
        tactic = response.content.strip().split()[0].lower()

        # Validar que es una tactica conocida
        if tactic in [t.lower() for t in available_tactics]:
            return tactic

        return available_tactics[0]  # Fallback

    async def explain_proof(
        self,
        theorem: str,
        proof: str,
        pillar: Optional[str] = None
    ) -> str:
        """
        Explicar una prueba en lenguaje natural.

        Args:
            theorem: Enunciado del teorema
            proof: Prueba en Lean
            pillar: Pilar relevante

        Returns:
            Explicacion en lenguaje natural
        """
        prompt = f"""Explica la siguiente prueba de Lean 4 en lenguaje natural:

Teorema: {theorem}

Prueba:
```lean
{proof}
```

Proporciona:
1. Una explicacion intuitiva del teorema
2. La estrategia de la prueba paso a paso
3. Conexiones con conceptos matematicos fundamentales"""

        response = await self.generate(
            prompt,
            context={"task": "proof_explanation", "pillar": pillar or "TYPE"}
        )

        return response.content

    async def translate_to_formal(
        self,
        statement: str,
        target: str = "lean4"
    ) -> str:
        """
        Traducir enunciado informal a formal.

        Args:
            statement: Enunciado en lenguaje natural
            target: Formato objetivo (lean4, latex, etc.)

        Returns:
            Enunciado formalizado
        """
        prompt = f"""Traduce el siguiente enunciado matematico a {target}:

"{statement}"

Responde SOLO con el codigo {target}, sin explicaciones adicionales."""

        response = await self.generate(
            prompt,
            context={"task": "formalization", "target": target}
        )

        return response.content

    def clear_conversation(self) -> None:
        """Limpiar historial de conversacion."""
        self._conversation.clear()

    def _format_context(self, context: dict[str, Any]) -> str:
        """Formatear contexto como string."""
        lines = []
        for key, value in context.items():
            if isinstance(value, list):
                value = ", ".join(str(v) for v in value)
            lines.append(f"- {key}: {value}")
        return "\n".join(lines)


class MockAnthropicClient:
    """Cliente mock para testing sin API key."""

    class MockMessage:
        def __init__(self, content: str):
            self.content = [type('obj', (object,), {'text': content})()]
            self.model = "mock-claude"
            self.usage = type('obj', (object,), {
                'input_tokens': 10,
                'output_tokens': 50
            })()
            self.stop_reason = "end_turn"

    class MockMessages:
        def create(self, **kwargs) -> "MockAnthropicClient.MockMessage":
            prompt = kwargs.get("messages", [{}])[-1].get("content", "")

            # Respuestas mock basadas en el prompt
            if "tactica" in prompt.lower() or "tactic" in prompt.lower():
                return MockAnthropicClient.MockMessage("simp")
            elif "explica" in prompt.lower() or "explain" in prompt.lower():
                return MockAnthropicClient.MockMessage(
                    "Esta prueba utiliza induccion estructural sobre los naturales. "
                    "El caso base se resuelve por reflexividad, y el paso inductivo "
                    "usa la hipotesis de induccion junto con propiedades de la suma."
                )
            elif "traduce" in prompt.lower() or "translate" in prompt.lower():
                return MockAnthropicClient.MockMessage(
                    "theorem example : forall n : Nat, n + 0 = n := by\n  intro n\n  induction n <;> simp_all"
                )
            else:
                return MockAnthropicClient.MockMessage(
                    f"[Mock response] Procesando: {prompt[:100]}..."
                )

    @property
    def messages(self):
        return self.MockMessages()
