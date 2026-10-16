# Design: App Stability Guard & Pre-Deploy Smoke Verification

## Context
Ver `proposal.md` y `specs/app-stability-guard/spec.md`. El proyecto corre sobre Streamlit Cloud. Los scripts de Streamlit ejecutan el archivo principal de arriba a abajo en cada renderizado. Errores de nombres no definidos (`NameError`) detienen la aplicación inmediatamente al arrancar si no se detectan antes del despliegue.

## Goals / Non-Goals

**Goals:**
- Implementar pruebas de humo en `tests/test_app_smoke.py` que verifiquen el módulo `app.py`.
- Emplear el analizador sintáctico nativo de Python (`ast`) para auditar asignaciones y referencias de nombres en `app.py` sin necesidad de ejecutar un servidor web completo en entornos CI.
- Probar formalmente las combinaciones de configuración de `GEMINI_KEY`, `GEMINI_KEYS` y `GEMINI_KEY_STRING`.
- Integrar la verificación al pipeline de Git y al registro de lecciones aprendidas.

**Non-Goals:**
- No se requiere montar un entorno Selenium o Playwright para pruebas E2E en esta fase (evita lentitud y dependencias de navegadores en contenedores livianos).
- No modificar la arquitectura de persistencia existente (Excel + Supabase).

## Decisions

### Decisión 1: AST y PyCompile vs Mock de Streamlit
- **Alternativa A:** Ejecutar `streamlit run app.py` en background y medir tiempo de respuesta. (Riesgoso en CI por puertos y timeouts).
- **Alternativa B (Elegida):** Combinar `py_compile` (AST y sintaxis), análisis de variables no resueltas mediante el visitor del AST nativo de Python, y prueba unitaria de la lógica de carga de llaves y secretos con `unittest.mock`.
- **Razón:** Es ultrarrápido (< 0.2 segundos), 100% determinístico y no requiere dependencias externas pesadas.

### Decisión 2: Política de "Zero Warning & Zero Regression"
- La suite de pruebas debe ejecutarse y validar el 100% antes de cualquier `git merge main` o `git push`.

## Risks / Trade-offs

- **[Riesgo]** Falsos positivos en análisis de AST para variables inyectadas dinámicamente por librerías.
  - **Mitigación:** Definir lista blanca (allowlist) de built-ins estándar de Python y variables globales declaradas en `app.py`.
- **[Riesgo]** Desconexión de secretos en Streamlit Cloud.
  - **Mitigación:** Probar explícitamente que ante ausencia de `st.secrets` el sistema no lance excepción sino que degrade limpiamente al modo local.
