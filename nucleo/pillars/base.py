"""
Base para Pilares Fundacionales
===============================

Clase base abstracta para los cuatro pilares.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from nucleo.types import Skill


@dataclass
class PillarSkill:
    """
    Skill perteneciente a un pilar.

    Representa una unidad de conocimiento dentro
    de un pilar fundacional especifico.
    """
    id: str
    name: str
    description: str
    dependencies: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class Pillar(ABC):
    """
    Clase base abstracta para pilares fundacionales.

    Cada pilar debe implementar:
    - get_skills(): Lista de skills del pilar
    - validate(): Verificar consistencia
    - translate_to(): Traducir a otro pilar
    """

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self._skills: dict[str, PillarSkill] = {}

    @abstractmethod
    def get_skills(self) -> list[PillarSkill]:
        """Obtener todos los skills del pilar."""
        pass

    @abstractmethod
    def validate(self) -> bool:
        """Verificar consistencia interna del pilar."""
        pass

    def get_skill(self, skill_id: str) -> Optional[PillarSkill]:
        """Obtener skill por ID."""
        return self._skills.get(skill_id)

    def add_skill(self, skill: PillarSkill) -> None:
        """Añadir skill al pilar."""
        self._skills[skill.id] = skill

    def get_dependencies(self, skill_id: str) -> list[str]:
        """Obtener dependencias de un skill."""
        skill = self.get_skill(skill_id)
        return skill.dependencies if skill else []


class PillarRegistry:
    """
    Registro global de pilares.

    Mantiene referencia a los cuatro pilares y
    gestiona las traducciones entre ellos.
    """

    def __init__(self):
        self._pillars: dict[str, Pillar] = {}
        self._translations: dict[tuple[str, str], Any] = {}

    def register(self, pillar: Pillar) -> None:
        """Registrar un pilar."""
        self._pillars[pillar.name] = pillar

    def get(self, name: str) -> Optional[Pillar]:
        """Obtener pilar por nombre."""
        return self._pillars.get(name)

    def register_translation(
        self,
        source: str,
        target: str,
        translator: Any
    ) -> None:
        """Registrar traduccion entre pilares."""
        self._translations[(source, target)] = translator

    def translate(
        self,
        source_pillar: str,
        target_pillar: str,
        content: Any
    ) -> Any:
        """
        Traducir contenido entre pilares.

        Args:
            source_pillar: Nombre del pilar origen
            target_pillar: Nombre del pilar destino
            content: Contenido a traducir

        Returns:
            Contenido traducido
        """
        key = (source_pillar, target_pillar)
        if key not in self._translations:
            raise ValueError(
                f"No hay traduccion registrada de {source_pillar} a {target_pillar}"
            )
        translator = self._translations[key]
        return translator(content)

    @property
    def pillar_names(self) -> list[str]:
        """Lista de nombres de pilares registrados."""
        return list(self._pillars.keys())


# Registro global
PILLAR_REGISTRY = PillarRegistry()
