"""
Tipos Base del Nucleo Logico Evolutivo
======================================

Define las estructuras de datos fundamentales del sistema:
- Skill: Unidad de conocimiento matematico
- Morphism: Relacion entre skills (dependencia, especializacion, etc.)
- State: Estado del MDP (contexto LLM, goal Lean, grafo, historial)
- Action: Acciones del agente (respuesta, reorganizacion, asistencia)

Version 7.0 - Extension MES (Memory Evolutive Systems):
- Pattern: Patron categorico (funtor P: I -> K)
- Colimit: Colimite de un patron
- CoRegulator: Co-reguladores del sistema
- ExperienceRecord: Registros de memoria
- EConcept: E-conceptos semanticos
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Optional
from datetime import datetime
import uuid


# =============================================================================
# ENUMS
# =============================================================================

class MorphismType(Enum):
    """
    Tipos de morfismos en la categoria de Skills.

    Definicion 4.2 del documento v6.0:
    - IDENTITY: Morfismo identidad (axioma categorico)
    - DEPENDENCY (->): t requiere s como prerrequisito
    - SPECIALIZATION (->>): t es caso especial de s
    - ANALOGY (<->): Isomorfismo parcial entre areas distintas
    - TRANSLATION (~>): Transformacion entre pilares fundacionales
    """
    IDENTITY = auto()        # id_s: s -> s (axioma categorico)
    DEPENDENCY = auto()      # s -> t: t requiere s
    SPECIALIZATION = auto()  # s ->> t: t especializa s
    ANALOGY = auto()         # s <-> t: isomorfismo parcial
    TRANSLATION = auto()     # s ~> t: entre pilares


class ActionType(Enum):
    """
    Tipos de acciones del agente RL.

    A = A_1 ⊔ A_2 ⊔ A_3
    """
    RESPONSE = auto()      # A_1: Responder al usuario
    REORGANIZE = auto()    # A_2: Reorganizar el grafo
    ASSIST = auto()        # A_3: Asistir con prueba Lean


class PillarType(Enum):
    """
    Los cuatro pilares fundacionales F.
    """
    SET = auto()      # F_Set: Teoria de Conjuntos
    CAT = auto()      # F_Cat: Teoria de Categorias
    LOG = auto()      # F_Log: Logica
    TYPE = auto()     # F_Type: Teoria de Tipos


class SkillStatus(Enum):
    """Estado de un skill en el grafo."""
    ACTIVE = auto()
    DEPRECATED = auto()
    PENDING_VERIFICATION = auto()


# =============================================================================
# ENUMS MES (v7.0 - Ehresmann & Vanbremeersch)
# =============================================================================

class CoRegulatorType(Enum):
    """
    Tipos de co-reguladores del NLE (Def. 4.1 v7.0).

    Red de co-reguladores {CR_k} que reemplaza el agente RL monolitico.
    """
    TACTICAL = auto()      # CR_tac: Nivel 0-1, cada interaccion
    ORGANIZATIONAL = auto()  # CR_org: Nivel 1-2, cada k interacciones
    STRATEGIC = auto()     # CR_str: Nivel 2-3, cada K sesiones
    INTEGRITY = auto()     # CR_int: Transversal, periodico


class MESActionType(Enum):
    """
    Acciones extendidas del MES (Def. 6.1 v7.0).

    A' = A_1 | A_2 | A_3 | A_4 (acciones MES)
    """
    # Acciones v6.0
    RESPONSE = auto()       # A_1: Responder al usuario
    REORGANIZE = auto()     # A_2: Reorganizar el grafo
    ASSIST = auto()         # A_3: Asistir con prueba Lean
    # Acciones MES v7.0
    COMPLEXIFY = auto()     # Complejificar: crear colimite de patron
    FORM_CONCEPT = auto()   # Formar E-concepto en memoria semantica
    CREATE_LEVEL = auto()   # Crear nuevo nivel jerarquico
    REPAIR_FRACTURE = auto()  # Reparar fractura detectada


class MemoryType(Enum):
    """
    Tipos de memoria en el NLE (Seccion 5.2 v7.0).
    """
    PROCEDURAL = auto()    # Secuencias de acciones exitosas
    SEMANTIC = auto()      # E-conceptos y sus relaciones
    CONSOLIDATED = auto()  # Registros fortalecidos con el tiempo
    EMPIRICAL = auto()     # Registros de experiencias concretas


class FractureType(Enum):
    """
    Tipos de fracturas en el sistema (Def. 7.4 v7.0).
    """
    TEMPORAL = auto()      # Discronia entre co-reguladores
    STRUCTURAL = auto()    # Violacion de invariante estructural
    LOGICAL = auto()       # Inconsistencia logica detectada


class LinkComplexity(Enum):
    """
    Complejidad de un enlace (Def 6.3 v7.0).

    - IDENTITY: Enlace identidad id_s
    - SIMPLE: Factoriza a traves de un unico cluster (colimite)
    - COMPLEX: Composicion de simples que NO factoriza por cluster adyacente
      (define emergencia - Thm 8.6)
    """
    IDENTITY = auto()
    SIMPLE = auto()
    COMPLEX = auto()


# =============================================================================
# SKILL
# =============================================================================

@dataclass
class Skill:
    """
    Unidad de conocimiento matematico en el grafo categorico.

    Cada skill es un objeto en la categoria Skill:
        Ob(Skill) = S (skills individuales)

    Version 7.0 (MES): Skills tienen nivel jerarquico.
    - Nivel 0: Atomos (axiomas, reglas basicas)
    - Nivel 1: Clusters (ZFC-axioms, FOL-rules, etc.)
    - Nivel 2: Habilidades (induccion, Curry-Howard)
    - Nivel 3: Competencias (Forcing, verificacion Lean)
    - Nivel >= 4: Meta-skills (traduccion entre pilares)

    Attributes:
        id: Identificador unico
        name: Nombre del skill
        description: Descripcion del skill
        pillar: Pilar fundacional al que pertenece
        level: Nivel jerarquico (0 = atomo, >= 1 = colimite)
        content: Contenido del skill (tacticas, lemas, etc.)
        metadata: Metadatos adicionales
        status: Estado del skill
        created_at: Fecha de creacion
        updated_at: Fecha de ultima actualizacion
        pattern_ids: IDs de skills que forman el patron (si es colimite)
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    pillar: Optional[PillarType] = None
    level: int = 0  # v7.0: Nivel jerarquico
    content: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    status: SkillStatus = SkillStatus.ACTIVE
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    pattern_ids: list[str] = field(default_factory=list)  # v7.0: componentes del patron

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Skill):
            return False
        return self.id == other.id


