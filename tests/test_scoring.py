"""
Suite de Pruebas Unitarias y de Integración para el Motor de Scoring y Mapeo Excel.
Valida el cumplimiento estricto de la especificación OpenSpec y los casos reales escaneados.
"""

import unittest
from core.models import BehaviorItem, ImprovementPlan, ObservationInput
from core.scoring import calculate_pcp, evaluate_observation
from core.excel_sync import map_observation_to_44_columns


class TestObservationScoring(unittest.TestCase):

    def test_pcp_calculation(self):
        """Verifica la fórmula matemática oficial de %PCP."""
        items = [
            BehaviorItem(item_number=1, cumple="SI"),
            BehaviorItem(item_number=2, cumple="SI"),
            BehaviorItem(item_number=3, cumple="NO", por_que_causa="Distracción"),
            BehaviorItem(item_number=4, cumple="N/A"),
        ]
        si, no, na, aplicables, pcp = calculate_pcp(items)
        self.assertEqual(si, 2)
        self.assertEqual(no, 1)
        self.assertEqual(na, 1)
        self.assertEqual(aplicables, 3)
        self.assertEqual(pcp, 66.67)

    def test_category_d_incomplete_metadata(self):
        """Verifica que observaciones sin metadatos obligatorios sean Categoría D."""
        obs = ObservationInput(
            terminal=None, # Falta terminal
            fecha_realizacion="2026-08-20",
            hora="14:00",
            observador="Carlos Romero",
            empresa_ejecutante="Contecar",
            items=[BehaviorItem(item_number=1, cumple="SI")],
            comentarios_observado="Buena jornada"
        )
        res = evaluate_observation(obs)
        self.assertEqual(res.categoria, "D")
        self.assertTrue(res.requiere_subsanacion)
        self.assertIn("Terminal", res.motivo_subsanacion)

    def test_category_d_no_without_cause(self):
        """Verifica que un ítem marcado con NO sin justificación sea Categoría D."""
        obs = ObservationInput(
            terminal="CTC",
            fecha_realizacion="2026-08-20",
            hora="14:00",
            observador="Carlos Romero",
            empresa_ejecutante="Contecar",
            items=[
                BehaviorItem(item_number=1, cumple="NO", por_que_causa=None) # Sin ¿Por qué?
            ],
            comentarios_observado="Buena jornada"
        )
        res = evaluate_observation(obs)
        self.assertEqual(res.categoria, "D")
        self.assertIn("¿Por qué?", res.motivo_subsanacion)

    def test_category_d_pcp_below_100_without_plan(self):
        """Verifica que PCP < 100% sin plan de mejoramiento sea Categoría D."""
        obs = ObservationInput(
            terminal="CTC",
            fecha_realizacion="2026-08-20",
            hora="14:00",
            observador="Carlos Romero",
            empresa_ejecutante="Contecar",
            items=[
                BehaviorItem(item_number=1, cumple="SI"),
                BehaviorItem(item_number=2, cumple="NO", por_que_causa="Falta de arnés")
            ],
            plan_mejoramiento=ImprovementPlan(propuesto=None), # Sin plan
            comentarios_observado="Estuvo bien"
        )
        res = evaluate_observation(obs)
        self.assertEqual(res.categoria, "D")
        self.assertIn("menor al 100%", res.motivo_subsanacion)

    def test_category_c_sin_comentarios(self):
        """Caso Real MAN DE INS ELE: PCP 100%, sin plan, comentarios = 'Sin comentarios' -> Categoría C."""
        items = [BehaviorItem(item_number=i, cumple="SI") for i in range(1, 19)]
        obs = ObservationInput(
            codigo_formato="HS-FMT305",
            terminal="CTC",
            fecha_realizacion="2026-08-20",
            hora="14:20",
            lugar="Plataforma rife 5A",
            tarea_critica="Mantenimiento de Instalaciones Eléctricas",
            observador="Carlos Romero",
            supervisor_sst="Said Zabaleta",
            empresa_ejecutante="Contecar",
            items=items,
            pcp_manuscrito=100.0,
            comentarios_observado="Sin comentarios",
            comentarios_adicionales_observador="Sin comentarios"
        )
        res = evaluate_observation(obs)
        self.assertEqual(res.categoria, "C")
        self.assertEqual(res.pcp_calculado, 100.0)
        self.assertFalse(res.discrepancia_pcp)
        self.assertIn("formular planes de mejora", res.recomendaciones)

    def test_category_c_plus_with_qualitative_comments(self):
        """Comentarios bien redactados sin plan de mejora -> Categoría C+."""
        items = [BehaviorItem(item_number=i, cumple="SI") for i in range(1, 11)]
        obs = ObservationInput(
            terminal="CTC",
            fecha_realizacion="2026-08-20",
            hora="10:00",
            observador="Ruben Quintana",
            empresa_ejecutante="Contecar",
            items=items,
            comentarios_observado="Los trabajos en altura son críticos, es excelente que se supervise con regularidad."
        )
        res = evaluate_observation(obs)
        self.assertEqual(res.categoria, "C+")
        self.assertIn("identifique un plan de mejora", res.recomendaciones)

    def test_category_b_standard_plan(self):
        """Caso Real Observación Compórtate: Plan específico de mejora -> Categoría B."""
        items = [BehaviorItem(item_number=i, cumple="SI") for i in range(1, 9)]
        items.extend([BehaviorItem(item_number=i, cumple="N/A") for i in range(9, 13)])
        
        obs = ObservationInput(
            codigo_formato="HS-FMT316",
            terminal="SPRC",
            fecha_realizacion="2026-09-11",
            hora="14:10",
            tarea_critica="Operaciones en Entrada y Salida Vehicular",
            observador="Fabio Galezo",
            supervisor_sst="Rubén Triviño",
            empresa_ejecutante="SPRC",
            items=items,
            pcp_manuscrito=100.0,
            plan_mejoramiento=ImprovementPlan(
                propuesto="Remarcar letras de PARE ubicadas en la vía que presentan desgaste",
                tipo_ejecucion="Fácil",
                es_viable=True,
                enfoque_sst=False,
                evidencia_fotografica_detectada=False
            ),
            comentarios_observado="La observación le parece muy buena ya que permite mantener el orden en las áreas."
        )
        res = evaluate_observation(obs)
        self.assertEqual(res.categoria, "B")
        self.assertEqual(res.pcp_calculado, 100.0)

    def test_category_b_plus_plan_sst_with_photos(self):
        """Plan enfocado en SST y con evidencia fotográfica -> Categoría B+."""
        items = [BehaviorItem(item_number=1, cumple="SI")]
        obs = ObservationInput(
            terminal="CTC",
            fecha_realizacion="2026-08-20",
            hora="14:00",
            observador="Carlos Romero",
            empresa_ejecutante="Contecar",
            items=items,
            plan_mejoramiento=ImprovementPlan(
                propuesto="Reemplazar interruptor térmico averiado por sobrecalentamiento",
                enfoque_sst=True,
                evidencia_fotografica_detectada=True
            ),
            comentarios_observado="Muy conforme con el seguimiento"
        )
        res = evaluate_observation(obs)
        self.assertEqual(res.categoria, "B+")
        self.assertIn("Gracias por las fotos", res.recomendaciones)

    def test_category_a_plus_high_impact_causal_analysis(self):
        """Plan de alto impacto con análisis causal / DOFA anexo -> Categoría A+."""
        items = [BehaviorItem(item_number=1, cumple="SI")]
        obs = ObservationInput(
            terminal="CTC",
            fecha_realizacion="2026-08-20",
            hora="14:00",
            observador="Carlos Romero",
            empresa_ejecutante="Contecar",
            items=items,
            plan_mejoramiento=ImprovementPlan(
                propuesto="Rediseño ergonómico de barandas en Reach Stacker con sistema anticaídas",
                alto_impacto=True,
                analisis_seguridad_anexo=True,
                evidencia_fotografica_detectada=True
            ),
            comentarios_observado="Aporte crucial para prevenir fatalidades"
        )
        res = evaluate_observation(obs)
        self.assertEqual(res.categoria, "A+")

    def test_44_column_mapping(self):
        """Verifica que el mapeo genere exactamente las 44 columnas canónicas."""
        items = [BehaviorItem(item_number=1, cumple="SI")]
        obs = ObservationInput(
            codigo_formato="HS-FMT305",
            terminal="CTC",
            fecha_realizacion="2026-08-20",
            hora="14:20",
            lugar="Plataforma rife 5A",
            tarea_critica="Mantenimiento de Instalaciones Eléctricas",
            observador="Carlos Romero",
            empresa_ejecutante="Contecar",
            items=items,
            comentarios_observado="Sin comentarios"
        )
        res = evaluate_observation(obs)
        row = map_observation_to_44_columns(obs, res)
        
        self.assertEqual(row["TERMINAL"], "CTC")
        self.assertEqual(row["MES"], "08. AGOSTO")
        self.assertEqual(row["TRIMESTRE"], "III TRIMESTRE")
        self.assertEqual(row["PCP"], 1.0)
        self.assertEqual(row["CATEGORÍA DE LA OBSERVACIÓN"], "C")
        self.assertEqual(row["CTC"], "X")
        self.assertIsNone(row["SPRC"])
        self.assertEqual(len(row), 44)


if __name__ == "__main__":
    unittest.main()
