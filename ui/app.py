import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import func
from datetime import datetime, timedelta, date
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from src.database import get_db
from src.models import (
    MachineDB, ArticleDB, ProductionEventDB, 
    ProductionPlanDB, QualityDataDB, UtilityConsumptionDB,
    DailySummaryDB,
    Machine, ProductionEvent, ProductionPlan, QualityMeasurement, UtilityData,
    DailySummary
)
from src.pipeline import Pipeline

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Production Report System",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS STYLING ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .main {
        background-color: #f8f9fa;
    }
    
    /* GLASSMORPHISM CARD */
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.9);
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.3);
        padding: 20px;
        border-radius: 20px;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.07);
        transition: all 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    }
    
    div[data-testid="stMetric"]:hover {
        transform: translateY(-8px);
        box-shadow: 0 12px 40px 0 rgba(31, 38, 135, 0.12);
    }

    [data-testid="stMetricLabel"] {
        font-weight: 600 !important;
        color: #6c757d !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        font-size: 0.8rem !important;
    }

    [data-testid="stMetricValue"] {
        font-weight: 700 !important;
        color: #212529 !important;
        font-size: 2.2rem !important;
    }

    /* SIDEBAR */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e9ecef;
    }

    /* TABS */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        background-color: transparent;
    }

    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px 4px 0px 0px;
        color: #495057;
        font-weight: 600;
        border-bottom: 2px solid transparent;
        transition: all 0.2s;
    }

    .stTabs [aria-selected="true"] {
        color: #0d6efd !important;
        border-bottom: 2px solid #0d6efd !important;
    }
