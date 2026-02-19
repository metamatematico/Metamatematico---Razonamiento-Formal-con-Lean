"""
NLE v7.0 — Visualizaciones del Sistema
=======================================
Grafos, embeddings, arquitectura y diagramas explicativos.
"""

import streamlit as st
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch
import networkx as nx
from sklearn.manifold import TSNE
from sklearn.decomposition import PCA
import warnings
warnings.filterwarnings("ignore")

st.markdown("""
<style>
.block-container { padding-top: 1.5rem; }
h1, h2, h3 { color: #c9d1d9; }
</style>
""", unsafe_allow_html=True)

st.title("📊 Visualizaciones del Sistema NLE v7.0")

# ── Consulta activa desde el Demostrador ──────────────────────────────────────
_cq = st.session_state.get("current_query", "")
if _cq:
    st.markdown(
        f'<div style="background:#131c2e;border:1px solid #818cf8;border-left:4px solid #818cf8;'
        f'border-radius:10px;padding:.8rem 1.2rem;margin-bottom:1rem;">'
        f'<span style="font-size:.72rem;color:#6e7681;text-transform:uppercase;'
        f'letter-spacing:.07em">Consulta activa</span><br>'
        f'<span style="font-size:.95rem;color:#c9d1d9;font-weight:500">{_cq}</span>'
        f'<span style="float:right;font-size:.72rem;color:#484f58">Todas las pestañas adaptadas a esta consulta</span>'
        f'</div>',
        unsafe_allow_html=True,
    )
    if st.button("✕ Limpiar — mostrar sistema completo", key="clear_query"):
        del st.session_state["current_query"]
        st.rerun()
else:
    st.caption("Grafo de skills · Espacio de embeddings · Arquitectura MES · Pipeline de razonamiento")

# ─── DATOS DEL SISTEMA ────────────────────────────────────────────────────────
# 76 skills organizados por categoría matemática

SKILLS = [
    # Level 0 — Fundamentos (10)
    ("zfc-axioms",      "ZFC Axioms",          0, "Fundamentos",    "#ef5350"),
    ("ordinals",        "Ordinales",           0, "Fundamentos",    "#ef5350"),
    ("category-basics", "Categorías (base)",   0, "Fundamentos",    "#ef5350"),
    ("functors",        "Funtores",            0, "Fundamentos",    "#ef5350"),
    ("nat-trans",       "Trans. Naturales",    0, "Fundamentos",    "#ef5350"),
    ("limits",          "Límites",             0, "Fundamentos",    "#ef5350"),
    ("fol-deduction",   "Deducción FOL",       0, "Fundamentos",    "#ef5350"),
    ("fol-metatheory",  "Metateoría FOL",      0, "Fundamentos",    "#ef5350"),
    ("type-theory",     "Teoría de Tipos",     0, "Fundamentos",    "#ef5350"),
    ("lean-kernel",     "Lean Kernel",         0, "Fundamentos",    "#ef5350"),
    # Level 1 — Álgebra (7)
    ("group-theory",    "Teoría de Grupos",    1, "Álgebra",        "#42a5f5"),
    ("ring-theory",     "Teoría de Anillos",   1, "Álgebra",        "#42a5f5"),
    ("field-theory",    "Teoría de Campos",    1, "Álgebra",        "#42a5f5"),
    ("module-theory",   "Módulos",             1, "Álgebra",        "#42a5f5"),
    ("comm-algebra",    "Álgebra Conmutativa", 1, "Álgebra",        "#42a5f5"),
    ("homological-alg", "Álgebra Homológica",  1, "Álgebra",        "#42a5f5"),
    ("repres-theory",   "Teoría de Repres.",   1, "Álgebra",        "#42a5f5"),
    # Level 1 — Geometría (6)
    ("euclidean-geo",   "Geom. Euclidiana",    1, "Geometría",      "#66bb6a"),
    ("projective-geo",  "Geom. Proyectiva",    1, "Geometría",      "#66bb6a"),
    ("diff-geo",        "Geom. Diferencial",   1, "Geometría",      "#66bb6a"),
    ("alg-geo",         "Geom. Algebraica",    1, "Geometría",      "#66bb6a"),
    ("symplectic-geo",  "Geom. Simpléctica",   1, "Geometría",      "#66bb6a"),
    ("complex-geo",     "Geom. Compleja",      1, "Geometría",      "#66bb6a"),
    # Level 1 — Análisis (6)
    ("real-analysis",   "Análisis Real",       1, "Análisis",       "#ffa726"),
    ("complex-analysis","Análisis Complejo",   1, "Análisis",       "#ffa726"),
    ("func-analysis",   "Análisis Funcional",  1, "Análisis",       "#ffa726"),
    ("harmonic-anal",   "Análisis Armónico",   1, "Análisis",       "#ffa726"),
    ("pde-techniques",  "EDPs",                1, "Análisis",       "#ffa726"),
    ("operator-theory", "Teoría de Op.",       1, "Análisis",       "#ffa726"),
    # Level 1 — Topología (5)
    ("point-set-topo",  "Top. Puntual",        1, "Topología",      "#ab47bc"),
    ("alg-topology",    "Top. Algebraica",     1, "Topología",      "#ab47bc"),
    ("diff-topology",   "Top. Diferencial",    1, "Topología",      "#ab47bc"),
    ("homotopy-theory", "Teoría de Homotopía", 1, "Topología",      "#ab47bc"),
    ("geometric-topo",  "Top. Geométrica",     1, "Topología",      "#ab47bc"),
    # Level 1 — Lógica (3)
    ("model-theory",    "Teoría de Modelos",   1, "Lógica",         "#26c6da"),
    ("proof-theory",    "Teoría de Pruebas",   1, "Lógica",         "#26c6da"),
    ("hott",            "HoTT",                1, "Lógica",         "#26c6da"),
    # Level 1 — Teoría de Números (4)
    ("elem-nt",         "TN Elemental",        1, "T. Números",     "#ef9a9a"),
    ("alg-nt",          "TN Algebraica",       1, "T. Números",     "#ef9a9a"),
    ("analytic-nt",     "TN Analítica",        1, "T. Números",     "#ef9a9a"),
    ("arith-geo",       "Geom. Aritmética",    1, "T. Números",     "#ef9a9a"),
    # Level 1 — Combinatoria (6)
    ("enumerative",     "Enumerativa",         1, "Combinatoria",   "#a5d6a7"),
    ("graph-theory",    "Teoría de Grafos",    1, "Combinatoria",   "#a5d6a7"),
    ("ramsey-theory",   "Ramsey",              1, "Combinatoria",   "#a5d6a7"),
    ("extremal-comb",   "Extremal",            1, "Combinatoria",   "#a5d6a7"),
    ("alg-comb",        "Algebraica",          1, "Combinatoria",   "#a5d6a7"),
    ("prob-method",     "Método Prob.",        1, "Combinatoria",   "#a5d6a7"),
    # Level 1 — Probabilidad (4)
    ("prob-theory",     "Probabilidad",        1, "Probabilidad",   "#ffcc80"),
    ("stochastic",      "Proc. Estocásticos",  1, "Probabilidad",   "#ffcc80"),
    ("martingale",      "Martingalas",         1, "Probabilidad",   "#ffcc80"),
    ("ergodic",         "Teoría Ergódica",     1, "Probabilidad",   "#ffcc80"),
    # Level 1 — T. Categorías avanzada (2)
    ("higher-cat",      "Cat. Superiores",     1, "Categorías",     "#ce93d8"),
    ("homol-cat",       "Álg. Hom. Categórica",1, "Categorías",     "#ce93d8"),
    # Level 1 — Computación (4)
    ("computability",   "Computabilidad",      1, "Computación",    "#80cbc4"),
    ("complexity",      "Complejidad",         1, "Computación",    "#80cbc4"),
    ("algo-analysis",   "Análisis de Alg.",    1, "Computación",    "#80cbc4"),
    ("formal-verif",    "Verif. Formal",       1, "Computación",    "#80cbc4"),
    # Level 1 — Optimización (3)
    ("convex-opt",      "Optim. Convexa",      1, "Optimización",   "#bcaaa4"),
    ("discrete-opt",    "Optim. Discreta",     1, "Optimización",   "#bcaaa4"),
    ("variational",     "Métodos Variacional.", 1, "Optimización",   "#bcaaa4"),
    # Level 1 — Tácticas Lean (9)
    ("tactic-simp",     "simp",                1, "Tácticas Lean",  "#f48fb1"),
    ("tactic-ring",     "ring",                1, "Tácticas Lean",  "#f48fb1"),
    ("tactic-omega",    "omega",               1, "Tácticas Lean",  "#f48fb1"),
    ("tactic-linarith", "linarith",            1, "Tácticas Lean",  "#f48fb1"),
    ("tactic-exact",    "exact",               1, "Tácticas Lean",  "#f48fb1"),
    ("tactic-apply",    "apply",               1, "Tácticas Lean",  "#f48fb1"),
    ("tactic-induction","induction",           1, "Tácticas Lean",  "#f48fb1"),
    ("tactic-aesop",    "aesop",               1, "Tácticas Lean",  "#f48fb1"),
    ("tactic-calc",     "calc",                1, "Tácticas Lean",  "#f48fb1"),
    # Level 2 — Estrategias de prueba (6)
    ("strat-backward",  "Hacia atrás",         2, "Estrategias",    "#fff59d"),
    ("strat-forward",   "Hacia adelante",      2, "Estrategias",    "#fff59d"),
    ("strat-contra",    "Contradicción",       2, "Estrategias",    "#fff59d"),
    ("strat-cases",     "Por casos",           2, "Estrategias",    "#fff59d"),
    ("strat-inductive", "Inductiva",           2, "Estrategias",    "#fff59d"),
    ("strat-construct", "Constructiva",        2, "Estrategias",    "#fff59d"),
]

