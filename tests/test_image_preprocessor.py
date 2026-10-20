"""
Pruebas Unitarias para el Preprocesador de Imágenes, Detección de Dudas OCR y Visualizaciones 3D.
Garantiza el estándar Anti-Slop y cero regresiones en la optimización de visión multimodal.
"""

import unittest
from PIL import Image
import pandas as pd

from core.image_preprocessor import preflight_image_enhancement
from core.models import BehaviorItem, ObservationInput
from core.charts_3d import build_3d_spatial_cube, build_3d_risk_topography


class TestImagePreprocessorAndConfidence(unittest.TestCase):
    """Verifica las optimizaciones de preprocesamiento de imagen y control de dudas OCR."""

    def test_preflight_enhancement_standard_image(self):
        """Verifica que una imagen estándar se procese y devuelva reporte diagnóstico completo."""
        img = Image.new("RGB", (800, 1000), color=(240, 240, 240))
        enhanced, report = preflight_image_enhancement(img)

        self.assertIsNotNone(enhanced)
        self.assertEqual(enhanced.size, (800, 1000))
        self.assertIn("status", report)
        self.assertIn("mean_brightness", report)
        self.assertIn("contrast_score", report)
        self.assertIn("advisory", report)

    def test_preflight_enhancement_low_resolution(self):
        """Detecta imágenes de baja resolución (<600px) para alertar al usuario."""
        small_img = Image.new("RGB", (300, 400), color=(128, 128, 128))
        _, report = preflight_image_enhancement(small_img)

        self.assertTrue(report["is_low_res"])
        self.assertEqual(report["status"], "LOW_RESOLUTION")
        self.assertIn("<600px", report["advisory"])

    def test_behavior_item_confidence_defaults(self):
        """Valida que los nuevos campos de confianza no rompan la compatibilidad hacia atrás."""
        item = BehaviorItem(item_number=1, cumple="SI")
        self.assertEqual(item.confianza, "ALTA")
        self.assertFalse(item.duda_lectura)

        item_dudoso = BehaviorItem(
            item_number=2,
            cumple="NO",
            por_que_causa="Falta arnés",
            confianza="BAJA",
            duda_lectura=True
        )
        self.assertEqual(item_dudoso.confianza, "BAJA")
        self.assertTrue(item_dudoso.duda_lectura)

    def test_charts_3d_builders(self):
        """Valida que los constructores de gráficos 3D desacoplados generen figuras Plotly válidas."""
        sample_df = pd.DataFrame({
            "area": ["Mantenimiento", "Refrigerados", "Aforos"],
            "empresa_ejecutante": ["CONTECAR", "SPRC", "CONTECAR"],
            "pcp_calculado": [95.0, 100.0, 88.0],
            "categoria": ["A", "A+", "B"]
        })

        fig_cube = build_3d_spatial_cube(sample_df)
        self.assertIsNotNone(fig_cube)
        self.assertEqual(len(fig_cube.data), 2)  # Stem lines + esferas volumétricas

        fig_surf = build_3d_risk_topography(sample_df)
        self.assertIsNotNone(fig_surf)


if __name__ == "__main__":
    unittest.main()
