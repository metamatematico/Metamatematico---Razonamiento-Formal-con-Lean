# Logic and Model Theory Knowledge Base for Lean 4

**Generated:** 2025-12-14
**Purpose:** Research knowledge base for mathematical logic and model theory formalization in Lean 4. Covers first-order logic, completeness/incompleteness theorems, model theory, computability theory, Curry-Howard isomorphism, and proof theory.

**Measurability Score:** ~82/100
- Strong coverage: First-order model theory, computability, Löwenheim-Skolem
- Significant gaps: Gödel incompleteness theorems, proof theory (sequent calculus, cut elimination)
- Active development: Model theory library in Mathlib, external projects for incompleteness

---

## Related Knowledge Bases

### Prerequisites
- **Set Theory** (`set_theory_knowledge_base.md`): ZFC foundations, cardinality

### Builds Upon This KB
- **Computability Theory** (`computability_theory_knowledge_base.md`): Decidability, recursion
- **Category Theory** (`category_theory_knowledge_base.md`): Categorical logic

### Related Topics
- **Arithmetic** (`arithmetic_knowledge_base.md`): Models of arithmetic
- **Order Theory** (`order_theory_knowledge_base.md`): Boolean algebras, model-theoretic orders

### Scope Clarification
This KB focuses on **logic and model theory**:
- First-order syntax and semantics
- Satisfaction and models
- Completeness and compactness theorems
- Löwenheim-Skolem theorems
- Gödel incompleteness (via external projects)
- Curry-Howard correspondence

For **proof formalization**, this KB is foundational to all other KBs.
For **computability aspects**, see **Computability Theory KB**.

---

## 1. First-Order Logic Fundamentals

### Syntax and Semantics

**Natural Language Statement:**
First-order logic (FOL) consists of:
- **Terms:** Variables and function applications built from a signature
- **Formulas:** Atomic formulas (relations on terms), logical connectives (∧, ∨, ¬, →), and quantifiers (∀, ∃)
- **Sentences:** Formulas with no free variables

A structure M satisfies a sentence φ (written M ⊨ φ) when φ is true under the interpretation given by M. A theory T is a set of sentences, and a model of T is a structure satisfying all sentences in T.

**Mathematical Statement:**
For a first-order language L with signature (functions, relations):
```
Terms t ::= x | f(t₁,...,tₙ)
Formulas φ ::= R(t₁,...,tₙ) | φ₁ ∧ φ₂ | ¬φ | ∀x.φ
Satisfaction: M ⊨ φ iff φ is true in M under assignment
Theory: T = {φ | φ is a sentence}
Model: M is a model of T iff ∀φ ∈ T, M ⊨ φ
```

**Lean 4 Formalization:**
```lean
import Mathlib.ModelTheory.Basic
import Mathlib.ModelTheory.Syntax

-- Language definition with function and relation symbols
structure Language where
  Functions : ℕ → Type u
  Relations : ℕ → Type u

-- Terms in a language
inductive Language.Term (L : Language) (α : Type*) : Type*
  | var : α → L.Term α
  | func : ∀ {n}, L.Functions n → (Fin n → L.Term α) → L.Term α

-- Formulas with bounded quantifiers
inductive Language.BoundedFormula (L : Language) (α : Type*) : ℕ → Type*
  | falsum : L.BoundedFormula α n
  | equal : L.Term (α ⊕ Fin n) → L.Term (α ⊕ Fin n) → L.BoundedFormula α n
  | rel : ∀ {l}, L.Relations l → (Fin l → L.Term (α ⊕ Fin n)) → L.BoundedFormula α n
  | imp : L.BoundedFormula α n → L.BoundedFormula α n → L.BoundedFormula α n
  | all : L.BoundedFormula α (n + 1) → L.BoundedFormula α n

-- Structure interpreting a language
structure Language.Structure (L : Language) where
  carrier : Type w
  funMap : ∀ {n}, L.Functions n → (Fin n → carrier) → carrier
  RelMap : ∀ {n}, L.Relations n → (Fin n → carrier) → Prop

-- Satisfaction relation
def Language.Structure.Realize {L : Language} (M : L.Structure) :
    ∀ {n}, L.BoundedFormula Empty n → (Fin n → M) → Prop := sorry
```

**Mathlib Status:** FULL
- Core syntax: `Mathlib.ModelTheory.Syntax`
- Structures: `Mathlib.ModelTheory.Semantics`
- Satisfaction: `Language.Structure.Realize`

**Key Concepts:**
1. **Signature:** Specifies function and relation symbols with arities
2. **Structure:** Assigns interpretations to symbols (universe + functions + relations)
3. **Valuation/Assignment:** Maps variables to elements of the structure
4. **Satisfaction:** Recursive definition of when M ⊨ φ[v] (formula φ true under valuation v)

**Difficulty:** medium

---

## 2. Completeness Theorems

### Gödel's Completeness Theorem

**100 Theorems List:** #21
**Natural Language Statement:**
A first-order sentence is provable from a theory T if and only if it is true in all models of T. Equivalently, a theory has a model if and only if it is consistent (no contradiction can be derived).

This establishes the semantic-syntactic correspondence: semantic consequence (⊨) coincides with syntactic provability (⊢).

**Mathematical Statement:**
For any first-order theory T and sentence φ:
```
T ⊢ φ  ⟺  T ⊨ φ
(Provable from T) ⟺ (True in all models of T)

Equivalently (contrapositive):
T has a model  ⟺  T is consistent
```

**Proof Sketch:**
1. **Soundness (⊢ → ⊨):** Show each inference rule preserves truth in models
2. **Completeness (⊨ → ⊢):** Construct a model for consistent theories:
   - Extend T to a maximal consistent theory T*
   - Build Henkin structure: universe = equivalence classes of terms
   - Interpret functions/relations using T* provability
   - Prove Truth Lemma: M ⊨ φ ⟺ φ ∈ T*
3. Therefore, if T ⊨ φ, then T ∪ {¬φ} has no model, so T ∪ {¬φ} is inconsistent, thus T ⊢ φ

