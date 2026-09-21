"""
Módulo para sincronización de datos con Supabase.
Maneja la inserción por lotes y consulta para el Dashboard (estructura JSON simplificada).
"""
import os
from dotenv import load_dotenv
load_dotenv()
import json
from typing import List, Dict, Any, Optional
from datetime import datetime
from supabase import create_client, Client
from pydantic import BaseModel

def get_supabase_client() -> Optional[Client]:
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    if not url or not key:
        return None
    try:
        return create_client(url, key)
    except Exception as e:
        print(f"Error al inicializar Supabase: {e}")
        return None

def insert_batch_to_supabase(results: List[Dict[str, Any]]) -> bool:
    """
    Inserta el lote procesado en la tabla 'observaciones' de Supabase con estructura JSON.
    """
    client = get_supabase_client()
    if not client:
        return False
        
    records_to_insert = []
    for r in results:
        if r["status"] == "SUCCESS":
            obs_input = r["obs_input"]
            eval_res = r["eval_res"]
            
            # Sanitizar fechas
            fecha_val = getattr(obs_input, "fecha_realizacion", None)
            
            record = {
                "fecha_realizacion": fecha_val if isinstance(fecha_val, str) else str(fecha_val),
                "terminal": getattr(obs_input, "terminal", "N/A"),
                "area": getattr(obs_input, "area", "N/A"),
                "observador": getattr(obs_input, "observador", "N/A"),
                "empresa_ejecutante": getattr(obs_input, "empresa_ejecutante", "N/A"),
                "pcp_calculado": getattr(eval_res, "pcp_calculado", 0.0),
                "categoria": getattr(eval_res, "categoria", "D"),
                "raw_data": {
                    "input": obs_input.model_dump(),
                    "eval": eval_res.model_dump()
                }
            }
            records_to_insert.append(record)
            
    if not records_to_insert:
        return True
        
    try:
        # Asume que la tabla se llama 'observaciones'
        client.table("observaciones").insert(records_to_insert).execute()
        return True
    except Exception as e:
        print(f"Error insertando en Supabase: {e}")
        return False

def fetch_observations_from_supabase() -> List[Dict[str, Any]]:
    """
    Recupera todo el historial para el dashboard.
    """
    client = get_supabase_client()
    if not client:
        return []
        
    try:
        res = client.table("observaciones").select("*").execute()
        return res.data
    except Exception as e:
        print(f"Error consultando Supabase: {e}")
        return []
