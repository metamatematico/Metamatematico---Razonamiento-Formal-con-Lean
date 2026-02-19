"""
Tactics Database - Lean 4 Tactic Patterns
==========================================

Comprehensive database of Lean 4 tactics extracted from lean4-skills.
Organized by goal patterns and use cases.

Based on:
- lean4-skills/plugins/lean4-theorem-proving/references/tactics-reference.md
- lean4-skills/plugins/lean4-theorem-proving/references/sorry-filling.md
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class TacticCategory(Enum):
    """Categories of tactics."""
    SIMPLIFICATION = auto()   # simp, ring, norm_num
    CASE_ANALYSIS = auto()    # by_cases, rcases, cases
    REWRITING = auto()        # rw, simp_rw, rfl
    APPLICATION = auto()      # exact, apply, refine
    CONSTRUCTION = auto()     # constructor, use
    EXTENSION = auto()        # ext, funext, congr
    ARITHMETIC = auto()       # linarith, omega, nlinarith
    DOMAIN_SPECIFIC = auto()  # continuity, measurability
    AUTOMATION = auto()       # simp?, exact?, apply?, aesop


@dataclass
class Tactic:
    """Representation of a Lean 4 tactic."""
    name: str
    category: TacticCategory
    description: str
    syntax: str
    when_to_use: str
    example: str = ""
    variants: list[str] = field(default_factory=list)
    see_also: list[str] = field(default_factory=list)


@dataclass
class GoalPattern:
    """A goal pattern and its suggested tactics."""
    pattern: str              # e.g., "a = b", "forall x, P x"
    description: str          # Human-readable description
    primary_tactics: list[str]
    reason: str
    alternatives: list[str] = field(default_factory=list)


class TacticsDatabase:
    """
    Database of Lean 4 tactics with goal pattern matching.

    Provides tactic suggestions based on goal structure.

    Example:
        db = TacticsDatabase()

        # Get suggestions for a goal
        suggestions = db.suggest_for_goal("forall x : Nat, x + 0 = x")
        print(suggestions)  # ['intro x', 'simp', 'rfl']

        # Get tactic info
        tactic = db.get_tactic("simp")
        print(tactic.when_to_use)
    """

    def __init__(self):
        """Initialize the tactics database."""
        self._tactics: dict[str, Tactic] = {}
        self._patterns: list[GoalPattern] = []
        self._load_tactics()
        self._load_patterns()

    def _load_tactics(self) -> None:
        """Load all known tactics."""
        # Simplification tactics
        self._add_tactic(Tactic(
            name="simp",
            category=TacticCategory.SIMPLIFICATION,
            description="Recursively applies @[simp] lemmas to rewrite expressions to normal form",
            syntax="simp [lemmas]",
            when_to_use="Obvious algebraic simplifications, normalizing expressions, cleaning up after other tactics",
            example="example : x + 0 = x := by simp",
            variants=["simp only [lem1, lem2]", "simp [*]", "simp at h", "simp at *", "simpa using h", "simp?"],
            see_also=["simp_rw", "norm_num", "ring"]
        ))

        self._add_tactic(Tactic(
            name="ring",
            category=TacticCategory.SIMPLIFICATION,
            description="Solve ring equations (polynomial arithmetic)",
            syntax="ring",
            when_to_use="Polynomial equalities in commutative rings",
            example="example (a b : Int) : (a + b)^2 = a^2 + 2*a*b + b^2 := by ring",
            see_also=["field_simp", "group"]
        ))

        self._add_tactic(Tactic(
            name="norm_num",
            category=TacticCategory.SIMPLIFICATION,
            description="Normalize numerical expressions",
            syntax="norm_num",
            when_to_use="Numerical computations, comparing concrete numbers",
            example="example : 2 + 2 = 4 := by norm_num",
            see_also=["ring", "simp"]
        ))

        self._add_tactic(Tactic(
            name="field_simp",
            category=TacticCategory.SIMPLIFICATION,
            description="Simplify field expressions by clearing denominators",
            syntax="field_simp",
            when_to_use="Expressions with fractions and division",
            example="example (x : Rat) (hx : x != 0) : x / x = 1 := by field_simp",
            see_also=["ring", "simp"]
        ))

        # Case analysis tactics
        self._add_tactic(Tactic(
            name="by_cases",
            category=TacticCategory.CASE_ANALYSIS,
            description="Split on decidable proposition",
            syntax="by_cases h : p",
            when_to_use="When proof depends on whether a proposition is true or false",
            example="by_cases h : n = 0",
            see_also=["cases", "rcases"]
        ))

        self._add_tactic(Tactic(
            name="rcases",
            category=TacticCategory.CASE_ANALYSIS,
            description="Recursive case analysis / destructuring",
            syntax="rcases h with pattern",
            when_to_use="Destructure exists, and, or hypotheses",
            example="rcases h with <x, hx> -- for h : exists x, P x",
            variants=["rcases h with <h1, h2>", "rcases h with h1 | h2", "rcases h with <x, y, <hx, hy>>"],
            see_also=["obtain", "cases"]
        ))

        self._add_tactic(Tactic(
            name="obtain",
            category=TacticCategory.CASE_ANALYSIS,
            description="Destructure with explicit intent",
            syntax="obtain pattern := proof",
            when_to_use="Extract witnesses from existential hypotheses",
            example="obtain <C, hC> := h_bound",
            see_also=["rcases", "cases"]
        ))

        self._add_tactic(Tactic(
            name="cases",
            category=TacticCategory.CASE_ANALYSIS,
            description="Case split on inductive type",
            syntax="cases x with | pattern1 => ... | pattern2 => ...",
            when_to_use="Inductive types like Nat, List, Option",
            example="cases n with | zero => ... | succ k => ...",
            see_also=["rcases", "induction"]
        ))

        # Rewriting tactics
        self._add_tactic(Tactic(
            name="rw",
            category=TacticCategory.REWRITING,
            description="Rewrite using equality",
            syntax="rw [lemma]",
            when_to_use="Single rewrite with known equality",
            example="rw [h] -- where h : x = y",
            variants=["rw [<- lemma]", "rw [lem1, lem2]", "rw [lemma] at h"],
            see_also=["simp_rw", "simp"]
        ))

        self._add_tactic(Tactic(
            name="simp_rw",
            category=TacticCategory.REWRITING,
            description="Simplifying rewrites (chains)",
            syntax="simp_rw [h1, h2, h3]",
            when_to_use="Multiple sequential rewrites, rewrite chains",
            example="simp_rw [hf_eq, integral_indicator, Measure.restrict_restrict]",
            see_also=["rw", "simp"]
        ))

        self._add_tactic(Tactic(
            name="rfl",
            category=TacticCategory.REWRITING,
            description="Reflexivity of equality",
            syntax="rfl",
            when_to_use="Goals of form a = a (definitionally equal)",
            example="example : 2 + 2 = 4 := by rfl",
            see_also=["exact"]
        ))

        # Application tactics
        self._add_tactic(Tactic(
            name="exact",
            category=TacticCategory.APPLICATION,
            description="Provide exact proof term",
            syntax="exact term",
            when_to_use="Have a term with exactly the right type",
            example="exact h",
            see_also=["apply", "refine"]
        ))

        self._add_tactic(Tactic(
            name="apply",
            category=TacticCategory.APPLICATION,
            description="Apply lemma, leave subgoals for premises",
            syntax="apply lemma",
            when_to_use="Have a lemma that matches goal structure",
            example="apply Nat.le_succ_of_le",
            see_also=["exact", "refine"]
        ))

        self._add_tactic(Tactic(
            name="refine",
            category=TacticCategory.APPLICATION,
            description="Apply with explicit placeholders",
            syntax="refine { field := ?_, ... }",
            when_to_use="Partial application with holes",
            example="refine { field1 := value, field2 := ?_ }",
            see_also=["exact", "apply"]
        ))

        # Construction tactics
        self._add_tactic(Tactic(
            name="constructor",
            category=TacticCategory.CONSTRUCTION,
            description="Build inductive type (and, iff, structures)",
            syntax="constructor",
            when_to_use="Prove conjunction, iff, or fill structure",
            example="constructor -- for P /\\ Q, creates two goals",
            see_also=["use", "exact"]
        ))

        self._add_tactic(Tactic(
            name="use",
            category=TacticCategory.CONSTRUCTION,
            description="Provide witness for existential",
            syntax="use witness",
            when_to_use="Prove exists x, P x by providing x",
            example="use 10 -- for exists n, n > 5",
            see_also=["constructor", "refine"]
        ))

        self._add_tactic(Tactic(
            name="intro",
            category=TacticCategory.CONSTRUCTION,
            description="Introduce hypothesis for forall or implication",
            syntax="intro x",
            when_to_use="Goal is forall x, P x or P -> Q",
            example="intro h",
            variants=["intros", "intro x y z"],
            see_also=["apply", "exact"]
        ))

        self._add_tactic(Tactic(
            name="left",
            category=TacticCategory.CONSTRUCTION,
            description="Prove left side of disjunction",
            syntax="left",
            when_to_use="Goal is A \\/ B and you can prove A",
            see_also=["right", "constructor"]
        ))

        self._add_tactic(Tactic(
            name="right",
            category=TacticCategory.CONSTRUCTION,
            description="Prove right side of disjunction",
            syntax="right",
            when_to_use="Goal is A \\/ B and you can prove B",
            see_also=["left", "constructor"]
        ))

        # Extension tactics
        self._add_tactic(Tactic(
            name="ext",
            category=TacticCategory.EXTENSION,
            description="Function extensionality",
            syntax="ext x",
            when_to_use="Prove f = g by proving f x = g x for all x",
            example="ext x",
            variants=["funext x"],
            see_also=["congr"]
        ))

        self._add_tactic(Tactic(
            name="congr",
            category=TacticCategory.EXTENSION,
            description="Congruence (break f a = f b into a = b)",
            syntax="congr",
            when_to_use="Same function applied to different arguments",
            see_also=["ext"]
        ))

        # Arithmetic tactics
        self._add_tactic(Tactic(
            name="linarith",
            category=TacticCategory.ARITHMETIC,
            description="Linear arithmetic (works on any additive group)",
            syntax="linarith",
            when_to_use="Linear inequalities and equalities on R, Q, Z, etc.",
            example="have : x <= y := by linarith",
            see_also=["nlinarith", "omega"]
        ))

        self._add_tactic(Tactic(
            name="omega",
            category=TacticCategory.ARITHMETIC,
            description="Integer linear arithmetic (Lean 4.13+)",
            syntax="omega",
            when_to_use="Integer inequalities",
            example="have : n < m := by omega",
            see_also=["linarith"]
        ))

        self._add_tactic(Tactic(
            name="nlinarith",
            category=TacticCategory.ARITHMETIC,
            description="Non-linear arithmetic",
            syntax="nlinarith",
            when_to_use="Non-linear inequalities",
            see_also=["linarith"]
        ))

        # Domain-specific tactics
        self._add_tactic(Tactic(
            name="continuity",
            category=TacticCategory.DOMAIN_SPECIFIC,
            description="Prove continuity automatically",
            syntax="continuity",
            when_to_use="Proving Continuous f",
            see_also=["measurability", "fun_prop"]
        ))

        self._add_tactic(Tactic(
            name="measurability",
            category=TacticCategory.DOMAIN_SPECIFIC,
            description="Prove measurability automatically",
            syntax="measurability",
            when_to_use="Proving Measurable f",
            see_also=["continuity", "fun_prop"]
        ))

        self._add_tactic(Tactic(
            name="positivity",
            category=TacticCategory.DOMAIN_SPECIFIC,
            description="Prove positivity of measures/integrals",
            syntax="positivity",
            when_to_use="Proving 0 <= x or 0 < x",
            see_also=["linarith"]
        ))

        self._add_tactic(Tactic(
            name="fun_prop",
            category=TacticCategory.DOMAIN_SPECIFIC,
            description="Prove function properties compositionally",
            syntax="fun_prop (disch := tactic)",
            when_to_use="Compositional proofs of Measurable, Continuous, etc.",
            example="fun_prop (disch := measurability)",
            variants=["fun_prop", "fun_prop (disch := assumption)", "fun_prop (disch := simp)"],
            see_also=["continuity", "measurability"]
        ))

        # Automation tactics
        self._add_tactic(Tactic(
            name="simp?",
            category=TacticCategory.AUTOMATION,
            description="Show which simp lemmas would be used",
            syntax="simp?",
            when_to_use="Exploring what simp does",
            see_also=["exact?", "apply?"]
        ))

        self._add_tactic(Tactic(
            name="exact?",
            category=TacticCategory.AUTOMATION,
            description="Search for exact term that closes goal",
            syntax="exact?",
            when_to_use="Finding lemma in library",
            see_also=["apply?", "simp?"]
        ))

        self._add_tactic(Tactic(
            name="apply?",
            category=TacticCategory.AUTOMATION,
            description="Search for applicable lemma",
            syntax="apply?",
            when_to_use="Finding lemma to apply",
            see_also=["exact?", "simp?"]
        ))

        self._add_tactic(Tactic(
            name="aesop",
            category=TacticCategory.AUTOMATION,
            description="Automated proof search",
            syntax="aesop",
            when_to_use="General automation, may solve goal completely",
            see_also=["simp", "decide"]
        ))

        self._add_tactic(Tactic(
            name="decide",
            category=TacticCategory.AUTOMATION,
            description="Decide decidable propositions",
            syntax="decide",
            when_to_use="Decidable goals (finite cases)",
            see_also=["aesop"]
        ))

    def _load_patterns(self) -> None:
        """Load goal patterns and their suggested tactics."""
        # Equality
        self._patterns.append(GoalPattern(
            pattern="a = b",
            description="Prove equality",
            primary_tactics=["rfl", "simp", "ring"],
            reason="Equality goals",
            alternatives=["rw", "ext", "congr"]
        ))

        # Universal quantifier
        self._patterns.append(GoalPattern(
            pattern="forall x, P x",
            description="Prove universal statement",
            primary_tactics=["intro x"],
            reason="Universal quantifier",
            alternatives=["intros"]
        ))

        # Existential
        self._patterns.append(GoalPattern(
            pattern="exists x, P x",
            description="Prove existential statement",
            primary_tactics=["use [term]"],
            reason="Existential proof",
            alternatives=["refine"]
        ))

        # Implication
        self._patterns.append(GoalPattern(
            pattern="A -> B",
            description="Prove implication",
            primary_tactics=["intro h"],
            reason="Implication",
            alternatives=["intros"]
        ))

        # Conjunction
        self._patterns.append(GoalPattern(
            pattern="A /\\ B",
            description="Prove conjunction",
            primary_tactics=["constructor"],
            reason="Conjunction",
            alternatives=["And.intro", "refine"]
        ))

        # Disjunction
        self._patterns.append(GoalPattern(
            pattern="A \\/ B",
            description="Prove disjunction",
            primary_tactics=["left", "right"],
            reason="Disjunction",
            alternatives=["Or.inl", "Or.inr"]
        ))

        # Inequality
        self._patterns.append(GoalPattern(
            pattern="a <= b",
            description="Prove inequality",
            primary_tactics=["linarith", "omega"],
            reason="Inequality",
            alternatives=["nlinarith", "apply"]
        ))

        self._patterns.append(GoalPattern(
            pattern="a < b",
            description="Prove strict inequality",
            primary_tactics=["linarith", "omega"],
            reason="Strict inequality",
            alternatives=["nlinarith", "apply"]
        ))

        # Iff
        self._patterns.append(GoalPattern(
            pattern="A <-> B",
            description="Prove biconditional",
            primary_tactics=["constructor"],
            reason="Iff creates P -> Q and Q -> P",
            alternatives=["Iff.intro", "refine"]
        ))

        # Negation
        self._patterns.append(GoalPattern(
            pattern="Not P",
            description="Prove negation",
            primary_tactics=["intro h"],
            reason="Not P = P -> False",
            alternatives=["by_contra"]
        ))

        # Function equality
        self._patterns.append(GoalPattern(
            pattern="f = g",
            description="Prove function equality",
            primary_tactics=["ext", "funext"],
            reason="Function extensionality",
            alternatives=["apply funext"]
        ))

        # Continuity
        self._patterns.append(GoalPattern(
            pattern="Continuous f",
            description="Prove continuity",
            primary_tactics=["continuity"],
            reason="Domain-specific automation",
            alternatives=["fun_prop", "apply Continuous.comp"]
        ))

        # Measurability
        self._patterns.append(GoalPattern(
            pattern="Measurable f",
            description="Prove measurability",
            primary_tactics=["measurability"],
            reason="Domain-specific automation",
            alternatives=["fun_prop (disch := measurability)", "apply Measurable.comp"]
        ))

    def _add_tactic(self, tactic: Tactic) -> None:
        """Add a tactic to the database."""
        self._tactics[tactic.name] = tactic

    def get_tactic(self, name: str) -> Optional[Tactic]:
        """Get tactic info by name."""
        return self._tactics.get(name)

    def get_tactics_by_category(self, category: TacticCategory) -> list[Tactic]:
        """Get all tactics in a category."""
        return [t for t in self._tactics.values() if t.category == category]

    def suggest_for_goal(self, goal: str) -> list[str]:
        """
        Suggest tactics based on goal pattern.

        Args:
            goal: The goal string (e.g., "forall x : Nat, x + 0 = x")

        Returns:
            List of suggested tactics
        """
        suggestions = []
        goal_lower = goal.lower()

        # Pattern matching
        for pattern in self._patterns:
            if self._matches_pattern(goal_lower, pattern.pattern):
                suggestions.extend(pattern.primary_tactics)

        # Keyword-based suggestions
        keyword_tactics = {
            "forall": ["intro"],
            "exists": ["use"],
            "->": ["intro"],
            "/\\": ["constructor"],
            "\\/": ["left", "right"],
            "<=": ["linarith", "omega"],
            "<": ["linarith", "omega"],
            "=": ["rfl", "simp", "ring"],
            "<->": ["constructor"],
            "not": ["intro"],
            "continuous": ["continuity", "fun_prop"],
            "measurable": ["measurability", "fun_prop"],
        }

        for keyword, tactics in keyword_tactics.items():
            if keyword in goal_lower:
                for t in tactics:
                    if t not in suggestions:
                        suggestions.append(t)

        # Default suggestions
        if not suggestions:
            suggestions = ["simp", "aesop", "exact?"]

        return suggestions

    def _matches_pattern(self, goal: str, pattern: str) -> bool:
        """Check if goal matches pattern (simple heuristic)."""
        pattern_lower = pattern.lower()

        # Simple keyword matching
        keywords = pattern_lower.replace("a", "").replace("b", "").replace("x", "").replace("p", "").strip().split()
        return any(kw in goal for kw in keywords if kw)

    def get_quick_reference(self) -> dict[str, str]:
        """Get quick reference table (want to... -> use...)."""
        return {
            "Close with exact term": "exact",
            "Apply lemma": "apply",
            "Rewrite once": "rw [lemma]",
            "Normalize expression": "simp, ring, norm_num",
            "Split cases": "by_cases, cases, rcases",
            "Prove exists": "use witness",
            "Prove and/iff": "constructor",
            "Prove function equality": "ext / funext",
            "Explore options": "exact?, apply?, simp?",
            "Domain-specific automation": "ring, linarith, continuity, measurability",
        }

    @property
    def all_tactics(self) -> list[str]:
        """List all tactic names."""
        return list(self._tactics.keys())

    @property
    def stats(self) -> dict[str, int]:
        """Database statistics."""
        return {
            "total_tactics": len(self._tactics),
            "total_patterns": len(self._patterns),
            "categories": len(TacticCategory),
        }


# Singleton instance
_tactics_db: Optional[TacticsDatabase] = None


def get_tactics_database() -> TacticsDatabase:
    """Get the global tactics database instance."""
    global _tactics_db
    if _tactics_db is None:
        _tactics_db = TacticsDatabase()
    return _tactics_db
