"""
Sorry Filler Strategy - Automated Proof Completion
===================================================

Implements the sorry-filling workflow from lean4-skills.
Generates proof candidates and tests them.

Core workflow:
1. Understand the sorry context
2. Search mathlib first (90% success rate)
3. Generate 2-3 proof candidates
4. Test before applying
5. Apply working solution or escalate

Based on:
- lean4-skills/plugins/lean4-subagents/agents/lean4-sorry-filler.md
- lean4-skills/plugins/lean4-theorem-proving/references/sorry-filling.md
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional, Callable

from nucleo.lean.tactics_db import get_tactics_database, TacticsDatabase
from nucleo.lean.solver_cascade import SolverCascade, CascadeResult


class SorryType(Enum):
    """Types of sorries based on difficulty."""
    MATHLIB_EXISTS = auto()     # 60% - Lemma exists in mathlib
    NEEDS_TACTIC = auto()       # 20% - Just needs right tactic
    MISSING_STEP = auto()       # 15% - Needs intermediate step
    COMPLEX_STRUCTURAL = auto()  # 4% - Complex proof structure
    NOVEL_RESULT = auto()        # 1% - Actually new result


@dataclass
class SorryContext:
    """Context information about a sorry."""
    file_path: str
    line_number: int
    goal: str                         # The goal to prove
    goal_type: str                    # equality, forall, exists, etc.
    hypotheses: list[str] = field(default_factory=list)
    surrounding_code: str = ""
    theorem_name: Optional[str] = None
    sorry_type: Optional[SorryType] = None


@dataclass
class ProofCandidate:
    """A candidate proof for a sorry."""
    code: str
    strategy: str        # direct, tactics, automation
    confidence: float    # 0.0 to 1.0
    explanation: str
    dependencies: list[str] = field(default_factory=list)  # Required imports


@dataclass
class CandidateResult:
    """Result of testing a proof candidate."""
    candidate: ProofCandidate
    success: bool
    error_message: Optional[str] = None
    error_type: Optional[str] = None


@dataclass
class SorryFillingResult:
    """Result of the sorry-filling process."""
    context: SorryContext
    candidates: list[ProofCandidate]
    results: list[CandidateResult]
    chosen_solution: Optional[ProofCandidate] = None
    needs_escalation: bool = False
    escalation_reason: Optional[str] = None
    cascade_result: Optional[CascadeResult] = None


class SorryFiller:
    """
    Strategy for filling Lean 4 sorries.

    Implements a breadth-first approach that tries obvious solutions
    before escalating to more complex strategies.

    Example:
        filler = SorryFiller()

        # Analyze a sorry
        context = SorryContext(
            file_path="MyTheory.lean",
            line_number=42,
            goal="forall n : Nat, n + 0 = n",
            goal_type="forall"
        )

        # Generate candidates
        candidates = filler.generate_candidates(context)

        # After testing (external)
        result = filler.create_result(context, candidates, results)
    """

    def __init__(
        self,
        tactics_db: Optional[TacticsDatabase] = None,
        solver_cascade: Optional[SolverCascade] = None,
        max_candidates: int = 3,
        max_diff_lines: int = 80
    ):
        """
        Initialize the sorry filler.

        Args:
            tactics_db: Tactics database (uses global if None)
            solver_cascade: Solver cascade for automated resolution
            max_candidates: Maximum candidates per sorry
            max_diff_lines: Maximum lines per candidate
        """
        self._tactics_db = tactics_db or get_tactics_database()
        self._solver_cascade = solver_cascade
        self._max_candidates = max_candidates
        self._max_diff_lines = max_diff_lines

    async def fill_sorry_with_cascade(
        self,
        context: SorryContext,
        full_code: str,
    ) -> SorryFillingResult:
        """
        Try to fill a sorry using solver cascade first, then candidates.

        This is the primary integration point with lean4-skills.
        Uses the APOLLO-inspired solver cascade as step 0 before
        generating LLM-based candidates.

        Args:
            context: Sorry context with location and goal
            full_code: Full Lean source containing the sorry

        Returns:
            SorryFillingResult (may be solved by cascade alone)
        """
        cascade_result = None

        # Step 0: Try solver cascade (handles 40-60% of simple cases)
        if self._solver_cascade:
            cascade_result = await self._solver_cascade.try_fill_sorry(
                code=full_code,
                sorry_line=context.line_number,
            )
            if cascade_result.success:
                # Cascade solved it! Create a result with the cascade solution
                cascade_candidate = ProofCandidate(
                    code=cascade_result.replacement_code or "",
                    strategy="solver_cascade",
                    confidence=1.0,
                    explanation=f"Solved by solver cascade ({cascade_result.solver})",
                )
                cascade_test = CandidateResult(
                    candidate=cascade_candidate,
                    success=True,
                )
                return SorryFillingResult(
                    context=context,
                    candidates=[cascade_candidate],
                    results=[cascade_test],
                    chosen_solution=cascade_candidate,
                    cascade_result=cascade_result,
                )

        # Step 1: Generate candidates (LLM-based fallback)
        candidates = self.generate_candidates(context)

        # Return without testing (caller is responsible for testing)
        return SorryFillingResult(
            context=context,
            candidates=candidates,
            results=[],
            cascade_result=cascade_result,
        )

    def classify_sorry(self, context: SorryContext) -> SorryType:
        """
        Classify the type of sorry based on context.

        Args:
            context: The sorry context

        Returns:
            Classified sorry type
        """
        goal = context.goal.lower()

        # Simple patterns that suggest mathlib lemmas
        mathlib_patterns = [
            r"continuous\s+\w+",
            r"measurable\s+\w+",
            r"\w+\s*\+\s*0\s*=",
            r"\w+\s*\*\s*1\s*=",
            r"0\s*<=",
            r"nat\.succ",
            r"list\.map",
            r"set\.mem",
        ]

        for pattern in mathlib_patterns:
            if re.search(pattern, goal):
                context.sorry_type = SorryType.MATHLIB_EXISTS
                return SorryType.MATHLIB_EXISTS

        # Simple tactic patterns
        simple_patterns = ["=", "rfl", "trivial"]
        if any(p in goal for p in simple_patterns) and len(goal) < 50:
            context.sorry_type = SorryType.NEEDS_TACTIC
            return SorryType.NEEDS_TACTIC

        # Structural indicators
        structural_keywords = ["induction", "cases", "match", "rec"]
        if any(kw in context.surrounding_code.lower() for kw in structural_keywords):
            context.sorry_type = SorryType.COMPLEX_STRUCTURAL
            return SorryType.COMPLEX_STRUCTURAL

        # Default to missing step
        context.sorry_type = SorryType.MISSING_STEP
        return SorryType.MISSING_STEP

    def analyze_goal(self, goal: str) -> dict:
        """
        Analyze goal structure.

        Args:
            goal: The goal string

        Returns:
            Analysis dict with type, components, etc.
        """
        analysis = {
            "goal_type": "unknown",
            "components": [],
            "suggested_tactics": [],
            "complexity": "unknown",
        }

        goal_lower = goal.lower()

        # Detect goal type
        if goal_lower.startswith("forall") or "forall" in goal_lower:
            analysis["goal_type"] = "forall"
        elif "exists" in goal_lower:
            analysis["goal_type"] = "exists"
        elif "->" in goal:
            analysis["goal_type"] = "implication"
        elif "/\\" in goal or "and" in goal_lower:
            analysis["goal_type"] = "conjunction"
        elif "\\/" in goal or " or " in goal_lower:
            analysis["goal_type"] = "disjunction"
        elif "=" in goal and "!=" not in goal:
            analysis["goal_type"] = "equality"
        elif "<=" in goal or ">=" in goal:
            analysis["goal_type"] = "inequality"
        elif "<" in goal or ">" in goal:
            analysis["goal_type"] = "strict_inequality"
        elif "<->" in goal or "iff" in goal_lower:
            analysis["goal_type"] = "iff"

        # Get tactic suggestions
        analysis["suggested_tactics"] = self._tactics_db.suggest_for_goal(goal)

        # Estimate complexity
        if len(goal) < 30:
            analysis["complexity"] = "simple"
        elif len(goal) < 100:
            analysis["complexity"] = "medium"
        else:
            analysis["complexity"] = "complex"

        return analysis

    def generate_candidates(self, context: SorryContext) -> list[ProofCandidate]:
        """
        Generate proof candidates for a sorry.

        Args:
            context: The sorry context

        Returns:
            List of proof candidates (max 3)
        """
        candidates = []
        analysis = self.analyze_goal(context.goal)
        sorry_type = context.sorry_type or self.classify_sorry(context)

        # Candidate A: Direct (if mathlib lemma likely exists)
        direct_candidate = self._generate_direct_candidate(context, analysis)
        if direct_candidate:
            candidates.append(direct_candidate)

        # Candidate B: Tactic-based
        tactic_candidate = self._generate_tactic_candidate(context, analysis)
        if tactic_candidate:
            candidates.append(tactic_candidate)

        # Candidate C: Automation
        auto_candidate = self._generate_automation_candidate(context, analysis)
        if auto_candidate:
            candidates.append(auto_candidate)

        return candidates[:self._max_candidates]

    def _generate_direct_candidate(
        self,
        context: SorryContext,
        analysis: dict
    ) -> Optional[ProofCandidate]:
        """Generate direct application candidate."""
        goal_type = analysis["goal_type"]

        # Map goal types to common direct proofs
        direct_proofs = {
            "equality": [
                "exact rfl",
                "exact Eq.refl _",
            ],
            "forall": [
                "intro x; exact rfl",
                "intro x; simp",
            ],
            "exists": [
                "use 0",  # placeholder
                "use default",
            ],
            "implication": [
                "intro h; exact h",
                "intro h; simp [h]",
            ],
        }

        if goal_type in direct_proofs:
            code = direct_proofs[goal_type][0]
            return ProofCandidate(
                code=code,
                strategy="direct",
                confidence=0.5,
                explanation=f"Direct application for {goal_type} goal"
            )

        return None

    def _generate_tactic_candidate(
        self,
        context: SorryContext,
        analysis: dict
    ) -> Optional[ProofCandidate]:
        """Generate tactic-based candidate."""
        tactics = analysis["suggested_tactics"]
        goal_type = analysis["goal_type"]

        if not tactics:
            return None

        # Build tactic sequence
        tactic_lines = []

        # Add intro if needed
        if goal_type in ["forall", "implication"]:
            tactic_lines.append("intro h")

        # Add main tactic
        main_tactic = tactics[0]
        if main_tactic == "intro":
            tactic_lines.append("intro x")
        elif main_tactic == "constructor":
            tactic_lines.append("constructor")
            tactic_lines.append("  sorry")
            tactic_lines.append("  sorry")
        elif main_tactic in ["simp", "ring", "linarith", "omega"]:
            tactic_lines.append(main_tactic)
        elif main_tactic == "use":
            tactic_lines.append("use _")
        else:
            tactic_lines.append(main_tactic)

        # Add cleanup if needed
        if main_tactic not in ["simp", "ring", "linarith", "omega", "rfl"]:
            tactic_lines.append("simp")

        code = "\n".join(tactic_lines)

        return ProofCandidate(
            code=code,
            strategy="tactics",
            confidence=0.6,
            explanation=f"Tactic-based approach using {main_tactic}"
        )

    def _generate_automation_candidate(
        self,
        context: SorryContext,
        analysis: dict
    ) -> Optional[ProofCandidate]:
        """Generate automation-based candidate."""
        complexity = analysis["complexity"]

        if complexity == "simple":
            code = "simp [*]"
            confidence = 0.7
        elif complexity == "medium":
            code = "simp only [*] <;> aesop"
            confidence = 0.4
        else:
            code = "aesop"
            confidence = 0.3

        return ProofCandidate(
            code=code,
            strategy="automation",
            confidence=confidence,
            explanation="Automation-first approach"
        )

    def create_result(
        self,
        context: SorryContext,
        candidates: list[ProofCandidate],
        test_results: list[bool],
        error_messages: Optional[list[str]] = None
    ) -> SorryFillingResult:
        """
        Create the final result after testing candidates.

        Args:
            context: The sorry context
            candidates: Generated candidates
            test_results: Boolean results for each candidate
            error_messages: Error messages for failed candidates

        Returns:
            Complete sorry filling result
        """
        error_messages = error_messages or [""] * len(candidates)

        results = []
        for i, (candidate, success) in enumerate(zip(candidates, test_results)):
            results.append(CandidateResult(
                candidate=candidate,
                success=success,
                error_message=error_messages[i] if not success else None
            ))

        # Find first successful candidate
        chosen = None
        for result in results:
            if result.success:
                chosen = result.candidate
                break

        # Check if escalation needed
        needs_escalation = not any(test_results)
        escalation_reason = None
        if needs_escalation:
            escalation_reason = "All 3 candidates failed. Needs lean4-sorry-filler-deep."

        return SorryFillingResult(
            context=context,
            candidates=candidates,
            results=results,
            chosen_solution=chosen,
            needs_escalation=needs_escalation,
            escalation_reason=escalation_reason
        )

    def format_result(self, result: SorryFillingResult) -> str:
        """
        Format result for display.

        Args:
            result: The sorry filling result

        Returns:
            Formatted string
        """
        lines = []
        lines.append(f"Sorry at {result.context.file_path}:{result.context.line_number}")
        lines.append(f"Goal: {result.context.goal[:80]}...")
        lines.append("")

        for i, (candidate, res) in enumerate(zip(result.candidates, result.results), 1):
            status = "[OK]" if res.success else "[X]"
            lines.append(f"Candidate {chr(64+i)} ({candidate.strategy}): {status}")
            lines.append(f"  Code: {candidate.code[:60]}...")
            if not res.success and res.error_message:
                lines.append(f"  Error: {res.error_message[:60]}...")

        lines.append("")
        if result.chosen_solution:
            lines.append(f"[OK] Solution: {result.chosen_solution.strategy}")
            lines.append(f"Code:\n{result.chosen_solution.code}")
        elif result.needs_escalation:
            lines.append(f"[X] ESCALATION NEEDED: {result.escalation_reason}")

        return "\n".join(lines)


# Convenience functions

def classify_goal_type(goal: str) -> str:
    """Quick goal type classification."""
    filler = SorryFiller()
    analysis = filler.analyze_goal(goal)
    return analysis["goal_type"]


def suggest_tactics_for_goal(goal: str) -> list[str]:
    """Get tactic suggestions for a goal."""
    filler = SorryFiller()
    analysis = filler.analyze_goal(goal)
    return analysis["suggested_tactics"]


def estimate_sorry_difficulty(goal: str, context: str = "") -> SorryType:
    """Estimate the difficulty of a sorry."""
    filler = SorryFiller()
    ctx = SorryContext(
        file_path="",
        line_number=0,
        goal=goal,
        goal_type="",
        surrounding_code=context
    )
    return filler.classify_sorry(ctx)