# =============================================================================
# MORPHISM
# =============================================================================

@dataclass
class Morphism:
    """
    Morfismo entre skills en la categoria.

    Hom(s, t) = transformaciones de s a t
    Cada morfismo tiene:
    - Tipo: dependencia, especializacion, analogia, traduccion
    - Peso: w(f) ∈ R+ indicando fuerza/utilidad

    Attributes:
        id: Identificador unico
        source: Skill origen
        target: Skill destino
        morphism_type: Tipo de morfismo
        weight: Peso del morfismo (fuerza de conexion)
        metadata: Metadatos adicionales
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    source_id: str = ""
    target_id: str = ""
    morphism_type: MorphismType = MorphismType.DEPENDENCY
    weight: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Morphism):
            return False
        return self.id == other.id


# =============================================================================
# INTERACTION
# =============================================================================

@dataclass
class Interaction:
    """
    Registro de una interaccion en el historial.

    Parte del estado x = (c_L, g_Lean, G, h, m)
    donde h ∈ H^k es el historial de las ultimas k interacciones.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    query: str = ""
    response: str = ""
    skills_used: list[str] = field(default_factory=list)
    lean_goal: Optional[str] = None
    lean_result: Optional[str] = None
    success: bool = False
    reward: float = 0.0


# =============================================================================
# STATE
# =============================================================================

@dataclass
class State:
    """
    Estado del sistema en el MDP.

    Definicion 5.2 del documento v6.0:
        x = (c_L, g_Lean, G, h, m)

    Attributes:
        llm_context: c_L ∈ R^d_c - Embedding del contexto del LLM
        lean_goal: g_Lean ∈ G ∪ {⊥} - Goal actual de Lean o None
        graph_snapshot: G = (S, Mor, w) - Snapshot del grafo actual
        history: h ∈ H^k - Historial de las ultimas k interacciones
        metrics: m ∈ R^p - Metricas de rendimiento acumuladas
    """
    llm_context: Optional[list[float]] = None  # Embedding vector
    lean_goal: Optional[str] = None
    graph_snapshot: dict[str, Any] = field(default_factory=dict)
    history: list[Interaction] = field(default_factory=list)
    metrics: dict[str, float] = field(default_factory=dict)

    @property
    def has_active_goal(self) -> bool:
        """Verifica si hay un goal de Lean activo."""
        return self.lean_goal is not None