# Conexiones clave (src_id, tgt_id, tipo)
EDGES = [
    # Fundamentos → dominios
    ("zfc-axioms", "group-theory", "dep"),
    ("zfc-axioms", "real-analysis", "dep"),
    ("zfc-axioms", "point-set-topo", "dep"),
    ("zfc-axioms", "elem-nt", "dep"),
    ("zfc-axioms", "prob-theory", "dep"),
    ("category-basics", "functors", "dep"),
    ("functors", "nat-trans", "dep"),
    ("nat-trans", "limits", "dep"),
    ("limits", "higher-cat", "dep"),
    ("fol-deduction", "model-theory", "dep"),
    ("fol-deduction", "proof-theory", "dep"),
    ("type-theory", "hott", "dep"),
    ("type-theory", "lean-kernel", "dep"),
    # Álgebra
    ("group-theory", "ring-theory", "dep"),
    ("ring-theory", "field-theory", "dep"),
    ("ring-theory", "module-theory", "dep"),
    ("module-theory", "comm-algebra", "dep"),
    ("comm-algebra", "homological-alg", "dep"),
    ("homological-alg", "repres-theory", "dep"),
    # Geometría
    ("euclidean-geo", "diff-geo", "dep"),
    ("alg-geo", "homological-alg", "dep"),   # cross
    ("diff-geo", "symplectic-geo", "dep"),
    # Análisis → topología
    ("real-analysis", "complex-analysis", "dep"),
    ("real-analysis", "func-analysis", "dep"),
    ("func-analysis", "operator-theory", "dep"),
    ("point-set-topo", "alg-topology", "dep"),
    ("alg-topology", "homotopy-theory", "dep"),
    ("homotopy-theory", "diff-topology", "dep"),
    # Lógica → computación
    ("proof-theory", "formal-verif", "dep"),
    ("proof-theory", "computability", "dep"),
    ("computability", "complexity", "dep"),
    # HoTT ↔ homotopy (traducción)
    ("hott", "homotopy-theory", "trans"),
    # Homological algebra ↔ topology (analogía)
    ("homological-alg", "alg-topology", "analogy"),
    # Lean tácticas → estrategias
    ("lean-kernel", "tactic-simp", "dep"),
    ("lean-kernel", "tactic-ring", "dep"),
    ("lean-kernel", "tactic-omega", "dep"),
    ("lean-kernel", "tactic-exact", "dep"),
    ("tactic-simp", "strat-forward", "dep"),
    ("tactic-exact", "strat-backward", "dep"),
    ("tactic-induction", "strat-inductive", "dep"),
]

# Índices
id_to_idx = {s[0]: i for i, s in enumerate(SKILLS)}

PALETTE = {
    "Fundamentos":   "#ef5350",
    "Álgebra":       "#42a5f5",
    "Geometría":     "#66bb6a",
    "Análisis":      "#ffa726",
    "Topología":     "#ab47bc",
    "Lógica":        "#26c6da",
    "T. Números":    "#ef9a9a",
    "Combinatoria":  "#a5d6a7",
    "Probabilidad":  "#ffcc80",
    "Categorías":    "#ce93d8",
    "Computación":   "#80cbc4",
    "Optimización":  "#bcaaa4",
    "Tácticas Lean": "#f48fb1",
    "Estrategias":   "#fff59d",
}

BG = "#0d1117"
FG = "#c9d1d9"
plt.rcParams.update({
    "figure.facecolor": BG, "axes.facecolor": BG,
    "text.color": FG, "axes.labelcolor": FG,
    "xtick.color": FG, "ytick.color": FG,
    "axes.edgecolor": "#21262d",
    "axes.spines.top": False, "axes.spines.right": False,
    "font.size": 9,
})


# ─── GRAFO DE SKILLS ──────────────────────────────────────────────────────────

@st.cache_data
def build_graph():
    G = nx.DiGraph()
    for sid, name, level, cat, color in SKILLS:
        G.add_node(sid, name=name, level=level, cat=cat, color=color)
    for src, tgt, kind in EDGES:
        G.add_edge(src, tgt, kind=kind)
    return G


@st.cache_data
def make_layout(_G):
    # Layout jerárquico: x = categoría, y = nivel
    cats = list(PALETTE.keys())
    pos = {}
    cat_counts = {c: 0 for c in cats}
    for sid, name, level, cat, _ in SKILLS:
        cx = cats.index(cat)
        cy = cat_counts[cat]
        cat_counts[cat] += 1
        pos[sid] = (cx * 2.5 + np.random.uniform(-0.4, 0.4),
                    level * -3.0 + cy * 0.28 + np.random.uniform(-0.05, 0.05))
    return pos


