#!/usr/bin/env python3
"""
Script de Migracion de Skills
=============================

Migra los skills existentes en agents/skills/ al formato
del grafo categorico del Nucleo Logico Evolutivo.

Uso:
    python scripts/migrate_skills.py [--output OUTPUT_PATH]
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Optional, Dict, Any, List

from nucleo.types import Skill, MorphismType, PillarType
from nucleo.graph.category import SkillCategory
from nucleo.graph.operations import GraphOperations


# Mapeo de skills a pilares
SKILL_PILLAR_MAP = {
    # Theorem Proving -> F_Type
    "lean-tp-foundations": PillarType.TYPE,
    "lean-tp-propositions": PillarType.LOG,
    "lean-tp-quantifiers": PillarType.LOG,
    "lean-tp-tactics": PillarType.TYPE,
    "lean-tp-tactic-selection": PillarType.TYPE,
    "lean-tp-advanced": PillarType.TYPE,
    # Functional Programming -> F_Type/F_Cat
    "lean-fp-basics": PillarType.TYPE,
    "lean-fp-type-classes": PillarType.CAT,
    "lean-fp-dependent-types": PillarType.TYPE,
    "lean-fp-functor-applicative": PillarType.CAT,
    "lean-fp-monads": PillarType.CAT,
    "lean-fp-transformers": PillarType.CAT,
    "lean-fp-performance": PillarType.TYPE,
    # Reference -> General
    "lean-quick-reference": None,
}

# Dependencias entre skills
SKILL_DEPENDENCIES = {
    "lean-tp-propositions": ["lean-tp-foundations"],
    "lean-tp-quantifiers": ["lean-tp-propositions"],
    "lean-tp-tactics": ["lean-tp-foundations"],
    "lean-tp-tactic-selection": ["lean-tp-tactics"],
    "lean-tp-advanced": ["lean-tp-tactics", "lean-tp-tactic-selection"],
    "lean-fp-type-classes": ["lean-fp-basics"],
    "lean-fp-dependent-types": ["lean-fp-basics"],
    "lean-fp-functor-applicative": ["lean-fp-type-classes"],
    "lean-fp-monads": ["lean-fp-functor-applicative"],
    "lean-fp-transformers": ["lean-fp-monads"],
    "lean-fp-performance": ["lean-fp-basics"],
}


def parse_skill_md(skill_path: Path) -> Dict[str, Any]:
    """
    Parsear archivo SKILL.md.

    Returns:
        Dict con name, description, metadata
    """
    skill_file = skill_path / "SKILL.md"
    if not skill_file.exists():
        return {}

    content = skill_file.read_text(encoding="utf-8")

    # Extraer nombre (primer heading)
    name_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    name = name_match.group(1) if name_match else skill_path.name

    # Extraer descripcion (primer parrafo despues del heading)
    desc_match = re.search(r"^#.+\n\n(.+?)(?:\n\n|$)", content, re.DOTALL)
    description = desc_match.group(1).strip() if desc_match else ""

    # Extraer secciones
    sections = {}
    section_pattern = re.compile(r"^##\s+(.+)$", re.MULTILINE)
    matches = list(section_pattern.finditer(content))

    for i, match in enumerate(matches):
        section_name = match.group(1).lower().replace(" ", "_")
        start = match.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
        sections[section_name] = content[start:end].strip()

    return {
        "name": name,
        "description": description,
        "sections": sections,
        "path": str(skill_path),
    }


def discover_skills(base_path: Path) -> List[Path]:
    """
    Descubrir todos los skills en el directorio.

    Returns:
        Lista de paths a directorios de skills
    """
    skills_dir = base_path / "agents" / "skills"
    if not skills_dir.exists():
        return []

    return [
        d for d in skills_dir.iterdir()
        if d.is_dir() and (d / "SKILL.md").exists()
    ]


def migrate_skills(base_path: Path) -> SkillCategory:
    """
    Migrar skills existentes al grafo categorico.

    Args:
        base_path: Ruta base del proyecto

    Returns:
        SkillCategory con skills migrados
    """
    graph = SkillCategory(name="MigratedSkills")

    # Descubrir skills
    skill_paths = discover_skills(base_path)
    print(f"Encontrados {len(skill_paths)} skills")

    # Parsear y crear nodos
    skill_data = {}
    for skill_path in skill_paths:
        skill_id = skill_path.name
        data = parse_skill_md(skill_path)

        if not data:
            print(f"  [SKIP] {skill_id}: No SKILL.md encontrado")
            continue

        # Determinar pilar
        pillar = SKILL_PILLAR_MAP.get(skill_id)

        # Crear skill
        skill = Skill(
            id=skill_id,
            name=data.get("name", skill_id),
            description=data.get("description", ""),
            pillar=pillar,
            metadata={
                "source": "migration",
                "path": data.get("path"),
                "sections": list(data.get("sections", {}).keys()),
            }
        )

        graph.add_skill(skill)
        skill_data[skill_id] = data
        print(f"  [OK] {skill_id} -> {pillar.name if pillar else 'None'}")

    # Crear morfismos de dependencia
    print("\nCreando morfismos de dependencia...")
    for skill_id, deps in SKILL_DEPENDENCIES.items():
        if skill_id not in graph.skill_ids:
            continue

        for dep_id in deps:
            if dep_id not in graph.skill_ids:
                continue

            morphism = graph.add_morphism(
                source_id=dep_id,
                target_id=skill_id,
                morphism_type=MorphismType.DEPENDENCY,
                weight=1.0
            )
            if morphism:
                print(f"  {dep_id} -> {skill_id}")

    # Crear morfismos de traduccion entre pilares
    print("\nCreando morfismos de traduccion entre pilares...")
    pillar_skills = {}
    for skill in graph.skills:
        if skill.pillar:
            if skill.pillar not in pillar_skills:
                pillar_skills[skill.pillar] = []
            pillar_skills[skill.pillar].append(skill.id)

    # Conectar skills de LOG con TYPE (Curry-Howard)
    if PillarType.LOG in pillar_skills and PillarType.TYPE in pillar_skills:
        for log_skill in pillar_skills[PillarType.LOG][:2]:  # Primeros 2
            for type_skill in pillar_skills[PillarType.TYPE][:2]:
                graph.add_morphism(
                    source_id=log_skill,
                    target_id=type_skill,
                    morphism_type=MorphismType.TRANSLATION,
                    weight=0.8,
                    metadata={"translation": "curry_howard"}
                )
                print(f"  {log_skill} ~> {type_skill} (Curry-Howard)")

    # Conectar skills de CAT con TYPE
    if PillarType.CAT in pillar_skills and PillarType.TYPE in pillar_skills:
        for cat_skill in pillar_skills[PillarType.CAT][:2]:
            for type_skill in pillar_skills[PillarType.TYPE][:2]:
                graph.add_morphism(
                    source_id=cat_skill,
                    target_id=type_skill,
                    morphism_type=MorphismType.TRANSLATION,
                    weight=0.7,
                    metadata={"translation": "universes"}
                )
                print(f"  {cat_skill} ~> {type_skill} (Universos)")

    return graph


def main():
    parser = argparse.ArgumentParser(description="Migrar skills al grafo categorico")
    parser.add_argument(
        "--base",
        type=Path,
        default=Path.cwd(),
        help="Ruta base del proyecto"
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/migrated_graph.json"),
        help="Ruta de salida para el grafo"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("Migracion de Skills al Grafo Categorico")
    print("=" * 60)
    print()

    # Migrar
    graph = migrate_skills(args.base)

    # Mostrar estadisticas
    print()
    print("=" * 60)
    print("Estadisticas del Grafo")
    print("=" * 60)
    stats = graph.stats
    print(f"  Skills: {stats['num_skills']}")
    print(f"  Morfismos: {stats['num_morphisms']}")
    print(f"  Peso total: {stats['total_weight']:.2f}")
    print(f"  Conectado: {'Si' if graph.is_connected() else 'No'}")

    # Guardar
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(graph.to_dict(), f, indent=2)

    print()
    print(f"Grafo guardado en: {args.output}")

    # Verificar axiomas
    print()
    print("Verificacion de axiomas:")
    axioms = graph.verify_axioms()
    for axiom, passed in axioms.items():
        status = "PASS" if passed else "FAIL"
        print(f"  {axiom}: {status}")


if __name__ == "__main__":
    main()
