import sys
import os
import random
from datetime import datetime

# Añadir el directorio raíz al path para importar core
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.models import ObservationInput, BehaviorItem, ImprovementPlan
from core.scoring import evaluate_observation

def generar_items(porcentaje_esperado):
    items = []
    # Generamos 10 items
    for i in range(1, 11):
        if random.random() < (porcentaje_esperado / 100.0):
            items.append(BehaviorItem(item_number=i, cumple="SI"))
        else:
            # Si es NO, debemos poner por_que_causa para no caer en D automático por omisión
            items.append(BehaviorItem(item_number=i, cumple="NO", por_que_causa="Se observó desviación en el estándar"))
    # Asegurar que al menos haya un SI para que pcp no sea 0 si no queremos
    if not items:
         items.append(BehaviorItem(item_number=1, cumple="SI"))
    return items

def simular_100_casos():
    resultados = {"A+": 0, "A": 0, "B+": 0, "B": 0, "R+": 0, "R": 0, "C+": 0, "C": 0, "D": 0}
    
    frases_evasivas = ["ninguna", "sin comentarios", "no aplica", "no hay", "nada", "n/a"]
    frases_validas = [
        "Capacitar al personal en trabajo en alturas",
        "Instalar barandas protectoras en la zona norte",
        "Cambiar arnés por desgaste",
        "Realizar charla de 5 minutos sobre riesgo eléctrico"
    ]
    
    comentarios_observados_validos = ["Me sentí bien", "Entiendo el riesgo", "Excelente charla"]
    
    casos_creados = 0
    
    for i in range(100):
        # 1. Metadatos (Ocasionalmente fallan para forzar categoría D de incompletitud)
        terminal = random.choice(["CTC", "SPRC"]) if random.random() > 0.05 else None
        fecha = "2026-10-01" if random.random() > 0.05 else None
        
        # 2. Rendimiento PCP
        # 70% de las veces PCP perfecto, 30% PCP con fallas
        es_perfecto = random.random() > 0.3
        items = generar_items(100 if es_perfecto else random.choice([50, 70, 80, 90]))
        
        # 3. Plan de mejoramiento
        tipo_plan = random.choice(["evasivo", "valido_basico", "valido_alto_impacto", "nulo"])
        
        plan = ImprovementPlan()
        if tipo_plan == "evasivo":
            plan.propuesto = random.choice(frases_evasivas)
        elif tipo_plan == "nulo":
            plan.propuesto = None
        else:
            plan.propuesto = random.choice(frases_validas)
            plan.es_viable = True
            if tipo_plan == "valido_alto_impacto":
                plan.alto_impacto = True
                plan.evidencia_fotografica_detectada = random.choice([True, False])
                plan.analisis_seguridad_anexo = random.choice([True, False])
            else:
                plan.enfoque_sst = random.choice([True, False])
                plan.evidencia_fotografica_detectada = random.choice([True, False])
        
        # 4. Comentarios observado
        comentario_obs = random.choice(comentarios_observados_validos) if random.random() > 0.1 else random.choice(["", "sin comentarios"])
        
        obs = ObservationInput(
            terminal=terminal,
            fecha_realizacion=fecha,
            hora="10:00",
            observador="Auditor Prueba",
            empresa_ejecutante="Empresa XYZ",
            items=items,
            plan_mejoramiento=plan,
            comentarios_observado=comentario_obs
        )
        
        # Evaluar
        evaluacion = evaluate_observation(obs)
        resultados[evaluacion.categoria] += 1
        
        # Si era evasivo con PCP 100, verificar que no sea A ni B
        if tipo_plan == "evasivo" and evaluacion.pcp_calculado == 100.0:
            if evaluacion.categoria not in ["C", "C+", "D"]:
                 print(f"ALERTA: Plan evasivo logró categoría alta: {evaluacion.categoria}")

    print("=== RESULTADOS DE LA SIMULACIÓN DE 100 OBSERVACIONES ===")
    print("Distribución de Categorías Asignadas por el Motor (SURA/CONTECAR):")
    for cat, count in resultados.items():
        print(f"Categoría {cat}: {count} casos")
        
    print("\nDetalle Técnico:")
    print("- Total simulados: 100")
    print("- La base de datos (Supabase/Excel) NO fue tocada.")

if __name__ == "__main__":
    simular_100_casos()
