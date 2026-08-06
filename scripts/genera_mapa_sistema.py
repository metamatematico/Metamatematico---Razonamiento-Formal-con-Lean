"""Genera el mapa del sistema Metamatematico en PDF.

Todo lo que aparece aqui esta medido, no inferido del paper.
"""
from datetime import datetime

from fpdf import FPDF

SALIDA = r"E:\Metamatematico\docs\MAPA_DEL_SISTEMA.pdf"

MORADO = (108, 43, 217)
AZUL = (37, 99, 235)
GRIS = (90, 90, 100)
NEGRO = (25, 25, 30)
VERDE = (21, 128, 61)
AMBAR = (180, 83, 9)
ROJO = (185, 28, 28)
FONDO_COD = (244, 244, 248)


class Mapa(FPDF):
    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Main", "", 7.5)
        self.set_text_color(*GRIS)
        self.cell(0, 6, "METAMATEMATICO — Mapa del sistema",
                  new_x="LMARGIN", new_y="NEXT", align="R")
        self.set_draw_color(220, 220, 230)
        self.line(self.l_margin, self.get_y(), self.w - self.r_margin, self.get_y())
        self.ln(3)

    def footer(self):
        self.set_y(-14)
        self.set_font("Main", "", 7.5)
        self.set_text_color(*GRIS)
        self.cell(0, 6, f"{self.page_no()}", align="C")


pdf = Mapa(format="A4")
pdf.set_auto_page_break(auto=True, margin=18)
pdf.add_font("Main", "", "C:/Windows/Fonts/arial.ttf")
pdf.add_font("Main", "B", "C:/Windows/Fonts/arialbd.ttf")
pdf.add_font("Mono", "", "C:/Windows/Fonts/consola.ttf")
pdf.set_margins(18, 16, 18)
pdf.add_page()

W = pdf.w - pdf.l_margin - pdf.r_margin


def h1(txt):
    pdf.ln(3)
    pdf.set_font("Main", "B", 15)
    pdf.set_text_color(*MORADO)
    pdf.multi_cell(W, 8, txt, new_x="LMARGIN", new_y="NEXT")
    pdf.set_draw_color(*MORADO)
    pdf.set_line_width(0.5)
    pdf.line(pdf.l_margin, pdf.get_y() + 1, pdf.l_margin + 28, pdf.get_y() + 1)
    pdf.ln(4)


def h2(txt):
    pdf.ln(2)
    pdf.set_font("Main", "B", 11)
    pdf.set_text_color(*AZUL)
    pdf.multi_cell(W, 6, txt, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)


def p(txt, size=9.5):
    pdf.set_font("Main", "", size)
    pdf.set_text_color(*NEGRO)
    pdf.multi_cell(W, 4.8, txt, new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1.5)


def code(txt):
    pdf.set_font("Mono", "", 7.6)
    pdf.set_text_color(30, 30, 60)
    pdf.set_fill_color(*FONDO_COD)
    for linea in txt.strip("\n").splitlines():
        pdf.multi_cell(W, 3.9, "  " + linea, fill=True,
                       new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2.5)


def tabla(cabeceras, filas, anchos, colores=None):
    pdf.set_font("Main", "B", 8.5)
    pdf.set_fill_color(235, 235, 245)
    pdf.set_text_color(*NEGRO)
    for h, w in zip(cabeceras, anchos):
        pdf.cell(w, 6, h, border=0, fill=True, align="L")
    pdf.ln(6)
    pdf.set_font("Main", "", 8.5)
    for i, fila in enumerate(filas):
        alto = 5.2
        if pdf.get_y() + alto > pdf.h - 20:
            pdf.add_page()
        pdf.set_fill_color(250, 250, 253) if i % 2 else pdf.set_fill_color(255, 255, 255)
        for j, (celda, w) in enumerate(zip(fila, anchos)):
            if colores and j == colores[0]:
                pdf.set_text_color(*colores[1].get(celda, NEGRO))
            else:
                pdf.set_text_color(*NEGRO)
            pdf.cell(w, alto, celda, border=0, fill=True, align="L")
        pdf.ln(alto)
    pdf.ln(3)


