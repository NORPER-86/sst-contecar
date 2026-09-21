"""
Modelos de Datos y Esquemas Formales (Spec-Driven Development)
para el Sistema de Observación de Comportamientos SST (CONTECAR / SPRC).
"""

from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field
from datetime import date, time, datetime


class BehaviorItem(BaseModel):
    """Evaluación de un comportamiento crítico específico."""
    item_number: int = Field(..., description="Número del ítem en la lista de chequeo")
    descripcion: Optional[str] = Field(None, description="Descripción del comportamiento crítico evaluado")
    cumple: Literal["SI", "NO", "N/A"] = Field(..., description="Estado de cumplimiento observado")
    por_que_causa: Optional[str] = Field(
        None, 
        description="Justificación obligatoria si cumple == 'NO'. Causa del comportamiento no cumplido."
    )


class ImprovementPlan(BaseModel):
    """Plan de mejoramiento propuesto o sugerido."""
    propuesto: Optional[str] = Field(None, description="Descripción del plan de mejoramiento formulado")
    tipo_ejecucion: Optional[Literal["Fácil", "Difícil", "Proyecto Especial"]] = Field(
        None, description="Grado de dificultad o nivel de gestión requerido"
    )
    es_recomendacion: bool = Field(False, description="Indica si el plan tiene carácter de recomendación")
    es_viable: bool = Field(True, description="Viabilidad técnica u operativa del plan propuesto")
    enfoque_sst: bool = Field(False, description="Enfocado directamente en prevención de accidentes y SST")
    alto_impacto: bool = Field(False, description="Alto impacto preventivo en accidentalidad portuaria")
    evidencia_fotografica_detectada: bool = Field(
        False, description="Presencia de fotografías o anexos gráficos en el PDF"
    )
    analisis_seguridad_anexo: bool = Field(
        False, description="Presencia de matriz de riesgo, DOFA o análisis causal de condiciones"
    )


class ObservationInput(BaseModel):
    """Contrato de entrada para una observación de tarea crítica escaneada."""
    codigo_formato: Optional[str] = Field(
        None, description="Código oficial del formato (ej. HS-FMT305, HS-FMT316)"
    )
    terminal: Optional[Literal["CTC", "SPRC"]] = Field(
        None, description="Terminal portuaria donde se realizó la observación (CTC = Contecar)"
    )
    fecha_realizacion: Optional[str] = Field(
        None, description="Fecha de realización en formato YYYY-MM-DD o DD/MM/YYYY"
    )
    hora: Optional[str] = Field(None, description="Hora de realización (ej. '14:20')")
    lugar: Optional[str] = Field(None, description="Ubicación física en el puerto (ej. 'Plataforma rife 5A')")
    tarea_critica: Optional[str] = Field(
        None, description="Nombre de la tarea crítica (ej. 'Mantenimiento de instalaciones eléctricas')"
    )
    area: Optional[str] = Field(
        "OPERACIONES", description="Área operativa (ej. AFOROS, BODEGAS, MANTENIMIENTO, MUELLE)"
    )
    lider_area: Optional[str] = Field(None, description="Líder del área asignada")
    observador: Optional[str] = Field(None, description="Nombre completo del observador")
    supervisor_sst: Optional[str] = Field(None, description="Nombre del supervisor o auxiliar SST")
    empresa_ejecutante: Optional[str] = Field(
        None, description="Empresa a la que pertenece el personal observado (CTC, SPRC o contratista)"
    )
    
    # Comportamientos
    items: List[BehaviorItem] = Field(default_factory=list, description="Lista de comportamientos evaluados")
    pcp_manuscrito: Optional[float] = Field(
        None, description="Valor del %PCP escrito a mano en el formato si fue diligenciado"
    )
    
    # Planes y Comentarios
    plan_mejoramiento: ImprovementPlan = Field(default_factory=ImprovementPlan)
    comentarios_observado: Optional[str] = Field(
        None, description="Comentarios del observado: ¿Cómo se sintió? / Riesgos adicionales"
    )
    comentarios_adicionales_observador: Optional[str] = Field(
        None, description="Comentarios adicionales del observador / Refuerzo positivo"
    )


class ObservationEvaluation(BaseModel):
    """Resultado de evaluación formal según la matriz de calidad de CONTECAR/SPRC."""
    total_cumplidos: int
    total_no_cumplidos: int
    total_no_aplica: int
    total_aplicables: int
    pcp_calculado: float
    discrepancia_pcp: bool = False
    
    categoria: Literal["D", "C", "C+", "R", "R+", "B", "B+", "A", "A+"]
    descripcion_calificacion: str
    recomendaciones: str
    requiere_subsanacion: bool = False
    motivo_subsanacion: Optional[str] = None
    
    # Mapeo a las 44 columnas
    fila_excel_44: Dict[str, Any] = Field(default_factory=dict)
