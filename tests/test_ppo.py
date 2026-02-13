"""
Tests de PPO y Actor-Critic
=============================

Verifica:
- Encoding de queries y goals
- Actor-Critic forward/backward pass
- PPO update step
- NucleoAgent con red neuronal
- Save/load de pesos del modelo
"""

import pytest
import torch
import os
import tempfile

from nucleo.types import Skill, MorphismType, PillarType, State, Action, ActionType
from nucleo.graph.category import SkillCategory
from nucleo.rl.networks import (
    ActorCriticNetwork, encode_query, encode_goal, VOCAB_SIZE, GOAL_DIM,
)
from nucleo.rl.gnn import graph_to_pyg
from nucleo.rl.agent import NucleoAgent, AgentConfig
from nucleo.rl.mdp import MDP, Transition


@pytest.fixture
def graph():
    """Grafo simple para tests."""
    g = SkillCategory(name="PPOTest")
    g.add_skill(Skill(id="s1", name="A", pillar=PillarType.SET, level=0))
    g.add_skill(Skill(id="s2", name="B", pillar=PillarType.LOG, level=0))
    g.add_skill(Skill(id="s3", name="C", pillar=PillarType.CAT, level=1))
    g.add_morphism("s1", "s2", MorphismType.DEPENDENCY)
    g.add_morphism("s2", "s3", MorphismType.SPECIALIZATION)
    return g


class TestQueryEncoding:
    """Tests para encode_query."""

    def test_shape(self):
        emb = encode_query("prove theorem by induction")
        assert emb.shape == (VOCAB_SIZE,)

    def test_known_keywords(self):
        emb = encode_query("prove theorem")
        assert emb.sum() > 0

    def test_empty_query(self):
        emb = encode_query("")
        assert emb.sum() == 0

    def test_normalized(self):
        emb = encode_query("prove prove prove theorem")
        assert emb.sum() == pytest.approx(1.0)

    def test_unknown_words_go_to_unk(self):
        emb = encode_query("xyz abc")
        # Solo UNK (ultimo indice) debe tener valor
        assert emb[-1] > 0
        assert emb[:-1].sum() == 0


class TestGoalEncoding:
    """Tests para encode_goal."""

    def test_shape(self):
        emb = encode_goal("forall x, x = x")
        assert emb.shape == (GOAL_DIM,)

    def test_empty_goal(self):
        emb = encode_goal("")
        assert torch.all(emb == 0)

    def test_deterministic(self):
        emb1 = encode_goal("forall x, x = x")
        emb2 = encode_goal("forall x, x = x")
        assert torch.allclose(emb1, emb2)

    def test_different_goals_different_embeddings(self):
        emb1 = encode_goal("forall x, x = x")
        emb2 = encode_goal("exists y, y > 0")
        assert not torch.allclose(emb1, emb2)

    def test_normalized(self):
        emb = encode_goal("some goal text")
        # Debe estar normalizado a norma 1
        assert emb.norm() == pytest.approx(1.0, abs=1e-5)


class TestActorCritic:
    """Tests para ActorCriticNetwork."""

    def test_forward(self, graph):
        net = ActorCriticNetwork(hidden_dim=64, gnn_num_layers=2)
        data = graph_to_pyg(graph)
        query = encode_query("prove lemma").unsqueeze(0)
        out = net(data, query)
        assert out.action_logits.shape == (1, 3)
        assert out.value.shape == (1, 1)
        assert out.graph_embedding.shape == (1, 64)

    def test_backward(self, graph):
        net = ActorCriticNetwork(hidden_dim=64, gnn_num_layers=2)
        data = graph_to_pyg(graph)
        query = encode_query("prove").unsqueeze(0)
        out = net(data, query)
        loss = out.action_logits.sum() + out.value.sum()
        loss.backward()
        params_with_grad = sum(1 for p in net.parameters() if p.grad is not None)
        assert params_with_grad > 0

    def test_with_goal(self, graph):
        net = ActorCriticNetwork(hidden_dim=64, gnn_num_layers=2)
        data = graph_to_pyg(graph)
        query = encode_query("prove").unsqueeze(0)
        goal = encode_goal("x = x").unsqueeze(0)
        out = net(data, query, goal_emb=goal)
        assert out.action_logits.shape == (1, 3)
        assert out.value.shape == (1, 1)

    def test_without_goal_different_from_with_goal(self, graph):
        """Resultados cambian cuando se proporciona goal."""
        net = ActorCriticNetwork(hidden_dim=64, gnn_num_layers=2)
        net.eval()
        data = graph_to_pyg(graph)
        query = encode_query("prove").unsqueeze(0)
        goal = encode_goal("forall x, x = x").unsqueeze(0)

        with torch.no_grad():
            out_no_goal = net(data, query)
            out_with_goal = net(data, query, goal_emb=goal)

        # Deben ser diferentes
        assert not torch.allclose(out_no_goal.action_logits, out_with_goal.action_logits)

    def test_num_actions_configurable(self, graph):
        net = ActorCriticNetwork(hidden_dim=64, gnn_num_layers=2, num_actions=5)
        data = graph_to_pyg(graph)
        query = encode_query("prove").unsqueeze(0)
        out = net(data, query)
        assert out.action_logits.shape == (1, 5)


