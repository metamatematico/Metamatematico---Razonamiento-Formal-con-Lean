"""
Núcleo Lógico Evolutivo — Visualizaciones del Sistema
======================================================
Grafos, embeddings, arquitectura y diagramas explicativos.
BIOMAT · Centro de Biomatemáticas
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

# ── Botón volver al chat ─────────────────────────────────────────────────────
_back_col, _ = st.columns([1, 5])
with _back_col:
    if st.button("← Volver al chat", width="stretch"):
        st.switch_page("app.py")
st.title("📊 Visualizaciones — Núcleo Lógico Evolutivo")

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


# ─── LIVE DATA HELPERS ────────────────────────────────────────────────────────

_LIVE_CMAP = {
    "algebra": "Álgebra", "geometry": "Geometría",
    "analysis": "Análisis", "topology": "Topología",
    "logic": "Lógica", "number-theory": "T. Números",
    "combinatorics": "Combinatoria", "probability": "Probabilidad",
    "category-theory": "Categorías", "computation": "Computación",
    "optimization": "Optimización", "lean-tactics": "Tácticas Lean",
    "proof-strategies": "Estrategias", "foundations": "Fundamentos",
    "SET": "Fundamentos", "CAT": "Categorías",
    "LOG": "Lógica", "TYPE": "Fundamentos",
}


def _vd():
    """Return viz_data from session_state, or None."""
    return st.session_state.get("viz_data")


def _live_cat(category_key):
    return _LIVE_CMAP.get(category_key, category_key.title() if category_key else "Fundamentos")


def _graph_live(vd):
    """Build nx.DiGraph from live viz_data."""
    G = nx.DiGraph()
    for n in vd.get("graph_nodes", []):
        cat = _live_cat(n.get("category", ""))
        color = PALETTE.get(cat, "#42a5f5")
        G.add_node(n["id"], name=n.get("name", n["id"]),
                   level=n.get("level", 1), cat=cat, color=color)
    for e in vd.get("graph_edges", []):
        mt = e.get("morphism_type", "").upper()
        if "DEPEND" in mt or "REQUIRES" in mt:
            kind = "dep"
        elif "ANALOG" in mt:
            kind = "analogy"
        elif "TRANSLAT" in mt:
            kind = "trans"
        else:
            kind = "dep"
        G.add_edge(e["source"], e["target"], kind=kind)
    return G


def _skill_sets_live(vd):
    """Return (matched_set, dep_set, tactic_set) from viz_data."""
    matched_set = set(vd.get("matched_skills", []))
    dep_set     = set(vd.get("dependency_skills", []))
    tactic_set  = set(vd.get("tactic_skills", []))
    return matched_set, dep_set, tactic_set


def _embeddings_live(vd):
    """Return (embs_array, skill_ids, colors) from viz_data."""
    skill_ids = vd.get("skill_ids_ordered", [])
    raw = vd.get("embeddings", [])
    if not raw or not skill_ids:
        return None, [], []
    embs = np.array(raw)
    nodes_by_id = {n["id"]: n for n in vd.get("graph_nodes", [])}
    colors = [PALETTE.get(_live_cat(nodes_by_id.get(sid, {}).get("category", "")), "#42a5f5")
              for sid in skill_ids]
    return embs, skill_ids, colors


def _skill_list_live(vd):
    """Return list of (id, name, level, cat_display, color) from viz_data."""
    result = []
    nodes_by_id = {n["id"]: n for n in vd.get("graph_nodes", [])}
    for sid in vd.get("skill_ids_ordered", []):
        nd = nodes_by_id.get(sid, {})
        cat = _live_cat(nd.get("category", ""))
        color = PALETTE.get(cat, "#42a5f5")
        result.append((sid, nd.get("name", sid), nd.get("level", 1), cat, color))
    return result

@st.cache_data
def build_graph():
    G = nx.DiGraph()
    for sid, name, level, cat, color in SKILLS:
        G.add_node(sid, name=name, level=level, cat=cat, color=color)
    for src, tgt, kind in EDGES:
        G.add_edge(src, tgt, kind=kind)
    return G


def build_graph_live(vd: dict) -> nx.DiGraph:
    """Construye el grafo desde datos en vivo de get_viz_data() del sistema real."""
    G = nx.DiGraph()
    for node in vd.get("graph_nodes", []):
        cat_display = _live_cat(node.get("category", "foundations"))
        color = PALETTE.get(cat_display, "#42a5f5")
        G.add_node(node["id"],
                   name=node.get("name", node["id"]),
                   level=node.get("level", 1),
                   cat=cat_display,
                   color=color)
    for edge in vd.get("graph_edges", []):
        src, tgt = edge.get("source"), edge.get("target")
        mt = edge.get("morphism_type", "DEPENDENCY")
        kind = ("trans" if "TRANS" in mt else "analogy" if "ANALOG" in mt else "dep")
        if src and tgt and G.has_node(src) and G.has_node(tgt):
            G.add_edge(src, tgt, kind=kind)
    return G


@st.cache_data
def make_layout(_G):
    # Layout jerárquico: x = categoría, y = nivel
    cats = list(PALETTE.keys())
    pos = {}
    cat_counts = {c: 0 for c in cats}
    for sid, name, level, cat, _ in SKILLS:
        cx = cats.index(cat) if cat in cats else 0
        cy = cat_counts.get(cat, 0)
        cat_counts[cat] = cy + 1
        np.random.seed(hash(sid) % (2**31))
        pos[sid] = (cx * 2.5 + np.random.uniform(-0.4, 0.4),
                    level * -3.0 + cy * 0.28 + np.random.uniform(-0.05, 0.05))
    return pos


def make_layout_live(G: nx.DiGraph) -> dict:
    """Layout jerárquico para grafo en vivo (datos del sistema real)."""
    cats = list(PALETTE.keys())
    pos = {}
    cat_counts: dict = {}
    for nid, d in G.nodes(data=True):
        cat = d.get("cat", "Fundamentos")
        level = d.get("level", 1)
        cx = cats.index(cat) if cat in cats else 0
        cy = cat_counts.get(cat, 0)
        cat_counts[cat] = cy + 1
        np.random.seed(hash(nid) % (2**31))
        pos[nid] = (cx * 2.5 + np.random.uniform(-0.4, 0.4),
                    level * -3.0 + cy * 0.28 + np.random.uniform(-0.05, 0.05))
    return pos


def fig_skill_graph(filter_cat=None, query=None):
    # Usar grafo en vivo cuando hay datos del sistema real disponibles
    vd = _vd()
    if vd and vd.get("graph_nodes") and len(vd["graph_nodes"]) > 5:
        G = build_graph_live(vd)
        pos = make_layout_live(G)
        data_source = "vivo"
    else:
        G = build_graph()
        pos = make_layout(G)
        data_source = "estático"
    _ = data_source  # usado para depuración

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
        f"Grafo Categórico de Skills — Núcleo Lógico Evolutivo  ({len(subG.nodes)} nodos){suffix}",
        color=FG, fontsize=10, pad=10)
    fig.tight_layout()
    return fig


# ─── ESPACIO DE EMBEDDINGS ────────────────────────────────────────────────────

@st.cache_data
def build_embeddings():
    """
    Embeddings semánticos de los 76 skills usando el mismo BOW que el sistema real.
    Skills del mismo dominio se agrupan porque comparten vocabulario matemático.
    El espacio es compatible con los query embeddings generados por el chat.
    """
    from nucleo.graph.embeddings import semantic_embed
    _cat_rev = {
        "Fundamentos": "foundations",   "Álgebra": "algebra",
        "Geometría": "geometry",        "Análisis": "analysis",
        "Topología": "topology",        "Lógica": "logic",
        "T. Números": "number-theory",  "Combinatoria": "combinatorics",
        "Probabilidad": "probability",  "Categorías": "category-theory",
        "Computación": "computation",   "Optimización": "optimization",
        "Tácticas Lean": "lean-tactics","Estrategias": "proof-strategies",
    }
    embs = []
    for sid, name, level, cat, _ in SKILLS:
        cat_key = _cat_rev.get(cat, cat.lower())
        # Texto: nombre del skill + tokens del ID (ej. "group-theory" → "group theory")
        text = f"{name} {sid.replace('-', ' ')}"
        text_emb = semantic_embed(text, category=cat_key, level=level, dim=256)
        struct_emb = np.zeros(64)   # sin grafo en contexto estático
        embs.append(np.concatenate([text_emb, struct_emb]))
    return np.array(embs, dtype=np.float32)


def fig_tsne(method="tsne", query=None):
    vd = _vd()
    skill_list = list(SKILLS)
    if vd and vd.get("embeddings") and vd.get("skill_ids_ordered"):
        _le, _ids, _cols = _embeddings_live(vd)
        if _le is not None and len(_le) > 1:
            embs = _le
            skill_list = _skill_list_live(vd)
        else:
            embs = build_embeddings()
    else:
        embs = build_embeddings()

    n_skills = len(skill_list)

    # ── Historial de query embeddings del chat ────────────────────────────────
    query_history = st.session_state.get("query_embeddings", [])
    q_embs = np.array([q["embedding"] for q in query_history]) if query_history else None
    q_texts = [q["text"] for q in query_history] if query_history else []

    # Combinar skills + queries para proyección conjunta
    if q_embs is not None and len(q_embs) > 0:
        all_embs = np.vstack([embs, q_embs])
    else:
        all_embs = embs

    if method == "tsne":
        perp = min(15, max(5, len(all_embs) // 3))
        proj = TSNE(n_components=2, random_state=42, perplexity=perp,
                    n_iter=1000, init="pca").fit_transform(all_embs)
        xlabel, ylabel = "t-SNE 1", "t-SNE 2"
        n_label = f"{n_skills} skills"
        if q_embs is not None and len(q_embs) > 0:
            n_label += f" + {len(q_embs)} quer{'y' if len(q_embs)==1 else 'ies'}"
        title = f"Espacio de Embeddings — t-SNE ({n_label})"
        subtitle = "Proximidad = vocabulario matemático compartido"
    else:
        pca = PCA(n_components=2, random_state=42)
        proj = pca.fit_transform(all_embs)
        xlabel = f"PC1 ({pca.explained_variance_ratio_[0]:.0%} varianza)"
        ylabel = f"PC2 ({pca.explained_variance_ratio_[1]:.0%} varianza)"
        n_label = f"{n_skills} skills"
        if q_embs is not None and len(q_embs) > 0:
            n_label += f" + {len(q_embs)} quer{'y' if len(q_embs)==1 else 'ies'}"
        title  = f"Espacio de Embeddings — PCA ({n_label})"
        subtitle = "PC1/PC2 capturan la mayor varianza entre los vectores BOW"

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
    for i, (sid, name, level, cat, color) in enumerate(skill_list):
        in_query = sid in (matched_set | dep_set | tactic_set)
        if query and not in_query:
            ax.scatter(proj[i, 0], proj[i, 1],
                       c=[color], s=30, marker=markers[level],
                       edgecolors="#0d1117", linewidths=0.3, alpha=0.18, zorder=3)

    # Luego los skills relevantes (encima)
    for i, (sid, name, level, cat, color) in enumerate(skill_list):
        in_matched = sid in matched_set
        in_tactic  = sid in tactic_set
        in_dep     = sid in dep_set
        in_q       = in_matched or in_tactic or in_dep

        if query and not in_q:
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
        show = in_q or (not query and level == 0)
        if show:
            fc = "#fbbf24" if in_matched else "#4ade80" if in_tactic else \
                 "#93c5fd" if in_dep else color
            ax.annotate(name, (proj[i, 0], proj[i, 1]),
                        fontsize=6.5 if in_matched else 5.5,
                        color=fc, fontweight="bold" if in_matched else "normal",
                        xytext=(5, 5), textcoords="offset points",
                        arrowprops=dict(arrowstyle="-", color=fc, lw=0.5, alpha=0.5)
                        if in_matched else None)

    # ── Query embeddings del historial del chat ───────────────────────────────
    if q_embs is not None and len(q_embs) > 0:
        QUERY_COLOR = "#f97316"   # naranja
        for j, txt in enumerate(q_texts):
            qi = n_skills + j
            is_current = (txt == query)
            sz  = 380 if is_current else 200
            ec  = "#ffffff" if is_current else "#f97316"
            lw  = 2.5 if is_current else 1.5
            ax.scatter(proj[qi, 0], proj[qi, 1],
                       c=[QUERY_COLOR], s=sz, marker="*",
                       edgecolors=ec, linewidths=lw, alpha=0.95, zorder=9)
            label = (txt[:40] + "…") if len(txt) > 40 else txt
            ax.annotate(
                label, (proj[qi, 0], proj[qi, 1]),
                fontsize=6.8 if is_current else 5.8,
                color=QUERY_COLOR,
                fontweight="bold" if is_current else "normal",
                xytext=(8, 6), textcoords="offset points",
                arrowprops=dict(arrowstyle="-", color=QUERY_COLOR, lw=0.6, alpha=0.6),
            )

    # Leyenda
    if query:
        handles = [
            mpatches.Patch(color="#fbbf24", label=f"Skills activados ({len(matched_set)})"),
            mpatches.Patch(color="#818cf8", label=f"Dependencias ({len(dep_set)})"),
            mpatches.Patch(color="#4ade80", label=f"Tácticas ({len(tactic_set)})"),
            mpatches.Patch(color="#3d444d", label="No involucrados"),
        ]
        title += f'\n"{query[:55]}{"…" if len(query)>55 else ""}"'
    else:
        handles = [mpatches.Patch(color=c, label=k) for k, c in PALETTE.items()]
    if q_embs is not None and len(q_embs) > 0:
        handles.append(plt.Line2D([0], [0], marker="*", color="w",
                                  markerfacecolor="#f97316", markersize=9,
                                  label=f"Queries del chat ({len(q_embs)})"))
    ax.legend(handles=handles, loc="upper left", ncol=1, fontsize=6.5,
              framealpha=0.2, edgecolor="#21262d", labelcolor=FG)

    ax.set_xlabel(xlabel, color=FG, fontsize=9)
    ax.set_ylabel(ylabel, color=FG, fontsize=9)
    ax.set_title(f"{title}\n{subtitle}", color=FG, fontsize=9, pad=10)
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

    ax.set_title("Arquitectura del Núcleo Lógico Evolutivo  —  Σ_t = (L, CR_t, G_t, F)",
                 color=FG, fontsize=12, pad=8, fontweight="bold")
    fig.tight_layout()
    return fig


# ─── MES: COMPLEXIFICACIÓN ────────────────────────────────────────────────────

def _fan_positions(skill_ids, y, x_spread=1.6):
    """Distribuye skill_ids uniformemente en y=y con separación x_spread."""
    n = len(skill_ids)
    if n == 0:
        return {}
    xs = [(i - (n - 1) / 2) * x_spread for i in range(n)]
    return {sid: (xs[i], y) for i, sid in enumerate(skill_ids)}


def fig_mes_complexification(query=None):
    """Complexificación MES — estática (sin consulta) o dinámica (con consulta)."""

    # ── VERSIÓN DINÁMICA ──────────────────────────────────────────────────────
    if query:
        from collections import Counter
        TACTIC_CATS = ("Tácticas Lean", "Estrategias")
        vd = _vd()
        _vd_match = vd and vd.get("matched_skills") and             vd.get("query", "").strip() == query.strip()
        if _vd_match:
            G = _graph_live(vd)
            _ms, _ds, _ts = _skill_sets_live(vd)
            matched    = list(_ms)[:5]
            dep_set    = _ds - set(matched)
            tactic_set = _ts
            needed     = set(matched) | dep_set | tactic_set
        else:
            G = build_graph()
            matched   = match_skills(query)[:5]
            needed    = proof_subgraph(G, matched)
            tactic_set = {n for n in needed if G.nodes[n].get("cat") in TACTIC_CATS}
            dep_set    = needed - set(matched) - tactic_set

        # Dominio predominante → nombre del colímite
        cats = [G.nodes[m].get("cat", "") for m in matched if m in G]
        _ci = vd.get("colimit_info", {}) if _vd_match else {}
        dom = _ci.get("dominant_category") or               (Counter(cats).most_common(1)[0][0] if cats else "Matemáticas")
        q_short   = query[:34] + ("…" if len(query) > 34 else "")
        cp_label  = f"cP — {dom}\n«{q_short}»"

        fig, axes = plt.subplots(1, 3, figsize=(14, 5.2), facecolor=BG)

        # ── Panel 1: Patrón P ─────────────────────────────────────────────────
        ax = axes[0]
        ax.set_facecolor(BG); ax.axis("off")
        ax.set_xlim(-3.2, 3.2); ax.set_ylim(-2.8, 2.6)
        ax.set_title(f"1. Patrón P ⊂ K\nSkills activados por la consulta",
                     color=FG, fontsize=8.5, pad=6)

        pat_pos = _fan_positions(matched, y=0.0, x_spread=min(2.0, 5.0 / max(len(matched), 1)))

        # Edges entre skills del patrón que existen en EDGES
        for src, tgt, kind in EDGES:
            if src in pat_pos and tgt in pat_pos:
                col = {"dep": "#4a5568", "trans": "#58a6ff", "analogy": "#4ade80"}.get(kind, "#4a5568")
                ax.annotate("", xy=pat_pos[tgt], xytext=pat_pos[src],
                            arrowprops=dict(arrowstyle="-|>", color=col, lw=1.0, alpha=0.7,
                                            connectionstyle="arc3,rad=0.1"))

        for i, sid in enumerate(matched):
            x, y = pat_pos[sid]
            c    = G.nodes[sid].get("color", "#42a5f5")
            cat  = G.nodes[sid].get("cat", "")
            ax.scatter(x, y, s=500, c=c, zorder=5, edgecolors="#fbbf24", lw=1.8)
            ax.text(x, y + 0.28, f"P{i+1}", ha="center", fontsize=8,
                    color="#fbbf24", fontweight="bold")
            ax.text(x, y - 0.42, G.nodes[sid]["name"], ha="center", fontsize=6.5,
                    color=FG, wrap=True)
            ax.text(x, y - 0.72, f"({cat})", ha="center", fontsize=5.5, color="#6e7681")

        ax.text(0, -1.9, f"Patrón P: I → K  ({len(matched)} skills)\nDominio: {dom}",
                ha="center", fontsize=7, color="#9ca3af",
                bbox=dict(boxstyle="round", facecolor="#161b22", edgecolor="#21262d"))

        # ── Panel 2: Colímite cP ──────────────────────────────────────────────
        ax = axes[1]
        ax.set_facecolor(BG); ax.axis("off")
        ax.set_xlim(-3.2, 3.2); ax.set_ylim(-2.8, 2.6)
        ax.set_title("2. Colímite cP\n(skill emergente: síntesis categórica)",
                     color=FG, fontsize=8.5, pad=6)

        # Pattern skills tenues
        for sid in matched:
            x, y = pat_pos[sid]
            c    = G.nodes[sid].get("color", "#42a5f5")
            ax.scatter(x, y, s=220, c=c, zorder=3, alpha=0.35,
                       edgecolors="#21262d", lw=0.6)
            ax.text(x, y - 0.38, G.nodes[sid]["name"], ha="center",
                    fontsize=5.5, color="#484f58")

        # Nodo cP
        ax.scatter(0, 1.7, s=800, c="#f59e0b", zorder=6, edgecolors="#fbbf24", lw=2.5)
        ax.text(0, 1.7, "cP", ha="center", va="center", fontsize=12,
                color="black", fontweight="bold", zorder=7)
        for ln in cp_label.split("\n"):
            pass  # handled below
        cp_lines = cp_label.split("\n")
        ax.text(0, 2.25, cp_lines[0], ha="center", fontsize=7.5,
                color="#fbbf24", fontweight="bold")
        if len(cp_lines) > 1:
            ax.text(0, 2.0, cp_lines[1], ha="center", fontsize=6.5, color="#fbbf24")

        # Co-cono: Pᵢ → cP
        for sid in matched:
            x, y = pat_pos[sid]
            ax.annotate("", xy=(0, 1.7), xytext=(x, y),
                        arrowprops=dict(arrowstyle="-|>", color="#f59e0b",
                                        lw=1.3, alpha=0.75,
                                        connectionstyle="arc3,rad=0.05"))

        ax.text(0, -1.9, f"cᵢ: Pᵢ → cP  (co-cono universal)\nPropiedad universal verificada formalmente",
                ha="center", fontsize=6.5, color="#9ca3af",
                bbox=dict(boxstyle="round", facecolor="#161b22", edgecolor="#21262d"))

        # ── Panel 3: K' Complexificada ────────────────────────────────────────
        ax = axes[2]
        ax.set_facecolor(BG); ax.axis("off")
        ax.set_xlim(-3.5, 3.5); ax.set_ylim(-2.8, 3.0)
        n_total = len(needed) + 1  # +1 por cP
        ax.set_title(f"3. K' Complexificada\n({n_total} nodos: {len(matched)} activados + "
                     f"{len(dep_set)} deps + {len(tactic_set)} tácticas + cP)",
                     color=FG, fontsize=8, pad=6)

        dep_show   = sorted(dep_set)[:5]
        tac_show   = sorted(tactic_set)[:4]
        mat_show   = matched[:5]

        pos3 = {}
        pos3.update(_fan_positions(mat_show, y=1.1, x_spread=min(1.8, 6.0 / max(len(mat_show), 1))))
        pos3.update(_fan_positions(dep_show, y=-0.2, x_spread=min(1.4, 6.0 / max(len(dep_show), 1))))
        pos3.update(_fan_positions(tac_show, y=-1.5, x_spread=min(1.6, 6.0 / max(len(tac_show), 1))))
        pos3["_cP"] = (0, 2.4)

        # Edges del subgrafo
        SG = G.subgraph(needed)
        for src, tgt, d in SG.edges(data=True):
            if src in pos3 and tgt in pos3:
                kind = d.get("kind", "dep")
                col  = {"dep": "#374151", "trans": "#58a6ff",
                        "analogy": "#3fb950"}.get(kind, "#374151")
                ax.annotate("", xy=pos3[tgt], xytext=pos3[src],
                            arrowprops=dict(arrowstyle="-|>", color=col, lw=0.9,
                                            alpha=0.7, connectionstyle="arc3,rad=0.08"))

        # Nodos del subgrafo
        for sid, (x, y) in pos3.items():
            if sid == "_cP":
                ax.scatter(x, y, s=650, c="#f59e0b", zorder=6,
                           edgecolors="#fbbf24", lw=2.2)
                ax.text(x, y, "cP", ha="center", va="center", fontsize=10,
                        color="black", fontweight="bold", zorder=7)
                ax.text(x, y + 0.42, "Síntesis ✦", ha="center",
                        fontsize=6.5, color="#fbbf24")
            else:
                if sid in matched:
                    c, ec, sz, fc = "#fbbf24", "#ffffff", 420, "#fbbf24"
                elif sid in tactic_set:
                    c, ec, sz, fc = "#4ade80", "#4ade80", 240, "#4ade80"
                else:
                    c, ec, sz, fc = "#818cf8", "#818cf8", 200, "#93c5fd"
                ax.scatter(x, y, s=sz, c=c, zorder=5, edgecolors=ec, lw=1.2)
                ax.text(x, y - 0.34, G.nodes[sid]["name"], ha="center",
                        fontsize=6, color=fc)

        # Co-conos hacia cP
        for sid in mat_show:
            if sid in pos3:
                ax.annotate("", xy=pos3["_cP"], xytext=pos3[sid],
                            arrowprops=dict(arrowstyle="-|>", color="#f59e0b",
                                            lw=1.0, alpha=0.45,
                                            connectionstyle="arc3,rad=0.0"))

        # Líneas divisoras
        for y_line, lbl, clr in [(-0.85, "↑ Deps / ↓ Activados", "#818cf8"),
                                  (-1.05, "↑ Tácticas Lean", "#4ade80")]:
            ax.axhline(y=y_line, color=clr, alpha=0.1, lw=0.7, linestyle="--")

        ax.legend(
            handles=[
                mpatches.Patch(color="#fbbf24", label=f"Activados ({len(matched)})"),
                mpatches.Patch(color="#818cf8", label=f"Dependencias ({len(dep_set)})"),
                mpatches.Patch(color="#4ade80", label=f"Tácticas ({len(tactic_set)})"),
                mpatches.Patch(color="#f59e0b", label="cP — colímite emergente"),
            ],
            loc="lower right", fontsize=6,
            facecolor="#161b22", edgecolor="#30363d", labelcolor=FG,
        )

        fig.suptitle(
            f"MES — Complexificación para «{q_short}»  "
            f"(Axiomas 8.1–8.4 · Teoremas 8.5–8.7)",
            color=FG, fontsize=10, y=1.01,
        )
        fig.tight_layout()
        return fig

    # ── VERSIÓN ESTÁTICA (ejemplo álgebra) ───────────────────────────────────
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
    for x, y, lbl, _ in nodes_pat:
        ax.scatter(x, y, s=150, c="#374151", zorder=3, alpha=0.5)
    ax.scatter(0, 1.5, s=600, c="#f59e0b", zorder=6, edgecolors="#fbbf24", lw=2)
    ax.text(0, 1.5, "cP", ha="center", va="center", fontsize=10,
            color="black", fontweight="bold", zorder=7)
    ax.text(0, 2.1, "Álgebra Abstracta\n(skill emergente)", ha="center",
            fontsize=7.5, color="#fbbf24")
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
    # Prefer live data from get_viz_data() when available and query matches
    vd = _vd()
    if vd and vd.get("matched_skills") and             vd.get("query", "").strip() == (query or "").strip():
        return list(vd["matched_skills"])
    # Fallback: keyword map
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

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "⬡ Grafo de Skills",
    "◎ Espacio de Embeddings",
    "⚙ Arquitectura NLE",
    "◈ Complexificación MES",
    "→ Pipeline",
    "⊛ GNN + Estadísticas",
    "🔍 Traza de Prueba",
    "🤖 Agentes",
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
    st.pyplot(fig, width="stretch")
    plt.close(fig)
    st.caption("◆ Nivel 0 (fundamentos)  ●  Nivel 1 (dominios)  ▲ Nivel 2 (estrategias) · Aristas: gris=dependencia, azul=traducción, verde=analogía")

with tab2:
    _qh = st.session_state.get("query_embeddings", [])
    st.markdown("### Espacio de embeddings del NLE")

    # Explicación del espacio
    with st.expander("¿Qué es este espacio y cómo se construye?", expanded=False):
        st.markdown("""