# =============================================================================
# ACTION
# =============================================================================

@dataclass
class Action:
    """
    Accion del agente RL.

    A = A_1 ⊔ A_2 ⊔ A_3:
    - A_1 (RESPONSE): Responder al usuario
    - A_2 (REORGANIZE): Reorganizar el grafo
    - A_3 (ASSIST): Asistir con prueba Lean

    Attributes:
        action_type: Tipo de accion
        params: Parametros especificos de la accion
    """
    action_type: ActionType = ActionType.RESPONSE
    params: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def response(cls, content: str) -> Action:
        """Crear accion de respuesta."""
        return cls(
            action_type=ActionType.RESPONSE,
            params={"content": content}
        )

    @classmethod
    def reorganize(cls, operation: str, **kwargs: Any) -> Action:
        """Crear accion de reorganizacion del grafo."""
        return cls(
            action_type=ActionType.REORGANIZE,
            params={"operation": operation, **kwargs}
        )

    @classmethod
    def assist(cls, tactic: str, goal: str) -> Action:
        """Crear accion de asistencia con Lean."""
        return cls(
            action_type=ActionType.ASSIST,
            params={"tactic": tactic, "goal": goal}
        )


# =============================================================================
# REWARD COMPONENTS
# =============================================================================

@dataclass
class RewardComponents:
    """
    Componentes de la funcion de recompensa.

    v6.0: R(x, a) = r_task + l1*r_e + l2*r_org + l3*r_emerge
    v7.0: R'(x, a) = ... + l4*r_hier + l5*r_mem (Eq. 5)

    Attributes:
        r_task: Recompensa por exito de tarea {-5, -1, +1, +5, +10}
        r_efficiency: Penalizacion por ineficiencia
        r_organization: Bonus por mejorar estructura del grafo
        r_emergence: Bonus por descubrir patrones nuevos
        r_hierarchy: Bonus por formacion de niveles (v7.0)
        r_memory: Bonus por consolidacion de memoria (v7.0)
    """
    r_task: float = 0.0
    r_efficiency: float = 0.0
    r_organization: float = 0.0
    r_emergence: float = 0.0
    # v7.0 MES terms
    r_hierarchy: float = 0.0
    r_memory: float = 0.0

    def total(
        self,
        lambda_1: float = 0.1,
        lambda_2: float = 0.05,
        lambda_3: float = 0.2,
        lambda_4: float = 0.1,   # v7.0: peso jerarquia
        lambda_5: float = 0.08   # v7.0: peso memoria
    ) -> float:
        """Calcular recompensa total con pesos."""
        return (
            self.r_task +
            lambda_1 * self.r_efficiency +
            lambda_2 * self.r_organization +
            lambda_3 * self.r_emergence +
            lambda_4 * self.r_hierarchy +
            lambda_5 * self.r_memory
        )


# =============================================================================
# MES TYPES (v7.0 - Ehresmann & Vanbremeersch)
# =============================================================================

