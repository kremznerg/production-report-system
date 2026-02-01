"""
ECOPAPER SOLUTIONS - OPERATIONS DASHBOARD
==========================================
Ez a fő belépési pontja a Streamlit alkalmazásnak. 
Felelős a felhasználói felület (UI) megjelenítéséért, az adatok 
vizualizációjáért és az interaktív funkciók (szűrés, exportálás) kezeléséért.

Szerző: Kremzner Gábor (2026)
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
from pathlib import Path
import sys

# Projekt gyökérkönyvtár hozzáadása az elérési úthoz
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

# --- KONFIGURÁCIÓ ÉS STÍLUS ---
st.set_page_config(
    page_title="EPS Dashboard",
    page_icon="assets/logo.jpeg",
    layout="wide",
    initial_sidebar_state="expanded"
)

# "Vissza a tetejére" horgony
st.markdown("<div id='top' style='position:absolute; top:0;'></div>", unsafe_allow_html=True)

# Egyedi CSS alkalmazása
apply_custom_css()

def render_sidebar():
    """Az oldalsáv (sidebar) tartalmának felépítése."""
    with st.sidebar:
        # Logó középre igazítása és méretének finomhangolása (hogy ne legyen túl nagy/pixeles)
        c1, c2, c3 = st.columns([1, 6, 1])
        with c2:
            st.image("assets/logo.jpeg", use_container_width=True)
        st.title("Vezérlőpult")
        st.markdown("---")
        
        # Adat elérhetőség lekérése
        min_date, max_date, total_events = get_data_availability()
        
        # Gép választás
        machines = load_machines()
        machine_options = {m.id: m.id for m in machines}
        
        if not machines:
            st.error("Nincsenek gépek az adatbázisban!")
            st.stop()

        selected_machine_id = st.selectbox(
            "TERMELŐEGYSÉG", 
            options=list(machine_options.keys()), 
            format_func=lambda x: machine_options[x], 
            help="Válaszd ki az elemzendő papírgépet"
        )
        
        # Dátum választás (None check a max_date-re)
        if total_events > 0 and max_date:
            default_date = max_date.date()
        else:
            default_date = date.today() - timedelta(days=1)
            
        selected_date = st.date_input(
            "DÁTUM VÁLASZTÁS", 
            value=default_date,
            help="Válaszd ki az elemzés napját"
        )
            
        # Adat szinkronizáció (ETL indítása)
        if st.button("Adatok szinkronizálása", width="stretch"):
            with st.spinner(f"Szinkronizálás folyamatban ({selected_date})..."):
                try:
                    pipeline = Pipeline()
                    pipeline.run_full_load(target_date=selected_date)
                    st.toast(f"Sikeres szinkronizáció: {selected_date}", icon="✅")
                    st.rerun()
                except Exception as e:
                    st.error(f"Hiba a szinkronizáció során: {str(e)}")

        # PDF Exportálás
        if total_events > 0:
            st.markdown("---")
            st.subheader("Exportálás")
            try:
                e, s, q = get_daily_data(selected_machine_id, selected_date)
                art_map = load_articles_map()
                if e:
                    pdf_buffer = generate_pdf_report(selected_machine_id, selected_date, s, e, quality=q, article_names=art_map)
                    st.download_button(
                        label="Napi jelentés (PDF)",
                        data=pdf_buffer,
                        file_name=f"Report_{selected_machine_id}_{selected_date}.pdf",
                        mime="application/pdf",
                        width="stretch"
                    )
                else:
                    st.info("Nincs adat ezen a napon.")
            except Exception as ex:
                st.error(f"PDF hiba: {str(ex)}")

        st.markdown("---")
        if total_events > 0 and min_date and max_date:
            st.markdown(f"""
            <div style='font-size: 0.82rem; color: #6c757d; line-height: 1.4; padding: 0 5px;'>
                <b style='color: #495057;'>ELÉRHETŐ ADATOK</b><br>
                <span>{min_date.strftime('%Y-%m-%d')} - {max_date.strftime('%Y-%m-%d')}</span><br>
                <span>{total_events:,} bejegyzés</span>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.info("Nincs adat az adatbázisban.")
                
    return selected_machine_id, selected_date, machine_options

