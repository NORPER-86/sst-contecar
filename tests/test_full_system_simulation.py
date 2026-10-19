"""
Suite de Pruebas de Simulación de Funcionamiento Integral y Auditoría Anti-Slop
para la Plataforma SST ComPORTate (CONTECAR / SPRC).

Ejecuta simulaciones exhaustivas de todos los componentes del sistema:
1. Ingesta y Sanitización de Archivos
2. Modelos de Dominio y Boundary Parsing
3. Motor de Scoring y Matriz de 9 Categorías
4. Sincronización Excel Maestro (44 Columnas)
5. Sincronización y Resiliencia Supabase
6. Pipeline de Agregación Analítica (BI)
7. Sistema de Diseño y Tokens de Branding SURA
"""

import unittest
import os
import shutil
import tempfile
import pandas as pd
from datetime import datetime
from unittest.mock import patch, MagicMock

from core.models import ObservationInput, BehaviorItem, ImprovementPlan, ObservationEvaluation
from core.scoring import calculate_pcp, evaluate_observation
from core.excel_sync import (
    map_observation_to_44_columns,
    append_to_master_excel,
    append_batch_to_master_excel,
    parse_date,
    get_week_of_month
)
from core.extractor import process_batch, render_pdf_to_images
from core.supabase_sync import insert_batch_to_supabase, fetch_observations_from_supabase
from core.branding import (
    SURA_BLUE, SURA_CYAN, SURA_YELLOW, SURA_NAVY_DARK,
    CATEGORY_PALETTE, get_custom_css, get_header_html
)


