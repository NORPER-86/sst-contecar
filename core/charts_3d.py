"""
Módulo de Visualizaciones 3D Interactivas para el Tablero BI (CONTECAR / SPRC - SURA).
Encapsula la construcción de Cubos Espaciales 3D y Topografías de Riesgo mediante Plotly WebGL.
"""

from typing import Optional, List, Dict, Any
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

from core.branding import (
    SURA_BLUE, SURA_CYAN, SURA_YELLOW, SURA_NAVY_DARK, CATEGORY_PALETTE
)


def build_3d_spatial_cube(df_3d: pd.DataFrame) -> Optional[go.Figure]:
    """
    Construye un Cubo Espacial 3D (go.Scatter3d) con postes verticales y esferas
    volumétricas codificadas con la paleta oficial SURA.
    """
    if df_3d.empty or len(df_3d) < 1:
        return None

    df_plot = df_3d.copy()
    df_plot["pcp_num"] = pd.to_numeric(df_plot["pcp_calculado"], errors="coerce").fillna(0)

    traces_3d = []

    # 1. Postes / Stem lines 3D verticales hacia el plano base
    x_stems: List[Any] = []
    y_stems: List[Any] = []
    z_stems: List[Any] = []
    for _, r_item in df_plot.iterrows():
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

    # 2. Esferas volumétricas 3D con colores oficiales de categoría SURA
    colors_3d = [CATEGORY_PALETTE.get(c, {}).get("color", SURA_BLUE) for c in df_plot["categoria"]]
    hover_texts = [
        f"<b>Área:</b> {r_item['area']}<br>"
        f"<b>Empresa:</b> {r_item['empresa_ejecutante']}<br>"
        f"<b>% PCP:</b> {r_item['pcp_num']:.1f}%<br>"
        f"<b>Categoría:</b> {r_item['categoria']}<br>"
        f"<b>Observador:</b> {r_item.get('observador', 'N/A')}"
        for _, r_item in df_plot.iterrows()
    ]

    traces_3d.append(go.Scatter3d(
        x=df_plot["area"],
        y=df_plot["empresa_ejecutante"],
        z=df_plot["pcp_num"],
        mode="markers+text",
        text=[f"{val:.0f}%" for val in df_plot["pcp_num"]],
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

    fig = go.Figure(data=traces_3d)
    fig.update_layout(
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
    return fig


def build_3d_risk_topography(df_filtered: pd.DataFrame) -> Optional[go.Figure]:
    """
    Construye una superficie 3D (go.Surface) o gráfico de barras tridimensional
    que refleja la concentración de observaciones por Área vs Categoría SURA.
    """
    if df_filtered.empty or "area" not in df_filtered or "categoria" not in df_filtered:
        return None

    ct = pd.crosstab(df_filtered["area"], df_filtered["categoria"])
    if not ct.empty and len(ct.index) >= 2 and len(ct.columns) >= 2:
        fig = go.Figure(data=[go.Surface(
            z=ct.values,
            x=ct.columns.tolist(),
            y=ct.index.tolist(),
            colorscale=[[0, "#E0F2FE"], [0.5, "#00AEC7"], [1, "#0033A0"]],
            opacity=0.94,
            contours=dict(z=dict(show=True, usecolormap=True, project_z=True))
        )])
        fig.update_layout(
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
        return fig
    else:
        # Respaldo visual 3D para matrices con pocas dimensiones
        counts_df = df_filtered["area"].value_counts().reset_index()
        counts_df.columns = ["area", "count"]
        fig_bar = px.bar(
            counts_df,
            x="area", y="count", color="area",
            color_discrete_sequence=[SURA_BLUE, SURA_CYAN, SURA_YELLOW, SURA_NAVY_DARK]
        )
        fig_bar.update_layout(height=440, showlegend=False)
        return fig_bar
