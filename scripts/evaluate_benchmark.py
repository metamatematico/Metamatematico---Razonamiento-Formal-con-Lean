"""
evaluate_benchmark.py
=====================
Evalua el Nucleo Logico Evolutivo contra benchmarks matematicos.

FILOSOFIA DE LA EVALUACION
---------------------------
El NLE es un sistema de razonamiento formal. La LLM es solo su capa
de lenguaje natural. Por lo tanto se miden DOS tipos de metricas:

1. Metricas de RESPUESTA (dependientes del LLM)
   - Accuracy final: ¿la respuesta coincide con la referencia?

2. Metricas del NLE (independientes del LLM)
   - Skill coverage: ¿el grafo tiene skills relevantes para el problema?
   - CR routing: ¿que decision tomaron los co-reguladores?
   - Lean verification: ¿se pudo verificar formalmente la respuesta?
   - Memory hits: ¿la MES memory tenia un patron similar previo?
   - Skill-aided accuracy: ¿los problemas con skills activos se resuelven mejor?

Datasets:
  - MATH  (Henderson et al., 7 categorias, 12500 problemas)
  - GSM8K (OpenAI, 8792 problemas de aritmetica)

Uso:
    python scripts/evaluate_benchmark.py --dataset gsm8k --n 50
    python scripts/evaluate_benchmark.py --dataset math --n 20 --category algebra
    python scripts/evaluate_benchmark.py --dataset both --n 30 --provider anthropic --api_key sk-ant-...
    python scripts/evaluate_benchmark.py --dataset math --n 10 --provider demo  # sin LLM real

Requiere datasets en E:/MetamatematicoDataSet/
"""

from __future__ import annotations

import argparse
import asyncio
import concurrent.futures
import json
import os
import re
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DATASET_DIR = Path("E:/MetamatematicoDataSet")

MATH_CATEGORIES = [
    "algebra",
    "counting_and_probability",
    "geometry",
    "intermediate_algebra",
    "number_theory",
    "prealgebra",
    "precalculus",
]


# =============================================================================
# Estructuras de resultado
# =============================================================================

@dataclass
class NLESignals:
    """
    Senales del Nucleo Logico Evolutivo por problema.

    Estas metricas son independientes de si el LLM acierta la respuesta.
    Miden la contribucion de los componentes internos del NLE.
    """
    # Skill graph
    skills_matched: list[str] = field(default_factory=list)   # skills activados
    skill_hit: bool = False                                     # ¿activo al menos 1?
    prerequisites_found: int = 0                               # profundidad de ruta

    # Co-reguladores
    cr_action: str = ""         # accion elegida: RESPONSE / ASSIST / REORGANIZE
    cr_source: str = ""         # CR que decidio: TACTICAL / STRATEGIC / etc.
    cr_confidence: float = 0.0  # confianza de la decision

    # Lean verifier
    lean_attempted: bool = False   # ¿se intento verificacion Lean?
    lean_verified: bool = False    # ¿Lean acepto la prueba?
    lean_has_sorry: bool = False   # ¿quedaron sorry sin resolver?
    sorry_filled: int = 0          # cuantos sorry resolvio el cascade

    # MES Memory
    memory_hit: bool = False       # ¿habia un patron previo util?
    memory_pattern: str = ""       # ID del patron reutilizado


@dataclass
class ProblemResult:
    problem: str
    reference: str
    prediction: str
    is_correct: bool
    match_type: str
    nle: NLESignals = field(default_factory=NLESignals)
    category: str = ""
    level: str = ""
    elapsed: float = 0.0


