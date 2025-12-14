# Prime Number Theorems Knowledge Base for Lean 4

**Generated:** 2025-12-13
**Purpose:** Research knowledge base for implementing classic prime number theorems in Lean 4 for dataset generation pairing formal proofs with natural language explanations.

---

## Overview

This knowledge base catalogs fundamental theorems in number theory, organized into two major areas:

1. **Prime Number Theory** (Sections 1-11): Classic results about primes, from ancient (Euclid, 300 BC) to modern (Prime Number Theorem, 1896)
2. **Transcendence Theory** (Sections 12-16): Results about transcendental numbers, from Liouville (1844) to Lindemann-Weierstrass (1885)

### Theorem Summary: Prime Numbers

| Theorem | Era | Mathlib Status | Difficulty |
|---------|-----|----------------|------------|
| **Euclid's Infinitude of Primes** | ~300 BC | FULL | Easy |
| **Fundamental Theorem of Arithmetic** | Medieval-1801 | FULL | Easy |
| **Fermat's Little Theorem** | 1640 | FULL | Easy |
| **Wilson's Theorem** | 1770 | FULL | Easy |
| **Euler's Theorem** | 1763 | FULL | Easy |
| **Bertrand's Postulate** | 1850 | FULL | Medium |
| **Quadratic Reciprocity** | 1801 | FULL | Medium |
| **Sum of Two Squares** | 1640s | FULL | Medium |
| **Prime Reciprocal Divergence** | 1737 | FULL | Medium |
| **Dirichlet's Theorem** | 1837 | FULL (2024) | Hard |
| **Prime Number Theorem** | 1896 | FULL (2024) | Hard |

### Theorem Summary: Transcendence Theory

| Theorem | Era | Freek # | Mathlib Status | Difficulty |
|---------|-----|---------|----------------|------------|
| **Transcendence of π** | 1882 | #53 | NOT FORMALIZED | Hard |
| **Transcendence of e** | 1873 | - | NOT FORMALIZED | Medium-Hard |
| **Lindemann-Weierstrass Theorem** | 1885 | #56 | NOT FORMALIZED | Very Hard |
| **Gelfond-Schneider Theorem** | 1934 | - | NOT FORMALIZED | Very Hard |
| **Liouville's Theorem** | 1844 | - | PARTIAL | Medium |

---

## 1. Euclid's Theorem on the Infinitude of Primes

### Natural Language Statement

There are infinitely many prime numbers. For every natural number n, there exists a prime number p such that p >= n.

### Mathematical Statement

```
∀n ∈ N, ∃p >= n : Prime(p)
```

### Proof Sketch (Euclid's Original)

1. Suppose p1, p2, ..., pk are all the primes
2. Construct N = (p1 * p2 * ... * pk) + 1
3. N is either prime (not in list) or has a prime factor q
4. If q = pi for some i, then q divides N and p1*...*pk, so q divides 1 (contradiction)
5. Therefore q is a new prime not in the list

### Lean 4 Formalization

**Primary Theorem:** `Nat.exists_infinite_primes`

```lean
theorem Nat.exists_infinite_primes : ∀ n : N, ∃ p >= n, Nat.Prime p
```

**Alternative Forms:**
```lean
theorem Nat.not_bdd_above_set_of_prime : ¬BddAbove {p : N | p.Prime}
theorem Nat.infinite_set_of_prime : Set.Infinite {p : N | p.Prime}
```

**Import:** `Mathlib.Data.Nat.Prime.Infinite`

**Difficulty:** easy

---

## 2. Fundamental Theorem of Arithmetic

### Natural Language Statement

Every integer greater than 1 is either prime or can be uniquely represented as a product of prime numbers (up to order of factors).

**Two Parts:**
1. **Existence:** Every n > 1 can be written as a product of primes
2. **Uniqueness:** This factorization is unique (up to reordering)

### Mathematical Statement

For every n in N with n > 1, there exists a unique (up to permutation) sequence of primes p1, p2, ..., pk such that:
```
n = p1 * p2 * ... * pk
```

### Proof Sketch

**Existence:** Strong induction on n. If n is prime, done. If composite, n = ab with 1 < a, b < n, apply induction.

**Uniqueness:** Uses Euclid's Lemma: if prime p divides ab, then p divides a or p divides b.

### Lean 4 Formalization

**Primary Functions:**
```lean
-- List of prime factors in nondecreasing order
Nat.primeFactorsList : N -> List N

-- Factorization as multiplicity function
Nat.factorization : N -> N -> N
```

