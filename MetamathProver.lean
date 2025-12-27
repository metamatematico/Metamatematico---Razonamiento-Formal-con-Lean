-- This module serves as the root of the `MetamathProver` library.
-- Import modules here that should be built as part of the library.
--
-- Note: MetamathProver.Basic defines custom Group/AbelianGroup classes for
-- educational purposes. The isomorphism theorem files use Mathlib's standard
-- algebra. These cannot be imported together due to name conflicts.
-- Import them separately as needed.

-- Educational group theory (custom definitions, no Mathlib)
-- import MetamathProver.Basic

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
