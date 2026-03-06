# Plan de Implementación: NLE v7.0 — Semántica Categórica Completa

> Cerrar los 5 gaps fundamentales entre la especificación MES (Ehresmann) y el código actual.

---

## Principios de Diseño

1. **Bottom-up**: Cada capa se prueba antes de construir la siguiente.
2. **Máximo rigor verificable**: Las propiedades universales se VERIFICAN en runtime.
3. **No romper lo existente**: Todos los tests actuales deben seguir pasando.
4. **Incremental**: Cada paso produce un commit funcional con tests nuevos.

---

## Fase 0: Corrección de Bugs Existentes

**Archivos**: `nucleo/mes/patterns.py`, `nucleo/graph/category.py`, `nucleo/mes/co_regulators.py`

### 0.1 Bug en patterns.py (get_morphism vs get_morphism_between)
- Línea donde se llama `graph.get_morphism(c1, c2)` → cambiar a `graph.get_morphism_between(c1, c2)`

### 0.2 Bug en co_regulators.py (is_connected hardcodeado)
- `is_connected = stats.get("num_skills", 0) > 0` → usar `graph.is_connected()` real

### 0.3 Bug en category.py (verify_axioms no verifica identidad)
- Implementar verificación real de `f ∘ id = f` y `id ∘ f = f`

### 0.4 Bug en category.py (compose pierde tipo de morfismo)
- Composición siempre produce DEPENDENCY → preservar tipo según reglas categóricas

**Tests**: Ejecutar `pytest tests/` para confirmar que nada se rompe.

---

## Fase 1: Propiedad Universal del Colímite (Gap #1)

**Archivos**: `nucleo/types.py`, `nucleo/mes/patterns.py`, `nucleo/graph/category.py`
**Test nuevo**: `tests/test_colimits.py`

### 1.1 Redefinir Pattern como Diagrama (types.py)

Añadir a Pattern los campos necesarios para ser un funtor P: I → K:

```python
@dataclass
class Pattern:
    id: str
    component_ids: list[str]          # Objetos P_i (imagen del funtor)
    distinguished_links: list[str]    # Morfismos en la imagen
    # --- NUEVOS CAMPOS ---
    index_objects: list[str]          # Ob(I) = nodos del diagrama de índices
    index_morphisms: dict[str, tuple[str, str]]  # Mor(I): nombre → (source_idx, target_idx)
    functor_map_objects: dict[str, str]   # F(i) = skill_id para cada i ∈ Ob(I)
    functor_map_morphisms: dict[str, str] # F(d) = morphism_id para cada d ∈ Mor(I)
    is_homologous_to: list[str]
    metadata: dict[str, Any]
```

### 1.2 Implementar verificación de co-cono (patterns.py)

Método nuevo en ColimitBuilder:

```python
def verify_cocone(self, pattern: Pattern, cocone_skill_id: str,
                  cocone_morphisms: dict[str, str], graph: SkillCategory) -> bool:
    """
    Verificar condición (a) de Def 2.2:
    Para todo morfismo d: i → j en I, se cumple c_j ∘ P(d) = c_i
    """
```

### 1.3 Implementar verificación de propiedad universal (patterns.py)

```python
def verify_universal_property(self, pattern: Pattern, cocone_skill_id: str,
                               cocone_morphisms: dict[str, str],
                               graph: SkillCategory) -> bool:
    """
    Verificar condición (b) de Def 2.2:
    Para todo B y familia compatible (g_i: P_i → B), existe único h: cP → B
    tal que h ∘ c_i = g_i para todo i.

    En la práctica: verificar para todos los B existentes en el grafo.
    """
```

### 1.4 Modificar build_colimit para que VERIFIQUE (patterns.py)

- Después de crear co-cono, llamar `verify_cocone()`
- Construir los morfismos universales h: cP → B para todo B alcanzable
- Si la verificación falla, lanzar excepción o retornar error

### 1.5 Tests (tests/test_colimits.py)

- Test: Patrón {s1 → s2} produce colímite con co-cono compatible
- Test: Propiedad universal: dado B con g1: s1→B, g2: s2→B compatible, existe único h: cP→B
- Test: Patrón sin colímite válido es detectado
- Test: Dos patrones homólogos producen el mismo colímite