**Key Theorems:**
```lean
theorem Nat.prime_of_mem_primeFactorsList :
  ∀ {n p}, p ∈ n.primeFactorsList -> p.Prime

theorem Nat.prod_primeFactorsList :
  ∀ {n}, 0 < n -> n.primeFactorsList.prod = n

theorem Nat.primeFactorsList_unique :
  ∀ {n l}, (∀ p ∈ l, Nat.Prime p) -> l.prod = n ->
  l ~~ n.primeFactorsList  -- permutation
```

**Import:** `Mathlib.Data.Nat.Factors`

**Difficulty:** easy

---

## 3. Fermat's Little Theorem

### Natural Language Statement

If p is a prime number and a is any integer not divisible by p, then:
```
a^(p-1) ≡ 1 (mod p)
```

**Alternative Form:** For any integer a and prime p:
```
a^p ≡ a (mod p)
```

### Mathematical Statement

For all primes p and integers a with gcd(a,p) = 1:
```
a^(p-1) ≡ 1 (mod p)
```

### Proof Sketch

**Group Theory Approach:**
1. The nonzero elements mod p form a group (Z/pZ)* under multiplication
2. This group has order p-1
3. By Lagrange's theorem, a^(p-1) = 1

**Elementary Approach:**
Consider {1, 2, ..., p-1} and {a*1, a*2, ..., a*(p-1)} mod p. These are permutations, so their products are equal. Cancel (p-1)! to get a^(p-1) ≡ 1.

### Lean 4 Formalization

**Primary Theorem:**
```lean
theorem ZMod.pow_card_sub_one {p : N} [Fact p.Prime] (a : ZMod p) (ha : a ≠ 0) :
  a ^ (p - 1) = 1
```

**General Finite Field Version:**
```lean
theorem FiniteField.pow_card {F : Type*} [Field F] [Fintype F] (a : F) :
  a ^ Fintype.card F = a
```

**Import:** `Mathlib.FieldTheory.Finite.Basic`

**Difficulty:** easy

### Applications

- **RSA Cryptography:** Decryption correctness relies on Fermat's Little Theorem
- **Primality Testing:** Fermat test, Miller-Rabin test
- **Efficient Modular Exponentiation**

---

## 4. Wilson's Theorem

### Natural Language Statement

A natural number n > 1 is prime if and only if (n-1)! ≡ -1 (mod n).

### Mathematical Statement

```
p is prime  <=>  (p-1)! ≡ -1 (mod p)
```

### Proof Sketch

**Forward direction (p prime):**
1. Consider the product 1 * 2 * ... * (p-1) mod p
2. Each element a in {1, ..., p-1} has a unique multiplicative inverse a^(-1) mod p
3. Most elements pair with a different inverse, canceling out
4. Only 1 and p-1 are self-inverse (since x^2 ≡ 1 mod p implies x ≡ ±1)
5. Therefore (p-1)! ≡ 1 * (p-1) ≡ -1 (mod p)

**Backward direction:** If n is composite, then (n-1)! ≡ 0 (mod n) for n > 4.

### Lean 4 Formalization

**Primary Theorem:**
```lean
theorem Nat.Prime.wilsons_lemma {p : N} (hp : p.Prime) :
  (p - 1)! ≡ -1 [MOD p]
```

**Converse:**
```lean
theorem Nat.Prime.of_factorial_eq_neg_one {n : N} (h : (n - 1)! ≡ -1 [MOD n]) (hn : 1 < n) :
  n.Prime
```

**Import:** `Mathlib.NumberTheory.Wilson`

**Difficulty:** easy

---

## 5. Euler's Theorem (Generalization of Fermat)

### Natural Language Statement

If a and n are coprime positive integers, then a raised to the power of Euler's totient function phi(n) is congruent to 1 modulo n.

### Mathematical Statement

```
gcd(a, n) = 1  =>  a^phi(n) ≡ 1 (mod n)
```

where phi(n) = |{k : 1 <= k <= n, gcd(k,n) = 1}| is Euler's totient function.

### Proof Sketch

1. The set of integers coprime to n forms a group (Z/nZ)* under multiplication
2. This group has order phi(n)
3. By Lagrange's theorem, a^phi(n) = 1 for any element a

**Special case:** When n = p is prime, phi(p) = p-1, recovering Fermat's Little Theorem.

### Lean 4 Formalization

**Primary Theorem:**
```lean
theorem ZMod.pow_totient {n : N} [NeZero n] (a : ZMod n) (ha : IsUnit a) :
  a ^ Nat.totient n = 1
```

**Alternative Form:**
```lean
theorem Nat.ModEq.pow_totient {a n : N} (h : a.Coprime n) :
  a ^ Nat.totient n ≡ 1 [MOD n]
```

**Import:** `Mathlib.Data.ZMod.Basic`, `Mathlib.Data.Nat.Totient`

**Difficulty:** easy

### Applications

