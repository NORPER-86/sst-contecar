"""
Suite de Pruebas Automatizadas para el Motor de Extracción Multimodal y Pipeline Completo.
Verifica la ingesta de los 4 archivos PDF escaneados de muestra en DOCUMENTOS DE BASE.
"""

import unittest
import os
import glob
from core.extractor import render_pdf_to_images, process_document


class TestExtractorPipeline(unittest.TestCase):

    def test_pdf_rendering(self):
        """Verifica que PyMuPDF renderice correctamente las páginas de un PDF a imágenes PIL."""
        pdf_path = r"DOCUMENTOS DE BASE\MAN DE INS ELE AGOSTO SEM 3.pdf"
        images = render_pdf_to_images(pdf_path, dpi=150)
        self.assertEqual(len(images), 2)
        self.assertEqual(images[0].mode, "RGB")
        self.assertGreater(images[0].width, 500)
        self.assertGreater(images[0].height, 500)

    def test_process_man_de_ins_ele(self):
        """Procesa escaneo real 1: Mantenimiento Eléctrico (Carlos Romero)."""
        pdf_path = r"DOCUMENTOS DE BASE\MAN DE INS ELE AGOSTO SEM 3.pdf"
        obs, eval_res, row = process_document(pdf_path)
        
        self.assertEqual(obs.terminal, "CTC")
        self.assertEqual(obs.observador, "Carlos Romero")
        self.assertEqual(eval_res.categoria, "C")
        self.assertEqual(eval_res.pcp_calculado, 100.0)
        self.assertEqual(row["TERMINAL"], "CTC")
        self.assertEqual(row["CTC"], "X")

    def test_process_observacion_comportate(self):
        """Procesa escaneo real 2: Entrada y Salida Vehicular (Fabio Galezo)."""
        pdf_path = glob.glob(r"DOCUMENTOS DE BASE\*11-09-2026*.pdf")[0]
        obs, eval_res, row = process_document(pdf_path)
        
        self.assertEqual(obs.terminal, "SPRC")
        self.assertEqual(obs.observador, "Fabio Galezo")
        self.assertEqual(eval_res.pcp_calculado, 100.0)
        self.assertIn(eval_res.categoria, ["B", "B+"])
        self.assertIn("PARE", obs.plan_mejoramiento.propuesto)
        self.assertEqual(row["SPRC"], "X")

    def test_process_camscanner_aforos(self):
        """Procesa escaneo real 3: Plataforma de Aforos (Paula Olivo / Sescaribe)."""
        pdf_path = glob.glob(r"DOCUMENTOS DE BASE\*CamScanner*.pdf")[0]
        obs, eval_res, row = process_document(pdf_path)
        
        self.assertEqual(obs.terminal, "SPRC")
        self.assertIn("Paula", obs.observador)
        self.assertEqual(obs.empresa_ejecutante, "Sescaribe")
        self.assertEqual(eval_res.pcp_calculado, 100.0)
        self.assertEqual(row["SESCARIBE"], "X")

    def test_process_scan_reefer(self):
        """Procesa escaneo real 4: Conexión Reefer (Victor Teran / Impotarja)."""
        pdf_path = glob.glob(r"DOCUMENTOS DE BASE\*Scan_0008*.pdf")[0]
        obs, eval_res, row = process_document(pdf_path)
        
        self.assertEqual(obs.terminal, "SPRC")
        self.assertEqual(obs.observador, "Victor Teran")
        self.assertEqual(obs.empresa_ejecutante, "Impotarja")
        self.assertEqual(eval_res.pcp_calculado, 100.0)
        self.assertEqual(row["IMPOTARJA"], "X")


if __name__ == "__main__":
    unittest.main()
