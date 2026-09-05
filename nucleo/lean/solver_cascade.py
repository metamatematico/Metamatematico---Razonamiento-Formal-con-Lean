"""
Solver Cascade - Automated Tactic Resolution
=============================================

Adapted from lean4-skills/plugins/lean4-theorem-proving/scripts/solverCascade.py

Tries automated solvers in sequence before resampling with LLM.
Handles 40-60% of simple cases mechanically.

Cascade order (APOLLO-inspired):
1. rfl (definitional equality)
2. simp (simplifier)
3. ring (ring normalization)
4. linarith (linear arithmetic)
5. nlinarith (nonlinear arithmetic)
6. omega (arithmetic automation)
7. exact? (proof search)
8. apply? (proof search)
9. aesop (general automation)

Reference:
- APOLLO: https://arxiv.org/abs/2505.05758
- lean4-skills solverCascade.py
"""

from __future__ import annotations

import logging
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Optional, TYPE_CHECKING
from pathlib import Path

from nucleo.lean.client import LeanClient, LeanResult, LeanResultStatus

if TYPE_CHECKING:
    from nucleo.graph.category import SkillCategory
    from nucleo.rl.networks import ActorCriticNetwork

logger = logging.getLogger(__name__)


# Solvers with their timeouts (seconds)
SOLVER_CASCADE = [
    ("rfl", 1),
    ("simp", 2),
    # norm_num, field_simp y ring_nf faltaban, y LeanWorkbook demuestra que
    # son de las mas usadas: 1.142, 1.306 y 447 usos respectivamente sobre
    # 18.985 pruebas. Ignorarlas dejaba fuera ~15% de los cierres posibles.
    ("norm_num", 2),
    ("ring", 2),
    ("ring_nf", 3),
    ("field_simp", 3),
    ("linarith", 3),
    ("nlinarith", 4),
    ("omega", 3),
    ("exact?", 5),
    ("apply?", 5),
    ("aesop", 8),
]

#: LA CASCADA EN UN SOLO COMPILADO.
#:
#: Cada intento costaba un `check_code`, o sea un proceso de Lean entero. Y el
#: coste NO esta en la tactica: esta en arrancar Lean y elaborar los imports.
#: Medido sobre un objetivo que ninguna de las doce cierra —el caso agotado,
#: que es el que produce el veredicto `parcial` y donde el alumno espera:
#:
#:     un compilado por tactica   185,5 s   (12 x ~15,5 s)
#:     `first |` en un compilado    15,5 s
#:     ------------------------------------
#:     12,0x, 170 segundos menos
#:
#: `first |` NO ES EQUIVALENTE AL BUCLE POR SI SOLO, y creerlo costaba el
#: resultado. `first` se queda con la primera rama que NO LANZA EXCEPCION; el
#: bucle se quedaba con la primera que hace COMPILAR EL FICHERO. No es lo
#: mismo: una tactica puede "progresar" sin cerrar el objetivo.
#:
#:     first | (rfl ; ...) | (simp ; ...) | (norm_num ; ...) | (ring ; ...)
#:     sobre  a + b = b + a
#:
#:       sin `done`   norm_num progresa, first la acepta -> UNSOLVED GOALS
#:       con `done`   norm_num no cierra, se descarta    -> gana ring
#:
#: Sin `done` la cascada declaraba agotados casos que el bucle cerraba, y lo
#: hacia en silencio: mismo tiempo, mismo formato de resultado, veredicto
#: distinto. `done` falla si quedan objetivos, y con el la equivalencia si se
#: sostiene.
#:
#: Y `trace "ELEGIDA:t"` en cada rama es lo que hace que Lean diga cual gano;
#: sin eso la ganancia costaria saber que tactica fue, que es justo lo que la
#: cascada tiene que devolver.
#:
#: DONDE NO GANA: si la primera tactica cierra, hoy tambien es un compilado.
#: La ganancia esta entera en la cola, y la cola es donde duele.
#:
#: Se deja en False para volver al bucle sin tocar codigo.
CASCADA_EN_UN_COMPILADO = True

