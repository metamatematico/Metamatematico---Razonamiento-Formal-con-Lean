# Modern Foundations of Mathematics

**Knowledge Base for AI Mathematician Project**
**Date**: December 2025
**Evidence Grade**: High (Stanford Encyclopedia, academic sources)

---

## Executive Summary

Modern mathematics rests on **three primary foundational approaches**:

1. **Set-Theoretic** (ZFC, NBG, Tarski-Grothendieck, NF, Constructive Set Theory)
2. **Type-Theoretic** (Simple Type Theory, MLTT, CIC, Cubical Type Theory, Two-Level Type Theory)
3. **Category-Theoretic** (ETCS, Topos Theory, HoTT)

**Critical for this project**: Lean 4 is based on the **Calculus of Inductive Constructions (CIC)**, a dependent type theory—NOT ZFC. However, Mario Carneiro (2019) proved that Lean is **equiconsistent** with ZFC + finitely many inaccessible cardinals, meaning Lean can formalize essentially all classical mathematics.

---

## 1. Major Foundational Systems

### 1.1 Set-Theoretic Foundations

#### ZFC (Zermelo-Fraenkel with Choice)
- **Date**: 1908-1922
- **Key Figures**: Ernst Zermelo, Abraham Fraenkel
- **Status**: Standard foundation for most working mathematicians
- **Axioms**: Extensionality, Regularity, Specification, Pairing, Union, Power Set, Infinity, Replacement, Choice
- **Proof Assistants**: Metamath, Isabelle/ZF, Mizar (uses stronger TG)

#### NBG (von Neumann-Bernays-Gödel)
- **Date**: 1937
- **Key Figures**: John von Neumann, Paul Bernays, Kurt Gödel
- **Status**: Conservative extension of ZFC allowing proper classes
- **Relationship**: Finitely axiomatizable, equiconsistent with ZFC

#### Tarski-Grothendieck (TG)
- **Date**: 1939
- **Key Figures**: Alfred Tarski, Alexander Grothendieck
- **Status**: ZFC + existence of Grothendieck universes
- **Proof Assistants**: Mizar
- **Strength**: Strictly stronger than ZFC

#### New Foundations (NF/NFU)
- **Date**: 1937
- **Key Figure**: Willard Van Orman Quine
- **Status**: Alternative to ZFC based on stratified comprehension
- **Key Innovation**: Avoids Russell's paradox via stratification (not type hierarchy)
- **Consistency**: **Proven consistent in 2024** by Randall Holmes using Lean!
- **Variants**: NFU (NF with urelements) proven consistent by Jensen (1969)
- **Significance**: 70-year-old open problem resolved using proof assistant

#### Constructive Set Theory (CZF/IZF)
- **Date**: 1970s-1980s
- **Key Figures**: Peter Aczel, John Myhill
- **Status**: Set theory compatible with constructive logic
- **Variants**:
  - **CZF** (Constructive ZF): Predicative, no power set, collection instead of replacement
  - **IZF** (Intuitionistic ZF): Full ZF axioms with intuitionistic logic
- **Key Result**: Aczel showed CZF interpretable in Martin-Löf Type Theory
- **Relationship**: Bridge between set-theoretic and type-theoretic foundations
- **Significance**: Shows sets and types are not fundamentally opposed