- **RSA Cryptography:** Uses Euler's theorem for decryption
- **Carmichael Function:** Further refinement of the exponent
- **Order of Elements:** phi(n) is an upper bound on element order

---

## 6. Quadratic Reciprocity

### Natural Language Statement

For distinct odd primes p and q, the Legendre symbols (p/q) and (q/p) are related by:
```
(p/q)(q/p) = (-1)^((p-1)/2 * (q-1)/2)
```

This determines whether p is a quadratic residue mod q based on whether q is a quadratic residue mod p.

### Mathematical Statement

For odd primes p != q:
```
(p/q)(q/p) = (-1)^((p-1)(q-1)/4)
```

**Explicit form:**
- If p ≡ 1 (mod 4) or q ≡ 1 (mod 4): (p/q) = (q/p)
- If p ≡ q ≡ 3 (mod 4): (p/q) = -(q/p)

### Supplementary Laws

**First Supplement (-1):**
```
(-1/p) = (-1)^((p-1)/2) = { 1 if p ≡ 1 (mod 4), -1 if p ≡ 3 (mod 4) }
```

**Second Supplement (2):**
```
(2/p) = (-1)^((p^2-1)/8) = { 1 if p ≡ ±1 (mod 8), -1 if p ≡ ±3 (mod 8) }
```

### Lean 4 Formalization

**Primary Theorem:**
```lean
theorem legendreSym.quadratic_reciprocity {p q : N} [Fact p.Prime] [Fact q.Prime]
  (hp : p ≠ 2) (hq : q ≠ 2) (hpq : p ≠ q) :
  legendreSym p q * legendreSym q p = (-1) ^ ((p - 1) / 2 * ((q - 1) / 2))
```

**Jacobi Symbol Version:**
```lean
theorem jacobiSym.quadratic_reciprocity {a b : N} (ha : Odd a) (hb : Odd b) (hab : a.Coprime b) :
  jacobiSym a b * jacobiSym b a = (-1) ^ ((a - 1) / 2 * ((b - 1) / 2))
```

**Import:** `Mathlib.NumberTheory.LegendreSymbol.QuadraticReciprocity`

**Difficulty:** medium

### Historical Note

Gauss called this his "golden theorem" and gave at least 8 different proofs. It was first stated by Euler (1783) and Legendre (1785), but first proved by Gauss (1801).

---

## 7. Sum of Two Squares Theorem

### Natural Language Statement

An odd prime p can be expressed as a sum of two squares if and only if p ≡ 1 (mod 4). The prime 2 can also be expressed as 2 = 1^2 + 1^2.

### Mathematical Statement

```
p prime  =>  (p = x^2 + y^2 for some x,y in Z)  <=>  (p = 2 or p ≡ 1 (mod 4))
```

### Proof Sketch (Fermat's descent)

1. By quadratic reciprocity, -1 is a quadratic residue mod p iff p ≡ 1 (mod 4)
2. So there exists a with a^2 ≡ -1 (mod p), meaning p | (a^2 + 1)
3. Consider the lattice L = {(x,y) : y ≡ ax (mod p)}
4. By Minkowski's theorem, L contains a short nonzero vector
5. Apply descent to reduce to the representation p = x^2 + y^2

### Lean 4 Formalization

**Primary Theorem:**
```lean
theorem Nat.Prime.sq_add_sq {p : N} (hp : p.Prime) :
  (∃ a b : N, a ^ 2 + b ^ 2 = p) <-> p = 2 ∨ p % 4 = 1
```

**Import:** `Mathlib.NumberTheory.SumTwoSquares`

**Difficulty:** medium

### Related Results

- **Fermat's theorem on sums of two squares** (general characterization)
- **Jacobi's two-square theorem** (counting representations)
- **Lagrange's four-square theorem** (every positive integer is sum of 4 squares)

---

## 8. Divergence of Prime Reciprocal Series

### Natural Language Statement

The sum of the reciprocals of all prime numbers diverges to infinity:
```
sum(1/p for p prime) = infinity
```

### Mathematical Statement

```
lim(N -> infinity) sum(1/p : p prime, p <= N) = infinity
```

Equivalently, the series sum(1/p) over primes p is not summable.

### Proof Sketch (Euler, 1737)

1. Consider log(sum(1/n)) ~ log(log N) by comparison with harmonic series
2. Use Euler product: sum(1/n) = prod(1/(1 - 1/p)) over primes p
3. Taking logs: log(sum(1/n)) = sum(-log(1 - 1/p)) ~ sum(1/p)
4. Therefore sum(1/p) ~ log(log N) -> infinity

### Lean 4 Formalization

**Primary Theorem:**
```lean
theorem tendsto_sum_one_div_prime_atTop :
  Tendsto (fun n => sum(1/p : p prime, p <= n)) atTop atTop
```