#: Marca que Lean imprime desde la rama que gano. Distintiva a proposito: se
#: busca en la salida cruda y no puede colisionar con nada de Mathlib.
_MARCA = "ELEGIDA:"


def _bloque_first(solvers) -> str:
    """`first | (t1; trace ...) | (t2; trace ...) | ...`, en UNA linea.

    En una sola linea a proposito: el `sorry` que se sustituye esta dentro de
    un bloque `by` con su indentacion, y Lean es sensible al espaciado. Un
    reemplazo de una linea por otra no puede romper la estructura; uno
    multilinea si.

    EL ESPACIO ANTES DEL `;` NO ES ESTILO. `LeanClient._normalize_code` lleva
    una tabla de reescrituras para arreglar salidas del modelo, y una de ellas
    es literal:

        ("ring_nf;", "ring_nf
  ")

    Con `(ring_nf; trace ...)` esa regla mete un salto de linea EN MEDIO del
    bloque y lo parte en dos, y Lean responde «unexpected identifier». El
    sintoma aparecia solo con la cascada entera —`ring_nf` es la quinta— asi
    que probar tactica a tactica no lo delataba.

    `ring_nf ; trace` no casa con el patron. Y hay un test que comprueba que
    el bloque sobrevive a `_normalize_code`, para que la proxima regla de esa
    tabla no lo vuelva a romper sin avisar.
    """
    ramas = " | ".join(
        '(%s ; done ; trace "%s%s")' % (t, _MARCA, t) for t, _ in solvers)
    return "first | " + ramas


# Error types that won't benefit from the cascade
SKIP_ERROR_TYPES = frozenset([
    "unknown_ident",
    "synth_implicit",
    "recursion_depth",
    "synth_instance",
])


