# Ejemplos de Uso del Sistema

Esta guía muestra ejemplos concretos de cómo usar el sistema para diferentes tareas matemáticas.

---

## Ejemplo 1: Consultas Básicas

### Definiciones matemáticas

```
Tu > ¿Qué es un grupo abeliano?

[RESPONSE | confianza: 0.85]
Un grupo abeliano (o conmutativo) es un grupo (G, ·) donde la operación
es conmutativa: ∀a,b ∈ G: a·b = b·a

Formalmente, (G, ·) es un grupo abeliano si:
1. (G, ·) es un grupo (asociativa, neutro, inversos)
2. ∀a,b ∈ G: a·b = b·a (conmutatividad)

Ejemplos:
- (ℤ, +): los enteros con suma
- (ℚ\{0}, ×): racionales no-cero con multiplicación
- (ℝⁿ, +): vectores en ℝⁿ con suma componente a componente
```

### Teoremas

```
Tu > Explica el teorema de Lagrange para grupos

[RESPONSE | confianza: 0.82]
El teorema de Lagrange establece que:

**Enunciado:** Si G es un grupo finito y H es un subgrupo de G,
entonces |H| divide a |G|.

Formalmente: |G| = |H| × [G : H]

donde [G : H] es el índice de H en G (número de coclases).

**Corolario importante:** El orden de cualquier elemento divide
al orden del grupo.

**Demostración (idea):**
1. Las coclases de H particionan G
2. Todas las coclases tienen el mismo tamaño |H|
3. Por tanto |G| = (número de coclases) × |H|
```

---

## Ejemplo 2: Formalización en Lean 4

### Definición de estructura algebraica

```
Tu > Formaliza la definición de grupo en Lean 4

[RESPONSE | confianza: 0.88]
```lean
-- Definición de grupo
class Group (G : Type u) where
  mul : G → G → G
  one : G
  inv : G → G
  mul_assoc : ∀ a b c : G, mul (mul a b) c = mul a (mul b c)
  mul_one : ∀ a : G, mul a one = a
  one_mul : ∀ a : G, mul one a = a
  mul_inv_self : ∀ a : G, mul a (inv a) = one
  inv_mul_self : ∀ a : G, mul (inv a) a = one

-- Notación
infixl:70 " * " => Group.mul
notation "1" => Group.one
postfix:max "⁻¹" => Group.inv

-- Ejemplo de uso
variable {G : Type u} [Group G]

theorem mul_left_cancel {a b c : G} (h : a * b = a * c) : b = c := by
  have : a⁻¹ * (a * b) = a⁻¹ * (a * c) := by rw [h]
  simp [mul_assoc, inv_mul_self, one_mul] at this
  exact this
```
```

### Teorema con demostración

```
Tu > Formaliza en Lean 4: "Todo grupo de orden primo es cíclico"

[RESPONSE | confianza: 0.75]
```lean
import Mathlib.GroupTheory.OrderOfElement
import Mathlib.Data.Nat.Prime

-- Teorema: Un grupo de orden primo es cíclico
theorem group_prime_order_is_cyclic
    {G : Type*} [Group G] [Fintype G]
    (hp : (Fintype.card G).Prime) :
    IsCyclic G := by
  -- Tomar cualquier elemento no-neutro
  obtain ⟨g, hg⟩ : ∃ g : G, g ≠ 1 := by
    by_contra h
    push_neg at h
    -- Si todos son neutro, |G| = 1, contradicción con primo
    have : Fintype.card G = 1 := by
      apply Fintype.card_eq_one_iff.mpr
      exact ⟨1, h⟩
    linarith [hp.one_lt]

  -- El orden de g divide |G| por Lagrange
  have hdiv : orderOf g ∣ Fintype.card G := orderOf_dvd_card

  -- Como |G| es primo y g ≠ 1, orderOf g = |G|
  have : orderOf g = Fintype.card G := by
    apply hp.eq_one_or_self_of_dvd _ hdiv
    exact orderOf_pos g |>.ne'
    intro h_ord
    have : g = 1 := orderOf_eq_one_iff.mp h_ord
    contradiction

  -- Entonces g genera G
  exact ⟨⟨g, by rwa [orderOf_eq_card_of_forall_mem_zpowers]⟩⟩
```
```

---

## Ejemplo 3: Demostraciones Paso a Paso

### Demostración clásica

