"""
Plataforma Integral de Observación de Comportamientos SST (CONTECAR - SPRC).
Diseño Corporativo Oficial basado en el Manual de Marca de SURA y CONTECAR.
Desarrollada bajo metodología Spec-Driven Development (OpenSpec).
Soporta procesamiento por lotes de carpetas completas de PDFs escaneados con OCR multimodal.
"""

from __future__ import annotations

import os
import io
import glob
import re
import pandas as pd
import openpyxl
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from dotenv import load_dotenv

# Modelos y lógica central
from core.models import ObservationInput, BehaviorItem, ImprovementPlan, ObservationEvaluation, AREAS_OPERATIVAS
from core.scoring import evaluate_observation, calculate_pcp
from core.excel_sync import map_observation_to_44_columns, append_to_master_excel, append_batch_to_master_excel
from core.extractor import (
    render_pdf_to_images, extract_observation_from_file, process_document,
    scan_directory_for_pdfs, process_batch
)
from core.branding import (
    get_custom_css, get_header_html, get_sidebar_brand_html,
    SURA_BLUE, SURA_CYAN, SURA_YELLOW, SURA_NAVY_DARK, SURA_TEXT_MUTED,
    CATEGORY_PALETTE
)

# Carga de variables de entorno y secretos (2 de Google Gemini + 1 de DeepSeek)
load_dotenv()
GEMINI_KEYS = []
if os.environ.get("GEMINI_API_KEY"):
    GEMINI_KEYS.append(os.environ.get("GEMINI_API_KEY"))
if os.environ.get("GEMINI_API_KEY_2") and os.environ.get("GEMINI_API_KEY_2") not in GEMINI_KEYS:
    GEMINI_KEYS.append(os.environ.get("GEMINI_API_KEY_2"))

try:
    if hasattr(st, "secrets"):
        if "GEMINI_API_KEY" in st.secrets and st.secrets["GEMINI_API_KEY"] not in GEMINI_KEYS:
            GEMINI_KEYS.append(st.secrets["GEMINI_API_KEY"])
        if "GEMINI_API_KEY_2" in st.secrets and st.secrets["GEMINI_API_KEY_2"] not in GEMINI_KEYS:
            GEMINI_KEYS.append(st.secrets["GEMINI_API_KEY_2"])
except Exception:
    pass

GEMINI_KEY = GEMINI_KEYS[0] if GEMINI_KEYS else None
GEMINI_KEY_STRING = ",".join(GEMINI_KEYS) if GEMINI_KEYS else None

DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY")
try:
    if hasattr(st, "secrets") and "DEEPSEEK_API_KEY" in st.secrets:
        DEEPSEEK_KEY = DEEPSEEK_KEY or st.secrets["DEEPSEEK_API_KEY"]
except Exception:
    pass

if GEMINI_KEY:
    os.environ["GEMINI_API_KEY"] = GEMINI_KEY