---

## Fase 2: Sistema Evolutivo con Funtores de Transición (Gap #2)

**Archivos nuevos**: `nucleo/graph/evolution.py`
**Archivos modificados**: `nucleo/types.py`, `nucleo/graph/category.py`, `nucleo/core.py`
**Test nuevo**: `tests/test_evolution.py`

### 2.1 Crear EvolutionarySystem (nucleo/graph/evolution.py)

```python
class CategorySnapshot:
    """Snapshot inmutable de Skill_t en el tiempo t."""
    timestamp: int
    skills: dict[str, Skill]          # Copia frozen
    morphisms: dict[str, Morphism]    # Copia frozen

class TransitionFunctor:
    """Funtor de transición k_{t,t+1}: Skill_t → Skill_{t+1}"""
    source_time: int
    target_time: int
    object_map: dict[str, Optional[str]]    # skill_id_t → skill_id_{t+1} (None = eliminado)
    morphism_map: dict[str, Optional[str]]  # morph_id_t → morph_id_{t+1}

class EvolutionarySystem:
    """Sistema evolutivo de skills S sobre T = N (Def 3.2)."""

    def snapshot(self) -> CategorySnapshot
    def apply_option(self, option: Option) -> TransitionFunctor
    def get_functor(self, t1: int, t2: int) -> TransitionFunctor
    def verify_compatibility(self, t1, t2, t3) -> bool  # k_{t2,t3} ∘ k_{t1,t2} = k_{t1,t3}
```

### 2.2 Conectar Option → Complejificación (Def 6.1)

- `apply_option()` recibe una Option del co-regulador
- Ejecuta las operaciones (absorción, eliminación, ligadura)
- Retorna el TransitionFunctor que describe el cambio
- Almacena el snapshot anterior para historial

### 2.3 Integrar en core.py

- `Nucleo.initialize()` crea `EvolutionarySystem` envolviendo `SkillCategory`
- Cada transición pasa por `apply_option()` en vez de mutar directamente
- Se mantiene historial de snapshots (configurable, últimos N)

### 2.4 Tests

- Test: Snapshot → Option(absorción) → TransitionFunctor mapea correctamente
- Test: Snapshot → Option(eliminación) → objeto eliminado tiene None en el mapa
- Test: Snapshot → Option(ligadura) → nuevo colímite aparece en Skill_{t+1}
- Test: Compatibilidad k_{0,1} ; k_{1,2} = k_{0,2}

---

## Fase 3: Enlaces Simples vs Complejos + Emergencia (Gap #3)

**Archivos modificados**: `nucleo/types.py`, `nucleo/graph/category.py`, `nucleo/graph/evolution.py`
**Test nuevo**: `tests/test_emergence.py`

### 3.1 Clasificación de enlaces (category.py)

Añadir a Morphism:

```python
class LinkComplexity(Enum):
    IDENTITY = auto()
    SIMPLE = auto()      # Factoriza a través de un único cluster
    COMPLEX = auto()     # Composición de simples que NO factoriza por cluster adyacente
```

Nuevo método en SkillCategory:

```python
def classify_link(self, morphism_id: str) -> LinkComplexity:
    """
    Def 6.3: Enlace simple si factoriza por un cluster.
    Enlace complejo si es composición de simples que no factorizan.
    """
```

### 3.2 Detección de emergencia (evolution.py)

```python
def detect_complex_links(self, t: int) -> list[str]:
    """Encontrar enlaces complejos que emergieron en Skill_t."""

def measure_emergence(self, t: int) -> dict:
    """
    Thm 8.6: Medir emergencia.
    - num_complex_links: cantidad de enlaces complejos nuevos
    - max_complexity_order: máximo orden de complejidad alcanzado
    - complexity_growth: ¿creció respecto a t-1?
    """
```

### 3.3 Tests

- Test: Enlace directo s1→s2 es SIMPLE
- Test: Composición s1→s2→s3 donde s2 es cluster es SIMPLE
- Test: Composición s1→cP→s3 donde cP es colímite de patrón con s1 como componente es COMPLEX
- Test: Después de merge con enlace complejo, measure_emergence reporta crecimiento

---

## Fase 4: Verificación del Principio de Multiplicidad (Gap #4)