**Cada skill es un vector de 320 dimensiones** con tres partes:

| Dims | Contenido | Qué captura |
|---|---|---|
| 0–63 | BOW sobre 64 términos matemáticos | Qué vocabulario técnico usa el skill |
| 64–77 | Señal de categoría × 5.0 | A qué dominio pertenece (álgebra, análisis…) |
| 78–80 | Nivel del skill | Fundamento (L0), dominio (L1) o estrategia (L2) |
| 81–319 | Estructura del grafo | Grado de entrada/salida en el grafo categórico |

**Las queries del chat** usan el mismo espacio (dims 0–63 y 64–77). Por eso puedes ver dónde "cae" cada consulta — si preguntas sobre grupos, la estrella aparecerá cerca del cluster de Álgebra.

La reducción **t-SNE / PCA** proyecta estos 320 dims a 2D manteniendo la proximidad relativa.
        """)

    if _cq:
        st.info(
            f"🔎 Consulta activa resaltada. "
            f"{'**' + str(len(_qh)) + ' quer' + ('y' if len(_qh)==1 else 'ies') + '** del historial proyectadas como ★' if _qh else 'Usa el chat para ver tus queries proyectadas como estrellas naranjas.'}"
        )
    elif _qh:
        st.info(
            f"**{len(_qh)} quer{'y' if len(_qh)==1 else 'ies'} del historial** "
            "proyectadas como estrellas naranjas ★ — su posición indica qué dominio activaron."
        )
    else:
        st.info(
            "Aún no hay queries del chat. Escribe una pregunta matemática, "
            "haz click en **'📊 Ver grafo · embeddings…'** y vuelve aquí para "
            "ver dónde cae tu consulta en el espacio vectorial."
        )

    method = st.radio("Método de reducción", ["tsne", "pca"], horizontal=True,
                      format_func=lambda x: "t-SNE — preserva agrupaciones locales" if x=="tsne" else "PCA — preserva varianza máxima")
    with st.spinner("Calculando proyección..."):
        fig = fig_tsne(method, query=_cq or None)
    st.pyplot(fig, width="stretch")
    plt.close(fig)

    if _qh:
        st.caption(
            "★ Estrellas naranjas = queries del historial del chat. "
            "La query activa (si la hay) aparece más grande con borde blanco. "
            "Proximidad = vocabulario matemático compartido entre skill y consulta."
        )
    else:
        st.caption(
            "Cada punto = 1 skill. Agrupaciones por color = mismo dominio matemático. "
            "Los skills de una misma categoría se agrupan porque comparten vocabulario técnico."
        )

with tab3:
    st.markdown("**Diagrama de bloques completo** — cómo interactúan todos los componentes del sistema.")
    with st.spinner("Generando arquitectura..."):
        fig = fig_architecture()
    st.pyplot(fig, width="stretch")
    plt.close(fig)

with tab4:
    col1, col2 = st.columns([2, 1])
    with col1:
        if _cq:
            st.markdown(
                f"**Complexificación MES para la consulta activa** — los tres paneles muestran "
                f"el patrón P, el colímite cP y la estructura K' específicos del teorema analizado."
            )
        else:
            st.markdown("**Proceso de complexificación** — cómo el sistema genera skills emergentes mediante colímites categoriales (ejemplo: Álgebra Abstracta).")
        with st.spinner("Generando diagrama MES..."):
            fig = fig_mes_complexification(query=_cq or None)
        st.pyplot(fig, width="stretch")
        plt.close(fig)
    with col2:
        st.markdown("**¿Qué es la complexificación?**")
        if _cq:
            _vd4 = _vd()
            _vd4_match = _vd4 and _vd4.get("matched_skills") and                 _vd4.get("query", "").strip() == _cq.strip()
            if _vd4_match:
                matched_info = list(_vd4["matched_skills"])
                G_tmp = _graph_live(_vd4)
            else:
                matched_info = match_skills(_cq)
                G_tmp = build_graph()
            st.markdown(
                f"Para la consulta activa, el sistema identificó **{len(matched_info)} skills** "
                f"que forman el patrón P."
            )
            _ci4 = _vd4.get("colimit_info", {}) if _vd4_match else {}
            if _ci4.get("dominant_category"):
                st.caption(f"Dominio predominante: **{_ci4['dominant_category']}** "
                           f"· deps: {_ci4.get('n_deps', '?')} "
                           f"· tácticas: {_ci4.get('n_tactics', '?')}")
            _cr4 = _vd4.get("cr_info", {}) if _vd4_match else {}
            if _cr4:
                st.caption(f"CR: {_cr4.get('source_cr','?')} "
                           f"→ {_cr4.get('action_type','?')} "
                           f"conf={_cr4.get('confidence','?')}")
            st.markdown("**Patrón activado:**")
            for sid in matched_info:
                if sid in G_tmp:
                    name = G_tmp.nodes[sid]["name"]
                    cat  = G_tmp.nodes[sid].get("cat", "")
                    st.markdown(f"- **{name}** _{cat}_")
            st.divider()
        st.markdown("""
