"""
Manual de Marca SURA & CONTECAR - Sistema de Diseño y Componentes Visuales.
Define la paleta de colores oficial, tipografía, badges, tarjetas KPI y encabezados institucionales.
"""

import os
import base64

# --- PALETA CORPORATIVA OFICIAL SURA ---
SURA_BLUE = "#0033A0"       # Azul Primario SURA (Pantone Reflex Blue)
SURA_CYAN = "#00AEC7"       # Azul Claro / Cian SURA
SURA_YELLOW = "#FFC72C"     # Amarillo / Dorado de acento
SURA_NAVY_DARK = "#0A1E4A"   # Azul Noche institucional
SURA_BG_LIGHT = "#F8FAFC"    # Fondo gris neutro de alta legibilidad
SURA_CARD_BORDER = "#E2E8F0" # Bordes limpios
SURA_TEXT_MAIN = "#1E293B"   # Texto oscuro principal
SURA_TEXT_MUTED = "#64748B"  # Texto secundario

# --- PALETA SEMÁFORO DE CALIDAD SST ---
CATEGORY_PALETTE = {
    "D": {"color": "#DC2626", "bg": "#FEE2E2", "label": "Categoría D (Subsanar / Incompleto)"},
    "C": {"color": "#D97706", "bg": "#FEF3C7", "label": "Categoría C (Sin comentarios / Sin plan)"},
    "C+": {"color": "#0033A0", "bg": "#DBEAFE", "label": "Categoría C+ (Comentario cualitativo)"},
    "R": {"color": "#7C3AED", "bg": "#EDE9FE", "label": "Categoría R (Recomendación no viable)"},
    "R+": {"color": "#6D28D9", "bg": "#DDD6FE", "label": "Categoría R+ (Recomendación viable)"},
    "B": {"color": "#00AEC7", "bg": "#E0F2FE", "label": "Categoría B (Plan estándar aplicable)"},
    "B+": {"color": "#059669", "bg": "#D1FAE5", "label": "Categoría B+ (Plan SST + Evidencia fotos)"},
    "A": {"color": "#047857", "bg": "#A7F3D0", "label": "Categoría A (Alto impacto en accidentalidad)"},
    "A+": {"color": "#064E3B", "bg": "#6EE7B7", "label": "Categoría A+ (Alto impacto + Análisis causal)"}
}

def get_base64_image(path: str) -> str:
    """Lee una imagen y la retorna en formato base64 data URI."""
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        data = f.read()
    b64 = base64.b64encode(data).decode("utf-8")
    ext = path.split(".")[-1].lower()
    mime = "image/svg+xml" if ext == "svg" else f"image/{ext}"
    return f"data:{mime};base64,{b64}"