```
Tu > Demuestra que la raíz de 2 es irracional

[RESPONSE | confianza: 0.90]
**Teorema:** √2 es irracional.

**Demostración (por contradicción):**

1. **Suponer lo contrario:** Supongamos que √2 es racional.

2. **Expresar como fracción:** Entonces √2 = p/q donde p, q ∈ ℤ,
   q ≠ 0, y la fracción está en términos mínimos (mcd(p,q) = 1).

3. **Elevar al cuadrado:** 2 = p²/q²

4. **Despejar:** 2q² = p²

5. **Conclusión 1:** p² es par → p es par (porque el cuadrado de
   un impar es impar).

6. **Escribir p como par:** p = 2k para algún k ∈ ℤ.

7. **Sustituir:** 2q² = (2k)² = 4k²

8. **Simplificar:** q² = 2k²

9. **Conclusión 2:** q² es par → q es par.

10. **Contradicción:** Tanto p como q son pares, pero supusimos
    que mcd(p,q) = 1. ⚡

11. **Conclusión final:** La suposición inicial es falsa.
    Por tanto, √2 es irracional. ∎
```

### Demostración algebraica

```
Tu > Demuestra que en todo grupo, (ab)⁻¹ = b⁻¹a⁻¹

[RESPONSE | confianza: 0.92]
**Teorema:** En un grupo (G, ·), para todo a, b ∈ G:
(a·b)⁻¹ = b⁻¹·a⁻¹

**Demostración:**

Necesitamos mostrar que b⁻¹·a⁻¹ es el inverso de a·b.

Por definición de inverso, debemos probar:
(a·b)·(b⁻¹·a⁻¹) = e  y  (b⁻¹·a⁻¹)·(a·b) = e

**Verificación 1:**
(a·b)·(b⁻¹·a⁻¹)
= a·(b·b⁻¹)·a⁻¹        [asociatividad]
= a·e·a⁻¹              [definición de inverso]
= a·a⁻¹                [neutro]
= e                    [definición de inverso] ✓

**Verificación 2:**
(b⁻¹·a⁻¹)·(a·b)
= b⁻¹·(a⁻¹·a)·b        [asociatividad]
= b⁻¹·e·b              [definición de inverso]
= b⁻¹·b                [neutro]
= e                    [definición de inverso] ✓

Por tanto, (a·b)⁻¹ = b⁻¹·a⁻¹. ∎
```

---

## Ejemplo 4: Consultas sobre Dominios Específicos

### Topología

```
Tu > ¿Qué es un espacio topológico de Hausdorff?

[RESPONSE | confianza: 0.83]
Un espacio topológico (X, τ) es de **Hausdorff** (o T₂) si:

**Definición:** Para cualesquiera dos puntos distintos x, y ∈ X,
existen entornos abiertos U de x y V de y tales que U ∩ V = ∅.

Formalmente: ∀x,y ∈ X, x ≠ y → ∃U,V ∈ τ: x ∈ U ∧ y ∈ V ∧ U ∩ V = ∅

**Intuición:** Los puntos se pueden "separar" con abiertos disjuntos.

**Ejemplos:**
- ℝⁿ con la topología usual es Hausdorff
- Todo espacio métrico es Hausdorff
- Espacios discretos son Hausdorff

**Contraejemplo:**
- ℝ con topología trivial {∅, ℝ} NO es Hausdorff
- Espacios con topología cofinita (si infinitos) NO son Hausdorff

**Propiedad importante:** En espacios de Hausdorff, los límites
de sucesiones son únicos.
```

### Análisis

```
Tu > Explica el teorema de la función inversa

[RESPONSE | confianza: 0.80]
**Teorema de la Función Inversa**

**Enunciado:** Sea f: ℝⁿ → ℝⁿ una función C¹ (continuamente diferenciable)
y sea a ∈ ℝⁿ tal que det(Df(a)) ≠ 0 (Jacobiano no-singular en a).

Entonces:
1. Existe un entorno U de a donde f es inyectiva
2. f(U) es abierto
3. f⁻¹: f(U) → U existe y es C¹
4. D(f⁻¹)(f(a)) = [Df(a)]⁻¹

**Intuición:** Si la derivada es invertible en un punto, la función
misma es localmente invertible cerca de ese punto.

**Versión informal:** "Derivada invertible ⟹ función localmente invertible"

**Aplicaciones:**
- Teorema de la función implícita
- Coordenadas curvilíneas
- Variedades diferenciables
- Sistemas de ecuaciones no-lineales

**Ejemplo (n=1):**
f(x) = x³ en x = 1:
- f'(1) = 3 ≠ 0 ✓
- Localmente cerca de 1, f es invertible
- f⁻¹(y) = ∛y
- (f⁻¹)'(1) = 1/f'(1) = 1/3
```

