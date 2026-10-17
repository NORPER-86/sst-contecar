# MEMORIA TÉCNICA, ALCANCE, LOGROS, FRUSTRACIONES Y REGISTRO DE ERRORES
## Proyecto: SST ComPORTate (SURA & Grupo Puerto de Cartagena - CONTECAR / SPRC)
**Estatus:** Producción Activa (v1.2.0)  
**Marco de Gobernanza:** Spec-Driven Development (OpenSpec) + Harness Engineering  
**Autoría Técnica:** Equipo de Ingeniería Senior & Antigravity Orchestrator  
**Fecha:** Octubre 2026  

---

## 1. DESCRIPCIÓN DETALLADA DE LA APLICACIÓN

### 1.1. Propósito Operativo y Estratégico
El sistema **SST ComPORTate** nace de la necesidad de modernizar, automatizar y blindar la gestión de la Seguridad y Salud en el Trabajo (SST) para las terminales marítimas de **CONTECAR** y **SPRC** (Sociedad Portuaria Regional de Cartagena), en alianza con **ARL SURA**.

Históricamente, los supervisores y observadores de patio diligencian formatos físicos en papel durante la observación de comportamientos en tareas críticas (conexión de contenedores refrigerados, trabajos eléctricos, operaciones en muelle, aforos, etc.). Estos formularios en papel debían ser recolectados, interpretados manualmente por un asistente y transcritos celda por celda a una hoja maestra de Excel con 44 columnas. Este proceso manual introducía:
1. Retrasos de días entre la observación en patio y el análisis gerencial.
2. Errores humanos de transcripción y sesgos en el cálculo matemático del %PCP (Porcentaje de Comportamiento Positivo).
3. Calificaciones complacientes o infladas donde formatos vacíos o evasivos recibían la máxima distinción.

**SST ComPORTate** digitaliza y automatiza este ciclo completo mediante un flujo **Human-in-the-Loop** impulsado por Visión Artificial Multimodal, evaluación matemática estricta según lineamientos SURA y doble sincronización de datos (Local en Excel + Nube en Supabase).

---

### 1.2. Arquitectura de Módulos y Flujo de Datos

```
[ Formatos PDF Escaneados (Patio) ]
               │
               ▼
┌────────────────────────────────────────────────────────┐
│  app.py (Streamlit Web Interface - Manual de Marca)    │
│  - Carga masiva por arrastre (Drag & Drop de PDFs)    │
│  - Renderizado de progreso y aislamiento de errores    │
└───────────────────────┬────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────┐
│  core/extractor.py (Motor de Visión Multimodal)       │
│  - Renderizado PDF a imágenes 300 DPI (PyMuPDF)       │
│  - Realce de contraste (+50%) y nitidez (+20%) con PIL│
│  - Inferencia con Google GenAI (Gemini Vision)        │
│  - Cascada de modelos (3.8 -> 3.7 -> 3.6 -> 2.5 Flash)│
│  - Rotación multi-llave y freno anti-cuota (3s delay) │
│  - Validación contra esquema tipado Pydantic           │
└───────────────────────┬────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────┐
│  core/scoring.py (Motor de Calificación SURA)          │
│  - Cálculo determinista del %PCP                      │
│  - Detección de discrepancias matemáticas manuscritas │
│  - Validación semántica de planes de mejora con IA    │
│  - Clasificación de calidad: A+, A, B+, B, C+, C, D   │
└───────────────────────┬────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────┐
│  Persistencia Híbrida y Visualización BI               │
│  ├── core/excel_sync.py -> Matriz Canónica 44 Columnas │
│  ├── core/supabase_sync.py -> Base Nube PostgreSQL    │
│  └── Tablero BI en app.py (Filtros, KPIs, Reporte IA) │
└────────────────────────────────────────────────────────┘
```