#### Non-Well-Founded Set Theory (AFA)
- **Date**: 1988 (Aczel's formalization)
- **Key Figures**: Peter Aczel (building on Mirimanoff 1917, Forti-Honsell 1983)
- **Status**: Alternative set theory replacing Foundation axiom
- **Core Axiom (AFA)**: Every accessible pointed directed graph has a unique decoration
- **Key Properties**:
  - **Circular sets allowed**: x = {x} (Quine atoms) is permitted
  - **Self-referential structures**: Can model circular processes and infinite data
  - **Bisimulation**: Two sets are equal iff they are bisimilar
- **Variants**:
  - **BAFA** (Boffa's AFA): Allows multiple decorations
  - **SAFA** (Scott's AFA): Different uniqueness condition
- **Applications**:
  - Coalgebra theory and coinduction
  - Semantics for process calculi (CCS, π-calculus)
  - Modeling streams and lazy data structures
- **Relationship to NF**: Different motivation—AFA is local (per set), NF is global (stratification)
- **Proof Assistants**: Limited support; Isabelle/ZF has some development

### 1.2 Type-Theoretic Foundations

#### Simple Type Theory (STT)
- **Date**: 1908 (Russell), 1940 (Church)
- **Key Figures**: Bertrand Russell, Alonzo Church
- **Status**: Foundation for HOL-family proof assistants
- **Proof Assistants**: Isabelle/HOL, HOL Light, HOL4
- **Strength**: Weaker than ZFC (cannot express all of ZFC)

#### Martin-Löf Type Theory (MLTT)
- **Date**: 1975
- **Key Figure**: Per Martin-Löf
- **Status**: Constructive foundation with dependent types
- **Proof Assistants**: Agda
- **Features**: Propositions-as-types, proof relevance

#### Calculus of Inductive Constructions (CIC)
- **Date**: 1988
- **Key Figures**: Thierry Coquand, Gérard Huet
- **Status**: Foundation for Lean 4 and Coq
- **Features**: Dependent types, inductive types, impredicative Prop (Lean), predicative (Coq)
- **Strength**: ZFC + ω inaccessible cardinals (Carneiro 2019)

#### Cubical Type Theory (CTT)
- **Date**: 2015-2017
- **Key Figures**: Cyril Cohen, Thierry Coquand, Simon Huber, Anders Mörtberg
- **Status**: Major advancement providing computational univalence
- **Key Innovation**: Solves HoTT's canonicity problem—univalence computes!
- **Proof Assistants**: **Cubical Agda**, redtt, cooltt (2024-2025)
- **Core Idea**: Adds interval type I with endpoints 0 and 1; paths are functions I → A
- **Variants**:
  - **CCHM** (Cohen-Coquand-Huber-Mörtberg): Original cubical model
  - **Cartesian CTT**: Used in redtt/cooltt
- **Significance**: First type theory where univalence is not just an axiom but computes
- **Lean Compatibility**: Not directly compatible with Lean's impredicative Prop

#### Two-Level Type Theory (2LTT)
- **Date**: 2017
- **Key Figures**: Danil Annenkov, Paolo Capriotti, Nicolai Kraus, Christian Sattler
- **Status**: Combines HoTT-style reasoning with traditional type theory
- **Key Innovation**: Two levels—"fibrant" (HoTT-like) and "strict" (traditional)
- **Proof Assistants**: Agda (via experimental flags)
- **Core Idea**:
  - Inner level: Homotopy types with univalence
  - Outer level: Strict types for metatheoretic reasoning
- **Use Case**: Prove metatheorems about HoTT within type theory itself
- **Significance**: Resolves tension between homotopical and strict equality

### 1.3 Category-Theoretic Foundations

#### ETCS (Elementary Theory of the Category of Sets)
- **Date**: 1964
- **Key Figure**: F. William Lawvere
- **Status**: Categorical axiomatization of set theory
- **Relationship**: Equiconsistent with Bounded Zermelo with Choice (BZC)

#### Topos Theory
- **Date**: 1970s
- **Key Figures**: Alexander Grothendieck, F. William Lawvere
- **Status**: Generalizes set theory to arbitrary toposes
- **Features**: Internal logic, constructive reasoning

#### Homotopy Type Theory (HoTT)
- **Date**: 2011
- **Key Figures**: Vladimir Voevodsky, Steve Awodey, Univalent Foundations Program
- **Status**: Active research area combining type theory and homotopy theory
- **Key Innovation**: Univalence Axiom (isomorphic structures are equal)
- **Proof Assistants**: Coq/HoTT, Agda/HoTT, Arend

#### Algebraic Set Theory (AST)
- **Date**: 1995
- **Key Figures**: André Joyal, Ieke Moerdijk
- **Status**: Categorical axiomatization using ZF-algebras
- **Core Idea**: Define "small maps" in a category; ZF-algebras are categories with small maps satisfying ZF axioms
- **Key Properties**:
  - Completely constructive formulation
  - Works in Heyting pretoposes
  - Uniform description of forcing models
- **Relationship to Other Systems**:
  - Generalizes ETCS (more flexible)
  - Categories of classes approach to NBG (Awodey)
- **Significance**: Shows how to do set theory categorically without assuming sets exist first
- **References**: Joyal-Moerdijk book (Cambridge 1995), Awodey's tutorials (CMU)

#### SEAR (Sets, Elements, And Relations)
- **Date**: 2009
- **Key Figure**: Michael Shulman
- **Status**: Structural set theory alternative to ETCS
- **Core Idea**: Three primitive sorts (sets, elements, relations) with dependent typing
- **Key Properties**:
  - Not explicitly categorical (unlike ETCS)
  - Stronger than ETCS (includes collection)
  - Easier to understand for non-category theorists
  - Elements have no internal structure (structural approach)
- **Variants**:
  - **SEARC** (with Choice): Equivalent to ZFC
  - **ISEAR**: Intuitionistic version
  - **PSEAR**: Predicative version
  - **Bounded SEAR**: Equivalent to ETCS
- **Relationship to Category Theory**: Generates two metacategories—Set (functions) and Rel (relations)
- **Significance**: Shows structural foundations don't require full categorical machinery

---

## 2. Comparison Tables

### 2.1 Foundational Systems

| Foundation | Date | Type | Constructive? | Relative Strength |
|------------|------|------|---------------|-------------------|
| **ZFC** | 1922 | Set theory | No | Standard baseline |
| **NF/NFU** | 1937 | Set theory | No | ≈ ZFC (proven 2024) |
| **AFA (Non-WF)** | 1988 | Set theory | No | ≈ ZFC (different axiom) |
| **CZF** | 1978 | Set theory | Yes | < ZFC |
| **IZF** | 1980s | Set theory | Yes | ≈ ZFC − LEM |
| **Simple Type Theory** | 1940 | Type theory | No | < ZFC |
| **MLTT** | 1975 | Type theory | Yes | ≈ ZFC |
| **CIC** (Lean/Coq) | 1988 | Type theory | Yes (core) | ZFC + ω inaccessibles |
| **Cubical TT** | 2017 | Type theory | Yes | ≈ CIC |
| **Two-Level TT** | 2017 | Type theory | Yes | ≈ CIC + meta |
| **ETCS** | 1964 | Category theory | No | ≈ BZC |
| **AST** | 1995 | Category theory | Yes | Flexible |
| **SEAR** | 2009 | Structural | Variants | ≈ ETCS to ZFC |
| **Tarski-Grothendieck** | 1939 | Set theory | No | > CIC |
| **HoTT** | 2011 | Type theory | Yes | Under investigation |

### 2.2 Proof Assistant Foundations

| System | Foundation | Impredicative? | Proof-Relevant? | Classical by Default? |
|--------|------------|----------------|-----------------|----------------------|
| **Lean 4** | CIC | Prop only | Type: yes, Prop: no | No (axioms available) |
| **Coq** | pCIC | No | Yes | No (axioms available) |
| **Cubical Agda** | Cubical TT | No | Yes | No |
| **Agda** | MLTT | No | Yes | No (axioms available) |
| **Isabelle/HOL** | STT + axioms | Yes | N/A | Yes |
| **Mizar** | TG | N/A | N/A | Yes |
| **Metamath** | ZFC | N/A | N/A | Yes |
| **redtt/cooltt** | Cartesian CTT | No | Yes | No |

---

## 3. Equiconsistency Results

### 3.1 Key Theorems

| System A | System B | Relationship | Reference |
|----------|----------|--------------|-----------|
| Lean 4 | ZFC + {n inaccessibles : n < ω} | Equiconsistent | Carneiro 2019 |
| Coq | ZFC + countably many inaccessibles | Equiconsistent | Werner 1997 |
| ETCS | BZC (Bounded Zermelo + Choice) | Equiconsistent | Lawvere 1964 |
| Isabelle/HOL | Weaker than ZFC | STT < ZFC | — |
| NF | Consistent | **Proven 2024** | Holmes (Lean proof) |
| NFU | ZFC - Infinity | Equiconsistent | Jensen 1969 |
| CZF | MLTT | Interpretable | Aczel 1978 |
| Cubical TT | ≈ CIC | Similar strength | CCHM 2017 |

### 3.2 Interpretations

- **ZFC in CIC**: ZFC can be modeled in Lean/Coq type theory
- **CIC in ZFC**: Requires inaccessible cardinals to model universes
- **Practical implication**: Lean can formalize all mathematics that ZFC can

---

## 4. Constructive vs Classical Mathematics

### 4.1 Key Principles

| Principle | Classical | Constructive |
|-----------|-----------|--------------|
| Law of Excluded Middle (LEM): ∀P. P ∨ ¬P | Accepted | Rejected (not assumed) |
| Double Negation Elimination: ¬¬P → P | Accepted | Rejected |
| Full Axiom of Choice | Accepted | Often rejected |
| Proof = Witness | No | Yes |

### 4.2 Diaconescu's Theorem (1975)

**Full AC → LEM** in constructive type theory.

This means constructivists who want to avoid LEM must also restrict the axiom of choice. Bishop-style constructivism accepts countable choice but rejects full choice.

### 4.3 Lean's Position

- **Core**: Constructive (no LEM, no choice built-in)
- **Mathlib**: Classical (adds `Classical.choice`, `Classical.em`)
- **Tracking**: `#print axioms` shows which axioms a theorem depends on
- **Implication**: Most Mathlib proofs are non-constructive but verified correct

---

## 5. Lean 4 Specifics

### 5.1 Type Universe Hierarchy

```
Sort 0 = Prop       -- propositions (impredicative, proof-irrelevant)
Sort 1 = Type 0     -- small types
Sort 2 = Type 1     -- large types
...
Sort (u+1) = Type u -- universe polymorphism
```

### 5.2 Impredicative Prop

**Definition**: `∀ P : Prop, P` has type `Prop` (self-reference allowed)

**Why it works**: Proof irrelevance—all proofs of a proposition are equal

**Contrast with Coq**: Coq's `Prop` is predicative (no impredicativity)

### 5.3 Core Axioms

Lean's kernel assumes these axioms:

| Axiom | Purpose |
|-------|---------|
| `propext` | Propositional extensionality: (P ↔ Q) → P = Q |
| `funext` | Function extensionality: (∀x, f x = g x) → f = g |
| `Quot.sound` | Quotient soundness |
| `Classical.choice` | Axiom of choice (in Mathlib) |

### 5.4 Soundness Guarantee

**Carneiro's Theorem (2019)**: If ZFC + finitely many inaccessible cardinals is consistent, then Lean cannot prove `False`.

**Trusted Computing Base**:
1. Kernel: ~10K lines of C++ (being verified by Lean4Lean)
2. Core axioms: propext, funext, Quot.sound
3. Metatheory: ZFC + inaccessibles

---

## 6. Homotopy Type Theory (HoTT)

### 6.1 Core Idea

Types are interpreted as homotopy spaces:
- **Types** = Spaces
- **Terms** = Points
- **Identity types** = Paths
- **Higher identity types** = Higher homotopies

### 6.2 Univalence Axiom

**Statement**: Equivalent types are equal: (A ≃ B) ≃ (A = B)

**Implications**:
- Isomorphic structures can be substituted freely
- Formalizes common mathematical practice ("the" natural numbers)
- Implies function extensionality

### 6.3 Status in Lean

- HoTT requires a predicative, proof-relevant type theory
- Lean's impredicative Prop is incompatible with full HoTT
- Separate libraries exist (Lean-HoTT) using different conventions

---

## 7. Implications for AI Mathematician Project

### 7.1 Foundation Choice: CIC via Lean 4

**Advantages**:
- Equiconsistent with ZFC + large cardinals (covers all classical math)
- Strong automation via tactics and type inference
- Active community (Mathlib has 150K+ lemmas)
- Compiles to efficient code

**Limitations**:
- Some constructions require classical axioms
- Not fully compatible with HoTT
- Soundness relative to TCB (not absolute)

### 7.2 Practical Recommendations

1. **Accept classical axioms** for Mathlib compatibility
2. **Track axiom usage** via `#print axioms`
3. **Document constructive proofs** when achieved
4. **Trust Lean's verification** (comparable to Coq, Isabelle)

### 7.3 Axiom Auditing in Knowledge Graph

```
Theorem: First Isomorphism Theorem
├─ Status: Verified ✓
├─ Axioms: Classical.choice, Quot.sound, propext
├─ Constructive: No
└─ Soundness: High (modulo TCB)
```

---

## 8. Philosophical and Methodological Approaches

### 8.1 Set-Theoretic Multiverse (Hamkins)

- **Date**: 2012 (formalized)
- **Key Figure**: Joel David Hamkins
- **Core Thesis**: There is no single "true" set-theoretic universe V; instead, there are many equally valid set-theoretic universes

**Contrast with Universe View**:
| Aspect | Universe View (Traditional) | Multiverse View (Hamkins) |
|--------|----------------------------|---------------------------|
| Status of V | One true universe | Many valid universes |
| Continuum Hypothesis | Has definite truth value | True in some, false in others |
| Independence results | Incompleteness of axioms | Reveals multiverse structure |
| Goal | Find "right" axioms | Explore landscape of possibilities |

**Types of Multiverses**:
- **Broad/Radical Multiverse**: All models of any consistent set theory
- **Set-Generic Multiverse**: All forcing extensions of a core model
- **Countable Transitive Multiverse**: All CTMs

**Key Concepts**:
- **Potentialism**: Modal interpretation of mathematical existence
- **Width potentialism**: Can always widen universe (forcing)
- **Height potentialism**: Can always extend ordinals (large cardinals)
- **No "dream solution"**: CH has no definite answer waiting to be found

**Current Status (2024-2025)**:
- Active research program with dedicated workshops
- Connections to modal logic and potentialism
- Influential in philosophy of mathematics

**Relevance to Formalization**: Philosophical, not technical—doesn't affect what's provable in Lean, but shapes how we interpret foundational independence.

### 8.2 Reverse Mathematics (Friedman-Simpson)

- **Date**: 1974 (Friedman), 1980s (Simpson)
- **Key Figures**: Harvey Friedman, Stephen Simpson
- **Core Question**: What axioms are **necessary and sufficient** to prove theorems of ordinary mathematics?

**Framework**: Subsystems of second-order arithmetic (Z₂)

**The Big Five** (in increasing strength):
| System | Informal Description | Typical Theorems |
|--------|---------------------|------------------|
| **RCA₀** | Recursive comprehension | Basic algebra, sequences |
| **WKL₀** | Weak König's Lemma | Compactness, Heine-Borel |
| **ACA₀** | Arithmetical comprehension | Countable completions |
| **ATR₀** | Arithmetical transfinite recursion | Well-ordering comparability |
| **Π¹₁-CA₀** | Π¹₁ comprehension | Strongest in Big Five |

**Key Finding**: Most theorems of ordinary mathematics are **equivalent** (over RCA₀) to one of the Big Five.

**Examples**:
- **WKL₀ ↔** Heine-Borel theorem, Gödel's completeness theorem
- **ACA₀ ↔** Bolzano-Weierstrass, every vector space has a basis
- **ATR₀ ↔** Every countable ordinal embeds in ℚ, Ulm's theorem

**Connections to Foundational Programs**:
| System | Corresponding Program |
|--------|----------------------|
| RCA₀ | Bishop's constructivism |
| WKL₀ | Hilbert's finitistic reductionism |
| ACA₀ | Predicativism (given the natural numbers) |
| ATR₀, Π¹₁-CA₀ | Predicative reductionism |

**Significance**: Not a foundation itself, but a **methodology** for understanding foundations—reveals "what rests on what."

**Proof-Theoretic Ordinals**:
- **RCA₀**: ω^ω
- **WKL₀**: ω^ω (same, but proves more "practically")
- **ACA₀**: ε₀
- **ATR₀**: Γ₀ (Feferman-Schütte ordinal)

### 8.3 Predicativism (Weyl-Feferman)

- **Date**: 1906 (Poincaré), 1918 (Weyl), 1960s (Feferman)
- **Key Figures**: Henri Poincaré, Hermann Weyl, Solomon Feferman

**Core Principle**:
- **Impredicative**: Defining X by quantifying over a totality containing X (circular)
- **Predicative**: Only define objects in terms of previously defined ones

**Historical Critique**: Poincaré criticized Cantor's diagonal argument and Russell's type theory as circular.

**Weyl's *Das Kontinuum* (1918)**:
- Developed real analysis predicatively
- Avoided power set axiom
- Showed most of 19th-century analysis survives predicatively

**Feferman-Schütte Ordinal (Γ₀)**:
- **Limit of predicative mathematics**
- Largest ordinal provably exists predicatively
- Proof-theoretic analysis confirms this bound

**Proof-Theoretic Results**:
- Predicative math ≈ ATR₀ in reverse mathematics
- Conservative over PA for many purposes
- Most "ordinary" mathematics is predicative

**Modern Status**:
| System | Predicative? |
|--------|--------------|
| Lean's Prop | **Impredicative** |
| Coq's pCIC | **Predicative** (Set), Impredicative (Prop) |
| Agda | **Predicative** |
| CZF | **Predicative** |

**Relevance to Lean**: Lean's impredicative `Prop` is explicitly non-predicative. This is intentional and widely accepted in modern proof assistants, but historically controversial.

---

## 9. References

### Primary Sources

1. **Zermelo, E.** (1908). Untersuchungen über die Grundlagen der Mengenlehre I. *Mathematische Annalen*.

2. **Church, A.** (1940). A Formulation of the Simple Theory of Types. *Journal of Symbolic Logic*.

3. **Martin-Löf, P.** (1975). An Intuitionistic Theory of Types: Predicative Part. *Logic Colloquium*.

4. **Coquand, T. & Huet, G.** (1988). The Calculus of Constructions. *Information and Computation*.

5. **Lawvere, F.W.** (1964). An Elementary Theory of the Category of Sets. *PNAS*.

6. **Voevodsky, V. et al.** (2013). *Homotopy Type Theory: Univalent Foundations of Mathematics*. Institute for Advanced Study.

7. **Carneiro, M.** (2019). *The Type Theory of Lean*. Master's thesis, Carnegie Mellon University.

8. **de Moura, L. & Ullrich, S.** (2021). The Lean 4 Theorem Prover and Programming Language. *CADE*.

### Additional Primary Sources

9. **Quine, W.V.O.** (1937). New Foundations for Mathematical Logic. *American Mathematical Monthly*.

10. **Aczel, P.** (1978). The Type Theoretic Interpretation of Constructive Set Theory. *Logic Colloquium*.

11. **Cohen, C., Coquand, T., Huber, S., & Mörtberg, A.** (2017). Cubical Type Theory: A Constructive Interpretation of the Univalence Axiom. *TYPES*.

12. **Annenkov, D., Capriotti, P., Kraus, N., & Sattler, C.** (2017). Two-Level Type Theory and Applications. *MSCS*.

13. **Holmes, R. & Wilshaw, S.** (2024). A Machine-Checked Proof of the Consistency of New Foundations. *arXiv* (Lean formalization).

14. **Aczel, P.** (1988). *Non-Well-Founded Sets*. CSLI Lecture Notes.

15. **Joyal, A. & Moerdijk, I.** (1995). *Algebraic Set Theory*. Cambridge University Press.

16. **Shulman, M.** (2009). SEAR (Sets, Elements, And Relations). *nLab*.

17. **Hamkins, J.D.** (2012). The Set-Theoretic Multiverse. *Review of Symbolic Logic*.

18. **Simpson, S.** (2009). *Subsystems of Second-Order Arithmetic*. Cambridge University Press.

19. **Feferman, S.** (1964). Systems of Predicative Analysis. *Journal of Symbolic Logic*.

20. **Weyl, H.** (1918). *Das Kontinuum*. Leipzig. (English translation: *The Continuum*, Dover 1994).

### Encyclopedia Articles

- [Stanford Encyclopedia: Type Theory](https://plato.stanford.edu/entries/type-theory/)
- [Stanford Encyclopedia: Intuitionistic Type Theory](https://plato.stanford.edu/entries/type-theory-intuitionistic/)
- [Stanford Encyclopedia: Constructive Mathematics](https://plato.stanford.edu/entries/mathematics-constructive/)
- [Stanford Encyclopedia: Quine's New Foundations](https://plato.stanford.edu/entries/quine-nf/)
- [Stanford Encyclopedia: Constructive Set Theory](https://plato.stanford.edu/entries/set-theory-constructive/)
- [Stanford Encyclopedia: Non-Wellfounded Set Theory](https://plato.stanford.edu/entries/nonwellfounded-set-theory/)
- [Stanford Encyclopedia: Reverse Mathematics](https://plato.stanford.edu/entries/reverse-mathematics/)
- [nLab: Foundation of Mathematics](https://ncatlab.org/nlab/show/foundation+of+mathematics)
- [nLab: Homotopy Type Theory](https://ncatlab.org/nlab/show/homotopy+type+theory)
- [nLab: Cubical Type Theory](https://ncatlab.org/nlab/show/cubical+type+theory)
- [nLab: Two-Level Type Theory](https://ncatlab.org/nlab/show/two-level+type+theory)
- [nLab: SEAR](https://ncatlab.org/nlab/show/SEAR)
- [nLab: Algebraic Set Theory](https://ncatlab.org/nlab/show/algebraic+set+theory)
- [CMU: Algebraic Set Theory Project](https://www.phil.cmu.edu/projects/ast/)

### Technical Documentation

- [Lean 4: Dependent Type Theory](https://lean-lang.org/theorem_proving_in_lean4/dependent_type_theory.html)
- [Lean 4: Axioms and Computation](https://lean-lang.org/theorem_proving_in_lean4/axioms_and_computation.html)

---

## Appendix: Timeline of Foundations

| Year | Event |
|------|-------|
| 1879 | Frege's *Begriffsschrift* (predicate logic) |
| 1901 | Russell's Paradox |
| 1906 | Poincaré's critique of impredicativity |
| 1908 | Zermelo's axioms; Russell's ramified type theory |
| 1917 | Mirimanoff studies non-well-founded sets |
| 1918 | Weyl's *Das Kontinuum* (predicative analysis) |
| 1922 | Fraenkel's Replacement axiom (ZFC complete) |
| 1931 | Gödel's incompleteness theorems |
| 1937 | Quine's New Foundations (NF); NBG set theory |
| 1939 | Tarski-Grothendieck set theory |
| 1940 | Church's simple type theory |
| 1964 | Lawvere's ETCS; Feferman's predicative analysis |
| 1969 | Jensen proves NFU consistent |
| 1972 | Martin-Löf type theory (first version) |
| 1974 | Friedman initiates Reverse Mathematics |
| 1975 | Diaconescu's theorem (AC → LEM) |
| 1978 | Aczel's Constructive Set Theory (CZF); interpretation in MLTT |
| 1984 | Calculus of Constructions (Coquand-Huet) |
| 1988 | Calculus of Inductive Constructions; Aczel's AFA (non-well-founded sets) |
| 1995 | Joyal-Moerdijk's *Algebraic Set Theory* |
| 2006 | Voevodsky begins Univalent Foundations |
| 2009 | Shulman introduces SEAR; Simpson's *Subsystems of Second-Order Arithmetic* |
| 2012 | Hamkins formalizes Set-Theoretic Multiverse |
| 2013 | HoTT Book published |
| 2015-17 | Cubical Type Theory developed (CCHM) |
| 2017 | Two-Level Type Theory introduced |
| 2019 | Carneiro proves Lean equiconsistent with ZFC + inaccessibles |
| 2021 | Lean 4 released |
| 2024 | **NF consistency proven using Lean** (Holmes & Wilshaw) |
| 2024-25 | redtt/cooltt cubical proof assistants mature |
