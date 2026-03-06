"""
Genera PDF con las mejoras e implementaciones recientes del NLE v7.0.
Usa matplotlib para renderizar texto en formato de documento.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
import textwrap


def add_page(pdf, title, sections, page_num=1):
    """Add a page to the PDF."""
    fig, ax = plt.subplots(1, 1, figsize=(8.5, 11))
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')

    y = 0.95

    # Title
    ax.text(0.5, y, title, ha='center', va='top',
            fontsize=16, fontweight='bold', family='serif')
    y -= 0.04

    for section_title, content in sections:
        if y < 0.08:
            break

        # Section title
        y -= 0.02
        if section_title:
            ax.text(0.05, y, section_title, ha='left', va='top',
                    fontsize=12, fontweight='bold', family='serif',
                    color='#1a5276')
            y -= 0.025

        # Content
        for line in content:
            if y < 0.05:
                break
            wrapped = textwrap.wrap(line, width=90)
            for wline in wrapped:
                if y < 0.05:
                    break
                ax.text(0.07, y, wline, ha='left', va='top',
                        fontsize=8.5, family='serif')
                y -= 0.017

    # Footer
    ax.text(0.5, 0.02, f'NLE v7.0 - Mejoras Recientes  |  Pagina {page_num}',
            ha='center', va='bottom', fontsize=7, color='gray', family='serif')

    # Border
    ax.plot([0.03, 0.97, 0.97, 0.03, 0.03],
            [0.04, 0.04, 0.98, 0.98, 0.04],
            color='#cccccc', linewidth=0.5)

    pdf.savefig(fig, bbox_inches='tight')
    plt.close(fig)


def main():
    out_path = "docs/MEJORAS_RECIENTES.pdf"

    with PdfPages(out_path) as pdf:
        # Page 1: Cover + Overview
        add_page(pdf,
            "NLE v7.0 - Mejoras e Implementaciones Recientes",
            [
                ("", [
                    "Demostrador de Enunciados Matematicos",
                    "BIOMAT · Centro de Biomatemáticas",
                    "Autor: Leonardo Jiménez Martínez",
                    "Fecha: Febrero 2026",
                    "",
                    "Este documento resume las mejoras e implementaciones recientes",
                    "del Nucleo Logico Evolutivo (NLE) v7.0.",
                ]),
                ("1. Resumen de Cambios", [
                    "- Red neuronal GNN+PPO (124,420 parametros)",
                    "- 15 nuevos skills: 9 tacticas Lean + 6 estrategias de prueba",
                    "- Aprendizaje en vivo desde interacciones reales del chat",
                    "- Memoria de patrones exitosos con busqueda por similitud",
                    "- Visualizacion del grafo de skills con embeddings GNN",
                    "- 352 tests pasando (68 nuevos tests)",
                    "- Progreso global: ~95% completado",
                ]),
                ("2. GNN Encoder (Graph Neural Network)", [
                    "Archivo: nucleo/rl/gnn.py",
                    "",
                    "Se implemento un encoder de grafo basado en Graph Attention Networks",
                    "(GATConv) de PyTorch Geometric. Convierte el grafo categorico de",
                    "skills en vectores de embedding de 64 dimensiones.",
                    "",
                    "Arquitectura:",
                    "  - Input: Node features (dim=9): pillar one-hot(4) + level + in/out degree",
                    "    + is_colimit + is_active",
                    "  - Edge features (dim=6): morphism_type one-hot(5) + weight",
                    "  - 3 capas GATConv con 4 heads de atencion",
                    "  - Residual connections + LayerNorm en cada capa",
                    "  - Global mean pooling para embedding del grafo completo",
                    "",
                    "La funcion graph_to_pyg() convierte un SkillCategory a formato",
                    "PyG Data, excluyendo morfismos identidad.",
                ]),
                ("3. Actor-Critic Network (PPO)", [
                    "Archivo: nucleo/rl/networks.py",
                    "",
                    "Red Actor-Critic que combina tres encoders:",
                    "  1. GNN Encoder: embedding del grafo de skills",
                    "  2. Query Encoder: bag-of-keywords (33 terminos matematicos)",
                    "  3. Goal Encoder: hash determinista de goals Lean",
                    "",
                    "Fusion: concat(graph_emb, query_emb, goal_emb) -> Linear -> hidden_dim",
                    "Actor: MLP -> 3 logits (RESPONSE, REORGANIZE, ASSIST)",
                    "Critic: MLP -> 1 valor escalar",
                    "",
                    "Total: 124,420 parametros entrenables",
                ]),
            ],
            page_num=1,
        )

        # Page 2: PPO + Skills
        add_page(pdf,
            "NLE v7.0 - Mejoras (continuacion)",
            [
                ("4. PPO (Proximal Policy Optimization)", [
                    "Archivo: nucleo/rl/agent.py",
                    "",
                    "Implementacion completa de PPO con GAE (Generalized Advantage",
                    "Estimation) en NucleoAgent:",
                    "",
                    "  - Parametro use_neural=True activa la red (backward compatible)",
                    "  - Epsilon-greedy durante entrenamiento",
                    "  - GAE con gamma=0.99, lambda=0.95",
                    "  - Clipped surrogate objective (epsilon=0.2)",
                    "  - Value loss + entropy bonus (0.01)",
                    "  - Gradient clipping a 0.5",
                    "  - Save/load de pesos (.json config + .pt weights)",
                    "",
                    "El agente primero consulta la memoria procedural; si hay un patron",
                    "exitoso (success_rate >= 0.8), lo usa directamente. Sino, usa la red.",
                ]),
                ("5. Skills de Tacticas Lean (9 skills, nivel 1)", [
                    "Archivo: nucleo/pillars/math_domains.py",
                    "",
                    "  tactic-simp:      simp, simp_all, norm_num",
                    "  tactic-rewrite:   rw, conv, simp with lemmas",
                    "  tactic-exact:     exact, refine, use",
                    "  tactic-apply:     apply, have, suffices",
                    "  tactic-induction: induction, cases, rcases",
                    "  tactic-omega:     omega, linarith, norm_num",
                    "  tactic-ring:      ring, ring_nf, field_simp",
                    "  tactic-aesop:     aesop, decide, tauto",
                    "  tactic-calc:      calc blocks, step-by-step",
                    "",
                    "Todos dependen de type-theory (L0). Pilar: TYPE.",
                ]),
                ("6. Skills de Estrategias de Prueba (6 skills, nivel 2)", [
                    "  strategy-backward:      Razonamiento hacia atras (goal-directed)",
                    "  strategy-forward:       Razonamiento hacia adelante",
                    "  strategy-contradiction: Prueba por contradiccion (by_contra)",
                    "  strategy-cases:         Analisis por casos exhaustivo",
                    "  strategy-inductive:     Patron inductivo: base + paso",
                    "  strategy-construction:  Construccion de testigos (use/exact)",
                    "",
                    "Dependen de los skills de tacticas Lean. Pilar: LOG.",
                    "",
                    "3 nuevas traducciones inter-pilar:",
                    "  tactic-apply <-> strategy-backward (DEPENDENCY)",
                    "  tactic-induction <-> strategy-inductive (DEPENDENCY)",
                    "  strategy-contradiction <-> proof-theory (ANALOGY)",
                ]),
            ],
            page_num=2,
        )

        # Page 3: Live Learning + Memory + Tests
        add_page(pdf,
            "NLE v7.0 - Mejoras (continuacion)",
            [
                ("7. Aprendizaje en Vivo", [
                    "Archivos: nucleo/core.py, nucleo/rl/agent.py",
                    "",
                    "El ciclo de aprendizaje en vivo conecta el chat real al PPO:",
                    "",
                    "  1. Usuario hace consulta en el chat",
                    "  2. Dinamica Global (CRs) decide accion",
                    "  3. Se ejecuta y se evalua el resultado (reward real: -1 a +1)",
                    "  4. Se crea un Transition(state, action, reward, next_state)",
                    "  5. Se llama agent.update([transition]) para PPO incremental",
                    "  6. Pesos se guardan automaticamente cada 10 interacciones",
                    "",
                    "Metodo: nucleo.set_neural_agent(agent)",
                    "Esto cierra el ciclo: chat -> decision -> reward -> PPO -> mejor decision",
                ]),
                ("8. Memoria de Patrones Exitosos", [
                    "Archivo: nucleo/mes/memory.py",
                    "",
                    "Se enriquecio la clase Procedure con campos adicionales:",
                    "  - query_text: texto original de la consulta",
                    "  - tactic_used: tactica Lean utilizada (si aplica)",
                    "  - lean_goal: goal de Lean (si aplica)",
                    "",
                    "Nuevo metodo ProceduralMemory.get_best_for_query(query):",
                    "  - Busca procedimientos por overlap de keywords con el query",
                    "  - Filtra por success_rate minimo (default: 0.8)",
                    "  - Score = overlap * success_rate * log(invocations)",
                    "  - Retorna el mejor procedimiento o None",
                    "",
                    "El agente consulta esta memoria ANTES de usar la red neuronal.",
                    "Si hay un patron probado, lo reutiliza directamente.",
                ]),
                ("9. Visualizacion de Embeddings", [
                    "Archivo: scripts/visualize_embeddings.py",
                    "",
                    "Script que genera 4 paneles de visualizacion:",
                    "  1. Grafo categorico de skills (networkx, coloreado por pilar)",
                    "  2. Embeddings GNN proyectados a 2D via t-SNE",
                    "  3. Clusters por categoria de dominio",
                    "  4. Heatmap de distancias entre pilares",
                    "",
                    "Uso: python -m scripts.visualize_embeddings",
                    "     python -m scripts.visualize_embeddings --show",
                ]),
                ("10. Tests Nuevos (68 tests)", [
                    "  test_gnn.py:           19 tests (GNN encoder, graph_to_pyg)",
                    "  test_ppo.py:           25 tests (Actor-Critic, PPO, save/load)",
                    "  test_live_learning.py: 24 tests (Lean skills, memoria, live PPO)",
                    "",
                    "Total: 352 tests pasando (284 existentes + 68 nuevos)",
                ]),
                ("11. Archivos Modificados", [
                    "  nucleo/rl/gnn.py          NUEVO  ~200 lineas",
                    "  nucleo/rl/networks.py      NUEVO  ~200 lineas",
                    "  nucleo/rl/agent.py         MOD    +170 lineas",
                    "  nucleo/rl/__init__.py       MOD    +4 lineas",
                    "  nucleo/core.py             MOD    +40 lineas",
                    "  nucleo/mes/memory.py       MOD    +50 lineas",
                    "  nucleo/mes/co_regulators.py MOD   +15 lineas",
                    "  nucleo/pillars/math_domains.py MOD +100 lineas",
                    "  scripts/visualize_embeddings.py NUEVO ~350 lineas",
                    "  tests/test_gnn.py          NUEVO  ~200 lineas",
                    "  tests/test_ppo.py          NUEVO  ~260 lineas",
                    "  tests/test_live_learning.py NUEVO ~210 lineas",
                ]),
            ],
            page_num=3,
        )

    print(f"PDF generado: {out_path}")


if __name__ == "__main__":
    main()
