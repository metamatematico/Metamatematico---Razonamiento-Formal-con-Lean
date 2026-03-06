"""
Generate PDF: Hierarchy-Reasoning Integration
==============================================

Generates a PDF documenting the implementation that connects
the categorical skill hierarchy to actual proof reasoning.

Usage:
    python scripts/generate_hierarchy_pdf.py
"""

from fpdf import FPDF
from pathlib import Path
import datetime


class HierarchyPDF(FPDF):
    """PDF document for Hierarchy-Reasoning Integration."""

    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.cell(0, 8, "NLE v7.0 - Hierarchy-Reasoning Integration", align="C")
        self.ln(4)
        self.set_draw_color(0, 102, 204)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(6)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.cell(0, 10, f"Pagina {self.page_no()}/{{nb}}", align="C")

    def chapter_title(self, title: str):
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(0, 51, 102)
        self.cell(0, 10, title)
        self.ln(8)
        self.set_text_color(0, 0, 0)

    def section_title(self, title: str):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(0, 76, 153)
        self.cell(0, 8, title)
        self.ln(7)
        self.set_text_color(0, 0, 0)

    def body_text(self, text: str):
        self.set_font("Helvetica", "", 10)
        self.multi_cell(0, 5.5, text)
        self.ln(3)

    def code_block(self, code: str):
        self.set_font("Courier", "", 8.5)
        self.set_fill_color(240, 240, 245)
        lines = code.strip().split("\n")
        for line in lines:
            safe = line.encode("latin-1", "replace").decode("latin-1")
            self.cell(0, 4.5, f"  {safe}", fill=True)
            self.ln()
        self.ln(3)
        self.set_font("Helvetica", "", 10)

    def bullet(self, text: str, indent: int = 10):
        self.set_font("Helvetica", "", 10)
        x = self.get_x()
        self.set_x(x + indent)
        safe = text.encode("latin-1", "replace").decode("latin-1")
        self.multi_cell(0, 5.5, f"* {safe}")
        self.ln(1)

    def bold_text(self, label: str, text: str):
        self.set_font("Helvetica", "B", 10)
        safe_label = label.encode("latin-1", "replace").decode("latin-1")
        self.write(5.5, safe_label)
        self.set_font("Helvetica", "", 10)
        safe_text = text.encode("latin-1", "replace").decode("latin-1")
        self.write(5.5, safe_text)
        self.ln(6)


