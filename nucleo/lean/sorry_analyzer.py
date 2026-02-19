"""
Sorry Analyzer - Static Analysis of Incomplete Proofs
=====================================================

Adapted from lean4-skills/plugins/lean4-theorem-proving/scripts/sorry_analyzer.py

Finds all 'sorry' instances in Lean files and extracts:
- Location (file, line number)
- Context (surrounding code)
- Documentation (TODO/NOTE comments)
- Declaration info (theorem/lemma/def name)

Used by the NLE to:
1. Identify proof obligations
2. Feed sorry contexts to solver cascade
3. Track proof progress in MES memory
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


@dataclass
class SorryInfo:
    """A sorry instance with full context for automated resolution."""
    file: str
    line: int
    context_before: list[str] = field(default_factory=list)
    context_after: list[str] = field(default_factory=list)
    documentation: list[str] = field(default_factory=list)
    in_declaration: Optional[str] = None

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SorryReport:
    """Summary report of sorries in a codebase."""
    total_count: int
    sorries: list[SorryInfo]
    files_scanned: int = 0

    @property
    def by_file(self) -> dict[str, list[SorryInfo]]:
        grouped: dict[str, list[SorryInfo]] = {}
        for sorry in self.sorries:
            grouped.setdefault(sorry.file, []).append(sorry)
        return grouped

    @property
    def declarations_with_sorry(self) -> list[str]:
        return [
            s.in_declaration for s in self.sorries
            if s.in_declaration is not None
        ]


def _extract_declaration_name(lines: list[str], sorry_idx: int) -> Optional[str]:
    """Extract the theorem/lemma/def name containing this sorry."""
    for i in range(sorry_idx - 1, max(0, sorry_idx - 50) - 1, -1):
        match = re.match(r'^\s*(theorem|lemma|def|example)\s+(\w+)', lines[i])
        if match:
            return f"{match.group(1)} {match.group(2)}"
    return None


def _extract_documentation(lines: list[str], sorry_idx: int) -> list[str]:
    """Extract TODO/NOTE comments near the sorry."""
    docs = []
    for i in range(sorry_idx + 1, min(len(lines), sorry_idx + 10)):
        line = lines[i].strip()
        if line.startswith('--'):
            comment = line[2:].strip()
            if any(kw in comment.upper() for kw in ['TODO', 'NOTE', 'FIXME', 'STRATEGY', 'DEPENDENCIES']):
                docs.append(comment)
        elif line and not line.startswith('--'):
            break
    return docs


def find_sorries_in_text(text: str, file_path: str = "<string>") -> list[SorryInfo]:
    """
    Find all sorries in Lean source text.

    Args:
        text: Lean source code
        file_path: Path to use in SorryInfo (for display)

    Returns:
        List of SorryInfo for each sorry found
    """
    lines = text.split("\n")
    sorries = []

    for i, line in enumerate(lines):
        # Look for sorry not in comments
        if 'sorry' in line:
            code_part = line.split('--')[0]
            if 'sorry' in code_part:
                context_before = [l.rstrip() for l in lines[max(0, i - 3):i]]
                context_after = [l.rstrip() for l in lines[i + 1:min(len(lines), i + 4)]]

                sorry = SorryInfo(
                    file=file_path,
                    line=i + 1,
                    context_before=context_before,
                    context_after=context_after,
                    documentation=_extract_documentation(lines, i),
                    in_declaration=_extract_declaration_name(lines, i),
                )
                sorries.append(sorry)

    return sorries


def find_sorries_in_file(filepath: Path) -> list[SorryInfo]:
    """Find all sorries in a Lean file."""
    try:
        text = filepath.read_text(encoding='utf-8')
    except Exception:
        return []
    return find_sorries_in_text(text, str(filepath))


def find_sorries_in_directory(
    directory: Path,
    include_deps: bool = False,
) -> list[SorryInfo]:
    """
    Find all sorries in a directory of Lean files.

    Args:
        directory: Directory to search
        include_deps: Include .lake/ directories

    Returns:
        List of SorryInfo across all files
    """
    import os
    sorries = []

    for root, dirs, files in os.walk(directory):
        if not include_deps:
            dirs[:] = [d for d in dirs if d != '.lake']

        for filename in files:
            if filename.endswith('.lean'):
                filepath = Path(root) / filename
                sorries.extend(find_sorries_in_file(filepath))

    return sorries


def analyze_sorries(
    target: Path,
    include_deps: bool = False,
) -> SorryReport:
    """
    Analyze sorries in a file or directory.

    Args:
        target: File or directory to analyze
        include_deps: Include .lake/ directories

    Returns:
        SorryReport with analysis
    """
    if target.is_file():
        sorries = find_sorries_in_file(target)
        files_scanned = 1
    elif target.is_dir():
        sorries = find_sorries_in_directory(target, include_deps)
        import os
        files_scanned = sum(
            1 for _, _, files in os.walk(target)
            for f in files if f.endswith('.lean')
        )
    else:
        return SorryReport(total_count=0, sorries=[], files_scanned=0)

    return SorryReport(
        total_count=len(sorries),
        sorries=sorries,
        files_scanned=files_scanned,
    )
