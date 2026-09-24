# -*- coding: utf-8 -*-
"""El grafo curado a solas: los 10 fundacionales L0 y los dominios de `math_domains`.

NO es el grafo del sistema. `Nucleo.initialize()` monta además los 147 nodos
leídos de Mathlib (módulos y áreas); éste es sólo lo escrito a mano, y es el
objeto que miden los tests de aciclicidad, funtor, multiplicidad y taxonomía.

Vivía como `build_skill_graph()` en `scripts/train_gnn_ppo.py`, el script que
entrenaba la red GNN+PPO. La red se retiró —aprendió una constante— y el grafo
se queda aquí, idéntico, porque lo que se mide sobre él no tiene que ver con la
red.
"""


def build_skill_graph():
    """
    Construye el grafo de 76 skills del NLE.
    Replica exactamente la inicializacion de core.py:
      1. Agrega 10 skills fundacionales L0 (pilares ZFC/Cat/Log/Type)
      2. Llama a load_math_domains para agregar los 66 skills L1-L2
    """
    from nucleo.graph.category import SkillCategory
    from nucleo.pillars.math_domains import load_math_domains
    from nucleo.types import Skill, MorphismType, PillarType

    graph = SkillCategory(name="NucleoSkillGraph")

    # --- L0: skills fundacionales (10 skills) ---
    # F_Set
    graph.add_skill(Skill(id="zfc-axioms",    name="ZFC Axioms",             description="Axiomas de Zermelo-Fraenkel", pillar=PillarType.SET, level=0))
    graph.add_skill(Skill(id="ordinals",      name="Ordinals",               description="Ordinales y aritmetica ordinal", pillar=PillarType.SET, level=0))
    # F_Cat
    graph.add_skill(Skill(id="cat-basics",    name="Category Basics",        description="Objetos, morfismos, composicion", pillar=PillarType.CAT, level=0))
    graph.add_skill(Skill(id="functors",      name="Functors",               description="Funtores covariantes/contravariantes", pillar=PillarType.CAT, level=0))
    graph.add_skill(Skill(id="nat-trans",     name="Natural Transformations", description="Transformaciones naturales", pillar=PillarType.CAT, level=0))
    graph.add_skill(Skill(id="limits",        name="Limits & Colimits",      description="Limites y colimites", pillar=PillarType.CAT, level=0))
    # F_Log
    graph.add_skill(Skill(id="fol-deduction", name="FOL Deduction",          description="Deduccion natural FOL", pillar=PillarType.LOG, level=0))
    graph.add_skill(Skill(id="fol-metatheory",name="FOL Metatheory",         description="Completitud, compacidad", pillar=PillarType.LOG, level=0))
    # F_Type
    graph.add_skill(Skill(id="cic",           name="CIC",                    description="Calculo de Construcciones Inductivas", pillar=PillarType.TYPE, level=0))
    graph.add_skill(Skill(id="lean-kernel",   name="Lean 4 Kernel",          description="Kernel Lean 4", pillar=PillarType.TYPE, level=0))

    # Morfismos L0
    graph.add_morphism("zfc-axioms",    "ordinals",        MorphismType.DEPENDENCY)
    graph.add_morphism("cat-basics",    "functors",        MorphismType.DEPENDENCY)
    graph.add_morphism("functors",      "nat-trans",       MorphismType.DEPENDENCY)
    graph.add_morphism("functors",      "limits",          MorphismType.DEPENDENCY)
    graph.add_morphism("cic",           "lean-kernel",     MorphismType.DEPENDENCY)
    graph.add_morphism("fol-deduction", "fol-metatheory",  MorphismType.DEPENDENCY)
    graph.add_morphism("fol-deduction", "cic",             MorphismType.TRANSLATION)
    graph.add_morphism("zfc-axioms",    "cat-basics",      MorphismType.ANALOGY)

    # --- L1-L2: 66 skills de dominios matematicos ---
    load_math_domains(graph)
    return graph