**Archivos modificados**: `nucleo/mes/patterns.py`, `nucleo/graph/category.py`
**Test nuevo**: `tests/test_multiplicity.py`

### 4.1 Verificación formal de homología (patterns.py)

Reescribir `_are_homologous()`:

```python
def are_homologous(self, p1: Pattern, p2: Pattern, graph: SkillCategory) -> bool:
    """
    Def 2.5: Dos patrones son homólogos si sus campos operativos son isomorfos.

    Campo operativo de P = conjunto de enlaces colectivos (morfismos desde
    el colímite de P hacia otros objetos del grafo).

    Isomorfismo = biyección que preserva composición.
    """
```

### 4.2 Verificación del principio (category.py)

```python
def verify_multiplicity_principle(self) -> dict:
    """
    Axioma 8.2: Existen patrones homólogos P, P' con colim P = colim P'
    que NO están conectados por un cluster.

    Returns:
        {
            "satisfies": bool,
            "homologous_pairs": list de pares,
            "shared_colimits": list de colímites con múltiples descomposiciones,
            "violations": list de problemas
        }
    """
```

### 4.3 Verificación de Prop 3.4 (los 4 pilares dan multiplicidad)

```python
def verify_pillar_multiplicity(self) -> bool:
    """
    Prop 3.4: Las traducciones τ1...τ6 entre los 4 pilares aseguran
    que existen patrones homólogos no conectados.

    Verificar que para al menos un concepto (ej: producto, inducción),
    existen descomposiciones en ≥2 pilares distintos.
    """
```

### 4.4 Tests

- Test: Dos patrones con mismo campo operativo son homólogos
- Test: Patrones en pilares distintos (SET vs CAT para "producto") son homólogos
- Test: Grafo con 4 pilares conectados satisface principio de multiplicidad
- Test: Grafo con un solo pilar NO satisface multiplicidad

---

## Fase 5: Co-reguladores Activos + Conexión con Memoria (Gap #5)

**Archivos modificados**: `nucleo/mes/co_regulators.py`, `nucleo/mes/memory.py`, `nucleo/mes/patterns.py`, `nucleo/core.py`
**Test nuevo**: `tests/test_coregulators.py`, `tests/test_memory.py`

### 5.1 CR_tac: Selección real de tácticas (co_regulators.py)

```python
def select_objectives(self, landscape: Landscape) -> Option:
    """
    CR_tac selecciona skills relevantes para la query actual.
    Consulta memoria procedural para procedimientos exitosos.
    """
    # Buscar en memoria procedural
    best_proc = self.memory.procedural.get_best_procedure(pattern_id)
    if best_proc:
        return Option(bindings=[], metadata={"procedure": best_proc})
    # Sin procedimiento → explorar
    return Option(absorptions=[query_skill_id])
```

### 5.2 CR_org: Reorganización real del grafo (co_regulators.py)

```python
def select_objectives(self, landscape: Landscape) -> Option:
    """
    CR_org detecta patrones sin colímite y propone ligaduras.
    Detecta skills poco usados y propone eliminación.
    """
    # Detectar patrones formables
    pm = PatternManager()
    unbound = pm.detect_patterns_without_colimit(graph)
    if unbound:
        return Option(bindings=[p.id for p in unbound[:3]])

    # Detectar skills con peso bajo → candidatos a eliminación
    weak = [s for s in graph.skills if max_weight(s) < threshold]
    if weak:
        return Option(eliminations=[s.id for s in weak[:2]])

    return Option()
```

### 5.3 CR_str: Complejificación real (co_regulators.py)

```python
def select_objectives(self, landscape: Landscape) -> Option:
    """
    CR_str busca oportunidades de crear niveles nuevos.
    Identifica patrones con enlaces complejos para complejificar.
    """
    complex_links = graph.find_complex_links()
    if complex_links:
        # Crear patrón a partir de skills conectados por enlaces complejos
        pattern = pm.create_pattern_from_links(complex_links)
        return Option(bindings=[pattern.id])
    return Option()
```

### 5.4 CR_int: Verificación real de axiomas (co_regulators.py)

