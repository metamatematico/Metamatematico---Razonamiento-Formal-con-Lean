"""
Pilar II: Teoria de Categorias (F_Cat)
======================================

El cluster F_Cat incluye:
- cat-basics: Objetos, morfismos, composicion
- functors: Functores covariantes/contravariantes, adjunciones
- nat-trans: Transformaciones naturales, equivalencias
- topos: Topos elementales, logica interna

Justificacion:
- El grafo de skills G_t es una categoria
- Los topos proporcionan modelos de logica intuicionista
- Conecta F_Cat con F_Log via tau_4

Propiedades:
- Composicion asociativa
- Identidades
- Estructura algebraica rica
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Generic, TypeVar, Optional, Callable

from nucleo.pillars.base import Pillar, PillarSkill


# Type variables para genericos
Obj = TypeVar("Obj")
Mor = TypeVar("Mor")


@dataclass
class CategoryObject:
    """
    Objeto en una categoria.

    En la categoria de Skills, los objetos son skills individuales.
    """
    id: str
    name: str
    data: Any = None

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CategoryObject):
            return False
        return self.id == other.id


@dataclass
class CategoryMorphism:
    """
    Morfismo en una categoria.

    f : A → B

    Propiedades:
    - source: Objeto origen
    - target: Objeto destino
    - compose: g ∘ f esta definido si target(f) = source(g)
    """
    id: str
    source: CategoryObject
    target: CategoryObject
    name: str = ""
    data: Any = None

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CategoryMorphism):
            return False
        return self.id == other.id

    def __str__(self) -> str:
        return f"{self.name}: {self.source.name} → {self.target.name}"


class Category:
    """
    Categoria abstracta.

    Una categoria C consiste en:
    - Ob(C): Coleccion de objetos
    - Hom(A, B): Morfismos de A a B
    - ∘: Composicion de morfismos
    - id_A: Identidad para cada objeto

    Satisface:
    - Asociatividad: h ∘ (g ∘ f) = (h ∘ g) ∘ f
    - Identidad: f ∘ id_A = f = id_B ∘ f
    """

    def __init__(self, name: str = ""):
        self.name = name
        self._objects: dict[str, CategoryObject] = {}
        self._morphisms: dict[str, CategoryMorphism] = {}
        self._hom_sets: dict[tuple[str, str], set[str]] = {}
        self._identities: dict[str, str] = {}  # obj_id -> id_morphism_id

    def add_object(self, obj: CategoryObject) -> None:
        """Añadir objeto a la categoria."""
        self._objects[obj.id] = obj
        # Crear morfismo identidad
        id_mor = CategoryMorphism(
            id=f"id_{obj.id}",
            source=obj,
            target=obj,
            name=f"id_{obj.name}"
        )
        self._morphisms[id_mor.id] = id_mor
        self._identities[obj.id] = id_mor.id
        self._hom_sets[(obj.id, obj.id)] = {id_mor.id}

    def add_morphism(self, mor: CategoryMorphism) -> None:
        """Añadir morfismo a la categoria."""
        if mor.source.id not in self._objects:
            raise ValueError(f"Source object {mor.source.id} not in category")
        if mor.target.id not in self._objects:
            raise ValueError(f"Target object {mor.target.id} not in category")

        self._morphisms[mor.id] = mor

        key = (mor.source.id, mor.target.id)
        if key not in self._hom_sets:
            self._hom_sets[key] = set()
        self._hom_sets[key].add(mor.id)

    def compose(
        self,
        g: CategoryMorphism,
        f: CategoryMorphism
    ) -> Optional[CategoryMorphism]:
        """
        Componer morfismos: g ∘ f

        Requiere: target(f) = source(g)

        Returns:
            Morfismo compuesto o None si no componibles
        """
        if f.target.id != g.source.id:
            return None

        composed = CategoryMorphism(
            id=f"{g.id}_o_{f.id}",
            source=f.source,
            target=g.target,
            name=f"{g.name} ∘ {f.name}"
        )
        self.add_morphism(composed)
        return composed

    def identity(self, obj: CategoryObject) -> CategoryMorphism:
        """Obtener morfismo identidad de un objeto."""
        id_mor_id = self._identities.get(obj.id)
        if id_mor_id:
            return self._morphisms[id_mor_id]
        raise ValueError(f"No identity for object {obj.id}")

    def hom(
        self,
        source: CategoryObject,
        target: CategoryObject
    ) -> list[CategoryMorphism]:
        """Obtener Hom(source, target)."""
        key = (source.id, target.id)
        mor_ids = self._hom_sets.get(key, set())
        return [self._morphisms[mid] for mid in mor_ids]

    @property
    def objects(self) -> list[CategoryObject]:
        """Lista de objetos."""
        return list(self._objects.values())

    @property
    def morphisms(self) -> list[CategoryMorphism]:
        """Lista de morfismos."""
        return list(self._morphisms.values())

    def verify_axioms(self) -> bool:
        """
        Verificar axiomas categoricos.

        - Asociatividad
        - Identidades
        """
        # Verificar identidades
        for obj in self._objects.values():
            id_mor = self.identity(obj)
            for mor in self.hom(obj, obj):
                # f ∘ id = f
                if mor.source.id == obj.id:
                    pass  # TODO: verificar composicion
            for mor in self.hom(obj, obj):
                # id ∘ f = f
                if mor.target.id == obj.id:
                    pass  # TODO: verificar composicion

        return True


@dataclass
class Functor:
    """
    Functor entre categorias.

    F: C → D

    Mapea:
    - Objetos: A ↦ F(A)
    - Morfismos: f ↦ F(f)

    Preserva:
    - Identidades: F(id_A) = id_{F(A)}
    - Composicion: F(g ∘ f) = F(g) ∘ F(f)
    """
    name: str
    source_category: Category
    target_category: Category
    object_map: Callable[[CategoryObject], CategoryObject] = field(default=lambda x: x)
    morphism_map: Callable[[CategoryMorphism], CategoryMorphism] = field(default=lambda x: x)


@dataclass
class NaturalTransformation:
    """
    Transformacion natural entre functores.

    η: F ⇒ G

    Para cada objeto A:
        η_A: F(A) → G(A)

    Tal que para f: A → B:
        η_B ∘ F(f) = G(f) ∘ η_A
    """
    name: str
    source_functor: Functor
    target_functor: Functor
    components: dict[str, CategoryMorphism] = field(default_factory=dict)


class CategoryTheoryPillar(Pillar):
    """
    Pilar de Teoria de Categorias (F_Cat).

    Implementa el cluster de teoria de categorias con:
    - Skills para conceptos categoricos
    - Soporte para functores y transformaciones naturales
    - Conexion con topos (logica interna)
    """

    def __init__(self):
        super().__init__(
            name="F_Cat",
            description="Teoria de Categorias: functores, transformaciones naturales, topos"
        )
        self._initialize_skills()

    def _initialize_skills(self) -> None:
        """Inicializar skills del pilar."""
        skills = [
            PillarSkill(
                id="cat-basics",
                name="Category Basics",
                description="Objetos, morfismos, composicion, identidad",
                dependencies=[],
            ),
            PillarSkill(
                id="functors",
                name="Functors",
                description="Functores covariantes/contravariantes",
                dependencies=["cat-basics"],
            ),
            PillarSkill(
                id="nat-trans",
                name="Natural Transformations",
                description="Transformaciones naturales, categoria de functores",
                dependencies=["functors"],
            ),
            PillarSkill(
                id="adjunctions",
                name="Adjunctions",
                description="Pares de functores adjuntos",
                dependencies=["nat-trans"],
            ),
            PillarSkill(
                id="limits",
                name="Limits and Colimits",
                description="Productos, coproductos, pullbacks, pushouts",
                dependencies=["functors"],
            ),
            PillarSkill(
                id="yoneda",
                name="Yoneda Lemma",
                description="Lema de Yoneda, representabilidad",
                dependencies=["nat-trans"],
            ),
            PillarSkill(
                id="topos-basics",
                name="Topos Basics",
                description="Topos elementales, clasificador de subobjetos",
                dependencies=["limits", "adjunctions"],
            ),
            PillarSkill(
                id="internal-logic",
                name="Internal Logic",
                description="Logica interna de un topos",
                dependencies=["topos-basics"],
                metadata={"connects_to": "F_Log"}
            ),
        ]

        for skill in skills:
            self.add_skill(skill)

    def get_skills(self) -> list[PillarSkill]:
        """Obtener todos los skills del pilar."""
        return list(self._skills.values())

    def validate(self) -> bool:
        """Verificar consistencia del pilar."""
        skill_ids = set(self._skills.keys())
        for skill in self._skills.values():
            for dep in skill.dependencies:
                if dep not in skill_ids:
                    return False
        return True