@dataclass
class BenchmarkReport:
    dataset: str
    total: int = 0
    correct: int = 0
    by_category: dict = field(default_factory=dict)
    by_level: dict = field(default_factory=dict)
    match_types: dict = field(default_factory=dict)
    total_time: float = 0.0
    results: list[ProblemResult] = field(default_factory=list)

    # --- Metricas NLE ---
    skill_hits: int = 0           # problemas con >=1 skill activo
    lean_attempts: int = 0        # intentos de verificacion Lean
    lean_verified: int = 0        # verificaciones exitosas
    memory_hits: int = 0          # hits en MES Memory
    cr_actions: dict = field(default_factory=dict)   # accion elegida: RESPONSE/ASSIST/...
    cr_sources: dict = field(default_factory=dict)   # CR que decidio: TACTICAL/STRATEGIC/...

    @property
    def accuracy(self) -> float:
        return self.correct / self.total if self.total else 0.0

    @property
    def skill_coverage(self) -> float:
        return self.skill_hits / self.total if self.total else 0.0

    @property
    def lean_verification_rate(self) -> float:
        return self.lean_verified / self.lean_attempts if self.lean_attempts else 0.0

    @property
    def accuracy_with_skill(self) -> float:
        rs = [r for r in self.results if r.nle.skill_hit]
        if not rs:
            return 0.0
        return sum(1 for r in rs if r.is_correct) / len(rs)

    @property
    def accuracy_without_skill(self) -> float:
        rs = [r for r in self.results if not r.nle.skill_hit]
        if not rs:
            return 0.0
        return sum(1 for r in rs if r.is_correct) / len(rs)

    def print_summary(self) -> None:
        sep = "=" * 65
        print(f"\n{sep}")
        print(f"  BENCHMARK: {self.dataset.upper()}")
        print(sep)

        # --- Metricas de respuesta ---
        print(f"\n  [RESPUESTA - depende del LLM]")
        print(f"    Total:    {self.total}")
        print(f"    Correct:  {self.correct}")
        print(f"    Accuracy: {self.accuracy:.1%}")
        print(f"    Tiempo:   {self.total_time:.1f}s  ({self.total_time/max(self.total,1):.1f}s/prob)")

        if self.by_category:
            print("\n    Por categoria:")
            for cat, (c, t) in sorted(self.by_category.items()):
                acc = c / t if t else 0.0
                print(f"      {cat:<32s}  {c:>3}/{t:<3}  ({acc:.1%})")

        if self.by_level:
            print("\n    Por nivel:")
            for lv in sorted(self.by_level):
                c, t = self.by_level[lv]
                acc = c / t if t else 0.0
                print(f"      {lv:<12}  {c:>3}/{t:<3}  ({acc:.1%})")

        if self.match_types:
            print("\n    Tipos de match:")
            for mt, cnt in sorted(self.match_types.items(), key=lambda x: -x[1]):
                print(f"      {mt:<22}  {cnt}")

        # --- Metricas NLE ---
        print(f"\n  [NLE - independiente del LLM]")

        # Skill graph
        print(f"\n    Skill Graph:")
        print(f"      Cobertura:           {self.skill_hits}/{self.total}  ({self.skill_coverage:.1%})")
        acc_w  = self.accuracy_with_skill
        acc_wo = self.accuracy_without_skill
        delta  = acc_w - acc_wo
        sign   = "+" if delta >= 0 else ""
        print(f"      Accuracy CON skill:  {acc_w:.1%}")
        print(f"      Accuracy SIN skill:  {acc_wo:.1%}")
        verdict = "POSITIVO" if delta > 0 else "sin aporte" if delta == 0 else "NEGATIVO"
        print(f"      Aporte del grafo:    {sign}{delta:.1%}  [{verdict}]")

        # Lean verifier
        print(f"\n    Lean Verifier:")
        if self.lean_attempts:
            print(f"      Intentos:            {self.lean_attempts}")
            print(f"      Verificados:         {self.lean_verified}  ({self.lean_verification_rate:.1%})")
        else:
            print(f"      No se intentaron verificaciones Lean")
            print(f"      (usar --lean para activar; requiere Lean 4 instalado)")

        # MES Memory
        print(f"\n    MES Memory:")
        mem_rate = self.memory_hits / self.total if self.total else 0.0
        print(f"      Memory hits:         {self.memory_hits}/{self.total}  ({mem_rate:.1%})")

        # Co-reguladores
        print(f"\n    Co-Reguladores:")
        print(f"      Quien decidio (CR source):")
        for src, cnt in sorted(self.cr_sources.items(), key=lambda x: -x[1]):
            pct = cnt / self.total if self.total else 0.0
            print(f"        {src:<22}  {cnt:>3}  ({pct:.1%})")
        print(f"      Accion elegida:")
        for action, cnt in sorted(self.cr_actions.items(), key=lambda x: -x[1]):
            pct = cnt / self.total if self.total else 0.0
            print(f"        {action:<22}  {cnt:>3}  ({pct:.1%})")

        print(sep + "\n")


# =============================================================================
# Extraccion de referencia GSM8K
# =============================================================================

