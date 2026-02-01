import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from ui.styles import apply_custom_css
from ui.data_loader import (
    load_machines, get_daily_data, get_pareto_data, 
    get_trend_data, get_data_availability, load_articles_map
)
from ui.charts import (
    render_sparkline, create_timeline_chart, create_status_pie_chart,
    create_article_bar_chart, create_article_pie_chart, create_quality_charts,
    create_pareto_chart
)
from ui.pdf_export import generate_pdf_report
from src.pipeline import Pipeline

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="Operations Dashboard",
    page_icon="assets/page_icon.png",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Anchor for Back to Top at the very beginning
st.markdown("<div id='top' style='position:absolute; top:0;'></div>", unsafe_allow_html=True)

# Apply Styles
apply_custom_css()

# --- OLDALSÁV (SIDEBAR) ---
with st.sidebar:
    st.image(str(project_root / "assets" / "factory.png"), width=100)
    st.title("Vezérlőpult")
    st.markdown("---")
    
    # Adat elérhetőség lekérése
    min_date, max_date, total_events = get_data_availability()
    
    # Gép és dátum választás
    machines = load_machines()
    machine_options = {m.id: m.id for m in machines}
    selected_machine_id = st.selectbox("TERMELŐEGYSÉG", options=list(machine_options.keys()), 
                                      format_func=lambda x: machine_options[x], help="Válaszd ki az elemzendő papírgépet")
    
    selected_date = st.date_input("DÁTUM VÁLASZTÁS", value=max_date.date() if total_events > 0 else date.today() - timedelta(days=1))
        
    # Szinkronizáció
    if st.button("Adatok szinkronizálása", width="stretch"):
        with st.spinner(f"Adatok lekérése a kiválasztott napra ({selected_date})..."):
            try:
                pipeline = Pipeline()
                pipeline.run_full_load(target_date=selected_date)
                st.success("Sikeres szinkronizáció!")
            except Exception as e:
                st.error(f"Hiba történt: {str(e)}")

    # PDF Export Szekció
    if total_events > 0:
        st.markdown("---")
        st.subheader("Exportálás")
        try:
            pdf_events, pdf_summary, pdf_quality = get_daily_data(selected_machine_id, selected_date)
            pdf_article_names = load_articles_map()
            if pdf_events:
                pdf_buffer = generate_pdf_report(
                    selected_machine_id, 
                    selected_date, 
                    pdf_summary, 
                    pdf_events,
                    quality=pdf_quality,
                    article_names=pdf_article_names
                )
                st.download_button(
                    label="📄 Napi jelentés (PDF)",
                    data=pdf_buffer,
                    file_name=f"Report_{selected_machine_id}_{selected_date}.pdf",
                    mime="application/pdf",
                    width="stretch"
                )
            else:
                st.info("Nincs adat az exportáláshoz ezen a napon.")
        except Exception as e:
            st.error(f"PDF hiba: {str(e)}")

    st.markdown("---")
    with st.expander("Elérhető adatok"):
        if total_events > 0:
            st.caption(f"**Elérhető időszak:**  \n{min_date.strftime('%Y-%m-%d')} - {max_date.strftime('%Y-%m-%d')}")
            st.caption(f"**Események száma:** {total_events:,} db")
        else:
            st.warning("Az adatbázis még üres.")

# --- FŐOLDAL ---
# Automatikus görgetés a tetejére (időbélyeggel kényszerítve)
st.components.v1.html(
    f"""
    <script>
        /* RunID: {datetime.now().timestamp()} */
        setTimeout(function() {{
            window.parent.window.scrollTo({{ top: 0, behavior: 'smooth' }});
        }}, 300);
    </script>
    """,
    height=0
)

col_title, col_logo = st.columns([4, 1], gap="large")
with col_title:
    st.title(f"{machine_options[selected_machine_id]} Operations Dashboard")
    st.markdown(f"**Teljesítmény-analitikai dashboard** | {selected_date.strftime('%Y. %m. %d.')}")

article_names = load_articles_map()
events, summary, quality = get_daily_data(selected_machine_id, selected_date)
trend_summaries = get_trend_data(selected_machine_id, selected_date)

if not events:
    st.warning("Ezen a napon nem található adat. Használd az 'Adatok Szinkronizálása' gombot az oldalsávban.")