class GoalAnalyzer:
    """
    Analyze Lean goal structure to prioritize tactics.

    Uses regex patterns to detect goal type, then reorders the solver
    cascade so the most likely tactics are tried first. Optionally
    consults the skill graph to find tactic skills connected to the
    relevant mathematical domain.
    """

    # (regex_pattern, priority_tactics) — checked in order, first match wins
    GOAL_PATTERNS: list[tuple[str, list[str]]] = [
        # Ring/field algebra: a * b + c = ...
        (r"[\+\-\*\^].*=.*[\+\-\*\^]", ["ring", "nlinarith", "linarith"]),
        # Natural/integer arithmetic with inequalities
        (r"(Nat|Int|Fin|ℕ|ℤ).*[≤<≥>]|[≤<≥>].*(Nat|Int|Fin|ℕ|ℤ)", ["omega", "linarith", "simp"]),
        # Pure arithmetic equalities (n + 0 = n)
        (r"\b\d+\s*[\+\-\*]\s*\d+\s*=", ["omega", "simp", "ring"]),
        # Logical connectives
        (r"[∧∨¬↔]|True|False", ["simp", "tauto", "aesop"]),
        # Quantifiers / implications
        (r"[∀∃]|→", ["simp", "exact", "apply?"]),
        # List/array operations
        (r"List\.|Array\.|length|append|map", ["simp", "omega"]),
    ]

    # Map tactic skill IDs to their solver cascade names
    _SKILL_TO_SOLVER = {
        "tactic-simp": "simp",
        "tactic-ring": "ring",
        "tactic-omega": "omega",
        "tactic-exact": "exact?",
        "tactic-apply": "apply?",
        "tactic-aesop": "aesop",
        "tactic-induction": "induction",
        "tactic-rewrite": "rw",
        "tactic-calc": "calc",
    }

    def prioritize(
        self,
        goal: str,
        graph: Optional[SkillCategory] = None,
        domain_tactic: str = "",
        domain_order: Optional[list[str]] = None,
    ) -> list[tuple[str, int]]:
        """
        Reordena SOLVER_CASCADE según el objetivo, el área y el grafo.

        EL ORDEN DE LAS FUENTES IMPORTA, y estaba al revés. La táctica del área
        iba PRIMERA, por delante de los patrones del objetivo. Dos motivos para
        bajarla:

        1. El área es un prior débil y estaba mal. Medido contra las pruebas de
           Mathlib, siete de once áreas proponían una táctica que no cierra ni
           una sola prueba de su propia área (ver CATEGORY_TACTIC_ORDER). Ante
           un objetivo de álgebra la cascada probaba `ring` primero, que en el
           álgebra de Mathlib cierra el 0 % de las pruebas de una línea.
        2. El objetivo es evidencia DIRECTA. `GOAL_PATTERNS` mira si hay sumas
           y productos, o desigualdades sobre ℕ/ℤ. Eso discrimina; el área no,
           porque `simp` gana en las once áreas sin excepción.

        Cada intento fallido cuesta una invocación de Lean, así que poner
        delante el prior malo desplazaba a la señal buena y pagaba el retraso.

        Sigue siendo una PERMUTACIÓN de SOLVER_CASCADE: ninguna reordenación
        puede hacer que Lean acepte algo falso, solo cambia cuánto se tarda.

        Args:
            goal: texto del objetivo Lean.
            graph: grafo de habilidades, para el orden según dominio.
            domain_tactic: táctica aprendida de éxito real, si la hay.
                Va por delante de `domain_order` porque es experiencia de
                este sistema, no un prior de tabla.
            domain_order: tácticas del área por frecuencia real medida. Es lo
                que conviene pasar — un orden, no un nombre.

        Returns:
            La cascada reordenada, lista de (solver, timeout).
        """
        priority_names: list[str] = []
        solver_names = {name for name, _ in SOLVER_CASCADE}

        # 1. El objetivo, que es evidencia directa: manda.
        for pattern, tactics in self.GOAL_PATTERNS:
            if re.search(pattern, goal):
                for t in tactics:
                    if t not in priority_names:
                        priority_names.append(t)
                break  # First match wins

        # 2. La táctica APRENDIDA, si la hay. Es experiencia real de éxito en
        #    consultas parecidas de este sistema, no un prior de tabla, así
        #    que va por delante del orden del área.
        # 3. El área, como prior medido: detrás del objetivo, nunca delante.
        for t in ([domain_tactic] if domain_tactic else []) + list(domain_order or ()):
            if t in solver_names and t not in priority_names:
                priority_names.append(t)

        # 4. El grafo: tácticas vecinas de los dominios que casan con el goal.
        if graph is not None:
            graph_tactics = self._tactics_from_graph(goal, graph)
            for t in graph_tactics:
                if t not in priority_names:
                    priority_names.append(t)

        if not priority_names:
            return list(SOLVER_CASCADE)

        # Y se arma la cascada: las prioritarias delante, el resto detrás.
        solver_dict = {name: timeout for name, timeout in SOLVER_CASCADE}
        ordered = []
        seen = set()
        for name in priority_names:
            if name in solver_dict and name not in seen:
                ordered.append((name, solver_dict[name]))
                seen.add(name)
        for name, timeout in SOLVER_CASCADE:
            if name not in seen:
                ordered.append((name, timeout))
                seen.add(name)

        return ordered

    def _tactics_from_graph(
        self, goal: str, graph: SkillCategory
    ) -> list[str]:
        """Find solver names from tactic skills connected to relevant domains."""
        goal_lower = goal.lower()
        tactics = []

        for skill_id in graph.skill_ids:
            # Check if skill name appears in goal
            skill = graph.get_skill(skill_id)
            if not skill:
                continue

            # Match domain skill names against goal keywords
            name_tokens = skill.name.lower().replace("-", " ").split()
            if any(tok in goal_lower for tok in name_tokens if len(tok) > 3):
                # Found relevant domain — check its neighbors for tactic skills
                for nbr_id in graph.neighbors(skill_id):
                    if nbr_id in self._SKILL_TO_SOLVER:
                        solver = self._SKILL_TO_SOLVER[nbr_id]
                        if solver not in tactics:
                            tactics.append(solver)

        return tactics


