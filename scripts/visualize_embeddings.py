"""
Visualizacion de Embeddings del Grafo Categorico de Skills
===========================================================

Muestra como la GNN organiza los skills en el espacio latente:
1. Grafo categorico coloreado por pilar
2. Embeddings GNN proyectados a 2D via t-SNE
3. Embeddings por categoria de dominio

Uso:
    python scripts/visualize_embeddings.py
"""

import torch
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch
from sklearn.manifold import TSNE
from collections import defaultdict

from nucleo.types import Skill, MorphismType, PillarType
from nucleo.graph.category import SkillCategory
from nucleo.pillars.math_domains import (
    load_math_domains, ALL_DOMAIN_SKILLS,
    LEAN_TACTICS_SKILLS, PROOF_STRATEGY_SKILLS,
)
from nucleo.rl.gnn import graph_to_pyg, SkillGNN, NODE_FEATURE_DIM


# Colores por pilar
PILLAR_COLORS = {
    PillarType.SET: "#E74C3C",   # rojo
    PillarType.CAT: "#3498DB",   # azul
    PillarType.LOG: "#2ECC71",   # verde
    PillarType.TYPE: "#F39C12",  # naranja
}

PILLAR_LABELS = {
    PillarType.SET: "SET (Conjuntos)",
    PillarType.CAT: "CAT (Categorias)",
    PillarType.LOG: "LOG (Logica)",
    PillarType.TYPE: "TYPE (Tipos)",
}

# Categorias especiales
CATEGORY_MARKERS = {
    "lean-tactics": "^",      # triangulo
    "proof-strategies": "s",  # cuadrado
}


def build_full_graph() -> SkillCategory:
    """Construir grafo completo con fundaciones + dominios."""
    g = SkillCategory(name="NLE_v7")

    # Foundational skills (L0)
    foundations = [
        ("zfc-axioms", "ZFC Axioms", PillarType.SET),
        ("ordinals", "Ordinals", PillarType.SET),
        ("category-basics", "Category Basics", PillarType.CAT),
        ("functors", "Functors", PillarType.CAT),
        ("nat-trans", "Natural Trans", PillarType.CAT),
        ("limits", "Limits", PillarType.CAT),
        ("fol-deduction", "FOL Deduction", PillarType.LOG),
        ("fol-metatheory", "FOL Metatheory", PillarType.LOG),
        ("type-theory", "Type Theory", PillarType.TYPE),
        ("cic", "CIC", PillarType.TYPE),
        ("lean-kernel", "Lean Kernel", PillarType.TYPE),
    ]
    for sid, name, pillar in foundations:
        g.add_skill(Skill(id=sid, name=name, pillar=pillar, level=0))

    # Foundation morphisms
    g.add_morphism("zfc-axioms", "category-basics", MorphismType.ANALOGY)
    g.add_morphism("fol-deduction", "cic", MorphismType.TRANSLATION)
    g.add_morphism("category-basics", "functors", MorphismType.DEPENDENCY)
    g.add_morphism("functors", "nat-trans", MorphismType.DEPENDENCY)
    g.add_morphism("functors", "limits", MorphismType.DEPENDENCY)
    g.add_morphism("cic", "lean-kernel", MorphismType.DEPENDENCY)
    g.add_morphism("fol-deduction", "fol-metatheory", MorphismType.DEPENDENCY)
    g.add_morphism("type-theory", "cic", MorphismType.DEPENDENCY)

    # Load domain skills
    stats = load_math_domains(g)
    print(f"Grafo construido: {len(g.skills)} skills, {stats}")
    return g


def get_node_embeddings(graph: SkillCategory, gnn: SkillGNN) -> np.ndarray:
    """
    Obtener embedding individual de cada nodo (no solo el global).

    Hace forward pass hasta antes del global pooling.
    """
    data = graph_to_pyg(graph)
    if data.x.size(0) == 0:
        return np.zeros((0, gnn.hidden_dim))

    gnn.eval()
    with torch.no_grad():
        x = gnn.input_proj(data.x)
        for conv, norm in zip(gnn.convs, gnn.norms):
            x_res = x
            x = conv(x, data.edge_index, edge_attr=data.edge_attr)
            x = norm(x + x_res)
            x = torch.relu(x)

    return x.numpy()


def get_skill_metadata(graph: SkillCategory) -> list[dict]:
    """Extraer metadata de cada skill para colorear."""
    domain_map = {s.id: s for s in ALL_DOMAIN_SKILLS}
    result = []
    for skill in graph.skills:
        info = {
            "id": skill.id,
            "name": skill.name,
            "pillar": skill.pillar or PillarType.SET,
            "level": skill.level,
            "category": "foundation",
        }
        if skill.id in domain_map:
            info["category"] = domain_map[skill.id].category
        result.append(info)
    return result


