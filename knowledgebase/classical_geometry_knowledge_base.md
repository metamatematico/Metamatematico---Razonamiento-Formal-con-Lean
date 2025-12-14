# Classical Geometry Knowledge Base

**Domain**: Euclidean & Projective Geometry
**Lean 4 Coverage**: Partial (Euclidean good, projective limited)
**Source**: Mathlib4 `Geometry.Euclidean.*` modules and LeanGeo project
**Last Updated**: 2025-12-14

---

## Overview

This knowledge base covers classical geometry formalization in Lean 4/Mathlib, including Euclidean geometry (triangles, circles, angles), metric properties, and basic constructions. Built on inner product spaces and affine geometry foundations.

**Key Gap**: Ceva's theorem (#61), Pick's theorem (#92), Desargues's theorem (#87), and Morley's theorem (#84) not yet formalized. Projective geometry infrastructure limited.

---

## 1. EUCLIDEAN SPACE FOUNDATIONS

### 1.1 Inner Product Geometry

**Concept**: Euclidean geometry built on inner product spaces.

**NL Statement**: "Euclidean geometry in Mathlib is modeled using inner product spaces V with point spaces P as affine torsors over V."

**Lean 4 Setup**:
```lean
variable {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V]
variable {P : Type*} [MetricSpace P] [NormedAddTorsor V P]
```

**Key Components**:
- `V`: Vector space with inner product
- `P`: Point space (affine space over V)
- `NormedAddTorsor`: P is an affine space over V with metric structure

**Imports**: `Mathlib.Geometry.Euclidean.Basic`

**Difficulty**: medium

---

### 1.2 Distance

**Concept**: Distance between points in Euclidean space.

**NL Statement**: "The distance between two points is the norm of the vector from one to the other."

**Lean 4**:
```lean
-- dist : P → P → ℝ
-- For points p₁, p₂, dist p₁ p₂ = ‖p₂ -ᵥ p₁‖
```

**Imports**: `Mathlib.Analysis.Normed.Group.Basic`

**Difficulty**: easy

---

## 2. ANGLES

### 2.1 Angle Between Vectors

**Concept**: The angle between two nonzero vectors using arccos of normalized inner product.

**NL Statement**: "The angle between vectors x and y is arccos(⟨x, y⟩ / (‖x‖ · ‖y‖)), ranging from 0 to π."

**Lean 4 Definition**:
```lean
def InnerProductGeometry.angle (x y : V) : ℝ :=
  Real.arccos (⟪x, y⟫ / (‖x‖ * ‖y‖))
```

**Key Properties**:
```lean
-- Range: angle x y ∈ [0, π]
-- Symmetry: angle x y = angle y x
-- Perpendicular: angle x y = π/2 ↔ ⟪x, y⟫ = 0
```

**Imports**: `Mathlib.Geometry.Euclidean.Angle.Unoriented.Basic`

**Difficulty**: medium

---

### 2.2 Angle at a Point

**Concept**: Angle formed at vertex p₂ by rays to p₁ and p₃.

**NL Statement**: "The angle at point p₂ looking toward p₁ and p₃ is the angle between vectors (p₁ - p₂) and (p₃ - p₂)."

**Lean 4 Definition**:
```lean
def EuclideanGeometry.angle (p₁ p₂ p₃ : P) : ℝ :=
  InnerProductGeometry.angle (p₁ -ᵥ p₂) (p₃ -ᵥ p₂)
```

**Imports**: `Mathlib.Geometry.Euclidean.Angle.Unoriented.Affine`

**Difficulty**: medium

---

## 3. TRIANGLE THEOREMS

### 3.1 Pythagorean Theorem (#4)

**Concept**: In a right triangle, the square of the hypotenuse equals the sum of squares of the legs.

**NL Statement**: "If the angle at p₂ is π/2, then dist(p₁, p₃)² = dist(p₁, p₂)² + dist(p₃, p₂)²."

**Lean 4 Theorem**:
```lean
theorem EuclideanGeometry.dist_sq_eq_dist_sq_add_dist_sq_iff_angle_eq_pi_div_two :
  dist p₁ p₃ * dist p₁ p₃ = dist p₁ p₂ * dist p₁ p₂ + dist p₃ p₂ * dist p₃ p₂ ↔
  angle p₁ p₂ p₃ = Real.pi / 2
```

**Imports**: `Mathlib.Geometry.Euclidean.Triangle`

**Difficulty**: medium

---

### 3.2 Law of Cosines

**Concept**: Generalization of Pythagorean theorem to arbitrary triangles.

**NL Statement**: "For any triangle with vertices p₁, p₂, p₃: dist(p₁, p₃)² = dist(p₁, p₂)² + dist(p₃, p₂)² - 2·dist(p₁, p₂)·dist(p₃, p₂)·cos(angle at p₂)."

**Lean 4 Theorem**:
```lean
theorem EuclideanGeometry.dist_sq_eq_dist_sq_add_dist_sq_sub_two_mul_dist_mul_dist_mul_cos_angle :
  dist p₁ p₃ * dist p₁ p₃ = dist p₁ p₂ * dist p₁ p₂ + dist p₃ p₂ * dist p₃ p₂ -
  2 * dist p₁ p₂ * dist p₃ p₂ * Real.cos (angle p₁ p₂ p₃)
```

**Imports**: `Mathlib.Geometry.Euclidean.Triangle`

**Difficulty**: medium

---

### 3.3 Law of Sines

**Concept**: The ratio of side length to sine of opposite angle is constant.

**NL Statement**: "In any triangle, sin(A)/a = sin(B)/b = sin(C)/c where a, b, c are side lengths opposite angles A, B, C."

**Lean 4 Theorem**:
```lean
theorem EuclideanGeometry.sin_angle_mul_dist_eq_sin_angle_mul_dist :
  Real.sin (angle p₁ p₂ p₃) * dist p₂ p₃ = Real.sin (angle p₃ p₁ p₂) * dist p₃ p₁
```

**Imports**: `Mathlib.Geometry.Euclidean.Triangle`

**Difficulty**: medium

---

### 3.4 Triangle Angle Sum (#14)

**Concept**: The sum of interior angles of a triangle is π.

**NL Statement**: "For any non-degenerate triangle, the three interior angles sum to π (180 degrees)."

**Lean 4 Theorem**:
```lean
theorem EuclideanGeometry.angle_sum_eq_pi :
  angle p₁ p₂ p₃ + angle p₂ p₃ p₁ + angle p₃ p₁ p₂ = π
```

**Note**: Requires non-collinearity conditions.

**Imports**: `Mathlib.Geometry.Euclidean.Triangle`

**Difficulty**: medium

---

### 3.5 Heron's Formula

**Concept**: Area formula in terms of side lengths.

**NL Statement**: "The area of a triangle with sides a, b, c is √(s(s-a)(s-b)(s-c)) where s = (a+b+c)/2 is the semi-perimeter."

**Lean 4 Theorem**:
```lean
theorem Theorems100.heron :
  let a := dist p₁ p₂
  let b := dist p₃ p₂
  let c := dist p₁ p₃
  let s := (a + b + c) / 2
  1/2 * a * b * Real.sin (EuclideanGeometry.angle p₁ p₂ p₃) =
  √(s * (s - a) * (s - b) * (s - c))
```

**Imports**: `Mathlib.Geometry.Euclidean.Triangle`

**Difficulty**: hard

---

### 3.6 Isosceles Triangle (Pons Asinorum)

**Concept**: Equal sides imply equal base angles.

**NL Statement**: "In an isosceles triangle, the base angles are equal."

**Lean 4 Theorem**:
```lean
theorem EuclideanGeometry.angle_eq_angle_of_dist_eq_dist :
  dist p₁ p₂ = dist p₁ p₃ → angle p₂ p₁ p₃ = angle p₃ p₁ p₂
```

**Imports**: `Mathlib.Geometry.Euclidean.Triangle`

**Difficulty**: easy

---

## 4. CIRCLES

### 4.1 Circle Definition

**Concept**: Set of points at fixed distance from center.

**NL Statement**: "A circle with center c and radius r is the set of points at distance exactly r from c."

**Lean 4 Definition**:
```lean
def Metric.sphere (c : P) (r : ℝ) : Set P := {p | dist p c = r}
def Metric.ball (c : P) (r : ℝ) : Set P := {p | dist p c < r}
def Metric.closedBall (c : P) (r : ℝ) : Set P := {p | dist p c ≤ r}
```

**Imports**: `Mathlib.Topology.MetricSpace.Basic`

**Difficulty**: easy

---

### 4.2 Area of Circle (#9)

**Concept**: The area enclosed by a circle of radius r is πr².

**NL Statement**: "The area of a circle with radius r is πr²."

**Lean 4 Theorem**:
```lean
-- Via n-dimensional ball volume with n=2
theorem InnerProductSpace.volume_ball :
  MeasureTheory.volume (Metric.ball x r) =
  ENNReal.ofReal r ^ Module.finrank ℝ E *
  ENNReal.ofReal (√Real.pi ^ Module.finrank ℝ E / Real.Gamma (↑(Module.finrank ℝ E) / 2 + 1))
```

**Note**: For dimension 2, this simplifies to πr².

**Imports**: `Mathlib.MeasureTheory.Measure.Lebesgue.VolumeOfBalls`

**Difficulty**: hard

---

### 4.3 Circle Intersection (2D)

**Concept**: Two distinct circles in the plane intersect in at most two points.

**NL Statement**: "In 2-dimensional Euclidean space, two circles can intersect in at most two points."

**Lean 4 Theorem**:
```lean
theorem EuclideanGeometry.eq_of_dist_eq_of_dist_eq_of_finrank_eq_two
  [FiniteDimensional ℝ V] (hd : finrank ℝ V = 2) :
  -- Two points equidistant from same pair of centers must be equal or swapped
```

**Imports**: `Mathlib.Geometry.Euclidean.Basic`

**Difficulty**: hard

---

## 5. AFFINE GEOMETRY

### 5.1 Midpoint

**Concept**: The point equidistant from two given points.

**NL Statement**: "The midpoint of p₁ and p₂ is the unique point m such that m - p₁ = p₂ - m."

**Lean 4 Definition**:
```lean
def AffineMap.midpoint (p₁ p₂ : P) : P :=
  AffineMap.lineMap p₁ p₂ (1/2 : ℝ)
```

**Imports**: `Mathlib.LinearAlgebra.AffineSpace.Midpoint`

**Difficulty**: easy

---

### 5.2 Collinearity

**Concept**: Three or more points lying on a single line.

**NL Statement**: "Points p₁, p₂, p₃ are collinear if they lie on a single affine line."

**Lean 4**:
```lean
def Collinear (s : Set P) : Prop :=
  ∃ (L : AffineSubspace ℝ P), L.direction.finrank ≤ 1 ∧ s ⊆ L
```

**Imports**: `Mathlib.LinearAlgebra.AffineSpace.AffineSubspace`

**Difficulty**: medium

---

### 5.3 Apollonius's Theorem

**Concept**: Relates sides and median of a triangle.

**NL Statement**: "In any triangle, the sum of squares of two sides equals twice the square of the median to the third side plus half the square of that side."

**Lean 4 Theorem**:
```lean
theorem EuclideanGeometry.dist_sq_add_dist_sq_eq_two_mul_dist_sq_add_half_dist_sq :
  dist a b ^ 2 + dist a c ^ 2 = 2 * (dist a (midpoint ℝ b c) ^ 2 + (dist b c / 2) ^ 2)
```

**Imports**: `Mathlib.Geometry.Euclidean.Triangle`

**Difficulty**: medium

---

### 5.4 Stewart's Theorem

**Concept**: Relates cevian length to side lengths.

**NL Statement**: "If a cevian of length d is drawn to a side of length a, dividing it into segments m and n, then b²m + c²n = a(d² + mn)."

**Lean 4**: Formalized via angle conditions and law of cosines applications.

**Imports**: `Mathlib.Geometry.Euclidean.Triangle`

**Difficulty**: hard

---

## 6. MISSING FREEK 100 THEOREMS (Geometry)

**Note**: 10 of the 18 missing Freek 100 theorems are from geometry. This section documents them with expected Lean templates for future formalization.

### 6.1 Ceva's Theorem (#61) - NOT FORMALIZED

**100 Theorems**: #61

**NL Statement**: "In a triangle ABC, cevians AD, BE, CF (lines from each vertex to the opposite side) are concurrent if and only if (AF/FB)·(BD/DC)·(CE/EA) = 1."

**Expected Lean 4 Template**:
```lean
theorem ceva {P : Type*} [MetricSpace P] [NormedAddTorsor V P]
  {A B C D E F : P}
  (hD : D ∈ segment ℝ B C) (hE : E ∈ segment ℝ C A) (hF : F ∈ segment ℝ A B) :
  Concurrent (Line A D) (Line B E) (Line C F) ↔
    (dist A F / dist F B) * (dist B D / dist D C) * (dist C E / dist E A) = 1 := sorry
```

**Proof Approach**: Area ratios telescope using signed areas.

**Imports**: `Mathlib.Geometry.Euclidean.Basic`, `Mathlib.LinearAlgebra.AffineSpace.Combination`

**Difficulty**: hard

---

### 6.2 Pick's Theorem (#92) - NOT FORMALIZED

**100 Theorems**: #92

**NL Statement**: "For a simple polygon P with vertices at integer lattice points, the area equals I + B/2 - 1, where I is the number of interior lattice points and B is the number of boundary lattice points."

**Expected Lean 4 Template**:
```lean
def LatticePolygon (P : Set (ℤ × ℤ)) : Prop :=
  IsSimplePolygon P ∧ P.vertices ⊆ (ℤ × ℤ)

def interiorLatticePoints (P : LatticePolygon) : ℕ := sorry
def boundaryLatticePoints (P : LatticePolygon) : ℕ := sorry

theorem pick_theorem (P : LatticePolygon) :
  area P = interiorLatticePoints P + boundaryLatticePoints P / 2 - 1 := sorry
```

**Proof Approach**: Induction on triangulations, base case for triangles.

**Requires**: Lattice geometry infrastructure, polygon triangulation

**Difficulty**: hard

---

### 6.3 Desargues's Theorem (#87) - NOT FORMALIZED

**100 Theorems**: #87

**NL Statement**: "Two triangles ABC and A'B'C' are perspective from a point O (meaning lines AA', BB', CC' are concurrent) if and only if they are perspective from a line (meaning the intersections AB∩A'B', BC∩B'C', CA∩C'A' are collinear)."

**Expected Lean 4 Template**:
```lean
-- Requires projective geometry framework
theorem desargues
  {P : Type*} [ProjectivePlane P]
  {A B C A' B' C' : P} :
  PerspectiveFromPoint A B C A' B' C' ↔ PerspectiveFromLine A B C A' B' C' := sorry
```

**Mathematical Significance**:
- Fundamental theorem of projective geometry
- Equivalent to commutativity of underlying field
- Self-dual theorem

**Requires**: Projective plane infrastructure (not in Mathlib)

**Difficulty**: very hard

---

### 6.4 Morley's Theorem (#84) - NOT FORMALIZED

**100 Theorems**: #84

**NL Statement**: "In any triangle, the three points of intersection of the adjacent angle trisectors form an equilateral triangle (the Morley triangle)."

**Expected Lean 4 Template**:
```lean
def angleTrisector (A B C : P) (k : Fin 3) : Line P := sorry

theorem morley {P : Type*} [EuclideanSpace ℝ P]
  {A B C : P} (h_noncol : ¬Collinear ℝ ({A, B, C} : Set P)) :
  let P₁ := intersect (angleTrisector A B C 1) (angleTrisector A C B 1)
  let P₂ := intersect (angleTrisector B C A 1) (angleTrisector B A C 1)
  let P₃ := intersect (angleTrisector C A B 1) (angleTrisector C B A 1)
  IsEquilateral P₁ P₂ P₃ := sorry
```

**Proof Approach**: Reverse-engineer using known equilateral and show it matches trisectors.

**Difficulty**: very hard (intricate angle calculations)

---

### 6.5 Pascal's Hexagon Theorem (#28) - NOT FORMALIZED

**100 Theorems**: #28

**NL Statement**: "If a hexagon is inscribed in a conic section (ellipse, parabola, or hyperbola), then the three pairs of opposite sides meet in collinear points."

**Expected Lean 4 Template**:
```lean
theorem pascal_hexagon
  {K : ConicSection ℝ} {A B C D E F : Point ℝ}
  (h_inscribed : ∀ P ∈ [A, B, C, D, E, F], P ∈ K) :
  Collinear ℝ {
    intersect (Line A B) (Line D E),
    intersect (Line B C) (Line E F),
    intersect (Line C D) (Line F A)
  } := sorry
```

**Special Case**: Circle version (most commonly stated)

**Difficulty**: hard

---

### 6.6 Feuerbach's Theorem (#29) - NOT FORMALIZED

**100 Theorems**: #29

**NL Statement**: "The nine-point circle of any triangle is tangent to the incircle and to each of the three excircles."

**Expected Lean 4 Template**:
```lean
theorem feuerbach {P : Type*} [EuclideanSpace ℝ P]
  {A B C : P} (h : ¬Collinear ℝ ({A, B, C} : Set P)) :
  IsTangent (ninePointCircle A B C) (incircle A B C) ∧
  IsTangent (ninePointCircle A B C) (excircle A B C) ∧
  IsTangent (ninePointCircle A B C) (excircle B C A) ∧
  IsTangent (ninePointCircle A B C) (excircle C A B) := sorry
```

**Difficulty**: very hard

---

### 6.7 Isoperimetric Inequality (#43) - NOT FORMALIZED

**100 Theorems**: #43

**NL Statement**: "Among all simple closed curves of fixed perimeter, the circle encloses the maximum area. Equivalently, 4πA ≤ L² where A is area and L is perimeter."

**Expected Lean 4 Template**:
```lean
theorem isoperimetric_inequality
  {C : SimpleClosedCurve ℝ²}
  (hA : area (interior C) = A)
  (hL : perimeter C = L) :
  4 * π * A ≤ L ^ 2 := sorry

-- Equality case
theorem isoperimetric_equality
  {C : SimpleClosedCurve ℝ²} :
  4 * π * (area (interior C)) = (perimeter C) ^ 2 ↔ IsCircle C := sorry
```

**Difficulty**: very hard

---

### 6.8 Number of Platonic Solids (#50) - NOT FORMALIZED

**100 Theorems**: #50

**NL Statement**: "There are exactly five Platonic solids: tetrahedron, cube, octahedron, dodecahedron, and icosahedron."

**Expected Lean 4 Template**:
```lean
def IsPlatonicSolid (P : Polyhedron) : Prop :=
  P.IsConvex ∧ P.AllFacesCongruent ∧ P.AllVertexFiguresCongruent

theorem platonic_solids_count :
  {P : Polyhedron // IsPlatonicSolid P}.Finite ∧
  Fintype.card {P : Polyhedron // IsPlatonicSolid P} = 5 := sorry
```

**Proof Approach**: Euler's formula V - E + F = 2 combined with regularity constraints.

**Difficulty**: medium

---

### 6.9 Trisection Impossibility (#8) - NOT FORMALIZED

**100 Theorems**: #8

**NL Statement**: "It is impossible to trisect an arbitrary angle using only a compass and straightedge."

**Expected Lean 4 Template**:
```lean
-- Requires constructible numbers theory
def IsConstructible (x : ℝ) : Prop := sorry

theorem angle_trisection_impossible :
  ∃ θ : ℝ, ¬IsConstructible (Real.cos (θ / 3)) := sorry

-- Specific counterexample: 60° angle
theorem cannot_trisect_60_degrees :
  ¬IsConstructible (Real.cos (20 * π / 180)) := sorry
```

**Proof Approach**:
- Show cos(20°) satisfies irreducible cubic 8x³ - 6x - 1 = 0
- Constructible numbers have degree 2^n over ℚ
- Contradiction since 3 is not a power of 2

**Related**: Galois theory (field extensions)

**Difficulty**: hard

---

### 6.10 Independence of Parallel Postulate (#12) - NOT FORMALIZED

**100 Theorems**: #12

**NL Statement**: "Euclid's parallel postulate is independent of the other axioms of Euclidean geometry, meaning both Euclidean and non-Euclidean geometries are consistent."

**Expected Lean 4 Template**:
```lean
-- This is a meta-theorem about consistency
theorem parallel_postulate_independent :
  Consistent (EuclideanAxioms ∪ {ParallelPostulate}) ∧
  Consistent (EuclideanAxioms ∪ {¬ParallelPostulate}) := sorry
```

**Proof Approach**: Construct models (Poincaré disk, Klein model for hyperbolic)

**Mathematical Significance**:
- Foundational result in geometry
- Led to discovery of non-Euclidean geometries
- Required for general relativity

**Difficulty**: very hard (requires formal model construction)

---

## 7. STANDARD SETUP

**NL Statement**: "Standard imports and variable declarations for Euclidean geometry work."

**Lean 4**:
```lean
import Mathlib.Geometry.Euclidean.Basic
import Mathlib.Geometry.Euclidean.Triangle
import Mathlib.Geometry.Euclidean.Angle.Unoriented.Affine
import Mathlib.LinearAlgebra.AffineSpace.AffineSubspace

open EuclideanGeometry InnerProductGeometry

variable {V : Type*} [NormedAddCommGroup V] [InnerProductSpace ℝ V]
variable {P : Type*} [MetricSpace P] [NormedAddTorsor V P]
variable (p₁ p₂ p₃ : P)
```

**Difficulty**: easy

---

## 8. NOTATION REFERENCE

| Math Notation | Lean 4 Notation | Description |
|---------------|-----------------|-------------|
| d(p, q) | `dist p q` | Distance between points |
| ∠ABC | `angle A B C` | Angle at vertex B |
| ⟨v, w⟩ | `⟪v, w⟫` | Inner product |
| ‖v‖ | `‖v‖` | Norm of vector |
| midpoint | `midpoint ℝ p q` | Midpoint of segment |
| π | `Real.pi` | Pi constant |

---

## 9. LEANGEO PROJECT

### External Library

**Project**: LeanGeo (August 2025)
**Scope**: ~260 competition geometry theorems
**Key Contributions**:
- Menelaus's theorem
- Inscribed angle theorem
- Power of a point
- Cyclic quadrilateral properties
- Triangle center definitions

**Note**: Not in Mathlib core but provides extensive synthetic geometry coverage.

---

## Sources

- [Mathlib.Geometry.Euclidean.Basic](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Geometry/Euclidean/Basic.html)
- [Mathlib.Geometry.Euclidean.Triangle](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Geometry/Euclidean/Triangle.html)
- [100 theorems in Lean](https://leanprover-community.github.io/100.html)
- [LeanGeo arXiv paper](https://arxiv.org/html/2508.14644v1)
- [Mathematics in mathlib](https://leanprover-community.github.io/mathlib-overview.html)