class TacticRanker:
    """
    Ordena la cascada con un modelo entrenado sobre datos reales.

    Sustituye al ranking por similitud coseno del GNN, que daba cosenos de
    0,01-0,09 —embeddings practicamente ortogonales al goal— porque la red se
    entreno con etiqueta constante y nunca vio una senal discriminativa.

    Este modelo se entreno sobre 9.488 pares (state_before -> tactic) de
    LeanWorkbook (scripts/train_tactic_ranker.py):

        accuracy               59,7%
        linea base mayoritaria 31,8%   (responder siempre "nlinarith")
        top-3 accuracy         88,1%   <- la metrica que importa al rankear

    El 88% de top-3 significa que la tactica correcta suele estar entre las
    tres primeras que prueba la cascada.

    SOUNDNESS: devuelve una PERMUTACION de la lista recibida. Es la hipotesis
    del axioma `gnnRankTactics_perm` y del teorema `cascade_gnn_iff_exists`
    (CoRegulatorNetwork.lean): reordenar no puede hacer demostrable lo que no
    lo es, asi que el orden es libre para optimizar.
    """

    def __init__(self, ruta_modelo: "Optional[Path]" = None) -> None:
        self._modelo = None
        self._clases: list[str] = []
        self._ruta = ruta_modelo
        self._intentado = False

    def _cargar(self) -> bool:
        if self._modelo is not None:
            return True
        if self._intentado:
            return False
        self._intentado = True
        ruta = self._ruta
        if ruta is None:
            from pathlib import Path as _P
            ruta = _P(__file__).resolve().parent.parent.parent / "data" / "tactic_ranker.pkl"
        try:
            import pickle
            with open(ruta, "rb") as f:
                datos = pickle.load(f)
            self._modelo = datos["modelo"]
            self._clases = list(datos["clases"])
            logger.info(
                "TacticRanker cargado: %d tacticas (%s)",
                len(self._clases), ", ".join(self._clases[:5]) + "...",
            )
            return True
        except FileNotFoundError:
            logger.info("TacticRanker: no hay modelo entrenado en %s", ruta)
        except Exception as exc:
            logger.warning("TacticRanker: no se pudo cargar (%s)", exc)
        return False

    @property
    def disponible(self) -> bool:
        return self._cargar()

    def rank(
        self,
        goal_text: str,
        solvers: list[tuple[str, int]],
    ) -> list[tuple[str, int]]:
        """Permutacion de `solvers` por probabilidad predicha para el goal."""
        if not goal_text or not self._cargar():
            return solvers
        try:
            probas = self._modelo.predict_proba([goal_text])[0]
            score = dict(zip(self._clases, probas))
        except Exception as exc:
            logger.warning("TacticRanker.rank: %s", exc)
            return solvers

        # Los solvers fuera del vocabulario del modelo (exact?, apply?) reciben
        # la MEDIANA, no cero. Hundirlos al fondo por no estar en el vocabulario
        # fue justamente el defecto del ranker anterior: mandaba rfl, linarith y
        # nlinarith al final —los mas baratos— y subia exact?/apply?, los mas
        # caros, invirtiendo la cascada por coste.
        import statistics
        conocidos = [score[n] for n, _ in solvers if n in score]
        neutro = statistics.median(conocidos) if conocidos else 0.0

        ordenados = sorted(
            solvers, key=lambda par: score.get(par[0], neutro), reverse=True
        )
        logger.debug(
            "TacticRanker: %s",
            [f"{n}={score.get(n, neutro):.2f}" for n, _ in ordenados[:4]],
        )
        return ordenados


