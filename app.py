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
import pandas as pd
import openpyxl
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from dotenv import load_dotenv

# Modelos y lógica central
from core.models import ObservationInput, BehaviorItem, ImprovementPlan, ObservationEvaluation
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

# Carga de variables de entorno y secretos
load_dotenv()
GEMINI_KEY = os.environ.get("GEMINI_API_KEY")
try:
    if hasattr(st, "secrets") and "GEMINI_API_KEY" in st.secrets:
        GEMINI_KEY = st.secrets["GEMINI_API_KEY"]
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
    if GEMINI_KEY:
        st.markdown(f"""
        <div style='background:#EFF6FF; padding:12px; border-radius:8px; border-left:4px solid {SURA_BLUE};'>
            <div style='font-size:12px; font-weight:700; color:{SURA_NAVY_DARK};'>Visión Multimodal:</div>
            <div style='font-size:11px; color:#059669; font-weight:700;'>● Servicio Conectado (Seguro)</div>
            <div style='font-size:10px; color:{SURA_TEXT_MUTED}; margin-top:3px;'>OCR Manuscrito & Layout Activo</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.info("Modo de extracción local activo.")
        
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
        ["📁 Escanear Carpeta Completa (Batch)", "📤 Arrastrar Múltiples Archivos (Drag & Drop)", "🔍 Seleccionar Archivo Individual"],
        horizontal=True
    )
    
    archivos_a_procesar = []
    
    if modo_ingesta == "📁 Escanear Carpeta Completa (Batch)":
        st.markdown("Haz clic en el siguiente botón para seleccionar gráficamente con el ratón la carpeta que contiene los PDFs.")
        
        # Helper function for opening the native folder dialog
        def select_folder_dialog():
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.wm_attributes('-topmost', 1)
            folder = filedialog.askdirectory(master=root, title="Seleccione la carpeta con las observaciones en PDF")
            root.destroy()
            return folder

        col_btn, col_chk = st.columns([2, 2])
        
        if col_btn.button("📂 Seleccionar Carpeta con el Ratón (Ventana de Windows)", use_container_width=True):
            selected_path = select_folder_dialog()
            if selected_path:
                st.session_state["scanned_folder_path"] = selected_path
                st.rerun()

        excluir_manuales = col_chk.checkbox("Excluir manuales (PRC-*)", value=True)
        
        carpeta_input = st.session_state.get("scanned_folder_path", "")
        
        if carpeta_input and os.path.exists(carpeta_input):
            encontrados = scan_directory_for_pdfs(carpeta_input, exclude_procedures=excluir_manuales)
            st.success(f"📍 **Carpeta seleccionada:** `{carpeta_input}`\n\n📄 Se detectaron **{len(encontrados)}** archivos PDF listos para escanear.")
            archivos_a_procesar = encontrados
        elif not carpeta_input:
            st.info("Aún no se ha seleccionado ninguna carpeta.")
        else:
            st.error(f"La carpeta '{carpeta_input}' ya no existe en el sistema.")

    elif modo_ingesta == "📤 Arrastrar Múltiples Archivos (Drag & Drop)":
        archivos_subidos = st.file_uploader(
            "Arrastra aquí todos los PDFs escaneados de la carpeta:",
            type=["pdf"],
            accept_multiple_files=True
        )
        if archivos_subidos:
            os.makedirs("scratch", exist_ok=True)
            rutas = []
            for up_file in archivos_subidos:
                save_p = os.path.join("scratch", up_file.name)
                with open(save_p, "wb") as f:
                    f.write(up_file.getbuffer())
                rutas.append(save_p)
            archivos_a_procesar = rutas
            st.info(f"Se cargaron **{len(archivos_a_procesar)}** archivos para procesar.")

    else:
        # Selección individual
        ejemplos_disponibles = {
            "MAN DE INS ELE AGOSTO SEM 3.pdf": "Mantenimiento Eléctrico (Contecar)",
            "Observación compórtate 11-09-2026.pdf": "Entrada y Salida Vehicular (SPRC)",
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

    # Botón de Procesamiento Masivo / Individual
    st.markdown("---")
    if archivos_a_procesar:
        btn_col, _ = st.columns([2, 3])
        texto_btn = f"🚀 Procesar Lote Completo ({len(archivos_a_procesar)} archivos con OCR)" if len(archivos_a_procesar) > 1 else "⚡ Extraer y Evaluar Observación"
        if btn_col.button(texto_btn, type="primary", use_container_width=True):
            progress_bar = st.progress(0.0)
            status_text = st.empty()
            
            def on_progress(current, total, fname):
                progress_bar.progress(current / total)
                status_text.caption(f"Procesando ({current}/{total}): `{fname}`...")
                
            resultados_lote = process_batch(archivos_a_procesar, api_key=GEMINI_KEY, progress_callback=on_progress)
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
            
            area_options = ["TODAS"] + sorted([str(x) for x in df_supa["area"].dropna().unique() if str(x) != 'nan'])
            filtro_area = col_f3.selectbox("Área Operativa", area_options)
            
            cat_options = ["TODAS"] + sorted([str(x) for x in df_supa["categoria"].dropna().unique() if str(x) != 'nan'])
            filtro_cat = col_f4.selectbox("Categoría Calidad", cat_options)
            
            btn_generar = st.form_submit_button("Generar Analítica 📊", type="primary")
            
        if not btn_generar and not st.session_state.get('analitica_generada', False):
            st.info("👈 Selecciona los filtros que desees y haz clic en 'Generar Analítica' para visualizar el dashboard.")
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
            
            # Contar cuántos tienen plan propuesto verificando dentro del JSON raw_data
            def tiene_plan(raw):
                try:
                    return 1 if raw.get("input", {}).get("plan_mejoramiento", {}).get("propuesto") else 0
                except:
                    return 0
                
            con_plan = df_filtered["raw_data"].apply(tiene_plan).sum() if not df_filtered.empty else 0
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
        
            # Fila de Gráficos 1
            cg1, cg2 = st.columns(2)
        
            with cg1:
                st.markdown("##### 🏆 Distribución de Categorías de Calidad (Matriz SURA)")
                cat_counts = df_filtered["categoria"].value_counts().reset_index()
                cat_counts.columns = ["Categoría", "Cantidad"]
            
                color_map = {cat: data["color"] for cat, data in CATEGORY_PALETTE.items()}
            
                fig_cat = px.bar(
                    cat_counts, x="Categoría", y="Cantidad",
                    color="Categoría", color_discrete_map=color_map,
                    text="Cantidad"
                )
                fig_cat.update_layout(
                    showlegend=False, height=350,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=20, r=20, t=20, b=20),
                    xaxis=dict(title="Categoría Oficial"),
                    yaxis=dict(title="Número de Observaciones", showgrid=True, gridcolor="#E2E8F0")
                )
                st.plotly_chart(fig_cat, use_container_width=True)
            
            with cg2:
                st.markdown("##### 📈 Evolución del %PCP (Tendencia Temporal)")
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
                    height=350, yaxis_title="% PCP Promedio",
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=20, r=20, t=20, b=20),
                    yaxis=dict(range=[80, 105], showgrid=True, gridcolor="#E2E8F0")
                )
                st.plotly_chart(fig_trend, use_container_width=True)
            
            # Fila de Gráficos 2
            cg3, cg4 = st.columns(2)
        
            with cg3:
                st.markdown("##### ⚓ Observaciones por Área Operativa")
                area_counts = df_filtered["area"].value_counts().reset_index().head(10)
                area_counts.columns = ["Área", "Observaciones"]
                fig_area = px.bar(
                    area_counts, y="Área", x="Observaciones", orientation='h',
                    color_discrete_sequence=[SURA_BLUE]
                )
                fig_area.update_layout(
                    height=350, yaxis={"categoryorder": "total ascending"},
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    margin=dict(l=20, r=20, t=20, b=20)
                )
                st.plotly_chart(fig_area, use_container_width=True)
            
            with cg4:
                st.markdown("##### 🏢 Observaciones por Empresa Ejecutante")
                emp_counts = df_filtered["empresa_ejecutante"].value_counts().reset_index().head(10)
                emp_counts.columns = ["Empresa", "Observaciones"]
                fig_emp = px.pie(
                    emp_counts, names="Empresa", values="Observaciones",
                    color_discrete_sequence=[SURA_BLUE, SURA_CYAN, SURA_YELLOW, SURA_NAVY_DARK, "#94A3B8"]
                )
                fig_emp.update_layout(height=350, margin=dict(l=20, r=20, t=20, b=20))
                st.plotly_chart(fig_emp, use_container_width=True)


            st.markdown("<hr>", unsafe_allow_html=True)
            st.markdown("#### 📝 Generador de Informe Ejecutivo Automático")
            st.caption("Genera un resumen en texto clasificado por las categorías de calidad A, B, C, D basado en tus filtros.")
            
            if st.button("Generar Informe de la Selección", type="secondary"):
                with st.spinner("La Inteligencia Artificial está redactando el informe ejecutivo..."):
                    try:
                        from google import genai
                        client = genai.Client()
                        
                        resumen_cat = df_filtered["categoria"].value_counts().to_dict()
                        total_obs = len(df_filtered)
                        
                        prompt = f'''
Eres el Director de Seguridad y Salud en el Trabajo (SST) de CONTECAR / SURA.
Acabas de revisar un lote de {total_obs} observaciones de comportamiento.
La distribución de calidad de las observaciones es la siguiente (Matriz SURA):
{resumen_cat}

Contexto de calificaciones:
- A / A+: Sobresalientes, alto impacto.
- B / B+: Buenas, planes de mejora estándar.
- C / C+: Regulares, incompletas pero funcionales.
- D: Deficientes, requieren subsanación.

Escribe un reporte ejecutivo formal y corto (máximo 3 párrafos).
1. Un párrafo resumiendo el balance general.
2. Un desglose en viñetas (bullet points) destacando las clasificaciones.
3. Una recomendación final para los supervisores.
'''
                        
                        response = client.models.generate_content(
                            model='gemini-2.5-flash',
                            contents=prompt
                        )
                        st.success("Informe generado con éxito:")
                        st.write(response.text)
                    except Exception as e:
                        st.error(f"No se pudo generar el informe: {e}")
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
