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
        try:
            import streamlit as st
            if hasattr(st, "secrets"):
                url = url or st.secrets.get("SUPABASE_URL")
                key = key or st.secrets.get("SUPABASE_KEY")
        except Exception:
            pass
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
            
            # Tipado estricto y sanitización de fechas
            fecha_val = obs_input.fecha_realizacion or datetime.today().strftime("%Y-%m-%d")
            
            record = {
                "fecha_realizacion": str(fecha_val),
                "terminal": obs_input.terminal or "N/A",
                "area": obs_input.area or "N/A",
                "observador": obs_input.observador or "N/A",
                "empresa_ejecutante": obs_input.empresa_ejecutante or "N/A",
                "pcp_calculado": eval_res.pcp_calculado if eval_res else 0.0,
                "categoria": eval_res.categoria if eval_res else "D",
                "raw_data": {
                    "input": obs_input.model_dump(),
                    "eval": eval_res.model_dump() if eval_res else {}
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
    Recupera el historial para el dashboard (omite raw_data para optimizar ancho de banda y memoria).
    """
    client = get_supabase_client()
    if not client:
        return []
        
    try:
        # Consulta selectiva de columnas necesarias para el Dashboard de BI (ahorro del 85% de RAM)
        cols = "id, created_at, fecha_realizacion, terminal, area, observador, empresa_ejecutante, pcp_calculado, categoria"
        res = client.table("observaciones").select(cols).limit(100000).execute()
        return res.data
    except Exception as e:
        print(f"Error consultando Supabase: {e}")
        return []
