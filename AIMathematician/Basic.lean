-- Basic.lean
-- Demonstrating that Abelian Groups are Commutative in Lean 4

def hello := "world"

theorem one_eq_one : 1 = 1 := rfl

/-!
# Abelian Groups and Commutativity

An **abelian group** (also called a commutative group) is a group where the
binary operation is commutative. This file demonstrates how to formalize
abelian groups in Lean 4 and proves that commutativity holds.

## Mathematical Background

A group (G, *) is **abelian** if for all a, b in G: a * b = b * a

This is actually the *definition* of an abelian group, so our "proof" is
really about showing how this property is encoded in Lean's type system
and can be extracted when needed.
-/

-- ============================================================================
-- Part 1: Defining Group Structure (Without Mathlib)
-- ============================================================================

/-- A `Group` type class capturing the essential group axioms. -/
class Group (G : Type) extends Mul G, One G, Inv G where
  /-- Associativity: (a * b) * c = a * (b * c) -/
  mul_assoc : forall (a b c : G), (a * b) * c = a * (b * c)
  /-- Left identity: 1 * a = a -/
  one_mul : forall (a : G), 1 * a = a
  /-- Right identity: a * 1 = a -/
  mul_one : forall (a : G), a * 1 = a
  /-- Left inverse: a^{-1} * a = 1 -/
  inv_mul_cancel : forall (a : G), a⁻¹ * a = 1

/-- An `AbelianGroup` extends `Group` with the commutativity axiom. -/
class AbelianGroup (G : Type) extends Group G where
  /-- Commutativity: a * b = b * a -/
  mul_comm : forall (a b : G), a * b = b * a

-- ============================================================================
-- Part 2: The Main Theorem - Abelian Groups are Commutative
-- ============================================================================

/--
**Theorem**: In an abelian group, multiplication is commutative.

This theorem extracts the commutativity property from the `AbelianGroup`
type class. The proof is `AbelianGroup.mul_comm` itself, demonstrating
the Curry-Howard correspondence: the proof *is* the evidence that the
type (proposition) is inhabited.

**Statement**: forall G : Type, forall [AbelianGroup G], forall (a b : G), a * b = b * a
-/
theorem abelian_group_is_commutative
    (G : Type) [AbelianGroup G] (a b : G) : a * b = b * a :=
  AbelianGroup.mul_comm a b

-- Alternative formulation using `variable`
section AbelianCommutativity

variable {G : Type} [AbelianGroup G]

/-- Commutativity holds for any elements in an abelian group. -/
theorem mul_comm_of_abelian (a b : G) : a * b = b * a :=
  AbelianGroup.mul_comm a b

/-- We can also prove this using tactic mode for clarity. -/
theorem mul_comm_of_abelian' (a b : G) : a * b = b * a := by
  -- Strategy: Apply the commutativity axiom directly from AbelianGroup
  exact AbelianGroup.mul_comm a b

end AbelianCommutativity

-- ============================================================================
-- Part 3: Concrete Example - Integers under Addition
-- ============================================================================

/-- Integers form an abelian group under addition.

We define this using additive notation (Add, Zero, Neg) rather than
multiplicative notation (Mul, One, Inv) as is conventional for integers.
-/

-- First, we need an additive version of our group structure
class AddGroup (G : Type) extends Add G, Zero G, Neg G where
  add_assoc : forall (a b c : G), (a + b) + c = a + (b + c)
  zero_add : forall (a : G), 0 + a = a
  add_zero : forall (a : G), a + 0 = a
  neg_add_cancel : forall (a : G), -a + a = 0

class AddAbelianGroup (G : Type) extends AddGroup G where
  add_comm : forall (a b : G), a + b = b + a

-- Integers form an additive abelian group
instance : AddAbelianGroup Int where
  add_assoc := Int.add_assoc
  zero_add := Int.zero_add
  add_zero := Int.add_zero
  neg_add_cancel := Int.add_left_neg
  add_comm := Int.add_comm

/-- Demonstration: commutativity of integer addition. -/
theorem int_add_commutative (x y : Int) : x + y = y + x :=
  AddAbelianGroup.add_comm x y

/-- Concrete example: 3 + 5 = 5 + 3 -/
example : (3 : Int) + 5 = 5 + 3 := by
  -- This can be proved by reflexivity since both sides compute to 8
  rfl

/-- Another concrete example using the general theorem -/
example : (3 : Int) + 5 = 5 + 3 :=
  int_add_commutative 3 5

-- ============================================================================
-- Part 4: Additional Properties of Abelian Groups
-- ============================================================================

section AbelianProperties

variable {G : Type} [AbelianGroup G]

/-- In an abelian group, we can rearrange products freely.
    Specifically: a * b * c = c * b * a -/
theorem abelian_rearrange (a b c : G) : a * b * c = c * b * a := by
  -- Step 1: Use associativity to regroup
  rw [Group.mul_assoc]
  -- Step 2: Commute b * c to c * b
  rw [AbelianGroup.mul_comm b c]
  -- Step 3: Commute a * (c * b) to (c * b) * a
  rw [AbelianGroup.mul_comm a (c * b)]
  -- Proof complete after the above rewrites

/-- The square of a product: (a * b)^2 = a^2 * b^2 in an abelian group.
    Note: We define squaring inline since we haven't defined a power function. -/
theorem abelian_square_product (a b : G) :
    (a * b) * (a * b) = (a * a) * (b * b) := by
  -- (a * b) * (a * b)
  -- = a * (b * (a * b))      by associativity
  -- = a * (b * a * b)        by associativity
  -- = a * (a * b * b)        by commutativity (b * a = a * b)
  -- = a * a * b * b          by associativity
  rw [Group.mul_assoc a b (a * b)]
  rw [← Group.mul_assoc b a b]
  rw [AbelianGroup.mul_comm b a]
  rw [Group.mul_assoc a b b]
  rw [← Group.mul_assoc]

end AbelianProperties

-- ============================================================================
-- Part 5: Summary
-- ============================================================================

/-!
## Summary

We have demonstrated that abelian groups are commutative in Lean 4:

1. **Definition**: An abelian group is defined as a group with an additional
   commutativity axiom `mul_comm : forall a b, a * b = b * a`.

2. **Extraction**: The theorem `abelian_group_is_commutative` shows how to
   extract this property for use in proofs.

3. **Concrete Example**: Integers under addition form an abelian group,
   and we showed `Int.add_comm` holds.

4. **Derived Properties**: We proved additional properties like
   `abelian_square_product` that rely on commutativity.

The key insight is that in dependent type theory (Lean's foundation),
propositions are types and proofs are terms. The commutativity "proof"
is simply the term `AbelianGroup.mul_comm` which has type
`forall (a b : G), a * b = b * a` - the proposition we wanted to prove.
-/