class TestNucleoAgentNeural:
    """Tests para NucleoAgent con red neuronal."""

    def test_agent_with_network(self, graph):
        agent = NucleoAgent(graph, use_neural=True)
        assert agent.has_network

    def test_agent_without_network(self, graph):
        agent = NucleoAgent(graph, use_neural=False)
        assert not agent.has_network

    def test_backward_compatible(self, graph):
        """Sin use_neural, funciona igual que antes."""
        agent = NucleoAgent(graph)
        assert not agent.has_network
        state = State()
        action = agent.select_action(state)
        assert action.action_type in [ActionType.RESPONSE, ActionType.REORGANIZE, ActionType.ASSIST]

    def test_select_action_neural(self, graph):
        agent = NucleoAgent(graph, use_neural=True)
        agent.eval_mode()
        state = State(lean_goal="prove x = x")
        action = agent.select_action(state)
        assert action.action_type in [ActionType.RESPONSE, ActionType.REORGANIZE, ActionType.ASSIST]

    def test_select_action_no_goal(self, graph):
        agent = NucleoAgent(graph, use_neural=True)
        agent.eval_mode()
        state = State()
        action = agent.select_action(state)
        assert action.action_type in [ActionType.RESPONSE, ActionType.REORGANIZE, ActionType.ASSIST]

    def test_ppo_update_runs(self, graph):
        agent = NucleoAgent(
            graph,
            config=AgentConfig(hidden_dim=32, num_layers=1, num_heads=4, n_epochs=2),
            use_neural=True,
        )
        state = State()
        next_state = State()
        transitions = [
            Transition(state=state, action=Action.response("x"), reward=1.0, next_state=next_state),
            Transition(state=state, action=Action.response("y"), reward=0.5, next_state=next_state),
            Transition(state=state, action=Action.reorganize("reweight"), reward=0.1, next_state=next_state),
        ]
        metrics = agent.update(transitions)
        assert "loss" in metrics
        assert metrics["loss"] > 0  # PPO loss deberia ser > 0

    def test_train_episode(self, graph):
        agent = NucleoAgent(
            graph,
            config=AgentConfig(hidden_dim=32, num_layers=1, num_heads=4, n_epochs=2),
            use_neural=True,
        )
        mdp = MDP(graph)
        metrics = agent.train_episode(mdp, max_steps=5)
        assert "episode_reward" in metrics
        assert "episode_length" in metrics
        assert "loss" in metrics
        assert metrics["episode_length"] <= 5

    def test_save_load_with_weights(self, graph):
        agent = NucleoAgent(
            graph,
            config=AgentConfig(hidden_dim=32, num_layers=1, num_heads=4),
            use_neural=True,
        )
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode='w') as f:
            path = f.name

        try:
            agent.save(path)
            assert os.path.exists(path)
            assert os.path.exists(path + ".pt")

            loaded = NucleoAgent.load(path, graph)
            assert loaded.has_network
            assert loaded.epsilon == agent.epsilon
            assert loaded.total_steps == agent.total_steps
        finally:
            os.unlink(path)
            pt_path = path + ".pt"
            if os.path.exists(pt_path):
                os.unlink(pt_path)

    def test_save_load_without_neural(self, graph):
        """Save/load funciona sin red neuronal."""
        agent = NucleoAgent(graph, use_neural=False)
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode='w') as f:
            path = f.name

        try:
            agent.save(path)
            loaded = NucleoAgent.load(path, graph)
            assert not loaded.has_network
        finally:
            os.unlink(path)

    def test_epsilon_decay(self, graph):
        config = AgentConfig(epsilon_start=1.0, epsilon_decay=0.5)
        agent = NucleoAgent(graph, config=config, use_neural=True)
        state = State()
        transitions = [
            Transition(state=state, action=Action.response("x"), reward=1.0, next_state=state),
            Transition(state=state, action=Action.response("y"), reward=1.0, next_state=state),
        ]
        agent.update(transitions)
        assert agent.epsilon < 1.0
