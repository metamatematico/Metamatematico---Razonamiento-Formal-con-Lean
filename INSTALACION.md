# Guía de Instalación Paso a Paso

Esta guía te llevará desde cero hasta tener el sistema funcionando, incluso si nunca has usado Python.

---

## Prerrequisitos

### 1. Instalar Python 3.10 o superior

#### Windows

1. Ve a https://www.python.org/downloads/
2. Descarga Python 3.10+ (o 3.11, 3.12)
3. **IMPORTANTE**: Durante instalación, marca "Add Python to PATH"
4. Completa la instalación
5. Verifica abriendo CMD y escribiendo:
   ```cmd
   python --version
   ```
   Deberías ver algo como: `Python 3.10.x` o superior

#### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install python3.10 python3-pip git
python3 --version  # Verificar
```

#### macOS

```bash
# Con Homebrew
brew install python@3.10
python3 --version  # Verificar
```

### 2. Obtener API Key de Anthropic

1. Ve a https://console.anthropic.com
2. Crea una cuenta (gratis)
3. Ve a "API Keys"
4. Crea una nueva key → copia el texto que empieza con `sk-ant-...`
5. **GUÁRDALA** en un lugar seguro

### 3. Agregar Créditos (necesario para usar Claude)

1. En https://console.anthropic.com
2. Ve a "Plans & Billing"
3. Agrega al menos $5 USD
4. Espera ~1 minuto a que se procese

---

## Instalación del Sistema

### Paso 1: Descargar el código

#### Opción A: Con Git (recomendado)

```bash
git clone https://github.com/metamatematico/Demostrador-de-enunciados-matem-ticos.git
cd Demostrador-de-enunciados-matem-ticos
```

#### Opción B: Descarga directa (sin Git)

1. Ve a https://github.com/metamatematico/Demostrador-de-enunciados-matem-ticos
2. Click en botón verde "Code"
3. Click en "Download ZIP"
4. Extrae el ZIP en una carpeta
5. Abre terminal en esa carpeta

### Paso 2: Instalar dependencias

```bash
pip install pyyaml rich anthropic
```

**¿Qué se está instalando?**
- `pyyaml`: Lee archivos de configuración
- `rich`: Interfaz bonita en terminal
- `anthropic`: Cliente oficial de Claude AI

Si ves errores, intenta:
```bash
python -m pip install --upgrade pip
pip install pyyaml rich anthropic
```

### Paso 3: Configurar API Key

**Windows CMD:**
```cmd
set ANTHROPIC_API_KEY=sk-ant-tu-clave-aqui
```

**Windows PowerShell:**
```powershell
$env:ANTHROPIC_API_KEY="sk-ant-tu-clave-aqui"
```

**Linux/Mac:**
```bash
export ANTHROPIC_API_KEY=sk-ant-tu-clave-aqui
```

**Nota:** Esta configuración es temporal (solo para esta sesión de terminal). Para hacerla permanente:

#### Windows (permanente)
1. Busca "Variables de entorno" en el menú inicio
2. "Editar las variables de entorno del sistema"
3. Click en "Variables de entorno..."
4. En "Variables de usuario" → "Nueva..."
5. Nombre: `ANTHROPIC_API_KEY`
6. Valor: tu clave `sk-ant-...`
7. Aceptar todo

#### Linux/Mac (permanente)
Agrega al final de `~/.bashrc` (o `~/.zshrc` en Mac):
```bash
export ANTHROPIC_API_KEY=sk-ant-tu-clave-aqui
```
Luego:
```bash
source ~/.bashrc  # o source ~/.zshrc en Mac
```

### Paso 4: Verificar instalación

```bash
python -c "from nucleo.core import Nucleo; print('Instalación correcta ✓')"
```

Si ves `Instalación correcta ✓`, todo está bien.

---

## Primer Uso: Chat Interactivo

### Iniciar el chat

```bash
python -m nucleo chat
```

Verás:
```
┌─────────────────────────────────┐
│ NLE v7.0 — Núcleo Lógico Evolutivo │
│ Modelo: claude-sonnet-4-20250514   │
└─────────────────────────────────┘
Inicializando sistema...
Listo. 61 skills cargados.

Tu >
```

### Tus primeras consultas

Escribe esto (presiona Enter después de cada línea):

```
¿Qué es un grupo en álgebra?
```

El sistema responderá con la definición formal de grupo.

Luego prueba:
```
Formaliza eso en Lean 4
```

Verás código Lean 4 generado automáticamente.

### Comandos especiales

Prueba estos comandos (todos empiezan con `/`):

```
/help       - Ver ayuda
/stats      - Ver estadísticas del sistema
/skills     - Ver los 61 skills matemáticos
/axioms     - Verificar axiomas formales
/clear      - Limpiar historial
/quit       - Salir
```

### Consultas de ejemplo

```
Tu > ¿Qué es un espacio vectorial?
Tu > Demuestra que la raíz de 2 es irracional
Tu > ¿Qué es el teorema de Lagrange para grupos?
Tu > Formaliza la definición de anillo en Lean 4
Tu > Explica el teorema fundamental del álgebra
```

---

## Uso Avanzado

### Cambiar modelo de Claude

Por defecto usa `claude-sonnet-4` (el más inteligente). Para usar el modelo rápido/barato:

```bash
python -m nucleo chat --model claude-haiku-4-5-20251001
```

**Comparación de modelos:**
| Modelo | Velocidad | Costo | Calidad |
|--------|-----------|-------|---------|
| haiku | ⚡⚡⚡ Muy rápido | 💰 $0.25/M tokens | ⭐⭐⭐ Buena |
| sonnet | ⚡⚡ Rápido | 💰💰 $3/M tokens | ⭐⭐⭐⭐⭐ Excelente |

### Modo verbose (ver decisiones del agente)

```bash
python -m nucleo chat --verbose
```

Esto muestra las decisiones internas del agente RL:
```
Tu > ¿Qué es un grupo?
  [RL: RESPONSE]  ← El agente decidió responder con Claude
