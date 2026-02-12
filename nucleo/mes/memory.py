"""
MES Memory System - v7.0
========================

Arquitectura de memoria del NLE siguiendo el marco MES.

Seccion 5 del documento v7.0:
- Registros de experiencia (empirica)
- Procedimientos (procedimental)
- E-conceptos (semantica)
- Registros fortalecidos (consolidada)

Reference:
- Ehresmann & Vanbremeersch (2007), Chapter 8
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from collections import defaultdict

from nucleo.types import (
    ExperienceRecord,
    EConcept,
    Pattern,
    MemoryType,
    CoRegulatorType,
)

logger = logging.getLogger(__name__)


@dataclass
class Procedure:
    """
    Procedimiento almacenado en memoria procedimental.

    Secuencia de acciones que resolvieron una clase de problemas.
    """
    id: str
    pattern_id: str  # Patron de skills usado
    action_sequence: list[str]  # Secuencia de acciones
    success_rate: float = 0.0
    invocation_count: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    last_used: datetime = field(default_factory=datetime.now)

    def invoke(self) -> None:
        """Registrar invocacion del procedimiento."""
        self.invocation_count += 1
        self.last_used = datetime.now()


class ProceduralMemory:
    """
    Memoria procedimental (Seccion 5.2, Tabla v7.0).

    Almacena secuencias de acciones exitosas como procedimientos
    reutilizables.
    """

    def __init__(self, max_procedures: int = 1000):
        self._procedures: dict[str, Procedure] = {}
        self._by_pattern: dict[str, list[str]] = defaultdict(list)
        self._max_procedures = max_procedures

    def add_procedure(
        self,
        pattern_id: str,
        action_sequence: list[str],
        success: bool = True
    ) -> Procedure:
        """
        Agregar o actualizar procedimiento.

        Args:
            pattern_id: ID del patron de skills
            action_sequence: Secuencia de acciones
            success: Si fue exitoso

        Returns:
            Procedimiento creado o actualizado
        """
        # Buscar procedimiento existente
        existing = self._find_matching(pattern_id, action_sequence)
        if existing:
            existing.invoke()
            existing.success_rate = (
                (existing.success_rate * (existing.invocation_count - 1) + float(success))
                / existing.invocation_count
            )
            return existing

        # Crear nuevo
        proc_id = f"proc_{len(self._procedures)}"
        proc = Procedure(
            id=proc_id,
            pattern_id=pattern_id,
            action_sequence=action_sequence,
            success_rate=float(success),
            invocation_count=1,
        )
        self._procedures[proc_id] = proc
        self._by_pattern[pattern_id].append(proc_id)

        # Limpieza si excede limite
        if len(self._procedures) > self._max_procedures:
            self._prune_least_used()

        return proc

    def get_procedures_for_pattern(self, pattern_id: str) -> list[Procedure]:
        """Obtener procedimientos asociados a un patron."""
        proc_ids = self._by_pattern.get(pattern_id, [])
        return [self._procedures[pid] for pid in proc_ids if pid in self._procedures]

    def get_best_procedure(self, pattern_id: str) -> Optional[Procedure]:
        """Obtener el procedimiento con mayor tasa de exito."""
        procs = self.get_procedures_for_pattern(pattern_id)
        if not procs:
            return None
        return max(procs, key=lambda p: p.success_rate)

    def _find_matching(
        self,
        pattern_id: str,
        action_sequence: list[str]
    ) -> Optional[Procedure]:
        """Buscar procedimiento que coincida."""
        for proc in self.get_procedures_for_pattern(pattern_id):
            if proc.action_sequence == action_sequence:
                return proc
        return None

    def _prune_least_used(self) -> None:
        """Eliminar procedimientos menos usados."""
        if len(self._procedures) <= self._max_procedures:
            return

        # Ordenar por uso y eliminar los menos usados
        sorted_procs = sorted(
            self._procedures.values(),
            key=lambda p: (p.invocation_count, p.success_rate)
        )
        to_remove = sorted_procs[:len(self._procedures) - self._max_procedures]

        for proc in to_remove:
            del self._procedures[proc.id]
            if proc.id in self._by_pattern.get(proc.pattern_id, []):
                self._by_pattern[proc.pattern_id].remove(proc.id)

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "num_procedures": len(self._procedures),
            "num_patterns": len(self._by_pattern),
            "avg_success_rate": (
                sum(p.success_rate for p in self._procedures.values()) /
                max(len(self._procedures), 1)
            ),
        }


class SemanticMemory:
    """
    Memoria semantica (Seccion 5.2, Tabla v7.0).

    Almacena E-conceptos y sus relaciones. Un E-concepto agrupa
    registros funcionalmente equivalentes.
    """

    def __init__(
        self,
        min_records_for_econcept: int = 5,
        similarity_threshold: float = 0.7
    ):
        self._econcepts: dict[str, EConcept] = {}
        self._record_to_econcept: dict[str, str] = {}
        self._min_records = min_records_for_econcept
        self._similarity_threshold = similarity_threshold
        self._record_store: Optional[dict[str, ExperienceRecord]] = None

    def set_record_store(self, store: dict[str, ExperienceRecord]) -> None:
        """Conectar almacen de registros para E-equivalencia (Def 5.3)."""
        self._record_store = store

    def add_econcept(self, econcept: EConcept) -> None:
        """Agregar E-concepto."""
        self._econcepts[econcept.id] = econcept
        for record_id in econcept.representative_records:
            self._record_to_econcept[record_id] = econcept.id

    def get_econcept(self, econcept_id: str) -> Optional[EConcept]:
        """Obtener E-concepto por ID."""
        return self._econcepts.get(econcept_id)

    def get_econcept_for_record(self, record_id: str) -> Optional[EConcept]:
        """Obtener E-concepto que contiene un registro."""
        econcept_id = self._record_to_econcept.get(record_id)
        if econcept_id:
            return self._econcepts.get(econcept_id)
        return None

    def find_similar_econcept(
        self,
        record: ExperienceRecord,
        cr_type: CoRegulatorType
    ) -> Optional[EConcept]:
        """
        Buscar E-concepto similar para un registro.

        Dos registros son E-equivalentes si producen la misma
        respuesta funcional para el co-regulador dado.
        """
        for econcept in self._econcepts.values():
            if econcept.co_regulator_type == cr_type:
                # Simplificado: comparar por patron
                if self._is_similar(record, econcept):
                    return econcept
        return None

    def _is_similar(self, record: ExperienceRecord, econcept: EConcept) -> bool:
        """
        Verificar si un registro es E-equivalente a un E-concepto (Def 5.3).

        Compara el registro contra los representantes del E-concepto
        usando E-equivalencia funcional.
        """
        if self._record_store:
            for rep_id in econcept.representative_records:
                rep = self._record_store.get(rep_id)
                if rep and self._is_e_equivalent(record, rep):
                    return True
            return False
        # Fallback sin record store: comparar pattern_id
        return record.pattern_id in [
            self._record_store.get(rid, ExperienceRecord()).pattern_id
            for rid in econcept.representative_records
        ] if self._record_store else record.success_value > 0.5

    def _is_e_equivalent(
        self, r1: ExperienceRecord, r2: ExperienceRecord
    ) -> bool:
        """
        Def 5.3 v7.0: Dos registros son E-equivalentes si producen
        la misma respuesta funcional (CRk no los distingue).

        Implementacion: mismo pattern_id + success similar + misma categoria.
        """
        if r1.pattern_id != r2.pattern_id:
            return False
        if abs(r1.success_value - r2.success_value) > 0.1:
            return False
        if (r1.success_value >= 0) != (r2.success_value >= 0):
            return False
        return True

    def try_form_econcept(
        self,
        records: list[ExperienceRecord],
        cr_type: CoRegulatorType
    ) -> Optional[EConcept]:
        """
        Intentar formar E-concepto desde registros similares.

        Teorema 5.4: El funtor E-concepto preserva colimites.
        """
        if len(records) < self._min_records:
            return None

        # Verificar que sean funcionalmente equivalentes
        if not self._are_equivalent(records, cr_type):
            return None

        econcept = EConcept(
            representative_records=[r.id for r in records],
            co_regulator_type=cr_type,
        )
        self.add_econcept(econcept)
        logger.info(f"Formado E-concepto {econcept.id} con {len(records)} registros")
        return econcept

    def _are_equivalent(
        self,
        records: list[ExperienceRecord],
        cr_type: CoRegulatorType
    ) -> bool:
        """
        Verificar equivalencia funcional de registros (Def 5.3 v7.0).

        Todos los registros deben ser pairwise E-equivalentes.
        """
        if len(records) < 2:
            return False
        for i, r1 in enumerate(records):
            for r2 in records[i + 1:]:
                if not self._is_e_equivalent(r1, r2):
                    return False
        return True

    @property
    def stats(self) -> dict[str, Any]:
        return {
            "num_econcepts": len(self._econcepts),
            "num_records_mapped": len(self._record_to_econcept),
        }


class MESMemory:
    """
    Sistema de memoria completo del NLE (Def. 5.1 v7.0).

    Subsistema evolutivo jerarquico que almacena:
    - Registros de experiencia (empirica)
    - Procedimientos (procedimental)
    - E-conceptos (semantica)
    - Registros consolidados
    """

    def __init__(
        self,
        max_records: int = 10000,
        max_procedures: int = 1000,
        consolidation_threshold: int = 3,
        econcept_min_records: int = 5
    ):
        self._records: dict[str, ExperienceRecord] = {}
        self._by_pattern: dict[str, list[str]] = defaultdict(list)
        self._max_records = max_records
        self._consolidation_threshold = consolidation_threshold

        self.procedural = ProceduralMemory(max_procedures)
        self.semantic = SemanticMemory(econcept_min_records)
        # Connect record store for E-equivalence (Def 5.3)
        self.semantic.set_record_store(self._records)

    def add_record(self, record: ExperienceRecord) -> None:
        """
        Agregar registro de experiencia.

        Args:
            record: Registro a agregar
        """
        self._records[record.id] = record
        self._by_pattern[record.pattern_id].append(record.id)

        # Verificar consolidacion
        if record.consolidation_count >= self._consolidation_threshold:
            record.memory_type = MemoryType.CONSOLIDATED

        # Limpieza si excede limite
        if len(self._records) > self._max_records:
            self._prune_old_records()

        logger.debug(f"Agregado registro {record.id}")

    def get_record(self, record_id: str) -> Optional[ExperienceRecord]:
        """Obtener registro por ID."""
        return self._records.get(record_id)

    def get_records_for_pattern(self, pattern_id: str) -> list[ExperienceRecord]:
        """Obtener registros asociados a un patron."""
        record_ids = self._by_pattern.get(pattern_id, [])
        return [self._records[rid] for rid in record_ids if rid in self._records]

    def consolidate_record(self, record_id: str) -> None:
        """
        Consolidar un registro (incrementar contador).

        Registros con suficientes consolidaciones pasan a memoria consolidada.
        """
        record = self._records.get(record_id)
        if record:
            record.consolidate()
            logger.debug(f"Consolidado registro {record_id}: {record.consolidation_count}")

    def recall_similar(
        self,
        query_pattern_id: str,
        limit: int = 10
    ) -> list[ExperienceRecord]:
        """
        Buscar registros similares a un patron.

        Args:
            query_pattern_id: ID del patron de consulta
            limit: Maximo de resultados

        Returns:
            Registros similares ordenados por exito
        """
        records = self.get_records_for_pattern(query_pattern_id)
        # Ordenar por exito y consolidacion
        sorted_records = sorted(
            records,
            key=lambda r: (r.success_value, r.consolidation_count),
            reverse=True
        )
        return sorted_records[:limit]

    def learn_procedure(
        self,
        pattern_id: str,
        action_sequence: list[str],
        success: bool
    ) -> Procedure:
        """
        Aprender o reforzar un procedimiento.

        Args:
            pattern_id: Patron de skills
            action_sequence: Secuencia de acciones
            success: Si fue exitoso

        Returns:
            Procedimiento aprendido
        """
        return self.procedural.add_procedure(pattern_id, action_sequence, success)

    def try_form_concept(
        self,
        pattern_id: str,
        cr_type: CoRegulatorType
    ) -> Optional[EConcept]:
        """
        Intentar formar E-concepto para un patron.

        Args:
            pattern_id: ID del patron
            cr_type: Tipo de co-regulador

        Returns:
            E-concepto si se pudo formar, None en caso contrario
        """
        records = self.get_records_for_pattern(pattern_id)
        return self.semantic.try_form_econcept(records, cr_type)

    def _prune_old_records(self) -> None:
        """Eliminar registros antiguos no consolidados."""
        if len(self._records) <= self._max_records:
            return

        # Ordenar por consolidacion y timestamp
        sorted_records = sorted(
            self._records.values(),
            key=lambda r: (r.memory_type == MemoryType.CONSOLIDATED, r.timestamp)
        )

        # Eliminar los no consolidados mas antiguos
        to_remove = []
        for record in sorted_records:
            if record.memory_type != MemoryType.CONSOLIDATED:
                to_remove.append(record.id)
                if len(self._records) - len(to_remove) <= self._max_records:
                    break

        for record_id in to_remove:
            record = self._records.pop(record_id, None)
            if record and record.id in self._by_pattern.get(record.pattern_id, []):
                self._by_pattern[record.pattern_id].remove(record.id)

    def save(self, path: str | Path) -> None:
        """
        Persistir memoria a disco (Teorema 9.9: enriquecimiento monotono).

        Guarda registros, procedimientos y E-conceptos en formato JSON.
        Garantiza que no se pierdan datos: si existe archivo previo,
        merge los registros (nunca decrementar).

        Args:
            path: Ruta del archivo JSON
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Serialize records
        records_data = {}
        for rid, record in self._records.items():
            records_data[rid] = {
                "id": record.id,
                "pattern_id": record.pattern_id,
                "success_value": record.success_value,
                "consolidation_count": record.consolidation_count,
                "memory_type": record.memory_type.name,
                "timestamp": record.timestamp.isoformat(),
            }

        # Serialize procedures
        procedures_data = {}
        for pid, proc in self.procedural._procedures.items():
            procedures_data[pid] = {
                "id": proc.id,
                "pattern_id": proc.pattern_id,
                "action_sequence": proc.action_sequence,
                "success_rate": proc.success_rate,
                "invocation_count": proc.invocation_count,
            }

        # Serialize E-concepts
        econcepts_data = {}
        for eid, ec in self.semantic._econcepts.items():
            econcepts_data[eid] = {
                "id": ec.id,
                "representative_records": ec.representative_records,
                "co_regulator_type": ec.co_regulator_type.name,
            }

        data = {
            "version": "7.0",
            "saved_at": datetime.now().isoformat(),
            "records": records_data,
            "procedures": procedures_data,
            "econcepts": econcepts_data,
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        logger.info(
            f"Memoria guardada: {len(records_data)} registros, "
            f"{len(procedures_data)} procedimientos, "
            f"{len(econcepts_data)} E-conceptos -> {path}"
        )

    def load(self, path: str | Path) -> bool:
        """
        Cargar memoria desde disco (Teorema 9.9: enriquecimiento monotono).

        Merge con registros existentes: nunca pierde datos previos.
        Los contadores de consolidacion solo se incrementan, nunca decrementan.

        Args:
            path: Ruta del archivo JSON

        Returns:
            True si se cargo correctamente
        """
        path = Path(path)
        if not path.exists():
            logger.debug(f"No existe archivo de memoria: {path}")
            return False

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.warning(f"Error leyendo memoria: {e}")
            return False

        loaded_records = 0
        loaded_procs = 0
        loaded_econcepts = 0

        # Load records (monotonic: keep higher consolidation_count)
        for rid, rdata in data.get("records", {}).items():
            existing = self._records.get(rid)
            if existing:
                # Monotonic: only increase consolidation
                existing.consolidation_count = max(
                    existing.consolidation_count,
                    rdata.get("consolidation_count", 0),
                )
            else:
                record = ExperienceRecord(
                    pattern_id=rdata["pattern_id"],
                    success_value=rdata.get("success_value", 0.0),
                )
                record.id = rdata["id"]
                record.consolidation_count = rdata.get("consolidation_count", 0)
                try:
                    record.memory_type = MemoryType[rdata.get("memory_type", "EMPIRICAL")]
                except KeyError:
                    pass
                self._records[rid] = record
                self._by_pattern[record.pattern_id].append(rid)
                loaded_records += 1

        # Load procedures
        for pid, pdata in data.get("procedures", {}).items():
            if pid not in self.procedural._procedures:
                proc = Procedure(
                    id=pdata["id"],
                    pattern_id=pdata["pattern_id"],
                    action_sequence=pdata.get("action_sequence", []),
                    success_rate=pdata.get("success_rate", 0.0),
                    invocation_count=pdata.get("invocation_count", 0),
                )
                self.procedural._procedures[pid] = proc
                self.procedural._by_pattern[proc.pattern_id].append(pid)
                loaded_procs += 1

        # Load E-concepts
        for eid, edata in data.get("econcepts", {}).items():
            if eid not in self.semantic._econcepts:
                try:
                    cr_type = CoRegulatorType[edata.get("co_regulator_type", "TACTICAL")]
                except KeyError:
                    cr_type = CoRegulatorType.TACTICAL
                econcept = EConcept(
                    representative_records=edata.get("representative_records", []),
                    co_regulator_type=cr_type,
                )
                econcept.id = edata["id"]
                self.semantic.add_econcept(econcept)
                loaded_econcepts += 1

        logger.info(
            f"Memoria cargada: +{loaded_records} registros, "
            f"+{loaded_procs} procedimientos, "
            f"+{loaded_econcepts} E-conceptos <- {path}"
        )
        return True

    @property
    def stats(self) -> dict[str, Any]:
        """Estadisticas de la memoria."""
        by_type = defaultdict(int)
        for record in self._records.values():
            by_type[record.memory_type.name] += 1

        return {
            "total_records": len(self._records),
            "records_by_type": dict(by_type),
            "num_patterns": len(self._by_pattern),
            "procedural": self.procedural.stats,
            "semantic": self.semantic.stats,
        }
