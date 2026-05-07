"""
ConsultoresModule — orquestador del módulo Consultores Avanzados.

Usa exclusivamente los componentes ya instanciados en el NLE:
    llm_client      → nucleo._llm
    lean_client     → nucleo._lean
    pattern_manager → nucleo._pattern_manager
    memory          → nucleo._memory

Flujo por request:
    1. Prompt maestro → LLM genera clasificación + spec + N candidatos
    2. Parser extrae artefactos de los bloques %%MARKER%%
    3. Lean verifica cada candidato (lean_client.check_code)
    4. Reranker puntúa y ordena
    5. Se registra en MESMemory para que el NLE aprenda
    6. Devuelve ConsultingResult
"""
from __future__ import annotations

import json
import logging
import re
import time
from typing import Optional, TYPE_CHECKING

from nucleo.consultores.artifacts import (
    AuditTrace,
    Candidate,
    ConsultingResult,
    FormalSpec,
    RankedCandidate,
    RequestType,
)
from nucleo.consultores.master_prompt import (
    MARKERS,
    build_consultores_prompt,
    candidate_markers,
)
from nucleo.consultores.reranker import score_and_rank

if TYPE_CHECKING:
    from nucleo.llm.client import LLMClient
    from nucleo.lean.client import LeanClient
    from nucleo.mes.patterns import PatternManager
    from nucleo.mes.memory import MESMemory

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Parser helpers
# ---------------------------------------------------------------------------

def _extract_block(text: str, start_marker: str, end_marker: str) -> str:
    """Extract content between start_marker and end_marker (exclusive)."""
    s = text.find(start_marker)
    if s == -1:
        return ""
    s += len(start_marker)
    e = text.find(end_marker, s)
    if e == -1:
        return text[s:].strip()
    return text[s:e].strip()


def _parse_json_block(text: str, start_marker: str, end_marker: str) -> dict:
    raw = _extract_block(text, start_marker, end_marker)
    if not raw:
        return {}
    # Strip markdown code fences if present
    raw = re.sub(r"^```[a-z]*\n?", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"\n?```$", "", raw, flags=re.MULTILINE)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("JSON decode failed for block %s…%s", start_marker, end_marker)
        return {}


def _parse_classification(text: str) -> RequestType:
    data = _parse_json_block(text, *MARKERS["clasificacion"])
    raw = data.get("type", "UNKNOWN").upper()
    try:
        return RequestType(raw.lower())
    except ValueError:
        return RequestType.UNKNOWN


def _parse_spec(text: str) -> FormalSpec:
    data = _parse_json_block(text, *MARKERS["spec"])
    return FormalSpec(
        enunciado_formal=data.get("enunciado_formal", ""),
        entradas=data.get("entradas", []),
        supuestos=data.get("supuestos", []),
        criterios_exito=data.get("criterios_exito", []),
        formato_salida=data.get("formato_salida", []),
        mathlib_anchors=data.get("mathlib_anchors", []),
    )


def _parse_candidates(text: str, n: int) -> list[Candidate]:
    candidates: list[Candidate] = []
    for i in range(1, n + 1):
        cm = candidate_markers(i)
        lean = _extract_block(text, *cm["lean"])
        skeleton = _extract_block(text, *cm["skeleton"])
        solver = _extract_block(text, *cm["solver"])
        bridge = _extract_block(text, *cm["bridge"])
        plan_raw = _extract_block(text, *cm["plan"])
        plan = [l.strip() for l in plan_raw.splitlines() if l.strip()] if plan_raw else []
        cmds_raw = _extract_block(text, *cm["comandos"])
        cmds = [l.strip() for l in cmds_raw.splitlines() if l.strip()] if cmds_raw else []

        # Strip markdown fences from lean block
        lean = re.sub(r"^```[a-z]*\n?", "", lean, flags=re.MULTILINE)
        lean = re.sub(r"\n?```$", "", lean, flags=re.MULTILINE).strip()

        sorry_count = lean.count("sorry")

        cand = Candidate(
            lean_file=lean,
            proof_skeleton=skeleton,
            solver_script=solver,
            verification_bridge=bridge,
            verification_plan=plan,
            lean_commands=cmds,
            sorry_count=sorry_count,
        )
        candidates.append(cand)
    return candidates


def _parse_metrics_notas(text: str, n: int) -> dict[int, str]:
    """Extract 'notas' per-candidate from the METRICAS block."""
    data = _parse_json_block(text, *MARKERS["metricas"])
    notas: dict[int, str] = {}
    for item in data.get("candidatos", []):
        idx = item.get("id", 0)
        notas[idx] = item.get("notas", "")
    return notas