@dataclass
class Pattern:
    """
    Patron categorico P: I -> K (Def. 2.1 v7.0).

    Un patron es un funtor desde una categoria de indices finita I
    hacia la categoria de skills K. Los objetos P_i son los componentes
    y los morfismos son los enlaces distinguidos.

    Attributes:
        id: Identificador unico
        component_ids: IDs de los skills componentes (objetos del patron)
        distinguished_links: Morfismos entre componentes (enlaces del patron)
        is_homologous_to: IDs de patrones homologos (mismo campo operativo)
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    component_ids: list[str] = field(default_factory=list)
    distinguished_links: list[str] = field(default_factory=list)  # Morphism IDs
    is_homologous_to: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    # Functor data P: I → K (Def 2.1 v7.0)
    # I = index category, K = skill category
    index_objects: list[str] = field(default_factory=list)  # Ob(I)
    index_morphisms: dict[str, tuple[str, str]] = field(default_factory=dict)  # Mor(I): name → (src, tgt)
    functor_map_objects: dict[str, str] = field(default_factory=dict)  # P on objects: idx → skill_id
    functor_map_morphisms: dict[str, str] = field(default_factory=dict)  # P on morphisms: idx_mor → morph_id

    @property
    def size(self) -> int:
        """Numero de componentes del patron."""
        return len(self.component_ids)

    @property
    def is_diagram(self) -> bool:
        """True if this pattern has full functor data (is a proper diagram)."""
        return bool(self.index_objects) and bool(self.functor_map_objects)


@dataclass
class Colimit:
    """
    Colimite de un patron (Def. 2.2 v7.0).

    El colimite cP es un objeto junto con un co-cono (c_i: P_i -> cP)
    que satisface la propiedad universal.

    Attributes:
        id: Identificador unico
        pattern_id: ID del patron del cual es colimite
        skill_id: ID del skill que representa el colimite
        cocone_morphisms: Morfismos del co-cono (c_i: P_i -> cP)
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    pattern_id: str = ""
    skill_id: str = ""  # El skill que ES el colimite
    cocone_morphisms: list[str] = field(default_factory=list)  # Morphism IDs
    cocone_map: dict[str, str] = field(default_factory=dict)  # component_id → cocone_morphism_id
    universal_morphisms: dict[str, str] = field(default_factory=dict)  # target_id → mediating_morphism_id
    cocone_verified: bool = False
    universal_property_verified: bool = False
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class ExperienceRecord:
    """
    Registro de experiencia en la memoria (Def. 5.2 v7.0).

    Cada registro M codifica una interaccion exitosa con:
    - Patron P_M de skills activados
    - Enlace l_M: cP_M -> resultado
    - Marca temporal tau_M
    - Valor de exito v_M

    Attributes:
        id: Identificador unico
        pattern_id: ID del patron de skills activados
        outcome_link: Enlace al resultado
        timestamp: Marca temporal
        success_value: Valor de exito en [-1, 1]
        memory_type: Tipo de memoria
        consolidation_count: Veces que se ha consolidado
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    pattern_id: str = ""
    outcome_link: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    success_value: float = 0.0
    memory_type: MemoryType = MemoryType.EMPIRICAL
    consolidation_count: int = 0
    query: str = ""
    response: str = ""

    def consolidate(self) -> None:
        """Incrementar contador de consolidacion."""
        self.consolidation_count += 1
        if self.consolidation_count >= 3:
            self.memory_type = MemoryType.CONSOLIDATED


@dataclass
class EConcept:
    """
    E-concepto en la memoria semantica (Def. 5.3 v7.0).

    Clase de E-invariancia: registros funcionalmente equivalentes
    desde la perspectiva de un co-regulador.

    Attributes:
        id: Identificador unico
        representative_records: IDs de registros representantes
        equivalence_links: Enlaces de equivalencia funcional
        co_regulator_type: Co-regulador para el cual es invariante
        colimit_id: ID del colimite en memoria semantica
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    representative_records: list[str] = field(default_factory=list)
    equivalence_links: list[str] = field(default_factory=list)
    co_regulator_type: CoRegulatorType = CoRegulatorType.TACTICAL
    colimit_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class Fracture:
    """
    Fractura en el sistema (Def. 7.4 v7.0).

    Ocurre cuando el paisaje real difiere del anticipado.

    Attributes:
        id: Identificador unico
        fracture_type: Tipo de fractura
        co_regulator: Co-regulador que la detecto
        anticipated_state: Estado anticipado
        actual_state: Estado real
        timestamp: Cuando ocurrio
        repaired: Si fue reparada
        repair_action: Accion de reparacion tomada
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    fracture_type: FractureType = FractureType.STRUCTURAL
    co_regulator: CoRegulatorType = CoRegulatorType.INTEGRITY
    anticipated_state: dict[str, Any] = field(default_factory=dict)
    actual_state: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    repaired: bool = False
    repair_action: Optional[str] = None


@dataclass
class Option:
    """
    Opcion sobre una categoria (Def. 2.9 v7.0).

    Lista de objetivos para una complejificacion:
    - Absorcion: elementos externos a incorporar
    - Eliminacion: objetos a eliminar
    - Ligadura: patrones que deben adquirir colimite
    - Clasificacion: patrones que deben adquirir limite

    Attributes:
        id: Identificador unico
        absorptions: Skills externos a incorporar
        eliminations: Skills a eliminar
        bindings: Patrones a ligar (crear colimite)
        classifications: Patrones a clasificar (crear limite)
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    absorptions: list[str] = field(default_factory=list)  # Skill IDs
    eliminations: list[str] = field(default_factory=list)  # Skill IDs
    bindings: list[str] = field(default_factory=list)  # Pattern IDs
    classifications: list[str] = field(default_factory=list)  # Pattern IDs
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
