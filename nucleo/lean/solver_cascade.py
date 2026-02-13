"""
Solver Cascade - Automated Tactic Resolution
=============================================

Adapted from lean4-skills/plugins/lean4-theorem-proving/scripts/solverCascade.py

Tries automated solvers in sequence before resampling with LLM.
Handles 40-60% of simple cases mechanically.

Cascade order (APOLLO-inspired):
1. rfl (definitional equality)
2. simp (simplifier)
3. ring (ring normalization)
4. linarith (linear arithmetic)
5. nlinarith (nonlinear arithmetic)
6. omega (arithmetic automation)
7. exact? (proof search)
8. apply? (proof search)
9. aesop (general automation)

Reference:
- APOLLO: https://arxiv.org/abs/2505.05758
- lean4-skills solverCascade.py
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING
from pathlib import Path

from nucleo.lean.client import LeanClient, LeanResult, LeanResultStatus

if TYPE_CHECKING:
    from nucleo.graph.category import SkillCategory

logger = logging.getLogger(__name__)


# Solvers with their timeouts (seconds)
SOLVER_CASCADE = [
    ("rfl", 1),
    ("simp", 2),
    ("ring", 2),
    ("linarith", 3),
    ("nlinarith", 4),
    ("omega", 3),
    ("exact?", 5),
    ("apply?", 5),
    ("aesop", 8),
]

# Error types that won't benefit from the cascade
SKIP_ERROR_TYPES = frozenset([
    "unknown_ident",
    "synth_implicit",
    "recursion_depth",
    "synth_instance",
])


class GoalAnalyzer:
    """
    Analyze Lean goal structure to prioritize tactics.

    Uses regex patterns to detect goal type, then reorders the solver
    cascade so the most likely tactics are tried first. Optionally
    consults the skill graph to find tactic skills connected to the
    relevant mathematical domain.
    """

    # (regex_pattern, priority_tactics) — checked in order, first match wins
    GOAL_PATTERNS: list[tuple[str, list[str]]] = [
        # Ring/field algebra: a * b + c = ...
        (r"[\+\-\*\^].*=.*[\+\-\*\^]", ["ring", "nlinarith", "linarith"]),
        # Natural/integer arithmetic with inequalities
        (r"(Nat|Int|Fin|ℕ|ℤ).*[≤<≥>]|[≤<≥>].*(Nat|Int|Fin|ℕ|ℤ)", ["omega", "linarith", "simp"]),
        # Pure arithmetic equalities (n + 0 = n)
        (r"\b\d+\s*[\+\-\*]\s*\d+\s*=", ["omega", "simp", "ring"]),
        # Logical connectives
        (r"[∧∨¬↔]|True|False", ["simp", "tauto", "aesop"]),
        # Quantifiers / implications
        (r"[∀∃]|→", ["simp", "exact", "apply?"]),
        # List/array operations
        (r"List\.|Array\.|length|append|map", ["simp", "omega"]),
    ]

    # Map tactic skill IDs to their solver cascade names
    _SKILL_TO_SOLVER = {
        "tactic-simp": "simp",
        "tactic-ring": "ring",
        "tactic-omega": "omega",
        "tactic-exact": "exact?",
        "tactic-apply": "apply?",
        "tactic-aesop": "aesop",
        "tactic-induction": "induction",
        "tactic-rewrite": "rw",
        "tactic-calc": "calc",
    }

    def prioritize(
        self,
        goal: str,
        graph: Optional[SkillCategory] = None,
    ) -> list[tuple[str, int]]:
        """
        Reorder SOLVER_CASCADE based on goal structure and graph context.

        Args:
            goal: The Lean goal text to analyze
            graph: Optional skill graph for domain-aware ordering

        Returns:
            Reordered list of (solver_name, timeout) tuples
        """
        priority_names: list[str] = []

        # 1. Pattern matching on goal text
        for pattern, tactics in self.GOAL_PATTERNS:
            if re.search(pattern, goal):
                priority_names.extend(tactics)
                break  # First match wins

        # 2. Graph-based: find tactic skills connected to matched domains
        if graph is not None:
            graph_tactics = self._tactics_from_graph(goal, graph)
            # Add graph-suggested tactics after pattern-based ones
            for t in graph_tactics:
                if t not in priority_names:
                    priority_names.append(t)

        if not priority_names:
            return list(SOLVER_CASCADE)

        # 3. Build reordered cascade: priority first, then remaining
        solver_dict = {name: timeout for name, timeout in SOLVER_CASCADE}
        ordered = []
        seen = set()
        for name in priority_names:
            if name in solver_dict and name not in seen:
                ordered.append((name, solver_dict[name]))
                seen.add(name)
        for name, timeout in SOLVER_CASCADE:
            if name not in seen:
                ordered.append((name, timeout))
                seen.add(name)

        return ordered

    def _tactics_from_graph(
        self, goal: str, graph: SkillCategory
    ) -> list[str]:
        """Find solver names from tactic skills connected to relevant domains."""
        goal_lower = goal.lower()
        tactics = []

        for skill_id in graph.skill_ids:
            # Check if skill name appears in goal
            skill = graph.get_skill(skill_id)
            if not skill:
                continue

            # Match domain skill names against goal keywords
            name_tokens = skill.name.lower().replace("-", " ").split()
            if any(tok in goal_lower for tok in name_tokens if len(tok) > 3):
                # Found relevant domain — check its neighbors for tactic skills
                for nbr_id in graph.neighbors(skill_id):
                    if nbr_id in self._SKILL_TO_SOLVER:
                        solver = self._SKILL_TO_SOLVER[nbr_id]
                        if solver not in tactics:
                            tactics.append(solver)

        return tactics


@dataclass
class CascadeResult:
    """Result of running the solver cascade."""
    success: bool
    solver: Optional[str] = None
    replacement_code: Optional[str] = None
    solvers_tried: int = 0
    lean_result: Optional[LeanResult] = None


class SolverCascade:
    """
    Solver cascade for automated sorry resolution.

    Tries a sequence of Lean tactics to replace 'sorry' placeholders,
    from simplest (rfl) to most powerful (aesop).

    Example:
        cascade = SolverCascade(lean_client)

        # Try to fill a sorry
        result = await cascade.try_fill_sorry(
            code='theorem foo : 1 + 1 = 2 := by\\n  sorry',
            sorry_line=2,
        )
        if result.success:
            print(f"Solved with: {result.solver}")
    """

    def __init__(
        self,
        lean_client: LeanClient,
        solvers: Optional[list[tuple[str, int]]] = None,
        graph: Optional[SkillCategory] = None,
    ):
        self._lean = lean_client
        self._solvers = solvers or list(SOLVER_CASCADE)
        self._graph = graph
        self._goal_analyzer = GoalAnalyzer()

    async def try_fill_sorry(
        self,
        code: str,
        sorry_line: int,
        error_type: Optional[str] = None,
        imports: Optional[list[str]] = None,
    ) -> CascadeResult:
        """
        Try solver cascade to replace a sorry at a given line.

        Args:
            code: Full Lean source code containing sorry
            sorry_line: 1-indexed line number of the sorry
            error_type: If known, skip cascade for incompatible errors
            imports: Additional imports to prepend

        Returns:
            CascadeResult with success status and solver used
        """
        if error_type and error_type in SKIP_ERROR_TYPES:
            logger.debug(f"Skipping cascade for error type: {error_type}")
            return CascadeResult(success=False, solvers_tried=0)

        lines = code.split("\n")
        if sorry_line < 1 or sorry_line > len(lines):
            return CascadeResult(success=False, solvers_tried=0)

        target_line = lines[sorry_line - 1]
        if "sorry" not in target_line:
            return CascadeResult(success=False, solvers_tried=0)

        solvers_tried = 0
        for solver, _timeout in self._solvers:
            solvers_tried += 1
            modified_code = self._replace_sorry(lines, sorry_line - 1, solver)

            if imports:
                import_block = "\n".join(f"import {imp}" for imp in imports) + "\n\n"
                modified_code = import_block + modified_code

            logger.debug(f"Trying solver: {solver}")
            result = await self._lean.check_code(modified_code)

            if result.is_success:
                logger.info(f"Solver cascade: {solver} succeeded")
                return CascadeResult(
                    success=True,
                    solver=solver,
                    replacement_code=solver,
                    solvers_tried=solvers_tried,
                    lean_result=result,
                )

        logger.debug(f"Solver cascade exhausted after {solvers_tried} attempts")
        return CascadeResult(success=False, solvers_tried=solvers_tried)

    async def try_fill_sorry_smart(
        self,
        code: str,
        sorry_line: int,
        goal_text: str = "",
        error_type: Optional[str] = None,
        imports: Optional[list[str]] = None,
    ) -> CascadeResult:
        """
        Goal-aware solver cascade that reorders tactics by goal structure.

        Uses GoalAnalyzer to prioritize tactics based on the goal text
        and the skill graph, then runs the cascade in the optimized order.

        Args:
            code: Full Lean source code containing sorry
            sorry_line: 1-indexed line number of the sorry
            goal_text: The Lean goal to analyze for tactic ordering
            error_type: If known, skip cascade for incompatible errors
            imports: Additional imports to prepend

        Returns:
            CascadeResult with success status and solver used
        """
        if not goal_text:
            return await self.try_fill_sorry(code, sorry_line, error_type, imports)

        # Reorder solvers based on goal analysis
        smart_order = self._goal_analyzer.prioritize(goal_text, self._graph)
        logger.debug(
            f"Smart cascade order for goal: "
            f"{[s for s, _ in smart_order[:3]]}..."
        )

        # Temporarily swap solver order and run
        original_solvers = self._solvers
        self._solvers = smart_order
        try:
            result = await self.try_fill_sorry(code, sorry_line, error_type, imports)
        finally:
            self._solvers = original_solvers

        return result

    async def try_fill_theorem(
        self,
        name: str,
        statement: str,
        imports: Optional[list[str]] = None,
    ) -> CascadeResult:
        """
        Try solver cascade to prove a theorem automatically.

        Args:
            name: Theorem name
            statement: Theorem statement
            imports: Required imports

        Returns:
            CascadeResult with success status
        """
        import_lines = ""
        if imports:
            import_lines = "\n".join(f"import {imp}" for imp in imports) + "\n\n"

        solvers_tried = 0
        for solver, _timeout in self._solvers:
            solvers_tried += 1
            code = f"{import_lines}theorem {name} : {statement} := by\n  {solver}\n"

            result = await self._lean.check_code(code)

            if result.is_success:
                logger.info(f"Theorem {name} proved by: {solver}")
                return CascadeResult(
                    success=True,
                    solver=solver,
                    replacement_code=solver,
                    solvers_tried=solvers_tried,
                    lean_result=result,
                )

        return CascadeResult(success=False, solvers_tried=solvers_tried)

    async def try_multiple_sorries(
        self,
        code: str,
        sorry_lines: list[int],
    ) -> list[CascadeResult]:
        """
        Try cascade on multiple sorries in a file.

        Processes from last to first to avoid line shifts.

        Args:
            code: Full Lean source code
            sorry_lines: 1-indexed line numbers of sorries

        Returns:
            List of CascadeResults, one per sorry
        """
        results = []
        current_code = code

        # Process from last to first to preserve line numbers
        for line_num in sorted(sorry_lines, reverse=True):
            result = await self.try_fill_sorry(current_code, line_num)
            results.append(result)

            if result.success:
                # Update code with the fix for next iteration
                lines = current_code.split("\n")
                current_code = self._replace_sorry(
                    lines, line_num - 1, result.replacement_code
                )

        results.reverse()  # Return in original order
        return results

    def _replace_sorry(
        self, lines: list[str], line_idx: int, solver: str
    ) -> str:
        """Replace sorry with solver on the given line."""
        modified = list(lines)
        target = modified[line_idx]

        if "sorry" in target:
            modified[line_idx] = target.replace("sorry", solver, 1)
        else:
            # Fallback: append after 'by' on same or previous line
            indent = len(target) - len(target.lstrip())
            modified[line_idx] = target + "\n" + " " * (indent + 2) + solver

        return "\n".join(modified)
