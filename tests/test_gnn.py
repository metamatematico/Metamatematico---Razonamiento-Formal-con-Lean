"""
Tests de GNN y conversion Graph-to-PyG
=======================================

Verifica:
- Conversion correcta de SkillCategory a Data de PyG
- Dimensiones de features de nodos y aristas
- Forward pass del GNN con grafos de diferentes tamanos
- Gradients flow correctamente
"""

import pytest
import torch

from nucleo.types import Skill, MorphismType, PillarType, SkillStatus
from nucleo.graph.category import SkillCategory
from nucleo.rl.gnn import graph_to_pyg, SkillGNN, NODE_FEATURE_DIM, EDGE_FEATURE_DIM


@pytest.fixture
def small_graph():
    """Grafo minimo: 3 skills, 2 aristas."""
    g = SkillCategory(name="TestGNN")
    g.add_skill(Skill(id="s1", name="A", pillar=PillarType.SET, level=0))
    g.add_skill(Skill(id="s2", name="B", pillar=PillarType.LOG, level=0))
    g.add_skill(Skill(id="s3", name="C", pillar=PillarType.SET, level=1, pattern_ids=["p1"]))
    g.add_morphism("s1", "s2", MorphismType.DEPENDENCY)
    g.add_morphism("s2", "s3", MorphismType.SPECIALIZATION, weight=0.5)
    return g


@pytest.fixture
def multi_pillar_graph():
    """Grafo con los 4 pilares y multiples tipos de morfismos."""
    g = SkillCategory(name="MultiPillar")
    g.add_skill(Skill(id="set1", name="ZFC", pillar=PillarType.SET, level=0))
    g.add_skill(Skill(id="cat1", name="Cat", pillar=PillarType.CAT, level=0))
    g.add_skill(Skill(id="log1", name="FOL", pillar=PillarType.LOG, level=0))
    g.add_skill(Skill(id="typ1", name="CIC", pillar=PillarType.TYPE, level=0))
    g.add_skill(Skill(id="adv1", name="Adv", pillar=PillarType.SET, level=2))
    g.add_morphism("set1", "cat1", MorphismType.TRANSLATION)
    g.add_morphism("log1", "typ1", MorphismType.ANALOGY)
    g.add_morphism("set1", "adv1", MorphismType.DEPENDENCY)
    g.add_morphism("cat1", "adv1", MorphismType.SPECIALIZATION)
    return g


class TestGraphToPyG:
    """Tests para la conversion de SkillCategory a PyG Data."""

    def test_node_features_shape(self, small_graph):
        data = graph_to_pyg(small_graph)
        assert data.x.shape == (3, NODE_FEATURE_DIM)

    def test_edge_index_shape(self, small_graph):
        data = graph_to_pyg(small_graph)
        assert data.edge_index.shape[0] == 2
        # 2 aristas no-identidad
        assert data.edge_index.shape[1] == 2

    def test_edge_attr_shape(self, small_graph):
        data = graph_to_pyg(small_graph)
        assert data.edge_attr.shape == (2, EDGE_FEATURE_DIM)

    def test_pillar_one_hot_set(self, small_graph):
        """Nodo s1 tiene pilar SET -> indice 0."""
        data = graph_to_pyg(small_graph)
        # s1 is first skill, pillar SET = index 0
        assert data.x[0, 0] == 1.0  # SET
        assert data.x[0, 1] == 0.0  # CAT
        assert data.x[0, 2] == 0.0  # LOG
        assert data.x[0, 3] == 0.0  # TYPE

    def test_pillar_one_hot_log(self, small_graph):
        """Nodo s2 tiene pilar LOG -> indice 2."""
        data = graph_to_pyg(small_graph)
        assert data.x[1, 0] == 0.0  # SET
        assert data.x[1, 2] == 1.0  # LOG

    def test_is_colimit_flag(self, small_graph):
        """Nodo s3 tiene pattern_ids -> is_colimit = 1."""
        data = graph_to_pyg(small_graph)
        assert data.x[2, 7] == 1.0  # is_colimit
        assert data.x[0, 7] == 0.0  # s1 no es colimite

    def test_is_active_flag(self, small_graph):
        """Skills activos tienen is_active = 1."""
        data = graph_to_pyg(small_graph)
        for i in range(3):
            assert data.x[i, 8] == 1.0  # Todos activos por defecto

    def test_empty_graph(self):
        """Grafo vacio produce Data con tensores vacios."""
        g = SkillCategory(name="Empty")
        data = graph_to_pyg(g)
        assert data.x.shape[0] == 0
        assert data.edge_index.shape[1] == 0
        assert data.edge_attr.shape[0] == 0

    def test_single_node(self):
        """Grafo con un solo nodo (sin aristas no-identidad)."""
        g = SkillCategory(name="Single")
        g.add_skill(Skill(id="s1", name="A", pillar=PillarType.SET, level=0))
        data = graph_to_pyg(g)
        assert data.x.shape == (1, NODE_FEATURE_DIM)
        assert data.edge_index.shape[1] == 0

    def test_multi_pillar_coverage(self, multi_pillar_graph):
        """Grafo con 4 pilares y 4 aristas de diferentes tipos."""
        data = graph_to_pyg(multi_pillar_graph)
        assert data.x.shape == (5, NODE_FEATURE_DIM)
        assert data.edge_index.shape[1] == 4

    def test_edge_weight_encoded(self, small_graph):
        """El peso del morfismo se codifica en edge_attr[5]."""
        data = graph_to_pyg(small_graph)
        # La segunda arista tiene weight=0.5
        assert data.edge_attr[1, 5] == pytest.approx(0.5)

    def test_morphism_type_one_hot(self, small_graph):
        """Tipo de morfismo codificado como one-hot en primeras 5 dims."""
        data = graph_to_pyg(small_graph)
        # Primera arista es DEPENDENCY -> indice 1
        assert data.edge_attr[0, 1] == 1.0
        assert data.edge_attr[0, 0] == 0.0  # No es IDENTITY
        # Segunda arista es SPECIALIZATION -> indice 2
        assert data.edge_attr[1, 2] == 1.0

    def test_identity_morphisms_excluded(self, small_graph):
        """Morfismos identidad no aparecen en edges."""
        data = graph_to_pyg(small_graph)
        # 3 skills generan 3 identidades, pero solo hay 2 aristas
        assert data.edge_index.shape[1] == 2