**Lean 4 Formalization:**
```lean
import Mathlib.ModelTheory.Satisfiability

-- Completeness: satisfiability implies consistency
theorem complete_of_satisfiable {L : Language} {T : L.Theory} :
    T.IsSatisfiable → T.IsConsistent := by
  sorry

-- The Completeness Theorem (semantic → syntactic)
-- NOTE: Requires proof calculus formalization
-- Currently available in flypitch project, being migrated to Mathlib
theorem completeness {L : Language} {T : L.Theory} {φ : L.Sentence} :
    T ⊨ φ → T ⊢ φ := by
  sorry
```

**Mathlib Status:** PARTIAL
- Satisfiability theory: `Mathlib.ModelTheory.Satisfiability` (FULL)
- Full completeness proof: Formalized in **flypitch project** by Jesse Michael Han and Floris van Doorn
- Migration status: Aaron Anderson working on integrating into Mathlib (as of 2025)
- Current Mathlib: Consequences of completeness (compactness, Löwenheim-Skolem) available

**Significance:**
- Establishes formal logic as complete: provability captures semantic truth
- Basis for compactness theorem (finite satisfiability → satisfiability)
- Equivalent to Boolean Prime Ideal Theorem (weak choice)

**Difficulty:** hard

---

### Compactness Theorem

**Natural Language Statement:**
A set of first-order sentences has a model if and only if every finite subset has a model. This allows constructing infinite models from finite consistency.

**Mathematical Statement:**
For any first-order theory T:
```
T has a model  ⟺  Every finite T₀ ⊆ T has a model
```

**Proof Sketch (via Completeness):**
1. (→) Trivial: if M ⊨ T, then M ⊨ T₀ for all finite T₀ ⊆ T
2. (←) Assume T has no model. By completeness, T is inconsistent.
3. Inconsistency means ⊢ ⊥ from T, which uses only finitely many sentences T₀ ⊆ T
4. Then T₀ is inconsistent, so T₀ has no model. Contradiction.

**Alternative Proof:** Directly via ultraproducts (model-theoretic construction)

**Lean 4 Formalization:**
```lean
import Mathlib.ModelTheory.Satisfiability

-- Compactness Theorem
theorem compactness {L : Language} {T : L.Theory} :
    T.IsSatisfiable ↔ ∀ T₀ : Finset T, (↑T₀ : L.Theory).IsSatisfiable := by
  sorry

-- Mathlib has related results:
-- If every finite subset is satisfiable, T is satisfiable
#check Theory.IsSatisfiable.realize_sentence_of_finite
```

**Mathlib Status:** PARTIAL
- Satisfiability notions: Available in `Mathlib.ModelTheory.Satisfiability`
- Full compactness: In flypitch, migration in progress
- Applications (e.g., existence of nonstandard models): Possible to express

**Applications:**
1. Existence of infinite models (e.g., add axioms "∃≥n elements" for each n)
2. Nonstandard analysis: Models of real analysis with infinitesimals
3. Graph coloring: Infinite graphs colorable if all finite subgraphs are
4. Algebraic closure existence (via model theory)

**Difficulty:** medium (proof via completeness), hard (ultraproduct proof)

---

## 3. Incompleteness Theorems

### Gödel's First Incompleteness Theorem

**100 Theorems List:** #55
**Natural Language Statement:**
Any consistent formal system F capable of expressing basic arithmetic (specifically, Peano Arithmetic) contains statements that are true but unprovable within F. Formally, there exists a sentence G such that:
- If F is consistent, then F ⊬ G and F ⊬ ¬G
- G is semantically true in the standard model of arithmetic

The sentence G is constructed to assert "G is not provable in F" (Gödel sentence via diagonal lemma).

**Mathematical Statement:**
For any consistent formal system F extending PA:
```
∃G : Sentence,
  (F is consistent → F ⊬ G ∧ F ⊬ ¬G) ∧
  (ℕ ⊨ G)
```

**Proof Sketch:**
1. **Arithmetization:** Encode formulas and proofs as natural numbers (Gödel numbering)
2. **Representability:** Basic syntactic operations (substitute, concatenate) are representable by arithmetic formulas
3. **Diagonal Lemma:** For any formula φ(x) with one free variable, there exists a sentence G such that:
   ```
   F ⊢ G ↔ φ(⌜G⌝)
   ```
   where ⌜G⌝ is the Gödel number of G
4. **Construction:** Let φ(x) = "x is not provable in F", construct G with F ⊢ G ↔ ¬Provable_F(⌜G⌝)
5. **Undecidability:**
   - If F ⊢ G, then Provable_F(⌜G⌝), so F ⊢ ¬G by equivalence. Contradiction if consistent.
   - If F ⊢ ¬G, then F ⊢ Provable_F(⌜G⌝), so F proves "F proves G", which should yield F ⊢ G if F is sound. Contradiction.
6. Therefore, if F is consistent, F ⊬ G and F ⊬ ¬G.

**Lean 4 Formalization:**
```lean
-- NOT IN MATHLIB - External project
-- Expected structure (based on similar formalizations)

import Mathlib.Computability.Primrec  -- For representability
import Mathlib.Logic.Encodable.Basic  -- For Gödel numbering

-- Gödel numbering of formulas
def godelNumber : Formula → ℕ := sorry

-- Representability of provability predicate
def provable (F : Theory) (n : ℕ) : Prop :=
  ∃ φ : Formula, godelNumber φ = n ∧ F ⊢ φ

-- Diagonal lemma
theorem diagonal_lemma (F : Theory) (φ : Formula) :
    ∃ G : Formula, F ⊢ (G ↔ φ.subst (godelNumber G)) := sorry

-- First Incompleteness Theorem
theorem first_incompleteness (F : Theory)
    (h_extends_PA : PA ⊆ F) (h_consistent : F.IsConsistent) :
    ∃ G : Sentence, F ⊬ G ∧ F ⊬ ¬G ∧ ℕ ⊨ G := sorry
```

