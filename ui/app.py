import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
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
    Machine, ProductionEvent, ProductionPlan, QualityMeasurement, UtilityData
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
def load_machines():
    with get_db() as db:
        db_machines = db.query(MachineDB).all()
        # Átalakítjuk Pydantic modellekké, így nem lesz DetachedInstanceError
        return [Machine.model_validate(m) for m in db_machines]

def get_daily_summary(machine_id, target_date):
    with get_db() as db:
        # Get events
        start_dt = datetime.combine(target_date, datetime.min.time())
        end_dt = datetime.combine(target_date, datetime.max.time())
        
        db_events = db.query(ProductionEventDB).filter(
            ProductionEventDB.machine_id == machine_id,
            ProductionEventDB.timestamp >= start_dt,
            ProductionEventDB.timestamp <= end_dt
        ).all()
        events = [ProductionEvent.model_validate(e) for e in db_events]
        
        # Get plans
        db_plan = db.query(ProductionPlanDB).filter(
            ProductionPlanDB.machine_id == machine_id,
            ProductionPlanDB.date == target_date
        ).first()
        plan = ProductionPlan.model_validate(db_plan) if db_plan else None
        
        # Get quality
        db_quality = db.query(QualityDataDB).filter(
            QualityDataDB.machine_id == machine_id,
            QualityDataDB.timestamp >= start_dt,
            QualityDataDB.timestamp <= end_dt
        ).all()
        quality = [QualityMeasurement.model_validate(q) for q in db_quality]

        # Get utilities
        db_utility = db.query(UtilityConsumptionDB).filter(
            UtilityConsumptionDB.machine_id == machine_id,
            UtilityConsumptionDB.date == target_date
        ).first()
        utility = UtilityData.model_validate(db_utility) if db_utility else None
        
        return events, plan, quality, utility

def get_pareto_data(machine_id, days=30):
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
            reason = s.description if s.description else "Unknown"
            duration = (s.duration_seconds / 60) if s.duration_seconds else 0
            data.append({"Reason": reason, "Duration (min)": duration})
            
        df = pd.DataFrame(data)
        pareto = df.groupby("Reason")["Duration (min)"].sum().reset_index()
        return pareto.sort_values(by="Duration (min)", ascending=False).head(5)


# --- SIDEBAR ---
with st.sidebar:
    st.image(str(project_root / "assets" / "factory.png"), width=100)
    st.title("Control Panel")
    st.markdown("---")
    
    # 1. Selection
    machines = load_machines()
    machine_options = {m.id: m.name for m in machines}
    selected_machine_id = st.selectbox("OPERATING UNIT", options=list(machine_options.keys()), format_func=lambda x: machine_options[x], help="Select the paper machine to analyze")
    
    selected_date = st.date_input("REPORTING DATE", value=date.today() - timedelta(days=1))
    
    st.divider()
    
    # 2. Sync Section
    if st.button("🚀 Sync Data", width="stretch"):
        with st.spinner(f"Fetching data for {selected_date}..."):
            try:
                pipeline = Pipeline()
                pipeline.run_full_load(target_date=selected_date)
                st.success("Sync Complete!")
                st.balloons()
            except Exception as e:
                st.error(f"Sync failed: {str(e)}")

# --- MAIN PAGE ---
col_title, col_logo = st.columns([4, 1])
with col_title:
    st.title(f"{machine_options[selected_machine_id]} - Intelligence")
    st.markdown(f"**Performance Analytics Dashboard** | {selected_date.strftime('%B %d, %Y')}")

events, plan, quality, utility = get_daily_summary(selected_machine_id, selected_date)

if not events:
    st.warning("No data found for this date. Please use the 'Sync Data' button in the sidebar.")
