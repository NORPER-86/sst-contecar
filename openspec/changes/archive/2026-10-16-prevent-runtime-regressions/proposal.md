# Proposal: App Stability Guard & Pre-Deploy Smoke Verification

## Why
Recientemente ocurrió una regresión en producción (`NameError` en `app.py`) al inicializar la UI de Streamlit debido a una variable no definida tras un refactor. No existía un mecanismo automatizado de verificación de arranque ("Smoke Test") ni análisis estático que impidiera el despliegue de código con variables indefinidas o importaciones rotas en el punto de entrada principal. Se requiere blindar el ciclo de vida del software con pruebas de humo y validación de AST antes de cualquier merge a producción.

## What Changes
- **New Capability (`app-stability-guard`)**: Especifica la obligatoriedad de ejecución de pruebas de humo y análisis de AST sobre `app.py` previas al despliegue.
- Creación de suite automatizada `tests/test_app_smoke.py` que:
  - Valida la sintaxis y el árbol sintáctico (AST) de `app.py` verificando que no existan variables globales no asignadas o `NameError` potenciales.
  - Simula la carga de variables de entorno y secretos con 0, 1 y múltiples API Keys asegurando que `GEMINI_KEY`, `GEMINI_KEYS` y `GEMINI_KEY_STRING` siempre queden definidos y coherentes.
- Integración en la suite general de pruebas para que `python -m unittest discover tests` ejecute estas comprobaciones de forma mandataria.
- Registro inmutable en el repositorio de prevención de errores (`error-prevention-registry`).

## Capabilities

### New Capabilities
- `app-stability-guard`: Validación estática y dinámica de estabilidad del punto de entrada `app.py` garantizando tolerancia a fallos, consistencia de secretos y ausencia de regresiones de nombres.

### Modified Capabilities
<!-- No requirement changes to observation-engine -->

## Impact
- **Código Afectado**: `tests/test_app_smoke.py`, `app.py`.
- **APIs y Dependencias**: Usa el módulo estándar `ast` y `unittest`. Cero sobrecarga ni nuevas dependencias pesadas.
- **Flujo de Integración**: Todo merge futuro a `main` debe tener la suite de pruebas al 100% en verde.
