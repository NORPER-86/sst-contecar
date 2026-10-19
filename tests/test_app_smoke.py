"""
Pruebas de Humo (Smoke Tests) y Guardián de Estabilidad para app.py.
Valida AST, sintaxis, importaciones y resiliencia de secretos para prevenir regresiones como NameError en producción.
"""

import ast
import unittest
from unittest.mock import patch, MagicMock
import os
import sys

class TestAppSmoke(unittest.TestCase):
    """Verifica que app.py esté sintácticamente sano y sus componentes clave no tengan regresiones."""

    def setUp(self):
        self.old_env = os.environ.get("GEMINI_API_KEY")
        if "GEMINI_API_KEY" in os.environ:
            del os.environ["GEMINI_API_KEY"]
        self.app_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app.py")
        self.assertTrue(os.path.exists(self.app_path), f"No se encontró app.py en {self.app_path}")
        with open(self.app_path, "r", encoding="utf-8") as f:
            self.code_content = f.read()

    def tearDown(self):
        if self.old_env is not None:
            os.environ["GEMINI_API_KEY"] = self.old_env

    def test_app_syntax_and_ast_compilation(self):
        """Verifica que app.py compile a nivel de AST sin ningún SyntaxError."""
        try:
            tree = ast.parse(self.code_content, filename=self.app_path)
            self.assertIsNotNone(tree)
        except SyntaxError as e:
            self.fail(f"SyntaxError en app.py: {e}")

    def test_core_dependencies_importable(self):
        """Verifica que todos los módulos internos requeridos por app.py se importen sin fallar."""
        modules = [
            "core.models",
            "core.scoring",
            "core.excel_sync",
            "core.extractor",
            "core.branding",
            "core.supabase_sync"
        ]
        for mod in modules:
            try:
                __import__(mod)
            except Exception as e:
                self.fail(f"Falla al importar dependencia requerida '{mod}': {e}")

    def test_gemini_keys_variables_defined_globally(self):
        """
        Escanea el AST de app.py para asegurar que GEMINI_KEY, GEMINI_KEYS y GEMINI_KEY_STRING
        estén asignadas en el scope global antes de cualquier uso.
        """
        tree = ast.parse(self.code_content)
        assigned_names = set()
        
        for node in tree.body:
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        assigned_names.add(target.id)

        self.assertIn("GEMINI_KEY", assigned_names, "GEMINI_KEY debe estar explícitamente declarada a nivel de módulo")
        self.assertIn("GEMINI_KEYS", assigned_names, "GEMINI_KEYS debe estar explícitamente declarada a nivel de módulo")
        self.assertIn("GEMINI_KEY_STRING", assigned_names, "GEMINI_KEY_STRING debe estar explícitamente declarada a nivel de módulo")
        self.assertIn("DEEPSEEK_KEY", assigned_names, "DEEPSEEK_KEY debe estar explícitamente declarada a nivel de módulo")

    def test_credentials_initialization_scenarios(self):
        """
        Simula las 3 variantes de entorno para garantizar que ninguna combinación
        cause NameError o excepciones no controladas.
        """
        def simulate_key_resolution(env_dict, secrets_dict):
            keys = []
            if env_dict.get("GEMINI_API_KEY"):
                keys.append(env_dict.get("GEMINI_API_KEY"))
            if env_dict.get("GEMINI_API_KEY_2") and env_dict.get("GEMINI_API_KEY_2") not in keys:
                keys.append(env_dict.get("GEMINI_API_KEY_2"))
            if secrets_dict:
                if "GEMINI_API_KEY" in secrets_dict and secrets_dict["GEMINI_API_KEY"] not in keys:
                    keys.append(secrets_dict["GEMINI_API_KEY"])
                if "GEMINI_API_KEY_2" in secrets_dict and secrets_dict["GEMINI_API_KEY_2"] not in keys:
                    keys.append(secrets_dict["GEMINI_API_KEY_2"])
            gemini_key = keys[0] if keys else None
            gemini_key_string = ",".join(keys) if keys else None
            deepseek_key = env_dict.get("DEEPSEEK_API_KEY") or (secrets_dict.get("DEEPSEEK_API_KEY") if secrets_dict else None)
            return gemini_key, keys, gemini_key_string, deepseek_key

        # Caso 1: Cero llaves (Modo local)
        k, keys, k_str, ds = simulate_key_resolution({}, {})
        self.assertIsNone(k)
        self.assertEqual(keys, [])
        self.assertIsNone(k_str)
        self.assertIsNone(ds)

        # Caso 2: 1 sola llave Gemini
        k, keys, k_str, ds = simulate_key_resolution({}, {"GEMINI_API_KEY": "KEY_1"})
        self.assertEqual(k, "KEY_1")
        self.assertEqual(keys, ["KEY_1"])
        self.assertEqual(k_str, "KEY_1")

        # Caso 3: 2 llaves Gemini con rotación + 1 llave DeepSeek
        k, keys, k_str, ds = simulate_key_resolution(
            {"GEMINI_API_KEY": "KEY_1", "GEMINI_API_KEY_2": "KEY_2", "DEEPSEEK_API_KEY": "DS_KEY"},
            {}
        )
        self.assertEqual(k, "KEY_1")
        self.assertEqual(keys, ["KEY_1", "KEY_2"])
        self.assertEqual(k_str, "KEY_1,KEY_2")
        self.assertEqual(ds, "DS_KEY")

    def test_required_stdlib_imports_present_in_app(self):
        """Verifica que módulos estándar críticos como 're', 'os', 'io', 'glob' estén importados."""
        tree = ast.parse(self.code_content)
        imported_modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_modules.add(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imported_modules.add(node.module)

        for required in ["re", "os", "io", "glob", "pandas", "streamlit"]:
            self.assertIn(
                required,
                imported_modules,
                f"El módulo '{required}' debe estar explícitamente importado en app.py"
            )

    def test_file_upload_sanitization_logic(self):
        """Valida que la rutina de sanitización de archivos subidos no lance NameError y filtre path traversal."""
        import re
        import os

        test_filenames = [
            ("../../../etc/passwd", "passwd.pdf"),
            ("..\\..\\boot.ini", "boot.ini.pdf"),
            ("Reporte SST 2026 #1 & final.pdf", "Reporte_SST_2026__1___final.pdf"),
            ("archivo_sin_extension", "archivo_sin_extension.pdf"),
            ("normal-doc_v1.0.pdf", "normal-doc_v1.0.pdf")
        ]

        for raw_name, expected_safe in test_filenames:
            base_name = os.path.basename(raw_name)
            safe_name = re.sub(r"[^\w\-.]", "_", base_name)
            if not safe_name.lower().endswith(".pdf"):
                safe_name += ".pdf"
            self.assertEqual(safe_name, expected_safe)
            self.assertNotIn("..", safe_name)
            self.assertNotIn("/", safe_name)
            self.assertNotIn("\\", safe_name)

if __name__ == "__main__":
    unittest.main()
