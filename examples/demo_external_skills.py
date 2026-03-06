#!/usr/bin/env python3
"""
Demo: External Skills Integration
=================================

Demonstrates the integration of skills extracted from:
- lean4-skills: Tactics database, sorry-filling strategies
- InternLM-Math: Mathematical answer evaluation

This example shows how the Nucleo system can leverage external
knowledge to improve theorem proving assistance.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add root to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def demo_tactics_database():
    """Demo: Tactics Database from lean4-skills."""
    print("=" * 60)
    print("Demo 1: Tactics Database (from lean4-skills)")
    print("=" * 60)
    print()

    from nucleo.lean.tactics_db import get_tactics_database, TacticCategory

    db = get_tactics_database()

    # Show statistics
    print(f"Database stats: {db.stats}")
    print()

    # Get tactic suggestions for various goals
    test_goals = [
        "forall x : Nat, x + 0 = x",
        "exists n : Nat, n > 5",
        "A -> B -> A /\\ B",
        "a <= b",
        "Continuous f",
        "Measurable g",
    ]

    print("Tactic suggestions by goal:")
    print("-" * 40)
    for goal in test_goals:
        suggestions = db.suggest_for_goal(goal)
        print(f"Goal: {goal[:40]}...")
        print(f"  -> {suggestions[:5]}")
        print()

    # Show quick reference
    print("Quick Reference Table:")
    print("-" * 40)
    for want, use in list(db.get_quick_reference().items())[:5]:
        print(f"  {want}: {use}")
    print()

    # Get info about a specific tactic
    simp = db.get_tactic("simp")
    if simp:
        print(f"Tactic 'simp' details:")
        print(f"  Category: {simp.category.name}")
        print(f"  When to use: {simp.when_to_use[:60]}...")
        print(f"  Variants: {simp.variants[:3]}")
    print()


def demo_sorry_filler():
    """Demo: Sorry Filler Strategy from lean4-skills."""
    print("=" * 60)
    print("Demo 2: Sorry Filler Strategy (from lean4-skills)")
    print("=" * 60)
    print()

    from nucleo.lean.sorry_filler import (
        SorryFiller,
        SorryContext,
        SorryType,
        classify_goal_type,
        suggest_tactics_for_goal,
    )

    filler = SorryFiller()

    # Test goal classification
    test_goals = [
        ("forall n : Nat, n + 0 = n", "forall"),
        ("exists x, x > 0", "exists"),
        ("A -> B", "implication"),
        ("P /\\ Q", "conjunction"),
        ("a = b", "equality"),
        ("x <= y", "inequality"),
    ]

    print("Goal Classification:")
    print("-" * 40)
    for goal, expected in test_goals:
        detected = classify_goal_type(goal)
        status = "[OK]" if detected == expected else "[?]"
        print(f"  {status} '{goal[:30]}...' -> {detected}")
    print()

    # Test sorry type classification
    print("Sorry Type Classification:")
    print("-" * 40)
    contexts = [
        SorryContext(
            file_path="Test.lean",
            line_number=10,
            goal="x + 0 = x",
            goal_type="equality",
            surrounding_code="theorem add_zero (x : Nat) : x + 0 = x := by sorry"
        ),
        SorryContext(
            file_path="Test.lean",
            line_number=20,
            goal="Continuous (fun x => x^2)",
            goal_type="continuous",
            surrounding_code="lemma cont_sq : Continuous (fun x => x^2) := by sorry"
        ),
        SorryContext(
            file_path="Test.lean",
            line_number=30,
            goal="P n -> P (n + 1)",
            goal_type="implication",
            surrounding_code="induction n with\n| zero => rfl\n| succ k ih => sorry"
        ),
    ]

    for ctx in contexts:
        sorry_type = filler.classify_sorry(ctx)
        print(f"  Goal: '{ctx.goal[:30]}...'")
        print(f"    Type: {sorry_type.name}")
        print()

    # Generate proof candidates
    print("Proof Candidate Generation:")
    print("-" * 40)
    ctx = SorryContext(
        file_path="Test.lean",
        line_number=42,
        goal="forall n : Nat, n + 0 = n",
        goal_type="forall"
    )

    candidates = filler.generate_candidates(ctx)
    for i, candidate in enumerate(candidates, 1):
        print(f"  Candidate {chr(64+i)} ({candidate.strategy}):")
        print(f"    Code: {candidate.code}")
        print(f"    Confidence: {candidate.confidence:.1%}")
        print()


def demo_math_evaluator():
    """Demo: Math Evaluator from InternLM-Math."""
    print("=" * 60)
    print("Demo 3: Math Evaluator (from InternLM-Math)")
    print("=" * 60)
    print()

    from nucleo.eval.math_evaluator import (
        MathEvaluator,
        extract_boxed_answer,
        check_math_equal,
    )

    evaluator = MathEvaluator()

    # Test answer extraction
    print("Answer Extraction:")
    print("-" * 40)
    test_texts = [
        "The answer is \\boxed{42}",
        "Therefore, we have \\boxed{x^2 + 1}",
        "The final answer is: 3.14159",
        "Computing... result = 100",
    ]

    for text in test_texts:
        answer = extract_boxed_answer(text)
        print(f"  Text: '{text[:40]}...'")
        print(f"    -> Answer: '{answer}'")
        print()

    # Test mathematical equality
    print("Mathematical Equality Checks:")
    print("-" * 40)
    test_pairs = [
        ("42", "42", True),
        ("3.14159", "3.14159", True),
        ("0.5", "1/2", True),  # May require sympy
        ("x^2 + 2x + 1", "(x+1)^2", True),  # May require sympy
        ("100", "99", False),
        ("\\frac{1}{2}", "0.5", True),
    ]

    for pred, ref, expected in test_pairs:
        result = evaluator.evaluate(pred, ref, extract_answers=False)
        status = "[OK]" if result.is_correct == expected else "[FAIL]"
        print(f"  {status} '{pred}' == '{ref}'")
        print(f"       Match: {result.is_correct} (type: {result.match_type})")
    print()

    # Batch evaluation
    print("Batch Evaluation:")
    print("-" * 40)
    predictions = ["\\boxed{4}", "\\boxed{9}", "\\boxed{16}"]
    references = ["4", "9", "15"]  # Last one wrong

    results = evaluator.batch_evaluate(predictions, references)
    accuracy = evaluator.compute_accuracy(results)
    print(f"  Predictions: {predictions}")
    print(f"  References:  {references}")
    print(f"  Accuracy: {accuracy:.1%}")
    print()


def demo_integrated_workflow():
    """Demo: Integrated workflow using all components."""
    print("=" * 60)
    print("Demo 4: Integrated Workflow")
    print("=" * 60)
    print()

    from nucleo.lean.tactics_db import get_tactics_database
    from nucleo.lean.sorry_filler import SorryFiller, SorryContext
    from nucleo.eval.math_evaluator import MathEvaluator

    print("Scenario: User asks to prove 'forall n, n + 0 = n'")
    print("-" * 50)

    # Step 1: Analyze the goal with tactics database
    db = get_tactics_database()
    goal = "forall n : Nat, n + 0 = n"

    print("\n1. Analyzing goal with TacticsDatabase...")
    suggestions = db.suggest_for_goal(goal)
    print(f"   Suggested tactics: {suggestions}")

    # Step 2: Generate proof candidates with SorryFiller
    print("\n2. Generating proof candidates with SorryFiller...")
    filler = SorryFiller()
    ctx = SorryContext(
        file_path="Example.lean",
        line_number=1,
        goal=goal,
        goal_type="forall"
    )

    candidates = filler.generate_candidates(ctx)
    for c in candidates:
        print(f"   {c.strategy}: {c.code}")

    # Step 3: Simulate testing (in real scenario, would use Lean)
    print("\n3. Testing candidates (simulated)...")
    test_results = [True, False, True]  # Simulated results
    result = filler.create_result(ctx, candidates, test_results)

    if result.chosen_solution:
        print(f"   [OK] Working solution: {result.chosen_solution.code}")
    else:
        print(f"   Escalation needed: {result.escalation_reason}")

    # Step 4: Evaluate mathematical correctness
    print("\n4. Evaluating mathematical answer...")
    evaluator = MathEvaluator()
    eval_result = evaluator.evaluate(
        "The result is n = n, which is \\boxed{true}",
        "true"
    )
    print(f"   Answer correct: {eval_result.is_correct}")
    print(f"   Match type: {eval_result.match_type}")

    print("\n" + "=" * 60)
    print("Integration complete!")
    print("=" * 60)


def main():
    """Run all demos."""
    print()
    print("*" * 60)
    print("* EXTERNAL SKILLS INTEGRATION DEMO")
    print("* Nucleo Logico Evolutivo")
    print("*" * 60)
    print()
    print("Skills integrated from:")
    print("  - lean4-skills: Tactics database, sorry-filling")
    print("  - InternLM-Math: Mathematical evaluation")
    print()

    demo_tactics_database()
    demo_sorry_filler()
    demo_math_evaluator()
    demo_integrated_workflow()


if __name__ == "__main__":
    main()
