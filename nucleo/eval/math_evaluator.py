"""
Math Evaluator - Answer Extraction and Verification
====================================================

Evaluates mathematical answers for correctness.
Supports numerical, symbolic, and LaTeX comparisons.

Based on InternLM-Math evaluation logic:
- Answer extraction from boxed expressions
- Numerical equality with tolerance
- Symbolic equality via sympy

Reference:
- InternLM-Math/agent/math_agent.py
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional, Union
from math import isclose


@dataclass
class MathAnswer:
    """Extracted mathematical answer."""
    raw: str                       # Original text
    normalized: str                # Cleaned/normalized form
    numeric_value: Optional[float] = None
    is_numeric: bool = False


@dataclass
class EvaluationResult:
    """Result of answer evaluation."""
    prediction: MathAnswer
    reference: MathAnswer
    is_correct: bool
    match_type: str  # exact, numeric, symbolic, none
    details: str = ""


class MathEvaluator:
    """
    Evaluates mathematical answers for correctness.

    Supports multiple comparison modes:
    - Exact string match (after normalization)
    - Numerical equality with tolerance
    - Symbolic equality (if sympy available)

    Example:
        evaluator = MathEvaluator()

        # Check if answer is correct
        result = evaluator.evaluate(
            prediction="\\boxed{42}",
            reference="42"
        )
        print(result.is_correct)  # True

        # Extract answer from solution
        answer = evaluator.extract_answer("The answer is \\boxed{x^2 + 1}")
        print(answer.normalized)  # "x^2 + 1"
    """

    def __init__(
        self,
        tolerance: float = 1e-4,
        include_percentage: bool = True,
        use_sympy: bool = True
    ):
        """
        Initialize the evaluator.

        Args:
            tolerance: Relative tolerance for numerical comparison
            include_percentage: Whether to check 100x and x/100 variants
            use_sympy: Whether to use symbolic comparison
        """
        self._tolerance = tolerance
        self._include_percentage = include_percentage
        self._use_sympy = use_sympy
        self._sympy_available = self._check_sympy()

    def _check_sympy(self) -> bool:
        """Check if sympy is available."""
        try:
            import sympy
            return True
        except ImportError:
            return False

    def extract_answer(self, text: str) -> MathAnswer:
        """
        Extract mathematical answer from text.

        Handles:
        - \\boxed{...} expressions
        - "The answer is: ..." patterns
        - Final numeric values

        Args:
            text: Text containing the answer

        Returns:
            Extracted and normalized answer
        """
        raw = ""

        # Try to extract from boxed
        if re.search(r'\\boxed|\\fbox', text):
            raw = self._extract_boxed(text)
        # Try "the answer is" pattern
        elif re.search(r'[Tt]he (final )?answer is:?', text):
            match = re.split(r'[Tt]he (final )?answer is:?', text)
            if match:
                raw = match[-1].strip().rstrip('.')
        # Fall back to last number
        else:
            numbers = re.findall(r'-?\d*\.?\d+', text.replace(',', ''))
            if numbers:
                raw = numbers[-1]

        normalized = self._normalize_string(raw)
        numeric_value, is_numeric = self._try_parse_numeric(normalized)

        return MathAnswer(
            raw=raw,
            normalized=normalized,
            numeric_value=numeric_value,
            is_numeric=is_numeric
        )

    def _extract_boxed(self, text: str) -> str:
        """Extract content from \\boxed{...} or \\fbox{...}."""
        # Find last boxed
        idx = text.rfind('\\boxed')
        if idx < 0:
            idx = text.rfind('\\fbox')
        if idx < 0:
            return ""

        # Find matching braces
        i = idx
        while i < len(text) and text[i] != '{':
            i += 1

        if i >= len(text):
            return ""

        brace_count = 0
        start = i + 1
        for j in range(i, len(text)):
            if text[j] == '{':
                brace_count += 1
            elif text[j] == '}':
                brace_count -= 1
                if brace_count == 0:
                    return text[start:j]

        return text[start:]

    def _normalize_string(self, s: str) -> str:
        """Normalize a mathematical string."""
        s = str(s).strip()

        # Remove newlines
        s = s.replace('\n', '')

        # Remove trailing dots
        s = s.rstrip('.')

        # Remove LaTeX spacing commands
        s = s.replace('\\!', '')
        s = s.replace('\\ ', '')
        s = s.replace('\\\\', '\\')

        # Normalize fractions
        s = s.replace('tfrac', 'frac')
        s = s.replace('dfrac', 'frac')

        # Remove \\left and \\right
        s = s.replace('\\left', '')
        s = s.replace('\\right', '')

        # Remove text units
        s = re.sub(r'\\text\{.*?\}$', '', s).strip()

        # Remove degrees
        s = s.replace('^{\\circ}', '')
        s = s.replace('^\\circ', '')

        # Remove currency
        s = s.replace('\\$', '')
        s = s.replace('$', '')

        # Remove percent
        s = s.replace('\\%', '')
        s = s.replace('%', '')

        # Fix decimals
        s = s.replace(' .', ' 0.')
        s = s.replace('{.', '{0.')
        if s and s[0] == '.':
            s = '0' + s

        # Remove cdot
        s = s.replace('\\cdot', '')

        # Handle infinity
        s = s.replace('infinity', '\\infty')
        if '\\infty' not in s:
            s = s.replace('inf', '\\infty')

        # Remove mbox
        s = re.sub(r'\\mbox\{.*?\}', '', s)

        # Complex numbers: j -> i
        if 'j' in s and 'i' not in s:
            s = s.replace('j', 'i')

        # Remove trailing zeros
        s = re.sub(r'(\d+)\.0+([^\d])', r'\1\2', s)
        s = re.sub(r'(\d+)\.0+$', r'\1', s)

        # Handle simple equations like "k = 5"
        if '=' in s:
            parts = s.split('=')
            if len(parts) == 2 and len(parts[0].strip()) <= 2:
                s = parts[1].strip()

        # Fix sqrt
        s = re.sub(r'\\sqrt(\w)', r'\\sqrt{\1}', s)

        # Remove spaces
        s = s.replace(' ', '')

        # Fix fractions
        s = self._fix_fracs(s)
        s = self._fix_slash(s)

        return s

    def _fix_fracs(self, s: str) -> str:
        """Fix malformed \\frac expressions."""
        if '\\frac' not in s:
            return s

        parts = s.split('\\frac')
        result = parts[0]

        for part in parts[1:]:
            result += '\\frac'
            if not part:
                continue

            if part[0] == '{':
                result += part
            elif len(part) >= 2:
                a, b = part[0], part[1]
                rest = part[2:] if len(part) > 2 else ""
                if b != '{':
                    result += '{' + a + '}{' + b + '}' + rest
                else:
                    result += '{' + a + '}' + b + rest
            else:
                result += part

        return result

    def _fix_slash(self, s: str) -> str:
        """Convert a/b to \\frac{a}{b} for simple cases."""
        if s.count('/') != 1:
            return s

        parts = s.split('/')
        if len(parts) != 2:
            return s

        a, b = parts
        try:
            if 'sqrt' not in a:
                int(a)
            if 'sqrt' not in b:
                int(b)
            return f'\\frac{{{a}}}{{{b}}}'
        except ValueError:
            return s

    def _try_parse_numeric(self, s: str) -> tuple[Optional[float], bool]:
        """Try to parse string as number."""
        try:
            value = float(s.replace(',', ''))
            return value, True
        except ValueError:
            return None, False

    def evaluate(
        self,
        prediction: str,
        reference: str,
        extract_answers: bool = True
    ) -> EvaluationResult:
        """
        Evaluate if prediction matches reference.

        Args:
            prediction: The predicted answer
            reference: The ground truth answer
            extract_answers: Whether to extract from boxed etc.

        Returns:
            Evaluation result with match details
        """
        if extract_answers:
            pred_answer = self.extract_answer(prediction)
            ref_answer = self.extract_answer(reference)
        else:
            pred_answer = MathAnswer(
                raw=prediction,
                normalized=self._normalize_string(prediction),
                *self._try_parse_numeric(self._normalize_string(prediction))
            )
            ref_answer = MathAnswer(
                raw=reference,
                normalized=self._normalize_string(reference),
                *self._try_parse_numeric(self._normalize_string(reference))
            )

        # Try different matching methods
        is_correct, match_type = self._compare_answers(pred_answer, ref_answer)

        return EvaluationResult(
            prediction=pred_answer,
            reference=ref_answer,
            is_correct=is_correct,
            match_type=match_type,
            details=f"Compared '{pred_answer.normalized}' with '{ref_answer.normalized}'"
        )

    def _compare_answers(
        self,
        pred: MathAnswer,
        ref: MathAnswer
    ) -> tuple[bool, str]:
        """Compare two answers using multiple methods."""
        # 1. Exact string match
        if pred.normalized == ref.normalized:
            return True, "exact"

        # 2. Numeric comparison
        if pred.is_numeric and ref.is_numeric:
            if self._numeric_equal(pred.numeric_value, ref.numeric_value):
                return True, "numeric"

        # 3. Remove brackets and compare
        pred_clean = self._remove_brackets(pred.normalized)
        ref_clean = self._remove_brackets(ref.normalized)
        if pred_clean == ref_clean:
            return True, "exact_cleaned"

        # 4. Symbolic comparison (if available)
        if self._use_sympy and self._sympy_available:
            if self._symbolic_equal(pred.normalized, ref.normalized):
                return True, "symbolic"

        return False, "none"

    def _numeric_equal(
        self,
        pred: Optional[float],
        ref: Optional[float]
    ) -> bool:
        """Check numeric equality with tolerance."""
        if pred is None or ref is None:
            return False

        targets = [ref]
        if self._include_percentage:
            targets.extend([ref / 100, ref * 100])

        for target in targets:
            try:
                if isclose(pred, target, rel_tol=self._tolerance):
                    return True
            except (TypeError, ValueError):
                continue

        return False

    def _remove_brackets(self, s: str) -> str:
        """Remove all brackets from string."""
        for char in '[](){}':
            s = s.replace(char, '')
        return s

    def _symbolic_equal(self, a: str, b: str) -> bool:
        """Check symbolic equality using sympy."""
        if not self._sympy_available:
            return False

        try:
            from sympy import simplify, N
            from sympy.parsing.latex import parse_latex
            from sympy.parsing.sympy_parser import parse_expr

            def parse(s):
                for f in [parse_latex, parse_expr]:
                    try:
                        return f(s)
                    except Exception:
                        pass
                return None

            pa = parse(a)
            pb = parse(b)

            if pa is None or pb is None:
                return False

            # Try simplify difference
            try:
                if simplify(pa - pb) == 0:
                    return True
            except Exception:
                pass

            # Try numeric comparison
            try:
                if isclose(float(N(pa)), float(N(pb)), rel_tol=1e-3):
                    return True
            except Exception:
                pass

        except Exception:
            pass

        return False

    def batch_evaluate(
        self,
        predictions: list[str],
        references: list[str]
    ) -> list[EvaluationResult]:
        """
        Evaluate a batch of predictions.

        Args:
            predictions: List of predictions
            references: List of ground truth answers

        Returns:
            List of evaluation results
        """
        if len(predictions) != len(references):
            raise ValueError("Predictions and references must have same length")

        return [
            self.evaluate(pred, ref)
            for pred, ref in zip(predictions, references)
        ]

    def compute_accuracy(self, results: list[EvaluationResult]) -> float:
        """Compute accuracy from results."""
        if not results:
            return 0.0
        correct = sum(1 for r in results if r.is_correct)
        return correct / len(results)


# Convenience functions

def extract_boxed_answer(text: str) -> str:
    """Extract answer from boxed expression."""
    evaluator = MathEvaluator()
    answer = evaluator.extract_answer(text)
    return answer.normalized


def check_math_equal(prediction: str, reference: str) -> bool:
    """Quick check if two math answers are equal."""
    evaluator = MathEvaluator()
    result = evaluator.evaluate(prediction, reference, extract_answers=False)
    return result.is_correct


def normalize_math_string(s: str) -> str:
    """Normalize a mathematical string."""
    evaluator = MathEvaluator()
    return evaluator._normalize_string(s)
