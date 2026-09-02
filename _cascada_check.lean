import Mathlib.Algebra.Homology.ShortComplex.LeftHomology
import Mathlib.CategoryTheory.Limits.Shapes.Opposites.Kernels

open Category Limits
variable {C : Type*} [Category* C] [HasZeroMorphisms C]
variable {S}
variable (h : S.RightHomologyData) {A : C}
variable (S)
variable {S} in
variable {S}
section
variable (φ : S₁ ⟶ S₂) (h₁ : S₁.RightHomologyData) (h₂ : S₂.RightHomologyData)
variable {φ h₁ h₂}

theorem _probe_ {γ₁ γ₂ : RightHomologyMapData φ h₁ h₂} (eq : γ₁ = γ₂) : γ₁.φH = γ₂.φH := by
  sorry