**Not Summable Form:**
```lean
theorem not_summable_one_div_on_primes :
  ¬Summable (fun p : {p : N // p.Prime} => (1 : R) / p)
```

**Import:** `Mathlib.NumberTheory.SumPrimeReciprocals`

**Difficulty:** medium

### Significance

This is a stronger result than Euclid's theorem on infinitude of primes. It shows primes are "dense enough" that their reciprocals don't converge.

---

## 9. Bertrand's Postulate (Chebyshev's Theorem)

### Natural Language Statement

For any integer n > 1, there exists at least one prime number p such that n < p < 2n.

### Mathematical Statement

```
∀n ∈ N, n > 1 -> ∃p : Prime(p) ∧ n < p < 2n
```

### Proof Sketch (Erdos 1932)

Analyzes the prime factorization of the central binomial coefficient C(2n,n):

1. **Lower bound:** C(2n,n) >= 4^n / (2n+1)

2. **Upper bound (assuming no prime in (n,2n]):**
   - Primes <= sqrt(2n): contribute at most (2n)^sqrt(2n)
   - Primes in (sqrt(2n), 2n/3]: contribute at most 4^(2n/3)
   - Primes in (2n/3, n]: don't divide C(2n,n)!
   - Primes in (n, 2n]: by assumption, none

3. **Contradiction:** For large n, upper bound < lower bound

4. **Small cases:** Verify explicitly using prime sequence 2, 3, 5, 7, 13, 23, 43, 83, 163, 317, 521

### Lean 4 Formalization

**Primary Theorem:**
```lean
theorem Nat.exists_prime_lt_and_lt {n : N} (hn : 1 < n) :
  ∃ p, Nat.Prime p ∧ n < p ∧ p < 2 * n
```

**Import:** `Mathlib.NumberTheory.Bertrand`

**Difficulty:** medium (main theorem easy, supporting lemmas medium)

---

## 10. Dirichlet's Theorem on Arithmetic Progressions

### Natural Language Statement

For any two coprime positive integers a and d (gcd(a,d) = 1), there are infinitely many primes of the form:
```
a, a+d, a+2d, a+3d, ...
```

### Mathematical Statement

For coprime a, d in N with d > 0:
```
|{p ∈ Primes : p ≡ a (mod d)}| = infinity
```

### Proof Sketch (Dirichlet's Analytic Method)

Uses L-functions and their non-vanishing at s=1:

1. **Define Dirichlet characters** chi: (Z/qZ)* -> C*

2. **Define L-functions:** L(s, chi) = sum(n=1 to infinity) chi(n)/n^s

3. **Key fact:** L(1, chi) != 0 for non-trivial characters

4. **Use orthogonality** to isolate primes in progression a mod q

5. **Show divergence** of sum over primes p ≡ a (mod q) implies infinitely many

### Lean 4 Formalization

**Primary Theorem:**
```lean
theorem Nat.setOf_prime_and_eq_mod_infinite {q : N} (hq : 0 < q) (a : ZMod q)
  (ha : IsUnit a) : Set.Infinite {p : N | p.Prime ∧ (p : ZMod q) = a}
```

**Alternative Form:**
```lean
theorem Nat.forall_exists_prime_gt_and_eq_mod {q : N} (hq : 0 < q) (a : ZMod q)
  (ha : IsUnit a) : ∀ n, ∃ p > n, p.Prime ∧ (p : ZMod q) = a
```

**Import:** `Mathlib.NumberTheory.LSeries.PrimesInAP`

**Difficulty:** hard (requires understanding L-function theory)

**Note:** Recently formalized (2024) by David Loeffler and Michael Stoll.

---

## 11. Prime Number Theorem

### Natural Language Statement

The prime counting function pi(x), which counts the number of primes less than or equal to x, is asymptotically equivalent to x/log(x) as x approaches infinity.

### Mathematical Statement

```
pi(x) ~ x / log(x)  as x -> infinity
```

More precisely:
```
lim(x -> infinity) pi(x) / (x / log(x)) = 1
```

**Stronger form with error term:**
```
pi(x) = Li(x) + O(x * exp(-c * sqrt(log x)))
```
where Li(x) is the logarithmic integral.

### Historical Context

- **1896:** Independently proved by Jacques Hadamard and Charles Jean de la Vallée Poussin
- Uses properties of the Riemann zeta function (zeros)
- **1949:** Elementary proofs by Selberg and Erdos (avoiding complex analysis)
- **2024:** Formalized in Lean 4 by Kontorovich, Tao, et al.

### Proof Sketch

The analytic proof uses:
1. Connection between pi(x) and the Riemann zeta function zeta(s)
2. The key fact that zeta(s) has no zeros on the line Re(s) = 1
3. Contour integration and Tauberian theorems