# Configuración de página Streamlit
st.set_page_config(
    page_title="SST ComPORTate - SURA & CONTECAR",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Inyección de estilos oficiales según Manual de Marca SURA
st.markdown(get_custom_css(), unsafe_allow_html=True)

MASTER_EXCEL_PATH = os.path.join("DOCUMENTOS DE BASE", "Ejemplos observaciones digitadas.xlsx")

@st.cache_data(ttl=60)
def load_historical_data(excel_path: str) -> pd.DataFrame:
    """Carga la base de datos histórica con las 44 columnas desde Excel."""
    if not os.path.exists(excel_path):
        return pd.DataFrame()
    df = pd.read_excel(excel_path, sheet_name="BD", skiprows=2)
    df = df.dropna(how="all")
    return df

df_master = load_historical_data(MASTER_EXCEL_PATH)

# Barra Lateral con Manual de Marca SURA
with st.sidebar:
    st.markdown(get_sidebar_brand_html(), unsafe_allow_html=True)
    st.markdown("---")
    
    st.markdown("#### 🎯 **Motor de Inteligencia Artificial**")
    if GEMINI_KEYS:
        num_keys = len(GEMINI_KEYS)
        key_label = f"({num_keys} API {'Key' if num_keys == 1 else 'Keys - Rotación'})"
        st.markdown(f"""
        <div style='background:#EFF6FF; padding:12px; border-radius:8px; border-left:4px solid {SURA_BLUE}; margin-bottom:8px;'>
            <div style='font-size:12px; font-weight:700; color:{SURA_NAVY_DARK};'>Google Gemini Vision:</div>
            <div style='font-size:11px; color:#059669; font-weight:700;'>● Conectado {key_label}</div>
            <div style='font-size:10px; color:{SURA_TEXT_MUTED}; margin-top:2px;'>OCR Manuscrito & Layout</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Modo de extracción local activo.")

    if DEEPSEEK_KEY:
        st.markdown(f"""
        <div style='background:#F5F3FF; padding:12px; border-radius:8px; border-left:4px solid #7C3AED; margin-bottom:8px;'>
            <div style='font-size:12px; font-weight:700; color:#4C1D95;'>DeepSeek V3 / R1:</div>
            <div style='font-size:11px; color:#7C3AED; font-weight:700;'>● Respaldo Semántico Activo</div>
            <div style='font-size:10px; color:{SURA_TEXT_MUTED}; margin-top:2px;'>Auditoría & Razonamiento SST</div>
        </div>
        """, unsafe_allow_html=True)
        
    st.markdown("---")
    st.markdown("#### ⚓ **Terminales del Puerto**")
    st.caption("• **CONTECAR** (CTC)\n• **SPRC** (Sociedad Portuaria Regional de Cartagena)")
    
    st.markdown("---")
    st.markdown("#### 🛡️ **Gobernanza y Calidad**")
    st.markdown(f"""
    <div style='background:#F1F5F9; padding:10px; border-radius:8px; border-left:4px solid {SURA_BLUE};'>
        <div style='font-size:12px; font-weight:700; color:{SURA_NAVY_DARK};'>Living Spec Activa:</div>
        <div style='font-size:11px; color:{SURA_TEXT_MUTED};'>openspec/specs/observation-engine</div>
        <div style='font-size:12px; font-weight:700; color:{SURA_CYAN}; margin-top:4px;'>Estatus: 100% Validado</div>
    </div>
    """, unsafe_allow_html=True)
    
    if not df_master.empty:
        st.caption(f"📁 Registros en base histórica: **{len(df_master):,}**")

# Banner Corporativo Superior con Logos de SURA y CONTECAR
st.markdown(get_header_html(), unsafe_allow_html=True)

# Pestañas de Navegación Estilizadas
tab_ingesta, tab_dashboard, tab_datos, tab_criterios = st.tabs([
    "📋 Ingesta & Escaneo de Carpeta (Human-in-the-Loop)",
    "📊 Tablero Analítico Gerencial (BI)",
    "🗄️ Base de Datos Maestra (44 Columnas)",
    "📖 Manual de Calificación & Normativa Portuaria"
])

# ==========================================================
# TAB 1: INGESTA POR CARPETA / ARCHIVO & COTEJO
# ==========================================================
with tab_ingesta:
    st.markdown("### 📥 Ingesta Masiva de Documentos Escaneados")
    st.caption("Carga una carpeta completa con todos los PDFs escaneados o arrastra múltiples archivos para extracción OCR simultánea.")
    
    # Selector de Modo de Ingesta
    modo_ingesta = st.radio(
        "Modo de Carga de Escaneos:",
        ["🗂️ Arrastrar Múltiples Archivos (Drag & Drop)", "🔍 Seleccionar Archivo Individual (Muestras)"],
        horizontal=True
    )
    
    archivos_a_procesar = []
    
    if modo_ingesta == "🗂️ Arrastrar Múltiples Archivos (Drag & Drop)":
        archivos_subidos = st.file_uploader(
            "Arrastra aquí todos los PDFs escaneados:",
            type=["pdf"],
            accept_multiple_files=True
        )
        if archivos_subidos:
            os.makedirs("scratch", exist_ok=True)
            rutas = []
            for up_file in archivos_subidos:
                # Sanitización estricta contra Path Traversal (CWE-22)
                base_name = os.path.basename(up_file.name)
                safe_name = re.sub(r"[^\w\-.]", "_", base_name)
                if not safe_name.lower().endswith(".pdf"):
                    safe_name += ".pdf"
                save_p = os.path.join("scratch", safe_name)
                with open(save_p, "wb") as f:
                    f.write(up_file.getbuffer())
                rutas.append(save_p)
            archivos_a_procesar = rutas
            st.info(f"Se cargaron **{len(archivos_a_procesar)}** archivos para procesar.")

    else:
        # Selección individual
        ejemplos_disponibles = {
            "MAN DE INS ELE AGOSTO SEM 3.pdf": "Mantenimiento Eléctrico (Contecar)",
            "Observación compórtate 11-09-2026.pdf": "Entrada y Salida Vehicular (SPRC)",
            "CamScanner 22-08-26 13.02.pdf": "Plataforma de Aforos (Sescaribe)",
            "Scan_0008 2.pdf": "Contenedores Refrigerados (Impotarja)"
        }
        ejemplo_sel = st.selectbox(
            "Seleccionar formato de muestra:",
            options=list(ejemplos_disponibles.keys()),
            format_func=lambda x: f"{x} — {ejemplos_disponibles.get(x, '')}"
        )
        found = glob.glob(os.path.join("DOCUMENTOS DE BASE", f"*{ejemplo_sel}*"))
        if found:
            archivos_a_procesar = [found[0]]

    # Configuración de Área Operativa y Botón de Procesamiento
    st.markdown("---")
    if archivos_a_procesar:
        c_ar_b1, c_ar_b2 = st.columns([1, 1])
        opciones_lote = ["🤖 Detección Automática por IA (según cada formato)"] + AREAS_OPERATIVAS
        sel_area_lote = c_ar_b1.selectbox(
            "🏢 Área que Realiza la Actividad:",
            opciones_lote,
            index=0,
            help="Selecciona el área para estos archivos, o déjalo en Detección Automática para que la IA la asigne."
        )
        if sel_area_lote == "Otros":
            custom_area_lote = c_ar_b2.text_input(
                "✏️ Especifique Área Adicional:",
                placeholder="Escribe el nombre del área...",
                key="batch_custom_area"
            )
            area_lote_final = custom_area_lote.strip() if custom_area_lote.strip() else "Otros"
        elif "Automática" in sel_area_lote:
            area_lote_final = None
            c_ar_b2.caption("ℹ️ La IA identificará y asignará el área de cada formato.")
        else:
            area_lote_final = sel_area_lote
            c_ar_b2.caption(f"Área asignada al lote: **{area_lote_final}**")

        btn_col, _ = st.columns([2, 3])
        texto_btn = f"🚀 Procesar Lote Completo ({len(archivos_a_procesar)} archivos con OCR)" if len(archivos_a_procesar) > 1 else "⚡ Extraer y Evaluar Observación"
        if btn_col.button(texto_btn, type="primary", use_container_width=True):
            progress_bar = st.progress(0.0)
            status_text = st.empty()
            
            def on_progress(current, total, fname):
                progress_bar.progress(current / total)
                status_text.caption(f"Procesando ({current}/{total}): `{fname}`...")
                
            resultados_lote = process_batch(archivos_a_procesar, api_key=GEMINI_KEY_STRING, progress_callback=on_progress)
            
            if area_lote_final:
                for r in resultados_lote:
                    if r.get("obs_input"):
                        r["obs_input"].area = area_lote_final
                        
            st.session_state["lote_results"] = resultados_lote
            progress_bar.progress(1.0)
            status_text.empty()
            st.success(f"🎉 ¡Procesamiento completado para {len(resultados_lote)} documentos!")

    # Renderizado de Resultados del Lote
    if "lote_results" in st.session_state and st.session_state["lote_results"]:
        lote: list = st.session_state["lote_results"]
        
        st.markdown("#### 📊 Resumen de Resultados del Lote")
        
        # Tarjetas de resumen del lote
        rl1, rl2, rl3, rl4 = st.columns(4)
        total_lote = len(lote)
        exitosos = sum(1 for r in lote if r["status"] == "SUCCESS")
        
        pcps = [r["eval_res"].pcp_calculado for r in lote if r.get("eval_res")]
        promedio_lote_pcp = sum(pcps) / max(1, len(pcps))
        
        cats_lote = [r["eval_res"].categoria for r in lote if r.get("eval_res")]
        cat_d_lote = cats_lote.count("D")
        
        rl1.metric("📁 Archivos Procesados", f"{total_lote}")
        rl2.metric("% PCP Promedio Lote", f"{promedio_lote_pcp:.1f}%")
        rl3.metric("✅ Procesados Exitosos", f"{exitosos}/{total_lote}")
        rl4.metric("⚠️ Con Observaciones D", f"{cat_d_lote}", delta_color="inverse")
        
        # Tabla resumen del lote
        tabla_rows = []
        for r in lote:
            fname = r["file_name"]
            if r["status"] == "SUCCESS":
                ev = r["eval_res"]
                obs = r["obs_input"]
                tabla_rows.append({
                    "Archivo": fname,
                    "Área": obs.area or "N/A",
                    "Tarea Crítica": obs.tarea_critica,
                    "Terminal": obs.terminal,
                    "Observador": obs.observador,
                    "Empresa": obs.empresa_ejecutante,
                    "% PCP": f"{ev.pcp_calculado}%",
                    "Categoría": ev.categoria,
                    "Estado": "Listo para Persistir" if not ev.requiere_subsanacion else "Subsanar (Cat D)"
                })
            else:
                tabla_rows.append({
                    "Archivo": fname,
                    "Área": "N/A",
                    "Tarea Crítica": "Error",
                    "Terminal": "N/A",
                    "Observador": "N/A",
                    "Empresa": "N/A",
                    "% PCP": "0%",
                    "Categoría": "ERROR",
                    "Estado": r.get("error", "Falla")
                })
                
        df_lote_view = pd.DataFrame(tabla_rows)
        st.dataframe(df_lote_view, use_container_width=True)
        
        # Botón de guardado masivo (Doble Persistencia: Excel + Supabase)
        c_save_all, c_clear = st.columns([2, 1])
        if c_save_all.button("💾 Sincronizar Todo el Lote (Excel Maestro + Supabase)", type="primary", use_container_width=True):
            filas_a_guardar = [r["row_44"] for r in lote if r["status"] == "SUCCESS" and r.get("row_44")]
            try:
                # 1. Guardar en Excel Maestro (44 columnas)
                filas_insertadas = append_batch_to_master_excel(MASTER_EXCEL_PATH, filas_a_guardar)
                
                # 2. Guardar en Supabase (JSON estructurado)
                from core.supabase_sync import insert_batch_to_supabase
                supa_status = insert_batch_to_supabase(lote)
                
                if supa_status:
                    st.success(f"🎉 ¡Doble sincronización exitosa! **{len(filas_insertadas)}** observaciones guardadas en Excel (`{MASTER_EXCEL_PATH}`) y en la nube (Supabase).")
                else:
                    st.warning(f"⚠️ Guardado en Excel exitoso ({len(filas_insertadas)} filas), pero falló la sincronización con Supabase (verifica credenciales en .env).")
                    
                st.cache_data.clear()
            except Exception as e:
                st.error(f"Error durante la sincronización: {e}")
                
        st.markdown("---")
        st.markdown("#### 🔎 Inspección Detallada (Split-View)")
        
        # Selector de archivo para ver en Split View
        archivo_sel = st.selectbox(
            "Selecciona un archivo del lote para cotejo visual:",
            options=[r["file_name"] for r in lote]
        )
        
        # Buscar el resultado seleccionado
        sel_res = next((r for r in lote if r["file_name"] == archivo_sel), None)
        
        if sel_res and sel_res["status"] == "SUCCESS":
            obs_input = sel_res["obs_input"]
            eval_res = sel_res["eval_res"]
            path_sel = sel_res["file_path"]
            
            col_pdf, col_form = st.columns([1, 1], gap="large")
            
            # --- PANEL IZQUIERDO: DOCUMENTO ESCANEADO ---
            with col_pdf:
                st.markdown("##### 📄 Documento Escaneado")
                try:
                    if path_sel.lower().endswith(".pdf"):
                        images = render_pdf_to_images(path_sel, dpi=150)
                        page_idx = st.radio("Página:", range(1, len(images) + 1), horizontal=True, key=f"p_{archivo_sel}")
                        st.image(
                            images[page_idx - 1], 
                            use_container_width=True, 
                            caption=f"Página {page_idx} de {len(images)} — {archivo_sel}"
                        )
                    else:
                        st.image(path_sel, use_container_width=True)
                except Exception as e:
                    st.warning(f"No se pudo visualizar el escaneo: {e}")
                    
            # --- PANEL DERECHO: FORMULARIO COTEJO ---
            with col_form:
                st.markdown("##### ✍️ Cotejo y Validación Humana")
                
                cat_info = CATEGORY_PALETTE.get(eval_res.categoria, {"color": SURA_BLUE, "bg": "#EFF6FF", "label": eval_res.categoria})
                
                st.markdown(f"""
                <div class="split-view-banner">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                        <div>
                            <span style="font-size: 13px; font-weight: 600; color: {SURA_TEXT_MUTED}; text-transform: uppercase;">Calificación Asignada:</span>
                            <div style="margin-top: 4px;">
                                <span class="sura-badge" style="background-color: {cat_info['bg']}; color: {cat_info['color']}; border: 1.5px solid {cat_info['color']};">
                                    ● {cat_info['label']}
                                </span>
                            </div>
                        </div>
                        <div style="text-align: right;">
                            <div style="font-size: 12px; font-weight: 600; color: {SURA_TEXT_MUTED};">CUMPLIMIENTO PCP</div>
                            <div style="font-size: 26px; font-weight: 800; color: {SURA_BLUE};">
                                {eval_res.pcp_calculado}%
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                if eval_res.requiere_subsanacion:
                    st.error(f"⚠️ **Incompleto**: {eval_res.motivo_subsanacion}")
                else:
                    st.info(f"💡 **Recomendación**: {eval_res.recomendaciones}")
                    
                with st.expander("📝 Metadatos Extraídos (Editables)", expanded=True):
                    c1, c2, c3 = st.columns(3)
                    val_term = c1.selectbox("Terminal", ["CTC", "SPRC"], index=0 if obs_input.terminal == "CTC" else 1, key=f"t_{archivo_sel}")
                    val_fecha = c2.text_input("Fecha", obs_input.fecha_realizacion or "", key=f"f_{archivo_sel}")
                    val_hora = c3.text_input("Hora", obs_input.hora or "", key=f"h_{archivo_sel}")
                    
                    # --- CAJA DE OPCIONES DE ÁREA QUE REALIZA LA ACTIVIDAD ---
                    c_ar1, c_ar2 = st.columns([1, 1])
                    current_area = (obs_input.area or "Administración de Operaciones").strip()
                    lista_oficial = [a for a in AREAS_OPERATIVAS if a != "Otros"]
                    
                    if current_area in lista_oficial:
                        idx_area = lista_oficial.index(current_area)
                        custom_area_val = ""
                    else:
                        matched = next((a for a in lista_oficial if a.lower() in current_area.lower() or current_area.lower() in a.lower()), None)
                        if matched:
                            idx_area = lista_oficial.index(matched)
                            custom_area_val = ""
                        else:
                            idx_area = len(AREAS_OPERATIVAS) - 1 # 'Otros'
                            custom_area_val = current_area
                    
                    val_area_sel = c_ar1.selectbox(
                        "🏢 Área que Realiza la Actividad:",
                        AREAS_OPERATIVAS,
                        index=idx_area,
                        key=f"area_sel_{archivo_sel}"
                    )
                    
                    if val_area_sel == "Otros":
                        val_area_custom = c_ar2.text_input(
                            "✏️ Especifique Área Adicional:",
                            value=custom_area_val,
                            key=f"area_custom_{archivo_sel}",
                            placeholder="Escribe el nombre del área..."
                        )
                        val_area_final = val_area_custom.strip() if val_area_custom.strip() else "Otros"
                    else:
                        val_area_final = val_area_sel
                        c_ar2.caption(f"Área Registrada: **{val_area_final}**")
                    
                    c4, c5 = st.columns(2)
                    val_obs = c4.text_input("Observador", obs_input.observador or "", key=f"o_{archivo_sel}")
                    val_sup = c5.text_input("Supervisor SST", obs_input.supervisor_sst or "", key=f"s_{archivo_sel}")
                    
                    c6, c7 = st.columns(2)
                    val_emp = c6.text_input("Empresa Ejecutante", obs_input.empresa_ejecutante or "", key=f"e_{archivo_sel}")
                    val_lugar = c7.text_input("Lugar", obs_input.lugar or "", key=f"l_{archivo_sel}")
                    val_tarea = st.text_input("Tarea Crítica", obs_input.tarea_critica or "", key=f"tc_{archivo_sel}")

                with st.expander(f"📊 Comportamientos Críticos ({len(obs_input.items)} ítems)", expanded=False):
                    st.markdown(f"**SI**: `{eval_res.total_cumplidos}` | **NO**: `{eval_res.total_no_cumplidos}` | **N/A**: `{eval_res.total_no_aplica}`")
                    for it in obs_input.items[:10]:
                        st.caption(f"**Ítem {it.item_number}** [{it.cumple}]: {it.descripcion or ''} {(' — Justificación: ' + it.por_que_causa) if it.por_que_causa else ''}")

                with st.expander("💡 Plan de Mejoramiento Formulado", expanded=True):
                    plan_text = st.text_area("Plan de Mejora:", obs_input.plan_mejoramiento.propuesto or "Ninguno", height=65, key=f"pm_{archivo_sel}")
                    cp1, cp2 = st.columns(2)
                    ejec_tipo = cp1.selectbox("Dificultad:", ["Fácil", "Difícil", "Proyecto Especial"], index=0, key=f"d_{archivo_sel}")
                    es_viable = cp2.checkbox("Es viable", value=obs_input.plan_mejoramiento.es_viable, key=f"v_{archivo_sel}")

                with st.expander("🗣️ Comentarios Registrados", expanded=False):
                    com_observado = st.text_area("Comentarios del Observado:", obs_input.comentarios_observado or "", height=60, key=f"co_{archivo_sel}")
                    com_adicional = st.text_area("Comentarios Adicionales:", obs_input.comentarios_adicionales_observador or "", height=60, key=f"ca_{archivo_sel}")

                st.markdown("---")
                if st.button(f"💾 Guardar Individual `{archivo_sel}` en Excel", key=f"save_btn_{archivo_sel}"):
                    obs_input.terminal = val_term
                    obs_input.fecha_realizacion = val_fecha
                    obs_input.hora = val_hora
                    obs_input.area = val_area_final
                    obs_input.observador = val_obs
                    obs_input.supervisor_sst = val_sup
                    obs_input.empresa_ejecutante = val_emp
                    obs_input.lugar = val_lugar
                    obs_input.tarea_critica = val_tarea
                    obs_input.plan_mejoramiento.propuesto = plan_text if plan_text != "Ninguno" else None
                    obs_input.plan_mejoramiento.tipo_ejecucion = ejec_tipo
                    obs_input.plan_mejoramiento.es_viable = es_viable
                    obs_input.comentarios_observado = com_observado
                    obs_input.comentarios_adicionales_observador = com_adicional
                    
                    new_eval = evaluate_observation(obs_input)
                    row_data = map_observation_to_44_columns(obs_input, new_eval)
                    try:
                        fila = append_to_master_excel(MASTER_EXCEL_PATH, row_data)
                        st.success(f"🎉 Observación guardada en fila {fila} de `{MASTER_EXCEL_PATH}`")
                        st.cache_data.clear()
                    except Exception as e:
                        st.error(f"Error al escribir en Excel: {e}")

# ==========================================================
# TAB 2: DASHBOARD ANALÍTICO (BI) - PALETA SURA (SUPABASE)
# ==========================================================
with tab_dashboard:
    from core.supabase_sync import fetch_observations_from_supabase
    
    st.markdown("### 📊 Indicadores de Desempeño y Calidad (Datos en Tiempo Real de Supabase)")
    st.caption("Este tablero se alimenta exclusivamente de las nuevas observaciones procesadas y almacenadas en Supabase.")
    
    col_info, col_btn = st.columns([3, 1])
    with col_info:
        st.info("⏳ **Nota de Sincronización:** Los datos guardados recientemente pueden tardar hasta 1 minuto en reflejarse debido a la memoria caché de la nube.")
    with col_btn:
        if st.button("🔄 Refrescar Datos Ahora"):
            st.cache_data.clear()
            st.rerun()
    
    raw_supa_data = fetch_observations_from_supabase()
    
    if not raw_supa_data:
        st.info("Aún no hay datos almacenados en Supabase o no se ha configurado la conexión. Procesa un lote de PDFs y sincronízalo para ver las analíticas.")
    else:
        df_supa = pd.DataFrame(raw_supa_data)
        
        # Parsear fechas para el filtro
        df_supa["fecha_realizacion"] = pd.to_datetime(df_supa["fecha_realizacion"], errors="coerce")
        valid_dates = df_supa["fecha_realizacion"].dropna()
        if not valid_dates.empty:
            min_date = valid_dates.min().date()
            max_date = valid_dates.max().date()
        else:
            min_date = datetime.today().date()
            max_date = datetime.today().date()
        
        # Filtros Superiores con diseño SURA
        with st.form("form_analitica"):
            st.markdown("#### Configuración de Filtros")
            col_f1, col_f2, col_f3, col_f4 = st.columns(4)
            
            # SIN min_value ni max_value para no bloquear el calendario si hay solo 1 dia registrado
            filtro_fechas = col_f1.date_input("Rango de Fechas", value=(min_date, max_date))
            
            obs_options = ["TODOS"] + sorted([str(x) for x in df_supa["observador"].dropna().unique() if str(x) != 'nan'])
            filtro_obs = col_f2.selectbox("Observador (Persona)", obs_options)
            
            # Áreas Oficiales solicitadas + Extras
            area_base = [a for a in AREAS_OPERATIVAS if a != "Otros"] + ["Otros"]
            extras = sorted([str(x) for x in df_supa["area"].dropna().unique() if str(x) != 'nan' and str(x) not in area_base])
            area_options = ["TODAS"] + area_base + extras
            filtro_area = col_f3.selectbox("🏢 Área que Realiza la Actividad", area_options)
            
            cat_options = ["TODAS"] + sorted([str(x) for x in df_supa["categoria"].dropna().unique() if str(x) != 'nan'])
            filtro_cat = col_f4.selectbox("Categoría Calidad", cat_options)
            
            btn_generar = st.form_submit_button("Generar Analítica 3D 📊", type="primary")
            
        if not btn_generar and not st.session_state.get('analitica_generada', False):
            st.info("👈 Selecciona los filtros que desees y haz clic en 'Generar Analítica 3D' para visualizar el dashboard.")
        else:
            st.session_state['analitica_generada'] = True
            
            # Aplicar filtros
            df_filtered = df_supa.copy()
        
            if isinstance(filtro_fechas, tuple) and len(filtro_fechas) == 2:
                start_dt, end_dt = filtro_fechas
                df_filtered = df_filtered[
                    (df_filtered["fecha_realizacion"].dt.date >= start_dt) & 
                    (df_filtered["fecha_realizacion"].dt.date <= end_dt)
                ]
            elif isinstance(filtro_fechas, tuple) and len(filtro_fechas) == 1:
                start_dt = filtro_fechas[0]
                df_filtered = df_filtered[df_filtered["fecha_realizacion"].dt.date == start_dt]
            
            if filtro_obs != "TODOS":
                df_filtered = df_filtered[df_filtered["observador"] == filtro_obs]
            if filtro_area != "TODAS":
                df_filtered = df_filtered[df_filtered["area"] == filtro_area]
            if filtro_cat != "TODAS":
                df_filtered = df_filtered[df_filtered["categoria"] == filtro_cat]
            
            total_obs = len(df_filtered)
        
            pcp_vals = pd.to_numeric(df_filtered["pcp_calculado"], errors="coerce").dropna()
            if not pcp_vals.empty:
                avg_pcp = pcp_vals.mean()
            else:
                avg_pcp = 0.0
            
            # Contar cuántos tienen plan propuesto
            def tiene_plan(raw):
                try:
                    return 1 if raw.get("input", {}).get("plan_mejoramiento", {}).get("propuesto") else 0
                except Exception:
                    return 0
                
            con_plan = df_filtered["raw_data"].apply(tiene_plan).sum() if ("raw_data" in df_filtered and not df_filtered.empty) else 0
            cat_d = (df_filtered["categoria"] == "D").sum()
        
            # Tarjetas de KPIs estilo Manual SURA
            k1, k2, k3, k4 = st.columns(4)
        
            with k1:
                st.markdown(f"""
                <div class="sura-kpi-card sura-kpi-border-blue">
                    <div class="sura-kpi-title">Observaciones Registradas</div>
                    <div class="sura-kpi-value">{total_obs:,}</div>
                    <div class="sura-kpi-subtext">Total en el periodo filtrado</div>
                </div>
                """, unsafe_allow_html=True)
            
            with k2:
                delta_color = "#059669" if avg_pcp >= 95.0 else "#DC2626"
                delta_sign = "+" if avg_pcp >= 95.0 else ""
                st.markdown(f"""
                <div class="sura-kpi-card sura-kpi-border-cyan">
                    <div class="sura-kpi-title">% PCP Promedio Cumplido</div>
                    <div class="sura-kpi-value">{avg_pcp:.1f}%</div>
                    <div class="sura-kpi-subtext" style="color: {delta_color}; font-weight:600;">
                        {delta_sign}{avg_pcp - 95.0:.1f}% vs Meta Corporativa (95%)
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with k3:
                pct_plan = (con_plan / max(1, total_obs)) * 100
                st.markdown(f"""
                <div class="sura-kpi-card sura-kpi-border-yellow">
                    <div class="sura-kpi-title">Planes de Mejora Propuestos</div>
                    <div class="sura-kpi-value">{con_plan:,}</div>
                    <div class="sura-kpi-subtext">Cobertura: <b>{pct_plan:.1f}%</b> de observaciones</div>
                </div>
                """, unsafe_allow_html=True)
            
            with k4:
                pct_d = (cat_d / max(1, total_obs)) * 100
                st.markdown(f"""
                <div class="sura-kpi-card sura-kpi-border-red">
                    <div class="sura-kpi-title">Incompletas (Categoría D)</div>
                    <div class="sura-kpi-value" style="color: #DC2626;">{cat_d:,}</div>
                    <div class="sura-kpi-subtext">Tasa de no conformidad: <b>{pct_d:.1f}%</b></div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            # ==========================================================
            # SECCIÓN 3D INTERACTIVA ULTRA-PREMIUM (NADA PLANO)
            # ==========================================================
            st.markdown("#### 🌐 **Espacio Tridimensional de Calidad Portuaria (Visualización 3D)**")
            st.caption("Interactúa libremente: arrastra con el ratón para rotación orbital 360°, usa la rueda para zoom y clic derecho para paneo.")
            
            c3d_1, c3d_2 = st.columns([3, 2])
            
            with c3d_1:
                st.markdown("##### 🚀 Cubo Espacial 3D (Área vs Empresa vs %PCP)")
                df_3d = df_filtered.dropna(subset=["area", "empresa_ejecutante", "pcp_calculado"]).copy()
                if not df_3d.empty:
                    df_3d["pcp_num"] = pd.to_numeric(df_3d["pcp_calculado"], errors="coerce").fillna(0)
                    
                    traces_3d = []
                    
                    # 1. Postes / Stem lines 3D verticales
                    x_stems, y_stems, z_stems = [], [], []
                    for _, r_item in df_3d.iterrows():
                        x_stems.extend([r_item["area"], r_item["area"], None])
                        y_stems.extend([r_item["empresa_ejecutante"], r_item["empresa_ejecutante"], None])
                        z_stems.extend([0, r_item["pcp_num"], None])
                        
                    traces_3d.append(go.Scatter3d(
                        x=x_stems, y=y_stems, z=z_stems,
                        mode="lines",
                        line=dict(color="#94A3B8", width=2),
                        hoverinfo="none",
                        showlegend=False
                    ))
                    
                    # 2. Esferas volumétricas 3D
                    colors_3d = [CATEGORY_PALETTE.get(c, {}).get("color", SURA_BLUE) for c in df_3d["categoria"]]
                    hover_texts = [
                        f"<b>Área:</b> {r_item['area']}<br>"
                        f"<b>Empresa:</b> {r_item['empresa_ejecutante']}<br>"
                        f"<b>% PCP:</b> {r_item['pcp_num']:.1f}%<br>"
                        f"<b>Categoría:</b> {r_item['categoria']}<br>"
                        f"<b>Observador:</b> {r_item.get('observador', 'N/A')}"
                        for _, r_item in df_3d.iterrows()
                    ]
                    
                    traces_3d.append(go.Scatter3d(
                        x=df_3d["area"],
                        y=df_3d["empresa_ejecutante"],
                        z=df_3d["pcp_num"],
                        mode="markers+text",
                        text=[f"{val:.0f}%" for val in df_3d["pcp_num"]],
                        textposition="top center",
                        textfont=dict(size=9, color=SURA_NAVY_DARK),
                        hoverinfo="text",
                        hovertext=hover_texts,
                        marker=dict(
                            size=9,
                            color=colors_3d,
                            opacity=0.92,
                            line=dict(color="#FFFFFF", width=1.5)
                        ),
                        name="Observaciones"
                    ))
                    
                    fig_cube = go.Figure(data=traces_3d)
                    fig_cube.update_layout(
                        scene=dict(
                            xaxis=dict(title="Área", backgroundcolor="#F8FAFC", gridcolor="#E2E8F0"),
                            yaxis=dict(title="Empresa", backgroundcolor="#F8FAFC", gridcolor="#E2E8F0"),
                            zaxis=dict(title="% PCP", range=[0, 105], backgroundcolor="#F8FAFC", gridcolor="#E2E8F0"),
                            camera=dict(eye=dict(x=1.65, y=1.65, z=1.2))
                        ),
                        height=440,
                        margin=dict(l=0, r=0, b=0, t=10),
                        paper_bgcolor="rgba(0,0,0,0)"
                    )
                    st.plotly_chart(fig_cube, use_container_width=True)
                else:
                    st.info("No hay suficientes datos filtrados para generar el Cubo 3D.")

            with c3d_2:
                st.markdown("##### 🏔️ Topografía 3D de Concentración de Riesgo")
                if not df_filtered.empty and "area" in df_filtered and "categoria" in df_filtered:
                    ct = pd.crosstab(df_filtered["area"], df_filtered["categoria"])
                    if not ct.empty and len(ct.index) >= 2 and len(ct.columns) >= 2:
                        fig_surf = go.Figure(data=[go.Surface(
                            z=ct.values,
                            x=ct.columns.tolist(),
                            y=ct.index.tolist(),
                            colorscale=[[0, "#E0F2FE"], [0.5, "#00AEC7"], [1, "#0033A0"]],
                            opacity=0.94,
                            contours=dict(z=dict(show=True, usecolormap=True, project_z=True))
                        )])
                        fig_surf.update_layout(
                            scene=dict(
                                xaxis=dict(title="Categoría", backgroundcolor="#F8FAFC", gridcolor="#E2E8F0"),
                                yaxis=dict(title="Área", backgroundcolor="#F8FAFC", gridcolor="#E2E8F0"),
                                zaxis=dict(title="Total Obs", backgroundcolor="#F8FAFC", gridcolor="#E2E8F0"),
                                camera=dict(eye=dict(x=1.5, y=1.5, z=1.3))
                            ),
                            height=440,
                            margin=dict(l=0, r=0, b=0, t=10),
                            paper_bgcolor="rgba(0,0,0,0)"
                        )
                        st.plotly_chart(fig_surf, use_container_width=True)
                    else:
                        # Respaldo 3D para matrices pequeñas
                        fig_bar3d = px.bar(
                            df_filtered["area"].value_counts().reset_index(),
                            x="area", y="count", color="area",
                            color_discrete_sequence=[SURA_BLUE, SURA_CYAN, SURA_YELLOW, SURA_NAVY_DARK]
                        )
                        fig_bar3d.update_layout(height=440, showlegend=False)
                        st.plotly_chart(fig_bar3d, use_container_width=True)
                else:
                    st.info("Sin registros para la topografía 3D.")

            # Fila de Gráficos 2 (Distribución por Área y Tendencia)
            cg1, cg2 = st.columns(2)
        
            with cg1:
                st.markdown("##### ⚓ Desempeño y Observaciones por Área que Realiza la Actividad")
                area_counts = df_filtered["area"].value_counts().reset_index()
                area_counts.columns = ["Área", "Observaciones"]
                fig_area = px.bar(
                    area_counts, y="Área", x="Observaciones", orientation='h',
                    color="Observaciones",
                    color_continuous_scale=[[0, SURA_CYAN], [1, SURA_BLUE]]
                )
                fig_area.update_layout(
                    height=360, yaxis={"categoryorder": "total ascending"},
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=20, r=20, t=20, b=20)
                )
                st.plotly_chart(fig_area, use_container_width=True)
            
            with cg2:
                st.markdown("##### 📈 Evolución del %PCP por Terminal (Tendencia Temporal)")
                df_pcp_trend = df_filtered.dropna(subset=["fecha_realizacion", "pcp_calculado", "terminal"]).copy()
                df_pcp_trend["Mes"] = df_pcp_trend["fecha_realizacion"].dt.strftime("%Y-%m")
                df_pcp_trend["PCP_Pct"] = pd.to_numeric(df_pcp_trend["pcp_calculado"], errors="coerce")
            
                trend_grouped = df_pcp_trend.groupby(["Mes", "terminal"])["PCP_Pct"].mean().reset_index()
                trend_grouped = trend_grouped.sort_values("Mes")
            
                fig_trend = px.line(
                    trend_grouped, x="Mes", y="PCP_Pct", color="terminal",
                    markers=True, color_discrete_map={"CTC": SURA_BLUE, "SPRC": SURA_CYAN}
                )
                fig_trend.update_layout(
                    height=360, yaxis_title="% PCP Promedio",
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=20, r=20, t=20, b=20),
                    yaxis=dict(range=[80, 105], showgrid=True, gridcolor="#E2E8F0")
                )
                st.plotly_chart(fig_trend, use_container_width=True)

            # ==========================================================
            # GENERADOR DE INFORME EJECUTIVO MODIFICADO (ÁREAS + IA DUAL)
            # ==========================================================
            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown("#### 📝 Generador de Informe Ejecutivo Multimodal (Áreas & Calidad)")
            st.caption("Genera un informe integral con balance por Área Operativa, cumplimiento de metas %PCP y recomendaciones específicas.")
            
            c_eng1, c_eng2 = st.columns([2, 1])
            motores_disponibles = []
            if GEMINI_KEY:
                motores_disponibles.append("Google Gemini 3.X Flash (Visión & Razonamiento)")
            if DEEPSEEK_KEY:
                motores_disponibles.append("DeepSeek V3 / R1 (Auditoría Profunda)")
            motores_disponibles.append("Motor Ejecutivo Heurístico Nativo")
            
            motor_sel = c_eng1.selectbox("Motor de Inteligencia Artificial para el Informe:", motores_disponibles)
            btn_generar_inf = c_eng2.button("Generar Informe Ejecutivo 🚀", type="primary", use_container_width=True)
            
            if btn_generar_inf:
                with st.spinner(f"Redactando informe ejecutivo con {motor_sel}..."):
                    resumen_cat = df_filtered["categoria"].value_counts().to_dict()
                    resumen_areas = df_filtered["area"].value_counts().to_dict()
                    
                    df_valid_pcp = df_filtered.dropna(subset=["area", "pcp_calculado"]).copy()
                    df_valid_pcp["pcp_num"] = pd.to_numeric(df_valid_pcp["pcp_calculado"], errors="coerce")
                    pcp_por_area = df_valid_pcp.groupby("area")["pcp_num"].mean().round(1).to_dict() if not df_valid_pcp.empty else {}
                    total_obs = len(df_filtered)
                    
                    prompt = f'''
Eres el Director de Seguridad y Salud en el Trabajo (SST) de CONTECAR y ARL SURA.
Acabas de auditar un lote consolidado de {total_obs} observaciones de tareas críticas.

DISTRIBUCIÓN POR ÁREA OPERATIVA QUE REALIZA LA ACTIVIDAD:
{resumen_areas}

PROMEDIO % PCP POR ÁREA:
{pcp_por_area}

DISTRIBUCIÓN DE CALIDAD DE LAS OBSERVACIONES (MATRIZ SURA):
{resumen_cat}

Contexto normativo:
- Meta corporativa: %PCP >= 95%.
- Categorías A / A+: Sobresalientes con alto impacto preventivo y análisis causal.
- Categorías B / B+: Buenas, planes de mejora aplicables estándar o con evidencias fotográficas.
- Categorías C / C+: Regulares, diligenciamiento completo pero sin plan de mejora estructurado.
- Categoría D: Deficientes o incompletas (requieren subsanación formal).

ÁREAS MONITOREADAS:
Administración de Operaciones, Aforos, Bodegas, Mantenimiento, Operaciones Marítimas, Refrigerados, Seguridad Física, SST, Vehículos y Otras.

Escribe un informe ejecutivo formal, contundente y estructurado:
1. Párrafo 1: Balance general de accidentalidad, cobertura y cumplimiento corporativo.
2. Párrafo 2: Diagnóstico por Áreas Operativas (destacando las áreas con mejor desempeño y las áreas críticas que demandan intervención inmediata).
3. Párrafo 3: Conclusiones y recomendaciones estratégicas por viñetas para los líderes de área y supervisores SST en campo.
'''
                    informe_texto = ""
                    try:
                        if "Gemini" in motor_sel and (GEMINI_KEYS or GEMINI_KEY):
                            from google import genai
                            gemini_3x_models = [
                                "gemini-3-flash",
                                "gemini-3.0-flash",
                                "gemini-3.8-flash",
                                "gemini-3.7-flash",
                                "gemini-3.6-flash"
                            ]
                            active_keys = GEMINI_KEYS if GEMINI_KEYS else [GEMINI_KEY]
                            for curr_key in active_keys:
                                client = genai.Client(api_key=curr_key)
                                for model_name in gemini_3x_models:
                                    try:
                                        res = client.models.generate_content(
                                            model=model_name,
                                            contents=prompt
                                        )
                                        if res and res.text:
                                            informe_texto = res.text
                                            break
                                    except Exception:
                                        continue
                                if informe_texto:
                                    break
                        elif "DeepSeek" in motor_sel and DEEPSEEK_KEY:
                            import json
                            import urllib.request
                            url = "https://api.deepseek.com/chat/completions"
                            headers = {
                                "Content-Type": "application/json",
                                "Authorization": f"Bearer {DEEPSEEK_KEY}"
                            }
                            payload = {
                                "model": "deepseek-chat",
                                "messages": [
                                    {"role": "system", "content": "Eres el Director Senior de SST de SURA y CONTECAR."},
                                    {"role": "user", "content": prompt}
                                ],
                                "temperature": 0.3
                            }
                            req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers=headers, method="POST")
                            with urllib.request.urlopen(req, timeout=30) as resp:
                                res_json = json.loads(resp.read().decode("utf-8"))
                                informe_texto = res_json["choices"][0]["message"]["content"]
                        else:
                            # Motor Heurístico Ejecutivo Nativo
                            mejor_area = max(pcp_por_area, key=pcp_por_area.get) if pcp_por_area else "N/A"
                            peor_area = min(pcp_por_area, key=pcp_por_area.get) if pcp_por_area else "N/A"
                            top_areas = ', '.join([f'{a} ({c} obs)' for a, c in list(resumen_areas.items())[:4]])
                            informe_texto = f"""
### 📋 Balance Ejecutivo Consolidado de SST y Calidad Operativa

Durante el periodo evaluado se auditaron un total de **{total_obs:,} observaciones** de tareas críticas en las terminales portuarias. El nivel de cumplimiento global alcanzó un **{avg_pcp:.1f}% de PCP**, frente a la meta corporativa del **95.0%**, evidenciando un compromiso firme en la aplicación de los estándares de seguridad basados en comportamientos (SBC).

#### 🏢 Diagnóstico por Áreas que Realizan la Actividad:
- **Área con Mayor Cumplimiento:** **{mejor_area}** con un promedio de **{pcp_por_area.get(mejor_area, 0):.1f}% de PCP**.
- **Área con Mayor Oportunidad de Mejora:** **{peor_area}** con un promedio de **{pcp_por_area.get(peor_area, 0):.1f}% de PCP**, concentrando la mayor tasa de observaciones que requieren acompañamiento técnico.
- **Distribución de Cobertura:** Las áreas con mayor registro fueron: {top_areas if top_areas else 'Áreas registradas'}.

#### 🎯 Recomendaciones Estratégicas para la Supervisión:
- **Subsanación de Incompletitudes:** Revisar con prioridad las **{cat_d} observaciones en Categoría D** para registrar causas específicas o planes de mejora.
- **Evidencia Gráfica en Áreas Críticas:** Promover en *Mantenimiento*, *Refrigerados* y *Operaciones Marítimas* la captura de fotos de mejoras para elevar las calificaciones a B+ y A.
- **Seguimiento a Comportamientos:** Coordinar sesiones de refuerzo positivo en *Vehículos* y *Aforos* para consolidar una cultura preventiva de autocuidado.
"""
                        st.success("✅ Informe Ejecutivo Generado Exitosamente:")
                        st.markdown(informe_texto)
                    except Exception as e:
                        st.error(f"Falla al conectar con el servicio de IA ({e}). Mostrando informe heurístico consolidado:")
                        st.markdown(f"**Balance:** {total_obs} observaciones evaluadas. PCP promedio: {avg_pcp:.1f}%.")
    # ==========================================================
    # TAB 3: BASE DE DATOS MAESTRA (44 COLUMNAS)
    # ==========================================================