def plot_graph_structure(graph: SkillCategory, ax, metadata: list[dict]):
    """Visualizar estructura del grafo categorico."""
    import networkx as nx

    G = nx.DiGraph()

    # Agregar nodos
    for i, info in enumerate(metadata):
        G.add_node(info["id"], **info)

    # Agregar aristas (sin identidades)
    for m in graph.morphisms:
        if m.morphism_type == MorphismType.IDENTITY:
            continue
        if m.source_id in G.nodes and m.target_id in G.nodes:
            G.add_edge(m.source_id, m.target_id, type=m.morphism_type.name)

    # Layout
    pos = nx.spring_layout(G, k=2.5, iterations=80, seed=42)

    # Dibujar aristas
    nx.draw_networkx_edges(
        G, pos, ax=ax,
        edge_color="#CCCCCC", alpha=0.3,
        arrows=True, arrowsize=8,
        connectionstyle="arc3,rad=0.1",
    )

    # Dibujar nodos por pilar
    for pillar, color in PILLAR_COLORS.items():
        nodes = [info["id"] for info in metadata if info["pillar"] == pillar]
        if not nodes:
            continue

        # Separar por categoria especial
        normal = [n for n in nodes if metadata[list(G.nodes).index(n)]["category"] not in CATEGORY_MARKERS]
        for cat, marker in CATEGORY_MARKERS.items():
            special = [n for n in nodes if n in G.nodes and metadata[list(G.nodes).index(n)]["category"] == cat]
            if special:
                nx.draw_networkx_nodes(
                    G, pos, nodelist=special, ax=ax,
                    node_color=color, node_size=120,
                    node_shape=marker, edgecolors="black", linewidths=0.5,
                )
        if normal:
            nx.draw_networkx_nodes(
                G, pos, nodelist=normal, ax=ax,
                node_color=color, node_size=80,
                edgecolors="black", linewidths=0.3,
            )

    # Labels solo para foundaciones
    foundation_labels = {info["id"]: info["name"] for info in metadata if info["level"] == 0}
    nx.draw_networkx_labels(
        G, pos, labels=foundation_labels, ax=ax,
        font_size=5, font_weight="bold",
    )

    ax.set_title("Grafo Categorico de Skills (76 nodos)", fontsize=12, fontweight="bold")

    # Leyenda
    for pillar, color in PILLAR_COLORS.items():
        ax.scatter([], [], c=color, s=60, label=PILLAR_LABELS[pillar])
    ax.scatter([], [], c="gray", s=60, marker="^", label="Lean Tactics")
    ax.scatter([], [], c="gray", s=60, marker="s", label="Proof Strategies")
    ax.legend(loc="lower left", fontsize=7, ncol=2)


def plot_embeddings_tsne(embeddings: np.ndarray, metadata: list[dict], ax):
    """Proyectar embeddings a 2D con t-SNE y visualizar."""
    if len(embeddings) < 5:
        ax.text(0.5, 0.5, "Muy pocos nodos", ha="center", va="center")
        return

    tsne = TSNE(n_components=2, perplexity=min(15, len(embeddings) - 1),
                random_state=42, n_iter=1000)
    coords = tsne.fit_transform(embeddings)

    # Colorear por pilar
    for pillar, color in PILLAR_COLORS.items():
        mask = [i for i, info in enumerate(metadata) if info["pillar"] == pillar]
        if not mask:
            continue
        pts = coords[mask]

        # Separar categorias especiales
        for cat, marker in CATEGORY_MARKERS.items():
            cat_mask = [j for j in range(len(mask)) if metadata[mask[j]]["category"] == cat]
            if cat_mask:
                ax.scatter(
                    pts[cat_mask, 0], pts[cat_mask, 1],
                    c=color, s=100, marker=marker, edgecolors="black",
                    linewidths=0.5, zorder=3,
                )

        normal_mask = [j for j in range(len(mask)) if metadata[mask[j]]["category"] not in CATEGORY_MARKERS]
        if normal_mask:
            ax.scatter(
                pts[normal_mask, 0], pts[normal_mask, 1],
                c=color, s=50, edgecolors="black", linewidths=0.3,
                zorder=2,
            )

    # Anotar foundaciones
    for i, info in enumerate(metadata):
        if info["level"] == 0:
            ax.annotate(
                info["name"], (coords[i, 0], coords[i, 1]),
                fontsize=5, fontweight="bold",
                xytext=(3, 3), textcoords="offset points",
            )

    # Anotar lean tactics
    for i, info in enumerate(metadata):
        if info["category"] in ("lean-tactics", "proof-strategies"):
            ax.annotate(
                info["name"], (coords[i, 0], coords[i, 1]),
                fontsize=4, color="gray",
                xytext=(3, -3), textcoords="offset points",
            )

    ax.set_title("GNN Embeddings (t-SNE 2D)", fontsize=12, fontweight="bold")
    ax.set_xlabel("t-SNE dim 1", fontsize=8)
    ax.set_ylabel("t-SNE dim 2", fontsize=8)