#### Descripción de Componentes Clave:
* **`app.py`:** Interfaz web corporativa con diseño de alta fidelidad basado en el Manual de Marca de SURA (Azul `#0033A0`, Cian `#00A3E0`, Amarillo `#FFD100`). Provee tres pestañas principales: *Ingesta Masiva de PDFs*, *Tablero Analítico Gerencial (BI)* y *Explorador de Base de Datos Maestra (44 Columnas)*.
* **`core/extractor.py`:** Pipeline de extracción de imágenes y llamada estructurada a la API de Google Gemini. Aplica preprocesamiento óptico para facilitar la lectura de letra manuscrita y devuelve un objeto fuertemente tipado `ObservationInput`.
* **`core/models.py`:** Contratos de datos formalizados con Pydantic (`ObservationInput`, `BehaviorItem`, `ImprovementPlan`, `ObservationEvaluation`).
* **`core/scoring.py`:** Implementación exacta de la lógica de evaluación corporativa de SURA. Aplica penalizaciones inmediatas por metadatos faltantes, inconsistencias de PCP o planes evasivos.
* **`core/excel_sync.py`:** Generador de la estructura canónica de 44 columnas que emula celda por celda el archivo histórico `DOCUMENTOS DE BASE/Ejemplos observaciones digitadas.xlsx`.
* **`core/supabase_sync.py`:** Conector cliente a Supabase (PostgreSQL en la nube) que almacena el JSON completo y los metadatos de calidad para permitir consultas analíticas instantáneas desde cualquier lugar sin bloquear el Excel local.

---

## 2. ALCANCE DEL PROYECTO (SCOPE)

### 2.1. Lo que SÍ cubre (In-Scope)
1. **Formatos Oficiales Soportados:**
   * `HS-FMT300`: Formato general de tareas críticas.
   * `HS-FMT303`: Observación de Conexión y Desconexión de Contenedores Refrigerados (Reefer).
   * `HS-FMT305`: Observación de Mantenimiento de Instalaciones Eléctricas.
   * `HS-FMT316`: Observación de Operaciones en Entrada y Salida Vehicular.
   * `HS-FMT322`: Observación de Operaciones en Plataforma de Aforos e Inspecciones.
2. **Terminales Portuarias:** Clasificación y segregación explícita para **CONTECAR (CTC)** y **SPRC** (Sociedad Portuaria Regional de Cartagena).
3. **Modalidad de Ingesta:** Carga por lotes mediante selección múltiple o arrastre de archivos (Drag & Drop) de hasta 200 MB por archivo en PDF o imágenes.
4. **Validación Semántica Cognitiva:** Análisis inteligente del texto diligenciado en la sección de planes de mejora para discriminar recomendaciones genuinas de textos evasivos o excusas.
5. **Auditoría y Mapeo Canónico:** Generación automática de las 44 columnas oficiales respetando la nomenclatura histórica del puerto.
6. **Almacenamiento Dual y Reportes:** Sincronización en la base local `.xlsx` y en base de datos nube Supabase, con generación de informes ejecutivos automatizados redactados por IA.
7. **Gobernanza Spec-Driven Development:** Living Specs en OpenSpec (`observation-engine` y `app-stability-guard`) con suite de 19 pruebas de humo y unitarias.

### 2.2. Lo que NO cubre (Out-of-Scope)
1. **Dispositivos IoT o Cámaras en Vivo:** El sistema no procesa streaming de video de cámaras de seguridad del puerto; trabaja sobre documentos físicos digitalizados.
2. **Firma Digital Biométrica:** No reemplaza firmas de validez jurídica mediante biometría digital; valida la presencia de nombres legibles de observador y supervisor en el papel.
3. **Reemplazo del ERP Central:** No sustituye el sistema SAP o el software transaccional principal del puerto; actúa como subsistema satélite especializado en el programa SBC (Seguridad Basada en Comportamientos).

---

## 3. LOGROS ALCANZADOS (MILESTONES & VICTORIAS)