def generate():
    pdf = HierarchyPDF()
    pdf.alias_nb_pages()
    pdf.set_auto_page_break(auto=True, margin=20)

    # =====================================================================
    # PAGE 1: Title + Problem
    # =====================================================================
    pdf.add_page()

    # Title
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(0, 51, 102)
    pdf.cell(0, 15, "Integracion Jerarquia-Razonamiento", align="C")
    pdf.ln(12)

    pdf.set_font("Helvetica", "B", 14)
    pdf.cell(0, 10, "Nucleo Logico Evolutivo v7.0", align="C")
    pdf.ln(10)

    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 6, "Leonardo Jiménez Martínez - BIOMAT · Centro de Biomatemáticas", align="C")
    pdf.ln(5)
    today = datetime.date.today().strftime("%d de %B de %Y")
    pdf.cell(0, 6, today, align="C")
    pdf.ln(15)

    pdf.set_text_color(0, 0, 0)

    # Problem statement
    pdf.chapter_title("1. El Problema")

    pdf.body_text(
        "El NLE v7.0 contiene un grafo categorico de 76 skills matematicos "
        "organizado en 4 pilares (SET, CAT, LOG, TYPE), con dependencias, "
        "traducciones inter-pilar, tacticas Lean 4 y estrategias de prueba. "
        "Sin embargo, esta estructura jerarquica era operacionalmente inerte: "
        "existia como dato pero no participaba en la generacion de pruebas."
    )

    pdf.section_title("1.1 Diagnostico: Tres desconexiones")

    pdf.bold_text(
        "Desconexion 1 - Solver Cascade fijo: ",
        "El cascade de tacticas (rfl, simp, ring, linarith, ...) ejecutaba "
        "siempre en el mismo orden sin importar la estructura del goal. "
        "Un goal algebraico como 'a * b + c = c + b * a' desperdiciaba tiempo "
        "probando rfl y simp antes de llegar a ring."
    )
    pdf.ln(2)

    pdf.bold_text(
        "Desconexion 2 - Contexto aleatorio para el LLM: ",
        "Cuando el sistema consultaba a Claude, le pasaba los primeros 10 "
        "skill IDs del grafo (list(skill_ids)[:10]), sin relevancia alguna "
        "con la consulta del usuario."
    )
    pdf.ln(2)

    pdf.bold_text(
        "Desconexion 3 - CR_tac solo por keywords: ",
        "El co-regulador tactico clasificaba queries solo con una lista fija "
        "de palabras clave (ASSIST_KEYWORDS). Una consulta sobre 'ring "
        "homomorphism' no activaba ASSIST aunque el sistema sabe que "
        "ring-theory esta conectado a tacticas Lean."
    )

    # =====================================================================
    # PAGE 2: Solution Architecture
    # =====================================================================
    pdf.add_page()
    pdf.chapter_title("2. Solucion: Tres Puntos de Integracion")

    pdf.body_text(
        "Se implementaron tres componentes que conectan la jerarquia categorica "
        "al razonamiento real. Cada uno opera en un punto diferente del pipeline "
        "de procesamiento, manteniendo compatibilidad hacia atras."
    )

    # A. GoalAnalyzer
    pdf.section_title("2.1 GoalAnalyzer (solver_cascade.py)")

    pdf.bold_text("Proposito: ", "Reordenar el cascade de tacticas segun la estructura del goal.")
    pdf.ln(2)

    pdf.bold_text("Mecanismo: ", "Dos niveles de analisis:")
    pdf.bullet("Nivel 1 - Regex: 6 patrones detectan tipo de goal (algebra, aritmetica, logica, etc.)")
    pdf.bullet("Nivel 2 - Grafo: Si se pasa el skill graph, busca skills de dominio que coincidan "
               "con el goal, luego recorre sus vecinos para encontrar tactic-* skills")

    pdf.body_text("Patrones regex implementados:")
    pdf.code_block(
        "GOAL_PATTERNS = [\n"
        '  (r"[+\\-*^].*=.*[+\\-*^]",  ["ring", "nlinarith", "linarith"]),\n'
        '  (r"(Nat|Int|Fin).*[<=>=]",   ["omega", "linarith", "simp"]),\n'
        '  (r"\\d+\\s*[+\\-*]\\s*\\d+=", ["omega", "simp", "ring"]),\n'
        '  (r"[and/or/not/iff]|True",   ["simp", "tauto", "aesop"]),\n'
        '  (r"[forall/exists]|->",      ["simp", "exact", "apply?"]),\n'
        '  (r"List.|Array.|length",     ["simp", "omega"]),\n'
        "]"
    )

    pdf.body_text("Mapeo skill-to-solver para integracion con el grafo:")
    pdf.code_block(
        "_SKILL_TO_SOLVER = {\n"
        '  "tactic-simp": "simp",   "tactic-ring": "ring",\n'
        '  "tactic-omega": "omega", "tactic-exact": "exact?",\n'
        '  "tactic-apply": "apply?","tactic-aesop": "aesop",\n'
        "}"
    )

    pdf.bold_text("Ejemplo: ", "")
    pdf.code_block(
        'goal = "a * b + c = c + b * a"\n'
        "# Sin GoalAnalyzer: rfl -> simp -> ring -> ... (ring es 3ro)\n"
        "# Con GoalAnalyzer: ring -> nlinarith -> linarith -> rfl -> ..."
    )

    pdf.bold_text("Metodo smart: ", "try_fill_sorry_smart(code, sorry_line, goal_text) "
                  "usa GoalAnalyzer para reordenar temporalmente el cascade antes de ejecutar.")

    # =====================================================================
    # PAGE 3: Context + CR_tac
    # =====================================================================
    pdf.add_page()

    # B. Graph-Aware Context
    pdf.section_title("2.2 Contexto Graph-Aware (core.py)")

    pdf.bold_text("Proposito: ", "Dar al LLM contexto relevante extraido del grafo, "
                  "no una lista aleatoria de skill IDs.")
    pdf.ln(2)

    pdf.bold_text("Metodos nuevos en Nucleo:", "")
    pdf.ln(2)

    pdf.bullet("_match_skills_to_query(query, graph): Tokeniza el query, compara contra "
               "IDs y nombres de skills, retorna ordenados por solapamiento de tokens.")
    pdf.bullet("_find_relevant_context(query, graph): Para cada skill matched, recorre "
               "dependencias (graph.dependencies) y vecinos (graph.neighbors) buscando "
               "tactic-* y strategy-* skills.")
    pdf.bullet("_dominant_pillar(skill_ids, graph): Cuenta pilares de los skills matched, "
               "retorna el mas frecuente (default: TYPE).")

    pdf.body_text("Estructura del contexto generado:")
    pdf.code_block(
        "{\n"
        '  "relevant_skills": ["ring-theory", "group-theory"],\n'
        '  "prerequisites": ["zfc-axioms"],\n'
        '  "suggested_tactics": ["tactic-ring", "tactic-simp"],\n'
        '  "proof_strategies": ["strategy-backward"],\n'
        '  "pillar": "SET"\n'
        "}"
    )

    pdf.bold_text("Antes: ", 'context = {"skills": list(self._graph.skill_ids)[:10]}')
    pdf.bold_text("Ahora: ", "context = self._find_relevant_context(query, self._graph)")
    pdf.ln(4)

    # C. CR_tac Graph-Informed
    pdf.section_title("2.3 CR_tac Graph-Informed (co_regulators.py)")

    pdf.bold_text("Proposito: ", "Clasificar queries usando el grafo, no solo keywords fijos.")
    pdf.ln(2)

    pdf.body_text(
        "El co-regulador tactico ahora tiene una cadena de clasificacion de 3 niveles:"
    )
    pdf.bullet("Nivel 1 - Neural: Si hay GNN+PPO entrenada, la red decide (mas rapido).")
    pdf.bullet("Nivel 2 - Keywords: Lista fija de ASSIST_KEYWORDS (prove, theorem, lean, sorry, ...).")
    pdf.bullet("Nivel 3 - Grafo: Tokeniza el query, busca skills con tokens coincidentes, "
               "y si algun skill matched tiene un vecino tactic-* o strategy-*, retorna ASSIST.")

    pdf.body_text("Firma actualizada (retrocompatible):")
    pdf.code_block(
        "def classify_query(\n"
        "    self, query: str, graph: Optional[SkillCategory] = None\n"
        ") -> ActionType:"
    )

    pdf.bold_text("Ejemplo: ", '"ring homomorphism" -> match ring-theory -> vecino tactic-ring -> ASSIST')
    pdf.ln(2)
    pdf.bold_text("Sin grafo: ", '"ring homomorphism" -> no keyword match -> RESPONSE (antes)')

    # =====================================================================
    # PAGE 4: Flow diagram + Why
    # =====================================================================
    pdf.add_page()
    pdf.chapter_title("3. Flujo Integrado")

    pdf.body_text(
        "Los tres componentes operan en secuencia durante el procesamiento "
        "de una consulta:"
    )

    pdf.code_block(
        "CONSULTA: 'ring homomorphism preserves addition'\n"
        "  |\n"
        "  v\n"
        "CR_tac.classify_query(query, graph)\n"
        "  |-- keywords: no match\n"
        "  |-- graph: 'ring' token -> ring-theory skill\n"
        "  |         ring-theory neighbors -> tactic-ring, tactic-simp\n"
        "  |         tactic-* found -> ASSIST\n"
        "  v\n"
        "Nucleo._find_relevant_context(query, graph)\n"
        "  |-- matched: [ring-theory, group-theory]\n"
        "  |-- deps: [zfc-axioms]\n"
        "  |-- tactics: [tactic-ring, tactic-simp]\n"
        "  |-- pillar: SET\n"
        "  v\n"
        "LLM recibe contexto estructurado\n"
        "  |\n"
        "  v\n"
        "Si hay goal Lean -> GoalAnalyzer.prioritize(goal, graph)\n"
        "  |-- regex: algebra pattern -> ring first\n"
        "  |-- graph: ring-theory -> tactic-ring -> ring\n"
        "  |-- cascade: ring, nlinarith, linarith, rfl, simp, ...\n"
        "  v\n"
        "SolverCascade.try_fill_sorry_smart() ejecuta en orden optimizado"
    )

    pdf.chapter_title("4. Por que se hizo")

    pdf.body_text(
        "La motivacion principal es hacer que la estructura categorica del "
        "sistema sea funcional, no decorativa. El NLE v7.0 modela el "
        "conocimiento matematico segun los Memory Evolutive Systems de "
        "Ehresmann, donde:"
    )

    pdf.bullet("Los skills forman los objetos de una categoria")
    pdf.bullet("Los morfismos (DEPENDENCY, TRANSLATION, COMPOSITION) capturan "
               "relaciones estructurales entre areas matematicas")
    pdf.bullet("Los pilares (SET, CAT, LOG, TYPE) organizan el conocimiento "
               "en perspectivas complementarias")

    pdf.body_text(
        "Sin embargo, hasta esta implementacion, la categoria existia solo "
        "como estructura de datos verificable (axiomas 8.1-8.4, teoremas "
        "8.5-8.7) pero no participaba en las decisiones del sistema. "
        "Esto equivalia a tener un mapa detallado pero no consultarlo "
        "al navegar."
    )

    pdf.body_text(
        "La integracion cierra esta brecha en tres dimensiones:"
    )

    pdf.bullet("Eficiencia: El GoalAnalyzer evita probar tacticas irrelevantes. "
               "Un goal algebraico va directo a ring en vez de probar rfl, simp primero.")
    pdf.bullet("Relevancia: El LLM recibe contexto extraido del grafo (skills "
               "relacionados, prerequisitos, tacticas sugeridas) en vez de IDs aleatorios.")
    pdf.bullet("Clasificacion: El CR_tac puede activar asistencia Lean para queries "
               "que mencionan dominios matematicos conectados a tacticas, "
               "sin necesitar keywords exactos.")

    # =====================================================================
    # PAGE 5: Tests + Technical details
    # =====================================================================
    pdf.add_page()
    pdf.chapter_title("5. Verificacion: 27 Tests Nuevos")

    pdf.body_text(
        "Se crearon 27 tests en tests/test_hierarchy_integration.py que "
        "verifican los tres puntos de integracion, elevando el total de "
        "352 a 379 tests:"
    )

    pdf.section_title("5.1 TestGoalAnalyzer (9 tests)")
    pdf.bullet("Ring goal prioriza ring (a * b + c = c + b * a)")
    pdf.bullet("Arithmetic goal prioriza omega (Nat.succ n <= n + 1)")
    pdf.bullet("Simple equality mantiene rfl primero (x = x)")
    pdf.bullet("Logic goal prioriza simp (P and Q -> Q and P)")
    pdf.bullet("Goal desconocido mantiene orden default")
    pdf.bullet("Goal con grafo usa tactic skills conectados")
    pdf.bullet("Goal vacio retorna default cascade")
    pdf.bullet("Lista reordenada contiene los 9 solvers")
    pdf.bullet("Aritmetica numerica prioriza omega/simp/ring")

    pdf.section_title("5.2 TestRelevantContext (9 tests)")
    pdf.bullet("Query 'group theory' matchea group-theory skill")
    pdf.bullet("Query 'ring' matchea ring-theory skill")
    pdf.bullet("Query 'induction' matchea tactic-induction")
    pdf.bullet("Dependencias se recorren (ring-theory -> zfc-axioms)")
    pdf.bullet("Tacticas conectadas aparecen en suggested_tactics")
    pdf.bullet("Query desconocido retorna contexto vacio")
    pdf.bullet("Pilar SET detectado para skills SET")
    pdf.bullet("Pilar TYPE detectado para skills TYPE")
    pdf.bullet("Pilar default TYPE cuando no hay skills")

    pdf.section_title("5.3 TestCRTacGraphAware (7 tests)")
    pdf.bullet("Keywords ASSIST siguen funcionando sin grafo")
    pdf.bullet("Non-keyword sin grafo retorna RESPONSE")
    pdf.bullet("Skill con tacticas conectadas retorna ASSIST")
    pdf.bullet("Skill sin tacticas conectadas retorna RESPONSE")
    pdf.bullet("_relevant_skills se puebla despues de classify")
    pdf.bullet("Keywords no pueblan _relevant_skills")
    pdf.bullet("graph=None no crashea, fallback a keywords")

    pdf.section_title("5.4 TestIntegration (2 tests)")
    pdf.bullet("Smart cascade completo con ring goal: ring en posicion <= 1")
    pdf.bullet("Pipeline CR_tac + context finder funciona end-to-end")

    # =====================================================================
    # PAGE 6: Files modified + Summary
    # =====================================================================
    pdf.add_page()
    pdf.chapter_title("6. Archivos Modificados")

    pdf.body_text("Cuatro archivos modificados, uno creado:")

    # Table
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(0, 76, 153)
    pdf.set_text_color(255, 255, 255)
    col_w = [60, 65, 60]
    headers = ["Archivo", "Cambio", "Lineas"]
    for i, h in enumerate(headers):
        pdf.cell(col_w[i], 7, h, border=1, fill=True, align="C")
    pdf.ln()

    pdf.set_font("Helvetica", "", 8.5)
    pdf.set_text_color(0, 0, 0)
    rows = [
        ("solver_cascade.py", "GoalAnalyzer + try_fill_sorry_smart", "~115 nuevas"),
        ("core.py", "_find_relevant_context + helpers", "~105 nuevas"),
        ("co_regulators.py", "classify_query graph + _match", "~70 nuevas"),
        ("test_hierarchy_integr...", "27 tests nuevos (CREADO)", "~336 nuevas"),
        ("README.md", "Documentacion actualizada", "~30 modificadas"),
    ]
    for row in rows:
        for i, val in enumerate(row):
            pdf.cell(col_w[i], 6, val, border=1)
        pdf.ln()

    pdf.ln(8)

    pdf.chapter_title("7. Para que Sirve")

    pdf.body_text(
        "Esta implementacion transforma la jerarquia categorica de un "
        "artefacto verificable (axiomas, teoremas) a un componente funcional "
        "que influye en tres decisiones concretas del sistema:"
    )

    pdf.bold_text("1. Que tacticas probar primero: ",
                  "GoalAnalyzer usa patrones + grafo para reordenar el "
                  "solver cascade, reduciendo intentos fallidos.")
    pdf.ln(2)
    pdf.bold_text("2. Que contexto dar al LLM: ",
                  "_find_relevant_context extrae skills, prerequisitos, "
                  "tacticas y pilares relevantes del grafo.")
    pdf.ln(2)
    pdf.bold_text("3. Cuando activar asistencia Lean: ",
                  "CR_tac usa el grafo para detectar queries que "
                  "involucran dominios conectados a tacticas formales.")

    pdf.ln(6)
    pdf.body_text(
        "En conjunto, estos tres puntos hacen que el conocimiento "
        "estructurado en la categoria no sea solo una formalizacion "
        "teorica, sino una guia activa para el razonamiento automatizado."
    )

    pdf.ln(4)

    pdf.section_title("Compatibilidad")
    pdf.body_text(
        "Todos los cambios son retrocompatibles. Los metodos originales "
        "(try_fill_sorry, classify_query sin graph) siguen funcionando "
        "sin modificacion. Los 352 tests previos siguen pasando, mas "
        "los 27 nuevos = 379 tests totales."
    )

    # Save
    out_dir = Path("docs")
    out_dir.mkdir(exist_ok=True)
    out_path = out_dir / "Integracion_Jerarquia_Razonamiento.pdf"
    pdf.output(str(out_path))
    print(f"PDF generado: {out_path}")
    return out_path


if __name__ == "__main__":
    generate()