def plot_category_clusters(embeddings: np.ndarray, metadata: list[dict], ax):
    """Mostrar clusters por categoria de dominio."""
    if len(embeddings) < 5:
        return

    tsne = TSNE(n_components=2, perplexity=min(15, len(embeddings) - 1),
                random_state=42, n_iter=1000)
    coords = tsne.fit_transform(embeddings)

    # Agrupar por categoria
    categories = defaultdict(list)
    for i, info in enumerate(metadata):
        categories[info["category"]].append(i)

    cmap = plt.cm.get_cmap("tab20", len(categories))
    for idx, (cat, indices) in enumerate(sorted(categories.items())):
        pts = coords[indices]
        ax.scatter(
            pts[:, 0], pts[:, 1],
            c=[cmap(idx)], s=40, label=cat,
            edgecolors="black", linewidths=0.3,
        )

    ax.set_title("Embeddings por Categoria", fontsize=12, fontweight="bold")
    ax.legend(
        loc="center left", bbox_to_anchor=(1.0, 0.5),
        fontsize=5, ncol=1, markerscale=0.8,
    )


def plot_pillar_distances(embeddings: np.ndarray, metadata: list[dict], ax):
    """Mostrar distancias promedio entre pilares."""
    pillar_embeddings = defaultdict(list)
    for i, info in enumerate(metadata):
        pillar_embeddings[info["pillar"]].append(embeddings[i])

    pillars = list(PILLAR_COLORS.keys())
    n = len(pillars)
    dist_matrix = np.zeros((n, n))

    for i in range(n):
        for j in range(n):
            if pillars[i] in pillar_embeddings and pillars[j] in pillar_embeddings:
                emb_i = np.mean(pillar_embeddings[pillars[i]], axis=0)
                emb_j = np.mean(pillar_embeddings[pillars[j]], axis=0)
                dist_matrix[i, j] = np.linalg.norm(emb_i - emb_j)

    im = ax.imshow(dist_matrix, cmap="YlOrRd", interpolation="nearest")
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    labels = [p.name for p in pillars]
    ax.set_xticklabels(labels, fontsize=8)
    ax.set_yticklabels(labels, fontsize=8)

    for i in range(n):
        for j in range(n):
            ax.text(j, i, f"{dist_matrix[i, j]:.1f}",
                    ha="center", va="center", fontsize=7,
                    color="white" if dist_matrix[i, j] > dist_matrix.max() * 0.6 else "black")

    ax.set_title("Distancia entre Pilares (L2)", fontsize=12, fontweight="bold")
    plt.colorbar(im, ax=ax, shrink=0.8)


def main():
    print("=" * 60)
    print("  NLE v7.0 - Visualizacion de Embeddings del Grafo")
    print("=" * 60)

    # 1. Construir grafo
    graph = build_full_graph()

    # 2. Crear GNN (pesos aleatorios - no entrenada)
    gnn = SkillGNN(hidden_dim=64, num_layers=3, num_heads=4, dropout=0.0)
    gnn.eval()
    print(f"GNN: {sum(p.numel() for p in gnn.parameters()):,} parametros")

    # 3. Obtener embeddings
    embeddings = get_node_embeddings(graph, gnn)
    metadata = get_skill_metadata(graph)
    print(f"Embeddings: {embeddings.shape} ({len(metadata)} skills)")

    # 4. Visualizar
    fig, axes = plt.subplots(2, 2, figsize=(16, 14))
    fig.suptitle(
        "NLE v7.0 — Grafo Categorico y Embeddings GNN\n"
        f"({len(graph.skills)} skills, {len([m for m in graph.morphisms if m.morphism_type != MorphismType.IDENTITY])} morfismos, 4 pilares)",
        fontsize=14, fontweight="bold",
    )

    plot_graph_structure(graph, axes[0, 0], metadata)
    plot_embeddings_tsne(embeddings, metadata, axes[0, 1])
    plot_category_clusters(embeddings, metadata, axes[1, 0])
    plot_pillar_distances(embeddings, metadata, axes[1, 1])

    plt.tight_layout()

    # Guardar
    out_path = "data/skill_embeddings.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"\nVisualizacion guardada en: {out_path}")

    import sys
    if "--show" in sys.argv:
        plt.show()
    else:
        print("(Usa --show para abrir ventana interactiva)")
        plt.close()


if __name__ == "__main__":
    main()
