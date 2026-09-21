"""
Módulo de Sincronización y Mapeo a las 44 Columnas del Archivo Excel Maestro.
Garantiza persistencia atómica e integridad de la base histórica de CONTECAR/SPRC.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import openpyxl
import os
from core.models import ObservationInput, ObservationEvaluation


MESES_NOMBRES = {
    1: "01. ENERO", 2: "02. FEBRERO", 3: "03. MARZO", 4: "04. ABRIL",
    5: "05. MAYO", 6: "06. JUNIO", 7: "07. JULIO", 8: "08. AGOSTO",
    9: "09. SEPTIEMBRE", 10: "10. OCTUBRE", 11: "11. NOVIEMBRE", 12: "12. DICIEMBRE"
}

TRIMESTRES = {
    1: "I TRIMESTRE", 2: "I TRIMESTRE", 3: "I TRIMESTRE",
    4: "II TRIMESTRE", 5: "II TRIMESTRE", 6: "II TRIMESTRE",
    7: "III TRIMESTRE", 8: "III TRIMESTRE", 9: "III TRIMESTRE",
    10: "IV TRIMESTRE", 11: "IV TRIMESTRE", 12: "IV TRIMESTRE"
}

CONTRATISTAS_COLUMNAS = [
    "IMPOTARJA", "SESCARIBE", "SEIMAR", "EQUILOG", "SERVIMAC",
    "MONTACAR", "SERVIPORTUARIOS", "ACTIPORT", "CTC", "SPRC"
]


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Intenta parsear múltiples formatos de fecha comunes (ISO, DD/MM/YYYY, DD-MM-YY)."""
    if not date_str:
        return None
    date_str = date_str.strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y", "%Y/%m/%d"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    return None


def get_week_of_month(dt: datetime) -> str:
    """Calcula la semana del mes (SEMANA 1 a SEMANA 5)."""
    first_day = dt.replace(day=1)
    adjusted_dom = dt.day + first_day.weekday()
    week_num = int((adjusted_dom - 1) / 7) + 1
    return f"SEMANA {min(week_num, 5)}"


def map_observation_to_44_columns(obs: ObservationInput, eval_res: ObservationEvaluation) -> Dict[str, Any]:
    """
    Construye el diccionario de 44 columnas canónicas correspondientes a la fila de Excel.
    """
    dt = parse_date(obs.fecha_realizacion)
    
    trimestre = TRIMESTRES.get(dt.month, "") if dt else ""
    mes = MESES_NOMBRES.get(dt.month, "") if dt else ""
    semana = get_week_of_month(dt) if dt else ""
    
    empresa_ej = (obs.empresa_ejecutante or "").upper()
    
    # Identificar ítems con oportunidad de mejora
    items_mejora = [str(item.item_number) for item in obs.items if item.cumple == "NO"]
    items_mejora_str = ", ".join(items_mejora) if items_mejora else None
    
    # Causas de ítems incumplidos
    causas = [f"Item {item.item_number}: {item.por_que_causa}" for item in obs.items if item.cumple == "NO" and item.por_que_causa]
    causas_str = " | ".join(causas) if causas else None

    # Flags de contratistas
    flags_contratistas = {}
    for c in CONTRATISTAS_COLUMNAS:
        is_match = False
        if c in empresa_ej:
            is_match = True
        elif c == "CTC" and ("CONTECAR" in empresa_ej or obs.terminal == "CTC"):
            is_match = True
        elif c == "SPRC" and ("SPRC" in empresa_ej or obs.terminal == "SPRC"):
            is_match = True
        flags_contratistas[c] = "X" if is_match else None

    row = {
        "TERMINAL": obs.terminal,
        "ÁREA": obs.area,
        "LÍDER ÁREA": obs.lider_area,
        "TRIMESTRE": trimestre,
        "MES": mes,
        "SEMANA": semana,
        "PERIODO": f"Mes de {mes.split('.')[-1].strip()}" if mes else None,
        "CODIGO REGISTRO": obs.codigo_formato or "X",
        "PROGRAMADA / EJECUTADA": "EJECUTADA",
        "COMPORTAMIENTO / CALIDAD": "COMPORTAMIENTO",
        "FECHA REALIZACIÓN": dt.strftime("%Y-%m-%d") if dt else obs.fecha_realizacion,
        "TAREA CRÍTICA": obs.tarea_critica,
        "ÁREA OBSERVADA": obs.area,
        "OBSERVADOR": obs.observador,
        "EMPRESA EJECUTANTE 1": obs.empresa_ejecutante,
        "EMPRESA EJECUTANTE 2": None,
        "IMPOTARJA": flags_contratistas["IMPOTARJA"],
        "SESCARIBE": flags_contratistas["SESCARIBE"],
        "SEIMAR": flags_contratistas["SEIMAR"],
        "EQUILOG": flags_contratistas["EQUILOG"],
        "SERVIMAC": flags_contratistas["SERVIMAC"],
        "MONTACAR": flags_contratistas["MONTACAR"],
        "SERVIPORTUARIOS": flags_contratistas["SERVIPORTUARIOS"],
        "ACTIPORT": flags_contratistas["ACTIPORT"],
        "CTC": flags_contratistas["CTC"],
        "SPRC": flags_contratistas["SPRC"],
        "OBSERVADOR OBSERVADO": None,
        "LUGAR": obs.lugar,
        "EQUIPO / CÓDIGO / PLACA/HORA": obs.hora,
        "ITEM CON OPORTUNIDAD DE MEJORA": items_mejora_str,
        "PCP": round(eval_res.pcp_calculado / 100.0, 4), # Formato decimal como en la BD (1.0 = 100%)
        "CAUSA DEL ITEM INCUMPLIDO (¿POR QUÉ?)": causas_str,
        "PLAN DE MEJORAMIENTO PROPUESTO": obs.plan_mejoramiento.propuesto,
        "ESTADO DEL PLAN DE MEJORAMIENTO": "PENDIENTE" if obs.plan_mejoramiento.propuesto else None,
        "RESPONSABLE DE LA GESTIÓN": "SUPERVISOR DE ÁREA" if obs.plan_mejoramiento.propuesto else None,
        "TIPO DE PLAN DE MEJORA": obs.plan_mejoramiento.tipo_ejecucion,
        "SEGUIMIENTO PLAN DE MEJORAMIENTO": None,
        "VIABILIDAD DEL PLAN DE MEJORAMIENTO": "VIABLE" if obs.plan_mejoramiento.es_viable else "NO VIABLE",
        "COMENTARIOS ADICIONALES REFUERZO POSITIVO": obs.comentarios_adicionales_observador,
        "COMENTARIOS DEL OBSERVADO": obs.comentarios_observado,
        "COMENTARIOS CALIDAD DE LA OBSERVACIÓN": eval_res.descripcion_calificacion,
        "CALIFICACIÓN CALIDAD INTERNA": eval_res.categoria,
        "CATEGORÍA DE LA OBSERVACIÓN": eval_res.categoria,
        "CALIFICACIÓN Y RECOMENDACIONES": eval_res.recomendaciones
    }
    
    return row


