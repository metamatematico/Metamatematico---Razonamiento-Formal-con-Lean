"""
Tests de Pilares Fundacionales
==============================

Verifica los cuatro pilares:
- F_Set: Teoria de Conjuntos
- F_Cat: Teoria de Categorias
- F_Log: Logica
- F_Type: Teoria de Tipos
"""

import pytest

from nucleo.pillars.base import Pillar, PillarRegistry
from nucleo.pillars.type_theory import (
    TypeTheoryPillar,
    Type,
    Universe,
    CurryHoward,
    PROP,
    TYPE_0,
)
from nucleo.pillars.logic import (
    LogicPillar,
    LogicSystem,
    Term,
    Formula,
    Connective,
)
from nucleo.pillars.category_theory import (
    CategoryTheoryPillar,
    Category,
    CategoryObject,
    CategoryMorphism,
)
from nucleo.pillars.set_theory import (
    SetTheoryPillar,
    ZFCAxiom,
    ZFCSet,
    EMPTY_SET,
)


class TestTypeTheoryPillar:
    """Tests para F_Type."""

    @pytest.fixture
    def pillar(self):
        return TypeTheoryPillar()

    def test_pillar_creation(self, pillar):
        """Crear pilar de teoria de tipos."""
        assert pillar.name == "F_Type"
        assert len(pillar.get_skills()) > 0

    def test_skills_exist(self, pillar):
        """Skills basicos existen."""
        skill_ids = [s.id for s in pillar.get_skills()]

        assert "cic" in skill_ids
        assert "curry-howard" in skill_ids
        assert "lean-kernel" in skill_ids

    def test_validation(self, pillar):
        """Pilar es valido."""
        assert pillar.validate() is True

    def test_universe_ordering(self):
        """Orden de universos."""
        assert PROP < TYPE_0
        assert TYPE_0 < Universe(level=1)

    def test_curry_howard_implication(self):
        """Curry-Howard: implicacion a funcion."""
        a = Type(name="A")
        b = Type(name="B")

        arrow = CurryHoward.implication_to_function(a, b)

        assert arrow.name == "Arrow"
        assert len(arrow.params) == 2

    def test_translate_to_lean(self, pillar):
        """Traducir tipo a Lean."""
        a = Type(name="Nat")
        b = Type(name="Nat")

        arrow = CurryHoward.implication_to_function(a, b)
        lean_code = pillar.translate_to_lean(arrow)

        assert "→" in lean_code
        assert "Nat" in lean_code


class TestLogicPillar:
    """Tests para F_Log."""

    @pytest.fixture
    def pillar(self):
        return LogicPillar()

    def test_pillar_creation(self, pillar):
        """Crear pilar de logica."""
        assert pillar.name == "F_Log"

    def test_fol_skills_exist(self, pillar):
        """Skills de FOL existen."""
        skill_ids = [s.id for s in pillar.get_skills()]

        assert "fol-syntax" in skill_ids
        assert "fol-semantics" in skill_ids
        assert "intuitionistic" in skill_ids

    def test_metalogical_properties_fol(self, pillar):
        """Propiedades metalogicas de FOL."""
        props = pillar.check_metalogical_properties(LogicSystem.FOL)

        assert props["completeness"] is True
        assert props["compactness"] is True
        assert props["semi_decidable"] is True

    def test_metalogical_properties_sol_std(self, pillar):
        """Propiedades perdidas en SOL estandar."""
        props = pillar.check_metalogical_properties(LogicSystem.SOL_STD)

        # Perdidas metalogicas!
        assert props["completeness"] is False
        assert props["compactness"] is False

    def test_metalogical_properties_il(self, pillar):
        """Propiedades de IL."""
        props = pillar.check_metalogical_properties(LogicSystem.IL)

        assert props["completeness"] is True
        assert props["lem"] is False  # No LEM
        assert props["program_extraction"] is True

    def test_formula_creation(self):
        """Crear formulas."""
        x = Term.var("x")
        y = Term.var("y")

        eq = Formula.equals(x, y)
        assert "=" in str(eq)

        forall = Formula.forall("x", eq)
        assert "∀" in str(forall)

    def test_implication_formula(self):
        """Crear implicacion."""
        p = Formula.atomic("P", Term.var("x"))
        q = Formula.atomic("Q", Term.var("x"))

        impl = Formula.implies(p, q)

        assert impl.connective == Connective.IMPLIES


class TestCategoryTheoryPillar:
    """Tests para F_Cat."""

    @pytest.fixture
    def pillar(self):
        return CategoryTheoryPillar()

    def test_pillar_creation(self, pillar):
        """Crear pilar de teoria de categorias."""
        assert pillar.name == "F_Cat"

    def test_skills_exist(self, pillar):
        """Skills basicos existen."""
        skill_ids = [s.id for s in pillar.get_skills()]

        assert "cat-basics" in skill_ids
        assert "functors" in skill_ids
        assert "topos-basics" in skill_ids

    def test_category_creation(self):
        """Crear categoria simple."""
        cat = Category(name="TestCat")

        a = CategoryObject(id="a", name="A")
        b = CategoryObject(id="b", name="B")

        cat.add_object(a)
        cat.add_object(b)

        assert len(cat.objects) == 2

    def test_category_morphism(self):
        """Crear morfismo en categoria."""
        cat = Category()

        a = CategoryObject(id="a", name="A")
        b = CategoryObject(id="b", name="B")

        cat.add_object(a)
        cat.add_object(b)

        f = CategoryMorphism(id="f", source=a, target=b, name="f")
        cat.add_morphism(f)

        assert len(cat.hom(a, b)) == 1


class TestSetTheoryPillar:
    """Tests para F_Set."""

    @pytest.fixture
    def pillar(self):
        return SetTheoryPillar()

    def test_pillar_creation(self, pillar):
        """Crear pilar de teoria de conjuntos."""
        assert pillar.name == "F_Set"

    def test_skills_exist(self, pillar):
        """Skills basicos existen."""
        skill_ids = [s.id for s in pillar.get_skills()]

        assert "zfc-axioms" in skill_ids
        assert "ordinals" in skill_ids
        assert "cardinals" in skill_ids

    def test_empty_set(self):
        """Conjunto vacio."""
        assert str(EMPTY_SET) == "∅"
        assert len(EMPTY_SET.elements) == 0

    def test_set_equality(self):
        """Extensionalidad: conjuntos iguales si mismos elementos."""
        s1 = ZFCSet(name="A", elements=frozenset({"x", "y"}))
        s2 = ZFCSet(name="B", elements=frozenset({"x", "y"}))
        s3 = ZFCSet(name="C", elements=frozenset({"x"}))

        assert s1 == s2
        assert s1 != s3

    def test_axiom_description(self, pillar):
        """Obtener descripcion de axioma."""
        desc = pillar.describe_axiom(ZFCAxiom.EXTENSIONALITY)

        assert "∀A" in desc
        assert "∀B" in desc


class TestPillarRegistry:
    """Tests para PillarRegistry."""

    def test_register_pillars(self):
        """Registrar pilares."""
        registry = PillarRegistry()

        registry.register(TypeTheoryPillar())
        registry.register(LogicPillar())

        assert "F_Type" in registry.pillar_names
        assert "F_Log" in registry.pillar_names

    def test_get_pillar(self):
        """Obtener pilar por nombre."""
        registry = PillarRegistry()
        pillar = TypeTheoryPillar()

        registry.register(pillar)

        retrieved = registry.get("F_Type")
        assert retrieved is pillar