def extract_gsm8k_answer(answer_text: str) -> str:
    """Extraer numero final de solucion GSM8K (despues de ####)."""
    match = re.search(r"####\s*(-?[\d,\.]+)", answer_text)
    if match:
        return match.group(1).replace(",", "")
    nums = re.findall(r"-?\d+(?:\.\d+)?", answer_text.replace(",", ""))
    return nums[-1] if nums else ""


# =============================================================================
# Evaluador principal
# =============================================================================

class BenchmarkEvaluator:
    """
    Conecta el NLE con los datasets MATH y GSM8K.

    Por cada problema:
      1. Consulta el NLE (process_sync) — los CRs deciden que hacer
      2. Extrae la respuesta y compara con referencia (MathEvaluator)
      3. Registra las senales NLE: skills activados, accion CR, Lean, Memory
    """

    def __init__(
        self,
        provider: str = "demo",
        model: str = "",
        api_key: str = "",
        max_tokens: int = 512,
        try_lean: bool = False,
        verbose: bool = False,
    ):
        self.provider  = provider
        self.model     = model
        self.api_key   = api_key
        self.max_tokens = max_tokens
        self.try_lean  = try_lean   # activar verificacion Lean por problema
        self.verbose   = verbose
        self._nucleo   = None

    # -------------------------------------------------------------------------
    # Inicializacion
    # -------------------------------------------------------------------------

    def _init_nucleo(self) -> None:
        if self._nucleo is not None:
            return

        from nucleo.core import Nucleo
        from nucleo.config import NucleoConfig

        print("Inicializando Nucleo Logico Evolutivo...")
        self._nucleo = Nucleo(NucleoConfig())

        def _run_init():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self._nucleo.initialize())
            finally:
                loop.close()

        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            pool.submit(_run_init).result(timeout=60)

        # Configurar LLM (siempre, incluyendo demo)
        self._nucleo.reconfigure_llm(
            provider=self.provider or "demo",
            model=self.model,
            api_key=self.api_key,
            max_tokens=self.max_tokens,
        )
        print(f"Nucleo listo  provider={self.provider}  model={self.model or 'default'}")
        stats = self._nucleo.stats
        cr    = stats.get("co_regulators", {})
        mem   = stats.get("memory", {})
        print(f"  Skills en grafo:   {stats.get('num_skills', 0)}")
        print(f"  Co-reguladores:    4 activos (TAC / ORG / STR / INT)")
        print(f"    steps  TAC={cr.get('tactical_steps', 0)}  "
              f"ORG={cr.get('organizational_steps', 0)}  "
              f"STR={cr.get('strategic_steps', 0)}  "
              f"INT={cr.get('integrity_steps', 0)}")
        print(f"    fracturas detectadas: {cr.get('detected_fractures', 0)}")
        print(f"  MES records:       {mem.get('total_records', 0)}")
        print(f"  MES e-concepts:    {mem.get('e_concepts', 0)}")

    # -------------------------------------------------------------------------
    # Consulta al NLE
    # -------------------------------------------------------------------------

    def _ask(self, question: str) -> tuple[str, NLESignals]:
        """
        Enviar pregunta al NLE y recopilar senales internas.

        Retorna (respuesta_texto, NLESignals).
        La respuesta puede ser vacia si el LLM falla — las senales NLE
        son validas independientemente.
        """
        nle = NLESignals()

        # El prompt pide \boxed{} para que MathEvaluator pueda extraer
        prompt = (
            f"{question}\n\n"
            "Resuelve paso a paso. Encierra tu respuesta final en \\boxed{{...}}."
        )

        try:
            resp = self._nucleo.process_sync(prompt)
            content = resp.content

            # --- Senales de la ultima decision ---
            decision_meta = self._nucleo.stats.get("last_decision", {})
            nle.cr_action     = decision_meta.get("action", "")
            nle.cr_source     = decision_meta.get("source_cr", "")
            nle.cr_confidence = decision_meta.get("confidence", 0.0)

            # Lean: si el NLE uso ASSIST y hay lean_result
            if resp.lean_result is not None:
                nle.lean_attempted = True
                nle.lean_verified  = resp.lean_result.is_success
                # Detectar sorry en el output
                if resp.lean_result.output:
                    nle.lean_has_sorry = "sorry" in resp.lean_result.output.lower()

        except Exception as e:
            if self.verbose:
                print(f"    [NLE ERROR] {e}")
            content = ""

        # --- Senales del grafo de skills (independiente del LLM) ---
        nle.skills_matched, nle.prerequisites_found = self._check_skill_graph(question)
        nle.skill_hit = len(nle.skills_matched) > 0

        # --- Senales de MES Memory ---
        nle.memory_hit, nle.memory_pattern = self._check_memory(question)

        return content, nle

    def _check_skill_graph(self, query: str) -> tuple[list[str], int]:
        """
        Verificar cuantos skills del grafo son relevantes para esta query.

        Usa el mismo metodo interno que usa el NLE en cada proceso.
        Esto es 100% independiente del LLM.
        """
        if not self._nucleo or not self._nucleo._graph:
            return [], 0
        try:
            matched = self._nucleo._match_skills_to_query(query, self._nucleo._graph)
            deps = []
            for sid in matched[:3]:
                for dep in self._nucleo._graph.dependencies(sid):
                    if dep not in deps:
                        deps.append(dep)
            return matched[:5], len(deps)
        except Exception:
            return [], 0

    def _check_memory(self, query: str) -> tuple[bool, str]:
        """
        Verificar si MES Memory tiene un patron util para esta query.

        Usa ProceduralMemory.get_best_for_query() — el mismo mecanismo
        que usa el NLE para tomar decisiones basadas en experiencia.
        """
        if not self._nucleo or not self._nucleo._memory:
            return False, ""
        try:
            proc = self._nucleo._memory.get_best_for_query(query)
            if proc:
                return True, proc.id
        except Exception:
            pass
        return False, ""

    # -------------------------------------------------------------------------
    # Lean opcional por problema
    # -------------------------------------------------------------------------

    def _try_lean_verify(self, question: str, response: str) -> NLESignals:
        """
        Intentar formalizar la respuesta en Lean 4 y verificarla.

        Solo se activa con --lean. Mide la capacidad del NLE de producir
        pruebas formalmente correctas, independiente de la respuesta textual.
        """
        nle = NLESignals()
        if not self.try_lean or not self._nucleo or not self._nucleo._lean:
            return nle

        # Pedir al LLM que genere codigo Lean para la respuesta
        lean_prompt = (
            f"Formaliza la siguiente solucion en Lean 4:\n\n"
            f"Problema: {question}\n"
            f"Solucion: {response}\n\n"
            "Escribe SOLO el bloque Lean 4, sin explicaciones."
        )
        try:
            lean_resp = self._nucleo.process_sync(lean_prompt)
            nle.lean_attempted = True
            if lean_resp.lean_result:
                nle.lean_verified = lean_resp.lean_result.is_success
        except Exception:
            pass
        return nle

    # -------------------------------------------------------------------------
    # Evaluacion MATH
    # -------------------------------------------------------------------------

    def evaluate_math(
        self,
        n: int = 50,
        categories: Optional[list[str]] = None,
        split: str = "test",
    ) -> BenchmarkReport:
        from datasets import load_from_disk

        self._init_nucleo()
        report = BenchmarkReport(dataset="MATH")
        cats = categories or MATH_CATEGORIES

        for cat in cats:
            cat_dir = DATASET_DIR / "MATH" / cat
            if not cat_dir.exists():
                print(f"  [SKIP] {cat} no encontrado")
                continue

            ds = load_from_disk(str(cat_dir))
            subset = ds[split]
            n_cat = min(n, len(subset))
            print(f"\n  Categoria: {cat}  ({n_cat}/{len(subset)})")

            correct_cat = 0
            for i in range(n_cat):
                row = subset[i]
                problem  = row["problem"]
                solution = row["solution"]
                level    = row.get("level", "")

                t0 = time.time()
                prediction, nle = self._ask(problem)
                elapsed = time.time() - t0

                eval_result = self._nucleo.evaluate_answer(prediction, solution)
                is_correct  = eval_result.is_correct

                pr = ProblemResult(
                    problem=problem[:120],
                    reference=eval_result.reference.normalized,
                    prediction=eval_result.prediction.normalized,
                    is_correct=is_correct,
                    match_type=eval_result.match_type,
                    nle=nle,
                    category=cat,
                    level=level,
                    elapsed=elapsed,
                )
                report.results.append(pr)
                self._accumulate(report, pr)

                if self.verbose or i % 10 == 0:
                    self._print_row(i + 1, n_cat, pr)

            correct_cat = sum(1 for r in report.results[-n_cat:] if r.is_correct)
            acc_cat = correct_cat / n_cat if n_cat else 0.0
            skill_cat = sum(1 for r in report.results[-n_cat:] if r.nle.skill_hit)
            print(f"  => {cat}: {correct_cat}/{n_cat} ({acc_cat:.1%})  skills_activos={skill_cat}/{n_cat}")

        return report

    # -------------------------------------------------------------------------
    # Evaluacion GSM8K
    # -------------------------------------------------------------------------

    def evaluate_gsm8k(
        self,
        n: int = 100,
        split: str = "test",
    ) -> BenchmarkReport:
        from datasets import load_from_disk

        self._init_nucleo()
        report = BenchmarkReport(dataset="GSM8K")

        ds = load_from_disk(str(DATASET_DIR / "GSM8K"))
        subset = ds[split]
        n_total = min(n, len(subset))
        print(f"\n  GSM8K {split}: {n_total}/{len(subset)}")

        for i in range(n_total):
            row = subset[i]
            question    = row["question"]
            answer_text = row["answer"]
            reference   = extract_gsm8k_answer(answer_text)

            t0 = time.time()
            prediction, nle = self._ask(question)
            elapsed = time.time() - t0

            eval_result = self._nucleo.evaluate_answer(
                prediction, reference, extract_answers=True
            )
            is_correct = eval_result.is_correct

            pr = ProblemResult(
                problem=question[:120],
                reference=eval_result.reference.normalized,
                prediction=eval_result.prediction.normalized,
                is_correct=is_correct,
                match_type=eval_result.match_type,
                nle=nle,
                elapsed=elapsed,
            )
            report.results.append(pr)
            self._accumulate(report, pr)

            if self.verbose or i % 10 == 0:
                self._print_row(i + 1, n_total, pr)

        return report

    # -------------------------------------------------------------------------
    # Acumulacion y salida
    # -------------------------------------------------------------------------

    def _accumulate(self, report: BenchmarkReport, pr: ProblemResult) -> None:
        """Acumular todas las metricas en el reporte."""
        report.total += 1
        if pr.is_correct:
            report.correct += 1

        # Metricas de respuesta
        if pr.category:
            if pr.category not in report.by_category:
                report.by_category[pr.category] = [0, 0]
            report.by_category[pr.category][1] += 1
            if pr.is_correct:
                report.by_category[pr.category][0] += 1

        if pr.level:
            if pr.level not in report.by_level:
                report.by_level[pr.level] = [0, 0]
            report.by_level[pr.level][1] += 1
            if pr.is_correct:
                report.by_level[pr.level][0] += 1

        report.match_types[pr.match_type] = (
            report.match_types.get(pr.match_type, 0) + 1
        )

        # Metricas NLE
        if pr.nle.skill_hit:
            report.skill_hits += 1
        if pr.nle.lean_attempted:
            report.lean_attempts += 1
        if pr.nle.lean_verified:
            report.lean_verified += 1
        if pr.nle.memory_hit:
            report.memory_hits += 1

        action = pr.nle.cr_action or "unknown"
        report.cr_actions[action] = report.cr_actions.get(action, 0) + 1

        source = pr.nle.cr_source or "unknown"
        report.cr_sources[source] = report.cr_sources.get(source, 0) + 1

    def _print_row(
        self, idx: int, total: int, pr: ProblemResult
    ) -> None:
        status  = "OK  " if pr.is_correct else "FAIL"
        skill   = "S" if pr.nle.skill_hit else "-"
        mem     = "M" if pr.nle.memory_hit else "-"
        lean    = "L" if pr.nle.lean_verified else ("-" if not pr.nle.lean_attempted else "X")
        cr      = pr.nle.cr_action[:3] if pr.nle.cr_action else "?"
        print(
            f"    [{idx:3d}/{total}] {status} "
            f"ref={pr.reference!r:12s} pred={pr.prediction!r:12s} "
            f"({pr.match_type:<14s}) "
            f"[skill={skill} mem={mem} lean={lean} cr={cr}] "
            f"{pr.elapsed:.1f}s"
        )