---

## Ejemplo 5: Uso Programático

### Script básico

```python
# ejemplo_basico.py
import asyncio
from nucleo.core import Nucleo
from nucleo.config import NucleoConfig

async def main():
    # Configurar sistema
    config = NucleoConfig()
    nucleo = Nucleo(config=config)
    await nucleo.initialize()
    nucleo.agent.eval_mode()

    # Hacer consulta
    response = await nucleo.process(
        "¿Cuáles son los axiomas de grupo?"
    )

    print(f"Respuesta:\n{response.content}")
    print(f"\nConfianza: {response.confidence:.0%}")

asyncio.run(main())
```

### Script con múltiples consultas

```python
# ejemplo_multiple.py
import asyncio
from nucleo.core import Nucleo
from nucleo.config import NucleoConfig

async def main():
    config = NucleoConfig()
    config.llm.model = "claude-haiku-4-5-20251001"  # Modelo rápido

    nucleo = Nucleo(config=config)
    await nucleo.initialize()
    nucleo.agent.eval_mode()

    consultas = [
        "¿Qué es un homomorfismo de grupos?",
        "¿Qué es un ideal en un anillo?",
        "Define espacio vectorial"
    ]

    for i, consulta in enumerate(consultas, 1):
        print(f"\n{'='*60}")
        print(f"Consulta {i}: {consulta}")
        print('='*60)

        response = await nucleo.process(consulta)
        print(response.content)

asyncio.run(main())
```

### Script con estadísticas

```python
# ejemplo_stats.py
import asyncio
from nucleo.core import Nucleo
from nucleo.config import NucleoConfig

async def main():
    nucleo = Nucleo(config=NucleoConfig())
    await nucleo.initialize()
    nucleo.agent.eval_mode()

    # Estadísticas del sistema
    stats = nucleo.stats

    print("ESTADÍSTICAS DEL SISTEMA")
    print("=" * 50)
    print(f"Skills cargados: {stats['num_skills']}")
    print(f"Niveles jerárquicos: {stats['num_levels']}")
    print(f"Pilares activos: {stats['num_pillars']}")
    print(f"Morfismos: {stats['num_morphisms']}")

    # Verificar axiomas
    from nucleo.graph.category import SkillCategory
    cat: SkillCategory = nucleo._graph
    axioms = cat.verify_all_axioms()

    print("\nAXIOMAS VERIFICADOS:")
    print(f"  8.1 Jerarquía: {'✓' if axioms['8.1_hierarchy']['satisfies'] else '✗'}")
    print(f"  8.2 Multiplicidad: {'✓' if axioms['8.2_multiplicity']['satisfies'] else '✗'}")
    print(f"  8.3 Conectividad: {'✓' if axioms['8.3_connectivity']['satisfies'] else '✗'}")
    print(f"  8.4 Cobertura: {'✓' if axioms['8.4_coverage']['satisfies'] else '✗'}")
    print(f"\nTodos: {'✓ PASAN' if axioms['all_satisfied'] else '✗ FALLAN'}")

asyncio.run(main())
```

---

## Ejemplo 6: Comandos del Chat

### Ver skills disponibles

```
Tu > /skills

┌─────────────────────────────────────────────────┐
│ 61 Skills Matemáticos por Pilar                │
├─────────────────────────────────────────────────┤
│                                                 │
│ SET (Teoría de Conjuntos):                      │
│   - zfc-axioms (L0)                             │
│   - ordinals (L0)                               │
│   - group-theory (L1)                           │
│   - ring-theory (L1)                            │
│   - field-theory (L1)                           │
│   - ...                                         │
│                                                 │
│ CAT (Teoría de Categorías):                     │
│   - cat-basics (L0)                             │
│   - functors (L0)                               │
│   - nat-trans (L0)                              │
│   - limits (L0)                                 │
│   - topos-theory (L1)                           │
│   - ...                                         │
│                                                 │
│ LOG (Lógica):                                   │
│   - fol-deduction (L0)                          │
│   - fol-metatheory (L0)                         │
│   - model-theory (L1)                           │
│   - proof-theory (L2)                           │
│   - ...                                         │
│                                                 │
│ TYPE (Teoría de Tipos):                         │
│   - cic (L0)                                    │
│   - lean-kernel (L0)                            │
│   - type-theory-advanced (L2)                   │
│   - ...                                         │
│                                                 │
│ Total: 61 skills                                │
└─────────────────────────────────────────────────┘
```

### Ver estadísticas