else:
    # --- 1. KPI SZEKCIÓ (FŐ MUTATÓK ÉS KÖZMŰVEK) ---
    if summary:
        k1, k2 = st.columns([0.05, 0.95])
        with k1: st.image("assets/oee.png", width=64)
        with k2: st.subheader("Napi teljesítménymutatók")

        col1, col2, col3, col4 = st.columns(4)
        
        # KPI 1: Termelés
        prod_delta_pct = (summary.total_tons / summary.target_tons - 1) * 100 if summary.target_tons and summary.target_tons > 0 else 0
        with col1:
            st.metric("TERMELÉS", f"{summary.total_tons:.1f} t", 
                    delta=f"{prod_delta_pct:.1f} %" if summary.target_tons else None,
                    help=f"A gép által termelt összes papír súlya (tonna).")
            st.plotly_chart(render_sparkline([s.total_tons for s in trend_summaries], "#2ecc71"), width="stretch", config={'displayModeBar': False})
        
        # KPI 2: OEE
        with col2:
            oee_formula = f"{summary.availability_pct:.1f}% (R) × {summary.performance_pct:.1f}% (T) × {summary.quality_pct:.1f}% (M)"
            st.metric("OEE MUTATÓ", f"{summary.oee_pct:.1f} %", 
                    help=f"Teljes eszközhatékonyság számítása:\n\n{oee_formula} = {summary.oee_pct:.1f}%\n\n"
                         f"R = Rendelkezésre állás\n"
                         f"T = Teljesítmény index\n"
                         f"M = Minőségi mutató")
            st.plotly_chart(render_sparkline([s.oee_pct for s in trend_summaries], "#3498db"), width="stretch", config={'displayModeBar': False})
        
        # KPI 3: Rendelkezésre állás
        with col3:
            st.metric("RENDELKEZÉSRE ÁLLÁS", f"{summary.availability_pct:.1f} %", help="A gép üzemidejének aránya a teljes naptári időhöz képest.")
            st.plotly_chart(render_sparkline([s.availability_pct for s in trend_summaries], "#9b59b6"), width="stretch", config={'displayModeBar': False})
        
        # KPI 4: Selejtarány
        scrap_rate = (summary.scrap_tons / summary.total_tons * 100) if summary.total_tons > 0 else 0
        with col4:
            st.metric("SELEJTARÁNY", f"{scrap_rate:.1f} %", help="A nem megfelelő minőségű termelés aránya az összes termeléshez képest.")
            trend_scraps = [(s.scrap_tons / s.total_tons * 100) if s.total_tons > 0 else 0 for s in trend_summaries]
            st.plotly_chart(render_sparkline(trend_scraps, "#e74c3c"), width="stretch", config={'displayModeBar': False})

        # Utilities
        u1, u2 = st.columns([0.05, 0.95])
        with u1: st.image("assets/power.png", width=64)
        with u2: st.subheader("Fajlagos erőforrás-felhasználás")

        u_col1, u_col2, u_col3, u_col4 = st.columns(4)
        u_col1.metric("VILLAMOS ENERGIA", f"{summary.spec_electricity_kwh_t:.0f} kWh/t", help="Fajlagos villamosenergia-felhasználás egy tonna késztermékre vetítve.")
        u_col2.metric("VÍZFELHASZNÁLÁS", f"{summary.spec_water_m3_t:.1f} m³/t", help="Fajlagos frissvíz-felhasználás egy tonna késztermékre vetítve.")
        u_col3.metric("GŐZFELHASZNÁLÁS", f"{summary.spec_steam_t_t:.2f} t/t", help="Fajlagos gőzfelhasználás egy tonna késztermékre vetítve.")
        u_col4.metric("ALAPANYAG (ROST)", f"{summary.spec_fiber_t_t:.2f} t/t", help="Fajlagos rostfelhasználás (Recovered Paper) egy tonna késztermékre vetítve.")
    
    st.divider()
    
    # --- 2. IDŐVONAL ÉS ESEMÉNYEK ---
    c1, c2 = st.columns([0.05, 0.95])
    with c1: st.image("assets/events.png", width=64)
    with c2: st.subheader("Termelési események")

    t_col1, t_col2 = st.columns([2, 1])
    with t_col1:
        raw_events = [
            {
                "Kezdet": e.timestamp,
                "Vége": e.timestamp + timedelta(seconds=e.duration_seconds if e.duration_seconds else 0),
                "Típus": e.event_type,
                "Állapot": e.status if e.event_type == "RUN" else e.event_type,
                "Termék": article_names.get(e.article_id, "Nincs gyártás") if e.article_id else "Nincs gyártás",
                "Gép": machine_options[selected_machine_id]
            } for e in events
        ]
        
        # Merge overlapping/adjacent events
        merged_events = []
        if raw_events:
            curr = raw_events[0].copy()
            for i in range(1, len(raw_events)):
                nxt = raw_events[i]
                if nxt["Állapot"] == curr["Állapot"] and nxt["Termék"] == curr["Termék"]:
                    curr["Vége"] = nxt["Vége"]
                else:
                    merged_events.append(curr)
                    curr = nxt.copy()
            merged_events.append(curr)
        
        df_events = pd.DataFrame(merged_events)
        if not df_events.empty:
            df_events["Időtartam_perc"] = (df_events["Vége"] - df_events["Kezdet"]).dt.total_seconds() / 60
            st.plotly_chart(create_timeline_chart(df_events, machine_options[selected_machine_id]), width="stretch")

    with t_col2:
        if not df_events.empty:
            df_states = df_events.groupby("Állapot")["Időtartam_perc"].sum().reset_index(name="Perc")
            st.plotly_chart(create_status_pie_chart(df_states), width="stretch")

    st.divider()

    # --- 3. TERMÉK STATISZTIKA ---
    s1, s2 = st.columns([0.05, 0.95])
    with s1: st.image("assets/layer.png", width=64)
    with s2: st.subheader("Termékstatisztika")
    
    df_prod = pd.DataFrame([
        {
            "Termék": article_names.get(e.article_id, "Ismeretlen") if e.article_id else "Ismeretlen",
            "Súly (kg)": e.weight_kg if e.weight_kg else 0,
            "Időtartam (perc)": (e.duration_seconds / 60) if e.duration_seconds else 0
        } for e in events if e.event_type == "RUN"
    ])
    
    if not df_prod.empty:
        article_mix = df_prod.groupby("Termék").agg({"Súly (kg)": "sum", "Időtartam (perc)": "sum"}).reset_index()
        article_mix["Tonna"] = article_mix["Súly (kg)"] / 1000
        pm_col1, pm_col2 = st.columns([2, 1])
        with pm_col1: st.plotly_chart(create_article_bar_chart(article_mix), width="stretch")
        with pm_col2: st.plotly_chart(create_article_pie_chart(article_mix), width="stretch")

    st.divider()

    # --- 4. MINŐSÉGI ANALÍTIKA ---
    q1, q2 = st.columns([0.05, 0.95])
    with q1: st.image("assets/flask.png", width=64)
    with q2: st.subheader("Minőségi analitika")
    
    if quality:
        df_q = pd.DataFrame([
            {
                "Idő": q.timestamp, "Nedvesség %": q.moisture_pct, 
                "Súly (GSM)": q.gsm_measured, "Szilárdság": q.strength_knm,
                "Termék": article_names.get(q.article_id, "Ismeretlen")
            } for q in quality
        ]).sort_values("Idő")
        st.plotly_chart(create_quality_charts(df_q), width="stretch")
    else:
        st.info("Nincsenek laboradatok ehhez az időszakhoz.")

    st.divider()

    # --- 5. TERMELÉSI ZAVAROK ---
    a1, a2 = st.columns([0.05, 0.95])
    with a1: st.image("assets/alert.png", width=64)
    with a2: st.subheader("Termelési zavarok")
    
    if summary:
        d_col1, d_col2 = st.columns([1, 2])
        d_col1.metric("ÖSSZES ÁLLÁSIDŐ", f"{summary.total_downtime_min:.0f} perc")
        d_col1.metric("SZAKADÁSSZÁM", f"{summary.break_count} db")
        
        pareto_df = get_pareto_data(selected_machine_id, selected_date)
        if not pareto_df.empty:
            with d_col2: st.plotly_chart(create_pareto_chart(pareto_df), width="stretch")
        else:
            d_col2.info("Nincs elég adat a Pareto elemzéshez.")

st.divider()
st.caption("Operations Dashboard | Kremzner Gábor 2026")
st.markdown("<a href='#top' class='back-to-top'>↑</a>", unsafe_allow_html=True)