</style>
""", unsafe_allow_html=True)

# Plotly Theme
PLOTLY_THEME = "plotly_white"
COLOR_PALETTE = ["#0d6efd", "#6610f2", "#6f42c1", "#d63384", "#dc3545", "#fd7e14", "#ffc107", "#198754", "#20c997", "#0dcaf0"]

# --- DATA HELPERS ---
def load_articles() -> Dict[str, str]:
    """Betölti a termék törzsadatokat az adatbázisból."""
    with get_db() as db:
        db_articles = db.query(ArticleDB).all()
        return {a.id: a.name for a in db_articles}

def load_machines() -> List[Machine]:
    """Betölti a gép törzsadatokat és Pydantic modellekké alakítja őket."""
    with get_db() as db:
        db_machines = db.query(MachineDB).all()
        return [Machine.model_validate(m) for m in db_machines]

def get_daily_data(machine_id: str, target_date: date):
    """Lekéri a nyers eseményeket és az előre kalkulált napi összesítőt is."""
    with get_db() as db:
        start_dt = datetime.combine(target_date, datetime.min.time())
        end_dt = datetime.combine(target_date, datetime.max.time())
        
        # 1. Nyers események (idővonalhoz és lebontáshoz)
        db_events = db.query(ProductionEventDB).filter(
            ProductionEventDB.machine_id == machine_id,
            ProductionEventDB.timestamp >= start_dt,
            ProductionEventDB.timestamp <= end_dt
        ).all()
        events = [ProductionEvent.model_validate(e) for e in db_events]
        
        # 2. Előre kalkulált napi összesítő
        db_summary = db.query(DailySummaryDB).filter(
            DailySummaryDB.machine_id == machine_id,
            DailySummaryDB.date == target_date
        ).first()
        summary = DailySummary.model_validate(db_summary) if db_summary else None
        
        # 3. Minőségi adatok (grafikonokhoz)
        db_quality = db.query(QualityDataDB).filter(
            QualityDataDB.machine_id == machine_id,
            QualityDataDB.timestamp >= start_dt,
            QualityDataDB.timestamp <= end_dt
        ).all()
        quality = [QualityMeasurement.model_validate(q) for q in db_quality]

        return events, summary, quality

def get_pareto_data(machine_id: str, days: int = 30) -> pd.DataFrame:
    """Lekéri az elmúlt X nap leállási okait Pareto elemzéshez."""
    with get_db() as db:
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        stops = db.query(ProductionEventDB).filter(
            ProductionEventDB.machine_id == machine_id,
            ProductionEventDB.event_type.in_(["STOP", "BREAK"]),
            ProductionEventDB.timestamp >= datetime.combine(start_date, datetime.min.time())
        ).all()
        
        if not stops:
            return pd.DataFrame()
            
        data = []
        for s in stops:
            reason = s.description if s.description else "Ismeretlen"
            duration = (s.duration_seconds / 60) if s.duration_seconds else 0
            data.append({"Ok": reason, "Időtartam (perc)": duration})
            
        df = pd.DataFrame(data)
        pareto = df.groupby("Ok")["Időtartam (perc)"].sum().reset_index()
        return pareto.sort_values(by="Időtartam (perc)", ascending=False).head(5)


# --- ADAT SEGÉDFÜGGVÉNYEK ---
def get_data_availability():
    """Lekéri az adatbázisból az elérhető dátumtartományt."""
    with get_db() as db:
        res = db.query(
            func.min(ProductionEventDB.timestamp),
            func.max(ProductionEventDB.timestamp),
            func.count(ProductionEventDB.id)
        ).first()
        return res

# --- OLDALSÁV (SIDEBAR) ---
with st.sidebar:
    st.image(str(project_root / "assets" / "factory.png"), width=100)
    st.title("Vezérlőpult")
    st.markdown("---")
    
    # 1. Adat Elérhetőség Infó
    min_date, max_date, total_events = get_data_availability()
    if total_events > 0:
        st.info(f"**Elérhető adatok:**\n\n{min_date.strftime('%Y-%m-%d')} — {max_date.strftime('%Y-%m-%d')}")
    else:
        st.warning("⚠️ Az adatbázis üres!")

    st.markdown("---")
    
    # 2. Gép és dátum választás
    machines = load_machines()
    machine_options = {m.id: m.id for m in machines}
    selected_machine_id = st.selectbox("TERMELŐEGYSÉG", options=list(machine_options.keys()), format_func=lambda x: machine_options[x], help="Válaszd ki az elemzendő papírgépet")
    
    selected_date = st.date_input("JELENTÉS DÁTUMA", value=max_date.date() if total_events > 0 else date.today() - timedelta(days=1))
    
    st.divider()
    
    # 3. Szinkronizáció
    if st.button("🚀 Adatok Szinkronizálása", width="stretch"):
        with st.spinner(f"Adatok lekérése a kiválasztott napra ({selected_date})..."):
            try:
                pipeline = Pipeline()
                pipeline.run_full_load(target_date=selected_date)
                st.success("Sikeres szinkronizáció!")
                st.balloons()
            except Exception as e:
                st.error(f"Hiba történt: {str(e)}")

# --- FŐOLDAL ---
col_title, col_logo = st.columns([4, 1])
with col_title:
    st.title(f"{machine_options[selected_machine_id]} Jelentés")
    st.markdown(f"**Teljesítmény-analitikai Dashboard** | {selected_date.strftime('%Y. %m. %d.')}")

events, summary, quality = get_daily_data(selected_machine_id, selected_date)

if not events:
    st.warning("Ezen a napon nem található adat. Használd az 'Adatok Szinkronizálása' gombot az oldalsávban.")
else:
    # --- 1. KPI SZEKCIÓ (FŐ MUTATÓK ÉS KÖZMŰVEK) ---
    if summary:
        # Felső sor: Termelési KPI-ok
        col1, col2, col3, col4 = st.columns(4)
        prod_delta_pct = (summary.total_tons / summary.target_tons - 1) * 100 if summary.target_tons and summary.target_tons > 0 else 0
        col1.metric("Termelés", f"{summary.total_tons:.1f} t", 
                  delta=f"{prod_delta_pct:.1f} %" if summary.target_tons else None,
                  help=f"A gép által termelt összes papír súlya (nettó tonna).\n\nNapi adatok:\n- Összes: {summary.total_tons:.1f} t\n- Jó termék: {summary.good_tons:.1f} t\n- Selejt: {summary.scrap_tons:.1f} t\n(Cél: {summary.target_tons:.1f} t)")
        
        col2.metric("OEE Állapot", f"{summary.oee_pct:.1f} %", 
                  help=f"Teljes Eszközhatékonyság (Overall Equipment Effectiveness).\n\nÖsszetevők:\n- Rendelkezésre állás: {summary.availability_pct}%\n- Teljesítmény: {summary.performance_pct}%\n- Minőség: {summary.quality_pct}%")
        
        speed_eff = (summary.avg_speed_m_min / summary.target_speed_m_min * 100) if summary.target_speed_m_min and summary.target_speed_m_min > 0 else 0
        col3.metric("Sebesség index", f"{speed_eff:.1f} %",
                  help=f"A gép sebességének hatékonysága a tervhez képest.\n\nTényleges: {summary.avg_speed_m_min:.0f} m/min\nTerv: {summary.target_speed_m_min:.0f} m/min")
        
        scrap_rate = (summary.scrap_tons / summary.total_tons * 100) if summary.total_tons > 0 else 0
        col4.metric("Selejtarány", f"{scrap_rate:.1f} %", 
                  help=f"A nem megfelelő minőségű termelés aránya az összes termeléshez képest.\n\nTechnikai adatok:\n- Összes selejt: {summary.scrap_tons:.1f} t\n- Összes termelés: {summary.total_tons:.1f} t")

        # Második sor: Fajlagos mutatók (Utilities)
        u_col1, u_col2, u_col3, u_col4 = st.columns(4)
        
        # Abszolút értékek visszaszámolása a fajlagosból
        total_elec = summary.spec_electricity_kwh_t * summary.total_tons
        u_col1.metric("⚡ Áram", f"{summary.spec_electricity_kwh_t:.0f} kWh/t", 
                  help=f"Átlagos elektromos energia fogyasztás 1 tonna termékre vetítve.\n\nÖsszes fogyasztás: {total_elec:,.0f} kWh")
        
        total_water = summary.spec_water_m3_t * summary.total_tons
        u_col2.metric("💧 Víz", f"{summary.spec_water_m3_t:.1f} m³/t", 
                  help=f"Frissvíz felhasználás 1 tonna termékre vetítve.\n\nÖsszes fogyasztás: {total_water:,.0f} m³")
        
        total_steam = summary.spec_steam_t_t * summary.total_tons
        u_col3.metric("💨 Gőz", f"{summary.spec_steam_t_t:.2f} t/t", 
                  help=f"Gőzfelhasználás a szárításhoz 1 tonna termékre vetítve.\n\nÖsszes fogyasztás: {total_steam:.1f} t")
        
        total_fiber = summary.spec_fiber_t_t * summary.total_tons
        u_col4.metric("♻️ Rost", f"{summary.spec_fiber_t_t:.2f} t/t", 
                  help=f"Felhasznált papírrost mennyisége 1 tonna késztermékre.\n\nÖsszes felhasználás: {total_fiber:.1f} t")
    else:
        st.info("A napi összesítés még nincs kiszámolva.")
        total_production = sum(e.weight_kg for e in events if e.event_type == "RUN") / 1000
        st.metric("Termelés (Nyers adat)", f"{total_production:.1f} t")
    
    st.divider()
    st.markdown("### Termelési események")

    # --- IDŐVONAL ÉS GÉPÁLLAPOT ELOSZLÁS ---
    t_col1, t_col2 = st.columns([2, 1])
    
    with t_col1:
        raw_events = [
            {
                "Kezdet": e.timestamp,
                "Vége": e.timestamp + timedelta(seconds=e.duration_seconds if e.duration_seconds else 0),
                "Típus": e.event_type,
                "Állapot": e.status if e.event_type == "RUN" else e.event_type,
                "Termék": e.article_id if e.article_id else "Nincs gyártás",
                "Gép": machine_options[selected_machine_id]
            } for e in events
        ]
        
        # --- ÖSSZEOLVASZTÁSI LOGIKA (Gépállapothoz és Termékhez) ---
        merged_status_events = []
        if raw_events:
            current = raw_events[0].copy()
            for i in range(1, len(raw_events)):
                nxt = raw_events[i]
                # Csak akkor olvasztunk össze, ha az állapot ÉS a termék is ugyanaz
                if nxt["Állapot"] == current["Állapot"] and nxt["Termék"] == current["Termék"]:
                    current["Vége"] = nxt["Vége"]
                else:
                    merged_status_events.append(current)
                    current = nxt.copy()
            merged_status_events.append(current)
        
        df_events = pd.DataFrame(merged_status_events)
        if not df_events.empty:
            df_events["Időtartam_perc"] = (df_events["Vége"] - df_events["Kezdet"]).dt.total_seconds() / 60
        
        st.markdown("**Napi Termelési Idővonal**")
        fig_timeline = px.timeline(
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
            height=300 
        )
        
        fig_timeline.update_yaxes(visible=False)
        fig_timeline.update_xaxes(showgrid=True, gridcolor='rgba(0,0,0,0.05)')
        fig_timeline.update_layout(
            template=PLOTLY_THEME,
            showlegend=True,
            legend_title_text="",
            margin=dict(t=30, b=0, l=0, r=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="left", x=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif")
        )
        st.plotly_chart(fig_timeline, use_container_width=True)

    with t_col2:
        st.markdown("**Gépállapot Eloszlás (időben)**")
        df_states = df_events.groupby("Állapot")["Időtartam_perc"].sum().reset_index(name="Perc")
        fig_pie_status = px.pie(
            df_states, values="Perc", names="Állapot", 
            hole=0.6, 
            color="Állapot",
            color_discrete_map={"GOOD": "#2ecc71", "SCRAP": "#e67e22", "STOP": "#e74c3c", "BREAK": "#f1c40f"},
            template=PLOTLY_THEME,
            height=320
        )
        fig_pie_status.update_layout(
            margin=dict(t=0, b=0, l=0, r=0),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
            annotations=[dict(text='Megoszlás', x=0.5, y=0.5, font_size=12, showarrow=False, font_family="Inter")],
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_pie_status, use_container_width=True)

    st.divider()

    # 2. TERMÉK STATISZTIKA
    st.markdown("### Termékstatisztika")
    df_prod = pd.DataFrame([
        {
            "Termék": e.article_id if e.article_id else "Ismeretlen",
            "Súly (kg)": e.weight_kg if e.weight_kg else 0,
            "Időtartam (perc)": (e.duration_seconds / 60) if e.duration_seconds else 0,
            "Állapot": e.status
        } for e in events if e.event_type == "RUN"
    ])
    
    if not df_prod.empty:
        # Csoportosítás termék szerint
        article_mix = df_prod.groupby("Termék").agg({
            "Súly (kg)": "sum",
            "Időtartam (perc)": "sum"
        }).reset_index()
        # Tonna konverzió
        article_mix["Tonna"] = article_mix["Súly (kg)"] / 1000
        
        pm_col1, pm_col2 = st.columns([2, 1])
        with pm_col1:
            fig_mix = px.bar(
                article_mix, x="Termék", y="Tonna", 
                text_auto='.1f',
                title="Mennyiség Termékenként (Tonna)",
                color="Termék",
                template=PLOTLY_THEME,
                color_discrete_sequence=COLOR_PALETTE
            )
            fig_mix.update_layout(
                showlegend=False, 
                margin=dict(t=40, b=0, l=0, r=0),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_mix, width="stretch")
        
        with pm_col2:
            fig_time_mix = px.pie(
                article_mix, values="Időtartam (perc)", names="Termék",
                hole=0.4,
                title="Futásidő Megoszlás",
                template=PLOTLY_THEME,
                color_discrete_sequence=COLOR_PALETTE
            )
            fig_time_mix.update_layout(
                showlegend=True, 
                margin=dict(t=40, b=0, l=0, r=0),
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_time_mix, width="stretch")
    else:
        st.info("Ezen a napon nem rögzítettek termelési (RUN) eseményt.")

    st.divider()

    # --- 4. MINŐSÉGI TRENDEK (TRENDS) ---
    st.markdown("### Minőségi analitika")
    if quality:
        df_q = pd.DataFrame([
            {
                "Idő": q.timestamp, 
                "Nedvesség %": q.moisture_pct, 
                "Súly (GSM)": q.gsm_measured, 
                "Szilárdság": q.strength_knm,
                "Termék": q.article_id
            } 
            for q in quality
        ]).sort_values("Idő")
        
        from plotly.subplots import make_subplots
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
            height=650, 
            template=PLOTLY_THEME, 
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.1, xanchor="center", x=0.5),
            margin=dict(t=60, b=100, l=40, r=40)
        )
        fig_q.update_xaxes(showgrid=True, gridcolor='rgba(0,0,0,0.05)')
        fig_q.update_yaxes(showgrid=True, gridcolor='rgba(0,0,0,0.05)', autorange=True)
        st.plotly_chart(fig_q, use_container_width=True)
    else:
        st.info("Nincsenek laboradatok ehhez az időszakhoz.")

    st.divider()

    # --- 5. LEÁLLÁS ANALÍZIS (DOWNTIME) ---
    st.markdown("### Termelési zavarok")
    if summary:
        d_col1, d_col2 = st.columns([1, 2])
        with d_col1:
            st.metric("⏱️ Összes Állásidő", f"{summary.total_downtime_min:.0f} perc")
            st.metric("✂️ Szakadásszám", f"{summary.break_count} db")
        
        with d_col2:
            pareto_df = get_pareto_data(selected_machine_id)
            if not pareto_df.empty:
                fig_pareto = px.bar(
                    pareto_df, x="Ok", y="Időtartam (perc)", 
                    title="Leggyakoribb Leállási Okok (30 nap)", 
                    color="Ok", template=PLOTLY_THEME, height=300
                )
                fig_pareto.update_layout(showlegend=False, margin=dict(t=40, b=0, l=0, r=0))
                st.plotly_chart(fig_pareto, use_container_width=True)
            else:
                st.info("Nincs elég adat a Pareto elemzéshez.")
    else:
        st.info("Az összesítés hiányában a leállási statisztika nem elérhető.")

st.divider()
st.caption("Termelési Jelentési Rendszer v1.0 | Kremzner Gábor 2026")