class GNNTacticRanker:
    """
    Rankea los solvers de la cascada usando los embeddings aprendidos por el GNN.

    El ActorCriticNetwork fue entrenado con PPO + recompensas de verificación Lean.
    Su componente GNN produce embeddings de nodo que codifican el rol estructural
    de cada skill/táctica en el grafo. El goal_encoder mapea el texto del goal
    al mismo espacio latente. Rankear por similitud coseno usa esta representación
    conjunta aprendida para ordenar tácticas — no es una heurística fija.

    Implementa CoRegulatorNetwork.lean §VI.5: gnnRankTactics es una permutación
    de la lista original, por lo que la soundness se preserva (teorema
    cascade_gnn_iff_exists).
    """

    # Inverso de GoalAnalyzer._SKILL_TO_SOLVER: nombre solver → skill ID en el grafo
    _SOLVER_TO_SKILL: dict[str, str] = {
        "simp":   "tactic-simp",
        "ring":   "tactic-ring",
        "omega":  "tactic-omega",
        "exact?": "tactic-exact",
        "apply?": "tactic-apply",
        "aesop":  "tactic-aesop",
        "rw":     "tactic-rewrite",
        "calc":   "tactic-calc",
    }

    def __init__(self, network: "ActorCriticNetwork", graph: "SkillCategory") -> None:
        self._net = network
        self._graph = graph
        self._node_embs = None          # Tensor (N, 256), cached tras primer uso
        self._skill_id_to_idx: dict[str, int] = {}

    def _ensure_cached(self) -> bool:
        """Calcula y cachea los embeddings de nodo del GNN para el grafo actual."""
        if self._node_embs is not None:
            return True
        try:
            from nucleo.rl.gnn import graph_to_pyg, TORCH_AVAILABLE
            if not TORCH_AVAILABLE:
                return False
            import torch
            data = graph_to_pyg(self._graph)
            if data is None or data.x.size(0) == 0:
                return False
            self._net.gnn.eval()
            with torch.no_grad():
                self._node_embs = self._net.gnn.forward_nodes(data)  # (N, 256)
            self._skill_id_to_idx = {
                s.id: i for i, s in enumerate(self._graph.skills)
            }
            return True
        except Exception as exc:
            logger.warning("GNNTacticRanker: no se pudo calcular embeddings: %s", exc)
            return False

    def rank(
        self,
        goal_text: str,
        solvers: list[tuple[str, int]],
    ) -> list[tuple[str, int]]:
        """
        Devuelve una PERMUTACIÓN de `solvers` ordenada por similitud GNN.

        Cada táctica con un nodo en el grafo recibe como score la similitud coseno
        entre el embedding del goal (goal_encoder) y el embedding del nodo de táctica
        (GNN.forward_nodes). Las tácticas sin nodo correspondiente reciben score 0.

        Garantía: el conjunto de tácticas no cambia — solo el orden.
        Esto corresponde al axioma gnnRankTactics_perm en CoRegulatorNetwork.lean.
        """
        if not self._ensure_cached():
            return solvers
        try:
            import torch
            import torch.nn.functional as F
            from nucleo.rl.networks import encode_goal, GOAL_DIM

            goal_raw = encode_goal(goal_text, GOAL_DIM)   # (32,)
            self._net.eval()
            with torch.no_grad():
                goal_emb = self._net.goal_encoder(
                    goal_raw.unsqueeze(0)
                ).squeeze(0)                               # (256,)

            scores: dict[str, float] = {}
            for name, _ in solvers:
                skill_id = self._SOLVER_TO_SKILL.get(name)
                idx = self._skill_id_to_idx.get(skill_id, -1) if skill_id else -1
                if idx >= 0 and self._node_embs is not None:
                    node_emb = self._node_embs[idx]        # (256,)
                    scores[name] = F.cosine_similarity(
                        goal_emb.unsqueeze(0), node_emb.unsqueeze(0)
                    ).item()
                else:
                    scores[name] = 0.0

            ranked = sorted(solvers, key=lambda p: scores.get(p[0], 0.0), reverse=True)
            logger.debug(
                "GNN tactic ranking: %s (scores: %s)",
                [n for n, _ in ranked[:4]],
                [f"{scores.get(n, 0):.3f}" for n, _ in ranked[:4]],
            )
            return ranked
        except Exception as exc:
            logger.warning("GNNTacticRanker.rank: %s", exc)
            return solvers

    def invalidate_cache(self) -> None:
        """Invalida el caché de embeddings (llamar si el grafo cambia)."""
        self._node_embs = None
        self._skill_id_to_idx = {}


@dataclass
class CascadeResult:
    """Result of running the solver cascade."""
    success: bool
    solver: Optional[str] = None
    replacement_code: Optional[str] = None
    solvers_tried: int = 0
    lean_result: Optional[LeanResult] = None


