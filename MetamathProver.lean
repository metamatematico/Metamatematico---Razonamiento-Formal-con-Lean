-- This module serves as the root of the `MetamathProver` library.
--
-- MATHEMATICAL FOUNDATIONS
-- ========================
-- The CategoryFoundations modules establish the formal mathematical basis
-- for the claims made by the METAMATEMÁTICO system. They clarify:
--
-- 1. The skill graph is a QUIVER — a directed multigraph.
-- 2. The CATEGORY used is the FREE CATEGORY (path category) on that quiver.
-- 3. "Colimit" claims are formally correct only in the FINITE subcategory
--    of currently known skills (decidable, exhaustively checkable).
-- 4. MES terminology is used as analogy, not as formal MES (Ehresmann).
--
-- These files do NOT prove that the Python NetworkX graph IS the category —
-- the graph is a representation of the quiver; the category is constructed here.

-- Category theory foundations for the skill graph
import MetamathProver.CategoryFoundations.SkillCategory
import MetamathProver.CategoryFoundations.ColimitVerifier
-- Central theorem: join = colimit in the preorder (thin) interpretation
import MetamathProver.CategoryFoundations.JoinColimit
-- Emergent hierarchy: complexity order and its well-foundedness
import MetamathProver.CategoryFoundations.ComplexityOrder
-- Co-regulator network: priority order, global decision protocol, E-equivalence,
-- ASSIST/RESPOND routing, and tactic cascade specification
import MetamathProver.CategoryFoundations.CoRegulatorNetwork
-- Formal bridge closing the IsColimit gap:
--   IsJoin S j ↔ ∃ hub, Nonempty (CategoryTheory.Limits.IsColimit (joinCocone S j hub))
-- Proved in any preorder (thin category). 0 sorry.
import MetamathProver.CategoryFoundations.IsColimitBridge
-- Funtor cociente pi: Skills -> Agentes. Demuestra que pi es funtor, que
-- preserva co-conos (18/18 medido) y que NO preserva la minimalidad, con
-- contraejemplo finito (12/18 medido).
import MetamathProver.CategoryFoundations.QuotientFunctor
-- La fibracion: la condicion que hace utilizable la base de areas
import MetamathProver.CategoryFoundations.Fibracion
-- Enlaces simples/complejos y principio de multiplicidad. Resultado principal
-- NEGATIVO: en una categoria delgada los simples son cerrados por composicion,
-- de modo que la emergencia de Ehresmann no puede darse en este modelo.
import MetamathProver.CategoryFoundations.SimpleComplexLinks
-- Enlaces simples/complejos en el sentido REAL de Ehresmann: inducidos por un
-- cluster entre descomposiciones, no por factorizar via un objeto. Demuestra
-- que el Principio de Multiplicidad es condicion NECESARIA de la complejidad.
import MetamathProver.CategoryFoundations.EhresmannLinks
-- Funtores de transicion entre instantaneas: composicion parcial, asociatividad
-- y compatibilidad (Def 3.2) = ley de funtor sobre el orden del tiempo.
import MetamathProver.CategoryFoundations.Evolution
-- La complexificacion de Ehresmann en el caso delgado: todo patron adquiere
-- colimite, los que ya lo tenian lo conservan, y los homologos lo comparten.
import MetamathProver.CategoryFoundations.Complexificacion
-- Cuantos morfismos hay de group-theory a ring-theory: al menos tres, y dos de
-- ellos son los que nombraria cualquier algebrista. El dominio NO es delgado.
import MetamathProver.CategoryFoundations.MorfismosGrupoAnillo
-- Los demas pares del grafo donde la multiplicidad se puede certificar. El
-- separador no siempre es el cardinal: group-actions se separa por puntos fijos.
import MetamathProver.CategoryFoundations.MultiplicidadDelGrafo

-- Ring isomorphism theorems (uses Mathlib)
import MetamathProver.Ring.FirstIsomorphism
import MetamathProver.Ring.SecondIsomorphism
import MetamathProver.Ring.ThirdIsomorphism
import MetamathProver.Ring.LatticeTheorem

-- Group isomorphism theorems (uses Mathlib)
import MetamathProver.Group.FirstIsomorphism
import MetamathProver.Group.SecondIsomorphism
import MetamathProver.Group.ThirdIsomorphism
import MetamathProver.Group.LatticeTheorem