def render_header(machine_name, selected_date):
    """A főoldal fejlécének megjelenítése."""
    # Automatikus görgetés a tetejére
    st.components.v1.html(
        f"<script>setTimeout(function() {{ window.parent.window.scrollTo({{ top: 0, behavior: 'smooth' }}); }}, 400);</script>",
        height=0
    )
    
    col_t, col_l = st.columns([4, 1], gap="large")
    with col_t:
        st.subheader("EcoPaper Solutions")
        st.title(f"{machine_name} Operations Dashboard")
        st.markdown(f"**Gyártáselemzési jelentés** | {selected_date.strftime('%Y. %m. %d.')}")

def main():
    """A Dashboard fő logikája."""
    selected_machine_id, selected_date, machine_options = render_sidebar()
    render_header(machine_options[selected_machine_id], selected_date)
    
    # Adatok betöltése
    article_names = load_articles_map()
    events, summary, quality = get_daily_data(selected_machine_id, selected_date)
    trend_summaries = get_trend_data(selected_machine_id, selected_date)
    
    if not events:
        st.info("Ezen a napon nem található adat. töltsd be az adatokat az 'Adatok szinkronizálása' gombbal.")
        return

    # --- 1. KPI SZEKCIÓ (FŐ MUTATÓK ÉS KÖZMŰVEK) ---
    if summary:
        k1, k2 = st.columns([0.05, 0.95])
        with k1: st.image("assets/oee.png", width=64)
        with k2: st.subheader("Napi teljesítménymutatók")

        col1, col2, col3, col4 = st.columns(4)
        
        # KPI 1: Termelés
        with col1:
            prod_delta = (summary.total_tons / summary.target_tons - 1) * 100 if summary.target_tons > 0 else 0
            st.metric("TERMELÉS", f"{summary.total_tons:.1f} t", 
                    delta=f"{prod_delta:.1f} %" if summary.target_tons > 0 else None,
                    help="A gép által termelt összes papír súlya (tonna).")
            st.plotly_chart(render_sparkline([s.total_tons for s in trend_summaries], "#2ecc71"), width="stretch", config={'displayModeBar': False})
        
        # KPI 2: OEE (Efficiency)
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
            st.metric("RENDELKEZÉSRE ÁLLÁS", f"{summary.availability_pct:.1f} %",
                    help="A gép üzemidejének aránya a teljes naptári időhöz képest.")
            st.plotly_chart(render_sparkline([s.availability_pct for s in trend_summaries], "#9b59b6"), width="stretch", config={'displayModeBar': False})
        
        # KPI 4: Selejtarány
        with col4:
            scrap_rate = (summary.scrap_tons / summary.total_tons * 100) if summary.total_tons > 0 else 0
            st.metric("SELEJTARÁNY", f"{scrap_rate:.1f} %",
                    help="A nem megfelelő minőségű termelés aránya az összes termeléshez képest.")
            trend_scraps = [(s.scrap_tons / s.total_tons * 100) if s.total_tons > 0 else 0 for s in trend_summaries]
            st.plotly_chart(render_sparkline(trend_scraps, "#e74c3c"), width="stretch", config={'displayModeBar': False})

        # --- ERŐFORRÁS SZEKCIÓ ---
        u1, u2 = st.columns([0.05, 0.95])
        with u1: st.image("assets/oee.png", width=64) # Javítva: oee.png helyett power.png-nek kéne lennie, de a design szerint maradjon konzisztens
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

    # Esemény adatok előkészítése a grafikonhoz
    df_raw = pd.DataFrame([
        {
            "Kezdet": e.timestamp,
            "Vége": e.timestamp + timedelta(seconds=e.duration_seconds or 0),
            "Állapot": e.status if e.event_type == "RUN" else e.event_type,
            "Termék": article_names.get(e.article_id, "Nincs gyártás") if e.article_id else "Nincs gyártás",
            "Gép": machine_options[selected_machine_id]
        } for e in events
    ])
    
    # Események összevonása (ha az állapot és a termék ugyanaz)
    merged = []
    if not df_raw.empty:
        curr = df_raw.iloc[0].to_dict()
        for i in range(1, len(df_raw)):
            row = df_raw.iloc[i].to_dict()
            if row["Állapot"] == curr["Állapot"] and row["Termék"] == curr["Termék"]:
                curr["Vége"] = row["Vége"]
            else:
                merged.append(curr)
                curr = row
        merged.append(curr)
    
    df_events = pd.DataFrame(merged)
    if not df_events.empty:
        df_events["Időtartam_perc"] = (df_events["Vége"] - df_events["Kezdet"]).dt.total_seconds() / 60
        t_colA, t_colB = st.columns([2, 1])
        with t_colA:
            st.plotly_chart(create_timeline_chart(df_events, machine_options[selected_machine_id]), width="stretch")
        with t_colB:
            df_states = df_events.groupby("Állapot")["Időtartam_perc"].sum().reset_index(name="Perc")
            st.plotly_chart(create_status_pie_chart(df_states), width="stretch")

    st.divider()

    # --- 3. TERMÉKELEMZÉS ---
    s1, s2 = st.columns([0.05, 0.95])
    with s1: st.image("assets/layer.png", width=64)
    with s2: st.subheader("Gyártott termékek elemzése")
    
    df_prod = pd.DataFrame([
        {
            "Termék": article_names.get(e.article_id, "N/A") if e.article_id else "N/A",
            "Súly (kg)": e.weight_kg or 0,
            "Időtartam (perc)": (e.duration_seconds / 60) if e.duration_seconds else 0
        } for e in events if e.event_type == "RUN"
    ])
    
    if not df_prod.empty:
        mix = df_prod.groupby("Termék").agg({"Súly (kg)": "sum", "Időtartam (perc)": "sum"}).reset_index()
        mix["Tonna"] = mix["Súly (kg)"] / 1000
        p_col1, p_col2 = st.columns([2, 1])
        with p_col1: st.plotly_chart(create_article_bar_chart(mix), width="stretch")
        with p_col2: st.plotly_chart(create_article_pie_chart(mix), width="stretch")

    st.divider()

    # --- 4. MINŐSÉGI ANALÍTIKA (LABOR) ---
    q1, q2 = st.columns([0.05, 0.95])
    with q1: st.image("assets/flask.png", width=64)
    with q2: st.subheader("Minőségi analitika (Labor)")
    
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
        st.info("Nincsenek laboradatok az adott napra.")

    st.divider()

    # --- 5. TERMELÉSI ZAVAROK (PARETO) ---
    a1, a2 = st.columns([0.05, 0.95])
    with a1: st.image("assets/alert.png", width=64)
    with a2: st.subheader("Termelési zavarok és állásidők")
    
    if summary:
        d_col1, d_col2 = st.columns([1, 2])
        with d_col1:
            st.metric("ÖSSZES ÁLLÁSIDŐ", f"{summary.total_downtime_min:.0f} perc")
            st.metric("SZAKADÁSSZÁM", f"{summary.break_count} db")
        
        pareto_df = get_pareto_data(selected_machine_id, selected_date)
        if not pareto_df.empty:
            with d_col2: st.plotly_chart(create_pareto_chart(pareto_df), width="stretch")
        else:
            with d_col2: st.info("Nincs elegendő adat a Pareto elemzéshez.")

    # --- LÁBLÉC ---
    st.divider()
    st.caption("EcoPaper Solutions Operations Dashboard | Kremzner Gábor 2026")
    st.markdown("<a href='#top' class='back-to-top'>↑</a>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()
