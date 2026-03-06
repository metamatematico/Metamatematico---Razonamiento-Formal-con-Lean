"""
Base para Experimentos Go/No-Go
===============================

Framework para ejecutar y reportar experimentos de validacion.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
import json
import time


class ExperimentStatus(Enum):
    """Estado del experimento."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"      # Go
    FAILED = "failed"      # No-Go
    ERROR = "error"        # Error de ejecucion


@dataclass
class ExperimentResult:
    """Resultado de un experimento."""
    name: str
    status: ExperimentStatus
    duration_ms: float
    metrics: Dict[str, Any] = field(default_factory=dict)
    details: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def passed(self) -> bool:
        return self.status == ExperimentStatus.PASSED

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "status": self.status.value,
            "duration_ms": self.duration_ms,
            "metrics": self.metrics,
            "details": self.details,
            "timestamp": self.timestamp,
        }

    def __str__(self) -> str:
        status_symbol = {
            ExperimentStatus.PASSED: "[GO]",
            ExperimentStatus.FAILED: "[NO-GO]",
            ExperimentStatus.ERROR: "[ERROR]",
            ExperimentStatus.RUNNING: "[...]",
            ExperimentStatus.PENDING: "[ ]",
        }
        return f"{status_symbol[self.status]} {self.name}: {self.details}"


class Experiment(ABC):
    """
    Clase base para experimentos Go/No-Go.

    Cada experimento debe:
    1. Definir criterios de exito claros
    2. Ejecutar pruebas automatizadas
    3. Reportar metricas y decision Go/No-Go
    """

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.result: Optional[ExperimentResult] = None

    @abstractmethod
    def run(self) -> ExperimentResult:
        """Ejecutar el experimento."""
        pass

    @abstractmethod
    def get_criteria(self) -> List[str]:
        """Obtener criterios de exito."""
        pass

    def execute(self) -> ExperimentResult:
        """
        Ejecutar experimento con manejo de errores y timing.
        """
        print(f"\n{'='*60}")
        print(f"Experimento: {self.name}")
        print(f"{'='*60}")
        print(f"{self.description}\n")

        print("Criterios de exito:")
        for i, criterion in enumerate(self.get_criteria(), 1):
            print(f"  {i}. {criterion}")
        print()

        start_time = time.time()

        try:
            self.result = self.run()
        except Exception as e:
            duration = (time.time() - start_time) * 1000
            self.result = ExperimentResult(
                name=self.name,
                status=ExperimentStatus.ERROR,
                duration_ms=duration,
                details=f"Error: {str(e)}"
            )

        # Mostrar resultado
        print(f"\n{'-'*60}")
        print(f"Resultado: {self.result}")
        print(f"Duracion: {self.result.duration_ms:.2f}ms")

        if self.result.metrics:
            print("\nMetricas:")
            for key, value in self.result.metrics.items():
                print(f"  {key}: {value}")

        return self.result


class ExperimentSuite:
    """Suite de experimentos Go/No-Go."""

    def __init__(self, name: str = "NucleoExperiments"):
        self.name = name
        self.experiments: List[Experiment] = []
        self.results: List[ExperimentResult] = []

    def add(self, experiment: Experiment) -> None:
        """Agregar experimento a la suite."""
        self.experiments.append(experiment)

    def run_all(self, stop_on_failure: bool = True) -> List[ExperimentResult]:
        """
        Ejecutar todos los experimentos.

        Args:
            stop_on_failure: Si True, detiene en primer No-Go
        """
        print(f"\n{'#'*60}")
        print(f"# Suite de Experimentos: {self.name}")
        print(f"# Total: {len(self.experiments)} experimentos")
        print(f"{'#'*60}")

        self.results = []

        for exp in self.experiments:
            result = exp.execute()
            self.results.append(result)

            if stop_on_failure and not result.passed:
                print(f"\n[STOP] Experimento fallido: {exp.name}")
                print("Deteniendo suite de experimentos.")
                break

        self._print_summary()
        return self.results

    def _print_summary(self) -> None:
        """Imprimir resumen de resultados."""
        print(f"\n{'#'*60}")
        print("# RESUMEN")
        print(f"{'#'*60}")

        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if r.status == ExperimentStatus.FAILED)
        errors = sum(1 for r in self.results if r.status == ExperimentStatus.ERROR)

        print(f"\nTotal ejecutados: {len(self.results)}/{len(self.experiments)}")
        print(f"  [GO]:    {passed}")
        print(f"  [NO-GO]: {failed}")
        print(f"  [ERROR]: {errors}")

        print("\nResultados:")
        for result in self.results:
            print(f"  {result}")

        # Decision final
        if failed > 0 or errors > 0:
            print(f"\n{'!'*60}")
            print("! DECISION: NO-GO - Revisar experimentos fallidos")
            print(f"{'!'*60}")
        elif passed == len(self.experiments):
            print(f"\n{'*'*60}")
            print("* DECISION: GO - Todos los experimentos pasaron")
            print(f"{'*'*60}")

    def save_report(self, path: str) -> None:
        """Guardar reporte JSON."""
        report = {
            "suite": self.name,
            "timestamp": datetime.now().isoformat(),
            "total_experiments": len(self.experiments),
            "executed": len(self.results),
            "passed": sum(1 for r in self.results if r.passed),
            "results": [r.to_dict() for r in self.results]
        }

        with open(path, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\nReporte guardado en: {path}")