def fig_skill_graph(filter_cat=None, query=None):
    G = build_graph()
    pos = make_layout(G)

    # Calcular nodos relevantes para la consulta
    TACTIC_CATS = ("Tácticas Lean", "Estrategias")
    matched_set, dep_set, tactic_set = set(), set(), set()
    if query:
        matched = match_skills(query)
        needed  = proof_subgraph(G, matched)
        matched_set = set(matched)
        tactic_set  = {n for n in needed if G.nodes[n].get("cat") in TACTIC_CATS}
        dep_set     = needed - matched_set - tactic_set

    nodes = [n for n in G.nodes if filter_cat is None or G.nodes[n]["cat"] == filter_cat]
    subG  = G.subgraph(nodes)

    fig, ax = plt.subplots(figsize=(16, 8), facecolor=BG)
    ax.set_facecolor(BG)

    # Edges — más visibles cuando conectan nodos relevantes
    for u, v, d in subG.edges(data=True):
        if u not in pos or v not in pos:
            continue
        kind = d.get("kind", "dep")
        active = query and (u in matched_set | dep_set | tactic_set or
                            v in matched_set | dep_set | tactic_set)
        col   = {"dep": "#58a6ff" if active else "#1c2333",
                 "trans": "#818cf8" if active else "#1c2333",
                 "analogy": "#4ade80" if active else "#1c2333"}.get(kind, "#1c2333")
        lw    = 1.4 if active else 0.4
        alpha = 0.9 if active else 0.3
        ax.annotate("", xy=pos[v], xytext=pos[u],
                    arrowprops=dict(arrowstyle="-|>", color=col, lw=lw, alpha=alpha,
                                    connectionstyle="arc3,rad=0.05"))

    # Nodes
    for sid in subG.nodes:
        x, y = pos[sid]
        d    = G.nodes[sid]
        if query:
            if sid in matched_set:
                color, size, alpha, ec, lw = "#fbbf24", 600, 1.0, "#ffffff", 1.5
            elif sid in tactic_set:
                color, size, alpha, ec, lw = "#4ade80", 350, 0.95, "#4ade80", 1.0
            elif sid in dep_set:
                color, size, alpha, ec, lw = "#818cf8", 280, 0.9, "#818cf8", 0.8
            else:
                color, size, alpha, ec, lw = "#1c2333", 60, 0.2, "#21262d", 0.3
        else:
            size  = 220 if d["level"] == 0 else (160 if d["level"] == 1 else 130)
            color, alpha, ec, lw = d["color"], 0.92, "#21262d", 0.5

        ax.scatter(x, y, s=size, c=[color], zorder=5, alpha=alpha,
                   edgecolors=ec, linewidths=lw)

        # Etiqueta: siempre en nodos relevantes, solo fundamentos en vista global
        show_label = (query and sid in (matched_set | dep_set | tactic_set)) or \
                     (not query and d["level"] == 0) or \
                     (not query and filter_cat is not None)
        if show_label:
            fc = "#fbbf24" if sid in matched_set else \
                 "#4ade80" if sid in tactic_set else \
                 "#93c5fd" if sid in dep_set else FG
            ax.text(x, y - 0.28, d["name"], fontsize=6, ha="center", va="top",
                    color=fc, zorder=6, fontweight="bold" if sid in matched_set else "normal")

    # Leyenda
    if query:
        legend_h = [
            mpatches.Patch(color="#fbbf24", label=f"Skills activados ({len(matched_set)})"),
            mpatches.Patch(color="#818cf8", label=f"Dependencias ({len(dep_set)})"),
            mpatches.Patch(color="#4ade80", label=f"Tácticas/Estrategias ({len(tactic_set)})"),
            mpatches.Patch(color="#1c2333", label="No involucrados"),
        ]
    else:
        legend_h = [mpatches.Patch(color=c, label=k) for k, c in PALETTE.items()] + [
            mpatches.Patch(color="#30363d", label="Dependencia"),
            mpatches.Patch(color="#58a6ff", label="Traducción"),
            mpatches.Patch(color="#3fb950", label="Analogía"),
        ]
    ax.legend(handles=legend_h, loc="lower left", ncol=2, fontsize=6.5,
              framealpha=0.2, edgecolor="#21262d", labelcolor=FG)

    ax.axis("off")
    suffix = f' — consulta: "{query[:45]}…"' if query and len(query) > 45 \
             else (f' — consulta: "{query}"' if query else "")
    ax.set_title(
        f"Grafo Categórico de Skills — NLE v7.0  ({len(subG.nodes)} nodos){suffix}",
        color=FG, fontsize=10, pad=10)
    fig.tight_layout()
    return fig


# ─── ESPACIO DE EMBEDDINGS ────────────────────────────────────────────────────

@st.cache_data
def build_embeddings():
    np.random.seed(42)
    cats = list(PALETTE.keys())
    embs = []
    for sid, name, level, cat, _ in SKILLS:
        # Hash-seed embedding (simula el SkillEmbeddingModel del sistema)
        rng = np.random.RandomState(hash(sid) % (2**31))
        text_emb = rng.randn(256) * 0.5
        # Añadir señal semántica por categoría
        cat_signal = np.zeros(256)
        cat_idx = cats.index(cat)
        cat_signal[cat_idx * 18: cat_idx * 18 + 18] = 2.0
        cat_signal[level * 64: level * 64 + 32] += 1.5
        embs.append(text_emb + cat_signal)
    return np.array(embs)


def fig_tsne(method="tsne", query=None):
    embs = build_embeddings()
    if method == "tsne":
        proj = TSNE(n_components=2, random_state=42, perplexity=15,
                    n_iter=1000, init="pca").fit_transform(embs)
        xlabel, ylabel = "t-SNE 1", "t-SNE 2"
        title = "Espacio de Embeddings — t-SNE (76 skills)"
    else:
        pca = PCA(n_components=2, random_state=42)
        proj = pca.fit_transform(embs)
        xlabel = f"PC1 ({pca.explained_variance_ratio_[0]:.0%})"
        ylabel = f"PC2 ({pca.explained_variance_ratio_[1]:.0%})"
        title  = "Espacio de Embeddings — PCA (76 skills)"

    # Calcular nodos relevantes
    TACTIC_CATS = ("Tácticas Lean", "Estrategias")
    matched_set, dep_set, tactic_set = set(), set(), set()
    if query:
        G = build_graph()
        matched    = match_skills(query)
        needed     = proof_subgraph(G, matched)
        matched_set = set(matched)
        tactic_set  = {n for n in needed if G.nodes[n].get("cat") in TACTIC_CATS}
        dep_set     = needed - matched_set - tactic_set

    fig, ax = plt.subplots(figsize=(11, 7), facecolor=BG)
    ax.set_facecolor(BG)

    markers = {0: "D", 1: "o", 2: "^"}

    # Dibuja primero los nodos no relevantes (fondo)
    for i, (sid, name, level, cat, color) in enumerate(SKILLS):
        in_query = sid in (matched_set | dep_set | tactic_set)
        if query and not in_query:
            ax.scatter(proj[i, 0], proj[i, 1],
                       c=[color], s=30, marker=markers[level],
                       edgecolors="#0d1117", linewidths=0.3, alpha=0.18, zorder=3)

    # Luego los relevantes (encima)
    for i, (sid, name, level, cat, color) in enumerate(SKILLS):
        in_matched = sid in matched_set
        in_tactic  = sid in tactic_set
        in_dep     = sid in dep_set
        in_query   = in_matched or in_tactic or in_dep

        if query and not in_query:
            continue  # ya dibujados arriba

        if in_matched:
            clr, sz, ec, lw, zord = "#fbbf24", 320, "#ffffff", 2.0, 7
        elif in_tactic:
            clr, sz, ec, lw, zord = "#4ade80", 200, "#4ade80", 1.5, 6
        elif in_dep:
            clr, sz, ec, lw, zord = "#818cf8", 160, "#818cf8", 1.2, 6
        else:
            clr, sz, ec, lw, zord = color, 80 if level == 0 else 55, "#0d1117", 0.4, 5

        ax.scatter(proj[i, 0], proj[i, 1],
                   c=[clr], s=sz, marker=markers[level],
                   edgecolors=ec, linewidths=lw, alpha=0.95, zorder=zord)

        # Etiquetas
        show = in_query or (not query and level == 0)
        if show:
            fc = "#fbbf24" if in_matched else "#4ade80" if in_tactic else \
                 "#93c5fd" if in_dep else color
            ax.annotate(name, (proj[i, 0], proj[i, 1]),
                        fontsize=6.5 if in_matched else 5.5,
                        color=fc, fontweight="bold" if in_matched else "normal",
                        xytext=(5, 5), textcoords="offset points",
                        arrowprops=dict(arrowstyle="-", color=fc, lw=0.5, alpha=0.5)
                        if in_matched else None)

    # Leyenda
    if query:
        handles = [
            mpatches.Patch(color="#fbbf24", label=f"Activados ({len(matched_set)})"),
            mpatches.Patch(color="#818cf8", label=f"Dependencias ({len(dep_set)})"),
            mpatches.Patch(color="#4ade80", label=f"Tácticas ({len(tactic_set)})"),
            mpatches.Patch(color="#3d444d", label="No involucrados"),
        ]
        title += f'\n"{query[:55]}{"…" if len(query)>55 else ""}"'
    else:
        handles = [mpatches.Patch(color=c, label=k) for k, c in PALETTE.items()]
    ax.legend(handles=handles, loc="upper left", ncol=1, fontsize=6.5,
              framealpha=0.2, edgecolor="#21262d", labelcolor=FG)

    ax.set_xlabel(xlabel, color=FG, fontsize=9)
    ax.set_ylabel(ylabel, color=FG, fontsize=9)
    ax.set_title(title, color=FG, fontsize=10, pad=10)
    ax.tick_params(colors=FG, labelsize=7)
    for spine in ax.spines.values():
        spine.set_edgecolor("#21262d")
    fig.tight_layout()
    return fig