class SolverCascade:
    """
    Solver cascade for automated sorry resolution.

    Tries a sequence of Lean tactics to replace 'sorry' placeholders,
    from simplest (rfl) to most powerful (aesop).

    Example:
        cascade = SolverCascade(lean_client)

        # Try to fill a sorry
        result = await cascade.try_fill_sorry(
            code='theorem foo : 1 + 1 = 2 := by\\n  sorry',
            sorry_line=2,
        )
        if result.success:
            print(f"Solved with: {result.solver}")
    """

    def __init__(
        self,
        lean_client: LeanClient,
        solvers: Optional[list[tuple[str, int]]] = None,
        graph: Optional["SkillCategory"] = None,
        gnn_ranker: Optional[GNNTacticRanker] = None,
    ):
        self._lean = lean_client
        self._solvers = solvers or list(SOLVER_CASCADE)
        self._graph = graph
        self._goal_analyzer = GoalAnalyzer()
        self._gnn_ranker: Optional[GNNTacticRanker] = gnn_ranker

    def set_gnn_ranker(self, ranker: GNNTacticRanker) -> None:
        """Conecta el GNNTacticRanker (llamado desde core.py tras cargar pesos)."""
        self._gnn_ranker = ranker

    def set_tactic_ranker(self, ranker: "TacticRanker") -> None:
        """
        Conecta el rankeador entrenado. Tiene PRIORIDAD sobre el del GNN:
        aquel se entreno con etiqueta constante y sus embeddings no discriminan
        (cosenos 0,01-0,09), mientras este mide 88,1% de top-3 sobre datos
        reales de LeanWorkbook.
        """
        self._tactic_ranker = ranker

    async def try_fill_sorry(
        self,
        code: str,
        sorry_line: int,
        error_type: Optional[str] = None,
        imports: Optional[list[str]] = None,
    ) -> CascadeResult:
        """
        Try solver cascade to replace a sorry at a given line.

        Args:
            code: Full Lean source code containing sorry
            sorry_line: 1-indexed line number of the sorry
            error_type: If known, skip cascade for incompatible errors
            imports: Additional imports to prepend

        Returns:
            CascadeResult with success status and solver used
        """
        if error_type and error_type in SKIP_ERROR_TYPES:
            logger.debug(f"Skipping cascade for error type: {error_type}")
            return CascadeResult(success=False, solvers_tried=0)

        lines = code.split("\n")
        if sorry_line < 1 or sorry_line > len(lines):
            return CascadeResult(success=False, solvers_tried=0)

        target_line = lines[sorry_line - 1]
        if "sorry" not in target_line:
            return CascadeResult(success=False, solvers_tried=0)

        if CASCADA_EN_UN_COMPILADO:
            return await self._cascada_de_un_tiro(lines, sorry_line - 1, imports)

        solvers_tried = 0
        statuses: list[str] = []
        for solver, _timeout in self._solvers:
            solvers_tried += 1
            modified_code = self._replace_sorry(lines, sorry_line - 1, solver)

            if imports:
                import_block = "\n".join(f"import {imp}" for imp in imports) + "\n\n"
                modified_code = import_block + modified_code

            logger.debug(f"Trying solver: {solver}")
            result = await self._lean.check_code(modified_code)

            if result.is_success:
                logger.info(f"Solver cascade: {solver} succeeded")
                return CascadeResult(
                    success=True,
                    solver=solver,
                    replacement_code=solver,
                    solvers_tried=solvers_tried,
                    lean_result=result,
                )

            # Sin esto la cascada agotada es indistinguible entre "el enunciado
            # no compila" y "las tacticas no cierran el goal" -- diagnosticos
            # opuestos. El status separa ademas el caso NOT_AVAILABLE (lake no
            # resuelto en este entorno), que no tiene nada que ver con tacticas.
            statuses.append(result.status.name)
            err = (result.get_first_error() or "").replace("\n", " ")[:200]
            logger.debug(
                f"Solver {solver} failed: status={result.status.name}"
                + (f" | {err}" if err else "")
            )

        summary = dict(Counter(statuses))
        logger.debug(
            f"Solver cascade exhausted after {solvers_tried} attempts "
            f"(statuses: {summary})"
        )
        return CascadeResult(success=False, solvers_tried=solvers_tried)

    async def _cascada_de_un_tiro(
        self,
        lines: list[str],
        idx: int,
        imports: Optional[list[str]] = None,
    ) -> CascadeResult:
        """Las doce tacticas en un `first |`, un solo proceso de Lean.

        Devuelve lo mismo que el bucle: si cerro, cual cerro y cuantas se
        probaron hasta ella. `solvers_tried` se deduce de la posicion de la
        ganadora en el orden vigente, que es la cuenta que el bucle daba.
        """
        modified_code = self._replace_sorry(
            lines, idx, _bloque_first(self._solvers))
        if imports:
            cab = "\n".join(f"import {imp}" for imp in imports)
            modified_code = cab + "\n\n" + modified_code

        result = await self._lean.check_code(modified_code)
        orden = [t for t, _ in self._solvers]

        if result.is_success:
            # DE LOS MENSAJES, no de `output`. `output` son lineas JSON, y
            # partirlas por la marca devolvia `rfl","endPos":{...` como
            # nombre de tactica. El mensaje ya viene con el texto limpio en
            # `data`.
            ganadora = None
            for m in result.messages:
                txt = str(m.get("data") or m.get("message") or "")
                if txt.startswith(_MARCA):
                    ganadora = txt[len(_MARCA):].strip()
                    break
            # Cerro pero sin marca: pasa si el objetivo ya estaba cerrado o si
            # el trace no llego a la salida. Se dice cual es el caso en vez de
            # inventar una tactica.
            if ganadora is None:
                logger.debug("cascada de un tiro: cerro sin marca ELEGIDA")
                return CascadeResult(
                    success=True, solver="first|", replacement_code="first|",
                    solvers_tried=len(orden), lean_result=result)
            pos = orden.index(ganadora) + 1 if ganadora in orden else len(orden)
            logger.info("Solver cascade (un compilado): %s cerro", ganadora)
            return CascadeResult(
                success=True, solver=ganadora, replacement_code=ganadora,
                solvers_tried=pos, lean_result=result)

        err = " ".join((result.get_first_error() or "").split())[:200]
        logger.debug(
            "cascada de un tiro agotada: %d tacticas, status=%s%s",
            len(orden), result.status.name, (" | " + err) if err else "")
        return CascadeResult(success=False, solvers_tried=len(orden))

    async def try_fill_sorry_smart(
        self,
        code: str,
        sorry_line: int,
        goal_text: str = "",
        error_type: Optional[str] = None,
        imports: Optional[list[str]] = None,
        domain_tactic: str = "",
        domain_order: Optional[list[str]] = None,
        area_premisas: str = "",
    ) -> CascadeResult:
        """
        Goal-aware solver cascade that reorders tactics by goal structure.

        Uses GoalAnalyzer to prioritize tactics based on the goal text,
        the skill graph, and the domain tactic provided by the ColimitAgent
        of the detected mathematical area (paper NLE v7.0 §3.5).

        Args:
            code: Full Lean source code containing sorry
            sorry_line: 1-indexed line number of the sorry
            goal_text: The Lean goal to analyze for tactic ordering
            error_type: If known, skip cascade for incompatible errors
            imports: Additional imports to prepend
            domain_tactic: Default tactic of the ColimitAgent for the
                detected area (e.g. "ring" for algebra, "linarith" for
                optimization). Placed first in the cascade.

        Returns:
            CascadeResult with success status and solver used
        """
        if not goal_text and not domain_tactic and not domain_order:
            return await self.try_fill_sorry(code, sorry_line, error_type, imports)

        # Etapa 1: reordenamiento heuristico. El objetivo primero, luego la
        # tactica aprendida, luego el orden medido del area. Ver prioritize.
        smart_order = self._goal_analyzer.prioritize(
            goal_text, self._graph, domain_tactic=domain_tactic,
            domain_order=domain_order,
        )

        # Stage 2: reordenamiento aprendido (permutacion — soundness intacta).
        # Preferencia: modelo entrenado > GNN. Ver set_tactic_ranker.
        _entrenado = getattr(self, "_tactic_ranker", None)
        if _entrenado is not None and goal_text and _entrenado.disponible:
            smart_order = _entrenado.rank(goal_text, smart_order)
            logger.debug(
                "Cascada (modelo entrenado): %s...",
                [s for s, _ in smart_order[:4]],
            )
        elif self._gnn_ranker is not None and goal_text:
            smart_order = self._gnn_ranker.rank(goal_text, smart_order)
            logger.debug(
                "GNN+heuristic cascade order: %s...",
                [s for s, _ in smart_order[:4]],
            )
        else:
            logger.debug(
                "Heuristic cascade order (no GNN): %s...",
                [s for s, _ in smart_order[:4]],
            )

        # LAS PREMISAS, AL FINAL DE LA CASCADA.
        #
        # Medido con Lean como juez sobre teoremas de una linea de Mathlib: la
        # cascada cierra el 16 %, y de los 21 que fallaron OCHO usaban `simp`
        # —que la cascada si ofrece—. Mathlib escribe `simp [foo, bar]`, y la
        # cascada probaba `simp` a secas: no podia reproducir ninguna prueba
        # que necesitara CITAR un hecho.
        #
        # Van detras a proposito: son mas caras y solo tienen sentido cuando la
        # version desnuda fallo. Si la desnuda cierra, esto no llega a probarse.
        # Y no tocan la correccion: una premisa mal elegida hace fallar la
        # tactica y se pasa a la siguiente.
        try:
            from nucleo.lean.premisas import tacticas_con_premisas
            extra = tacticas_con_premisas(goal_text, area_premisas or "")
            if extra:
                smart_order = list(smart_order) + [
                    e for e in extra if e[0] not in {n for n, _ in smart_order}]
        except Exception as e:
            logger.debug("sin premisas (%s)", type(e).__name__)

        # Temporarily swap solver order and run
        original_solvers = self._solvers
        self._solvers = smart_order
        try:
            result = await self.try_fill_sorry(code, sorry_line, error_type, imports)
        finally:
            self._solvers = original_solvers

        return result

    async def try_fill_theorem(
        self,
        name: str,
        statement: str,
        imports: Optional[list[str]] = None,
    ) -> CascadeResult:
        """
        Try solver cascade to prove a theorem automatically.

        Args:
            name: Theorem name
            statement: Theorem statement
            imports: Required imports

        Returns:
            CascadeResult with success status
        """
        import_lines = ""
        if imports:
            import_lines = "\n".join(f"import {imp}" for imp in imports) + "\n\n"

        solvers_tried = 0
        for solver, _timeout in self._solvers:
            solvers_tried += 1
            code = f"{import_lines}theorem {name} : {statement} := by\n  {solver}\n"

            result = await self._lean.check_code(code)

            if result.is_success:
                logger.info(f"Theorem {name} proved by: {solver}")
                return CascadeResult(
                    success=True,
                    solver=solver,
                    replacement_code=solver,
                    solvers_tried=solvers_tried,
                    lean_result=result,
                )

        return CascadeResult(success=False, solvers_tried=solvers_tried)

    async def try_multiple_sorries(
        self,
        code: str,
        sorry_lines: list[int],
    ) -> list[CascadeResult]:
        """
        Try cascade on multiple sorries in a file.

        Processes from last to first to avoid line shifts.

        Args:
            code: Full Lean source code
            sorry_lines: 1-indexed line numbers of sorries

        Returns:
            List of CascadeResults, one per sorry
        """
        results = []
        current_code = code

        # Process from last to first to preserve line numbers
        for line_num in sorted(sorry_lines, reverse=True):
            result = await self.try_fill_sorry(current_code, line_num)
            results.append(result)

            if result.success:
                # Update code with the fix for next iteration
                lines = current_code.split("\n")
                current_code = self._replace_sorry(
                    lines, line_num - 1, result.replacement_code
                )

        results.reverse()  # Return in original order
        return results

    def _replace_sorry(
        self, lines: list[str], line_idx: int, solver: str
    ) -> str:
        """Replace sorry with solver on the given line."""
        modified = list(lines)
        target = modified[line_idx]

        if "sorry" in target:
            modified[line_idx] = target.replace("sorry", solver, 1)
        else:
            # Fallback: append after 'by' on same or previous line
            indent = len(target) - len(target.lstrip())
            modified[line_idx] = target + "\n" + " " * (indent + 2) + solver

        return "\n".join(modified)