```python
def build_landscape(self, graph: SkillCategory) -> Landscape:
    axiom_results = graph.verify_axioms()
    multiplicity = graph.verify_multiplicity_principle()
    return Landscape(
        metrics={
            "is_connected": float(graph.is_connected()),
            "has_all_pillars": float(self._check_all_pillars(graph)),
            "axioms_satisfied": float(all(axiom_results.values())),
            "multiplicity_holds": float(multiplicity["satisfies"]),
            "num_fractures": len(self._state.detected_fractures),
        }
    )

def detect_fracture(self, anticipated, actual) -> Optional[Fracture]:
    """Fractura = axioma que se cumplía y dejó de cumplirse."""
    for key in ["axioms_satisfied", "multiplicity_holds", "is_connected"]:
        if anticipated.metrics.get(key, 1.0) > 0 and actual.metrics.get(key, 1.0) == 0:
            return Fracture(
                fracture_type=FractureType.STRUCTURAL,
                anticipated_state=anticipated.metrics,
                actual_state=actual.metrics
            )
    return None
```

### 5.5 Memoria con E-equivalencia real (memory.py)

```python
def _is_e_equivalent(self, r1: ExperienceRecord, r2: ExperienceRecord,
                      cr_type: CoRegulatorType) -> bool:
    """
    Def 5.3: r1 y r2 son E-equivalentes respecto a CRk si CRk
    no los distingue (producen la misma respuesta funcional).

    Implementación: mismos pattern_ids activados Y mismo outcome type.
    """
    return (set(r1.pattern_ids) == set(r2.pattern_ids) and
            abs(r1.success_value - r2.success_value) < 0.1 and
            r1.outcome_type == r2.outcome_type)
```

### 5.6 Integrar todo en core.py

```python
class Nucleo:
    async def initialize(self):
        # ... existente ...

        # NUEVO: MES components
        self._evolution = EvolutionarySystem(self._graph)
        self._memory = MESMemory(config=self.config.mes)
        self._pattern_manager = PatternManager()
        self._colimit_builder = ColimitBuilder(self._pattern_manager)
        self._cr_network = CoRegulatorNetwork(
            memory=self._memory,
            cr_org_frequency=self.config.mes.cr_org_frequency,
            cr_str_frequency=self.config.mes.cr_str_frequency,
        )

    async def process(self, input_text: str) -> NucleoResponse:
        # ... paso 1-3 existentes ...

        # NUEVO: Ejecutar co-reguladores
        cr_results = self._cr_network.step(self._graph)

        # Construir opción agregada
        option = self._aggregate_options(cr_results)

        # Aplicar como complejificación
        if option.has_objectives():
            functor = self._evolution.apply_option(option)

        # ... paso 4-7 existentes ...

        # NUEVO: Registrar experiencia en memoria
        record = ExperienceRecord(
            pattern_id=active_pattern_id,
            success_value=reward,
            query=input_text,
            response=response.content,
        )
        self._memory.add_record(record)

        # Intentar formar E-concepto
        self._memory.try_form_concept(active_pattern_id, CoRegulatorType.TACTICAL)
```

### 5.7 Tests

- Test: CR_tac consulta memoria y retorna procedimiento conocido
- Test: CR_org detecta patrón sin colímite y propone ligadura
- Test: CR_str detecta enlace complejo y propone complejificación
- Test: CR_int detecta fractura cuando axioma deja de cumplirse
- Test: E-equivalencia agrupa registros con mismo patrón y resultado
- Test: Flujo completo: input → CR_tac → acción → reward → memoria → E-concepto

---

## Fase 6: Integración con lean4-skills + Verificación Formal

**Archivos modificados**: `nucleo/lean/client.py`, `nucleo/core.py`
**Referencia**: `external/lean4-skills/`

### 6.1 Integrar scripts de lean4-skills

- Usar `solverCascade.py` en `sorry_filler.py` para verificación automática de candidatos
- Usar `sorry_analyzer.py` para análisis de pruebas incompletas
- Usar `parseLeanErrors.py` para parsing estructurado de errores Lean

### 6.2 Conectar verificación Lean al ciclo MES

- Cuando CR_tac selecciona ASSIST → usar lean4-skills solver cascade
- Resultado de Lean alimenta la recompensa r_task directamente
- Éxitos/fallos se registran como ExperienceRecords en memoria