# ─── ARQUITECTURA NLE ─────────────────────────────────────────────────────────

def fig_architecture():
    fig, ax = plt.subplots(figsize=(14, 8), facecolor=BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 14)
    ax.set_ylim(0, 8)
    ax.axis("off")

    def box(x, y, w, h, label, sublabel="", color="#1f2937", textcolor="#e5e7eb", fontsize=8):
        rect = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08",
                              facecolor=color, edgecolor="#374151", linewidth=1.2, zorder=3)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h/2 + (0.12 if sublabel else 0), label,
                ha="center", va="center", fontsize=fontsize, color=textcolor,
                fontweight="bold", zorder=4)
        if sublabel:
            ax.text(x + w/2, y + h/2 - 0.22, sublabel,
                    ha="center", va="center", fontsize=6, color="#9ca3af", zorder=4)

    def arrow(x0, y0, x1, y1, label="", color="#58a6ff"):
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                    arrowprops=dict(arrowstyle="-|>", color=color, lw=1.5,
                                    connectionstyle="arc3,rad=0"))
        if label:
            mx, my = (x0+x1)/2, (y0+y1)/2
            ax.text(mx, my + 0.12, label, ha="center", va="bottom",
                    fontsize=6.5, color=color)

    # Usuario
    box(0.2, 3.5, 1.8, 1.0, "Usuario", "Consulta NL", "#0d2137", "#60a5fa")
    # CR_tac
    box(2.4, 3.5, 2.2, 1.0, "CR_tac", "Clasificador\nquery→modo", "#1a2a1a", "#4ade80")
    # Grafo de Skills
    box(5.0, 5.5, 3.5, 1.8, "Grafo Categórico", "76 skills · 4 pilares\ndep + analogía + traducción", "#1a1a2e", "#818cf8")
    # GoalAnalyzer
    box(5.0, 3.2, 2.2, 1.0, "GoalAnalyzer", "regex + grafo\n→ orden tácticas", "#1a1a2e", "#818cf8")
    # LLM
    box(5.0, 1.5, 2.2, 1.0, "LLM (Claude/Gemini)", "contexto enriquecido\ndel grafo", "#1f1107", "#fb923c")
    # Lean 4
    box(8.0, 3.2, 2.2, 1.0, "Lean 4", "SolverCascade\nrfl→simp→ring→omega", "#0d1f0d", "#4ade80")
    # MES Memory
    box(8.0, 5.5, 2.5, 1.8, "MES Memory", "Patrones\nColimites\nEmergencia", "#1a0d2e", "#c084fc")
    # GNN+PPO
    box(11.0, 3.5, 2.5, 1.8, "GNN + PPO", "SkillGNN 124K params\nActorCritic\nAprendizaje vivo", "#0d1f1f", "#2dd4bf")
    # Respuesta
    box(11.0, 1.0, 2.5, 1.0, "Respuesta", "explicación +\nprueba Lean", "#1a1007", "#fbbf24")

    # Flechas
    arrow(2.0, 4.0, 2.4, 4.0, "consulta")
    arrow(4.6, 4.0, 5.0, 3.7, "ASISTIR")
    arrow(4.6, 3.8, 5.0, 2.0, "RESPONDER")
    arrow(6.0, 3.2, 6.0, 2.5)
    arrow(7.2, 3.7, 8.0, 3.7)
    arrow(6.0, 5.5, 6.0, 4.2, "skills\nrelevantes")
    arrow(5.0, 6.4, 2.6, 4.5, "contexto", "#9ca3af")
    arrow(8.0, 6.4, 11.0, 4.5, "memoria", "#c084fc")
    arrow(10.2, 3.7, 11.0, 4.0)
    arrow(13.0, 4.0, 13.5, 1.5, "reward", "#2dd4bf")
    arrow(11.0, 1.5, 8.5, 1.5)
    ax.text(8.5, 1.5, "→", color="#fbbf24", fontsize=14)

    ax.set_title("Arquitectura del Sistema NLE v7.0  —  Σ_t = (L, CR_t, G_t, F)",
                 color=FG, fontsize=12, pad=8, fontweight="bold")
    fig.tight_layout()
    return fig


# ─── MES: COMPLEXIFICACIÓN ────────────────────────────────────────────────────