with tab_datos:
    st.markdown("### 🗄️ Explorador de la Base de Datos Maestra (44 Columnas)")
    if df_master.empty:
        st.info("No hay datos disponibles.")
    else:
        st.caption(f"Fuente oficial conectada: `{MASTER_EXCEL_PATH}` ({len(df_master):,} registros).")
        
        col_s1, col_s2 = st.columns([3, 1])
        busqueda = col_s1.text_input("🔍 Filtro global por Observador, Tarea Crítica, Lugar o Empresa:")
        
        df_display = df_master.copy()
        if busqueda:
            mask = df_display.astype(str).apply(lambda row: row.str.contains(busqueda, case=False).any(), axis=1)
            df_display = df_display[mask]
            
        st.dataframe(df_display.head(100), use_container_width=True, height=450)
        st.caption(f"Mostrando {min(100, len(df_display))} de {len(df_display)} registros filtrados.")
        
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            df_display.to_excel(writer, sheet_name="BD_SST", index=False)
            
        st.download_button(
            label="📥 Descargar Base Completa en Excel (.xlsx)",
            data=buf.getvalue(),
            file_name=f"BD_Observaciones_SURA_CONTECAR_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

# ==========================================================
# TAB 4: CRITERIOS DE CALIFICACIÓN & NORMATIVA
# ==========================================================
with tab_criterios:
    st.markdown("### 📖 Manual de Calificación y Criterios Operativos SURA / CONTECAR")
    st.markdown("""
    Criterios estandarizados de evaluación de la calidad de observaciones de comportamiento, basados en el acuerdo operativo con **Kellys Escorcia**:
    """)
    
    tabla_criterios = pd.DataFrame([
        {"Categoría": "D", "Estado": "Subsanación Requerida", "Condición Disparadora": "Falta fecha, hora, terminal, empresa, ítem 'NO' sin justificación '¿Por qué?', o PCP < 100% sin Plan de Mejora.", "Acción / Recomendación": "El formato presenta campos sin diligenciar. Se devuelve para subsanar y remitir nuevamente."},
        {"Categoría": "C", "Estado": "Básico", "Condición Disparadora": "Formato completo, sin plan de mejora, y comentarios del observado dicen 'Sin comentarios'.", "Acción / Recomendación": "Diligenciamiento adecuado. Formular planes de mejora concretos y registrar percepción del observado."},
        {"Categoría": "C+", "Estado": "Aceptable", "Condición Disparadora": "Formato completo, comentarios del observado y/o adicionales redactados con sustancia, sin plan.", "Acción / Recomendación": "Diligenciamiento adecuado. Comentario bien redactado. En próximas observaciones formular plan de mejora."},
        {"Categoría": "R", "Estado": "Recomendación", "Condición Disparadora": "Diligencia recomendación pero no es viable o no aplica a la operación portuaria.", "Acción / Recomendación": "Recomendación identificada para validación con encargado de gestión."},
        {"Categoría": "R+", "Estado": "Recomendación Viable", "Condición Disparadora": "Diligencia recomendación viable y aplicable a la operación portuaria.", "Acción / Recomendación": "Recomendación viable identificada para validación técnica."},
        {"Categoría": "B", "Estado": "Plan Estándar", "Condición Disparadora": "Plan de mejora específico y aplicable (Clasificación estándar directa de IA).", "Acción / Recomendación": "Plan de mejora identificado y remitido para validación y seguimiento en campo."},
        {"Categoría": "B+", "Estado": "Plan con Evidencias", "Condición Disparadora": "Plan enfocado en prevención de accidentes / SST con evidencias fotográficas adjuntas.", "Acción / Recomendación": "Plan concreto enfocado en SST. Se agradecen las fotos y anexos para gestión efectiva."},
        {"Categoría": "A", "Estado": "Alto Impacto", "Condición Disparadora": "Plan de mejora con alto impacto comprobado en accidentalidad portuaria + fotos.", "Acción / Recomendación": "Plan de alto impacto enfocado en accidentalidad enviado a jefatura de gestión."},
        {"Categoría": "A+", "Estado": "Sobresaliente", "Condición Disparadora": "Plan de alto impacto con análisis causal, matriz de riesgos, DOFA o estudio de condiciones anexo.", "Acción / Recomendación": "Plan de alto impacto con análisis de condiciones de seguridad validado y priorizado."}
    ])
    
    st.table(tabla_criterios)
    
    st.markdown("#### 📑 Marco Normativo y Procedimientos Vinculados")
    st.markdown("""
    - **`PRC-HS-INT301`**: Instructivo para Reporte y Diligenciamiento de Observaciones de Comportamiento.
    - **`PRC-HS-SOP303`**: Procedimiento para Observación de Tareas Críticas (Formatos `HS-FMT301` a `HS-FMT326`).
    - **Metodología Spec-Driven**: Especificación formal activa en `openspec/specs/observation-engine/spec.md`.
    - **Estándar ARL SURA**: Gestión de la Seguridad Basada en Comportamientos (SBC) para operaciones marítimo-portuarias.
    """)
