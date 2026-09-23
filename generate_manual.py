from fpdf import FPDF
import os

class PDF(FPDF):
    def header(self):
        # Arial bold 15
        self.set_font("helvetica", "B", 18)
        # Move to the right
        self.cell(80)
        # Title
        self.cell(30, 10, "Manual de Uso: Plataforma ComPORTate", 0, 0, "C")
        # Line break
        self.ln(20)

    def footer(self):
        # Position at 1.5 cm from bottom
        self.set_y(-15)
        # Arial italic 8
        self.set_font("helvetica", "I", 8)
        # Page number
        self.cell(0, 10, f"Página {self.page_no()}/{{nb}} - CONTECAR & ARL SURA", 0, 0, "C")

    def chapter_title(self, num, title):
        # Arial 12
        self.set_font("helvetica", "B", 14)
        # Background color
        self.set_fill_color(0, 51, 160) # SURA BLUE
        self.set_text_color(255, 255, 255)
        # Title
        self.cell(0, 10, f"Paso {num}: {title}", 0, 1, "L", 1)
        self.set_text_color(0, 0, 0)
        # Line break
        self.ln(4)

    def chapter_body(self, body):
        # Times 12
        self.set_font("helvetica", "", 12)
        # Output justified text
        self.multi_cell(0, 8, body)
        # Line break
        self.ln()

# Instantiate PDF object and add page
pdf = PDF()
pdf.alias_nb_pages()
pdf.add_page()

# Introduction
pdf.set_font("helvetica", "", 12)
intro = (
    "Bienvenido a la nueva plataforma de Seguridad Basada en Comportamientos (SBC) de CONTECAR y ARL SURA. "
    "Este sistema inteligente impulsado por IA le permite digitalizar y auditar formatos físicos de "
    "observación de manera masiva, generando analíticas e informes ejecutivos de alto valor.\n\n"
    "Para acceder, ingrese al enlace web proporcionado por el administrador desde cualquier navegador web moderno."
)
pdf.multi_cell(0, 8, intro)
pdf.ln(5)

# Step 1
pdf.chapter_title(1, "Carga y Escaneo Masivo (Ingesta)")
body1 = (
    "1. En el menú superior, seleccione la pestaña 'Ingesta & Escaneo de Carpeta'.\n"
    "2. Asegúrese de que el Modo de Carga esté en 'Arrastrar Múltiples Archivos (Drag & Drop)'.\n"
    "3. Seleccione los archivos PDF de su computadora, arrástrelos con el ratón y suéltelos sobre "
    "el recuadro gris que dice 'Drag and drop files here'.\n"
    "4. Haga clic en el botón azul 'Procesar Lote Completo'. La Inteligencia Artificial extraerá "
    "toda la información caligráfica y generará la calificación de Calidad."
)
pdf.chapter_body(body1)

# Step 2
pdf.chapter_title(2, "Verificación y Guardado")
body2 = (
    "1. Una vez que la IA termine el escaneo, aparecerán 'Tarjetas de Verificación' para cada PDF.\n"
    "2. Revise que la información extraída coincida con el documento original (podrá ver la foto del documento a la izquierda).\n"
    "3. Si un dato no se extrajo bien por la letra del observador, puede corregirlo manualmente en las casillas.\n"
    "4. Al final de cada tarjeta, presione 'Guardar Individual en Excel / Supabase'. Esto enviará la información "
    "a la base de datos oficial en la nube."
)
pdf.chapter_body(body2)

# Step 3
pdf.chapter_title(3, "Tablero Analítico Gerencial (Dashboard)")
body3 = (
    "1. En el menú superior, diríjase a la pestaña 'Tablero Analítico Gerencial'.\n"
    "2. Configure los filtros superiores según su necesidad: Rango de fechas, Observador, Área Operativa y Categoría.\n"
    "3. MUY IMPORTANTE: Para ver la información, debe hacer clic en el botón azul 'Generar Analítica'.\n"
    "4. El sistema cargará indicadores clave como el % PCP Promedio, observaciones procesadas, y gráficas de distribución "
    "según la Matriz SURA."
)
pdf.chapter_body(body3)

# Add screenshot if available
img_path = r"C:\\Users\\NOPER\\.gemini\\antigravity\\brain\\a8de81f2-a830-4db0-92f0-74f8379d762f\\.user_uploaded\\media_1789997472079.png"
if os.path.exists(img_path):
    pdf.image(img_path, x=15, w=180)
    pdf.ln(10)

# Step 4
pdf.add_page()
pdf.chapter_title(4, "Informe Ejecutivo (IA)")
body4 = (
    "1. Dentro de la misma pestaña del Tablero Analítico, diríjase a la parte inferior (debajo de las gráficas).\n"
    "2. Encontrará una sección llamada 'Generador de Informe Ejecutivo Automático'.\n"
    "3. Haga clic en el botón 'Generar Informe de la Selección'.\n"
    "4. La Inteligencia Artificial analizará estadísticamente todos los filtros que seleccionó y redactará un "
    "informe ejecutivo de 3 párrafos con recomendaciones y conclusiones listos para ser copiados y pegados "
    "en sus correos o presentaciones de gerencia."
)
pdf.chapter_body(body4)

# Output
pdf.output("Manual_Usuario_ComPORTate.pdf")
print("PDF generado exitosamente.")