# ---------------------------------------------------------------------------
# ConsultoresModule
# ---------------------------------------------------------------------------

class ConsultoresModule:
    """
    Módulo Consultores Avanzados del NLE.

    Se instancia desde Nucleo.set_consultores_mode() y reutiliza
    exactamente los mismos clientes que el NLE principal.
    """

    def __init__(
        self,
        llm_client: "LLMClient",
        lean_client: "LeanClient",
        pattern_manager: "PatternManager",
        memory: "MESMemory",
        n_candidates: int = 3,
    ) -> None:
        self._llm = llm_client
        self._lean = lean_client
        self._pattern_manager = pattern_manager
        self._memory = memory
        self.n_candidates = max(1, n_candidates)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def process(self, query: str) -> ConsultingResult:
        t0 = time.monotonic()
        result = ConsultingResult(query=query)

        try:
            # 1. Build prompt and call LLM
            prompt = build_consultores_prompt(query, self.n_candidates)
            llm_resp = await self._llm.generate(
                prompt,
                system=(
                    "Eres el Consultor Avanzado del Núcleo Lógico Evolutivo. "
                    "Sigue exactamente el protocolo de bloques %%MARKER%%."
                ),
            )
            raw = llm_resp.content
            result.raw_llm_response = raw

            # 2. Parse artefactos
            result.request_type = _parse_classification(raw)
            result.spec = _parse_spec(raw)
            candidates = _parse_candidates(raw, self.n_candidates)
            notas_map = _parse_metrics_notas(raw, self.n_candidates)

            logger.info(
                "Consultores: %d candidatos parseados, tipo=%s",
                len(candidates),
                result.request_type.value,
            )

            # 3. Lean verification layer
            n_lean_passed = 0
            for idx, cand in enumerate(candidates, start=1):
                if cand.lean_file:
                    lean_result = await self._lean.check_code(cand.lean_file)
                    cand.lean_verified = lean_result.success
                    if lean_result.errors:
                        cand.lean_errors = lean_result.errors
                    if lean_result.success:
                        n_lean_passed += 1
                    # Recount sorries from actual content (paranoia)
                    cand.sorry_count = cand.lean_file.count("sorry")
                    logger.debug(
                        "Lean cand %d: verified=%s sorries=%d",
                        idx,
                        cand.lean_verified,
                        cand.sorry_count,
                    )

            # 4. Rerank with notas from LLM metrics
            for idx, cand in enumerate(candidates, start=1):
                cand_notas = notas_map.get(idx, "")
                # Store notas temporarily in metadata-like field (solver_script unused for non-opt)
                cand.proof_skeleton = (
                    cand.proof_skeleton
                    + (f"\n\n[Notas LLM: {cand_notas}]" if cand_notas else "")
                )
            result.ranked_candidates = score_and_rank(candidates)

            # 5. Executive summary
            result.executive_summary = _extract_block(raw, *MARKERS["resumen"])

            # 6. Audit trace
            audit_data = _parse_json_block(raw, *MARKERS["audit"])
            result.audit = AuditTrace(
                query=query,
                request_type=result.request_type.value,
                n_candidates_generated=len(candidates),
                n_lean_passed=n_lean_passed,
                model_used=getattr(self._llm, "model", "unknown"),
                processing_time_s=time.monotonic() - t0,
                metadata=audit_data,
            )

            # 7. Record in MESMemory so the NLE learns from the session
            self._record_in_memory(query, result)

        except Exception as exc:
            logger.exception("ConsultoresModule.process failed: %s", exc)
            result.error = str(exc)

        return result

    # ------------------------------------------------------------------
    # Memory integration
    # ------------------------------------------------------------------

    def _record_in_memory(self, query: str, result: ConsultingResult) -> None:
        """Store consulting session in MESMemory for future retrieval."""
        if self._memory is None:
            return
        try:
            from nucleo.types import ExperienceRecord

            best = result.best
            tactic = (
                best.candidate.proof_skeleton[:120]
                if best and best.candidate.proof_skeleton
                else ""
            )
            goal = result.spec.enunciado_formal if result.spec else ""

            # Procedural memory: stores query+tactic+goal for similarity search
            self._memory.procedural.add_procedure(
                pattern_id="consultores",
                action_sequence=[result.request_type.value],
                success=result.has_verified,
                query_text=query[:300],
                tactic_used=tactic,
                lean_goal=goal,
            )

            # Empirical memory: stores success signal
            record = ExperienceRecord(
                success_value=1.0 if result.has_verified else 0.5,
                query=query[:200],
                response=(result.executive_summary or "")[:200],
            )
            self._memory.add_record(record)
        except Exception as e:
            logger.warning("ConsultoresModule._record_in_memory: %s", e)
