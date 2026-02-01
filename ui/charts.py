import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# Plotly Theme
PLOTLY_THEME = "plotly_white"
COLOR_PALETTE = ["#0d6efd", "#6610f2", "#6f42c1", "#d63384", "#dc3545", "#fd7e14", "#ffc107", "#198754", "#20c997", "#0dcaf0"]

def render_sparkline(values, color="#0d6efd"):
    """Létrehoz egy apró trendvonalat (sparkline)."""
    if not values or len(values) < 2:
        return None
        
    fig = px.line(y=values, template="plotly_white")
    fig.update_traces(line=dict(color=color, width=3), hoverinfo="skip")
    fig.update_layout(
        showlegend=False,
        margin=dict(t=5, b=5, l=0, r=0),
        height=40,
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig

def create_timeline_chart(df_events, machine_name: str):
    """Létrehozza a napi termelési idővonal grafikonját."""
    fig = px.timeline(
        df_events, 
        x_start="Kezdet", 
        x_end="Vége", 
        y="Gép", 
        color="Állapot",
        hover_name="Termék",
        hover_data={
            "Állapot": True,
            "Kezdet": "|%H:%M",
            "Vége": "|%H:%M",
            "Gép": False,
            "Termék": False
        },
        color_discrete_map={
            "GOOD": "#2ecc71", 
            "SCRAP": "#e67e22", 
            "STOP": "#e74c3c", 
            "BREAK": "#f1c40f"
        },
        category_orders={"Állapot": ["GOOD", "SCRAP", "STOP", "BREAK"]},
        height=200 
    )
    
    fig.update_yaxes(visible=False)
    fig.update_xaxes(showgrid=True, gridcolor='rgba(0,0,0,0.05)')
    fig.update_layout(
        template=PLOTLY_THEME,
        showlegend=True,
        legend_title_text="",
        margin=dict(t=30, b=0, l=0, r=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="left", x=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif")
    )
    return fig

def create_status_pie_chart(df_states):
    """Létrehozza a gépállapot eloszlás kördiagramját."""
    fig = px.pie(
        df_states, values="Perc", names="Állapot", 
        hole=0.6, 
        color="Állapot",
        color_discrete_map={"GOOD": "#2ecc71", "SCRAP": "#e67e22", "STOP": "#e74c3c", "BREAK": "#f1c40f"},
        template=PLOTLY_THEME,
        height=250
    )
    fig.update_layout(
        margin=dict(t=0, b=0, l=0, r=0),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig

def create_article_bar_chart(article_mix):
    """Létrehozza a termékmennyiség oszlopdiagramját."""
    fig = px.bar(
        article_mix, x="Tonna", y="Termék", 
        orientation="h",
        text_auto='.1f',
        title="Mennyiség termékenként (tonna)",
        color="Termék",
        template=PLOTLY_THEME,
        color_discrete_sequence=COLOR_PALETTE,
        height=250
    )
    fig.update_layout(
        showlegend=False, 
        xaxis_title="",
        yaxis_title="",
        margin=dict(t=40, b=0, l=0, r=0),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig

def create_article_pie_chart(article_mix):
    """Létrehozza a termék futásidő eloszlás kördiagramját."""
    fig = px.pie(
        article_mix, values="Időtartam (perc)", names="Termék",
        hole=0.6,
        title="Futásidő megoszlás",
        template=PLOTLY_THEME,
        color_discrete_sequence=COLOR_PALETTE,
        height=250
    )
    fig.update_layout(
        showlegend=True, 
        margin=dict(t=40, b=0, l=0, r=0),
        legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="center", x=0.5),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )
    return fig

def create_quality_charts(df_q):
    """Létrehozza a minőségi trendek összetett grafikonját."""
    fig_q = make_subplots(
        rows=3, cols=1, 
        shared_xaxes=True,
        vertical_spacing=0.07,
        subplot_titles=("Grammsúly (GSM)", "Szakítószilárdság (kNm)", "Nedvesség %")
    )
    
    # 1. GSM
    fig_q.add_trace(go.Scatter(
        x=df_q["Idő"], y=df_q["Súly (GSM)"], 
        name="GSM", mode="lines+markers",
        line=dict(color="#3498db"),
        customdata=df_q["Termék"],
        hovertemplate="<b>Idő: %{x}</b><br>GSM: %{y:.1f}<br>Termék: %{customdata}<extra></extra>"
    ), row=1, col=1)
    
    # 2. Szilárdság
    fig_q.add_trace(go.Scatter(
        x=df_q["Idő"], y=df_q["Szilárdság"], 
        name="Szilárdság", mode="lines+markers",
        line=dict(color="#2ecc71"),
        customdata=df_q["Termék"],
        hovertemplate="<b>Idő: %{x}</b><br>Knm: %{y:.1f}<br>Termék: %{customdata}<extra></extra>"
    ), row=2, col=1)
    
    # 3. Nedvesség
    fig_q.add_trace(go.Scatter(
        x=df_q["Idő"], y=df_q["Nedvesség %"], 
        name="Nedvesség", mode="lines+markers",
        line=dict(color="#e74c3c"),
        customdata=df_q["Termék"],
        hovertemplate="<b>Idő: %{x}</b><br>Nedvesség %: %{y:.1f}<br>Termék: %{customdata}<extra></extra>"
    ), row=3, col=1)
    
    fig_q.update_layout(
        height=500, 
        template=PLOTLY_THEME, 
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.4, xanchor="center", x=0.5),
        margin=dict(t=60, b=120, l=40, r=40)
    )
    fig_q.update_xaxes(showgrid=True, gridcolor='rgba(0,0,0,0.05)')
    fig_q.update_yaxes(showgrid=True, gridcolor='rgba(0,0,0,0.05)', autorange=True)
    return fig_q

def create_pareto_chart(pareto_df):
    """Létrehozza a leállási okok Pareto diagramját."""
    fig = px.bar(
        pareto_df, x="Ok", y="Időtartam (perc)", 
        title="Leggyakoribb leállási okok (30 nap)", 
        color="Ok", template=PLOTLY_THEME, height=300
    )
    fig.update_layout(showlegend=False, margin=dict(t=40, b=0, l=0, r=0))
    return fig