def fig_mes_complexification():
    fig, axes = plt.subplots(1, 3, figsize=(14, 5), facecolor=BG)
    titles = [
        "1. Patrón P: I → K\n(colección de skills)",
        "2. Colímite cP\n(nuevo skill emergente)",
        "3. Complexificación K'\n(grafo evolucionado)",
    ]

    for idx, ax in enumerate(axes):
        ax.set_facecolor(BG)
        ax.set_xlim(-2.5, 2.5)
        ax.set_ylim(-2.5, 2.5)
        ax.axis("off")
        ax.set_title(titles[idx], color=FG, fontsize=9, pad=6)

    # Panel 1: Patrón
    ax = axes[0]
    nodes_pat = [(-1.5, -1, "P₁\nGrupos", "#42a5f5"),
                 (0, -1,    "P₂\nAnillos", "#42a5f5"),
                 (1.5, -1,  "P₃\nMódulos", "#42a5f5"),
                 (-0.75, 0.5,"P₁₂", "#7c3aed"),
                 (0.75, 0.5, "P₂₃", "#7c3aed")]
    for x, y, lbl, c in nodes_pat:
        ax.scatter(x, y, s=300, c=c, zorder=5, edgecolors="#21262d", lw=1)
        ax.text(x, y - 0.35, lbl, ha="center", fontsize=7, color=FG)
    ax.annotate("", xy=(-0.75, 0.5), xytext=(-1.5, -1),
                arrowprops=dict(arrowstyle="-|>", color="#58a6ff", lw=1))
    ax.annotate("", xy=(-0.75, 0.5), xytext=(0, -1),
                arrowprops=dict(arrowstyle="-|>", color="#58a6ff", lw=1))
    ax.annotate("", xy=(0.75, 0.5), xytext=(0, -1),
                arrowprops=dict(arrowstyle="-|>", color="#58a6ff", lw=1))
    ax.annotate("", xy=(0.75, 0.5), xytext=(1.5, -1),
                arrowprops=dict(arrowstyle="-|>", color="#58a6ff", lw=1))
    ax.text(0, -2, "Categoría índice I\n+ Skills en K", ha="center",
            fontsize=7, color="#9ca3af",
            bbox=dict(boxstyle="round", facecolor="#161b22", edgecolor="#21262d"))

    # Panel 2: Colímite
    ax = axes[1]
    # Nodos del patrón (tenue)
    for x, y, lbl, _ in nodes_pat:
        ax.scatter(x, y, s=150, c="#374151", zorder=3, alpha=0.5)
    # Colímite
    ax.scatter(0, 1.5, s=600, c="#f59e0b", zorder=6, edgecolors="#fbbf24", lw=2)
    ax.text(0, 1.5, "cP", ha="center", va="center", fontsize=10, color="black", fontweight="bold", zorder=7)
    ax.text(0, 2.1, "Álgebra Abstracta\n(skill emergente)", ha="center", fontsize=7.5, color="#fbbf24")
    for x, y, _, _ in nodes_pat:
        ax.annotate("", xy=(0, 1.5), xytext=(x, y),
                    arrowprops=dict(arrowstyle="-|>", color="#f59e0b", lw=1, alpha=0.6))
    ax.text(0, -1.8, "cᵢ: Pᵢ → cP\n(co-cono universal)", ha="center",
            fontsize=7, color="#9ca3af",
            bbox=dict(boxstyle="round", facecolor="#161b22", edgecolor="#21262d"))

    # Panel 3: Grafo evolucionado
    ax = axes[2]
    old_nodes = [(-1.5, -1.2, "Grupos", "#42a5f5"),
                 (0, -1.2,    "Anillos", "#42a5f5"),
                 (1.5, -1.2,  "Módulos", "#42a5f5"),
                 (-1, 0.3,    "Comutativa", "#66bb6a"),
                 (1, 0.3,     "Homológica", "#66bb6a")]
    new_node = (0, 1.8, "Álgebra\nAbstracta ✦", "#f59e0b")
    for x, y, lbl, c in old_nodes:
        ax.scatter(x, y, s=200, c=c, zorder=5, edgecolors="#21262d", lw=0.8)
        ax.text(x, y - 0.35, lbl, ha="center", fontsize=6.5, color=FG)
    ax.scatter(*new_node[:2], s=500, c=[new_node[3]], zorder=6, edgecolors="#fbbf24", lw=2)
    ax.text(new_node[0], new_node[1] - 0.38, new_node[2], ha="center", fontsize=7, color="#fbbf24")
    for x, y, _, _ in old_nodes:
        ax.annotate("", xy=(0, 1.8), xytext=(x, y),
                    arrowprops=dict(arrowstyle="-|>", color="#f59e0b", lw=0.8, alpha=0.6))
    for (x1, y1, *_), (x2, y2, *_) in [
        (old_nodes[0], old_nodes[1]), (old_nodes[1], old_nodes[2]),
        (old_nodes[3], old_nodes[4])
    ]:
        ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                    arrowprops=dict(arrowstyle="-|>", color="#30363d", lw=0.8))
    ax.text(0, -2, "K' = K + cP + co-conos\n(grafo complexificado)", ha="center",
            fontsize=7, color="#9ca3af",
            bbox=dict(boxstyle="round", facecolor="#161b22", edgecolor="#21262d"))

    fig.suptitle("Memory Evolutive Systems — Complexificación y Emergencia", color=FG, fontsize=11, y=1.01)
    fig.tight_layout()
    return fig


# ─── PIPELINE CR_TAC ─────────────────────────────────────────────────────────

def fig_pipeline():
    fig, ax = plt.subplots(figsize=(13, 4.5), facecolor=BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 4.5)
    ax.axis("off")

    steps = [
        (0.4, 2.0, 1.6, 1.6, "Consulta\ndel usuario", "#1e3a5f", "#60a5fa"),
        (2.5, 2.0, 1.8, 1.6, "CR_tac\nClasificación", "#1a2a1a", "#4ade80"),
        (5.0, 3.0, 1.8, 1.2, "RESPONDER\nExplicación", "#1f1107", "#fb923c"),
        (5.0, 0.8, 1.8, 1.2, "ASISTIR\nPrueba Lean", "#0d1f0d", "#4ade80"),
        (7.3, 3.0, 1.8, 1.2, "Grafo de Skills\nContexto", "#1a1a2e", "#818cf8"),
        (7.3, 0.8, 1.8, 1.2, "GoalAnalyzer\nOrden tácticas", "#1a1a2e", "#818cf8"),
        (9.6, 2.0, 1.8, 1.6, "LLM\nRespuesta", "#1f1107", "#fb923c"),
        (11.8, 2.0, 1.0, 1.6, "✓\nLean 4", "#0d1f0d", "#4ade80"),
    ]

    for x, y, w, h, lbl, bg, fg in steps:
        rect = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1",
                              facecolor=bg, edgecolor=fg, linewidth=1.2, zorder=3)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h/2, lbl, ha="center", va="center",
                fontsize=8.5, color=fg, fontweight="bold", zorder=4)

    # Flechas
    arrows = [
        (2.0, 2.8, 2.5, 2.8), (4.3, 3.2, 5.0, 3.6), (4.3, 2.6, 5.0, 1.4),
        (6.8, 3.6, 7.3, 3.6), (6.8, 1.4, 7.3, 1.4),
        (9.1, 3.6, 9.6, 2.8), (9.1, 1.4, 9.6, 2.2),
        (11.4, 2.8, 11.8, 2.8),
    ]
    for x0, y0, x1, y1 in arrows:
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                    arrowprops=dict(arrowstyle="-|>", color="#58a6ff", lw=1.3))

    # Nivel 2: GNN+PPO y memoria
    ax.text(6.5, 0.15, "GNN+PPO aprende de cada interacción · Memoria procedimental guarda patrones exitosos",
            ha="center", fontsize=7.5, color="#9ca3af",
            bbox=dict(boxstyle="round", facecolor="#161b22", edgecolor="#21262d", alpha=0.8))

    ax.set_title("Pipeline de Procesamiento — De la consulta a la respuesta", color=FG, fontsize=11, pad=8)
    fig.tight_layout()
    return fig


# ─── DISTRIBUCIÓN POR CATEGORÍA ──────────────────────────────────────────────

def fig_distribution():
    from collections import Counter
    cat_counts = Counter(s[3] for s in SKILLS)
    cats = list(cat_counts.keys())
    counts = [cat_counts[c] for c in cats]
    colors = [PALETTE[c] for c in cats]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5), facecolor=BG)

    # Barras horizontales
    ax1.set_facecolor(BG)
    bars = ax1.barh(cats[::-1], counts[::-1], color=[PALETTE[c] for c in cats[::-1]],
                    edgecolor="#21262d", linewidth=0.5, height=0.7)
    for bar, count in zip(bars, counts[::-1]):
        ax1.text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                 str(count), va="center", fontsize=8, color=FG)
    ax1.set_xlabel("Número de skills", color=FG)
    ax1.set_title("Skills por categoría matemática", color=FG, fontsize=10)
    ax1.tick_params(colors=FG, labelsize=8)
    ax1.spines["top"].set_visible(False)
    ax1.spines["right"].set_visible(False)
    ax1.spines["left"].set_edgecolor("#21262d")
    ax1.spines["bottom"].set_edgecolor("#21262d")

    # Pie chart por nivel
    ax2.set_facecolor(BG)
    level_counts = Counter(s[2] for s in SKILLS)
    level_labels = ["Nivel 0\nFundamentos", "Nivel 1\nDominios", "Nivel 2\nEstrategias"]
    level_colors = ["#ef5350", "#42a5f5", "#fff59d"]
    wedges, texts, autotexts = ax2.pie(
        [level_counts[k] for k in [0, 1, 2]],
        labels=level_labels, colors=level_colors,
        autopct="%1.0f%%", startangle=90,
        textprops={"color": FG, "fontsize": 8},
        wedgeprops={"edgecolor": BG, "linewidth": 2},
    )
    for at in autotexts:
        at.set_fontsize(9)
        at.set_color(BG)
        at.set_fontweight("bold")
    ax2.set_title("Distribución por nivel jerárquico", color=FG, fontsize=10)

    fig.tight_layout()
    return fig


