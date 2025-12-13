-- This module serves as the root of the `AIMathematician` library.
-- Import modules here that should be built as part of the library.
--
-- Note: AIMathematician.Basic defines custom Group/AbelianGroup classes for
-- educational purposes. The isomorphism theorem files use Mathlib's standard
-- algebra. These cannot be imported together due to name conflicts.
-- Import them separately as needed.

-- Educational group theory (custom definitions, no Mathlib)
-- import AIMathematician.Basic

-- Ring isomorphism theorems (uses Mathlib)
import AIMathematician.Ring.FirstIsomorphism
import AIMathematician.Ring.SecondIsomorphism
import AIMathematician.Ring.ThirdIsomorphism
import AIMathematician.Ring.LatticeTheorem

-- Group isomorphism theorems (uses Mathlib)
import AIMathematician.Group.FirstIsomorphism
import AIMathematician.Group.SecondIsomorphism
import AIMathematician.Group.ThirdIsomorphism
import AIMathematician.Group.LatticeTheorem