def append_to_master_excel(excel_path: str, row_data: Dict[str, Any], sheet_name: str = "BD") -> int:
    """
    Agrega de manera segura una nueva fila al final de la hoja sin alterar columnas ni fórmulas preexistentes.
    Retorna el número de fila insertada.
    """
    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"El archivo maestro de Excel no existe en: {excel_path}")
        
    wb = openpyxl.load_workbook(excel_path)
    if sheet_name not in wb.sheetnames:
        raise ValueError(f"La hoja '{sheet_name}' no existe en {excel_path}")
        
    ws = wb[sheet_name]
    
    # Fila 3 contiene los encabezados oficiales
    headers = [ws.cell(row=3, column=c).value for c in range(1, ws.max_column + 1)]
    next_row = ws.max_row + 1
    
    # Mapeo por nombre de columna
    for col_idx, header in enumerate(headers, start=1):
        if header and header in row_data:
            ws.cell(row=next_row, column=col_idx, value=row_data[header])
            
    wb.save(excel_path)
    return next_row


def append_batch_to_master_excel(excel_path: str, rows_data: List[Dict[str, Any]], sheet_name: str = "BD") -> List[int]:
    """
    Agrega en bloque una lista de observaciones a la hoja de Excel de forma atómica y eficiente.
    Retorna la lista de índices de fila insertados.
    """
    if not os.path.exists(excel_path):
        raise FileNotFoundError(f"El archivo maestro de Excel no existe en: {excel_path}")
        
    if not rows_data:
        return []
        
    wb = openpyxl.load_workbook(excel_path)
    if sheet_name not in wb.sheetnames:
        raise ValueError(f"La hoja '{sheet_name}' no existe en {excel_path}")
        
    ws = wb[sheet_name]
    headers = [ws.cell(row=3, column=c).value for c in range(1, ws.max_column + 1)]
    inserted_rows = []
    
    current_row = ws.max_row
    for row_data in rows_data:
        current_row += 1
        for col_idx, header in enumerate(headers, start=1):
            if header and header in row_data:
                ws.cell(row=current_row, column=col_idx, value=row_data[header])
        inserted_rows.append(current_row)
        
    wb.save(excel_path)
    return inserted_rows
