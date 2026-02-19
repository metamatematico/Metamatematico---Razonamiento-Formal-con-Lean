# Demostrador de Enunciados Matemáticos — NLE v7.0

Sistema interactivo de razonamiento matemático formal basado en **NLE v7.0** (Evolutionary Logical Core, Ehresmann Memory Evolutive Systems).

🔗 **Demo en vivo:** https://share.streamlit.io
📄 **Paper:** UNAM 2025 — Leonardo Jiménez Martínez

---

## Funcionalidades

### 🧮 Demostrador
- Consultas en lenguaje natural sobre matemáticas formales
- Soporte para **Google AI Studio** (Gemini 2.0 Flash, gratis)
- Soporte para **Groq** (Llama 3.3 70B, Gemma 2, Mixtral — gratis)
- Soporte para **Anthropic** (Claude Haiku / Sonnet)
- Modo demo sin API key
- Clasificación automática de dominio matemático
- Enriquecimiento de contexto para goals Lean 4

### 📊 Visualizaciones
| Tab | Contenido |
|-----|-----------|
| ⬡ Grafo de Skills | 76 skills en grafo categórico (NetworkX) |
| ◎ Espacio de Embeddings | t-SNE / PCA de embeddings 256-dim |
| ⚙ Arquitectura NLE | Diagrama de bloques del sistema |
| ◈ Complexificación MES | Proceso Pattern→Colimit→Grafo evolucionado |
| → Pipeline | Flujo consulta→respuesta + heatmap inter-categorías |
| ⊛ GNN + Estadísticas | SkillGNN 3×GATConv + PPO (124,420 params) |
| 🔍 Traza de Prueba | **Subred de skills activada para tu teorema** |

---

## Uso rápido (local)

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Modelos gratuitos recomendados

| Proveedor | Modelo | Cómo obtener la key |
|-----------|--------|---------------------|
| Google AI Studio | gemini-2.0-flash | [aistudio.google.com](https://aistudio.google.com) |
| Groq | llama-3.3-70b-versatile | [console.groq.com](https://console.groq.com) |

---

## Arquitectura del sistema NLE v7.0

```
Consulta → CR_tac (co-regulador táctico)
         ├─ RESPONDER → Grafo de Skills → LLM
         └─ ASISTIR  → GoalAnalyzer → Cascada Lean 4 → LLM
                                                ↓
                                         GNN+PPO aprende
                                         Memoria procedimental
```

**76 skills matemáticos** en 14 categorías (L0 Fundamentos → L1 Dominios → L2 Estrategias)
**Colímites categoriales** como mecanismo de emergencia (Axiomas 8.1–8.4 MES)

---

## Despliegue en Streamlit Cloud

1. Fork este repositorio
2. Ve a [share.streamlit.io](https://share.streamlit.io)
3. Conecta tu GitHub → selecciona este repo → `app.py`
4. Deploy (sin configuración adicional)
5. Agrega tu API key en el panel lateral de la app

---

*UNAM 2025 · NLE v7.0 · Leonardo Jiménez Martínez*