**Mathlib Status:** NOT FORMALIZED
- **External Project:** "Formalizing Gödel's Incompleteness Theorems" exists but not in Mathlib
- Related Isabelle formalization by Larry Paulson exists
- Key dependencies available:
  - `Mathlib.Computability.Primrec` (primitive recursive functions)
  - Encoding/representability infrastructure partially available
- On Lean community's radar but not prioritized yet

**Historical Note:**
This theorem shattered Hilbert's program to formalize all of mathematics in a complete, consistent system. It shows fundamental limitations of formal systems.

**Difficulty:** hard

---

### Gödel's Second Incompleteness Theorem

**Natural Language Statement:**
No consistent formal system F that extends Peano Arithmetic can prove its own consistency. Specifically, if F is consistent, then F cannot prove "F is consistent."

**Mathematical Statement:**
For consistent formal system F extending PA:
```
F ⊬ Con(F)
```
where Con(F) is the arithmetic statement "F is consistent" (formalized as "no proof of ⊥ exists").

**Proof Sketch:**
1. Formalize consistency: Con(F) := ¬Provable_F(⌜⊥⌝)
2. From First Incompleteness, construct Gödel sentence G with F ⊢ G ↔ ¬Provable_F(⌜G⌝)
3. **Key Step:** Show F ⊢ Con(F) → G (provable within F using formalized provability logic)
   - Reasoning: If F is consistent, then F doesn't prove G (by First Incompleteness)
   - This reasoning can be formalized in arithmetic
4. If F ⊢ Con(F), then F ⊢ G
5. But F ⊬ G (by First Incompleteness), contradiction
6. Therefore F ⊬ Con(F)

**Lean 4 Formalization:**
```lean
-- NOT IN MATHLIB
-- Expected structure

-- Consistency predicate as arithmetic formula
def consistencyStatement (F : Theory) : Sentence :=
  ¬(provable F (godelNumber ⊥))

-- Second Incompleteness Theorem
theorem second_incompleteness (F : Theory)
    (h_extends_PA : PA ⊆ F) (h_consistent : F.IsConsistent) :
    F ⊬ consistencyStatement F := sorry
```

