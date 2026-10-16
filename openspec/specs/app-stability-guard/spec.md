# app-stability-guard Specification

## Purpose
Garantiza la estabilidad continua y la ausencia de regresiones de nombres, fallos de importación o variables indefinidas en la aplicación web de Streamlit antes de cualquier despliegue a producción.

## Requirements

### Requirement: Verificación Estática del Árbol Sintáctico (AST) de app.py
El sistema de pruebas SHALL analizar el código fuente de `app.py` mediante inspección de AST para validar que todas las variables globales referenciadas estén declaradas.

#### Scenario: Detección de variables no declaradas o faltantes
- **WHEN** Se ejecuta la suite de pruebas unitarias sobre el código base.
- **THEN** El validador de AST inspecciona las referencias globales en `app.py` y genera una falla inmediata si alguna variable utilizada no está previamente definida en el scope del módulo o en las importaciones.

### Requirement: Prueba de Inicialización de Configuración de Secretos y API Keys
El sistema SHALL comprobar la inicialización de variables de credenciales ante múltiples escenarios de configuración.

#### Scenario: Inicialización con cero, una o múltiples API Keys
- **WHEN** Se ejecuta la prueba de compatibilidad de credenciales bajo diferentes combinaciones de `st.secrets` y variables de entorno.
- **THEN** Las variables `GEMINI_KEY`, `GEMINI_KEYS` y `GEMINI_KEY_STRING` quedan siempre definidas con tipos coherentes (`None`, lista o string) sin levantar excepciones `NameError` ni `AttributeError`.

### Requirement: Puerta de Calidad Pre-Despliegue Mandataria
El sistema SHALL exigir que todas las pruebas de humo y validación de AST pasen con éxito (cero fallas) antes de autorizar cualquier merge o despliegue a la rama `main`.

#### Scenario: Ejecución de la suite completa de pruebas
- **WHEN** Se invoca `python -m unittest discover tests`.
- **THEN** La prueba `test_app_smoke.py` se ejecuta conjuntamente con `test_scoring.py` y `test_extractor.py`, retornando código de salida 0 únicamente si todos los casos pasan.