else:
    # 1. KPI SECTION (TABS)
    tab1, tab2, tab3 = st.tabs(["📊 Daily Performance", "⚡ Utilities & Fiber", "📉 Downtime Analysis"])
    
    with tab1:
        col1, col2, col3, col4 = st.columns(4)
        
        total_production = sum(e.weight_kg for e in events if e.event_type == "RUN") / 1000 # Tons
        scrap_production = sum(e.weight_kg for e in events if e.event_type == "RUN" and e.status == "SCRAP") / 1000
        
        run_events = [e for e in events if e.event_type == "RUN"]
        avg_speed = sum(e.average_speed for e in run_events) / len(run_events) if run_events else 0
        target_speed = plan.target_speed if plan else 0
        speed_util = (avg_speed / target_speed * 100) if target_speed > 0 else 0
        
        run_time = sum(e.duration_seconds for e in events if e.event_type == "RUN")
        total_time = sum(e.duration_seconds for e in events)
        time_util = (run_time / total_time * 100) if total_time > 0 else 0
        
        target_qty = plan.target_quantity_tons if plan else 0
        
        col1.metric("Production", f"{total_production:.1f} t", delta=f"{total_production - target_qty:.1f} t" if target_qty else None, help="Total weight of paper produced by the machine in metric tons.")
        col2.metric("Time Utilization", f"{time_util:.1f} %", help="Percentage of total time the machine was actively producing paper (OEE - Availability).")
        col3.metric("Speed Utilization", f"{speed_util:.1f} %", help="Actual average production speed compared to the target speed set in the plan.")
        col4.metric("Scrap Rate", f"{(scrap_production/total_production*100):.1f} %" if total_production > 0 else "0%", help="Ratio of non-conforming (scrap) production to total production.")

        # TIMELINE CHART
        st.subheader("Daily Production Timeline")
        df_events = pd.DataFrame([
            {
                "Start": e.timestamp,
                "End": e.timestamp + timedelta(seconds=e.duration_seconds if e.duration_seconds else 0),
                "Type": e.event_type,
                "Status": e.status if e.event_type == "RUN" else e.event_type,
                "Machine": machine_options[selected_machine_id]
            } for e in events
        ])
        
        fig_timeline = px.timeline(
            df_events, 
            x_start="Start", 
            x_end="End", 
            y="Machine", 
            color="Status",
            color_discrete_map={
                "GOOD": "#2ecc71", 
                "SCRAP": "#e67e22", 
                "STOP": "#e74c3c", 
                "BREAK": "#f1c40f"
            },
            category_orders={"Status": ["GOOD", "SCRAP", "STOP", "BREAK"]},
            height=250 # Kicsit magasabb, hogy legyen helye
        )
        
        fig_timeline.update_yaxes(title="", showgrid=False, zeroline=False)
        fig_timeline.update_xaxes(showgrid=True, gridcolor='rgba(0,0,0,0.05)')
        fig_timeline.update_layout(
            template=PLOTLY_THEME,
            showlegend=True,
            legend_title_text="",
            margin=dict(t=0, b=0, l=0, r=0),
            legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="left", x=0),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )
        st.plotly_chart(fig_timeline, width="stretch")

        # 3. QUALITY & DETAILS
        c1, c2 = st.columns([2, 1])
        with c1:
            if quality:
                df_q = pd.DataFrame([
                    {"Time": q.timestamp, "Moisture %": q.moisture_pct, "GSM": q.gsm_measured, "Strength": q.strength_knm} 
                    for q in quality
                ]).sort_values("Time")
                
                from plotly.subplots import make_subplots
                
                # Setup 3 subplots (vertical)
                fig_q = make_subplots(
                    rows=3, cols=1, 
                    shared_xaxes=True,
                    vertical_spacing=0.05,
                    subplot_titles=("Grammage (GSM)", "Strength (kNm)", "Moisture %")
                )
                
                # 1. GSM
                fig_q.add_trace(go.Scatter(
                    x=df_q["Time"], y=df_q["GSM"],
                    name="GSM", mode="lines+markers",
                    line=dict(color="#3498db")
                ), row=1, col=1)
                
                # 2. Strength
                fig_q.add_trace(go.Scatter(
                    x=df_q["Time"], y=df_q["Strength"],
                    name="Strength", mode="lines+markers",
                    line=dict(color="#2ecc71")
                ), row=2, col=1)
                
                # 3. Moisture
                fig_q.add_trace(go.Scatter(
                    x=df_q["Time"], y=df_q["Moisture %"],
                    name="Moisture", mode="lines+markers",
                    line=dict(color="#e74c3c")
                ), row=3, col=1)
                
                fig_q.update_layout(
                    height=600,
                    template=PLOTLY_THEME,
                    showlegend=False,
                    margin=dict(t=60, b=40, l=40, r=40),
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Inter, sans-serif")
                )
                
                # Update axes
                fig_q.update_xaxes(showgrid=True, gridcolor='rgba(0,0,0,0.05)')
                fig_q.update_yaxes(showgrid=True, gridcolor='rgba(0,0,0,0.05)', autorange=True, fixedrange=False)
                
                st.plotly_chart(fig_q, width="stretch")
            else:
                st.info("No quality data for this day.")
        with c2:
            df_states = df_events.groupby("Status").size().reset_index(name="Count")
            fig_pie = px.pie(
                df_states, values="Count", names="Status", 
                hole=0.6, 
                color="Status",
                color_discrete_map={"GOOD": "#2ecc71", "SCRAP": "#e67e22", "STOP": "#e74c3c", "BREAK": "#f1c40f"},
                template=PLOTLY_THEME
            )
            fig_pie.update_layout(
                margin=dict(t=40, b=0, l=0, r=0),
                showlegend=False,
                annotations=[dict(text='Distribution', x=0.5, y=0.5, font_size=14, showarrow=False, font_family="Inter")],
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
            )
            st.plotly_chart(fig_pie, width="stretch")

    with tab2:
        st.subheader("Specific Consumption (Per Ton)")
        if utility and total_production > 0:
            u_col1, u_col2, u_col3, u_col4 = st.columns(4)
            u_col1.metric("⚡ Electricity", f"{utility.electricity_kwh / total_production:.1f} kWh/t", help="Total electrical energy consumed per metric ton of paper produced.")
            u_col2.metric("💧 Water", f"{utility.water_m3 / total_production:.1f} m³/t", help="Fresh water consumption per metric ton of paper produced.")
            u_col3.metric("💨 Steam", f"{utility.steam_tons / total_production:.1f} t/t", help="Steam energy used for drying per metric ton of paper produced.")
            u_col4.metric("♻️ Recovered Paper", f"{utility.fiber_tons / total_production:.2f} t/t", help="Amount of waste paper (recovered fiber) used per metric ton of finished product.")
            
            st.divider()
            st.subheader("Additive Usage")
            st.info(f"Total additives consumed: {utility.additives_kg:.1f} kg")
        else:
            st.warning("Utility data or production records missing for this date.")

    with tab3:
        st.subheader("Top 5 Downtime Reasons (Last 30 Days)")
        pareto_df = get_pareto_data(selected_machine_id)
        if not pareto_df.empty:
            fig_pareto = px.bar(
                pareto_df, x="Reason", y="Duration (min)", 
                color="Reason",
                template=PLOTLY_THEME,
                color_discrete_sequence=COLOR_PALETTE
            )
            fig_pareto.update_layout(
                margin=dict(t=20, b=20, l=0, r=0),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                showlegend=False
            )
            st.plotly_chart(fig_pareto, width="stretch")
        else:
            st.info("Not enough data for Pareto analysis yet.")

st.divider()
st.caption("Production Report System v1.0 | Academic Project 2026")