```
Tu > /stats

┌─────────────────────────────────────────────────┐
│ Estadísticas del Sistema NLE v7.0               │
├─────────────────────────────────────────────────┤
│                                                 │
│ Grafo Categórico:                               │
│   Skills: 61                                    │
│   Niveles: 3                                    │
│   Pilares: 4 (SET, CAT, LOG, TYPE)              │
│   Morfismos: 127                                │
│                                                 │
│ Agente RL:                                      │
│   Modo: evaluación                              │
│   Epsilon: 1.0                                  │
│   Pasos: 5                                      │
│                                                 │
│ Memoria MES:                                    │
│   Empírica: 12 registros                        │
│   Procedural: 3 procedimientos                  │
│   Semántica: 1 E-concepto                       │
│                                                 │
│ Co-Reguladores:                                 │
│   CR_tac: activo (paso 5)                       │
│   CR_org: siguiente en paso 10                  │
│   CR_str: siguiente en paso 100                 │
│   CR_int: verificado recientemente              │
└─────────────────────────────────────────────────┘
```

### Verificar axiomas

```
Tu > /axioms

┌─────────────────────────────────────────────────┐
│ Verificación de Axiomas Formales                │
├─────────────────────────────────────────────────┤
│                                                 │
│ Axioma 8.1 - Jerarquía:           ✓ SATISFECHO  │
│   Niveles jerárquicos: 3                        │
│   Mínimo requerido: 2                           │
│                                                 │
│ Axioma 8.2 - Multiplicidad:       ✓ SATISFECHO  │
│   Pilares: 4 (SET, CAT, LOG, TYPE)              │
│   Traducciones inter-pilar: 8                   │
│                                                 │
│ Axioma 8.3 - Conectividad:        ✓ SATISFECHO  │
│   Grafo débilmente conexo: Sí                   │
│   Conexiones inter-pilar: 8                     │
│                                                 │
│ Axioma 8.4 - Cobertura:           ✓ SATISFECHO  │
│   Skills alcanzables: 61/61 (100%)              │
│                                                 │
│ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━  │
│ TODOS LOS AXIOMAS SATISFECHOS ✓                 │
└─────────────────────────────────────────────────┘
```

---

## Ejemplo 7: Temas Avanzados

### Teoría de Categorías

```
Tu > Explica qué es un funtor en teoría de categorías

[RESPONSE]
Un **funtor** F: C → D entre categorías C y D es un mapeo que:

1. **Preserva objetos:** Para cada objeto X en C, F(X) es un objeto en D

2. **Preserva morfismos:** Para cada morfismo f: X → Y en C,
   F(f): F(X) → F(Y) es un morfismo en D

3. **Preserva composición:** F(g ∘ f) = F(g) ∘ F(f)

4. **Preserva identidades:** F(id_X) = id_{F(X)}

**Tipos de funtores:**
- **Covariante:** Preserva dirección de flechas
- **Contravariante:** Invierte dirección (f: X→Y ⟹ F(f): F(Y)→F(X))

**Ejemplos:**
- Funtor olvido: Grp → Set (olvida estructura, solo conjunto)
- Funtor potencia: Set → Set, X ↦ P(X)
- Hom-funtor: Hom(A, -): C → Set
```

### Topología Algebraica

```
Tu > ¿Qué es el grupo fundamental de un espacio topológico?

[RESPONSE]
El **grupo fundamental** π₁(X, x₀) de un espacio topológico X
con punto base x₀ es:

**Definición:** El conjunto de clases de homotopía de lazos
basados en x₀, con la operación de concatenación.

**Construcción:**
1. **Lazo:** Camino continuo γ: [0,1] → X con γ(0) = γ(1) = x₀

2. **Homotopía:** Dos lazos γ₀, γ₁ son homotópicos si existe
   H: [0,1]×[0,1] → X continua con:
   - H(t, 0) = γ₀(t)
   - H(t, 1) = γ₁(t)
   - H(0, s) = H(1, s) = x₀

3. **Clases:** [γ] = {lazos homotópicos a γ}

4. **Operación:** [γ] * [δ] = [γ · δ] (concatenación)

**Propiedades:**
- Identidad: Lazo constante en x₀
- Inversos: Recorrer lazo al revés
- Es un invariante topológico

**Ejemplos:**
- π₁(ℝⁿ) = {e} (contráctil)
- π₁(S¹) = ℤ (círculo)
- π₁(Torus) = ℤ × ℤ
```

---

**Para más ejemplos, consulta la carpeta `examples/` del repositorio.**