### Lean 4 Formalization

**Primary Theorem:**
```lean
theorem PrimeNumberTheorem :
  Tendsto (fun x => primeCountingFun x / (x / log x)) atTop (nhds 1)
```

**With Error Term:**
```lean
theorem PrimeNumberTheorem.withErrorTerm :
  ∃ c > 0, primeCountingFun x = Li x + O(x * exp (-c * sqrt (log x)))
```

**Import:** `Mathlib.NumberTheory.PrimeNumberTheorem` (from PrimeNumberTheoremAnd project)

**Difficulty:** hard

### Related Results

- **Chebyshev functions:** psi(x) and theta(x)
- **Mertens' theorems:** Asymptotic behavior of prime products
- **Riemann Hypothesis:** Would give optimal error term O(sqrt(x) log(x))
- **Prime Number Theorem for APs:** pi(x; q, a) ~ pi(x) / phi(q)

---

## 12. Transcendence of π (Freek #53)

### Natural Language Statement

The number π (pi) is transcendental, meaning it is not the root of any non-zero polynomial equation with rational (or equivalently, integer) coefficients.

### Mathematical Statement

```
¬∃p ∈ ℤ[X], p ≠ 0 ∧ p(π) = 0
```

Equivalently: π is not algebraic over ℚ.

### Proof Sketch (Lindemann 1882)

The proof uses the Lindemann-Weierstrass theorem (see below):

