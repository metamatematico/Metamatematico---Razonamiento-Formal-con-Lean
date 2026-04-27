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
