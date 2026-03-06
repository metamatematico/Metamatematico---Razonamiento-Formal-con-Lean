# 🚀 Inicio Rápido - 5 minutos

Si nunca has programado o solo quieres probar el sistema rápidamente, sigue estos pasos.

---

## ¿Qué hace este sistema?

Es un **asistente matemático con IA** al que le puedes hacer preguntas en español y te responde:

- Definiciones matemáticas
- Demostraciones de teoremas
- Código formal en Lean 4
- Explicaciones paso a paso

---

## Instalación Express (Windows)

### 1. Instalar Python

1. Descarga: https://www.python.org/downloads/
2. Al instalar, **marca "Add Python to PATH"** ✅
3. Siguiente, siguiente, instalar

### 2. Descargar el sistema

1. Descarga este ZIP: https://github.com/metamatematico/Demostrador-de-enunciados-matem-ticos/archive/refs/heads/main.zip
2. Extrae el ZIP en tu escritorio
3. Renombra la carpeta a `demostrador`

### 3. Instalar dependencias

Abre **CMD** (tecla Windows + R → escribe `cmd` → Enter):

```cmd
cd Desktop\demostrador
pip install pyyaml rich anthropic
```

Espera 30 segundos a que instale.

### 4. Conseguir API key de Claude

1. Ve a: https://console.anthropic.com
2. Crea cuenta (gratis)
3. Click en "API Keys" → "Create Key"
4. Copia la clave (empieza con `sk-ant-...`)
5. Ve a "Plans & Billing" → Agrega $5 USD

### 5. Configurar la clave

En el mismo CMD:

```cmd
set ANTHROPIC_API_KEY=sk-ant-pega-tu-clave-aqui
```

### 6. ¡Usar el sistema!

```cmd
python -m nucleo chat
```

Verás:

```
┌─────────────────────────────────┐
│ NLE v7.0 — Núcleo Lógico Evolutivo │
└─────────────────────────────────┘
Listo. 61 skills cargados.

Tu >
```

**Escribe tu primera pregunta:**

```
Tu > ¿Qué es un grupo en álgebra?
```

El sistema responderá con la definición formal.

**Prueba otra:**

```
Tu > Demuestra que la raíz de 2 es irracional
```

Verás la demostración paso a paso.

**Salir:**

```
Tu > /quit
```

---

## Instalación Express (Mac/Linux)

### 1. Abrir Terminal

Mac: `Cmd + Espacio` → escribe "Terminal"
Linux: `Ctrl + Alt + T`

### 2. Instalar

```bash
# Clonar repositorio
git clone https://github.com/metamatematico/Demostrador-de-enunciados-matem-ticos.git
cd Demostrador-de-enunciados-matem-ticos

# Instalar dependencias
pip3 install pyyaml rich anthropic

# Configurar API key (reemplaza con tu clave)
export ANTHROPIC_API_KEY=sk-ant-tu-clave-aqui

# Iniciar
python3 -m nucleo chat
```

---

## Ejemplos de Preguntas

### Definiciones
```
¿Qué es un espacio vectorial?
Define un anillo conmutativo
¿Qué es un homomorfismo?
```

### Teoremas
```
Enuncia el teorema de Lagrange para grupos
Explica el teorema fundamental del álgebra
¿Qué dice el teorema de Pitágoras?
```

### Demostraciones
```
Demuestra que la raíz de 2 es irracional
Prueba que todo grupo de orden primo es cíclico
Demuestra el teorema de los números primos gemelos
```

### Lean 4
```
Formaliza la definición de grupo en Lean 4
Escribe en Lean el teorema de isomorfismo
Cómo defino un espacio métrico en Lean?
```

---

## Comandos Útiles

Dentro del chat:

| Escribe | Qué hace |
|---------|----------|
| `/help` | Ver ayuda |
| `/skills` | Ver los 61 dominios matemáticos |
| `/stats` | Ver estadísticas del sistema |
| `/clear` | Limpiar pantalla |
| `/quit` | Salir |

---

## Problemas Comunes

### "python: command not found"
**Solución:** Reinstala Python marcando "Add to PATH"

### "ANTHROPIC_API_KEY not found"
**Solución:** Repite el paso 5 (configurar clave)

### "Your credit balance is too low"
**Solución:** Agrega créditos en https://console.anthropic.com

### Muestra caracteres raros (�, �)
**Solución (Windows):** Antes de iniciar:
```cmd
chcp 65001
python -m nucleo chat
```

---

## ¿Cuánto cuesta?

El sistema es **gratis**, pero Claude AI cobra por uso:

- **Haiku** (rápido): ~$0.25 por millón de caracteres
- **Sonnet** (mejor): ~$3 por millón de caracteres

**Típico:** 20 preguntas = menos de $0.10 USD

Para usar el modelo barato:
```cmd
python -m nucleo chat --model claude-haiku-4-5-20251001
```

---

## Más Información

- **Guía completa:** `README.md`
- **Instalación detallada:** `INSTALACION.md`
- **Ejemplos:** `EJEMPLOS.md`
- **Problemas:** https://github.com/metamatematico/Demostrador-de-enunciados-matem-ticos/issues

---

**¡Disfruta tu asistente matemático con IA!** 🎓
