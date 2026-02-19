"""
Tests del Grafo Categorico
==========================

Verifica:
- Operaciones CRUD de skills y morfismos
- Axiomas categoricos
- Operaciones atomicas (merge, split, reweight)
"""

import pytest

from nucleo.types import Skill, MorphismType, PillarType
from nucleo.graph.category import SkillCategory
from nucleo.graph.operations import GraphOperations


class TestSkillCategory:
    """Tests para SkillCategory."""

    @pytest.fixture
    def empty_graph(self):
        """Grafo vacio."""
        return SkillCategory(name="TestGraph")

    @pytest.fixture
    def simple_graph(self):
        """Grafo con 3 skills conectados."""
        graph = SkillCategory(name="SimpleGraph")

        # Crear skills
        s1 = Skill(id="s1", name="Skill 1", pillar=PillarType.TYPE)
        s2 = Skill(id="s2", name="Skill 2", pillar=PillarType.TYPE)
        s3 = Skill(id="s3", name="Skill 3", pillar=PillarType.LOG)

        graph.add_skill(s1)
        graph.add_skill(s2)
        graph.add_skill(s3)

        # Crear morfismos: s1 -> s2 -> s3
        graph.add_morphism("s1", "s2", MorphismType.DEPENDENCY, weight=1.0)
        graph.add_morphism("s2", "s3", MorphismType.DEPENDENCY, weight=0.8)

        return graph

    def test_add_skill(self, empty_graph):
        """Añadir skill al grafo."""
        skill = Skill(name="New Skill")
        empty_graph.add_skill(skill)

        assert skill.id in empty_graph.skill_ids
        assert empty_graph.stats["num_skills"] == 1

    def test_identity_morphism_created(self, empty_graph):
        """Identidad se crea automaticamente."""
        skill = Skill(id="test", name="Test")
        empty_graph.add_skill(skill)

        identity = empty_graph.identity("test")
        assert identity is not None
        assert identity.source_id == "test"
        assert identity.target_id == "test"

    def test_add_morphism(self, empty_graph):
        """Añadir morfismo entre skills."""
        s1 = Skill(id="s1", name="Skill 1")
        s2 = Skill(id="s2", name="Skill 2")

        empty_graph.add_skill(s1)
        empty_graph.add_skill(s2)

        morphism = empty_graph.add_morphism(
            "s1", "s2",
            MorphismType.DEPENDENCY,
            weight=1.5
        )

        assert morphism is not None
        assert morphism.weight == 1.5

    def test_hom_set(self, simple_graph):
        """Obtener Hom(s, t)."""
        hom = simple_graph.hom("s1", "s2")

        assert len(hom) == 1
        assert hom[0].morphism_type == MorphismType.DEPENDENCY

    def test_composition(self, simple_graph):
        """Componer morfismos."""
        # Obtener f: s1 -> s2 y g: s2 -> s3
        f = simple_graph.hom("s1", "s2")[0]
        g = simple_graph.hom("s2", "s3")[0]

        # Componer g ∘ f: s1 -> s3
        composed = simple_graph.compose(g.id, f.id)

        assert composed is not None
        assert composed.source_id == "s1"
        assert composed.target_id == "s3"
        assert composed.weight == pytest.approx(0.8, rel=1e-3)  # 1.0 * 0.8

    def test_neighbors(self, simple_graph):
        """Obtener vecinos de un skill."""
        neighbors = simple_graph.neighbors("s2")

        assert "s1" in neighbors
        assert "s3" in neighbors
        assert len(neighbors) == 2

    def test_dependencies(self, simple_graph):
        """Obtener dependencias."""
        deps = simple_graph.dependencies("s2")

        assert "s1" in deps

    def test_is_connected(self, simple_graph):
        """Verificar conectividad."""
        assert simple_graph.is_connected() is True

    def test_reweight(self, simple_graph):
        """Actualizar peso de morfismo."""
        morphism = simple_graph.hom("s1", "s2")[0]
        old_weight = morphism.weight

        simple_graph.reweight(morphism.id, 2.0)

        assert morphism.weight == 2.0
        assert morphism.weight != old_weight

    def test_serialization(self, simple_graph):
        """Serializar grafo a dict/JSON."""
        data = simple_graph.to_dict()

        assert data["name"] == "SimpleGraph"
        assert len(data["skills"]) == 3
        assert data["stats"]["num_skills"] == 3


class TestGraphOperations:
    """Tests para GraphOperations."""

    @pytest.fixture
    def graph(self):
        """Grafo para operaciones."""
        return SkillCategory(name="OpTestGraph")

    def test_add_node(self, graph):
        """Operacion add_node."""
        result = GraphOperations.add_node(
            graph,
            name="New Skill",
            description="A new skill",
            pillar=PillarType.SET
        )

        assert result.success is True
        assert len(result.affected_skills) == 1
        assert graph.stats["num_skills"] == 1

    def test_add_edge(self, graph):
        """Operacion add_edge."""
        # Crear dos skills
        GraphOperations.add_node(graph, name="Skill A")
        GraphOperations.add_node(graph, name="Skill B")

        s1, s2 = graph.skill_ids[0], graph.skill_ids[1]

        result = GraphOperations.add_edge(
            graph, s1, s2,
            MorphismType.DEPENDENCY,
            weight=1.0
        )

        assert result.success is True
        assert len(result.affected_morphisms) == 1

    def test_merge(self, graph):
        """Operacion merge."""
        # Crear skills
        r1 = GraphOperations.add_node(graph, name="Skill A")
        r2 = GraphOperations.add_node(graph, name="Skill B")
        r3 = GraphOperations.add_node(graph, name="Skill C")

        s1, s2, s3 = graph.skill_ids[:3]

        # Conectar: C -> A, C -> B
        GraphOperations.add_edge(graph, s3, s1, MorphismType.DEPENDENCY)
        GraphOperations.add_edge(graph, s3, s2, MorphismType.DEPENDENCY)

        # Merge A y B
        result = GraphOperations.merge(graph, s1, s2, new_name="AB")

        assert result.success is True
        assert "AB" in result.message
        assert graph.stats["num_skills"] == 2  # C y AB

    def test_reweight_operation(self, graph):
        """Operacion reweight."""
        GraphOperations.add_node(graph, name="A")
        GraphOperations.add_node(graph, name="B")

        s1, s2 = graph.skill_ids[:2]
        result = GraphOperations.add_edge(graph, s1, s2)

        mor_id = result.affected_morphisms[0]

        # Reweight
        result = GraphOperations.reweight(graph, mor_id, 5.0)

        assert result.success is True
        assert graph.get_morphism(mor_id).weight == 5.0


class TestCategoryAxioms:
    """Tests para axiomas categoricos."""

    @pytest.fixture
    def graph(self):
        """Grafo para verificar axiomas."""
        g = SkillCategory()

        # Crear skills
        for name in ["A", "B", "C", "D"]:
            g.add_skill(Skill(id=name, name=name))

        # Crear morfismos: A -> B -> C -> D
        g.add_morphism("A", "B", MorphismType.DEPENDENCY)
        g.add_morphism("B", "C", MorphismType.DEPENDENCY)
        g.add_morphism("C", "D", MorphismType.DEPENDENCY)

        return g

    def test_identity_exists(self, graph):
        """Cada objeto tiene identidad."""
        for skill_id in graph.skill_ids:
            identity = graph.identity(skill_id)
            assert identity is not None
            assert identity.source_id == skill_id
            assert identity.target_id == skill_id

    def test_verify_axioms(self, graph):
        """Verificar axiomas."""
        results = graph.verify_axioms()

        assert results["identities_exist"] is True
