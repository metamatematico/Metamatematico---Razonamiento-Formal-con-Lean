"""
Tests de Tipos Base
===================

Verifica los tipos fundamentales del sistema:
- Skill
- Morphism
- State
- Action
"""

import pytest
from datetime import datetime

from nucleo.types import (
    Skill,
    Morphism,
    MorphismType,
    State,
    Action,
    ActionType,
    PillarType,
    SkillStatus,
    Interaction,
    RewardComponents,
)


class TestSkill:
    """Tests para Skill."""

    def test_skill_creation(self):
        """Crear skill basico."""
        skill = Skill(
            name="test-skill",
            description="A test skill"
        )

        assert skill.name == "test-skill"
        assert skill.description == "A test skill"
        assert skill.id is not None
        assert skill.status == SkillStatus.ACTIVE

    def test_skill_with_pillar(self):
        """Crear skill con pilar asignado."""
        skill = Skill(
            name="type-theory-skill",
            pillar=PillarType.TYPE
        )

        assert skill.pillar == PillarType.TYPE

    def test_skill_equality(self):
        """Skills son iguales si tienen mismo ID."""
        skill1 = Skill(id="same-id", name="Skill 1")
        skill2 = Skill(id="same-id", name="Skill 2")
        skill3 = Skill(id="different-id", name="Skill 1")

        assert skill1 == skill2
        assert skill1 != skill3

    def test_skill_hash(self):
        """Skills pueden usarse en sets/dicts."""
        skill1 = Skill(id="id1", name="Skill 1")
        skill2 = Skill(id="id2", name="Skill 2")

        skill_set = {skill1, skill2}
        assert len(skill_set) == 2


class TestMorphism:
    """Tests para Morphism."""

    def test_morphism_creation(self):
        """Crear morfismo basico."""
        morphism = Morphism(
            source_id="skill-a",
            target_id="skill-b",
            morphism_type=MorphismType.DEPENDENCY,
            weight=1.5
        )

        assert morphism.source_id == "skill-a"
        assert morphism.target_id == "skill-b"
        assert morphism.morphism_type == MorphismType.DEPENDENCY
        assert morphism.weight == 1.5

    def test_morphism_types(self):
        """Verificar tipos de morfismos."""
        assert MorphismType.DEPENDENCY.name == "DEPENDENCY"
        assert MorphismType.SPECIALIZATION.name == "SPECIALIZATION"
        assert MorphismType.ANALOGY.name == "ANALOGY"
        assert MorphismType.TRANSLATION.name == "TRANSLATION"


class TestState:
    """Tests para State."""

    def test_state_creation(self):
        """Crear estado basico."""
        state = State()

        assert state.llm_context is None
        assert state.lean_goal is None
        assert state.history == []
        assert state.has_active_goal is False

    def test_state_with_goal(self):
        """Estado con goal activo."""
        state = State(lean_goal="n + 0 = n")

        assert state.has_active_goal is True
        assert state.lean_goal == "n + 0 = n"

    def test_state_with_history(self):
        """Estado con historial."""
        interaction = Interaction(
            query="Prove n + 0 = n",
            response="Use induction",
            success=True
        )

        state = State(history=[interaction])

        assert len(state.history) == 1
        assert state.history[0].success is True


class TestAction:
    """Tests para Action."""

    def test_response_action(self):
        """Crear accion de respuesta."""
        action = Action.response("Here is the proof...")

        assert action.action_type == ActionType.RESPONSE
        assert action.params["content"] == "Here is the proof..."

    def test_reorganize_action(self):
        """Crear accion de reorganizacion."""
        action = Action.reorganize("merge", skill1="a", skill2="b")

        assert action.action_type == ActionType.REORGANIZE
        assert action.params["operation"] == "merge"

    def test_assist_action(self):
        """Crear accion de asistencia."""
        action = Action.assist(tactic="simp", goal="n + 0 = n")

        assert action.action_type == ActionType.ASSIST
        assert action.params["tactic"] == "simp"


class TestRewardComponents:
    """Tests para RewardComponents."""

    def test_reward_total(self):
        """Calcular recompensa total."""
        rewards = RewardComponents(
            r_task=5.0,
            r_efficiency=-0.5,
            r_organization=0.1,
            r_emergence=1.0
        )

        # Con pesos por defecto: 5 + 0.1*(-0.5) + 0.05*0.1 + 0.2*1.0
        # = 5 - 0.05 + 0.005 + 0.2 = 5.155
        total = rewards.total()

        assert total == pytest.approx(5.155, rel=1e-3)

    def test_reward_custom_weights(self):
        """Calcular recompensa con pesos custom."""
        rewards = RewardComponents(
            r_task=10.0,
            r_efficiency=-1.0,
            r_organization=0.5,
            r_emergence=0.0
        )

        total = rewards.total(lambda_1=0.5, lambda_2=0.5, lambda_3=0.0)
        # 10 + 0.5*(-1) + 0.5*0.5 + 0*0 = 10 - 0.5 + 0.25 = 9.75

        assert total == pytest.approx(9.75, rel=1e-3)
