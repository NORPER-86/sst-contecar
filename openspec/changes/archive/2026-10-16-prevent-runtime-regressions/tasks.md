# Tasks

## 1. Suite de Pruebas de Humo (Smoke Tests)
- [x] 1.1 Crear `tests/test_app_smoke.py` con verificación de compilación AST y sintaxis de `app.py`.
- [x] 1.2 Implementar prueba unitaria de resiliencia de secretos (0 llaves, 1 llave, 2 llaves) asegurando que `GEMINI_KEY`, `GEMINI_KEYS` y `GEMINI_KEY_STRING` no produzcan `NameError`.
- [x] 1.3 Implementar escaneo de AST para validar que los identificadores de credenciales en `app.py` estén acoplados sin variables huérfanas.

## 2. Verificación y Calidad
- [x] 2.1 Ejecutar suite completa con `python -m unittest discover tests` y verificar 100% de éxito.
- [x] 2.2 Registrar la lección aprendida y contramedida en `error-prevention-registry`.

## 3. Cierre y Sincronización OpenSpec
- [x] 3.1 Validar cambio con `openspec validate prevent-runtime-regressions`.
- [x] 3.2 Aplicar y archivar el cambio en OpenSpec actualizando la especificación principal.
- [ ] 3.3 Commit atómico y push a GitHub con estándar Senior.