def get_custom_css() -> str:
    """Retorna las reglas CSS adaptadas al Manual de Marca de SURA."""
    return f"""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
        
        html, body, [class*="css"] {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            color: {SURA_TEXT_MAIN};
        }}
        
        /* Contenedor de encabezado superior institucional */
        .sura-header-container {{
            background: #FFFFFF;
            border-radius: 12px;
            padding: 16px 24px;
            box-shadow: 0 4px 16px rgba(0, 51, 160, 0.06);
            border: 1px solid {SURA_CARD_BORDER};
            border-bottom: 4px solid {SURA_BLUE};
            margin-bottom: 24px;
            position: relative;
        }}
        
        .sura-accent-stripe {{
            position: absolute;
            bottom: -4px;
            left: 0;
            width: 140px;
            height: 4px;
            background: {SURA_YELLOW};
            border-radius: 2px 2px 0 0;
        }}
        
        /* Tarjetas de Métricas KPI */
        .sura-kpi-card {{
            background: #FFFFFF;
            border: 1px solid {SURA_CARD_BORDER};
            border-radius: 12px;
            padding: 18px 20px;
            box-shadow: 0 2px 10px rgba(0, 51, 160, 0.04);
            transition: all 0.2s ease-in-out;
            position: relative;
            overflow: hidden;
        }}
        .sura-kpi-card:hover {{
            box-shadow: 0 6px 20px rgba(0, 51, 160, 0.10);
            transform: translateY(-2px);
        }}
        .sura-kpi-border-blue {{ border-left: 5px solid {SURA_BLUE}; }}
        .sura-kpi-border-cyan {{ border-left: 5px solid {SURA_CYAN}; }}
        .sura-kpi-border-yellow {{ border-left: 5px solid {SURA_YELLOW}; }}
        .sura-kpi-border-red {{ border-left: 5px solid #DC2626; }}
        
        .sura-kpi-title {{
            font-size: 13px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            color: {SURA_TEXT_MUTED};
            margin-bottom: 6px;
        }}
        .sura-kpi-value {{
            font-size: 28px;
            font-weight: 700;
            color: {SURA_NAVY_DARK};
            line-height: 1.2;
        }}
        .sura-kpi-subtext {{
            font-size: 12px;
            color: {SURA_TEXT_MUTED};
            margin-top: 4px;
        }}
        
        /* Botones estilo SURA */
        div.stButton > button[kind="primary"] {{
            background-color: {SURA_BLUE} !important;
            color: #FFFFFF !important;
            font-weight: 600 !important;
            border-radius: 8px !important;
            border: none !important;
            padding: 10px 24px !important;
            box-shadow: 0 3px 12px rgba(0, 51, 160, 0.25) !important;
            transition: background-color 0.2s ease !important;
        }}
        div.stButton > button[kind="primary"]:hover {{
            background-color: #002270 !important;
            box-shadow: 0 4px 16px rgba(0, 51, 160, 0.35) !important;
        }}
        
        div.stButton > button[kind="secondary"] {{
            background-color: #FFFFFF !important;
            color: {SURA_BLUE} !important;
            font-weight: 600 !important;
            border-radius: 8px !important;
            border: 1.5px solid {SURA_BLUE} !important;
        }}
        
        /* Pestañas / Tabs */
        .stTabs [data-baseweb="tab-list"] {{
            gap: 12px;
            border-bottom: 2px solid {SURA_CARD_BORDER};
            padding-bottom: 2px;
        }}
        .stTabs [data-baseweb="tab"] {{
            font-weight: 600;
            font-size: 15px;
            color: {SURA_TEXT_MUTED};
            padding: 10px 18px;
            border-radius: 8px 8px 0 0;
        }}
        .stTabs [aria-selected="true"] {{
            color: {SURA_BLUE} !important;
            border-bottom: 3px solid {SURA_BLUE} !important;
            background-color: rgba(0, 51, 160, 0.04);
        }}
        
        /* Badges de Categoría */
        .sura-badge {{
            display: inline-flex;
            align-items: center;
            gap: 6px;
            font-weight: 700;
            font-size: 13px;
            padding: 5px 14px;
            border-radius: 20px;
            letter-spacing: 0.3px;
        }}
        
        /* Bloque informativo Split-view */
        .split-view-banner {{
            background: linear-gradient(135deg, rgba(0, 51, 160, 0.05) 0%, rgba(0, 174, 199, 0.08) 100%);
            border: 1px solid rgba(0, 51, 160, 0.15);
            border-radius: 10px;
            padding: 14px 18px;
            margin-bottom: 15px;
        }}
    </style>
    """


def get_header_html() -> str:
    """Genera el bloque HTML superior institucional combinando los logos oficiales de SURA y CONTECAR."""
    sura_uri = get_base64_image("assets/sura_logo.svg")
    contecar_uri = get_base64_image("assets/int301_img_0.jpeg")
    
    return f"""
    <div class="sura-header-container">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
            <div style="display: flex; align-items: center; gap: 24px;">
                <img src="{sura_uri}" alt="Logo SURA" style="height: 48px; object-fit: contain;">
                <div style="height: 40px; width: 1.5px; background-color: {SURA_CARD_BORDER};"></div>
                <img src="{contecar_uri}" alt="Logo CONTECAR / SPRC" style="height: 46px; object-fit: contain;">
            </div>
            <div style="text-align: right;">
                <div style="font-size: 19px; font-weight: 700; color: {SURA_NAVY_DARK}; letter-spacing: -0.3px;">
                    Programa de Seguridad Basada en Comportamientos (SBC)
                </div>
                <div style="font-size: 13px; font-weight: 500; color: {SURA_TEXT_MUTED};">
                    Proceso ComPORTate • CONTECAR & SPRC • Modelo Integral de Gestión del Riesgo
                </div>
            </div>
        </div>
        <div class="sura-accent-stripe"></div>
    </div>
    """


def get_sidebar_brand_html() -> str:
    """Genera el bloque de identidad para la barra lateral."""
    sura_uri = get_base64_image("assets/sura_logo.svg")
    return f"""
    <div style="text-align: center; padding: 10px 0 16px 0;">
        <img src="{sura_uri}" alt="SURA" style="max-width: 140px; margin-bottom: 8px;">
        <div style="font-size: 11px; font-weight: 700; color: {SURA_BLUE}; letter-spacing: 1px; text-transform: uppercase;">
            ARL SURA • CUIDADO Y PREVENCIÓN
        </div>
    </div>
    """
