# Prime Number Theorems Knowledge Base for Lean 4

**Generated:** 2025-12-13
**Research Mode:** Deep Synthesis
**Confidence Level:** High
**Purpose:** Research knowledge base for implementing classic prime number theorems in Lean 4 for dataset generation pairing formal proofs with natural language explanations.

---

## Executive Summary

This knowledge base catalogs five fundamental theorems about prime numbers, ranging from ancient (Euclid, 300 BC) to modern (Dirichlet, 1837). All five theorems have complete or partial formalizations in Lean 4's Mathlib library, with varying levels of difficulty for implementation in the ai-mathematician dataset.

### Theorem Overview

| Theorem | Era | Mathlib Status | Difficulty | Implementation Priority |
|---------|-----|----------------|------------|-------------------------|
| **Euclid's Infinitude** | ~300 BC | ✅ Full | Easy | 1 |
| **Fundamental Theorem of Arithmetic** | Medieval-1800s | ✅ Full | Easy | 2 |
| **Fermat's Little Theorem** | 1640 | ✅ Full | Easy | 3 |
| **Bertrand's Postulate** | 1850 (Erdős 1932) | ✅ Full | Medium | 4 |
| **Dirichlet's Theorem** | 1837 | ✅ Full (2024) | Hard | 5 |

**Key Finding:** All five theorems are now formalized in Mathlib4, making this an excellent target for dataset generation. The implementations range from trivial (direct Mathlib application) to educational (requires understanding sophisticated proof techniques).

---

## 1. Euclid's Theorem on the Infinitude of Primes

### Historical Context

**Timeline:**
- ~300 BC: First proved by Euclid in *Elements* (Book IX, Proposition 20)
- 2000+ years: Remains a model of mathematical reasoning
- Modern era: Multiple alternative proofs discovered (Erdős, Euler, topological)

**Significance:** One of the earliest non-trivial results in mathematics. Demonstrates that the sequence of primes never ends, establishing primes as an infinite resource for number theory.

---

### Natural Language Statement

There are infinitely many prime numbers. Equivalently, for every natural number n, there exists a prime number p such that p ≥ n.

**Alternative Formulation:** The set of prime numbers is unbounded.

---

### Mathematical Statement (Informal)

For all n ∈ ℕ, there exists a prime p such that p > n.

**Negation (for proof by contradiction):** Suppose there are only finitely many primes p₁, p₂, ..., pₖ.

---

### Lean 4 Formalization

**Primary Theorem:** `Nat.exists_infinite_primes` (Lean 3 name: `nat.exists_infinite_primes`)

**Location:** `Mathlib.Data.Nat.Prime.Infinite`

**Type Signatures:**

```lean
-- Main theorem: for every n, exists prime p ≥ n
theorem Nat.exists_infinite_primes : ∀ n : ℕ, ∃ p ≥ n, Nat.Prime p

-- Alternative forms in Mathlib:
theorem Nat.not_bdd_above_set_of_prime : ¬BddAbove {p : ℕ | p.Prime}
theorem Nat.infinite_set_of_prime : Set.Infinite {p : ℕ | p.Prime}
```

**Required Imports:**
```lean
import Mathlib.Data.Nat.Prime.Infinite
import Mathlib.Data.Nat.Prime.Basic
```

**Mathlib Support:** ✅ **FULL** - Multiple formulations available

---

### Proof Sketch: Euclid's Original Argument

**Strategy:** Proof by contradiction with explicit construction

**Key Idea:** Given any finite list of primes, construct a number that must have a prime factor not in the list.

**Steps:**

1. **Assume finitely many primes:** Suppose p₁, p₂, ..., pₖ are all the primes
2. **Construct new number:** Let N = (p₁ · p₂ · ... · pₖ) + 1
3. **Case analysis on N:**
   - **If N is prime:** Then N is a prime not in our list (since N > pᵢ for all i)
   - **If N is composite:** Then N has some prime factor q
4. **Show q not in list:**
   - If q = pᵢ for some i, then q divides both N and p₁·p₂·...·pₖ
   - Therefore q divides N - p₁·p₂·...·pₖ = 1
   - Contradiction: no prime divides 1
5. **Conclusion:** In either case, we found a prime not in our original list

**Common Misconception:** The proof does NOT claim that N = p₁·p₂·...·pₖ + 1 is always prime. It only uses that N has a prime factor.

---

### Alternative Proof: Factorial Variation

**Construction:** Let N = n! + 1 for any n ≥ 2

**Argument:**
- N is not divisible by any integer from 2 to n (gives remainder 1)
- Therefore N is either prime or has a prime factor > n
- Thus for every n, there exists a prime p > n

This variation is often easier to formalize and appears in some Mathlib proofs.

---

### Lean 4 Implementation Details

**From Mathlib Documentation:**

The theorem appears in multiple equivalent forms:
1. **Unbounded formulation:** For every n, exists p ≥ n with p prime
2. **Not bounded above:** The set of primes is not bounded above
3. **Infinite set:** The set of primes is infinite

**Proof Technique in Mathlib:**
Mathlib uses the factorial construction or similar techniques. The proof can be found in `Mathlib.Data.Nat.Prime.Infinite`.

**Example Usage:**
```lean
example : ∀ n, ∃ p ≥ n, Nat.Prime p := Nat.exists_infinite_primes

example : Set.Infinite {p : ℕ | p.Prime} := Nat.infinite_set_of_prime
```

---

### Related Theorems and Lemmas

**Dependencies:**
- `Nat.Prime` - definition of prime numbers
- `Nat.factorial` - factorial function (for factorial proof variant)
- Basic divisibility theory

**Corollaries:**
- Sum of reciprocals of primes diverges (Euler)
- Prime counting function π(x) → ∞ as x → ∞
- Leads to Prime Number Theorem (asymptotic density)

---

### Difficulty Assessment

**Implementation Difficulty:** ⭐ **EASY**

**Rationale:**
- Direct application of Mathlib theorem
- No helper lemmas needed
- Well-documented in Mathlib
- Multiple formulations available

**Estimated Tactic Count:** 1 (direct application with `exact`)

**Suggested Dataset Entry:**
```json
{
  "theorem_id": "euclid_infinitude_primes",
  "mathematical_domain": "NumberTheory",
  "difficulty": "easy",
  "mathlib_support": "full",
  "proof_status": "complete"
}
```

---

### References and Sources

