"""
Modulo LLM del Nucleo Logico Evolutivo.

Integracion con Claude para:
- Procesamiento de lenguaje natural
- Generacion de tacticas
- Explicacion de pruebas
"""

from nucleo.llm.client import LLMClient, LLMConfig, LLMResponse
from nucleo.llm.prompts import PromptManager, MathPrompt

__all__ = [
    "LLMClient",
    "LLMConfig",
    "LLMResponse",
    "PromptManager",
    "MathPrompt",
]
