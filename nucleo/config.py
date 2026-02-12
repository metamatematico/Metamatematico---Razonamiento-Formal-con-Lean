"""
Configuracion Global del Nucleo Logico Evolutivo
=================================================

Hiperparametros y configuracion del sistema.
Basado en Seccion 5.2 del documento v6.0.

Version 7.0 - Extension MES (Seccion 9.3):
- lambda_4: Peso jerarquia [0.05, 0.3]
- lambda_5: Peso memoria [0.03, 0.2]
- k: Frecuencia CRorg [5, 50]
- K: Frecuencia CRstr [50, 500]
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional
import yaml


@dataclass
class RLConfig:
    """
    Configuracion del Aprendizaje por Refuerzo.

    Hiperparametros recomendados (Tabla 5.2 v6.0 + Seccion 9.3 v7.0):
    - gamma: Factor de descuento [0.95, 0.999]
    - lambda_1: Peso eficiencia [0.01, 0.5]
    - lambda_2: Peso organizacion [0.01, 0.2]
    - lambda_3: Peso emergencia [0.1, 0.5]
    - lambda_4: Peso jerarquia [0.05, 0.3] (v7.0)
    - lambda_5: Peso memoria [0.03, 0.2] (v7.0)
    - history_size: Tamano del historial [5, 50]
    """
    # Factor de descuento (alto: efectos a largo plazo importan)
    gamma: float = 0.99

    # Pesos de recompensa v6.0
    lambda_1: float = 0.1   # Eficiencia (bajo: no sacrificar calidad)
    lambda_2: float = 0.05  # Organizacion (bajo: cambios graduales)
    lambda_3: float = 0.2   # Emergencia (moderado: fomentar exploracion)

    # Pesos de recompensa v7.0 MES
    lambda_4: float = 0.1   # Jerarquia: fomentar formacion de niveles
    lambda_5: float = 0.08  # Memoria: incentivar consolidacion gradual

    # Penalizaciones
    alpha: float = 0.1   # Penalizacion por skill usado
    beta: float = 0.01   # Penalizacion por tiempo

    # Historial
    history_size: int = 10

    # PPO
    learning_rate: float = 3e-4
    batch_size: int = 64
    n_epochs: int = 10
    clip_range: float = 0.2

    # Epsilon-greedy
    epsilon_start: float = 1.0
    epsilon_end: float = 0.1
    epsilon_decay: float = 0.995

    def validate(self) -> None:
        """Validar rangos de hiperparametros."""
        assert 0.95 <= self.gamma <= 0.999, f"gamma fuera de rango: {self.gamma}"
        assert 0.01 <= self.lambda_1 <= 0.5, f"lambda_1 fuera de rango: {self.lambda_1}"
        assert 0.01 <= self.lambda_2 <= 0.2, f"lambda_2 fuera de rango: {self.lambda_2}"
        assert 0.1 <= self.lambda_3 <= 0.5, f"lambda_3 fuera de rango: {self.lambda_3}"
        assert 0.05 <= self.lambda_4 <= 0.3, f"lambda_4 fuera de rango: {self.lambda_4}"
        assert 0.03 <= self.lambda_5 <= 0.2, f"lambda_5 fuera de rango: {self.lambda_5}"
        assert 5 <= self.history_size <= 50, f"history_size fuera de rango: {self.history_size}"


@dataclass
class LeanConfig:
    """Configuracion de integracion con Lean 4."""
    # Ruta al ejecutable de Lean
    lean_path: str = "lake"

    # Timeout para comandos (ms)
    timeout_ms: int = 30000

    # Proyecto Lean
    project_path: Optional[str] = None

    # Mathlib
    use_mathlib: bool = True
    mathlib_cache: bool = True


@dataclass
class GraphConfig:
    """Configuracion del grafo categorico jerarquico (v7.0)."""
    # Numero maximo de skills
    max_skills: int = 100000

    # Peso inicial de morfismos
    default_weight: float = 1.0

    # Decaimiento de pesos no usados
    weight_decay: float = 0.99

    # GNN
    gnn_hidden_dim: int = 256
    gnn_num_layers: int = 3
    gnn_dropout: float = 0.1

    # v7.0: Jerarquia
    max_levels: int = 10  # Numero maximo de niveles jerarquicos
    min_pattern_size: int = 2  # Minimo componentes para formar colimite


@dataclass
class MESConfig:
    """
    Configuracion del Sistema Evolutivo con Memoria (v7.0).

    Parametros para co-reguladores y memoria segun Seccion 9.3.
    """
    # Frecuencias de co-reguladores
    cr_org_frequency: int = 10    # k: CRorg cada k interacciones [5, 50]
    cr_str_frequency: int = 100   # K: CRstr cada K sesiones [50, 500]
    cr_int_period: int = 50       # Periodo de verificacion de integridad

    # Memoria
    max_records: int = 10000      # Maximo registros en memoria empirica
    consolidation_threshold: int = 3  # Accesos para consolidar
    econcept_min_records: int = 5     # Minimo registros para formar E-concepto

    # Complejificacion
    colimit_threshold: float = 0.8   # Umbral de coherencia para crear colimite
    pattern_similarity: float = 0.7  # Umbral para detectar patrones homologos

    # Fracturas
    fracture_check_interval: int = 10  # Cada cuantos pasos verificar fracturas
    max_repair_attempts: int = 3       # Intentos de reparacion antes de escalar

    def validate(self) -> None:
        """Validar rangos de hiperparametros MES."""
        assert 5 <= self.cr_org_frequency <= 50, f"k fuera de rango: {self.cr_org_frequency}"
        assert 50 <= self.cr_str_frequency <= 500, f"K fuera de rango: {self.cr_str_frequency}"


@dataclass
class LLMConfig:
    """Configuracion del LLM (Claude)."""
    # Modelo
    model: str = "claude-sonnet-4-20250514"

    # Parametros de generacion
    max_tokens: int = 4096
    temperature: float = 0.7

    # Dimension de embeddings
    embedding_dim: int = 1536

    # API key (si no se especifica, usa ANTHROPIC_API_KEY del entorno)
    api_key: Optional[str] = None


@dataclass
class NucleoConfig:
    """
    Configuracion principal del Nucleo Logico Evolutivo.

    Agrupa todas las configuraciones del sistema.
    v7.0: Incluye MESConfig para Sistema Evolutivo con Memoria.
    """
    # Subconfigs
    rl: RLConfig = field(default_factory=RLConfig)
    lean: LeanConfig = field(default_factory=LeanConfig)
    graph: GraphConfig = field(default_factory=GraphConfig)
    llm: LLMConfig = field(default_factory=LLMConfig)
    mes: MESConfig = field(default_factory=MESConfig)  # v7.0

    # Paths
    data_dir: Path = field(default_factory=lambda: Path("data"))
    models_dir: Path = field(default_factory=lambda: Path("models"))
    logs_dir: Path = field(default_factory=lambda: Path("logs"))

    # Debug
    debug: bool = False
    verbose: bool = False

    def validate(self) -> None:
        """Validar toda la configuracion."""
        self.rl.validate()
        self.mes.validate()

    @classmethod
    def from_yaml(cls, path: Path | str) -> NucleoConfig:
        """Cargar configuracion desde archivo YAML."""
        path = Path(path)
        with open(path) as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> NucleoConfig:
        """Crear configuracion desde diccionario."""
        return cls(
            rl=RLConfig(**data.get("rl", {})),
            lean=LeanConfig(**data.get("lean", {})),
            graph=GraphConfig(**data.get("graph", {})),
            llm=LLMConfig(**data.get("llm", {})),
            mes=MESConfig(**data.get("mes", {})),
            data_dir=Path(data.get("data_dir", "data")),
            models_dir=Path(data.get("models_dir", "models")),
            logs_dir=Path(data.get("logs_dir", "logs")),
            debug=data.get("debug", False),
            verbose=data.get("verbose", False),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convertir a diccionario."""
        return {
            "rl": {
                "gamma": self.rl.gamma,
                "lambda_1": self.rl.lambda_1,
                "lambda_2": self.rl.lambda_2,
                "lambda_3": self.rl.lambda_3,
                "lambda_4": self.rl.lambda_4,
                "lambda_5": self.rl.lambda_5,
                "alpha": self.rl.alpha,
                "beta": self.rl.beta,
                "history_size": self.rl.history_size,
                "learning_rate": self.rl.learning_rate,
                "batch_size": self.rl.batch_size,
                "n_epochs": self.rl.n_epochs,
                "clip_range": self.rl.clip_range,
            },
            "lean": {
                "lean_path": self.lean.lean_path,
                "timeout_ms": self.lean.timeout_ms,
                "project_path": self.lean.project_path,
                "use_mathlib": self.lean.use_mathlib,
                "mathlib_cache": self.lean.mathlib_cache,
            },
            "graph": {
                "max_skills": self.graph.max_skills,
                "default_weight": self.graph.default_weight,
                "weight_decay": self.graph.weight_decay,
                "gnn_hidden_dim": self.graph.gnn_hidden_dim,
                "gnn_num_layers": self.graph.gnn_num_layers,
                "gnn_dropout": self.graph.gnn_dropout,
                "max_levels": self.graph.max_levels,
                "min_pattern_size": self.graph.min_pattern_size,
            },
            "llm": {
                "model": self.llm.model,
                "max_tokens": self.llm.max_tokens,
                "temperature": self.llm.temperature,
                "embedding_dim": self.llm.embedding_dim,
            },
            "mes": {
                "cr_org_frequency": self.mes.cr_org_frequency,
                "cr_str_frequency": self.mes.cr_str_frequency,
                "cr_int_period": self.mes.cr_int_period,
                "max_records": self.mes.max_records,
                "consolidation_threshold": self.mes.consolidation_threshold,
                "econcept_min_records": self.mes.econcept_min_records,
                "colimit_threshold": self.mes.colimit_threshold,
                "pattern_similarity": self.mes.pattern_similarity,
            },
            "data_dir": str(self.data_dir),
            "models_dir": str(self.models_dir),
            "logs_dir": str(self.logs_dir),
            "debug": self.debug,
            "verbose": self.verbose,
        }

    def save_yaml(self, path: Path | str) -> None:
        """Guardar configuracion a archivo YAML."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False)


# Configuracion por defecto
DEFAULT_CONFIG = NucleoConfig()