# ─── MAPA DE CALOR INTER-CATEGORÍAS ──────────────────────────────────────────

def fig_heatmap():
    embs = build_embeddings()
    cats = list(PALETTE.keys())

    # Centroides por categoría
    cat_embs = {}
    for i, (sid, name, level, cat, _) in enumerate(SKILLS):
        cat_embs.setdefault(cat, []).append(embs[i])
    centroids = {c: np.mean(v, axis=0) for c, v in cat_embs.items()}

    # Matriz de similitud coseno
    n = len(cats)
    sim = np.zeros((n, n))
    for i, c1 in enumerate(cats):
        for j, c2 in enumerate(cats):
            v1, v2 = centroids[c1], centroids[c2]
            sim[i, j] = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-9)

    fig, ax = plt.subplots(figsize=(9, 7), facecolor=BG)
    ax.set_facecolor(BG)
    im = ax.imshow(sim, cmap="Blues", vmin=0.2, vmax=1.0, aspect="auto")
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04).ax.yaxis.set_tick_params(color=FG)
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(cats, rotation=45, ha="right", fontsize=7, color=FG)
    ax.set_yticklabels(cats, fontsize=7, color=FG)
    for i in range(n):
        for j in range(n):
            ax.text(j, i, f"{sim[i,j]:.2f}", ha="center", va="center",
                    fontsize=5.5, color="white" if sim[i,j] > 0.7 else "#9ca3af")
    ax.set_title("Similitud Semántica entre Categorías (embeddings NLE)", color=FG, fontsize=10, pad=10)
    fig.tight_layout()
    return fig


# ─── GNN ARCHITECTURE ────────────────────────────────────────────────────────

def fig_gnn():
    fig, ax = plt.subplots(figsize=(12, 5), facecolor=BG)
    ax.set_facecolor(BG)
    ax.set_xlim(0, 12)
    ax.set_ylim(0, 5)
    ax.axis("off")

    # Capas del GNN
    layers = [
        (0.5, "Input\nFeatures\n(node)", "#1e3a5f", 4),
        (2.2, "GATConv 1\n64-dim\n4 heads", "#1a1a2e", 5),
        (4.2, "GATConv 2\n64-dim\n4 heads", "#1a1a2e", 5),
        (6.2, "GATConv 3\n64-dim\n4 heads", "#1a1a2e", 5),
        (8.2, "Skill\nEmbedding\n64-dim", "#0d2137", 4),
        (10.0, "Actor\nCritic\n(PPO)", "#1f1107", 3),
    ]

    for x, lbl, color, n_nodes in layers:
        # Nodos de la capa
        ys = np.linspace(0.5, 4.5, n_nodes)
        for y in ys:
            ax.scatter(x, y, s=200, c=color, zorder=5, edgecolors="#58a6ff", lw=1.2)
        ax.text(x, -0.1, lbl, ha="center", va="top", fontsize=7, color=FG,
                bbox=dict(boxstyle="round", facecolor="#161b22", edgecolor="#21262d", alpha=0.8))

    # Conexiones
    for (x1, _, _, n1), (x2, _, _, n2) in zip(layers[:-1], layers[1:]):
        ys1 = np.linspace(0.5, 4.5, n1)
        ys2 = np.linspace(0.5, 4.5, n2)
        for y1 in ys1:
            for y2 in ys2:
                alpha = 0.08 if n1 * n2 > 12 else 0.2
                ax.plot([x1, x2], [y1, y2], color="#374151", lw=0.5, alpha=alpha, zorder=2)

    # Anotaciones de atención
    for x in [2.2, 4.2, 6.2]:
        ax.text(x, 4.9, "↗ Atención\nmulticabeza", ha="center", fontsize=6, color="#818cf8")

    # Skip connections
    ax.annotate("", xy=(8.2, 2.5), xytext=(0.5, 2.5),
                arrowprops=dict(arrowstyle="-|>", color="#3fb950", lw=1.2,
                                connectionstyle="arc3,rad=-0.3"))
    ax.text(4.5, 0.1, "Skip connection", ha="center", fontsize=6.5, color="#3fb950")

    # Stats
    ax.text(11, 2.5, "124,420\nparámetros", ha="center", va="center",
            fontsize=8, color="#fbbf24",
            bbox=dict(boxstyle="round", facecolor="#1f1107", edgecolor="#fbbf24", lw=1.5))

    ax.set_title("SkillGNN — Graph Attention Network para selección de skills (GNN + PPO)",
                 color=FG, fontsize=10, pad=8)
    fig.tight_layout()
    return fig


# ─── TRAZA DE PRUEBA ─────────────────────────────────────────────────────────

# Mapa keyword → skill IDs activados
_KW_MAP = {
    "irracional":    ["real-analysis", "elem-nt", "zfc-axioms", "strat-contra"],
    "√2":            ["real-analysis", "elem-nt", "strat-contra"],
    "primo":         ["elem-nt", "alg-nt"],
    "prime":         ["elem-nt", "alg-nt"],
    "grupo":         ["group-theory", "category-basics"],
    "group":         ["group-theory", "category-basics"],
    "anillo":        ["ring-theory", "tactic-ring"],
    "ring":          ["ring-theory", "tactic-ring"],
    "campo":         ["field-theory"],
    "field":         ["field-theory"],
    "módulo":        ["module-theory"],
    "module":        ["module-theory"],
    "homológ":       ["homological-alg", "alg-topology"],
    "homolog":       ["homological-alg"],
    "yoneda":        ["category-basics", "functors", "nat-trans", "limits"],
    "funtor":        ["functors", "category-basics"],
    "functor":       ["functors", "category-basics"],
    "categoría":     ["category-basics"],
    "category":      ["category-basics"],
    "colímite":      ["limits", "category-basics", "functors"],
    "colimit":       ["limits", "category-basics"],
    "límite":        ["limits"],
    "limit":         ["limits"],
    "lean":          ["lean-kernel", "tactic-simp"],
    "simp":          ["tactic-simp", "lean-kernel"],
    "omega":         ["tactic-omega", "lean-kernel"],
    "linarith":      ["tactic-linarith", "lean-kernel"],
    "exact":         ["tactic-exact", "lean-kernel"],
    "apply":         ["tactic-apply", "lean-kernel"],
    "aesop":         ["tactic-aesop", "lean-kernel"],
    "calc":          ["tactic-calc", "lean-kernel"],
    "inducción":     ["tactic-induction", "strat-inductive"],
    "induction":     ["tactic-induction", "strat-inductive"],
    "nat":           ["lean-kernel", "tactic-omega", "tactic-induction"],
    "succ":          ["tactic-induction", "lean-kernel"],
    "curry":         ["type-theory", "proof-theory", "hott"],
    "howard":        ["type-theory", "proof-theory"],
    "tipos":         ["type-theory"],
    "type":          ["type-theory"],
    "hott":          ["hott", "homotopy-theory"],
    "homotop":       ["homotopy-theory", "alg-topology"],
    "diferencial":   ["diff-geo", "real-analysis"],
    "integral":      ["real-analysis", "complex-analysis"],
    "análisis":      ["real-analysis"],
    "analysis":      ["real-analysis"],
    "topolog":       ["point-set-topo", "alg-topology"],
    "contradicción": ["strat-contra"],
    "contradict":    ["strat-contra"],
    "casos":         ["strat-cases"],
    "probabilidad":  ["prob-theory"],
    "probability":   ["prob-theory"],
    "combinatoria":  ["enumerative", "graph-theory"],
    "combinat":      ["enumerative"],
    "grafo":         ["graph-theory"],
    "graph":         ["graph-theory"],
    "optimiz":       ["convex-opt", "discrete-opt"],
    "theorem":       ["proof-theory", "lean-kernel"],
    "lemma":         ["lean-kernel", "proof-theory"],
    "formal":        ["formal-verif", "lean-kernel"],
    "computab":      ["computability"],
    "demostrar":     ["strat-forward", "proof-theory"],
    "proof":         ["strat-forward", "proof-theory"],
    "prueba":        ["strat-forward", "proof-theory"],
    "backward":      ["strat-backward"],
    "hacia atrás":   ["strat-backward"],
    "constructiv":   ["strat-construct", "type-theory"],
}


