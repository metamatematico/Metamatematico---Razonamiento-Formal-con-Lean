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


class LLMProvider(Enum):
    """Proveedor de LLM soportado."""
    ANTHROPIC = "anthropic"
    GOOGLE    = "google"
    GROQ      = "groq"
    DEMO      = "demo"


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
    model: str = "claude-sonnet-4-6"
    max_tokens: int = 4096
    temperature: float = 0.7
    api_key: Optional[str] = None
    provider: LLMProvider = LLMProvider.ANTHROPIC

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

    # System prompt general: respuestas educativas en lenguaje natural
    MATH_SYSTEM_PROMPT = """Eres un asistente experto en matemáticas, claro y didáctico.

Responde siempre en lenguaje natural accesible. Cuando expliques un concepto o resultado:
- Comienza con la intuición o idea central.
- Da una explicación paso a paso.
- Usa ejemplos concretos cuando ayuden.
- Señala conexiones con otros conceptos matemáticos relevantes.

No incluyas código Lean 4 ni tácticas de demostración formal a menos que el usuario
lo pida explícitamente. Responde en el mismo idioma que el usuario."""

    # System prompt para modo Lean/formalización (usado en _assist_lean)
    LEAN_SYSTEM_PROMPT = """Eres un experto en Lean 4 y matemáticas formales.

Tu conocimiento cubre los cuatro pilares: Teoría de Conjuntos (ZFC), Teoría de
Categorías, Lógica Formal y Teoría de Tipos (CIC, Curry-Howard).

Cuando expliques código Lean 4:
- Traduce cada táctica a lenguaje matemático natural.
- Explica la estrategia de demostración de forma didáctica.
- Señala por qué cada paso es matemáticamente válido.

Responde en el mismo idioma que el usuario."""

    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()
        self._client = None
        self._conversation: list[LLMMessage] = []

    @property
    def is_demo(self) -> bool:
        """True si el cliente está en modo demo (sin API key real)."""
        if self.config.provider == LLMProvider.DEMO:
            return True
        # Sin API key efectiva → modo demo implícito
        if self.config.provider == LLMProvider.ANTHROPIC and not self.config.api_key:
            return True
        return False

    def reconfigure(
        self,
        provider: "LLMProvider",
        model: str,
        api_key: str,
        max_tokens: int = 1024,
    ) -> None:
        """Cambiar proveedor/modelo/key en caliente (llamado desde Streamlit)."""
        prev_provider = self.config.provider
        self.config.provider  = provider
        self.config.model     = model
        self.config.api_key   = api_key or self.config.api_key
        self.config.max_tokens = max_tokens
        self._client = None  # forzar re-init del cliente
        # Si cambia el proveedor, limpiar conversacion (formatos incompatibles)
        if provider != prev_provider:
            self._conversation.clear()

    def _get_client(self):
        """Obtener cliente según provider (lazy loading)."""
        if self._client is not None:
            return self._client

        provider = self.config.provider

        if provider == LLMProvider.DEMO:
            self._client = DemoLLMClient()

        elif provider == LLMProvider.ANTHROPIC:
            try:
                from anthropic import Anthropic
                self._client = Anthropic(api_key=self.config.api_key)
            except ImportError:
                logger.warning("anthropic not installed, using demo mode")
                self._client = DemoLLMClient()

        elif provider == LLMProvider.GOOGLE:
            try:
                from google import genai
                self._client = genai.Client(api_key=self.config.api_key)
            except ImportError:
                logger.warning("google-genai not installed, using demo mode")
                self._client = DemoLLMClient()

        elif provider == LLMProvider.GROQ:
            try:
                from groq import Groq
                self._client = Groq(api_key=self.config.api_key)
            except ImportError:
                logger.warning("groq not installed, using demo mode")
                self._client = DemoLLMClient()

        else:
            self._client = DemoLLMClient()

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

        provider = self.config.provider
        client   = self._get_client()

        try:
            content = ""
            model_name = self.config.model
            in_tok = out_tok = 0

            if provider == LLMProvider.ANTHROPIC:
                messages = [m.to_dict() for m in self._conversation]
                resp = client.messages.create(
                    model=model_name,
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature,
                    system=sys_prompt,
                    messages=messages,
                )
                content = resp.content[0].text if resp.content else ""
                in_tok  = resp.usage.input_tokens
                out_tok = resp.usage.output_tokens
                model_name = resp.model

            elif provider == LLMProvider.GOOGLE:
                from google.genai import types as gtypes
                # Multi-turn para Gemini: convertir _conversation a formato contents
                contents = []
                for msg in self._conversation:
                    role = "user" if msg.role == LLMRole.USER else "model"
                    contents.append({"role": role, "parts": [{"text": msg.content}]})
                resp = client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=gtypes.GenerateContentConfig(
                        system_instruction=sys_prompt,
                        max_output_tokens=self.config.max_tokens,
                        temperature=self.config.temperature,
                    ),
                )
                content = resp.text or ""

            elif provider == LLMProvider.GROQ:
                messages = [{"role": "system", "content": sys_prompt}] + \
                           [m.to_dict() for m in self._conversation]
                resp = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    max_tokens=self.config.max_tokens,
                    temperature=self.config.temperature,
                )
                content = resp.choices[0].message.content or ""
                if resp.usage:
                    in_tok  = resp.usage.prompt_tokens
                    out_tok = resp.usage.completion_tokens

            else:  # DEMO
                content = client.generate(prompt, sys_prompt)

            llm_response = LLMResponse(
                content=content,
                model=model_name,
                usage={"input_tokens": in_tok, "output_tokens": out_tok},
            )

            # Agregar respuesta a la conversacion
            self._conversation.append(LLMMessage(LLMRole.ASSISTANT, content))
            return llm_response

        except Exception as e:
            # Rollback: quitar el mensaje del usuario para mantener la conversacion
            # en estado valido (evita mensajes consecutivos del mismo rol).
            if self._conversation and self._conversation[-1].role == LLMRole.USER:
                self._conversation.pop()
            logger.error(f"Error generating response ({provider.value}): {e}")
            raise  # Re-raise para que process_sync() lo capture y lo muestre

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


class DemoLLMClient:
    """Cliente demo para modo sin API key."""

    def generate(self, prompt: str, system: str = "") -> str:
        p = prompt.lower()
        if "tactica" in p or "tactic" in p:
            return "simp"
        if "explica" in p or "explain" in p:
            return (
                "Esta prueba utiliza inducción estructural sobre los naturales. "
                "El caso base se resuelve por reflexividad, y el paso inductivo "
                "usa la hipótesis de inducción junto con propiedades de la suma."
            )
        if "traduce" in p or "translate" in p:
            return (
                "theorem example : ∀ n : Nat, n + 0 = n := by\n"
                "  intro n\n  induction n <;> simp_all"
            )
        return f"[Demo] Procesando: {prompt[:120]}…"


# Alias para compatibilidad con tests existentes
MockAnthropicClient = DemoLLMClient