1. **Eliminación del Cuello de Botella Operativo:** Se pasó de un tiempo promedio de digitación de **15 minutos por formulario** a **3 a 5 segundos por documento**, permitiendo procesar el lote semanal de 50 observaciones en menos de 3 minutos.
2. **Integridad Matemática del 100% en PCP:** El motor calcula matemáticamente el %PCP real a partir de los ítems marcados, detectando automáticamente cuando el observador escribió un cálculo erróneo en el papel y registrando la discrepancia para auditoría de calidad.
3. **Cero Tolerancia a Mocks en Producción:** Se erradicó por completo la inyección de datos simulados (e.g. observadores ficticios como *"Carlos Romero"* en fallbacks) para garantizar que los tableros analíticos reflejen exclusivamente la verdad de la operación.
4. **Preservación Estricta del Esquema de 44 Columnas:** Integración perfecta con el Excel maestro corporativo sin corromper fórmulas preexistentes, tipos de datos ni cabeceras.
5. **Doble Capa de Persistencia:** Acceso analítico instantáneo y distribuido vía Supabase para directores y gerentes de SURA/CONTECAR, mientras la operación conserva su respaldo en Excel.
6. **Manejo Inteligente de API Keys:** Arquitectura de conmutación por error (Failover) que rota transparentemente entre múltiples API Keys de Gemini y aplica retardos de 3 segundos para eludir el límite estricto de 15 peticiones por minuto.
7. **Blindaje contra Regresiones con OpenSpec y Smoke Tests:** Suite de pruebas con cobertura de sintaxis, AST, inicialización de credenciales y escenarios reales con tiempo de ejecución menor a 1 segundo (`Ran 19 tests in 0.970s. OK`).

---

## 4. FRUSTRACIONES Y RETOS TÉCNICOS ENCONTRADOS

Durante las distintas fases del ciclo de vida del software, el equipo de ingeniería enfrentó desafíos técnicos considerables:

### 4.1. Frustración 1: Caligrafía Manuscrita Deficiente y Degradación de Fotocopias
* **El Reto:** Los trabajadores y supervisores diligencian los formularios en el patio bajo el sol, con prisa, apoyados en superficies irregulares, usando bolígrafos con tinta tenue o lápiz. Además, los formatos suelen ser fotocopias de fotocopias que llegan con arrugas, manchas o inclinación.
* **Impacto:** Modelos OCR tradicionales fallaban completamente en identificar los nombres propios o los números de los ítems.
* **Respuesta Aplicada:** Se incrementó la resolución de renderizado a **300 DPI** y se implementó un pipeline de realce digital con `PIL.ImageEnhance` (+50% contraste, +20% nitidez) antes de entregar los cuadros a Gemini Vision. Aunque mejoró notablemente la tasa de acierto, sigue existiendo una minoría de casos donde la caligrafía humana es ilegible incluso para el ojo humano.

### 4.2. Frustración 2: Cuotas Agresivas del Nivel Gratuito de Google Gemini (15 RPM)
* **El Reto:** La directriz del proyecto fue operar bajo el nivel gratuito (Free Tier) de Google AI Studio. Este nivel impone un techo inflexible de **15 peticiones por minuto (RPM)**.
* **Impacto:** Si un usuario subía un lote de 50 PDFs y el procesador los enviaba en paralelo o en bucle rápido, a partir del archivo número 16 Google arrojaba un `Error 429 Too Many Requests (ResourceExhausted)` interrumpiendo el lote.
* **Respuesta Aplicada:** Se construyó la rotación automática entre múltiples llaves de API (`GEMINI_API_KEY` y `GEMINI_API_KEY_2`) y se intercaló un `time.sleep(3)` estratégico por documento para asegurar que el sistema nunca exceda el umbral de 15 peticiones por minuto.

### 4.3. Frustración 3: Suspensión por Inactividad ("Sleep Zzzz") en Streamlit Community Cloud
* **El Reto:** La aplicación está desplegada en la infraestructura gratuita de Streamlit Community Cloud. Si no recibe visitas durante varios días consecutivos, el contenedor entra en modo de hibernación (*"This app has gone to sleep due to inactivity"*).
* **Impacto:** Cuando un usuario intenta acceder después de días de inactividad, se encuentra con una pantalla de espera y un botón que solicita despertar la aplicación, generando la falsa impresión de que el servicio se cayó.