1. **Assume** π is algebraic
2. **Then** iπ is algebraic (since i is algebraic)
3. **By Lindemann-Weierstrass:** If α is nonzero algebraic, then e^α is transcendental
4. **But** e^(iπ) = -1 is algebraic (it's rational!)
5. **Contradiction:** Therefore π must be transcendental

### Historical Significance

- **1761:** Lambert proved π is irrational
- **1882:** Lindemann proved π is transcendental
- **Consequence:** Squaring the circle is impossible (ancient Greek problem)
- This was the first proof that a "naturally occurring" constant is transcendental

### Lean 4 Formalization

**Status:** NOT FORMALIZED in Mathlib (as of 2024)

**Expected Lean Template:**
```lean
-- Requires: Lindemann-Weierstrass theorem
theorem pi_transcendental : Transcendental ℚ Real.pi := by
  -- Uses: e^(i*π) = -1 is algebraic, but Lindemann-Weierstrass says e^α
  -- is transcendental for nonzero algebraic α, contradiction
  sorry
```

**Import:** Would require `Mathlib.Analysis.SpecialFunctions.Pow.Real`, `Mathlib.RingTheory.Algebraic.Basic`

**Difficulty:** hard (requires Lindemann-Weierstrass theorem, which is also not formalized)

### Related Results

- **Transcendence of e:** Easier, proved by Hermite 1873
- **Lindemann-Weierstrass Theorem:** The general result
- **Gelfond-Schneider Theorem:** α^β is transcendental for algebraic α ≠ 0,1 and irrational algebraic β

---

## 13. Transcendence of e (Hermite 1873)

### Natural Language Statement

The number e (Euler's number, base of natural logarithm) is transcendental.

### Mathematical Statement

```
¬∃p ∈ ℤ[X], p ≠ 0 ∧ p(e) = 0
```

### Proof Sketch (Hermite's Method)

1. **Assume** e is algebraic of degree n, satisfying a₀ + a₁e + ... + aₙeⁿ = 0
2. **Construct** special polynomials with large integer coefficients
3. **Use integration by parts** to create contradiction via:
   - An integer that should be divisible by a large prime power
   - But is also bounded by a small constant
4. **Contradiction** establishes transcendence

### Lean 4 Formalization

**Status:** NOT FORMALIZED in Mathlib (as of 2024)

**Expected Lean Template:**
```lean
theorem exp_one_transcendental : Transcendental ℚ (Real.exp 1) := by
  -- Hermite's proof: construct auxiliary polynomials
  -- show integer with contradictory divisibility properties
  sorry
```

**Difficulty:** medium-hard (simpler than π, but still requires careful analysis)

---

## 14. Lindemann-Weierstrass Theorem (Freek #56)

### Natural Language Statement

If α₁, α₂, ..., αₙ are distinct algebraic numbers, then e^α₁, e^α₂, ..., e^αₙ are linearly independent over the algebraic numbers.

**Important Special Case:** If α is a nonzero algebraic number, then e^α is transcendental.

### Mathematical Statement

For distinct algebraic numbers α₁, ..., αₙ and nonzero algebraic numbers β₁, ..., βₙ:
```
β₁·e^α₁ + β₂·e^α₂ + ... + βₙ·e^αₙ ≠ 0
```

### Proof Sketch

1. **Assume** a nontrivial algebraic relation exists
2. **Construct** a determinant using derivatives of auxiliary functions
3. **Show** this determinant is:
   - A nonzero integer (by algebraic properties)
   - Arbitrarily small (by analytic estimates)
4. **Contradiction**

### Lean 4 Formalization

**Status:** NOT FORMALIZED in Mathlib (as of 2024)

**Expected Lean Template:**
```lean
theorem lindemann_weierstrass
    {n : ℕ} {α : Fin n → ℂ} {β : Fin n → ℂ}
    (hα_distinct : Function.Injective α)
    (hα_alg : ∀ i, IsAlgebraic ℚ (α i))
    (hβ_alg : ∀ i, IsAlgebraic ℚ (β i))
    (hβ_ne : ∃ i, β i ≠ 0) :
    ∑ i, β i * Complex.exp (α i) ≠ 0 := by
  sorry
```

**Difficulty:** very hard (one of the hardest unformalized theorems)

### Consequences

| Corollary | Statement |
|-----------|-----------|
| e transcendental | Take α₁ = 0, α₂ = 1 |
| π transcendental | Take α₁ = 0, α₂ = iπ, use e^(iπ) = -1 |
| e^α transcendental | For nonzero algebraic α |
| ln(α) transcendental | For algebraic α ≠ 0, 1 |

---

## 15. Gelfond-Schneider Theorem

### Natural Language Statement

If α and β are algebraic numbers with α ≠ 0, 1 and β irrational, then α^β is transcendental.

### Mathematical Statement

```
α ∈ Algebraic, α ≠ 0, α ≠ 1, β ∈ Algebraic \ ℚ  ⟹  α^β ∉ Algebraic
```

### Famous Consequences

| Example | Transcendental Number |
|---------|----------------------|
| 2^√2 | (Hilbert's 7th problem, "Hilbert number") |
| e^π | (Gelfond's constant) |
| i^i = e^(-π/2) | |

### Proof Sketch (1934)

Uses auxiliary functions and the Thue-Siegel-Roth theorem:
1. Assume α^β is algebraic
2. Construct auxiliary function with many zeros
3. Apply extrapolation lemma
4. Obtain contradiction via arithmetic properties

### Lean 4 Formalization

**Status:** NOT FORMALIZED in Mathlib

**Expected Lean Template:**
```lean
theorem gelfond_schneider
    {α β : ℂ}
    (hα_alg : IsAlgebraic ℚ α)
    (hα_ne_zero : α ≠ 0)
    (hα_ne_one : α ≠ 1)
    (hβ_alg : IsAlgebraic ℚ β)
    (hβ_irr : ¬IsAlgebraic ℚ β ∨ β ∉ Set.range ((↑) : ℚ → ℂ)) :
    Transcendental ℚ (α ^ β) := by
  sorry
```

**Difficulty:** very hard

---

## 16. Liouville's Theorem on Transcendental Numbers

### Natural Language Statement

A Liouville number is a real number x such that for every positive integer n, there exist integers p and q (q > 1) satisfying:
```
0 < |x - p/q| < 1/q^n
```

**Theorem:** Every Liouville number is transcendental.

### Mathematical Statement

```
(∀n > 0, ∃p,q ∈ ℤ, q > 1 ∧ 0 < |x - p/q| < 1/q^n) ⟹ x is transcendental
```

### Liouville's Constant

The first explicitly constructed transcendental number (1844):
```
L = ∑(n=1 to ∞) 10^(-n!) = 0.110001000000000000000001000...
```
where 1's appear at positions 1!, 2!, 3!, 4!, ...

### Proof Sketch

1. **Assume** x is algebraic of degree d
2. **By Liouville's approximation theorem:** For algebraic x of degree d, there exists c > 0 such that |x - p/q| > c/q^d for all p/q
3. **But** x being Liouville means |x - p/q| < 1/q^n for arbitrarily large n
4. **Taking** n > d gives contradiction

### Lean 4 Formalization

**Status:** PARTIAL in Mathlib

**Mathlib:** `Mathlib.NumberTheory.Liouville.Basic` contains Liouville's approximation theorem

**Expected Lean Template:**
```lean
theorem Liouville.transcendental {x : ℝ}
    (hx : Liouville x) : Transcendental ℚ x := by
  intro h
  obtain ⟨p, hp⟩ := h  -- x is root of polynomial p
  have hdeg := Polynomial.degree_pos_of_ne_zero_of_nonroot hp
  -- Apply Liouville approximation theorem to get contradiction
  sorry
```

**Import:** `Mathlib.NumberTheory.Liouville.Basic`

**Difficulty:** medium

---

## Implementation Priority (Updated)

### Phase 1: Easy Theorems (1 tactic each)

| Theorem | `theorem_id` | Lean Proof |
|---------|--------------|------------|
| Euclid's Infinitude | `euclid_infinitude_primes` | `exact Nat.exists_infinite_primes` |
| FTA Existence | `fta_existence` | `exact Nat.prod_primeFactorsList` |
| FTA Uniqueness | `fta_uniqueness` | `exact Nat.primeFactorsList_unique` |
| Fermat's Little | `fermat_little_theorem` | `exact ZMod.pow_card_sub_one` |
| Wilson's Theorem | `wilson_theorem` | `exact Nat.Prime.wilsons_lemma` |
| Euler's Theorem | `euler_theorem` | `exact ZMod.pow_totient` |

### Phase 2: Medium Theorems (5-15 tactics)

| Theorem | `theorem_id` | Lean Proof |
|---------|--------------|------------|
| Bertrand's Postulate | `bertrand_postulate` | `exact Nat.exists_prime_lt_and_lt` |
| Quadratic Reciprocity | `quadratic_reciprocity` | `exact legendreSym.quadratic_reciprocity` |
| Sum of Two Squares | `sum_two_squares` | `exact Nat.Prime.sq_add_sq` |
| Prime Reciprocal Divergence | `prime_reciprocal_diverges` | `exact tendsto_sum_one_div_prime_atTop` |
| Liouville Transcendence | `liouville_transcendental` | Uses `Liouville.transcendental` |

### Phase 3: Supporting Lemmas

| Lemma | Description |
|-------|-------------|
| Euclid's Lemma | If p prime and p divides ab, then p divides a or b |
| Central Binomial Bounds | Lower/upper bounds on C(2n,n) |
| Legendre Symbol Properties | Basic properties for quadratic reciprocity |
| Totient Function Properties | For Euler's theorem applications |
| Liouville Approximation | Algebraic numbers have bounded rational approximation |

### Phase 4: Hard (Analytic Number Theory)

| Theorem | Description |
|---------|-------------|
| Dirichlet (simple cases) | Primes ≡ 1 (mod 4), Primes ≡ 3 (mod 4) |
| General Dirichlet | For any coprime a, d |
| L(1, chi) != 0 | Non-vanishing at s=1 |
| Prime Number Theorem | pi(x) ~ x/log(x) |

### Phase 5: Transcendence Theory (NOT YET FORMALIZED)

| Theorem | Status | Freek # | Difficulty |
|---------|--------|---------|------------|
| e transcendental | NOT FORMALIZED | - | Medium-Hard |
| π transcendental | NOT FORMALIZED | #53 | Hard |
| Lindemann-Weierstrass | NOT FORMALIZED | #56 | Very Hard |
| Gelfond-Schneider | NOT FORMALIZED | - | Very Hard |
| Liouville's Theorem | PARTIAL | - | Medium |

---

## Dataset Integration

### Example Theorem Record

```json
{
  "theorem_id": "euclid_infinitude_primes",
  "mathematical_domain": "NumberTheory",
  "theorem_name": "Euclid's Theorem on the Infinitude of Primes",
  "nl_statement": "There are infinitely many prime numbers. For every natural number n, there exists a prime p >= n.",
  "lean_statement": "theorem euclid_infinitude : ∀ n : N, ∃ p >= n, Nat.Prime p",
  "lean_proof_term": "Nat.exists_infinite_primes",
  "lean_proof_tactic": "by exact Nat.exists_infinite_primes",
  "imports": ["Mathlib.Data.Nat.Prime.Infinite"],
  "difficulty": "easy",
  "mathlib_support": "full",
  "reasoning_trace": {
    "mathematical_insight": "Construct n! + 1, which has a prime factor > n",
    "key_lemmas": ["Nat.exists_infinite_primes"],
    "proof_strategy": "Direct application of Mathlib theorem",
    "common_pitfalls": ["n! + 1 is not always prime, but has a prime factor > n"]
  },
  "proof_status": "complete",
  "schema_version": "2.0.0"
}
```

### Example Lemma Record

```json
{
  "lemma_id": "euclids_lemma_prime_dvd_mul",
  "theorem_id": "fta_uniqueness",
  "lemma_name": "Euclid's Lemma",
  "nl_statement": "If a prime p divides a product ab, then p divides a or p divides b.",
  "lean_statement": "lemma euclids_lemma {p a b : N} (hp : Nat.Prime p) (h : p ∣ a * b) : p ∣ a ∨ p ∣ b",
  "lean_proof_term": "hp.dvd_mul.mp h",
  "lean_proof_tactic": "by exact hp.dvd_mul.mp h",
  "depends_on_lemmas": [],
  "imports": ["Mathlib.Data.Nat.Prime.Basic"],
  "proof_status": "complete",
  "schema_version": "2.0.0"
}
```

---

## References

### Mathlib Documentation
- [Data.Nat.Prime.Infinite](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Data/Nat/Prime/Infinite.html)
- [Data.Nat.Factors](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Data/Nat/Factors.html)
- [FieldTheory.Finite.Basic](https://leanprover-community.github.io/mathlib4_docs/Mathlib/FieldTheory/Finite/Basic.html)
- [NumberTheory.Wilson](https://leanprover-community.github.io/mathlib4_docs/Mathlib/NumberTheory/Wilson.html)
- [Data.ZMod.Basic](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Data/ZMod/Basic.html)
- [Data.Nat.Totient](https://leanprover-community.github.io/mathlib4_docs/Mathlib/Data/Nat/Totient.html)
- [NumberTheory.LegendreSymbol.QuadraticReciprocity](https://leanprover-community.github.io/mathlib4_docs/Mathlib/NumberTheory/LegendreSymbol/QuadraticReciprocity.html)
- [NumberTheory.SumTwoSquares](https://leanprover-community.github.io/mathlib4_docs/Mathlib/NumberTheory/SumTwoSquares.html)
- [NumberTheory.SumPrimeReciprocals](https://leanprover-community.github.io/mathlib4_docs/Mathlib/NumberTheory/SumPrimeReciprocals.html)
- [NumberTheory.Bertrand](https://leanprover-community.github.io/mathlib4_docs/Mathlib/NumberTheory/Bertrand.html)
- [NumberTheory.LSeries.PrimesInAP](https://leanprover-community.github.io/mathlib4_docs/Mathlib/NumberTheory/LSeries/PrimesInAP.html)
- [NumberTheory.PrimeNumberTheoremAnd](https://github.com/AlexKontorovich/PrimeNumberTheoremAnd)

### Wikipedia: Prime Numbers
- [Euclid's Theorem](https://en.wikipedia.org/wiki/Euclid's_theorem)
- [Fundamental Theorem of Arithmetic](https://en.wikipedia.org/wiki/Fundamental_theorem_of_arithmetic)
- [Fermat's Little Theorem](https://en.wikipedia.org/wiki/Fermat's_little_theorem)
- [Wilson's Theorem](https://en.wikipedia.org/wiki/Wilson's_theorem)
- [Euler's Theorem](https://en.wikipedia.org/wiki/Euler's_theorem)
- [Quadratic Reciprocity](https://en.wikipedia.org/wiki/Quadratic_reciprocity)
- [Fermat's Theorem on Sums of Two Squares](https://en.wikipedia.org/wiki/Fermat's_theorem_on_sums_of_two_squares)
- [Divergence of the Sum of Reciprocals of Primes](https://en.wikipedia.org/wiki/Divergence_of_the_sum_of_the_reciprocals_of_the_primes)
- [Bertrand's Postulate](https://en.wikipedia.org/wiki/Bertrand's_postulate)
- [Dirichlet's Theorem](https://en.wikipedia.org/wiki/Dirichlet's_theorem_on_arithmetic_progressions)
- [Prime Number Theorem](https://en.wikipedia.org/wiki/Prime_number_theorem)

### Wikipedia: Transcendence Theory
- [Transcendental Number](https://en.wikipedia.org/wiki/Transcendental_number)
- [Lindemann-Weierstrass Theorem](https://en.wikipedia.org/wiki/Lindemann–Weierstrass_theorem)
- [Gelfond-Schneider Theorem](https://en.wikipedia.org/wiki/Gelfond–Schneider_theorem)
- [Liouville Number](https://en.wikipedia.org/wiki/Liouville_number)
- [Proof that π is transcendental](https://en.wikipedia.org/wiki/Proof_that_π_is_transcendental)
- [Proof that e is transcendental](https://en.wikipedia.org/wiki/Proof_that_e_is_irrational#Proof_that_e_is_transcendental)

### Mathlib: Transcendence Theory (Partial)
- [NumberTheory.Liouville.Basic](https://leanprover-community.github.io/mathlib4_docs/Mathlib/NumberTheory/Liouville/Basic.html)
- [RingTheory.Algebraic.Basic](https://leanprover-community.github.io/mathlib4_docs/Mathlib/RingTheory/Algebraic/Basic.html)

### Academic
- [Loeffler & Stoll: Formalizing L-functions in Lean (2024)](https://arxiv.org/abs/2503.00959)
- [100 Theorems in Lean](https://leanprover-community.github.io/100.html)
- [Freek #53: π is Transcendental](https://www.cs.ru.nl/~freek/100/#53)
- [Freek #56: Hermite-Lindemann Theorem](https://www.cs.ru.nl/~freek/100/#56)

---

**End of Knowledge Base**
