# Especificación de Motor de Observación de Comportamientos SST (CONTECAR / SPRC)

## Purpose
El motor de observación automatiza la validación, cálculo de porcentaje de comportamiento positivo (%PCP), clasificación de calidad (D a A+), generación de recomendaciones y sincronización a la base maestra de 44 columnas para las observaciones de tareas críticas de CONTECAR y SPRC.

## Requirements

### Requirement: Validación de Metadatos Obligatorios
El sistema SHALL verificar la completitud de los metadatos requeridos para cada formato escaneado.

#### Scenario: Formato con metadatos completos
- **WHEN** Una observación contiene terminal ('CTC' o 'SPRC'), fecha, hora, lugar, tarea crítica, observador y empresa ejecutante.
- **THEN** El sistema valida los metadatos como completos y continúa al análisis de ítems.

#### Scenario: Formato con campos obligatorios vacíos
- **WHEN** Falta alguno de los campos fecha, hora, terminal, lugar u observador.
- **THEN** El sistema marca la observación con Categoría 'D' y genera una recomendación solicitando completar la información faltante.

### Requirement: Validación de Comportamientos Críticos y Cálculo del %PCP
El sistema SHALL evaluar el cumplimiento de cada comportamiento crítico y calcular el porcentaje de comportamiento positivo (%PCP).

#### Scenario: Cálculo estándar del %PCP
- **WHEN** Se registran comportamientos como 'SI', 'NO' o 'N/A'.
- **THEN** El sistema calcula `%PCP = (Total SI / (Total SI + Total NO)) * 100`.

#### Scenario: Ítem marcado como NO sin causa justificada
- **WHEN** Un comportamiento crítico es marcado como 'NO' pero el campo '¿Por qué?' está vacío.
- **THEN** El sistema marca la observación con Categoría 'D'.

#### Scenario: PCP inferior a 100% sin plan de mejoramiento
- **WHEN** El `%PCP` calculado es menor al 100% y no se diligenció la sección de 'Planes de Mejoramiento'.
- **THEN** El sistema marca la observación con Categoría 'D'.

### Requirement: Reglas de Clasificación de Calidad
El sistema SHALL asignar una categoría de calidad y recomendación formal basada en la matriz de evaluación de CONTECAR / SPRC.

#### Scenario: Categoría C por falta de comentarios sustantivos
- **WHEN** El formato está completo, no tiene plan de mejora y los comentarios del observado indican 'Sin comentarios'.
- **THEN** El sistema asigna Categoría 'C' y emite la recomendación de fortalecer la formulación de planes de mejora y registrar la percepción del observado.

#### Scenario: Categoría C+ por comentarios redactados
- **WHEN** El formato está completo, no tiene plan de mejora pero los comentarios del observado y/o adicionales están bien redactados.
- **THEN** El sistema asigna Categoría 'C+' y emite la recomendación correspondiente.

#### Scenario: Categoría B por plan de mejora estándar
- **WHEN** El formato registra un plan de mejora específico y aplicable en la operación.
- **THEN** El sistema asigna Categoría 'B' y prepara el plan para validación con el encargado de gestión.

#### Scenario: Categoría B+ o A por evidencias fotográficas y enfoque SST
- **WHEN** El plan de mejora está enfocado en prevención de accidentes / SST e incluye evidencias fotográficas o análisis anexo en el documento.
- **THEN** El sistema asigna Categoría 'B+' o 'A' reconociendo los anexos y gestionando la condición reportada.

### Requirement: Mapeo y Persistencia en 44 Columnas de Excel
El sistema SHALL transformar la observación procesada a una fila estructurada con las 44 columnas requeridas por el archivo maestro.

#### Scenario: Mapeo a fila de base de datos maestra
- **WHEN** Una observación es validada y categorizada.
- **THEN** El sistema mapea cada campo a su posición exacta (1 a 44), calculando trimestre, mes y semana según la fecha de realización, y activando los flags de empresas contratistas.
