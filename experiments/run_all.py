#!/usr/bin/env python3
"""
Ejecutar Suite de Experimentos Go/No-Go
=======================================

Ejecuta todos los experimentos de validacion del Nucleo Logico Evolutivo.

Uso:
    python experiments/run_all.py [--stop-on-failure] [--save-report PATH]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Agregar root al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from experiments.base import ExperimentSuite
from experiments.exp1_lean import LeanIntegrationExperiment
from experiments.exp2_graph import GraphValidationExperiment
from experiments.exp3_agent import AgentBaselineExperiment


def create_suite() -> ExperimentSuite:
    """Crear suite con todos los experimentos."""
    suite = ExperimentSuite(name="Nucleo Go/No-Go Suite")

    # Experimento 1: Integracion Lean 4
    suite.add(LeanIntegrationExperiment())

    # Experimento 2: Grafo Categorico
    suite.add(GraphValidationExperiment())

    # Experimento 3: Agente RL Baseline
    suite.add(AgentBaselineExperiment())

    return suite


def main():
    parser = argparse.ArgumentParser(
        description="Ejecutar experimentos Go/No-Go del Nucleo"
    )
    parser.add_argument(
        "--stop-on-failure",
        action="store_true",
        help="Detener al primer experimento fallido"
    )
    parser.add_argument(
        "--save-report",
        type=Path,
        default=None,
        help="Guardar reporte JSON en PATH"
    )
    parser.add_argument(
        "--exp",
        type=int,
        choices=[1, 2, 3],
        default=None,
        help="Ejecutar solo experimento especifico (1, 2, o 3)"
    )

    args = parser.parse_args()

    print("""
    ============================================================
    |     NUCLEO LOGICO EVOLUTIVO - Experimentos Go/No-Go      |
    ============================================================
    |  Exp 1: Integracion Lean 4                               |
    |  Exp 2: Validacion Grafo Categorico                      |
    |  Exp 3: Baseline Agente RL                               |
    ============================================================
    """)

    # Ejecutar experimento especifico o suite completa
    if args.exp:
        experiments = {
            1: LeanIntegrationExperiment,
            2: GraphValidationExperiment,
            3: AgentBaselineExperiment,
        }
        exp = experiments[args.exp]()
        result = exp.execute()
        results = [result]
    else:
        suite = create_suite()
        results = suite.run_all(stop_on_failure=args.stop_on_failure)

        if args.save_report:
            suite.save_report(str(args.save_report))

    # Exit code basado en resultados
    all_passed = all(r.passed for r in results)
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