**Mathlib Status:** NOT FORMALIZED
- Not in Mathlib
- Would follow from First Incompleteness formalization
- Requires formalized provability logic (Löb's theorem, Hilbert-Bernays derivability conditions)

**Philosophical Significance:**
- Systems cannot "bootstrap" their own trustworthiness
- Consistency must be established from outside (e.g., PA's consistency proven in ZFC)
- Foundation for epistemic limits of formal verification

**Difficulty:** hard

---

### Rosser's Improvement

**Natural Language Statement:**
Rosser strengthened Gödel's First Incompleteness by removing the soundness assumption. Gödel required F to be ω-consistent (consistent + "if F proves ¬P(n) for each n, then F doesn't prove ∃x.P(x)"). Rosser only requires simple consistency.

**Mathematical Statement:**
For any consistent formal system F extending PA:
```
∃R : Sentence, F ⊬ R ∧ F ⊬ ¬R
```
(No ω-consistency needed)

**Proof Sketch:**
1. Modify Gödel's construction: Instead of "I am not provable," construct R saying:
   ```
   "For every proof of R, there exists a shorter proof of ¬R"
   ```
2. If F ⊢ R, then some proof exists, so by R's statement, a shorter proof of ¬R exists, so F ⊢ ¬R. Contradiction.
3. If F ⊢ ¬R, then some proof of ¬R exists. R claims a shorter proof of R should exist, which is false. This yields F ⊢ R by subtle argument, contradiction.
4. Therefore F ⊬ R and F ⊬ ¬R under simple consistency.

**Mathlib Status:** NOT FORMALIZED

**Difficulty:** hard

---

## 4. Model Theory Basics

### Löwenheim-Skolem Theorems

**Natural Language Statement:**
The Löwenheim-Skolem theorems constrain the possible cardinalities of models:

**Downward L-S:** If a countable first-order theory has an infinite model, it has a countable model. More generally, any model has an elementary substructure of any infinite cardinality ≥ max(|L|, |generators|).

**Upward L-S:** If a theory has an infinite model of cardinality κ, it has models of all infinite cardinalities ≥ κ.

**Mathematical Statement:**
Downward:
```
∀ infinite L-structure M, ∀ S ⊆ M, ∀ κ infinite cardinal,
  max(#S, #L) ≤ κ ≤ #M
  → ∃ N ≼ M, S ⊆ N ∧ #N = κ
```

Upward:
```
∀ infinite L-structure M, ∀ κ > max(#M, #L),
  ∃ N ≽ M, #N = κ
```

**Proof Sketch (Downward):**
1. Start with subset S ⊆ M
2. Recursively add Skolem witnesses: For each formula φ(x, ȳ) and parameters ā in current set, if M ⊨ ∃x.φ(x,ā), add witness b with M ⊨ φ(b,ā)
3. After ω steps, obtain elementary substructure (closed under Skolem functions)
4. Control cardinality by choosing witnesses systematically

**Lean 4 Formalization:**
```lean
import Mathlib.ModelTheory.Skolem
import Mathlib.SetTheory.Cardinal.Basic

-- Downward Löwenheim-Skolem
theorem exists_elementary_substructure_card_eq
    {L : Language} {M : L.Structure} {S : Set M}
    (κ : Cardinal.{w}) [Infinite M] [κ.Infinite]
    (h₁ : max (Cardinal.lift.{w} #S) L.card ≤ Cardinal.lift.{u} κ)
    (h₂ : Cardinal.lift.{u} κ ≤ Cardinal.lift.{w} #M) :
    ∃ N : L.ElementarySubstructure M, S ⊆ N ∧ Cardinal.lift.{u} #N = Cardinal.lift.{w} κ :=
  sorry

-- Upward Löwenheim-Skolem
theorem exists_elementary_embedding_card_eq
    {L : Language} {M : L.Structure} [Infinite M]
    (κ : Cardinal.{w}) [κ.Infinite]
    (h : max (Cardinal.lift.{w} #M) L.card < κ) :
    ∃ N : L.Structure, Nonempty (M ↪ₑ[L] N) ∧ Cardinal.lift.{u} #N = Cardinal.lift.{w} κ :=
  sorry
```

**Mathlib Status:** FULL
- Both directions formalized in `Mathlib.ModelTheory.Skolem`
- Elementary substructures: `Language.ElementarySubstructure`
- Elementary embeddings: `Language.ElementaryEmbedding` (notation `M ↪ₑ[L] N`)
- Skolem function construction: `skolem₁`, recursive Skolemization

**Significance:**
- First-order theories cannot pin down infinite cardinality (unlike second-order logic)
- **Skolem's Paradox:** ZFC set theory has countable models (even though it "proves" uncountable sets exist!)
- Resolution: "Uncountable" is relative to the model; countable from outside

**Difficulty:** medium

---

### Ultraproducts and Łoś's Theorem

**Natural Language Statement:**
Ultraproducts provide a construction for building new models from a family of structures. Given structures {Mᵢ}ᵢ∈I and an ultrafilter U on I, the ultraproduct ∏ᵢMᵢ/U consists of equivalence classes of tuples, where (aᵢ) ~ (bᵢ) iff {i : aᵢ = bᵢ} ∈ U.

**Łoś's Theorem:** A first-order formula φ(a₁,...,aₙ) is true in the ultraproduct iff the set of indices where φ holds in Mᵢ belongs to the ultrafilter:
```
∏ᵢMᵢ/U ⊨ φ([a₁],...,[aₙ])  ⟺  {i : Mᵢ ⊨ φ(a₁(i),...,aₙ(i))} ∈ U
```

**Proof Sketch (Łoś's Theorem):**
Induction on formula structure:
1. **Atomic:** Definition of ultraproduct operations
2. **¬φ:** Use ultrafilter property: A ∈ U ↔ Aᶜ ∉ U
3. **φ ∧ ψ:** Use A ∩ B ∈ U ↔ A ∈ U ∧ B ∈ U
4. **∃x.φ:** Use axiom of choice to select witnesses

**Lean 4 Formalization:**
```lean
import Mathlib.ModelTheory.Ultraproducts
import Mathlib.Order.Filter.Ultrafilter

-- Ultraproduct structure
def ultraproduct {I : Type*} (M : I → Type*) [∀ i, L.Structure (M i)]
    (U : Ultrafilter I) : L.Structure (Π i, M i / Setoid.ker sorry) :=
  sorry

-- Łoś's Theorem
theorem los_theorem {I : Type*} {M : I → Type*} [∀ i, L.Structure (M i)]
    (U : Ultrafilter I) (φ : L.BoundedFormula α n) (v : α → ultraproduct M U)
    (a : Fin n → Π i, M i) :
    ultraproduct M U ⊨ φ v (λ j => [a j])
    ↔ {i | M i ⊨ φ (v · i) (a · i)} ∈ U :=
  sorry
```

**Mathlib Status:** PARTIAL
- Ultrafilters: `Mathlib.Order.Filter.Ultrafilter` (FULL)
- Ultraproduct construction: In progress in `Mathlib.ModelTheory.Ultraproducts`
- Full Łoś's theorem: Under development

**Applications:**
1. **Compactness Theorem:** Alternative proof via ultraproducts
2. **Nonstandard Analysis:** Hyperreals as ultrapower of ℝ
3. **Transfer Principle:** Transfer first-order properties between standard/nonstandard models

**Difficulty:** medium

---

### Elementary Embeddings

**Natural Language Statement:**
An elementary embedding f : M → N is a structure-preserving map that preserves and reflects all first-order formulas. It's stronger than a homomorphism (which only preserves atomic formulas).

Formally: f is elementary iff for all formulas φ(x₁,...,xₙ) and elements a₁,...,aₙ ∈ M:
```
M ⊨ φ(a₁,...,aₙ)  ⟺  N ⊨ φ(f(a₁),...,f(aₙ))
```

Elementary embeddings preserve the "theory" of elements: f(a) and a satisfy the same formulas.

**Lean 4 Formalization:**
```lean
import Mathlib.ModelTheory.ElementaryMaps

-- Elementary embedding
structure ElementaryEmbedding (L : Language) (M N : Type*)
    [L.Structure M] [L.Structure N] extends M ↪ N where
  map_formula : ∀ {n} (φ : L.BoundedFormula Empty n) (x : Fin n → M),
    M.Realize φ x ↔ N.Realize φ (toEmbedding ∘ x)

notation:25 M " ↪ₑ[" L "] " N:24 => ElementaryEmbedding L M N

-- Elementary substructure
def ElementarySubstructure (L : Language) (M : Type*) [L.Structure M] :=
  {N : L.Substructure M // N.toStructure ↪ₑ[L] M}

notation:25 N " ≼ " M:24 => ElementarySubstructure L M
```

**Mathlib Status:** FULL
- Elementary embeddings: `Mathlib.ModelTheory.ElementaryMaps`
- Composition, identity, equivalence: Fully formalized
- Elementary substructures: `Language.ElementarySubstructure`

**Properties:**
1. Elementary embeddings are injective
2. Composition of elementary embeddings is elementary
3. If f : M ↪ₑ N and g : N ↪ₑ P, then g ∘ f : M ↪ₑ P
4. Elementary equivalence: M ≡ N iff there exist elementary embeddings into a common structure

**Difficulty:** medium

---

## 5. Computability Theory

### Recursive/Computable Functions

**Natural Language Statement:**
The recursive (computable) functions are those that can be computed by an algorithm. Formally defined as the smallest class containing:
- **Zero function:** Z(x) = 0
- **Successor:** S(x) = x + 1
- **Projection:** Pᵢⁿ(x₁,...,xₙ) = xᵢ
- **Composition:** If g, h₁,...,hₘ are recursive, so is f(x) = g(h₁(x),...,hₘ(x))
- **Primitive recursion:** If g and h are recursive, so is:
  ```
  f(0,x) = g(x)
  f(n+1,x) = h(n, f(n,x), x)
  ```
- **Unbounded minimization (μ-recursion):** If g is recursive and ∀x ∃y.g(x,y)=0, then:
  ```
  f(x) = μy.g(x,y) = 0  (least y such that g(x,y)=0)
  ```

**Primitive recursive functions** omit unbounded minimization (always terminate).
**General recursive functions** include μ-recursion (may not terminate).

**Lean 4 Formalization:**
```lean
import Mathlib.Computability.Primrec
import Mathlib.Computability.Partrec

-- Primitive recursive predicates
class Primrec {α β : Type*} [Primcodable α] [Primcodable β] (f : α → β) : Prop where
  prim : sorry  -- Provable from primrec axioms

-- Basic primitive recursive functions
#check Primrec.zero      -- Zero function
#check Primrec.succ      -- Successor
#check Primrec.const     -- Constant function
#check Primrec.comp      -- Composition
#check Nat.Primrec       -- Primitive recursion on ℕ

-- Partial recursive functions (using Part monad)
class Partrec {α β : Type*} [Primcodable α] [Primcodable β]
    (f : α → Part β) : Prop where
  part : sorry

-- μ-recursion (unbounded search)
#check Partrec.rfind     -- Least n with f n = 0 (or diverge)

-- Examples
example : Primrec (λ n : ℕ => n + n) := by
  exact Primrec.add.comp Primrec.id Primrec.id

-- Encoding: represent types as ℕ
class Primcodable (α : Type*) extends Encodable α where
  primrec_encode : Primrec encode
  primrec_decode : Primrec decode
```

**Mathlib Status:** FULL
- Primitive recursive functions: `Mathlib.Computability.Primrec`
- Partial recursive functions: `Mathlib.Computability.Partrec`
- Encoding to ℕ: `Primcodable` type class
- Developed by Mario Carneiro based on paper "Formalizing computability theory via partial recursive functions"

**Key Results in Mathlib:**
- `Primrec` and `Primrec₂` type classes
- `Partrec` for partial functions
- Universal partial recursive function
- Rice's theorem
- Halting problem undecidability

**Difficulty:** medium

---

### Halting Problem

**Natural Language Statement:**
There is no algorithm that determines, for arbitrary program P and input x, whether P(x) halts (terminates). The halting problem is undecidable.

**Proof Sketch (Diagonalization):**
1. Assume there exists a halting decider H: H(P,x) = true iff P(x) halts
2. Construct program D:
   ```
   D(P):
     if H(P, P) then loop_forever
     else halt
   ```
3. Ask: Does D(D) halt?
   - If D(D) halts, then H(D,D)=true, so D(D) loops forever. Contradiction.
   - If D(D) loops, then H(D,D)=false, so D(D) halts. Contradiction.
4. Therefore H cannot exist.

**Lean 4 Formalization:**
```lean
import Mathlib.Computability.Halting

-- Halting problem for partial recursive functions
def halts (c : ℕ) (a : ℕ) : Prop :=
  (Nat.Partrec.Code.ofNat c).eval a ≠ ⊥

-- Halting problem is not computable
theorem halting_problem_undecidable :
    ¬ ∃ f : ℕ → ℕ → Bool, Computable (Function.uncurry f) ∧
      ∀ c a, halts c a ↔ f c a = true := by
  sorry

-- Rice's Theorem: any non-trivial semantic property is undecidable
theorem rice_theorem {p : (ℕ →. ℕ) → Prop}
    (h_nontrivial : (∃ f, p f) ∧ (∃ f, ¬p f))
    (h_extensional : ∀ f g, (∀ n, f n = g n) → (p f ↔ p g)) :
    ¬ Decidable (p ∘ Nat.Partrec.Code.eval) := by
  sorry
```

**Mathlib Status:** FULL
- Halting problem: `Mathlib.Computability.Halting`
- Rice's theorem: Formalized
- Reduction methods available

**Significance:**
- First major undecidability result in computer science
- Foundation for complexity theory
- Shows limits of verification: cannot decide arbitrary program properties

**Difficulty:** medium

---

### Church-Turing Thesis

**Natural Language Statement (Philosophical):**
The Church-Turing thesis asserts that the informal notion of "computable function" (what can be computed by any algorithm) coincides with:
- Turing-computable functions (Turing machines)
- λ-definable functions (λ-calculus)
- μ-recursive functions (as defined above)
- Functions computable by any reasonable model of computation

This is a **philosophical claim**, not a mathematical theorem, because "computable by any algorithm" is informal. However, all proposed formalizations turn out equivalent.

**Equivalent Formulations:**
```
Informally computable
  = Turing-computable
  = λ-definable
  = μ-recursive
  = Register machine computable
  = While-program computable
```

**Lean 4 Formalization:**
```lean
-- Church-Turing thesis is NOT formally stated as a theorem
-- (informal notion cannot be formalized)

-- Instead, we formalize equivalences between models:

import Mathlib.Computability.TuringMachine
import Mathlib.Computability.Partrec

-- Example: Equivalence between Turing machines and partial recursive functions
theorem turing_computable_iff_partrec (f : ℕ → Part ℕ) :
    (∃ M : TuringMachine, M.computes f) ↔ Partrec f := by
  sorry

-- In practice, Lean uses type theory as model of computation
-- Computable = reducible to simple inductive operations
```

**Mathlib Status:** NOT FORMALIZED (philosophical claim)
- Equivalence results formalized: Turing machines ↔ partial recursive functions
- Various computation models available: `Mathlib.Computability.TuringMachine`, λ-calculus, etc.

**Importance:**
- Justifies studying any single model (all are equivalent)
- Establishes computability as robust concept
- Basis for complexity theory (P vs NP, etc.)

**Difficulty:** N/A (philosophical)

---

## 6. Curry-Howard Isomorphism

**Natural Language Statement:**
The Curry-Howard isomorphism establishes a deep correspondence between:
- **Propositions** (logic) ↔ **Types** (programming)
- **Proofs** (logic) ↔ **Programs** (programming)
- **Proof checking** ↔ **Type checking**

Under this correspondence:
```
Logic                    Programming
----------------------------------------
Proposition P            Type P
Proof of P               Term of type P
P ∧ Q                    Product type P × Q
P ∨ Q                    Sum type P ⊕ Q
P → Q                    Function type P → Q
⊥ (false)                Empty type
⊤ (true)                 Unit type
∀x:A. P(x)               Dependent product Π(x:A), P(x)
∃x:A. P(x)               Dependent sum Σ(x:A), P(x)
```

**Mathematical Statement:**
For intuitionistic logic and simply-typed λ-calculus:
```
P is provable  ⟺  Type P is inhabited (has a term)
Proof structure ≅ λ-term structure
```

**Lean 4 Formalization:**
```lean
-- Lean is BUILT on Curry-Howard isomorphism
-- Propositions ARE types in Lean (via Prop universe)

-- Conjunction as product
example (P Q : Prop) : P ∧ Q ≃ P × Q := by
  constructor
  · intro ⟨hp, hq⟩; exact ⟨hp, hq⟩
  · intro ⟨hp, hq⟩; exact ⟨hp, hq⟩

-- Implication as function type
example (P Q : Prop) (h : P → Q) (hp : P) : Q :=
  h hp  -- Function application

-- Universal quantification as dependent product (Π-type)
example (α : Type*) (P : α → Prop) : (∀ x, P x) ≃ Π x : α, P x := by
  rfl  -- Definitionally equal in Lean

-- Existential as dependent sum (Σ-type)
example (α : Type*) (P : α → Prop) : (∃ x, P x) ≃ Σ x : α, P x := by
  constructor
  · intro ⟨x, hx⟩; exact ⟨x, hx⟩
  · intro ⟨x, hx⟩; exact ⟨x, hx⟩

-- Proof = Program example
def modus_ponens {P Q : Prop} (h1 : P → Q) (h2 : P) : Q :=
  h1 h2  -- This is both a proof and a program!

-- Type hierarchy in Lean
#check Prop      -- Universe of propositions
#check Type      -- Universe of data types
#check Type 1    -- Higher universe
```

**Mathlib Status:** FOUNDATIONAL
- Curry-Howard is the **foundation** of Lean's design
- Not formalized as a theorem (it's the meta-theory)
- Lean's kernel implements the correspondence

**Proof Theory Connection:**
- **Natural Deduction** (proof system) ↔ **λ-calculus** (computation)
- Proof normalization ↔ Program evaluation
- Cut elimination (sequent calculus) ↔ β-reduction (λ-calculus)

**Lean's Type Theory:**
Lean uses **Calculus of Inductive Constructions (CIC)** with:
- Dependent types: Types can depend on values
- Inductive types: Define types by constructors
- Prop vs Type: Separation for proof irrelevance
- Impredicativity: Prop is impredicative (∀ P : Prop, P) : Prop

**Non-Constructive Extensions:**
Lean adds non-constructive axioms:
1. `Classical.choice` (axiom of choice)
2. `Quot.sound` (quotient types)
3. `propext` (propositional extensionality)

These break computational interpretation but preserve logical consistency.

**Difficulty:** medium (concept), foundational (in Lean)

---

## 7. Proof Theory

### Sequent Calculus

**Natural Language Statement:**
Sequent calculus is a proof system where judgments have form:
```
Γ ⊢ Δ
```
meaning "from hypotheses Γ, we can derive one of the conclusions Δ." In classical logic, this means "if all of Γ are true, at least one of Δ is true."

**Inference rules** include:
- **Axiom:** `P ⊢ P`
- **Left/Right rules** for each connective (∧, ∨, →, ¬, ∀, ∃)
- **Structural rules:** Weakening, Contraction, Exchange
- **Cut rule:** If `Γ ⊢ Δ, A` and `A, Γ' ⊢ Δ'`, then `Γ, Γ' ⊢ Δ, Δ'`

**Example (∧-Left):**
```
    Γ, A, B ⊢ Δ
  ――――――――――――――――  (∧-L)
   Γ, A ∧ B ⊢ Δ
```

**Lean 4 Formalization:**
```lean
-- NOT IN MATHLIB - Partial external formalization
-- Expected structure:

import Mathlib.Logic.Basic

-- Sequent: Γ ⊢ Δ (list of hypotheses ⊢ list of conclusions)
structure Sequent (α : Type*) where
  hypotheses : List α
  conclusions : List α

-- Inference rules as inductive type
inductive Derivable : Sequent Formula → Prop
  | axiom (P : Formula) : Derivable ⟨[P], [P]⟩
  | weakening_left {Γ Δ A} : Derivable ⟨Γ, Δ⟩ → Derivable ⟨A :: Γ, Δ⟩
  | and_left {Γ Δ A B} : Derivable ⟨A :: B :: Γ, Δ⟩ → Derivable ⟨(A ∧ B) :: Γ, Δ⟩
  | and_right {Γ Δ A B} : Derivable ⟨Γ, A :: Δ⟩ → Derivable ⟨Γ, B :: Δ⟩
                        → Derivable ⟨Γ, (A ∧ B) :: Δ⟩
  | cut {Γ Γ' Δ Δ' A} : Derivable ⟨Γ, A :: Δ⟩ → Derivable ⟨A :: Γ', Δ'⟩
                       → Derivable ⟨Γ ++ Γ', Δ ++ Δ'⟩
  -- ... (more rules)
```

**Mathlib Status:** NOT FORMALIZED
- Basic propositional logic: Available in `Mathlib.Logic.Basic`
- Sequent calculus: **Not in Mathlib**
- External project: `FormalizedFormalLogic/Foundation` (Lean 4) has some formal logic
- Isabelle/HOL has full formalization by Michaelis & Nipkow

**Difficulty:** medium

---

### Cut Elimination

**Natural Language Statement:**
The **cut-elimination theorem** (Gentzen's Hauptsatz) states: If a sequent Γ ⊢ Δ is derivable in sequent calculus with the cut rule, then it is also derivable without using cut (cut-free).

The **cut rule** allows:
```
  Γ ⊢ Δ, A      A, Γ' ⊢ Δ'
  ――――――――――――――――――――――――――  (Cut)
       Γ, Γ' ⊢ Δ, Δ'
```

Cut-free proofs have the **subformula property:** every formula in the proof is a subformula of the conclusion. This makes proof search decidable (at least for propositional logic).

**Proof Sketch:**
Double induction on:
1. Complexity of cut formula A
2. Sum of heights of the two derivations

**Key cases:**
- If cut formula A is principal in both premises (introduced by last rule), reduce to smaller cuts
- If A is not principal in one premise, permute cut upward
- Eventually eliminate all cuts

**Lean 4 Formalization:**
```lean
-- NOT IN MATHLIB
-- Expected structure:

-- Cut-free derivability
inductive CutFreeDerivable : Sequent Formula → Prop
  | axiom : ...
  | and_left : ...
  -- (All rules EXCEPT cut)

-- Cut elimination theorem
theorem cut_elimination {Γ Δ : List Formula} :
    Derivable ⟨Γ, Δ⟩ → CutFreeDerivable ⟨Γ, Δ⟩ := by
  sorry
```

**Mathlib Status:** NOT FORMALIZED
- Not in Mathlib
- **Isabelle/HOL formalization exists** (Michaelis & Nipkow)
- **Coq formalization exists** for linear logic sequent calculus

**Significance:**
1. **Consistency:** Cut-free system is obviously consistent (no proof of empty sequent)
2. **Decidability:** Subformula property enables proof search
3. **Normalization:** Analogous to β-reduction in λ-calculus (via Curry-Howard)

**Difficulty:** hard

---

### Natural Deduction

**Natural Language Statement:**
Natural deduction is a proof system designed to mirror mathematical reasoning. Proofs are trees where:
- **Hypotheses** appear as leaves (can be discharged)
- **Rules** introduce or eliminate logical connectives

**Introduction rules** construct connectives:
```
  A    B              A                    [A]ⁱ
  ―――――― (∧-I)      ――――――― (→-I)ⁱ           :
  A ∧ B             A → B                  B
                                        ――――――― (∀-I)
                                        ∀x. B
```

**Elimination rules** use connectives:
```
  A ∧ B            A ∧ B          A → B    A
  ――――― (∧-E₁)     ――――― (∧-E₂)    ――――――――――――― (→-E)
    A                B                  B
```

**Lean 4 Formalization:**
```lean
-- Lean's tactics implement natural deduction!

example (P Q : Prop) : P ∧ Q → Q ∧ P := by
  intro h              -- (→-I): Assume P ∧ Q
  constructor          -- (∧-I): Prove Q and P separately
  · exact h.2          -- (∧-E₂): Extract Q from P ∧ Q
  · exact h.1          -- (∧-E₁): Extract P from P ∧ Q

example (P Q R : Prop) : (P → Q) → (Q → R) → (P → R) := by
  intro hpq hqr hp     -- (→-I) three times
  exact hqr (hpq hp)   -- (→-E) twice
```

**Mathlib Status:** FOUNDATIONAL
- Lean's tactic system IS natural deduction
- `intro`, `constructor`, `exact`, `apply` are ND rules
- Proof terms correspond to ND derivations

**Curry-Howard for Natural Deduction:**
```
Natural Deduction Rule    λ-calculus Term Construction
――――――――――――――――――――――――    ――――――――――――――――――――――――――――
(→-I): A → B             λ-abstraction: λx:A. b
(→-E): Modus ponens      Application: f a
(∧-I): A ∧ B             Pair: ⟨a, b⟩
(∧-E): Projection        Projection: π₁, π₂
(∀-I): ∀x. P(x)          Dependent function: λx:A. b(x)
(∀-E): Instantiation     Application: f t
```

**Difficulty:** easy

---

### Proof Normalization

**Natural Language Statement:**
Proof normalization is the process of simplifying proofs by removing "detours" - cases where a connective is introduced and immediately eliminated.

**Normalization theorem:** Every natural deduction proof can be transformed into a **normal form** where no introduction rule is immediately followed by an elimination rule for the same connective.

**Example of a detour (for →):**
```
     [P]¹
      :
      Q
   ――――――― (→-I)¹    P
    P → Q         ―――――――――― (→-E)
           Q
```

This reduces to just deriving Q from P directly (substituting the proof of P into the derivation of Q).

**Curry-Howard Interpretation:**
Proof normalization ↔ β-reduction in λ-calculus
```
(λx. e) a  →β  e[a/x]
```

**Lean 4 Formalization:**
```lean
-- Not explicitly formalized, but implicit in Lean's kernel
-- Lean's kernel performs definitional reduction (β, ι, δ reduction)

example : (λ x : ℕ => x + 1) 0 = 1 := by
  rfl  -- Definitional equality via reduction

-- Normalization is part of Lean's metatheory
-- Strong normalization: All reductions terminate
-- (Not proven IN Lean, proven ABOUT Lean)
```

**Mathlib Status:** METATHEORETICAL
- Not formalized in Mathlib (part of Lean's metatheory)
- Lean's kernel implements normalization
- Consistency of Lean depends on strong normalization (proven externally)

**Significance:**
1. **Consistency:** Normal proofs cannot derive absurdity
2. **Decidability:** Normal proofs have decidable structure
3. **Canonicity:** Normal proofs are canonical representatives

**Connection to Cut Elimination:**
Normalization (natural deduction) ≈ Cut elimination (sequent calculus)

**Difficulty:** hard (metatheory)

---

## Summary Table: Formalization Status

| Topic | Lean/Mathlib Status | Difficulty | Freek #100 |
|-------|-------------------|-----------|-----------|
| **First-Order Logic Syntax** | FULL (`Mathlib.ModelTheory`) | medium | - |
| **Gödel Completeness** | PARTIAL (flypitch → Mathlib) | hard | #21 ✓ |
| **Compactness Theorem** | PARTIAL (flypitch → Mathlib) | medium | - |
| **Gödel 1st Incompleteness** | NOT FORMALIZED (external project) | hard | #55 ✗ |
| **Gödel 2nd Incompleteness** | NOT FORMALIZED | hard | - |
| **Löwenheim-Skolem** | FULL (`Mathlib.ModelTheory.Skolem`) | medium | - |
| **Ultraproducts & Łoś** | PARTIAL (in progress) | medium | - |
| **Elementary Embeddings** | FULL (`Mathlib.ModelTheory.ElementaryMaps`) | medium | - |
| **Primitive Recursive** | FULL (`Mathlib.Computability.Primrec`) | medium | - |
| **Partial Recursive** | FULL (`Mathlib.Computability.Partrec`) | medium | - |
| **Halting Problem** | FULL (`Mathlib.Computability.Halting`) | medium | - |
| **Church-Turing Thesis** | N/A (philosophical) | N/A | - |
| **Curry-Howard** | FOUNDATIONAL (Lean design) | foundational | - |
| **Sequent Calculus** | NOT FORMALIZED (external partial) | medium | - |
| **Cut Elimination** | NOT FORMALIZED (Isabelle/Coq yes) | hard | - |
| **Natural Deduction** | FOUNDATIONAL (Lean tactics) | easy | - |
| **Proof Normalization** | METATHEORETICAL | hard | - |

---

## References and Resources

### Mathlib Documentation
- [Mathlib.ModelTheory.Basic](https://leanprover-community.github.io/mathlib4_docs/Mathlib/ModelTheory/Basic.html) - Core model theory definitions
- [Mathlib.ModelTheory.Satisfiability](https://leanprover-community.github.io/mathlib4_docs/Mathlib/ModelTheory/Satisfiability.html) - Satisfiability and completeness foundations
- [Mathlib.ModelTheory.Skolem](https://leanprover-community.github.io/mathlib_docs/model_theory/skolem.html) - Löwenheim-Skolem theorems
- [Mathlib.Computability.Primrec](https://leanprover-community.github.io/mathlib_docs/computability/primrec.html) - Primitive recursive functions
- [Mathlib.Computability.Partrec](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Computability/Partrec.html) - Partial recursive functions
- [Mathlib.Computability.Halting](https://leanprover-community.github.io/mathlib_docs/computability/halting.html) - Halting problem

### Academic Papers & Projects
- **Flypitch Project:** Han & van Doorn, "A Formal Proof of the Independence of the Continuum Hypothesis" (2019) - [Paper](https://florisvandoorn.com/papers/flypitch-itp-2019.pdf)
- **Computability in Mathlib:** Carneiro, "Formalizing Computability Theory via Partial Recursive Functions" (2019)
- **Sequent Calculus in Isabelle:** Michaelis & Nipkow (formalized equivalence of proof systems)
- **Cut Elimination in Coq:** Linear logic sequent calculus formalization
- **FormalizedFormalLogic/Foundation:** [GitHub Project](https://github.com/FormalizedFormalLogic/Foundation) - Mathematical logic in Lean 4

### Textbooks & Surveys
- Enderton, *A Mathematical Introduction to Logic* - Standard FOL textbook
- Marker, *Model Theory: An Introduction* - Graduate model theory
- Hinman, *Fundamentals of Mathematical Logic* - Comprehensive logic text
- Sørensen & Urzyczyn, *Lectures on the Curry-Howard Isomorphism* - [PDF](https://disi.unitn.it/~bernardi/RSISE11/Papers/curry-howard.pdf)

### Wikipedia & Online Resources
- [Gödel's Completeness Theorem](https://en.wikipedia.org/wiki/Gödel%27s_completeness_theorem)
- [Gödel's Incompleteness Theorems](https://en.wikipedia.org/wiki/Gödel%27s_incompleteness_theorems)
- [Löwenheim-Skolem Theorem](https://en.wikipedia.org/wiki/Löwenheim–Skolem_theorem)
- [Curry-Howard Correspondence](https://en.wikipedia.org/wiki/Curry–Howard_correspondence)
- [Cut-Elimination Theorem](https://en.wikipedia.org/wiki/Cut-elimination_theorem)
- [100 Theorems List](https://leanprover-community.github.io/100.html) - Lean formalization progress

### Lean Community Resources
- [Lean Community GitHub](https://github.com/leanprover-community/mathlib4) - Mathlib4 repository
- [Zulip: Gödel Completeness](https://leanprover-community.github.io/archive/stream/116395-maths/topic/G.C3.B6del.20completeness.20theorem.html)
- [Zulip: Gödel Incompleteness](https://leanprover-community.github.io/archive/stream/113488-general/topic/Godel's.20incompleteness.20theorem.html)

---

## Research Notes

### Current Active Development (2025)
1. **Model Theory Migration:** Aaron Anderson leading integration of flypitch's completeness/compactness theorems into Mathlib
2. **Ultraproducts:** Partial implementation in progress
3. **Incompleteness Theorems:** External formalization exists, but not prioritized for Mathlib integration

### Major Gaps
1. **Gödel Incompleteness:** No Mathlib formalization; requires:
   - Arithmetization of syntax (Gödel numbering)
   - Representability theorems
   - Diagonal lemma
   - Provability logic
2. **Proof Theory:** Sequent calculus, cut elimination not formalized in Lean
   - Isabelle/HOL has comprehensive formalization
   - Could be ported to Lean

### Potential Formalization Projects
- **High Priority:** Complete incompleteness theorems (significant mathematical milestone)
- **Medium Priority:** Sequent calculus + cut elimination (proof theory foundations)
- **Low Priority:** Ultraproduct theory completion (some infrastructure exists)

### Dependencies for Dataset Generation
For creating theorem-proof pairs:
1. **Available Now:** First-order logic syntax, Löwenheim-Skolem, computability theory, elementary embeddings
2. **Coming Soon:** Completeness/compactness (flypitch migration)
3. **Long-term:** Incompleteness theorems (requires new formalization)

---

**End of Knowledge Base**