def match_skills(query: str) -> list:
    """Devuelve lista de skill IDs que coinciden con la consulta."""
    q = query.lower()
    matched = set()
    for kw, sids in _KW_MAP.items():
        if kw in q:
            matched.update(sids)
    if not matched:
        matched.update(["zfc-axioms", "fol-deduction", "strat-forward"])
    G = build_graph()
    return [s for s in matched if s in G]


def proof_subgraph(G, matched: list) -> set:
    """Calcula el conjunto de nodos: activados + dependencias + tácticas alcanzables."""
    needed = set(s for s in matched if s in G)
    for sk in list(needed):
        needed.update(nx.ancestors(G, sk))
    for sk in matched:
        if sk in G:
            for succ in G.successors(sk):
                if G.nodes[succ].get("cat") in ("Tácticas Lean", "Estrategias"):
                    needed.add(succ)
    return needed


def fig_proof_trace(query: str):
    """Grafo jerárquico de la subred de skills activada para demostrar 'query'."""
    G = build_graph()
    matched = match_skills(query)
    needed = proof_subgraph(G, matched)
    SG = G.subgraph(needed)

    TACTIC_CATS = ("Tácticas Lean", "Estrategias")

    # Layout jerárquico por nivel
    from collections import defaultdict
    level_of = {}
    for n in SG.nodes():
        cat = G.nodes[n].get("cat", "")
        level_of[n] = 2 if cat in TACTIC_CATS else G.nodes[n].get("level", 1)

    buckets = defaultdict(list)
    for n in SG.nodes():
        buckets[level_of[n]].append(n)

    pos = {}
    y_of = {0: 4.0, 1: 2.0, 2: 0.0}
    for lvl, nodes in buckets.items():
        for i, nd in enumerate(nodes):
            x = (i - (len(nodes) - 1) / 2) * 2.2
            pos[nd] = (x, y_of.get(lvl, -lvl * 2.0))

    fig, axes = plt.subplots(1, 2, figsize=(16, 8), facecolor=BG,
                             gridspec_kw={"width_ratios": [3, 1]})

    # ── Subgrafo izquierdo ──────────────────────────────────────────
    ax = axes[0]
    ax.set_facecolor(BG)
    ax.axis("off")

    node_colors, node_sizes, edge_colors_list = [], [], []
    for n in SG.nodes():
        cat = G.nodes[n].get("cat", "")
        if n in matched:
            node_colors.append("#fbbf24"); node_sizes.append(1100)
        elif cat in TACTIC_CATS:
            node_colors.append("#4ade80"); node_sizes.append(650)
        else:
            node_colors.append("#818cf8"); node_sizes.append(480)

    for kind, color, alpha in [("dep", "#4a5568", 0.85),
                                ("trans", "#58a6ff", 0.7),
                                ("analogy", "#4ade80", 0.5)]:
        elist = [(u, v) for u, v, d in SG.edges(data=True)
                 if d.get("kind") == kind and u in pos and v in pos]
        if elist:
            nx.draw_networkx_edges(
                SG, pos, edgelist=elist, ax=ax,
                edge_color=color, alpha=alpha, arrows=True,
                arrowsize=18, width=1.6, node_size=700,
                connectionstyle="arc3,rad=0.08",
            )

    nx.draw_networkx_nodes(SG, pos, ax=ax,
                           node_color=node_colors, node_size=node_sizes,
                           edgecolors=["#ffffff" if c == "#fbbf24" else c
                                       for c in node_colors],
                           linewidths=1.8)

    labels = {n: G.nodes[n]["name"] for n in SG.nodes() if n in pos}
    nx.draw_networkx_labels(SG, pos, labels, ax=ax, font_size=7, font_color=FG)

    # Líneas divisoras de nivel
    if pos:
        x_min = min(p[0] for p in pos.values()) - 1.8
        for lvl, lbl, clr in [(0, "L0 — Fundamentos", "#ef5350"),
                               (1, "L1 — Dominios", "#42a5f5"),
                               (2, "L2 — Tácticas / Estrategias", "#f48fb1")]:
            y = y_of.get(lvl, -lvl * 2.0)
            ax.axhline(y=y + 0.9, color=clr, alpha=0.12, lw=0.8, linestyle="--")
            ax.text(x_min, y, lbl, color=clr, fontsize=7, alpha=0.75, va="center")

    q_short = query[:55] + ("…" if len(query) > 55 else "")
    ax.set_title(f'Subred activada: "{q_short}"', color=FG, fontsize=10, pad=10)

    n_deps = len([n for n in needed if n not in matched
                  and G.nodes[n].get("cat") not in TACTIC_CATS])
    n_tacs = len([n for n in needed if G.nodes[n].get("cat") in TACTIC_CATS])
    ax.legend(
        handles=[
            mpatches.Patch(color="#fbbf24", label=f"Skills activados ({len(matched)})"),
            mpatches.Patch(color="#818cf8", label=f"Dependencias ({n_deps})"),
            mpatches.Patch(color="#4ade80", label=f"Tácticas / Estrategias ({n_tacs})"),
        ],
        loc="lower right", fontsize=7,
        facecolor="#161b22", edgecolor="#30363d", labelcolor=FG,
    )

    # ── Jerarquía textual derecha ───────────────────────────────────
    ax2 = axes[1]
    ax2.set_facecolor(BG)
    ax2.axis("off")
    ax2.set_title("Jerarquía activada", color=FG, fontsize=10, pad=10)

    matched_names = {G.nodes[m]["name"] for m in matched if m in G}
    y = 0.96
    for lvl, title, clr in [(0, "L0 — Fundamentos", "#ef5350"),
                             (1, "L1 — Dominios", "#42a5f5")]:
        nodes_lvl = [n for n in SG.nodes()
                     if level_of.get(n) == lvl
                     and G.nodes[n].get("cat") not in TACTIC_CATS]
        if not nodes_lvl:
            continue
        ax2.text(0.04, y, title, transform=ax2.transAxes,
                 color=clr, fontsize=8.5, fontweight="bold")
        y -= 0.05
        for n in nodes_lvl:
            name = G.nodes[n]["name"]
            star = " ★" if name in matched_names else ""
            c = "#fbbf24" if name in matched_names else FG
            ax2.text(0.08, y, f"• {name}{star}",
                     transform=ax2.transAxes, color=c, fontsize=7.5)
            y -= 0.042
        y -= 0.01

    tac_nodes = [n for n in SG.nodes() if G.nodes[n].get("cat") in TACTIC_CATS]
    if tac_nodes:
        ax2.text(0.04, y, "Tácticas Lean 4", transform=ax2.transAxes,
                 color="#f48fb1", fontsize=8.5, fontweight="bold")
        y -= 0.05
        for n in tac_nodes:
            name = G.nodes[n]["name"]
            cat  = G.nodes[n].get("cat", "")
            pfx  = "▶" if cat == "Tácticas Lean" else "◆"
            clr  = "#f48fb1" if cat == "Tácticas Lean" else "#fff59d"
            ax2.text(0.08, y, f"{pfx} {name}",
                     transform=ax2.transAxes, color=clr, fontsize=7.5)
            y -= 0.042

    fig.tight_layout()
    return fig, len(matched), len(needed)


# ─── INTERFAZ STREAMLIT ───────────────────────────────────────────────────────

tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "⬡ Grafo de Skills",
    "◎ Espacio de Embeddings",
    "⚙ Arquitectura NLE",
    "◈ Complexificación MES",
    "→ Pipeline",
    "⊛ GNN + Estadísticas",
    "🔍 Traza de Prueba",
])

