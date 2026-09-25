# Arquitectura del Sistema - SST ComPORTate

## Estado de la Versión: v1.0.0 (MVP) + Parche Anti-Evasivas
**Última Actualización:** Septiembre 2026

## 1. Módulos Principales
- **`app.py`**: Interfaz de usuario (Frontend en Streamlit). Maneja la Ingesta (Drag & Drop), el Tablero Analítico y la conexión con el modelo AI de Gemini.
- **`core/extractor.py`**: Motor de Visión Multimodal. Usa `gemini-3.8-flash` en cascada hasta `2.5-flash` para leer imágenes y extraer OCR. Ahora maneja fallos inyectando datos nulos reales, no mocks.
- **`core/scoring.py`**: Motor matemático. Evalúa el %PCP y asigna Categorías (A+, A, B+, B, C+, C, D). **[NUEVO]** Incorpora filtro estricto de palabras evasivas (*"ninguna"*, *"no aplica"*) que neutraliza el Plan de Mejora y fuerza categorías C o D.
- **`core/supabase_sync.py`**: Capa de persistencia. Inserción masiva y lectura de hasta 100,000 registros para evitar pérdida de datos en el BI.
- **`core/models.py`**: Esquemas de Pydantic que garantizan que el JSON devuelto por la IA sea perfecto.

## 2. Flujo de Datos
1. Usuario arrastra PDF -> `extractor.py` lo pasa a imagen y llama a Gemini.
2. Gemini devuelve JSON estructurado según `ObservationInput`.
3. `scoring.py` califica la observación (Reglas SURA).
4. El usuario revisa en UI y hace clic en Guardar -> `supabase_sync.py` y `excel_sync.py` guardan la información.
5. El Dashboard lee de Supabase (caché de 60s) y grafica.

## 3. Decisiones de Diseño (ADRs)
- Se eliminó Tkinter por incompatibilidad con Streamlit Cloud.
- Se implementó un botón manual "Generar Analítica" para no saturar las consultas a Supabase cada vez que cambia un filtro.