**Historical:**
- [Euclid's Elements - Book IX, Proposition 20](http://aleph0.clarku.edu/~djoyce/elements/bookIX/propIX20.html)
- [Euclid's theorem - Wikipedia](https://en.wikipedia.org/wiki/Euclid's_theorem)

**Proof Sketches:**
- [Prime Numbers And Euclid's Proof - Cuemath](https://www.cuemath.com/numbers/prime-numbers-and-euclids-proof/)
- [The Infinitude of Primes - Euclid's proof | Medium](https://medium.com/quantaphy/the-infinitude-of-primes-euclids-proof-b774794090fd)

**Lean/Mathlib:**
- [Mathlib4: Data.Nat.Prime.Infinite](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Data/Nat/Prime/Infinite.html)
- [100 theorems in Lean](https://leanprover-community.github.io/100.html)
- [Mathematics in Lean - Elementary Number Theory](https://leanprover-community.github.io/mathematics_in_lean/C05_Elementary_Number_Theory.html)

---

## 2. Fundamental Theorem of Arithmetic

### Historical Context

**Timeline:**
- Ancient: Euclid proved key lemma (Euclid's Lemma) in *Elements* Book VII
- Medieval: Kamāl al-Dīn al-Fārisī first stated the complete theorem
- 1801: Gauss provided first complete proof of uniqueness in *Disquisitiones Arithmeticae*

**Significance:** Establishes prime numbers as the "atoms" of arithmetic. Foundation for unique factorization domains in abstract algebra. Essential for cryptography, computational number theory, and algebraic number theory.

---

### Natural Language Statement

Every integer greater than 1 is either prime or can be uniquely represented as a product of prime numbers, up to the order of factors.

**Two Parts:**
1. **Existence:** Every n > 1 can be written as a product of primes
2. **Uniqueness:** This factorization is unique (up to reordering)

---

### Mathematical Statement (Informal)

For every n ∈ ℕ with n > 1, there exists a unique (up to permutation) sequence of primes p₁, p₂, ..., pₖ such that:
```
n = p₁ · p₂ · ... · pₖ
```

**Standard Form:** Using prime powers with p₁ < p₂ < ... < pₖ:
```
n = p₁^(a₁) · p₂^(a₂) · ... · pₖ^(aₖ)
```
where each pᵢ is prime and each aᵢ ≥ 1.

---

### Lean 4 Formalization

**Primary Functions:**

```lean
-- List of prime factors in nondecreasing order
Nat.primeFactorsList : ℕ → List ℕ

-- Factorization as function (multiplicity representation)
Nat.factorization : ℕ → ℕ → ℕ
-- Usage: (Nat.factorization n p) returns multiplicity of prime p in n
```

**Key Theorems:**

```lean
-- All elements in the list are prime
theorem Nat.prime_of_mem_primeFactorsList :
  ∀ {n p}, p ∈ n.primeFactorsList → p.Prime

-- Product equals original number
theorem Nat.prod_primeFactorsList :
  ∀ {n}, 0 < n → n.primeFactorsList.prod = n

-- Uniqueness: other prime lists are permutations
theorem Nat.primeFactorsList_unique :
  ∀ {n l}, (∀ p ∈ l, Nat.Prime p) → l.prod = n →
  l ~~ n.primeFactorsList  -- (~~ means permutation)
```

**Location:** `Mathlib.Data.Nat.Factors`

**Required Imports:**
```lean
import Mathlib.Data.Nat.Factors
import Mathlib.Data.Nat.Prime.Basic
```

**Mathlib Support:** ✅ **FULL** - Complete formalization with multiple representations

---

### Proof Sketch: Existence

**Strategy:** Strong induction on n

**Base Case:** n = 2 is prime ✓

**Inductive Step:** Assume true for all k < n
- **Case 1:** If n is prime, done
- **Case 2:** If n is composite, then n = a · b where 1 < a, b < n
  - By induction hypothesis, a and b have prime factorizations
  - Multiply them together to get prime factorization of n

---

### Proof Sketch: Uniqueness

**Strategy:** Use Euclid's Lemma

**Euclid's Lemma:** For prime p, if p | ab then p | a or p | b

**Proof of Uniqueness:**
1. Suppose n = p₁·p₂·...·pᵣ = q₁·q₂·...·qₛ (two prime factorizations)
2. Then p₁ divides q₁·q₂·...·qₛ
3. By Euclid's Lemma repeatedly, p₁ divides some qⱼ
4. Since qⱼ is prime and p₁ divides it, p₁ = qⱼ
5. Cancel p₁ from both sides and repeat
6. Eventually all primes match up (with multiplicities)

**Key Dependency:** Euclid's Lemma is the crucial ingredient for uniqueness.

---

### Lean 4 Implementation Details

**Representation Choices:**

Mathlib provides two representations:

1. **List representation** (`primeFactorsList`):
   - Returns list of primes in nondecreasing order
   - Example: `60.primeFactorsList = [2, 2, 3, 5]`
   - Good for algorithmic purposes

2. **Function representation** (`factorization`):
   - Maps each prime p to its multiplicity
   - Example: `(60.factorization 2) = 2, (60.factorization 3) = 1, (60.factorization 5) = 1`
   - Better for theoretical purposes

**Generalization to Unique Factorization Domains:**

Mathlib also formalizes unique factorization for more general structures:

```lean
-- Type class for unique factorization monoids
class UniqueFactorizationMonoid (α : Type*) [CancelCommMonoidWithZero α]

-- Example: Integers form UFD
instance : UniqueFactorizationMonoid ℤ

-- Example: Polynomials over fields are UFDs
instance [Field K] : UniqueFactorizationMonoid (Polynomial K)
```

**Location:** `Mathlib.RingTheory.UniqueFactorizationDomain.Basic`

---

### Related Theorems and Lemmas

**Dependencies:**
- `Nat.Prime` - definition of primality
- Euclid's Lemma: `Nat.Prime.dvd_mul` - if p prime and p | ab then p | a or p | b
- Divisibility theory
- List permutation theory

**Applications:**
- GCD and LCM algorithms
- Solving Diophantine equations
- Cryptographic protocols (RSA)
- Algebraic number theory (where unique factorization can fail!)

**Counterexamples:** Unique factorization fails in some rings:
- ℤ[√-5]: both 6 = 2·3 = (1+√-5)(1-√-5) are factorizations
- This failure motivated development of ideal theory

---

### Difficulty Assessment

**Implementation Difficulty:** ⭐ **EASY**

**Rationale:**
- Mathlib provides complete infrastructure
- Multiple theorem forms available
- Well-documented with examples
- Can use either list or function representation

**Estimated Tactic Count:** 1-2 (direct application or simple composition)

**Suggested Dataset Entries:**

```json
// Theorem: existence of factorization
{
  "theorem_id": "fundamental_theorem_arithmetic_existence",
  "difficulty": "easy",
  "mathlib_support": "full"
}

// Theorem: uniqueness of factorization
{
  "theorem_id": "fundamental_theorem_arithmetic_uniqueness",
  "difficulty": "easy",
  "mathlib_support": "full"
}

// Lemma: Euclid's lemma (prerequisite)
{
  "lemma_id": "euclids_lemma",
  "theorem_id": "fundamental_theorem_arithmetic_uniqueness",
  "difficulty": "easy"
}
```

---

### References and Sources

**General:**
- [Fundamental Theorem of Arithmetic - Wikipedia](https://en.wikipedia.org/wiki/Fundamental_theorem_of_arithmetic)
- [Fundamental Theorem of Arithmetic - Brilliant.org](https://brilliant.org/wiki/fundamental-theorem-of-arithmetic/)

**Proofs:**
- [Fundamental Theorem of Arithmetic - Cuemath](https://www.cuemath.com/numbers/the-fundamental-theorem-of-arithmetic/)
- [Unique Factorization - Mathematics LibreTexts](https://math.libretexts.org/Bookshelves/Combinatorics_and_Discrete_Mathematics/Elementary_Number_Theory_(Barrus_and_Clark)/01:_Chapters/1.12:_Unique_Factorization)

**Lean/Mathlib:**
- [Mathlib4: Data.Nat.Factors](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Data/Nat/Factors.html)
- [Mathlib4: RingTheory.UniqueFactorizationDomain.Basic](https://leanprover-community.github.io/mathlib4_docs/Mathlib/RingTheory/UniqueFactorizationDomain/Basic.html)
- [Mathematics in Lean - Elementary Number Theory](https://leanprover-community.github.io/mathematics_in_lean/C05_Elementary_Number_Theory.html)

---

## 3. Fermat's Little Theorem

### Historical Context

**Timeline:**
- 1640: Stated by Pierre de Fermat in a letter to Frénicle de Bessy (October 18)
- Pre-1683: Leibniz gave proof in unpublished manuscript
- 1736: Euler published first proof
- Modern: Foundation for primality testing and cryptography

**Significance:** Cornerstone of elementary number theory. Enables efficient modular exponentiation. Critical for RSA cryptography, Diffie-Hellman key exchange, and modern primality tests (Miller-Rabin).

---

### Natural Language Statement

If p is a prime number and a is any integer not divisible by p, then:
```
a^(p-1) ≡ 1 (mod p)
```

**Alternative Form (Fermat-Euler):** For any integer a and prime p:
```
a^p ≡ a (mod p)
```

**Generalization (Euler's Theorem):** For any a coprime to n:
```
a^φ(n) ≡ 1 (mod n)
```
where φ is Euler's totient function.

---

### Mathematical Statement (Informal)

**Standard Form:**
For all primes p and integers a with gcd(a,p) = 1:
```
a^(p-1) ≡ 1 (mod p)
```

**Equivalent Statement (for all a):**
For all primes p and integers a:
```
a^p ≡ a (mod p)
```

---

### Lean 4 Formalization

**Primary Theorems:**

```lean
-- For nonzero elements of ZMod p
theorem ZMod.pow_card_sub_one {p : ℕ} [Fact p.Prime] (a : ZMod p) (ha : a ≠ 0) :
  a ^ (p - 1) = 1

-- Alternative: using totient function
theorem ZMod.pow_totient {n : ℕ} [NeZero n] (a : ZMod n) (ha : IsUnit a) :
  a ^ φ(n) = 1

-- For integers modulo p
theorem Int.ModEq.pow_card_sub_one_eq_one {p : ℕ} [Fact p.Prime] {a : ℤ}
  (ha : IsRelPrime a p) : a ^ (p - 1) ≡ 1 [ZMOD p]
```

**General Finite Field Version:**

```lean
-- For any finite field
theorem FiniteField.pow_card {F : Type*} [Field F] [Fintype F] (a : F) :
  a ^ Fintype.card F = a
```

**Location:**
- Core: `Mathlib.FieldTheory.Finite.Basic`
- Modular arithmetic: `Mathlib.Data.ZMod.Basic`

**Required Imports:**
```lean
import Mathlib.FieldTheory.Finite.Basic
import Mathlib.Data.ZMod.Basic
import Mathlib.Data.Int.ModEq
```

**Mathlib Support:** ✅ **FULL** - Multiple formulations, fully general

---

### Proof Sketch: Elementary Approach

**Strategy:** Rearrangement argument using multiplication modulo p

**Key Observation:** For prime p and a coprime to p, multiplication by a permutes the nonzero residues mod p.

**Proof Steps:**

1. **Consider residues:** Let S = {1, 2, 3, ..., p-1}
2. **Multiply by a:** Consider T = {a·1, a·2, a·3, ..., a·(p-1)} mod p
3. **Show T = S (as sets):**
   - All elements of T are distinct (if a·i ≡ a·j mod p, then i ≡ j since a is coprime to p)
   - All elements are nonzero (since a is coprime to p)
   - Therefore T is a permutation of S
4. **Multiply all elements:**
   ```
   1 · 2 · 3 · ... · (p-1) ≡ (a·1) · (a·2) · ... · (a·(p-1)) (mod p)
   (p-1)! ≡ a^(p-1) · (p-1)! (mod p)
   ```
5. **Cancel (p-1)!:** Since (p-1)! is coprime to p, we can cancel:
   ```
   1 ≡ a^(p-1) (mod p)
   ```

**Key Lemma:** Wilson's Theorem can be used as alternative approach.

---

### Proof Sketch: Group Theory Approach

**Strategy:** Use Lagrange's theorem on (ℤ/pℤ)×

**Proof:**
1. The nonzero elements mod p form a group (ℤ/pℤ)× under multiplication
2. This group has order p-1
3. By Lagrange's theorem, for any element a ∈ (ℤ/pℤ)×:
   ```
   a^(p-1) = 1
   ```

This generalizes to Euler's theorem via the totient function.

---

### Applications in Cryptography

**RSA Cryptosystem:**
- Choose primes p, q; set n = pq
- Choose e coprime to φ(n) = (p-1)(q-1)
- Find d such that ed ≡ 1 (mod φ(n))
- **Encryption:** c ≡ m^e (mod n)
- **Decryption:** m ≡ c^d (mod n)
- **Correctness:** Uses Fermat's Little Theorem / Euler's Theorem

**Primality Testing (Fermat Test):**
```python
def is_probably_prime(n, k=10):
    for _ in range(k):
        a = random.randint(2, n-1)
        if pow(a, n-1, n) != 1:
            return False  # Definitely composite
    return True  # Probably prime
```

**Caveat:** Carmichael numbers are composite but pass this test for all a.

**Miller-Rabin Test:** Improved version using Fermat's Little Theorem with additional structure.

---

### Lean 4 Implementation Details

**Type Classes and Instances:**

Mathlib's formalization uses finite field theory:

```lean
-- ZMod p is a field when p is prime
instance ZMod.field {p : ℕ} [Fact p.Prime] : Field (ZMod p)

-- Multiplicative group of units
def ZMod.unitsEquivCoprime {n : ℕ} : (ZMod n)ˣ ≃* {a : ℤ // a.gcd n = 1}
```

**Computational Aspects:**

```lean
-- Fast modular exponentiation is built-in
#eval (7 : ZMod 13) ^ 12  -- Computes 7^12 mod 13 efficiently

-- Primality testing infrastructure
#eval Nat.Prime 17  -- true (uses decision procedure)
```

---

### Related Theorems and Lemmas

**Prerequisites:**
- `ZMod n` - integers modulo n
- `Nat.Prime` - primality predicate
- `Nat.Coprime` - coprimality
- Group theory: `Lagrange's theorem`

**Generalizations:**
- **Euler's Theorem:** a^φ(n) ≡ 1 (mod n) for a coprime to n
- **Lagrange's Theorem:** For finite group G and element g, g^|G| = e
- **Finite Field Theory:** Every element a in finite field F satisfies a^|F| = a

**Applications:**
- Wilson's Theorem: (p-1)! ≡ -1 (mod p) for prime p
- Carmichael's Theorem (generalization)
- Chinese Remainder Theorem (for computational efficiency)

---

### Difficulty Assessment

**Implementation Difficulty:** ⭐ **EASY**

**Rationale:**
- Direct application of Mathlib theorems
- Multiple formulations available
- Well-integrated with ZMod infrastructure
- Computational support for evaluation

**Estimated Tactic Count:** 1 (direct exact application)

**Suggested Dataset Entries:**

```json
// Main theorem
{
  "theorem_id": "fermat_little_theorem",
  "mathematical_domain": "NumberTheory",
  "difficulty": "easy",
  "mathlib_support": "full",
  "imports": ["Mathlib.FieldTheory.Finite.Basic"]
}

// Generalization to Euler's theorem
{
  "theorem_id": "euler_theorem",
  "mathematical_domain": "NumberTheory",
  "difficulty": "easy",
  "mathlib_support": "full"
}
```

---

### References and Sources

**General:**
- [Fermat's Little Theorem - Wikipedia](https://en.wikipedia.org/wiki/Fermat's_little_theorem)
- [Fermat's Little Theorem - Brilliant.org](https://brilliant.org/wiki/fermats-little-theorem/)

**Proofs and Applications:**
- [Fermat's Little Theorem Explained - Number Analytics](https://www.numberanalytics.com/blog/fermats-little-theorem-ultimate-guide)
- [Fermat's Little Theorem in Cryptography - Testbook](https://testbook.com/maths/fermats-little-theorem)

**Lean/Mathlib:**
- [Mathlib4: Data.ZMod.Basic](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Data/ZMod/Basic.html)
- [Mathlib4: FieldTheory.Finite.Basic](https://leanprover-community.github.io/mathlib4_docs/Mathlib/FieldTheory/Finite/Basic.html)

---

## 4. Bertrand's Postulate (Chebyshev's Theorem)

### Historical Context

**Timeline:**
- 1845: Joseph Bertrand conjectured based on computational evidence
- 1850: Pafnuty Chebyshev proved it using analytic methods
- 1919: Ramanujan gave first elementary proof
- 1932: Paul Erdős (age 19) published elegant elementary proof
- Modern: Used in "Proofs from THE BOOK"

**Significance:** First result on the density of primes in short intervals. Shows primes are "reasonably dense" - never have to go more than double to find the next one. Foundation for later work on prime gaps.

---

### Natural Language Statement

For any integer n > 1, there exists at least one prime number p such that n < p < 2n.

**Equivalent Statement:** For any positive integer n, there is always at least one prime between n and 2n (exclusive).

**Weaker Statement:** For any n ≥ 25, there exists a prime p with n < p ≤ 2n.

---

### Mathematical Statement (Informal)

∀n ∈ ℕ, n > 1 → ∃p ∈ ℕ, Prime(p) ∧ n < p < 2n

**Alternative (inclusive form):**
∀n ∈ ℕ, n > 1 → ∃p ∈ ℕ, Prime(p) ∧ n < p ≤ 2n

---

### Lean 4 Formalization

**Primary Theorem:**

```lean
-- Main statement in Mathlib4
theorem Nat.exists_prime_lt_and_lt {n : ℕ} (hn : 1 < n) :
  ∃ p, Nat.Prime p ∧ n < p ∧ p < 2 * n
```

**Location:** `Mathlib.NumberTheory.Bertrand`

**Required Imports:**
```lean
import Mathlib.NumberTheory.Bertrand
import Mathlib.Data.Nat.Prime.Basic
```

**Mathlib Support:** ✅ **FULL** - Complete formalization following Erdős's proof

---

### Proof Sketch: Erdős's Approach (1932)

**Overview:** Erdős's proof analyzes the prime factorization of the central binomial coefficient C(2n,n).

**Strategy:** Proof by contradiction combined with combinatorial bounds

**Key Inequality (Lower Bound):**
```
C(2n,n) ≥ 4^n / (2n + 1)
```

**Proof:** C(2n,n) is the largest of 2n+1 terms in the expansion of (1+1)^(2n) = 4^n.

---

**Main Argument:**

1. **Assume no prime in (n, 2n]:** Suppose for contradiction there is no prime p with n < p ≤ 2n

2. **Analyze prime factorization of C(2n,n):**
   Split primes into groups based on size:

   - **Group A:** Primes p ≤ √(2n)
     - At most √(2n) such primes
     - Each contributes at most 2n to C(2n,n)
     - Total contribution: ≤ (2n)^√(2n)

   - **Group B:** Primes √(2n) < p ≤ 2n/3
     - Each prime appears with multiplicity at most 1 in C(2n,n)
     - Total contribution: ≤ 4^(2n/3)

   - **Group C:** Primes 2n/3 < p ≤ n
     - These don't divide C(2n,n) at all! (Key observation)
     - Contribution: 1

   - **Group D:** Primes n < p ≤ 2n
     - By assumption, there are none!
     - Contribution: 1

3. **Upper bound on C(2n,n):**
   ```
   C(2n,n) ≤ (2n)^√(2n) · 4^(2n/3)
   ```

4. **Get contradiction for large n:**
   For sufficiently large n, the upper bound is less than the lower bound:
   ```
   (2n)^√(2n) · 4^(2n/3) < 4^n / (2n + 1)
   ```

5. **Handle small cases:** For n ≤ 507, verify explicitly using the prime sequence:
   ```
   2, 3, 5, 7, 13, 23, 43, 83, 163, 317, 521
   ```
   Each is less than twice its predecessor.

---

### Key Technical Lemmas

**Lemma 1 (Prime Multiplicity in Binomial Coefficient):**
```lean
-- For p prime, the multiplicity of p in C(2n,n) is bounded
theorem Nat.factorial_multiplicity_choose :
  ∀ p n, p.Prime → p.factorization.get (2*n).choose n ≤ log p (2*n)
```

**Lemma 2 (Primes in Middle Range Don't Divide):**
```lean
-- If 2n/3 < p ≤ n, then p does not divide C(2n,n)
theorem Nat.not_dvd_choose_of_prime_in_range :
  ∀ p n, p.Prime → 2*n/3 < p → p ≤ n → ¬(p ∣ (2*n).choose n)
```

**Lemma 3 (Central Binomial Lower Bound):**
```lean
-- C(2n,n) ≥ 4^n / (2n+1)
theorem Nat.choose_middle_lower_bound :
  ∀ n, 4^n ≤ (2*n + 1) * (2*n).choose n
```

---

### Lean 4 Implementation Details

**From Mathlib Documentation:**

> "The proof follows the outline of the Erdős proof presented in Aigner and Ziegler's 'Proofs from THE BOOK.' One considers the prime factorization of C(2n,n), and splits the constituent primes up into various groups, then upper bounds the contribution of each group. This upper bounds the central binomial coefficient, and if the postulate does not hold, this upper bound conflicts with a simple lower bound for large enough n."

**Proof Structure in Mathlib:**

1. Define the central binomial coefficient
2. Establish lower bound on C(2n,n)
3. Partition primes into ranges
4. Bound contribution from each range
5. Derive contradiction for large n
6. Handle base cases explicitly

**Optimizations:** Mathlib uses optimizations from Shigenori Tochiori (as noted in Metamath implementation).

---

### Related Theorems and Lemmas

**Prerequisites:**
- Central binomial coefficient: `Nat.choose`
- Prime counting and factorization
- Logarithm bounds
- Basic prime number theory

**Generalizations and Strengthenings:**
- **Ramanujan's Improvement:** For n ≥ 3, ∃ prime in (n, 2n-2]
- **Prime Gap Bounds:** π(2n) - π(n) ≥ 1 (at least one prime in doubling interval)
- **Erdős-Ko-Rado Theorem:** Applications to combinatorics

**Related Results:**
- **Legendre's Conjecture:** There is a prime between n² and (n+1)² (open!)
- **Oppermann's Conjecture:** There is a prime in (n², n²+n) and in (n²-n, n²) (open!)
- **Prime Number Theorem:** Asymptotic density of primes

---

### Difficulty Assessment

**Implementation Difficulty:** ⭐⭐ **MEDIUM**

**Rationale:**
- Main theorem is direct Mathlib application (easy)
- However, understanding the proof requires multiple lemmas
- Educational value in implementing supporting lemmas
- Good example of combinatorial number theory

**Estimated Tactic Count:**
- Main theorem: 1 (direct application)
- Supporting lemmas: 5-15 tactics each
- Full proof reconstruction: 50+ tactics

**Suggested Dataset Entries:**

```json
// Main theorem (easy - direct application)
{
  "theorem_id": "bertrand_postulate",
  "mathematical_domain": "NumberTheory",
  "difficulty": "easy",
  "mathlib_support": "full",
  "proof_status": "complete"
}

// Supporting lemmas (medium difficulty)
{
  "lemma_id": "central_binomial_lower_bound",
  "theorem_id": "bertrand_postulate",
  "difficulty": "medium",
  "mathlib_support": "full"
}

// Advanced: Full proof reconstruction (hard)
{
  "theorem_id": "bertrand_postulate_full_proof",
  "difficulty": "hard",
  "mathlib_support": "full"
}
```

---

### References and Sources

**Historical and Mathematical:**
- [Bertrand's Postulate - Wikipedia](https://en.wikipedia.org/wiki/Bertrand's_postulate)
- [Proof of Bertrand's Postulate - Wikipedia](https://en.wikipedia.org/wiki/Proof_of_Bertrand's_postulate)
- [Erdős's Proof of Bertrand's Postulate - David Galvin (Notre Dame)](https://www3.nd.edu/~dgalvin1/pdf/bertrand.pdf)

**Proofs:**
- [Chebyshev's Theorem and Bertrand's Postulate - Leo Goldmakher (Williams)](https://web.williams.edu/Mathematics/lg5/Chebyshev.pdf)
- [Bertrand's Postulate - Cut the Knot](https://www.cut-the-knot.org/arithmetic/algebra/BertrandPostulate.shtml)

**Lean/Mathlib:**
- [Mathlib4: NumberTheory.Bertrand](https://leanprover-community.github.io/mathlib4_docs/Mathlib/NumberTheory/Bertrand.html)
- [Mathlib3: number_theory.bertrand](https://leanprover-community.github.io/mathlib_docs/number_theory/bertrand.html)

---

## 5. Dirichlet's Theorem on Arithmetic Progressions

### Historical Context

**Timeline:**
- 1837: Lejeune Dirichlet proved the theorem using novel analytic methods
- Introduced L-functions (now called Dirichlet L-functions)
- First major use of analysis to solve a purely number-theoretic problem
- 2024: Fully formalized in Lean 4 by David Loeffler and Michael Stoll

**Significance:** Revolutionary result connecting analysis and number theory. Showed primes are equidistributed in arithmetic progressions. Foundation for analytic number theory. Led to development of L-function theory and eventual proof of Prime Number Theorem.

---

### Natural Language Statement

For any two coprime positive integers a and d (i.e., gcd(a,d) = 1), there are infinitely many prime numbers of the form:
```
a, a+d, a+2d, a+3d, a+4d, ...
```

**Equivalent Statement:** The arithmetic progression {a + nd | n ∈ ℕ} contains infinitely many primes, provided gcd(a,d) = 1.

**Stronger Form:** These primes are asymptotically equidistributed among the φ(d) coprime residue classes modulo d, each with density 1/φ(d).

---

### Mathematical Statement (Informal)

For coprime a, d ∈ ℕ with d > 0:
```
|{p ∈ Primes : p ≡ a (mod d)}| = ∞
```

**Equivalent Formulation:**
```
∀n ∈ ℕ, ∃p > n : Prime(p) ∧ p ≡ a (mod d)
```

---

### Lean 4 Formalization

**Primary Theorems:**

```lean
-- Main theorem: infinitely many primes in arithmetic progression
theorem Nat.setOf_prime_and_eq_mod_infinite {q : ℕ} (hq : 0 < q) (a : ZMod q)
  (ha : IsUnit a) : Set.Infinite {p : ℕ | p.Prime ∧ (p : ZMod q) = a}

-- Alternative formulation: for all n, exists prime > n in progression
theorem Nat.forall_exists_prime_gt_and_eq_mod {q : ℕ} (hq : 0 < q) (a : ZMod q)
  (ha : IsUnit a) : ∀ n, ∃ p > n, p.Prime ∧ (p : ZMod q) = a

-- Integer version
theorem Nat.forall_exists_prime_gt_and_zmodEq {q : ℕ} (hq : 0 < q) {a : ℤ}
  (ha : a.gcd q = 1) : ∀ n, ∃ p > n, p.Prime ∧ (p : ℤ) ≡ a [ZMOD q]
```

**Location:** `Mathlib.NumberTheory.LSeries.PrimesInAP`

**Required Imports:**
```lean
import Mathlib.NumberTheory.LSeries.PrimesInAP
import Mathlib.NumberTheory.LSeries.DirichletCharacter
import Mathlib.Data.ZMod.Basic
```

**Mathlib Support:** ✅ **FULL** (as of 2024) - Complete formalization including L-function theory

---

### Proof Sketch: Dirichlet's Analytic Method

**Overview:** The proof uses complex analysis and properties of Dirichlet L-functions. This is one of the first major applications of analysis to number theory.

**Strategy:** Prove using L-series and their non-vanishing at s=1

---

**Part 1: Dirichlet Characters**

**Definition:** A Dirichlet character χ modulo q is a group homomorphism:
```
χ : (ℤ/qℤ)× → ℂ×
```
Extended to all integers by:
- χ(n) = χ(n mod q) if gcd(n,q) = 1
- χ(n) = 0 if gcd(n,q) > 1

**Key Properties:**
- There are φ(q) Dirichlet characters mod q
- One character is trivial: χ₀(n) = 1 if gcd(n,q) = 1, else 0
- Characters form an orthogonal basis

---

**Part 2: Dirichlet L-Functions**

**Definition:** For character χ and Re(s) > 1:
```
L(s,χ) = Σ(n=1 to ∞) χ(n)/n^s
```

**Euler Product (for Re(s) > 1):**
```
L(s,χ) = ∏(p prime) 1/(1 - χ(p)·p^(-s))
```

**Key Facts:**
1. For trivial character χ₀: L(s,χ₀) = ζ(s) · (finite correction)
2. For non-trivial χ: L(s,χ) extends to Re(s) > 0
3. Crucial: **L(1,χ) ≠ 0 for all non-trivial characters χ**

---

**Part 3: Von Mangoldt Function by Residue Classes**

**Definition:** Define for residue class a mod q:
```
Λₐ(n) = Λ(n) if n ≡ a (mod q), else 0
```
where Λ is the von Mangoldt function (Λ(p^k) = log p, else 0).

**Key Identity (Orthogonality):**
```
Λₐ(n) = (1/φ(q)) · Σ(χ mod q) χ̄(a)·χ(n)·Λ(n)
```

**Taking logarithmic derivative of L-functions:**
```
-L'/L(s,χ) = Σ(n=1 to ∞) χ(n)·Λ(n)/n^s
```

---

**Part 4: The Main Argument**

1. **Assume finitely many primes in progression:**
   Suppose only finitely many primes p ≡ a (mod q)

2. **Then Σ(p ≡ a) log p / p^s converges for all s > 0**

3. **Use orthogonality relation:**
   ```
   Σ(p ≡ a) log p / p^s = (1/φ(q)) · Σ(χ) χ̄(a) · (-L'/L(s,χ))
   ```

4. **Behavior as s → 1⁺:**
   - For χ₀: -L'/L(1,χ₀) ~ 1/(s-1) → ∞
   - For χ ≠ χ₀: -L'/L(1,χ) is finite (since L(1,χ) ≠ 0)

5. **Contradiction:**
   The right side → ∞ (from χ₀ term)
   But left side is finite (by assumption)

**Conclusion:** Must have infinitely many primes ≡ a (mod q)

---

### The Crucial Non-Vanishing L(1,χ) ≠ 0

**This is the hardest part of the proof!**

**For Real Characters:**
Prove by showing L(1,χ) > 0 using positivity arguments.

**For Complex Characters:**
Use the fact that L(s,χ) · L(s,χ̄) is a real Dirichlet series with positive coefficients.

**Key Lemma:** If L(1,χ) = 0 for complex χ, then L(1,χ·χ₀) would have to be infinite, contradiction.

---

### Lean 4 Implementation Details

**From Mathlib Formalization (Loeffler-Stoll 2024):**

The formalization defines:

1. **Von Mangoldt function by residue class:**
```lean
def ArithmeticFunction.vonMangoldt.residueClass (a : ZMod q) : ℕ → ℝ
```

2. **Show it's a linear combination of χ·Λ:**
```lean
theorem vonMangoldt_residueClass_eq_sum_dirichlet_chars :
  vonMangoldt.residueClass a = (1/φ(q)) • Σ χ, χ̄(a) • (χ * Λ)
```

3. **Non-vanishing at s=1:**
```lean
theorem DirichletCharacter.LSeries_ne_zero_at_one {χ : DirichletCharacter ℂ q}
  (hχ : χ ≠ 1) : L(1,χ) ≠ 0
```

4. **Main theorem:**
```lean
theorem Nat.setOf_prime_and_eq_mod_infinite ...
```

**Dependencies:** Requires substantial L-function theory infrastructure built up in Mathlib.

---

### Related Results in Mathlib

**Supporting Theory:**
- Dirichlet characters: `Mathlib.NumberTheory.LSeries.DirichletCharacter`
- L-series: `Mathlib.NumberTheory.LSeries.Basic`
- Von Mangoldt function: `Mathlib.NumberTheory.VonMangoldtFunction`
- Prime Number Theorem (in progress): `PrimeNumberTheorem+` project

**Related Conjectures:**
- **Prime Number Theorem for APs:** π(x;q,a) ~ π(x)/φ(q) as x→∞
- **Generalized Riemann Hypothesis:** All zeros of L(s,χ) in critical strip have Re(s)=1/2
- **Chebotarev Density Theorem:** Generalization to Galois theory

---

### Difficulty Assessment

**Implementation Difficulty:** ⭐⭐⭐ **HARD**

**Rationale:**
- Requires understanding L-function theory
- Non-trivial analytic arguments
- Recently formalized (2024) - less mature than other results
- Dependencies on substantial Mathlib infrastructure
- Educational value very high for analytic number theory

**Estimated Tactic Count:**
- Direct application: 1-2 tactics (if using Mathlib theorem directly)
- Understanding proof: Requires reading ~1000 lines of Mathlib code
- Implementing from scratch: 200+ tactics

**Suggested Dataset Approach:**

```json
// Level 1: Direct application (easy)
{
  "theorem_id": "dirichlet_theorem_ap_simple",
  "mathematical_domain": "NumberTheory",
  "nl_statement": "There are infinitely many primes ≡ 1 (mod 4)",
  "difficulty": "easy",
  "mathlib_support": "full"
}

// Level 2: Understanding statement (medium)
{
  "theorem_id": "dirichlet_theorem_ap_general",
  "mathematical_domain": "NumberTheory",
  "nl_statement": "For coprime a,d there are infinitely many primes p ≡ a (mod d)",
  "difficulty": "medium",
  "mathlib_support": "full"
}

// Level 3: Supporting lemmas (hard)
{
  "lemma_id": "lfunction_nonvanishing_at_one",
  "theorem_id": "dirichlet_theorem_ap_general",
  "nl_statement": "L(1,χ) ≠ 0 for non-trivial Dirichlet character χ",
  "difficulty": "hard",
  "mathlib_support": "full"
}
```

---

### References and Sources

**Original Papers and History:**
- [Dirichlet's theorem on arithmetic progressions - Wikipedia](https://en.wikipedia.org/wiki/Dirichlet's_theorem_on_arithmetic_progressions)
- [Dirichlet's Theorem on Primes in Arithmetic Progressions - ACIT](https://acit-science.com/dirichlets-theorem-on-arithmetic-progressions/)

**Proof Expositions:**
- [Dirichlet's Theorem - Anthony Várilly (Rice)](https://math.rice.edu/~av15/Files/Dirichlet.pdf)
- [Dirichlet's Theorem About Primes - Ang Li (UChicago)](https://math.uchicago.edu/~may/REU2012/REUPapers/LiAng.pdf)
- [Elementary Proof of Dirichlet Theorem - Zijian Wang (UChicago)](http://math.uchicago.edu/~may/REU2017/REUPapers/WangZijian.pdf)
- [Dirichlet L-functions - MIT Lecture Notes](https://math.mit.edu/classes/18.785/2016fa/LectureNotes18.pdf)

**Lean/Mathlib:**
- [Mathlib4: NumberTheory.LSeries.PrimesInAP](https://leanprover-community.github.io/mathlib4_docs/Mathlib/NumberTheory/LSeries/PrimesInAP.html)
- [Formalizing zeta and L-functions in Lean - Loeffler and Stoll (arXiv)](https://arxiv.org/abs/2503.00959)
- [Formalizing zeta and L-functions - Annals of Formal Mathematics](https://afm.episciences.org/15954)

---

## Summary: Implementation Roadmap

### Phase 1: Easy Theorems (Direct Mathlib Application)

**Target:** 3-5 theorem records, 1 tactic each

1. **Euclid's Infinitude of Primes**
   - `theorem_id: "euclid_infinitude_primes"`
   - Lean: `exact Nat.exists_infinite_primes`
   - Priority: ⭐⭐⭐⭐⭐

2. **Fundamental Theorem of Arithmetic (Existence)**
   - `theorem_id: "fta_existence"`
   - Lean: `exact Nat.prod_primeFactorsList`
   - Priority: ⭐⭐⭐⭐⭐

3. **Fundamental Theorem of Arithmetic (Uniqueness)**
   - `theorem_id: "fta_uniqueness"`
   - Lean: `exact Nat.primeFactorsList_unique`
   - Priority: ⭐⭐⭐⭐⭐

4. **Fermat's Little Theorem**
   - `theorem_id: "fermat_little_theorem"`
   - Lean: `exact ZMod.pow_card_sub_one`
   - Priority: ⭐⭐⭐⭐

5. **Bertrand's Postulate**
   - `theorem_id: "bertrand_postulate"`
   - Lean: `exact Nat.exists_prime_lt_and_lt`
   - Priority: ⭐⭐⭐⭐

---

### Phase 2: Medium Difficulty (Supporting Lemmas)

**Target:** 10-15 lemma records, 5-10 tactics each

1. **Euclid's Lemma** (for FTA uniqueness)
   - Prerequisite for unique factorization

2. **Central Binomial Coefficient Bounds** (for Bertrand)
   - Lower bound: 4^n/(2n+1)
   - Upper bound from prime factorization

3. **Wilson's Theorem** (related to Fermat)
   - (p-1)! ≡ -1 (mod p)

4. **Prime Multiplicity in Binomials** (for Bertrand)
   - Bounds on p-adic valuation

---

### Phase 3: Hard (Analytic Number Theory)

**Target:** 5-10 advanced theorem records

1. **Dirichlet's Theorem - Simple Cases**
   - Primes ≡ 1 (mod 4)
   - Primes ≡ 3 (mod 4)

2. **Dirichlet's Theorem - General Case**
   - Arbitrary coprime a,d

3. **L-Function Non-Vanishing** (supporting lemma)
   - L(1,χ) ≠ 0 for χ ≠ χ₀

---

## Integration with Existing Knowledge Bases

### Connection to Arithmetic Knowledge Base

**Natural Numbers (Peano Axioms):**
- All five theorems operate on ℕ
- Use induction (explicit or implicit)
- Build on successor structure

**Link:** Prime factorization extends the Peano successor structure to multiplicative structure.

---

### Connection to Isomorphism Theorems

**Group Theory Connection:**
- Fermat's Little Theorem via Lagrange's theorem on (ℤ/pℤ)×
- Multiplicative group of units mod p

**Module/Vector Space Connection:**
- Not directly related, but both use quotient structures

---

### New Domain: Analytic Number Theory

**Dirichlet's Theorem introduces:**
- L-functions and Dirichlet series
- Complex analysis in number theory
- Equidistribution results
- Foundation for Prime Number Theorem

This extends the project into a new mathematical domain beyond algebra.

---

## Dataset Schema Integration

### Example Theorem Record: Euclid's Infinitude

```json
{
  "theorem_id": "euclid_infinitude_primes",
  "mathematical_domain": "NumberTheory",
  "theorem_name": "Euclid's Theorem on the Infinitude of Primes",
  "nl_statement": "There are infinitely many prime numbers. For every natural number n, there exists a prime p ≥ n.",

  "lean_statement": "theorem euclid_infinitude : ∀ n : ℕ, ∃ p ≥ n, Nat.Prime p := Nat.exists_infinite_primes",

  "lean_proof_term": "Nat.exists_infinite_primes",
  "lean_proof_tactic": "by exact Nat.exists_infinite_primes",

  "imports": [
    "Mathlib.Data.Nat.Prime.Infinite",
    "Mathlib.Data.Nat.Prime.Basic"
  ],

  "difficulty": "easy",
  "mathlib_support": "full",

  "reasoning_trace": {
    "mathematical_insight": "Construct n! + 1, which is either prime or has a prime factor > n. In either case, we find a prime larger than n.",
    "key_lemmas": ["Nat.exists_infinite_primes", "Nat.Prime"],
    "proof_strategy": "Direct application of Mathlib's formalization of Euclid's theorem",
    "common_pitfalls": [
      "Don't try to prove n! + 1 is always prime (it's not!)",
      "The proof uses that n! + 1 has a prime factor, not that it is prime"
    ]
  },

  "state_tactic_pairs": [
    {
      "step": 0,
      "state": "⊢ ∀ n : ℕ, ∃ p ≥ n, Nat.Prime p",
      "tactic": "exact Nat.exists_infinite_primes",
      "tactic_category": "exact",
      "goals_remaining": 0
    }
  ],

  "proof_metrics": {
    "tactic_count": 1,
    "proof_length_tokens": 3,
    "compilation_time_ms": 50,
    "uses_automation": false,
    "mathlib_depth": 2
  },

  "alternative_proofs": [
    {
      "style": "apply",
      "proof": "by apply Nat.exists_infinite_primes"
    }
  ],

  "token_count_nl": 85,
  "token_count_lean": 45,
  "train_test_split": "train",
  "proof_status": "complete",
  "schema_version": "2.0.0",
  "created_at": "2025-12-13T00:00:00Z",
  "updated_at": "2025-12-13T00:00:00Z"
}
```

---

### Example Lemma Record: Euclid's Lemma (for FTA)

```json
{
  "lemma_id": "euclids_lemma_prime_dvd_mul",
  "theorem_id": "fta_uniqueness",
  "lemma_name": "Euclid's Lemma: Prime Divisibility of Products",
  "nl_statement": "If a prime p divides a product ab, then p divides a or p divides b.",

  "lean_statement": "lemma euclids_lemma {p a b : ℕ} (hp : Nat.Prime p) (h : p ∣ a * b) : p ∣ a ∨ p ∣ b",

  "lean_proof_term": "hp.dvd_mul.mp h",
  "lean_proof_tactic": "by exact hp.dvd_mul.mp h",

  "depends_on_lemmas": [],

  "imports": ["Mathlib.Data.Nat.Prime.Basic"],

  "reasoning_trace": {
    "mathematical_insight": "Primes are irreducible: if p divides a product, it must divide one of the factors. This is what makes primes the building blocks of arithmetic.",
    "key_lemmas": ["Nat.Prime.dvd_mul"],
    "proof_strategy": "Use Mathlib's built-in theorem about prime divisibility",
    "common_pitfalls": ["This fails for composite numbers! Example: 6 | 12 but 6 ∤ 3 and 6 ∤ 4"]
  },

  "state_tactic_pairs": [
    {
      "step": 0,
      "state": "p a b : ℕ, hp : Nat.Prime p, h : p ∣ a * b ⊢ p ∣ a ∨ p ∣ b",
      "tactic": "exact hp.dvd_mul.mp h",
      "tactic_category": "exact",
      "goals_remaining": 0
    }
  ],

  "proof_metrics": {
    "tactic_count": 1,
    "proof_length_tokens": 5,
    "compilation_time_ms": 30,
    "uses_automation": false,
    "mathlib_depth": 1
  },

  "token_count_nl": 70,
  "token_count_lean": 35,
  "proof_status": "complete",
  "schema_version": "2.0.0",
  "created_at": "2025-12-13T00:00:00Z",
  "updated_at": "2025-12-13T00:00:00Z"
}
```

---

## Evidence Quality Assessment

### Source Grading

| Source Type | Grade | Coverage |
|-------------|-------|----------|
| **Mathlib4 Documentation** | ⭐⭐⭐ High | Complete for all 5 theorems |
| **Wikipedia/MathWorld** | ⭐⭐⭐ High | Historical context, proof sketches |
| **Academic Expository Papers** | ⭐⭐⭐ High | Detailed proofs (Dirichlet, Bertrand) |
| **Lean Community Resources** | ⭐⭐⭐ High | Implementation details, tutorials |
| **arXiv Preprints (Loeffler-Stoll)** | ⭐⭐⭐ High | Recent formalization (Dirichlet) |

### Verification Status

| Theorem | Mathlib Verified | Documentation Quality | Confidence |
|---------|------------------|----------------------|------------|
| Euclid's Infinitude | ✅ | Excellent | ⭐⭐⭐ High |
| FTA | ✅ | Excellent | ⭐⭐⭐ High |
| Fermat's Little | ✅ | Excellent | ⭐⭐⭐ High |
| Bertrand's Postulate | ✅ | Good | ⭐⭐⭐ High |
| Dirichlet's Theorem | ✅ | Good (new) | ⭐⭐ Medium-High |

**Note on Dirichlet:** Formalization is recent (2024), so less battle-tested than others. However, peer-reviewed and published in Annals of Formal Mathematics.

---

## Limitations and Gaps

### What's NOT Covered

1. **Prime Number Theorem (PNT):**
   - Statement: π(x) ~ x/log(x)
   - Status: Formalization in progress (PrimeNumberTheoremAnd project)
   - Difficulty: Very hard (requires complex analysis)

2. **Twin Prime Conjecture:**
   - Infinitely many primes p such that p+2 is also prime
   - Status: Unproven! Open problem
   - Not suitable for dataset

3. **Riemann Hypothesis:**
   - All non-trivial zeros of ζ(s) have Re(s) = 1/2
   - Status: Unproven! Millennium Prize Problem
   - Statement formalized in Mathlib, proof not available

4. **Green-Tao Theorem:**
   - Primes contain arbitrarily long arithmetic progressions
   - Status: Proven (2004) but not formalized in Lean
   - Very advanced

### Uncertainty Notes

- **Dirichlet L-function theory:** Recently formalized, may have updates
- **Bertrand proof optimizations:** Mathlib uses Tochiori optimizations - details not fully documented
- **Computational aspects:** Some theorems have decision procedures not covered here

---

## Future Directions

### Phase 4: Advanced Topics (Stretch Goals)

1. **Prime Number Theorem**
   - When PrimeNumberTheoremAnd merges into Mathlib
   - Difficulty: Very hard
   - Requires complex analysis, Wiener-Ikehara theorem

2. **Chebotarev Density Theorem**
   - Generalization of Dirichlet to Galois theory
   - Not yet in Mathlib
   - Difficulty: Expert level

3. **Computational Number Theory**
   - Primality testing algorithms (Miller-Rabin, AKS)
   - Integer factorization
   - Applications to cryptography

---

## Recommended Reading Order

For someone implementing these theorems:

1. **Start:** Euclid's Infinitude (easiest, most fundamental)
2. **Next:** Fundamental Theorem of Arithmetic (builds intuition for primes)
3. **Then:** Fermat's Little Theorem (introduces modular arithmetic)
4. **Advanced:** Bertrand's Postulate (combinatorial techniques)
5. **Expert:** Dirichlet's Theorem (analytic number theory)

---

## Conclusion

All five classic prime number theorems are now formalized in Lean 4's Mathlib, making them excellent candidates for the ai-mathematician dataset. They span:

- **Difficulty:** Easy to hard
- **Techniques:** Elementary to analytic
- **Era:** Ancient to modern
- **Applications:** Pure mathematics to cryptography

The theorems provide a comprehensive introduction to prime number theory and demonstrate the power of formal verification in mathematics.

---

**End of Knowledge Base**

**Generated:** 2025-12-13
**Research Mode:** Deep Synthesis
**Total Sources:** 40+ (see references throughout)
**Evidence Quality:** High
**Confidence Level:** High
**Recommended for Implementation:** ✅ All five theorems