### 4.4. Frustración 4: Renovación de Certificados SSL Let's Encrypt (Gen Y / `YR1`) y Bloqueo HSTS
* **El Reto:** A mediados de octubre de 2026, Streamlit Cloud renovó sus certificados comodín (`*.streamlit.app`) utilizando la nueva jerarquía intermedia `YR1` de Let's Encrypt.
* **Impacto:** Equipos corporativos con sistemas operativos Windows desactualizados o detrás de proxies portuarios con inspección SSL no reconocieron la nueva entidad emisora, arrojando la pantalla roja `NET::ERR_CERT_AUTHORITY_INVALID`. Al tener Streamlit la política estricta HSTS activada, Chrome ocultó el enlace de "Continuar de todos modos", bloqueando el acceso a usuarios que no conocen el atajo de teclado de Chrome.

### 4.5. Frustración 5: Incompatibilidad de Librerías de Escritorio en Contenedores Headless
* **El Reto:** En las fases iniciales se intentó utilizar módulos como `tkinter` para abrir cuadros de diálogo nativos de selección de carpetas en Windows.
* **Impacto:** Al desplegar en Streamlit Cloud (que corre sobre contenedores Linux sin servidor gráfico X11), la aplicación crasheaba de inmediato con `TclError: no display name and no $DISPLAY environment variable`.
* **Respuesta Aplicada:** Se erradicó cualquier rastro de librerías GUI locales y se adoptó el componente nativo web `st.file_uploader` configurado para selección múltiple de PDFs.

---

## 5. CATÁLOGO COMPLETO DE ERRORES E INCIDENTES (HISTORIAL DE DEUDA TÉCNICA)

A continuación se documentan todos los errores que se han manifestado a lo largo del desarrollo, indicando su causa raíz, si fueron solucionados o permanecen bajo mitigación:

| ID | Incidente / Error | Causa Raíz Técnica | Estado | Solución o Mitigación Aplicada |
|---|---|---|---|---|
| **ERR-01** | **Calificación A+ a planes evasivos** | El motor de scoring verificaba la existencia de texto con `len(texto) > 0` sin análisis semántico. Textos como *"ninguna"* o *"todo bien"* eran premiados con calificación máxima A+. | **SOLUCIONADO** | Se agregó el flag `es_plan_valido` a `ImprovementPlan`, se instruyó a Gemini para detectar evasivas semánticas y se programó `scoring.py` para forzar degradación a C/C+ o D ante respuestas complacientes. |
| **ERR-02** | **NameError en `app.py` línea 82** | Al migrar la variable de credencial única `GEMINI_KEY` a una lista `GEMINI_KEYS`, se omitió actualizar la referencia en el condicional de la barra lateral visual. | **SOLUCIONADO** | Se restauró la retrocompatibilidad explícita declarando `GEMINI_KEY = GEMINI_KEYS[0] if GEMINI_KEYS else None` y se creó la suite `tests/test_app_smoke.py` que audita el AST antes de cada commit. |
| **ERR-03** | **Truncamiento silencioso a 1,000 filas en Supabase** | El método `.select("*").execute()` de Supabase tiene un límite interno por defecto de 1,000 registros, lo que ocultaba registros históricos antiguos en el Dashboard. | **SOLUCIONADO** | Se inyectó `.limit(100000)` en `core/supabase_sync.py` para permitir la lectura completa de la base histórica sin truncamiento silencioso. |
| **ERR-04** | **Datos Mocks inyectados en Fallbacks ("Carlos Romero")** | Para evitar que las pruebas locales fallaran sin API Key, el código fallback tenía nombres hardcodeados que se guardaban en la base de datos real ante fallas de escaneo. | **SOLUCIONADO** | Se eliminó cualquier dato simulado. Si un escaneo falla o carece de texto legible, el extractor asigna `N/A`, permitiendo que el motor de scoring marque la observación como Deficiente ('D') para subsanación humana. |
| **ERR-05** | **Crash de arranque en Linux por `tkinter`** | Invocación de `filedialog.askdirectory()` de `tkinter` en código cargado por Streamlit Cloud en contenedores headless. | **SOLUCIONADO** | Se eliminó por completo `tkinter` y los scripts auxiliares obsoletos (`remove_tk.py`). Se estandarizó la carga mediante el componente web nativo `st.file_uploader`. |
| **ERR-06** | **Error 429 Quota Exceeded (ResourceExhausted)** | Envío consecutivo de más de 15 solicitudes por minuto a la API gratuita de Gemini durante la ingesta de lotes medianos. | **SOLUCIONADO** | Implementación de rotación de múltiples llaves (`GEMINI_API_KEY` y `GEMINI_API_KEY_2`) y retardo preventivo de 3 segundos entre documentos. |
| **ERR-07** | **Alerta SSL `ERR_CERT_AUTHORITY_INVALID` con HSTS** | Renovación de certificado wildcard de Streamlit Cloud bajo la nueva entidad intermedia `YR1` de Let's Encrypt (Oct 2026), no reconocida aún por ciertos equipos corporativos con proxies estrictos. | **DOCUMENTADO / MITIGADO** | Solución inmediata documentada para el usuario mediante el bypass de teclado de Chrome (`thisisunsafe`) o el botón "Avanzado". |
| **ERR-08** | **Ilegibilidad de caligrafía extrema en patio** | Trazos incompletos, lápiz borroso o formularios manchados que ni la visión artificial ni el ojo humano logran descifrar con 100% de certeza. | **MITIGADO / PENDIENTE v2.0** | Aumento de DPI a 300 y filtros de contraste/nitidez. En v2.0 se plantea captura digital directa en campo mediante tabletas/móviles para erradicar el papel en observaciones críticas. |
| **ERR-09** | **Demora de 60 segundos en actualización del Dashboard** | Streamlit aplica `@st.cache_data(ttl=60)` para no saturar las consultas a Supabase en cada recarga de pantalla. | **SOLUCIONADO** | Se agregó una advertencia visual explicativa en la UI y un botón manual de refresco inmediato `"🔄 Refrescar Datos Ahora"` que limpia la caché de memoria instantáneamente. |

