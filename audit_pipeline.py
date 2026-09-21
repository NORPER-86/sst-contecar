import os
import json
import logging
from core.extractor import extract_observation_from_file
from core.supabase_sync import insert_batch_to_supabase, fetch_observations_from_supabase
from core.excel_sync import map_observation_to_44_columns
from core.scoring import evaluate_observation
import pandas as pd

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Auditoria-E2E")

PDF_TEST = r"DOCUMENTOS DE BASE\Scan_0008 2.pdf"

def auditar_pipeline():
    logger.info("=== INICIANDO AUDITORÍA COMPLETA DEL PIPELINE ===")
    
    # 1. Prueba de Extracción OCR (Gemini 3.1 Pro / Fallback)
    logger.info(f"1. Extrayendo datos de {PDF_TEST}")
    try:
        resultado = extract_observation_from_file(PDF_TEST)
        logger.info("✅ Extracción completada correctamente.")
        # logger.info(f"Datos: {resultado.model_dump_json(indent=2)}")
    except Exception as e:
        logger.error(f"❌ Fallo en extracción: {e}")
        return

    # 2. Prueba de Evaluación Lógica (Reglas de Negocio / OpenSpec)
    logger.info("2. Evaluando reglas de negocio...")
    try:
        eval_res = evaluate_observation(resultado)
        logger.info(f"✅ Reglas evaluadas. PCP: {eval_res.pcp_calculado}%, Categoría: {eval_res.categoria}")
    except Exception as e:
        logger.error(f"❌ Fallo en evaluación: {e}")
        return

    # 3. Prueba de Mapeo a Excel (44 Columnas)
    logger.info("3. Mapeando a formato Excel 44 Columnas...")
    try:
        row_44 = map_observation_to_44_columns(resultado, eval_res)
        logger.info(f"✅ Mapeo exitoso. Total columnas: {len(row_44)}")
    except Exception as e:
        logger.error(f"❌ Fallo en mapeo Excel: {e}")
        return

    # 4. Prueba de Sincronización Supabase
    logger.info("4. Simulando guardado en Supabase...")
    lote_simulado = [{
        "file_name": os.path.basename(PDF_TEST),
        "status": "SUCCESS",
        "obs_input": resultado,
        "eval_res": eval_res,
        "row_44": row_44
    }]
    
    try:
        supa_status = insert_batch_to_supabase(lote_simulado)
        if supa_status:
            logger.info("✅ Guardado en Supabase EXITOSO.")
        else:
            logger.error("❌ Fallo en Supabase (retornó False).")
    except Exception as e:
        logger.error(f"❌ Error en Supabase: {e}")

    # 5. Prueba de Recuperación desde Supabase
    logger.info("5. Verificando lectura desde Supabase (Dashboard)...")
    try:
        registros = fetch_observations_from_supabase()
        logger.info(f"✅ Leídos {len(registros)} registros de Supabase.")
        df = pd.DataFrame(registros)
        logger.info(f"Columnas obtenidas: {list(df.columns)}")
    except Exception as e:
        logger.error(f"❌ Fallo en lectura Supabase: {e}")

if __name__ == "__main__":
    auditar_pipeline()