# =============================================================================
# Guardado de resultados
# =============================================================================

def save_report(report: BenchmarkReport, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y%m%d_%H%M%S")
    out_path = out_dir / f"eval_{report.dataset.lower()}_{ts}.json"

    data = {
        # Metricas de respuesta
        "dataset": report.dataset,
        "total": report.total,
        "correct": report.correct,
        "accuracy": report.accuracy,
        "by_category": {k: {"correct": v[0], "total": v[1]} for k, v in report.by_category.items()},
        "by_level": {k: {"correct": v[0], "total": v[1]} for k, v in report.by_level.items()},
        "match_types": report.match_types,
        "total_time_s": report.total_time,
        # Metricas NLE
        "nle": {
            "skill_coverage": report.skill_coverage,
            "skill_hits": report.skill_hits,
            "accuracy_with_skill": report.accuracy_with_skill,
            "accuracy_without_skill": report.accuracy_without_skill,
            "lean_attempts": report.lean_attempts,
            "lean_verified": report.lean_verified,
            "lean_verification_rate": report.lean_verification_rate,
            "memory_hits": report.memory_hits,
            "cr_actions": report.cr_actions,
        },
        # Detalle problema a problema
        "results": [
            {
                "problem":    r.problem,
                "reference":  r.reference,
                "prediction": r.prediction,
                "is_correct": r.is_correct,
                "match_type": r.match_type,
                "category":   r.category,
                "level":      r.level,
                "elapsed_s":  r.elapsed,
                "nle": {
                    "skills_matched":    r.nle.skills_matched,
                    "skill_hit":         r.nle.skill_hit,
                    "prerequisites":     r.nle.prerequisites_found,
                    "cr_action":         r.nle.cr_action,
                    "cr_source":         r.nle.cr_source,
                    "cr_confidence":     r.nle.cr_confidence,
                    "lean_attempted":    r.nle.lean_attempted,
                    "lean_verified":     r.nle.lean_verified,
                    "lean_has_sorry":    r.nle.lean_has_sorry,
                    "sorry_filled":      r.nle.sorry_filled,
                    "memory_hit":        r.nle.memory_hit,
                    "memory_pattern":    r.nle.memory_pattern,
                },
            }
            for r in report.results
        ],
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Reporte guardado: {out_path}")
    return out_path


# =============================================================================
# CLI
# =============================================================================

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Evalua el NLE contra MATH y GSM8K"
    )
    p.add_argument(
        "--dataset", choices=["math", "gsm8k", "both"], default="gsm8k",
    )
    p.add_argument(
        "--n", type=int, default=20,
        help="Problemas por categoria MATH, o total GSM8K (default: 20)"
    )
    p.add_argument("--category", nargs="+", choices=MATH_CATEGORIES)
    p.add_argument("--split", choices=["train", "test"], default="test")
    p.add_argument(
        "--provider", default="demo",
        choices=["demo", "anthropic", "google", "groq"],
    )
    p.add_argument("--model",   default="")
    p.add_argument("--api_key", default="")
    p.add_argument("--max_tokens", type=int, default=512)
    p.add_argument(
        "--lean", action="store_true",
        help="Intentar verificacion Lean por problema (requiere Lean 4)"
    )
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--out", default="data/eval_results")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    api_key = args.api_key
    if not api_key:
        env_map = {
            "anthropic": "ANTHROPIC_API_KEY",
            "google":    "GOOGLE_API_KEY",
            "groq":      "GROQ_API_KEY",
        }
        api_key = os.environ.get(env_map.get(args.provider, ""), "")

    evaluator = BenchmarkEvaluator(
        provider=args.provider,
        model=args.model,
        api_key=api_key,
        max_tokens=args.max_tokens,
        try_lean=args.lean,
        verbose=args.verbose,
    )

    out_dir = PROJECT_ROOT / args.out
    t_start = time.time()

    if args.dataset in ("math", "both"):
        t0 = time.time()
        print(f"\n{'='*65}")
        print(f"  MATH benchmark  (n={args.n} por categoria)")
        print(f"{'='*65}")
        report = evaluator.evaluate_math(
            n=args.n, categories=args.category, split=args.split
        )
        report.total_time = time.time() - t0
        report.print_summary()
        save_report(report, out_dir)

    if args.dataset in ("gsm8k", "both"):
        t0 = time.time()
        print(f"\n{'='*65}")
        print(f"  GSM8K benchmark  (n={args.n})")
        print(f"{'='*65}")
        report = evaluator.evaluate_gsm8k(n=args.n, split=args.split)
        report.total_time = time.time() - t0
        report.print_summary()
        save_report(report, out_dir)

    print(f"Tiempo total: {time.time() - t_start:.1f}s")


if __name__ == "__main__":
    main()
