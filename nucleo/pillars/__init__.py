"""
Los Cuatro Pilares Fundacionales
================================

F = {F_Set, F_Cat, F_Log, F_Type}

Los cuatro clusters fundacionales del Nucleo Logico Evolutivo:

1. F_Set (Teoria de Conjuntos):
   - ZFC-axioms, ordinals, cardinals, forcing
   - Lenguaje estandar de la matematica clasica

2. F_Cat (Teoria de Categorias):
   - cat-basics, functors, nat-trans, topos
   - Estructura de transformaciones y relaciones

3. F_Log (Logica):
   - FOL=, SOL, HOL, IL
   - Lenguaje formal y mecanismo de inferencia
   - "Punto dulce" de FOL= (completo + compacto)

4. F_Type (Teoria de Tipos):
   - STLC, System F, CC, CIC, MLTT
   - Base de asistentes de pruebas (Lean, Coq)
   - Curry-Howard: pruebas = programas

Traducciones entre pilares (tau):
- tau_1: ETCS (F_Set <-> F_Cat)
- tau_2: Curry-Howard (F_Log <-> F_Type)
- tau_3: Modelos Tarski (F_Log <-> F_Set)
- tau_4: Topos (F_Cat <-> F_Log)
- tau_5: Universos (F_Cat <-> F_Type)
- tau_6: Set : Type (F_Set <-> F_Type)
"""

from nucleo.pillars.base import Pillar, PillarRegistry
from nucleo.pillars.type_theory import TypeTheoryPillar
from nucleo.pillars.logic import LogicPillar
from nucleo.pillars.category_theory import CategoryTheoryPillar
from nucleo.pillars.set_theory import SetTheoryPillar

__all__ = [
    # Base
    "Pillar",
    "PillarRegistry",
    # Pilares
    "TypeTheoryPillar",
    "LogicPillar",
    "CategoryTheoryPillar",
    "SetTheoryPillar",
]
