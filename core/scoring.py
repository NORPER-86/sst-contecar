"""
Motor de Reglas y Clasificación de Calidad SST (CONTECAR / SPRC).
Implementa estrictamente los criterios de evaluación de CRITERIOS PARA CALIFICACIÓN.docx
y las directrices operativas de Kellys Escorcia.
"""

from typing import List, Tuple, Optional
from core.models import BehaviorItem, ObservationInput, ObservationEvaluation, ImprovementPlan


def calculate_pcp(items: List[BehaviorItem]) -> Tuple[int, int, int, int, float]:
    """
    Calcula las estadísticas y el Porcentaje de Comportamiento Positivo (%PCP).
    Fórmula: (Total Cumple 'SI' / (Total Cumple 'SI' + Total No Cumple 'NO')) * 100
    Retorna: (total_si, total_no, total_na, total_aplicables, pcp_percent)
    """
    si = sum(1 for item in items if item.cumple == "SI")
    no = sum(1 for item in items if item.cumple == "NO")
    na = sum(1 for item in items if item.cumple == "N/A")
    aplicables = si + no
    
    if aplicables == 0:
        pcp = 100.0
    else:
        pcp = round((si / aplicables) * 100.0, 2)
        
    return si, no, na, aplicables, pcp


def evaluate_observation(obs: ObservationInput) -> ObservationEvaluation:
    """
    Evalúa integralmente la observación, asignando la categoría oficial (D, C, C+, R, R+, B, B+, A, A+)
    y generando la descripción y recomendación correspondiente.
    """
    si, no, na, aplicables, pcp = calculate_pcp(obs.items)
    
    # 1. Verificación de discrepancia matemática en PCP manuscrito
    discrepancia = False
    if obs.pcp_manuscrito is not None:
        # Algunos escriben 1.0 (para 100%) o 100
        manuscrito = obs.pcp_manuscrito
        if manuscrito <= 1.0 and pcp > 1.0:
            manuscrito = manuscrito * 100.0
        if abs(pcp - manuscrito) > 1.0:
            discrepancia = True

    # 2. Verificación de Completitud (Reglas de Categoría D)
    motivos_d = []
    
    # Metadatos obligatorios
    if not obs.terminal:
        motivos_d.append("Terminal portuaria (CTC o SPRC) no seleccionada")
    if not obs.fecha_realizacion or not obs.fecha_realizacion.strip():
        motivos_d.append("Fecha de realización no diligenciada")
    if not obs.hora or not obs.hora.strip():
        motivos_d.append("Hora de la observación no registrada")
    if not obs.observador or not obs.observador.strip():
        motivos_d.append("Nombre del observador no registrado")
    if not obs.empresa_ejecutante or not obs.empresa_ejecutante.strip():
        motivos_d.append("Datos de la empresa ejecutante no registrados")
        
    # Justificación de comportamientos NO cumplidos
    for item in obs.items:
        if item.cumple == "NO" and (not item.por_que_causa or not item.por_que_causa.strip()):
            motivos_d.append(f"El ítem {item.item_number} está marcado como 'NO' y no tiene diligenciada la columna de los ¿Por qué?")
            
    # Verificación de Plan de Mejoramiento real (No evasivas)
    plan = obs.plan_mejoramiento
    propuesto_texto = (plan.propuesto or "").strip().lower()
    
    es_plan_evasivo = False
    if len(propuesto_texto) < 4:
        es_plan_evasivo = True
    else:
        evasivas = [
            "ninguna", "ninguno", "n/a", "na", "sin comentario", "sin recomendacion", 
            "no hay", "no se ", "no aplica", "no existen", "nada", "sin novedad"
        ]
        # Si empieza con alguna frase evasiva típica y es corto
        if len(propuesto_texto) < 50 and any(propuesto_texto.startswith(e) for e in evasivas):
            es_plan_evasivo = True
            
    tiene_plan = not es_plan_evasivo
    
    # PCP < 100% exige plan de mejoramiento
    if pcp < 100.0 and not tiene_plan:
        motivos_d.append("El PCP es menor al 100% y no se diligenció un Plan de mejora válido")
        
    # Comentarios del observado obligatorios
    comentarios_obs = (obs.comentarios_observado or "").strip()
    if not comentarios_obs:
        motivos_d.append("No se diligenció el campo de 'Comentarios del observado'")
        
    # Si incurre en causales de D:
    if motivos_d:
        return ObservationEvaluation(
            total_cumplidos=si,
            total_no_cumplidos=no,
            total_no_aplica=na,
            total_aplicables=aplicables,
            pcp_calculado=pcp,
            discrepancia_pcp=discrepancia,
            categoria="D",
            descripcion_calificacion="El formato de observación presenta campos sin diligenciar.",
            recomendaciones="Se solicita completar la totalidad de la información requerida y remitir nuevamente la observación para su revisión y registro correspondientes.",
            requiere_subsanacion=True,
            motivo_subsanacion="; ".join(motivos_d)
        )
        
    # 3. Categorías C y C+ (Sin Plan de Mejora)
    normalizado_comentario = comentarios_obs.lower()
    es_sin_comentarios = (
        normalizado_comentario in ["sin comentarios", "sin comentario", "ninguno", "n/a", "no tiene", "s/c"]
        or len(normalizado_comentario) < 4
    )
    
    if not tiene_plan:
        if es_sin_comentarios:
            # Categoría C
            return ObservationEvaluation(
                total_cumplidos=si,
                total_no_cumplidos=no,
                total_no_aplica=na,
                total_aplicables=aplicables,
                pcp_calculado=pcp,
                discrepancia_pcp=discrepancia,
                categoria="C",
                descripcion_calificacion="Diligenciamiento adecuado del formato.",
                recomendaciones="Para fortalecer la calidad de la observación y mejorar su calificación, se recomienda formular planes de mejora concretos y específicos, acompañados de evidencia fotográfica de la acción o mejora a implementar. Adicionalmente, es importante registrar en el campo de comentarios del observado: cómo se sintió durante la observación, así como aprovechar el espacio para dar a conocer y reforzar los objetivos y beneficios del proceso ComPORTate."
            )
        else:
            # Categoría C+
            return ObservationEvaluation(
                total_cumplidos=si,
                total_no_cumplidos=no,
                total_no_aplica=na,
                total_aplicables=aplicables,
                pcp_calculado=pcp,
                discrepancia_pcp=discrepancia,
                categoria="C+",
                descripcion_calificacion="Diligenciamiento adecuado del formato. Comentario del observado bien redactado.",
                recomendaciones="Para mejorar su calificación en próximas observaciones identifique un plan de mejora concreto enfocado en la prevención de accidentes, anexe fotos de la condición o mejora a implementar."
            )

    # 4. Categorías con Plan de Mejora Formulada (R, R+, B, B+, A, A+)
    if plan.es_recomendacion:
        if not plan.es_viable:
            # Categoría R
            return ObservationEvaluation(
                total_cumplidos=si,
                total_no_cumplidos=no,
                total_no_aplica=na,
                total_aplicables=aplicables,
                pcp_calculado=pcp,
                discrepancia_pcp=discrepancia,
                categoria="R",
                descripcion_calificacion="Diligenciamiento adecuado del formato. Comentario del observado bien redactado. Se identifica recomendación, será enviada a encargado de gestión para validación.",
                recomendaciones="Para mejorar su calificación en próximas observaciones identifique un plan de mejora concreto enfocado en la prevención de accidentes, anexe fotos de la condición o mejora a implementar."
            )
        else:
            # Categoría R+
            return ObservationEvaluation(
                total_cumplidos=si,
                total_no_cumplidos=no,
                total_no_aplica=na,
                total_aplicables=aplicables,
                pcp_calculado=pcp,
                discrepancia_pcp=discrepancia,
                categoria="R+",
                descripcion_calificacion="Diligenciamiento adecuado del formato. Comentario del observado bien redactado. Se identifica recomendación viable, será enviada a encargado de gestión para validación.",
                recomendaciones="Para mejorar su calificación en próximas observaciones identifique un plan de mejora concreto enfocado en la prevención de accidentes, anexe fotos de la condición o mejora a implementar."
            )
            
    # Plan de mejora estructurado
    # A+ : Alto impacto + análisis de condiciones/seguridad anexo
    if plan.alto_impacto and plan.analisis_seguridad_anexo:
        return ObservationEvaluation(
            total_cumplidos=si,
            total_no_cumplidos=no,
            total_no_aplica=na,
            total_aplicables=aplicables,
            pcp_calculado=pcp,
            discrepancia_pcp=discrepancia,
            categoria="A+",
            descripcion_calificacion="Diligenciamiento adecuado del formato. Comentario del observado bien redactado. Se identifica plan de mejora concreto enfocado en la prevención de accidentes de alto impacto con análisis causal, será enviado a encargado de gestión para validación.",
            recomendaciones="Gracias por las fotos y anexos enviados, ayudan a gestionar con más efectividad las condiciones reportadas."
        )

    # A : Alto impacto con evidencia
    if plan.alto_impacto and plan.evidencia_fotografica_detectada:
        return ObservationEvaluation(
            total_cumplidos=si,
            total_no_cumplidos=no,
            total_no_aplica=na,
            total_aplicables=aplicables,
            pcp_calculado=pcp,
            discrepancia_pcp=discrepancia,
            categoria="A",
            descripcion_calificacion="Diligenciamiento adecuado del formato. Comentario del observado bien redactado. Se identifica plan de mejora concreto enfocado en la prevención de accidentes con alto impacto en la accidentalidad, será enviado a encargado de gestión para validación.",
            recomendaciones="Gracias por las fotos y anexos enviados, ayudan a gestionar con más efectividad las condiciones reportadas."
        )

    # B+ : Plan específico enfocado en SST con fotos/anexos
    if (plan.enfoque_sst or plan.evidencia_fotografica_detectada):
        return ObservationEvaluation(
            total_cumplidos=si,
            total_no_cumplidos=no,
            total_no_aplica=na,
            total_aplicables=aplicables,
            pcp_calculado=pcp,
            discrepancia_pcp=discrepancia,
            categoria="B+",
            descripcion_calificacion="Diligenciamiento adecuado del formato. Comentario del observado bien redactado. Se identifica plan de mejora concreto enfocado en la prevención de accidentes, será enviado a encargado de gestión para validación.",
            recomendaciones="Gracias por las fotos y anexos enviados, ayudan a gestionar con más efectividad las condiciones reportadas."
        )

    # B : Plan de mejora específico y aplicable estándar (Directriz Kellys Audio 3)
    return ObservationEvaluation(
        total_cumplidos=si,
        total_no_cumplidos=no,
        total_no_aplica=na,
        total_aplicables=aplicables,
        pcp_calculado=pcp,
        discrepancia_pcp=discrepancia,
        categoria="B",
        descripcion_calificacion="Diligenciamiento adecuado del formato. Comentario del observado bien redactado. Se identifica plan de mejora, será enviado a encargado de gestión para validación.",
        recomendaciones="Para mejorar su calificación en próximas observaciones identifique un plan de mejora concreto enfocado en la prevención de accidentes, anexe fotos de la condición o mejora a implementar."
    )