Un **patrón** P es un funtor P: I → K que selecciona una colección de skills conectados.

El **colímite** cP es el skill "más pequeño" que recibe morfismos de todos los componentes del patrón — representa la *síntesis* de esos conocimientos.

La **complexificación** K'  añade cP al grafo junto con los morfismos co-cono, generando un nuevo nivel de abstracción.

Este proceso modela cómo el sistema *aprende*: combina skills conocidos para crear competencias emergentes (Axiomas 8.1–8.4 del paper MES v7.0).

**Verificado formalmente**: 379 tests confirman:
- Universalidad del colímite
- Functorialidad de la complexificación
- Principio de multiplicidad
- Conectividad del grafo
        """)

with tab5:
    st.markdown("**Flujo de una consulta** — desde el texto del usuario hasta la respuesta con prueba Lean.")
    with st.spinner("Generando pipeline..."):
        fig = fig_pipeline()
    st.pyplot(fig, width="stretch")
    plt.close(fig)
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Mapa de calor inter-categorías**")
        st.caption("Similitud coseno entre embeddings centroide de cada dominio matemático.")
        with st.spinner("Calculando similitudes..."):
            fig = fig_heatmap()
        st.pyplot(fig, width="stretch")
        plt.close(fig)
    with col2:
        st.markdown("**Distribución de skills**")
        with st.spinner("Generando distribución..."):
            fig = fig_distribution()
        st.pyplot(fig, width="stretch")
        plt.close(fig)

with tab6:
    st.markdown("**Red neuronal GNN + PPO** — arquitectura del sistema de aprendizaje por refuerzo.")
    with st.spinner("Generando diagrama GNN..."):
        fig = fig_gnn()
    st.pyplot(fig, width="stretch")
    plt.close(fig)

    st.divider()
    col1, col2, col3, col4 = st.columns(4)
    _vd6 = _vd()
    _n_skills6 = len(_vd6["graph_nodes"]) if _vd6 and _vd6.get("graph_nodes") else 76
    col1.metric("Skills totales", str(_n_skills6), "10 fundamentos + 66 dominio")
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
            if st.button(label, width="stretch", key=f"_ex_{label}"):
                st.session_state["_trace_q"] = ex
                st.rerun()

    run_trace = st.button("Trazar subred →", type="primary",
                          disabled=not (query_input and query_input.strip()))

    if (run_trace or _auto_run) and query_input and query_input.strip():
        with st.spinner("Calculando subred de skills activada..."):
            fig, n_act, n_total = fig_proof_trace(query_input.strip())
        st.pyplot(fig, width="stretch")
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

# ── Tab 8: Agentes ─────────────────────────────────────────────────────────────
with tab8:
    import json as _json
    from pathlib import Path as _Path

    st.markdown("**Sistema multi-agente** — jerarquía L0→L1→L2→L3, pesos entrenados y rendimiento por categoría.")

    # Cargar summary de entrenamiento
    _summary_path = _Path(__file__).parent.parent / "training" / "agents" / "training_summary.json"
    _best_dir     = _Path(__file__).parent.parent / "training" / "agents" / "best"
    _summary = []
    if _summary_path.exists():
        with open(_summary_path, encoding="utf-8") as _f:
            _summary = _json.load(_f)

    # ── Grafo jerárquico de agentes ─────────────────────────────────────────────
    st.markdown("### Grafo categórico: Skills → ColimitAgents → Orchestrator")

    def _fig_agents():
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        import networkx as nx
        import numpy as np

        _CAT_COLORS = {
            "algebra":         "#42a5f5", "analysis":       "#ab47bc",
            "category-theory": "#ef5350", "combinatorics":  "#26c6da",
            "computation":     "#ff7043", "geometry":       "#66bb6a",
            "lean-tactics":    "#ffa726", "logic":          "#ec407a",
            "number-theory":   "#8d6e63", "optimization":   "#29b6f6",
            "probability":     "#9ccc65", "proof-strategies":"#78909c",
            "set-theory":      "#ffee58", "topology":       "#26a69a",
        }
        # IDs coinciden exactamente con los de SKILLS (validados)
        _CAT_SKILLS = {
            "algebra":          ["group-theory","ring-theory","field-theory","module-theory","comm-algebra","homological-alg","repres-theory"],
            "analysis":         ["real-analysis","complex-analysis","func-analysis","harmonic-anal","pde-techniques","operator-theory"],
            "category-theory":  ["category-basics","functors","nat-trans","limits","higher-cat","homol-cat"],
            "combinatorics":    ["graph-theory","enumerative","ramsey-theory","extremal-comb","alg-comb","prob-method"],
            "computation":      ["computability","complexity","algo-analysis","formal-verif"],
            "geometry":         ["euclidean-geo","projective-geo","diff-geo","alg-geo","symplectic-geo","complex-geo"],
            "lean-tactics":     ["lean-kernel","tactic-simp","tactic-ring","tactic-omega","tactic-linarith","tactic-aesop","tactic-exact","tactic-apply","tactic-induction","tactic-calc"],
            "logic":            ["fol-deduction","fol-metatheory","model-theory","proof-theory","hott"],
            "number-theory":    ["elem-nt","alg-nt","analytic-nt","arith-geo"],
            "optimization":     ["convex-opt","discrete-opt","variational"],
            "probability":      ["prob-theory","stochastic","martingale","ergodic"],
            "proof-strategies": ["strat-backward","strat-forward","strat-contra","strat-cases","strat-inductive","strat-construct"],
            "set-theory":       ["zfc-axioms","ordinals","category-basics","functors","nat-trans","limits"],
            "topology":         ["point-set-topo","alg-topology","diff-topology","homotopy-theory","geometric-topo"],
        }

        G = nx.DiGraph()
        # Nodo orquestador (L3)
        G.add_node("ORCHESTRATOR", kind="orch", label="Orchestrator\nL3", color="#f59e0b")
        # 14 ColimitAgents (L2)
        for cat in _CAT_COLORS:
            G.add_node(cat, kind="agent", label=cat.replace("-", "\n"), color=_CAT_COLORS[cat])
            G.add_edge(cat, "ORCHESTRATOR")
        # Skills representativos (L1) — 3 por agente para no saturar
        for cat, skills in _CAT_SKILLS.items():
            for sk in skills[:3]:
                nid = f"{cat}::{sk}"
                G.add_node(nid, kind="skill", label=sk.replace("-", "\n"), color=_CAT_COLORS[cat])
                G.add_edge(nid, cat)

        fig, ax = plt.subplots(figsize=(18, 10), facecolor="#080c12")
        ax.set_facecolor("#080c12")
        ax.axis("off")

        # Layout manual: orquestador arriba, agentes en el medio, skills abajo
        pos = {}
        cats = list(_CAT_COLORS.keys())
        n = len(cats)
        pos["ORCHESTRATOR"] = (0.5, 0.95)
        for i, cat in enumerate(cats):
            x = (i + 0.5) / n
            pos[cat] = (x, 0.60)
            skills = _CAT_SKILLS.get(cat, [])[:3]
            for j, sk in enumerate(skills):
                nid = f"{cat}::{sk}"
                sw = 1.0 / n
                pos[nid] = (x - sw/3 + j * sw/3, 0.25)

        # Edges
        for u, v in G.edges():
            xu, yu = pos.get(u, (0, 0))
            xv, yv = pos.get(v, (0, 0))
            ku = G.nodes[u].get("kind")
            col = "#2d3748" if ku == "skill" else "#4a5568"
            ax.annotate("", xy=(xv, yv), xytext=(xu, yu),
                        xycoords="axes fraction", textcoords="axes fraction",
                        arrowprops=dict(arrowstyle="-|>", color=col, lw=0.6, alpha=0.5,
                                        connectionstyle="arc3,rad=0.0"))

        # Nodes
        for nid, d in G.nodes(data=True):
            if nid not in pos:
                continue
            x, y = pos[nid]
            kind  = d.get("kind")
            color = d.get("color", "#374151")
            if kind == "orch":
                ax.scatter(x, y, s=2000, c=[color], transform=ax.transAxes,
                           zorder=8, edgecolors="#ffffff", linewidths=2)
                ax.text(x, y, "L3\nOrch", ha="center", va="center", fontsize=7,
                        fontweight="bold", color="#000000", zorder=9, transform=ax.transAxes)
            elif kind == "agent":
                # ¿tiene pesos?
                has_wt = (_best_dir / f"{nid}.pt").exists()
                ec = "#ffffff" if has_wt else "#6b7280"
                lw = 2.0 if has_wt else 0.8
                ax.scatter(x, y, s=700, c=[color], transform=ax.transAxes,
                           zorder=7, edgecolors=ec, linewidths=lw, marker="s")
                short = nid[:8] if len(nid) > 8 else nid
                ax.text(x, y + 0.025, short, ha="center", va="bottom", fontsize=5.5,
                        color="#e5e7eb", zorder=8, transform=ax.transAxes, fontweight="bold")
                # F1 acc badge
                acc = next((s["phase1_val_acc"] for s in _summary if s["category"] == nid), None)
                if acc is not None:
                    ax.text(x, y - 0.025, f"F1={acc:.2f}", ha="center", va="top", fontsize=4.5,
                            color="#9ca3af", zorder=8, transform=ax.transAxes)
            else:
                ax.scatter(x, y, s=80, c=[color], transform=ax.transAxes,
                           zorder=6, edgecolors="#374151", linewidths=0.3, alpha=0.7)

        # Leyenda
        legend_h = [
            mpatches.Patch(color="#f59e0b", label="L3 Orchestrator"),
            mpatches.Patch(color="#6366f1", label="L2 ColimitAgent (borde blanco = pesos cargados)"),
            mpatches.Patch(color="#6b7280", label="L1 Skills (3 por agente)"),
        ]
        ax.legend(handles=legend_h, loc="lower center", bbox_to_anchor=(0.5, -0.02),
                  ncol=3, fontsize=7, facecolor="#0d1117", edgecolor="#21262d", labelcolor="#9ca3af")
        ax.set_title("Jerarquía L0→L1→L2→L3 · 14 ColimitAgents · 76 skills",
                     color="#c9d1d9", fontsize=11, pad=8)
        fig.tight_layout()
        return fig

    with st.spinner("Generando grafo de agentes..."):
        _fig_ag = _fig_agents()
    st.pyplot(_fig_ag, width="stretch")
    plt.close(_fig_ag)

    # ── Tabla de estadísticas ────────────────────────────────────────────────────
    st.markdown("### Resultados de entrenamiento por agente")
    if _summary:
        _col_names = ["Categoría", "Muestras", "F1 routing acc", "F2 tactic acc", "Pesos"]
        _rows = []
        for s in _summary:
            cat    = s["category"]
            n_samp = s.get("train_samples", 0)
            f1     = s.get("phase1_val_acc", 0.0)
            f2     = s.get("phase2_tactic_acc", 0.0)
            has_wt = "✓" if (_best_dir / f"{cat}.pt").exists() else "✗"
            _rows.append({
                "Categoría":      cat,
                "Muestras":       f"{n_samp:,}",
                "F1 routing acc": f"{f1:.3f}",
                "F2 tactic acc":  f"{f2:.3f}",
                "Pesos":          has_wt,
            })
        import pandas as _pd
        _df = _pd.DataFrame(_rows)
        st.dataframe(_df, use_container_width=True, hide_index=True)
    else:
        st.warning("No se encontró training_summary.json — entrena primero con scripts/train_multiagent.py")

    # ── Bar chart F1 / F2 ────────────────────────────────────────────────────────
    if _summary:
        st.markdown("### F1 routing vs F2 tactic accuracy por agente")
        _cats  = [s["category"] for s in _summary]
        _f1s   = [s.get("phase1_val_acc", 0.0) for s in _summary]
        _f2s   = [s.get("phase2_tactic_acc", 0.0) for s in _summary]
        _x     = np.arange(len(_cats))
        _w     = 0.4
        _fig_b, _ax_b = plt.subplots(figsize=(14, 4), facecolor="#080c12")
        _ax_b.set_facecolor("#0d1117")
        _ax_b.bar(_x - _w/2, _f1s, _w, label="F1 routing", color="#6366f1", alpha=0.85)
        _ax_b.bar(_x + _w/2, _f2s, _w, label="F2 tactic",  color="#22c55e", alpha=0.85)
        _ax_b.set_xticks(_x)
        _ax_b.set_xticklabels([c[:10] for c in _cats], rotation=35, ha="right",
                               fontsize=8, color="#9ca3af")
        _ax_b.set_ylim(0, 1.05)
        _ax_b.set_ylabel("Accuracy", color="#9ca3af", fontsize=9)
        _ax_b.tick_params(colors="#9ca3af")
        for spine in _ax_b.spines.values():
            spine.set_edgecolor("#21262d")
        _ax_b.legend(facecolor="#0d1117", edgecolor="#21262d", labelcolor="#c9d1d9", fontsize=8)
        _ax_b.axhline(0.5, color="#374151", lw=0.8, linestyle="--", alpha=0.6)
        _fig_b.tight_layout()
        st.pyplot(_fig_b, width="stretch")
        plt.close(_fig_b)