[RESPONSE | confianza: 0.80]
Un grupo es...
```

### Uso desde código Python

Crea un archivo `mi_script.py`:

```python
import asyncio
from nucleo.core import Nucleo
from nucleo.config import NucleoConfig

async def main():
    # Configurar
    config = NucleoConfig()
    config.llm.model = "claude-haiku-4-5-20251001"

    # Inicializar
    nucleo = Nucleo(config=config)
    await nucleo.initialize()
    nucleo.agent.eval_mode()

    # Consulta
    response = await nucleo.process("¿Qué es un anillo conmutativo?")

    print(f"Acción: {response.action_type.name}")
    print(f"Confianza: {response.confidence}")
    print(f"\n{response.content}")

    # Estadísticas
    stats = nucleo.stats
    print(f"\nSkills: {stats['num_skills']}")
    print(f"Niveles: {stats['num_levels']}")

asyncio.run(main())
```

Ejecuta:
```bash
python mi_script.py
```

---

## Verificar Tests

El sistema incluye 284 tests. Para correrlos:

### Instalar pytest (si no lo tienes)

```bash
pip install pytest
```

### Correr todos los tests

```bash
python -m pytest tests/ -v
```

Deberías ver:
```
====== 284 passed in 1.37s ======
```

### Correr tests específicos

```bash
# Solo tests del grafo
python -m pytest tests/test_graph.py -v

# Solo tests de memoria
python -m pytest tests/test_memory.py -v

# Solo tests de Lean
python -m pytest tests/test_lean_integration.py -v
```

---

## Solución de Problemas Comunes

### Problema 1: "python: command not found"

**En Windows:**
- Python no está en PATH. Reinstala Python marcando "Add Python to PATH"

**En Linux/Mac:**
- Usa `python3` en lugar de `python`:
  ```bash
  python3 -m nucleo chat
  ```

### Problema 2: "No module named 'nucleo'"

Asegúrate de estar en la carpeta correcta:
```bash
cd Demostrador-de-enunciados-matematicos
python -m nucleo chat
```

### Problema 3: "ANTHROPIC_API_KEY not found"

La variable de entorno no está configurada. Repite el Paso 3 de instalación.

### Problema 4: "Your credit balance is too low"

Tu cuenta de Anthropic no tiene créditos. Ve a https://console.anthropic.com → Plans & Billing → agrega $5 USD.

### Problema 5: El chat muestra caracteres raros (�)

**Windows:** Problema de encoding. Antes de iniciar el chat:
```cmd
chcp 65001
python -m nucleo chat
```

**Linux/Mac:** Agrega a tu `~/.bashrc`:
```bash
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
```

### Problema 6: "ModuleNotFoundError: No module named 'yaml'"

Falta instalar dependencias:
```bash
pip install pyyaml rich anthropic
```

### Problema 7: Tests fallan con "coverage" error

```bash
python -m pytest tests/ -o "addopts=" -v
```

El flag `-o "addopts="` desactiva coverage que puede causar problemas.

---

## Configuración Avanzada

### Archivo de configuración

El sistema lee configuración de `nucleo_config.yaml`:

```yaml
llm:
  model: "claude-sonnet-4-20250514"
  temperature: 0.7
  max_tokens: 2000

rl:
  epsilon_start: 1.0
  epsilon_end: 0.1
  epsilon_decay: 0.995
  learning_rate: 0.001

graph:
  max_level: 5
  embedding_dim: 128

lean:
  enabled: false
  executable_path: null
```

Puedes editar estos valores para cambiar el comportamiento del sistema.

### Habilitar integración con Lean 4 (opcional)

Si quieres verificar demostraciones formalmente:

1. Instalar Lean 4:
   ```bash
   curl https://raw.githubusercontent.com/leanprover/elan/master/elan-init.sh -sSf | sh
   ```

2. En `nucleo_config.yaml`, cambiar:
   ```yaml
   lean:
     enabled: true
     executable_path: "/ruta/a/lean"  # o null para auto-detectar
   ```

---

## Próximos Pasos

Una vez que todo funciona, puedes:

1. **Explorar los 61 skills:** Usa `/skills` en el chat para ver todos los dominios matemáticos

2. **Leer la documentación técnica:** Ve `README.md` para detalles sobre la arquitectura

3. **Ver ejemplos:** Revisa la carpeta `examples/` para código de ejemplo

4. **Contribuir:** Si encuentras bugs o quieres agregar funcionalidades, abre un issue en GitHub

---

## Soporte

Si tienes problemas:

1. Revisa esta guía completa
2. Revisa la sección "Solución de Problemas" en `README.md`
3. Abre un issue en: https://github.com/metamatematico/Demostrador-de-enunciados-matem-ticos/issues

---

**¡Listo! Ahora tienes un asistente matemático con IA funcionando en tu computadora.**