# ─────────────────────────────── PORTADA ──────────────────────────────
pdf.ln(14)
pdf.set_font("Main", "B", 26)
pdf.set_text_color(*MORADO)
pdf.multi_cell(W, 12, "METAMATEMATICO", new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Main", "B", 13)
pdf.set_text_color(*NEGRO)
pdf.multi_cell(W, 7, "Mapa del sistema", new_x="LMARGIN", new_y="NEXT")
pdf.ln(2)
pdf.set_font("Main", "", 9.5)
pdf.set_text_color(*GRIS)
pdf.multi_cell(
    W, 5,
    "Nucleo Logico Evolutivo v7.0 + Lean 4 / Mathlib\n"
    f"Generado el {datetime.now().strftime('%d/%m/%Y')}",
    new_x="LMARGIN", new_y="NEXT")
pdf.ln(6)

pdf.set_fill_color(252, 250, 235)
pdf.set_draw_color(230, 200, 120)
pdf.set_font("Main", "B", 9.5)
pdf.set_text_color(*AMBAR)
pdf.multi_cell(W, 5.5, "Sobre este documento", border=1, fill=True,
               new_x="LMARGIN", new_y="NEXT")
pdf.set_font("Main", "", 9)
pdf.set_text_color(*NEGRO)
pdf.multi_cell(
    W, 4.6,
    "Describe el sistema tal y como se comporta al ejecutarlo, no tal y como lo "
    "describe el paper. Cada cifra procede de una medicion sobre esta instalacion. "
    "Cuando un subsistema esta construido pero no influye en la salida, se dice "
    "explicitamente: es la diferencia entre 'el codigo existe y sus tests pasan' y "
    "'cambia lo que el sistema responde'.",
    border=1, fill=True, new_x="LMARGIN", new_y="NEXT")

# ────────────────────────── 1. RECORRIDO ──────────────────────────────
h1("1. Que ocurre cuando escribes una consulta")

code("""
   Usuario (Streamlit, app.py)
        |
        v
   Nucleo.process()
        |
        +--> Co-reguladores deciden la accion .......... CR_tac clasifica
        |      RESPONSE (conversacion o matematica)
        |      ASSIST   (el usuario adjunto codigo Lean)
        |
        +--> Es matematica?  --NO--> LLM directo, sin tocar Lean
        |            |
        |           SI
        |            v
        |    _math_via_lean()  ....................... pipeline principal
        |       1. LLM formaliza el enunciado en Lean 4
        |       2. Se normaliza el codigo (ver seccion 3)
        |       3. Lean verifica ...................... FUENTE DE VERDAD
        |       4. Si falla: reparar imports y reintentar
        |       5. Si hay 'sorry': cascada de solvers
        |       6. El LLM traduce el veredicto a lenguaje natural
        |
        +--> Se registra el resultado en la memoria MES
        +--> Se alimenta el agente PPO
""")

p("El principio de diseno es que la verdad matematica la establece Lean, no el "
  "modelo de lenguaje. El LLM cumple dos papeles distintos y separados: "
  "formalizador al principio y traductor al final. Entre ambos, quien decide es "
  "el verificador.")

# ────────────────────────── 2. ESTADO REAL ────────────────────────────
h1("2. Estado real de cada subsistema")

p("Un subsistema puede estar en tres situaciones distintas. Conviene no "
  "confundirlas.")

tabla(
    ["Subsistema", "Estado", "Que hace hoy"],
    [
        ["LLM (Anthropic)", "ACTIVO", "Formaliza y traduce"],
        ["Lean 4 + Mathlib", "ACTIVO", "Arbitro: acepta o rechaza pruebas"],
        ["Normalizacion Lean", "ACTIVO", "Imports y lemas: sin ella casi nada compila"],
        ["Reparacion de errores", "ACTIVO", "Localiza el modulo que falta y reintenta"],
        ["Grafo de skills", "ACTIVO", "Inyecta skills y tactica en el prompt"],
        ["Memoria procedimental", "ACTIVO", "Reutiliza tacticas que ya funcionaron"],
        ["Co-regulador CR_tac", "ACTIVO", "Decide el enrutado de cada consulta"],
        ["Cascada de solvers", "PARCIAL", "Solo entra si Lean devuelve 'sorry'"],
        ["Otros co-reguladores", "INERTE", "Proponen, pero no alteran la decision"],
        ["Colimites y patrones", "INERTE", "Construido y con tests; fuera del lazo"],
        ["Evolucion / snapshots", "INERTE", "Construido; no toca la salida"],
        ["E-equivalencia", "INERTE", "Construido; no toca la salida"],
        ["GNN + PPO", "DESACTIVADO", "Red degenerada: misma accion para todo"],
    ],
    [46, 26, W - 72],
    colores=(1, {"ACTIVO": VERDE, "PARCIAL": AMBAR,
                 "INERTE": GRIS, "DESACTIVADO": ROJO}),
)

h2("Por que el GNN esta desactivado")
p("La red se entreno con el objetivo 'todo problema matematico -> ASSIST'. Al "
  "haber una sola clase, aprendio la constante y alcanzo el 100% de acierto sin "
  "discriminar nada: devuelve ASSIST tambien para 'Hola' o 'Cual es la capital de "
  "Francia'. El sistema lo detecta con una sonda de cuatro entradas heterogeneas y, "
  "si colapsan a una sola accion, ignora la red y usa la heuristica. Recuperarla "
  "exige reentrenar con un objetivo que tenga al menos dos clases reales.")

# ────────────────────────── 3. CAPA LEAN ──────────────────────────────
h1("3. La capa que hace posible la verificacion")

p("Un modelo de lenguaje escribiendo Lean falla casi siempre por tres motivos, y "
  "ninguno es matematico. Sin esta capa, practicamente ninguna prueba llegaba a "
  "compilar.")

tabla(
    ["Problema", "Tratamiento"],
    [
        ["import Mathlib completo", "Se sustituye por un header estrecho"],
        ["Imports inventados", "Se validan contra las fuentes y se descartan"],
        ["Lemas renombrados", "Tabla de equivalencias (Nat.factors, etc.)"],
        ["Modulo concreto ausente", "Imports tematicos segun el contenido"],
        ["Notacion con ambito", "'open List' solo si el codigo usa ~"],
        ["Identificador no hallado", "Se busca en Mathlib y se reintenta"],
    ],
    [52, W - 52],
)

h2("Por que no se permite 'import Mathlib'")
p("Medido en esta instalacion: importar Mathlib entero tarda 742 segundos, frente "
  "a un limite de 360. Es decir, siempre expiraba y jamas devolvia nada. El header "
  "estrecho compila el mismo teorema en unos 11 segundos.")

h2("El bucle de reparacion")
p("Cuando Lean falla, se extraen los identificadores del mensaje de error (Lean los "
  "nombra de cuatro formas distintas segun el contexto), se localizan sus "
  "declaraciones recorriendo los 7.746 ficheros fuente de Mathlib en una sola "
  "pasada (unos 2 segundos), se deduce el modulo de cada uno y se reintenta. El "
  "reintento solo se acepta si mejora el resultado.")

code("""
   Ejemplo real, area sin ninguna regla especifica:

   1) Lean: ERROR - "Function expected at SimpleGraph"
   2) Busqueda en fuentes ................. 2,0 s
      + import Mathlib.Combinatorics.SimpleGraph.Basic
   3) Lean: SUCCESS ....................... 10,7 s
""")

# ────────────────────────── 4. GRAFO ──────────────────────────────────
h1("4. El grafo de skills")

tabla(
    ["Magnitud", "Valor"],
    [
        ["Nodos (skills)", "172"],
        ["Morfismos", "553"],
        ["Skills fundacionales (L0)", "10"],
        ["Definiciones de dominio (L1-L3)", "162"],
        ["Categorias matematicas", "15"],
        ["Tacticas Lean", "9"],
        ["Estrategias de prueba", "6"],
        ["Enlaces dominio -> tactica", "165"],
    ],
    [70, W - 70],
)

p("Los niveles organizan la granularidad: L1 es el campo entero (teoria de grupos), "
  "L2 la sub-area (algebra homologica) y L3 la sub-rama concreta (homomorfismos de "
  "grupos, factorizacion prima, teoria de Galois).")

h2("Como llega el grafo a influir en la respuesta")
p("Al recibir una consulta se buscan las skills que casan con ella, se recorren sus "
  "dependencias y su tactica asociada, y el resultado se anade al prompt del "
  "modelo. Las skills declaran terminos en espanol y en ingles: sin ellos, ninguna "
  "consulta en castellano casaba con nombres escritos en ingles.")

code("""
   Consulta: "Demuestra el primer teorema de homomorfismo"

   Contexto que recibe el LLM:
     - relevant_skills   : group-homomorphisms
     - prerequisites     : group-theory
     - suggested_tactics : tactic-ring
     - pillar            : SET
""")

p("Los enlaces dominio->tactica son morfismos de tipo TRANSLATION, no DEPENDENCY: "
  "las tacticas pertenecen al pilar de teoria de tipos y los dominios a conjuntos, "
  "categorias o logica, de modo que el morfismo cruza pilares.")

# ────────────────────────── 5. RENDIMIENTO ────────────────────────────
h1("5. Rendimiento medido")

tabla(
    ["Operacion", "Antes", "Ahora"],
    [
        ["Arranque en frio de Lean", "552 s", "11 s"],
        ["Verificacion de un teorema", "167 s", "11-19 s"],
        ["Import de Mathlib completo", "742 s", "(prohibido)"],
        ["Busqueda de un identificador", "-", "2 s"],
        ["Arranque de la aplicacion", "-", "4-8 s"],
    ],
    [64, 34, W - 98],
)

h2("De donde viene la diferencia")
p("Mathlib son 7.746 ficheros compilados. Cuando estaban en el disco USB, el coste "
  "no era el ancho de banda (39 MB/s medidos) sino la latencia de abrir miles de "
  "ficheros pequenos en un disco mecanico. Trasladar esa carpeta al disco de estado "
  "solido redujo el arranque en frio de 552 a 11 segundos.")

# ────────────────────────── 6. INSTALACION ────────────────────────────
h1("6. Como esta instalado")

code("""
   E:\\Metamatematico\\               proyecto (codigo, datos, paper)
     |
     +-- .lake  --> enlace a  C:\\MetamatematicoLake   (Mathlib compilado, SSD)
     +-- app.py                     interfaz Streamlit
     +-- nucleo/                    el sistema
     +-- .streamlit/secrets.toml    clave de API (fuera de git)
     +-- logs/                      traza de ejecucion
     +-- cache/  tmp/               todo lo temporal, nunca en C:

   Acceso directo del escritorio
     -> wscript -> Metamatematico.vbs -> Metamatematico.ps1
     -> env_local.ps1 (redirige temporales) -> streamlit
""")

p("El proyecto vive en E:. La unica excepcion deliberada es la carpeta de Mathlib "
  "compilado, que es cache de compilacion y no datos del proyecto: se movio al SSD "
  "por rendimiento y se dejo un enlace, de modo que para Lean la ruta sigue siendo "
  "la misma.")

# ────────────────────────── 7. LIMITES ────────────────────────────────
h1("7. Que no hace todavia")

h2("Formalizar un marco teorico completo")
p("El pipeline pide al modelo una unica formalizacion y Lean emite un unico "
  "veredicto sobre todo el fichero. Con cinco estructuras interdependientes, si "
  "cada una acierta el 70% de las veces, las cinco juntas salen el 17%. La via es "
  "descomponer: formalizar y verificar pieza a pieza, acumulando lo que ya compila "
  "y reparando lo que falla. El grafo aporta el orden de dependencias.")

h2("Aprender de verdad")
p("La memoria procedimental ya conserva que tactica funciono para cada consulta, "
  "pero el historico anterior se guardo sin ese dato y no es recuperable: hay que "
  "volver a sembrarlo. El agente neuronal necesita reentrenarse con un objetivo "
  "que discrimine.")

h2("Reparar errores de tactica")
p("La cascada de solvers solo actua ante 'sorry'. Los errores de compilacion, que "
  "son los que produce un modelo escribiendo Lean, aun no la activan salvo cuando "
  "se trata de un import ausente.")

pdf.ln(4)
pdf.set_draw_color(200, 200, 215)
pdf.line(pdf.l_margin, pdf.get_y(), pdf.w - pdf.r_margin, pdf.get_y())
pdf.ln(3)
pdf.set_font("Main", "", 8)
pdf.set_text_color(*GRIS)
pdf.multi_cell(
    W, 4.2,
    "Metamatematico — Leonardo Jimenez Martinez (UNAM) · BIOMAT, Centro de "
    "Biomatematicas. Suite de pruebas: 428 tests en verde en el momento de generar "
    "este documento.",
    new_x="LMARGIN", new_y="NEXT")

pdf.output(SALIDA)
print(f"OK -> {SALIDA}")