with tab1:
    if _cq:
        st.markdown(f"**Grafo completo** — nodos resaltados según la consulta activa. "
                    f"🟡 activados · 🟣 dependencias · 🟢 tácticas · gris=no involucrados")
    else:
        st.markdown("**Grafo categórico completo de los 76 skills** — nodos por dominio, aristas por tipo de morfismo.")
    cats_filter = ["Todos"] + list(PALETTE.keys())
    sel = st.selectbox("Filtrar por categoría", cats_filter, key="cat_filter")
    with st.spinner("Generando grafo..."):
        fig = fig_skill_graph(None if sel == "Todos" else sel, query=_cq or None)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)
    st.caption("◆ Nivel 0 (fundamentos)  ●  Nivel 1 (dominios)  ▲ Nivel 2 (estrategias) · Aristas: gris=dependencia, azul=traducción, verde=analogía")

with tab2:
    if _cq:
        st.markdown("**Espacio de embeddings** — skills relevantes a la consulta resaltados. "
                    "Los clusters muestran la proximidad semántica entre skills.")
    else:
        st.markdown("**Proyección 2D del espacio de embeddings** — cada skill representado por un vector 256-dim + estructura de grafo.")
    method = st.radio("Método de reducción", ["tsne", "pca"], horizontal=True,
                      format_func=lambda x: "t-SNE (preserva clusters)" if x=="tsne" else "PCA (preserva varianza)")
    with st.spinner("Calculando proyección..."):
        fig = fig_tsne(method, query=_cq or None)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)
    st.caption("Los clusters visibles reflejan la organización semántica del grafo. Skills del mismo dominio se agrupan naturalmente.")

with tab3:
    st.markdown("**Diagrama de bloques completo** — cómo interactúan todos los componentes del sistema.")
    with st.spinner("Generando arquitectura..."):
        fig = fig_architecture()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

with tab4:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("**Proceso de complexificación** — cómo el sistema genera skills emergentes mediante colímites categoriales.")
        with st.spinner("Generando diagrama MES..."):
            fig = fig_mes_complexification()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
    with col2:
        st.markdown("**¿Qué es la complexificación?**")
        st.markdown("""
Un **patrón** P es un funtor P: I → K que selecciona una colección de skills conectados.

El **colímite** cP es el skill "más pequeño" que recibe morfismos de todos los componentes del patrón — representa la *síntesis* de esos conocimientos.

La **complexificación** K' añade cP al grafo junto con los morfismos co-cono, generando un nuevo nivel de abstracción.

Este proceso modela cómo el sistema *aprende*: combina skills conocidos para crear competencias emergentes (Axiomas 8.1–8.4 del paper MES v7.0).

**Verificado formalmente**: 379 tests confirman las propiedades:
- Universalidad del colímite
- Functorialidad de la complexificación
- Principio de multiplicidad
- Conectividad del grafo
        """)

with tab5:
    st.markdown("**Flujo de una consulta** — desde el texto del usuario hasta la respuesta con prueba Lean.")
    with st.spinner("Generando pipeline..."):
        fig = fig_pipeline()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Mapa de calor inter-categorías**")
        st.caption("Similitud coseno entre embeddings centroide de cada dominio matemático.")
        with st.spinner("Calculando similitudes..."):
            fig = fig_heatmap()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)
    with col2:
        st.markdown("**Distribución de skills**")
        with st.spinner("Generando distribución..."):
            fig = fig_distribution()
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

with tab6:
    st.markdown("**Red neuronal GNN + PPO** — arquitectura del sistema de aprendizaje por refuerzo.")
    with st.spinner("Generando diagrama GNN..."):
        fig = fig_gnn()
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)

    st.divider()
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Skills totales", "76", "10 fundamentos + 66 dominio")
    col2.metric("Parámetros GNN+PPO", "124,420", "3 capas GATConv")
    col3.metric("Tests", "379", "17 suites")
    col4.metric("Categorías matemáticas", "14", "4 niveles jerárquicos")

    st.markdown("**Desglose de parámetros GNN:**")
    st.code("""
SkillGNN:
  node_proj    →  feat_dim × 64             (variable)
  GATConv 1   →  64 × 64 × 4 heads         ≈ 16,640
  GATConv 2   →  64 × 64 × 4 heads         ≈ 16,640
  GATConv 3   →  64 × 64 × 4 heads         ≈ 16,640
  skip_proj   →  feat_dim × 64             (variable)
  out_proj    →  128 × 64                  ≈  8,192

ActorCriticNetwork:
  encode_query →  embed_dim × 128           ≈  9,216
  actor        →  128 × num_skills          ≈  9,728
  critic       →  128 × 1                  ≈    129
  shared_net   →  (128+128) × 128 × 2      ≈ 33,024

Total trainable: ~124,420 params
    """, language="")

with tab7:
    st.markdown("**Traza de prueba interactiva** — ingresa un teorema o problema y ve qué skills, dependencias y tácticas activa el sistema.")

    # ── Precargar textarea y detectar auto-ejecución ───────────────────────────
    _auto_run = False
    if "_trace_q" in st.session_state:
        # Botón de ejemplo pulsado → forzar valor en el widget
        st.session_state["_tab7_textarea"] = st.session_state.pop("_trace_q")
    elif _cq and st.session_state.get("_tab7_last_cq") != _cq:
        # Nueva consulta procedente del Demostrador → pre-llenar y auto-ejecutar
        st.session_state["_tab7_textarea"] = _cq
        st.session_state["_tab7_last_cq"] = _cq
        _auto_run = True

    col_a, col_b = st.columns([3, 1])
    with col_a:
        if _auto_run:
            st.caption("↓ Trazando automáticamente la consulta que enviaste al Demostrador")
        query_input = st.text_area(
            "Teorema o problema",
            key="_tab7_textarea",
            placeholder="Ej: Demuestra que √2 es irracional\n     example (n : Nat) : n + 0 = n := by ?\n     Explica el Lema de Yoneda",
            height=90,
            label_visibility="collapsed",
        )
    with col_b:
        st.markdown("**Ejemplos rápidos:**")
        ejemplos = {
            "√2 irracional":    "Demuestra que √2 es irracional",
            "Lema de Yoneda":   "Explica el Lema de Yoneda con funtores y transformaciones naturales",
            "Lean: n + 0 = n":  "example (n : Nat) : n + 0 = n := by ?",
            "Curry-Howard":     "Qué es la correspondencia Curry-Howard entre pruebas y tipos",
            "Colímites":        "Demuestra la propiedad universal del colímite en teoría de categorías",
            "Anillos":          "Demuestra que todo campo es un anillo conmutativo",
            "Inducción Nat":    "Prueba por inducción que la suma de los primeros n naturales es n(n+1)/2",
        }
        for label, ex in ejemplos.items():
            if st.button(label, use_container_width=True, key=f"_ex_{label}"):
                st.session_state["_trace_q"] = ex
                st.rerun()

    run_trace = st.button("Trazar subred →", type="primary",
                          disabled=not (query_input and query_input.strip()))

    if (run_trace or _auto_run) and query_input and query_input.strip():
        with st.spinner("Calculando subred de skills activada..."):
            fig, n_act, n_total = fig_proof_trace(query_input.strip())
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

        st.caption(
            f"**{n_act}** skills directamente activados · "
            f"**{n_total}** nodos en la subred total (dependencias + tácticas) · "
            f"Aristas: gris=dependencia, azul=traducción, verde=analogía"
        )
        st.info(
            "★ = skill activado por tu consulta · "
            "🟡 nodo dorado = skill principal · "
            "🟣 nodo azul = dependencia requerida · "
            "🟢 nodo verde = táctica / estrategia Lean"
        )