### 6.3 Tests

- Test: Solver cascade resuelve `sorry` triviales (rfl, simp, ring)
- Test: Resultado Lean se registra correctamente en memoria MES

---

## Fase 7: Propiedades Formales (Axiomas 8.1-8.4, Teoremas 8.5-8.7)

**Archivos modificados**: `nucleo/graph/category.py`, `nucleo/graph/evolution.py`
**Test nuevo**: `tests/test_formal_properties.py`

### 7.1 Verificar Axiomas 8.1-8.4

```python
def verify_all_axioms(self) -> dict:
    return {
        "8.1_hierarchy": self._verify_hierarchy(),        # ≥2 niveles
        "8.2_multiplicity": self.verify_multiplicity_principle(),
        "8.3_connectivity": self._verify_connectivity(),  # débilmente conexa + inter-pilar
        "8.4_coverage": self._verify_coverage(),           # todo skill cubierto por pilar
    }
```

### 7.2 Verificar Teoremas

- **Thm 8.5 (Consistencia)**: Después de cada `apply_option()`, verificar que Skill_{t+1} sigue siendo categoría jerárquica válida con multiplicidad.
- **Thm 8.6 (Emergencia)**: Después de merge con enlace complejo, verificar que max_complexity_order creció.
- **Thm 8.7 (Preservación de cobertura)**: Después de cada transición, verificar que cobertura fundacional se mantiene.

### 7.3 Tests

- Test: Grafo inicial satisface 4 axiomas
- Test: Complejificación preserva axiomas (Thm 8.5)
- Test: Merge con enlace complejo produce emergencia (Thm 8.6)
- Test: Cobertura se preserva bajo complejificación (Thm 8.7)

---

## Orden de Implementación

```
Fase 0  ─── Bugfixes                              ─── ~30 min
Fase 1  ─── Propiedad Universal del Colímite       ─── Sesión 1
Fase 2  ─── Sistema Evolutivo + Funtores           ─── Sesión 2
Fase 3  ─── Enlaces Simples/Complejos              ─── Sesión 3
Fase 4  ─── Principio de Multiplicidad             ─── Sesión 3
Fase 5  ─── Co-reguladores + Memoria               ─── Sesión 4-5
Fase 6  ─── Lean4-skills Integration               ─── Sesión 5
Fase 7  ─── Propiedades Formales                   ─── Sesión 6
```

Cada fase termina con:
1. Tests nuevos pasan
2. Tests viejos siguen pasando
3. Commit con mensaje descriptivo

---

## Archivos Nuevos

| Archivo | Propósito |
|---------|-----------|
| `nucleo/graph/evolution.py` | EvolutionarySystem, TransitionFunctor, CategorySnapshot |
| `tests/test_colimits.py` | Tests de propiedad universal |
| `tests/test_evolution.py` | Tests de funtores de transición |
| `tests/test_emergence.py` | Tests de enlaces simples/complejos |
| `tests/test_multiplicity.py` | Tests del principio de multiplicidad |
| `tests/test_coregulators.py` | Tests de co-reguladores activos |
| `tests/test_memory.py` | Tests de memoria MES |
| `tests/test_formal_properties.py` | Tests de Axiomas 8.1-8.4 y Teoremas 8.5-8.7 |

## Archivos Modificados

| Archivo | Cambios |
|---------|---------|
| `nucleo/types.py` | Pattern con funtor, LinkComplexity enum, ExperienceRecord con outcome_type |
| `nucleo/graph/category.py` | verify_axioms real, compose preserva tipo, classify_link, verify_multiplicity |
| `nucleo/mes/patterns.py` | Fix bug, verify_cocone, verify_universal_property, are_homologous real |
| `nucleo/mes/co_regulators.py` | Fix bug, select_objectives real para los 4 CRs, fracture detection real |
| `nucleo/mes/memory.py` | E-equivalencia real, conexión con co-reguladores |
| `nucleo/graph/operations.py` | merge/split preservan propiedades categóricas |
| `nucleo/core.py` | Integrar EvolutionarySystem, CoRegulatorNetwork, MESMemory, PatternManager |
| `nucleo/lean/sorry_filler.py` | Integrar solverCascade de lean4-skills |