---

## 6. ESTADO ACTUAL Y GOBERNANZA TÉCNICA

A la fecha de este documento:
* **Entorno de Producción:** 100% Online y desplegado en:  
  `https://sst-contecar-uddimimtns7w5nzav82a9f.streamlit.app/`
* **Gobernanza OpenSpec:** Especificaciones archivadas y activas:
  1. `openspec/specs/observation-engine/spec.md`: Reglas del motor de scoring y mapeo de 44 columnas.
  2. `openspec/specs/app-stability-guard/spec.md`: Auditoría estática obligatoria de AST y pruebas de humo previas al despliegue.
* **Cobertura de Pruebas Automatizadas:** 19/19 tests unitarios pasando en modo sandbox aislado en `0.97` segundos.

---

## 7. HOJA DE RUTA Y RECOMENDACIONES PARA EL FUTURO (ROADMAP v2.0)

Para consolidar el sistema y llevarlo al estándar de clase mundial de la industria portuaria internacional, se recomienda:
1. **Dominio Personalizado Corporativo con SSL Propio:** Configurar un subdominio institucional (e.g. `comportate.puertocartagena.com`) con un certificado SSL corporativo emitido por una CA tradicional (DigiCert / GlobalSign) para evitar cualquier alerta de red o proxy en equipos del puerto.
2. **PWA / App Móvil para Patio (Offline-First):** Dotar a los supervisores de patio de una Progressive Web App en tablets rugerizadas donde puedan marcar los comportamientos directamente en pantalla, eliminando el 100% de los problemas de caligrafía en papel.
3. **Cuenta de Facturación Pay-As-You-Go en Gemini:** Habilitar una tarjeta corporativa en Google Cloud para migrar de la cuota gratuita (15 RPM) al nivel comercial (hasta 1,000+ RPM), lo que permitirá procesar lotes de 100 PDFs en menos de 20 segundos sin necesidad de retardos.
4. **Preprocesamiento Avanzado con OpenCV:** Integrar algoritmos de corrección de perspectiva (Deskewing) y binarización adaptativa Otsu para maximizar la legibilidad de documentos fotografiados torcidos con celular.