class TestSkillGNN:
    """Tests para la red GNN."""

    def test_forward_pass(self, small_graph):
        """Forward pass produce embedding de dimension correcta."""
        gnn = SkillGNN(hidden_dim=64, num_layers=2, num_heads=4)
        data = graph_to_pyg(small_graph)
        out = gnn(data)
        assert out.shape == (1, 64)

    def test_gradient_flow(self, small_graph):
        """Los gradientes fluyen a traves de toda la red."""
        gnn = SkillGNN(hidden_dim=64, num_layers=2, num_heads=4)
        data = graph_to_pyg(small_graph)
        out = gnn(data)
        loss = out.sum()
        loss.backward()
        for name, p in gnn.named_parameters():
            assert p.grad is not None, f"No gradient for {name}"

    def test_different_graph_sizes(self):
        """GNN maneja grafos de diferentes tamanos."""
        gnn = SkillGNN(hidden_dim=64, num_layers=2, num_heads=4)
        for n_skills in [2, 5, 10, 20]:
            g = SkillCategory(name=f"G{n_skills}")
            for i in range(n_skills):
                g.add_skill(Skill(
                    id=f"s{i}", name=f"S{i}",
                    pillar=PillarType.SET, level=i % 3
                ))
            if n_skills >= 2:
                g.add_morphism("s0", "s1", MorphismType.DEPENDENCY)
            data = graph_to_pyg(g)
            out = gnn(data)
            assert out.shape == (1, 64)

    def test_empty_graph_returns_zeros(self):
        """Grafo vacio produce embedding de ceros."""
        gnn = SkillGNN(hidden_dim=64, num_layers=2, num_heads=4)
        g = SkillCategory(name="Empty")
        data = graph_to_pyg(g)
        out = gnn(data)
        assert out.shape == (1, 64)
        assert torch.all(out == 0)

    def test_deterministic_output(self, small_graph):
        """Misma entrada produce misma salida (modo eval)."""
        gnn = SkillGNN(hidden_dim=64, num_layers=2, num_heads=4, dropout=0.0)
        gnn.eval()
        data = graph_to_pyg(small_graph)
        out1 = gnn(data)
        out2 = gnn(data)
        assert torch.allclose(out1, out2)

    def test_config_hidden_dim(self):
        """Hidden dim configurable."""
        for dim in [32, 128, 256]:
            gnn = SkillGNN(hidden_dim=dim, num_layers=2, num_heads=4)
            g = SkillCategory(name="T")
            g.add_skill(Skill(id="s1", name="A", pillar=PillarType.SET, level=0))
            g.add_skill(Skill(id="s2", name="B", pillar=PillarType.LOG, level=0))
            g.add_morphism("s1", "s2", MorphismType.DEPENDENCY)
            data = graph_to_pyg(g)
            out = gnn(data)
            assert out.shape == (1, dim)