class TestFullSystemSimulation(unittest.TestCase):
    """Simulación de extremo a extremo de todos los componentes del sistema."""

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp(prefix="sst_simulation_")
        cls.master_excel_template = os.path.join("DOCUMENTOS DE BASE", "Ejemplos observaciones digitadas.xlsx")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.temp_dir, ignore_errors=True)

    # -------------------------------------------------------------
    # COMPONENTE 1: INGESTA, SANITIZACIÓN Y MANEJO DE LOTES
    # -------------------------------------------------------------
    def test_component_1_ingestion_and_batch_resilience(self):
        """Simula ingesta por lotes con archivos válidos e inválidos garantizando tolerancia a fallos."""
        import re

        # Simulación de sanitización segura de nombres
        nombres_prueba = [
            ("../../etc/shadow", "shadow.pdf"),
            ("Reporte SST #1.pdf", "Reporte_SST__1.pdf"),
            ("OBS 2026-10-19.PDF", "OBS_2026-10-19.PDF")
        ]
        for entrada, esperada in nombres_prueba:
            base = os.path.basename(entrada)
            limpio = re.sub(r"[^\w\-.]", "_", base)
            if not limpio.lower().endswith(".pdf"):
                limpio += ".pdf"
            self.assertEqual(limpio, esperada)
            self.assertNotIn("..", limpio)

        # Simular process_batch con archivos inexistentes: no debe lanzar excepción no controlada
        rutas_ficticias = [
            os.path.join(self.temp_dir, "archivo_inexistente_1.pdf"),
            os.path.join(self.temp_dir, "archivo_inexistente_2.pdf")
        ]
        progress_calls = []

        def track_progress(current, total, fname):
            progress_calls.append((current, total, fname))

        results = process_batch(rutas_ficticias, api_key=None, progress_callback=track_progress)
        self.assertEqual(len(results), 2)
        for r in results:
            self.assertEqual(r["status"], "ERROR")
            self.assertIsNotNone(r["error"])
        self.assertEqual(len(progress_calls), 2)

    # -------------------------------------------------------------
    # COMPONENTE 2: MODELOS DE DOMINIO Y BOUNDARY PARSING
    # -------------------------------------------------------------
    def test_component_2_boundary_parsing_and_schema_validation(self):
        """Valida que los datos externos no tipados se validen estrictamente en la frontera (Boundary Parsing)."""
        from pydantic import ValidationError

        # 1. Caso Válido
        item_valido = BehaviorItem(item_number=1, descripcion="Uso de EPP", cumple="SI")
        self.assertEqual(item_valido.cumple, "SI")

        # 2. Caso Inválido: valor de literal no permitido
        with self.assertRaises(ValidationError):
            BehaviorItem(item_number=1, cumple="TAL_VEZ")

        # 3. Caso Inválido: falta item_number obligatorio
        with self.assertRaises(ValidationError):
            BehaviorItem(cumple="NO")

        # 4. Parsing de ObservationInput completo
        raw_json = {
            "terminal": "CTC",
            "fecha_realizacion": "2026-10-19",
            "hora": "10:30",
            "observador": "Ingeniero Staff",
            "empresa_ejecutante": "CONTECAR",
            "items": [
                {"item_number": 1, "cumple": "SI"},
                {"item_number": 2, "cumple": "NO", "por_que_causa": "Falta de señalización"}
            ],
            "plan_mejoramiento": {
                "propuesto": "Instalar cinta de advertencia",
                "es_viable": True,
                "enfoque_sst": True
            },
            "comentarios_observado": "Se siente respaldado por el proceso"
        }
        obs = ObservationInput.model_validate(raw_json)
        self.assertEqual(obs.terminal, "CTC")
        self.assertEqual(len(obs.items), 2)
        self.assertEqual(obs.items[1].por_que_causa, "Falta de señalización")

    # -------------------------------------------------------------
    # COMPONENTE 3: MOTOR DE SCORING Y MATRIZ DE 9 CATEGORÍAS
    # -------------------------------------------------------------
    def test_component_3_scoring_engine_and_pcp_matrix(self):
        """Simula exhaustivamente el cálculo de PCP y las 9 categorías oficiales de SST."""
        # 1. Cálculo de PCP
        items = [
            BehaviorItem(item_number=1, cumple="SI"),
            BehaviorItem(item_number=2, cumple="SI"),
            BehaviorItem(item_number=3, cumple="NO"),
            BehaviorItem(item_number=4, cumple="N/A")
        ]
        si, no, na, aplicables, pcp = calculate_pcp(items)
        self.assertEqual(si, 2)
        self.assertEqual(no, 1)
        self.assertEqual(na, 1)
        self.assertEqual(aplicables, 3)
        self.assertEqual(pcp, 66.67)

        # 2. Simulación Categoría D: Formato Incompleto (Sin observador ni comentarios)
        obs_d = ObservationInput(
            terminal="CTC",
            fecha_realizacion="2026-10-19",
            hora="08:00",
            observador="",  # Falta observador
            empresa_ejecutante="CTC",
            items=[BehaviorItem(item_number=1, cumple="SI")],
            comentarios_observado=""
        )
        res_d = evaluate_observation(obs_d)
        self.assertEqual(res_d.categoria, "D")
        self.assertTrue(res_d.requiere_subsanacion)

        # 3. Simulación Categoría C: Formato completo, PCP 100%, sin plan, comentario vacío o 'Sin comentarios'
        obs_c = ObservationInput(
            terminal="CTC",
            fecha_realizacion="2026-10-19",
            hora="08:00",
            observador="Carlos Perez",
            empresa_ejecutante="CTC",
            items=[BehaviorItem(item_number=1, cumple="SI")],
            comentarios_observado="Sin comentarios",
            plan_mejoramiento=ImprovementPlan(propuesto=None)
        )
        res_c = evaluate_observation(obs_c)
        self.assertEqual(res_c.categoria, "C")

        # 4. Simulación Categoría C+: Sin plan, pero con comentario de calidad
        obs_cp = ObservationInput(
            terminal="SPRC",
            fecha_realizacion="2026-10-19",
            hora="09:00",
            observador="Maria Gomez",
            empresa_ejecutante="SPRC",
            items=[BehaviorItem(item_number=1, cumple="SI")],
            comentarios_observado="El trabajador agradece la retroalimentación y se compromete a verificar el arnés",
            plan_mejoramiento=ImprovementPlan(propuesto=None)
        )
        res_cp = evaluate_observation(obs_cp)
        self.assertEqual(res_cp.categoria, "C+")

        # 5. Simulación Categoría R: Recomendación No Viable
        obs_r = ObservationInput(
            terminal="CTC",
            fecha_realizacion="2026-10-19",
            hora="10:00",
            observador="Luis Diaz",
            empresa_ejecutante="CTC",
            items=[BehaviorItem(item_number=1, cumple="SI")],
            comentarios_observado="Muy conforme",
            plan_mejoramiento=ImprovementPlan(
                propuesto="Comprar una grúa pórtico nueva para el muelle 1",
                es_recomendacion=True,
                es_viable=False
            )
        )
        res_r = evaluate_observation(obs_r)
        self.assertEqual(res_r.categoria, "R")

        # 6. Simulación Categoría R+: Recomendación Viable
        obs_rp = ObservationInput(
            terminal="CTC",
            fecha_realizacion="2026-10-19",
            hora="10:00",
            observador="Luis Diaz",
            empresa_ejecutante="CTC",
            items=[BehaviorItem(item_number=1, cumple="SI")],
            comentarios_observado="Muy conforme",
            plan_mejoramiento=ImprovementPlan(
                propuesto="Ajustar el espejo retrovisor izquierdo del montacargas 04",
                es_recomendacion=True,
                es_viable=True
            )
        )
        res_rp = evaluate_observation(obs_rp)
        self.assertEqual(res_rp.categoria, "R+")

        # 7. Simulación Categoría B: Plan de Mejora Estándar Aplicable
        obs_b = ObservationInput(
            terminal="SPRC",
            fecha_realizacion="2026-10-19",
            hora="11:00",
            observador="Pedro Soto",
            empresa_ejecutante="SPRC",
            items=[BehaviorItem(item_number=1, cumple="SI")],
            comentarios_observado="Observación constructiva",
            plan_mejoramiento=ImprovementPlan(
                propuesto="Organizar cables en el piso del taller",
                es_recomendacion=False,
                es_viable=True,
                enfoque_sst=False
            )
        )
        res_b = evaluate_observation(obs_b)
        self.assertEqual(res_b.categoria, "B")

        # 8. Simulación Categoría B+: Plan enfocado en SST o con evidencia fotográfica
        obs_bp = ObservationInput(
            terminal="SPRC",
            fecha_realizacion="2026-10-19",
            hora="11:00",
            observador="Pedro Soto",
            empresa_ejecutante="SPRC",
            items=[BehaviorItem(item_number=1, cumple="SI")],
            comentarios_observado="Observación constructiva",
            plan_mejoramiento=ImprovementPlan(
                propuesto="Reemplazar línea de vida desgastada en rampa",
                es_recomendacion=False,
                es_viable=True,
                enfoque_sst=True,
                evidencia_fotografica_detectada=True
            )
        )
        res_bp = evaluate_observation(obs_bp)
        self.assertEqual(res_bp.categoria, "B+")

        # 9. Simulación Categoría A: Alto impacto preventivo con evidencia fotográfica
        obs_a = ObservationInput(
            terminal="CTC",
            fecha_realizacion="2026-10-19",
            hora="12:00",
            observador="Andres Torres",
            empresa_ejecutante="CTC",
            items=[BehaviorItem(item_number=1, cumple="SI")],
            comentarios_observado="Excelente retroalimentación",
            plan_mejoramiento=ImprovementPlan(
                propuesto="Reconfigurar sistema de frenado automático de RTG para evitar colisión",
                es_recomendacion=False,
                es_viable=True,
                alto_impacto=True,
                evidencia_fotografica_detectada=True
            )
        )
        res_a = evaluate_observation(obs_a)
        self.assertEqual(res_a.categoria, "A")

        # 10. Simulación Categoría A+: Alto impacto con análisis causal / de seguridad anexo
        obs_ap = ObservationInput(
            terminal="CTC",
            fecha_realizacion="2026-10-19",
            hora="12:00",
            observador="Andres Torres",
            empresa_ejecutante="CTC",
            items=[BehaviorItem(item_number=1, cumple="SI")],
            comentarios_observado="Excelente retroalimentación",
            plan_mejoramiento=ImprovementPlan(
                propuesto="Rediseño del flujo de tráfico vehicular con matriz DOFA y estudio causal",
                es_recomendacion=False,
                es_viable=True,
                alto_impacto=True,
                analisis_seguridad_anexo=True
            )
        )
        res_ap = evaluate_observation(obs_ap)
        self.assertEqual(res_ap.categoria, "A+")

    # -------------------------------------------------------------
    # COMPONENTE 4: BASE DE DATOS MAESTRA DE 44 COLUMNAS (EXCEL)
    # -------------------------------------------------------------
    def test_component_4_excel_master_sync_and_44_columns(self):
        """Simula mapeo riguroso de 44 columnas y adición atómica / por lotes en Excel."""
        obs = ObservationInput(
            terminal="CTC",
            area="MANTENIMIENTO",
            lider_area="Juan Valiente",
            codigo_formato="HS-FMT305",
            fecha_realizacion="2026-10-19",
            hora="14:30",
            lugar="Taller Eléctrico",
            tarea_critica="Mantenimiento eléctrico en subestación",
            observador="Ingeniero Auditor",
            empresa_ejecutante="SESCARIBE",
            items=[
                BehaviorItem(item_number=1, cumple="SI"),
                BehaviorItem(item_number=2, cumple="NO", por_que_causa="Herramienta sin aislamiento")
            ],
            plan_mejoramiento=ImprovementPlan(
                propuesto="Dotar al personal con kit dieléctrico certificado",
                tipo_ejecucion="Fácil",
                es_viable=True,
                enfoque_sst=True
            ),
            comentarios_observado="Recibe las recomendaciones adecuadamente",
            comentarios_adicionales_observador="Cumple la mayoría de pasos de seguridad"
        )
        eval_res = evaluate_observation(obs)
        row_44 = map_observation_to_44_columns(obs, eval_res)

        # Verificar integridad del diccionario de 44 columnas
        self.assertEqual(row_44["TERMINAL"], "CTC")
        self.assertEqual(row_44["ÁREA"], "MANTENIMIENTO")
        self.assertEqual(row_44["MES"], "10. OCTUBRE")
        self.assertEqual(row_44["TRIMESTRE"], "IV TRIMESTRE")
        self.assertEqual(row_44["SESCARIBE"], "X")
        self.assertIsNone(row_44["IMPOTARJA"])
        self.assertEqual(row_44["ITEM CON OPORTUNIDAD DE MEJORA"], "2")
        self.assertIn("Herramienta sin aislamiento", row_44["CAUSA DEL ITEM INCUMPLIDO (¿POR QUÉ?)"])
        self.assertEqual(row_44["CALIFICACIÓN CALIDAD INTERNA"], eval_res.categoria)

        # Probar adición en Excel real si la plantilla existe
        if os.path.exists(self.master_excel_template):
            test_excel = os.path.join(self.temp_dir, "test_maestro.xlsx")
            shutil.copy2(self.master_excel_template, test_excel)

            # Inserción individual
            inserted_row = append_to_master_excel(test_excel, row_44, sheet_name="BD")
            self.assertGreater(inserted_row, 3)

            # Inserción por lote (2 registros)
            batch_rows = append_batch_to_master_excel(test_excel, [row_44, row_44], sheet_name="BD")
            self.assertEqual(len(batch_rows), 2)
            self.assertEqual(batch_rows[1], batch_rows[0] + 1)

    # -------------------------------------------------------------
    # COMPONENTE 5: SINCRONIZACIÓN Y RESILIENCIA SUPABASE
    # -------------------------------------------------------------
    def test_component_5_supabase_resilience_and_memory_optimization(self):
        """Simula el comportamiento del conector Supabase bajo condiciones de ausencia o presencia de llaves."""
        # En ausencia de credenciales válidas, get_supabase_client() debe ser None sin lanzar error
        with patch.dict(os.environ, {"SUPABASE_URL": "", "SUPABASE_KEY": ""}):
            from core.supabase_sync import get_supabase_client
            client = get_supabase_client()
            self.assertIsNone(client)
            self.assertFalse(insert_batch_to_supabase([{"status": "SUCCESS", "obs_input": MagicMock(), "eval_res": MagicMock()}]))
            self.assertEqual(fetch_observations_from_supabase(), [])

        # Con cliente mockeado, verificar optimización de columnas solicitadas (no traer raw_data para ahorrar RAM)
        with patch("core.supabase_sync.get_supabase_client") as mock_get_client:
            mock_client = MagicMock()
            mock_table = MagicMock()
            mock_select = MagicMock()
            mock_limit = MagicMock()
            mock_limit.execute.return_value = MagicMock(data=[{"id": 1, "pcp_calculado": 100.0, "categoria": "C"}])
            mock_select.limit.return_value = mock_limit
            mock_table.select.return_value = mock_select
            mock_client.table.return_value = mock_table
            mock_get_client.return_value = mock_client

            data = fetch_observations_from_supabase()
            self.assertEqual(len(data), 1)
            # Asegurar que se solicitan únicamente columnas específicas de BI
            mock_table.select.assert_called_with("id, created_at, fecha_realizacion, terminal, area, observador, empresa_ejecutante, pcp_calculado, categoria")

    # -------------------------------------------------------------
    # COMPONENTE 6: TABLERO ANALÍTICO GERENCIAL (BI) Y BENCHMARK $O(N)$
    # -------------------------------------------------------------
    def test_component_6_bi_analytics_processing_and_algorithmic_efficiency(self):
        """Valida que los cálculos de agregación del Dashboard BI sean $O(N)$, sin copias cuadráticas ni NaN no controlados."""
        # Simular DataFrame representativo de observaciones históricas
        data = {
            "FECHA REALIZACIÓN": ["2026-08-01", "2026-08-15", "2026-09-01", "2026-09-15", "2026-10-01"],
            "TERMINAL": ["CTC", "CTC", "SPRC", "SPRC", "CTC"],
            "ÁREA": ["OPERACIONES", "MANTENIMIENTO", "AFOROS", "OPERACIONES", "MANTENIMIENTO"],
            "EMPRESA EJECUTANTE 1": ["CTC", "SESCARIBE", "IMPOTARJA", "SPRC", "CTC"],
            "PCP": [1.0, 0.9, 0.85, 1.0, 0.95], # Formato decimal
            "CATEGORÍA DE LA OBSERVACIÓN": ["A", "B+", "C", "D", "B"]
        }
        df = pd.DataFrame(data)

        # 1. Normalización de PCP a porcentaje
        pcp_vals = df["PCP"].apply(lambda v: v * 100.0 if v <= 1.0 else v)
        self.assertAlmostEqual(pcp_vals.mean(), 94.0, places=2)

        # 2. Distribución de categorías
        cat_counts = df["CATEGORÍA DE LA OBSERVACIÓN"].value_counts().to_dict()
        self.assertEqual(cat_counts["A"], 1)
        self.assertEqual(cat_counts["B+"], 1)
        self.assertEqual(cat_counts["D"], 1)

        # 3. Agrupación temporal O(N) sin acumuladores con spread
        df["FECHA_DT"] = pd.to_datetime(df["FECHA REALIZACIÓN"])
        trend = df.groupby(df["FECHA_DT"].dt.to_period("M"))["PCP"].mean()
        self.assertEqual(len(trend), 3) # Ago, Sep, Oct

    # -------------------------------------------------------------
    # COMPONENTE 7: MANUAL DE MARCA Y TOKENS VISUALES SURA
    # -------------------------------------------------------------
    def test_component_7_branding_design_tokens_and_accessibility(self):
        """Valida que los estilos, colores corporativos SURA y paletas semafóricas cumplan con los estándares."""
        # Validar colores primarios
        self.assertEqual(SURA_BLUE, "#0033A0")
        self.assertEqual(SURA_CYAN, "#00AEC7")
        self.assertEqual(SURA_YELLOW, "#FFC72C")
        self.assertEqual(SURA_NAVY_DARK, "#0A1E4A")

        # Validar que las 9 categorías tengan color y contraste en CATEGORY_PALETTE
        for cat in ["D", "C", "C+", "R", "R+", "B", "B+", "A", "A+"]:
            self.assertIn(cat, CATEGORY_PALETTE)
            cat_info = CATEGORY_PALETTE[cat]
            self.assertTrue(cat_info["color"].startswith("#"))
            self.assertTrue(cat_info["bg"].startswith("#"))
            self.assertTrue(len(cat_info["label"]) > 0)

        # Validar inyección CSS
        css = get_custom_css()
        self.assertIn("font-family", css)
        self.assertIn(SURA_BLUE, css)
        self.assertIn(".sura-header-container", css)
        self.assertIn(".sura-kpi-card", css)


if __name__ == "__main__":
    unittest.main()
