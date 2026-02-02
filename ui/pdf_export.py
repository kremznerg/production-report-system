"""
PDF EXPORTÁLÓ MODUL (PDF REPORT GENERATION)
==========================================
Ez a modul felelős a professzionális, nyomtatható PDF gyártási jelentések 
generálásáért a ReportLab könyvtár segítségével.
"""

from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily
import os
from datetime import datetime
import pandas as pd

# --- BETŰTÍPUS REGISZTRÁCIÓ A MAGYAR ÉKEZETEKHEZ ---
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
FONT_PATH = os.path.join(BASE_DIR, "assets", "fonts", "Arial.ttf")
FONT_BOLD_PATH = os.path.join(BASE_DIR, "assets", "fonts", "Arial-Bold.ttf")

try:
    if os.path.exists(FONT_PATH):
        pdfmetrics.registerFont(TTFont('Arial', FONT_PATH))
        pdfmetrics.registerFont(TTFont('Arial-Bold', FONT_BOLD_PATH))
        registerFontFamily('Arial', normal='Arial', bold='Arial-Bold')
        BASE_FONT = 'Arial'
        BOLD_FONT = 'Arial-Bold'
    else:
        BASE_FONT = 'Helvetica'
        BOLD_FONT = 'Helvetica-Bold'
except Exception:
    BASE_FONT = 'Helvetica'
    BOLD_FONT = 'Helvetica-Bold'

def generate_pdf_report(machine_id, selected_date, summary, events, quality=None, article_names=None):
    """Létrehoz egy részletes, professzionális PDF jelentést magyar ékezet támogatással."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    styles = getSampleStyleSheet()
    
    # Központi stílusok
    title_style = ParagraphStyle('Title', parent=styles['Heading1'], fontName=BOLD_FONT, fontSize=18, alignment=1)
    section_style = ParagraphStyle('Section', parent=styles['Heading2'], fontName=BOLD_FONT, fontSize=12, color=colors.HexColor("#0d6efd"), spaceBefore=12, spaceAfter=8)
    normal_style = ParagraphStyle('Normal', parent=styles['Normal'], fontName=BASE_FONT, fontSize=9)
    normal_bold_style = ParagraphStyle('NormalBold', parent=styles['Normal'], fontName=BOLD_FONT, fontSize=9)

    elements = []

    # --- 1. FEJLÉC (Logó + Cím) ---
    logo_path = os.path.join(os.path.dirname(__file__), "..", "assets", "logo.jpeg")
    if os.path.exists(logo_path):
        img = Image(logo_path)
        aspect = img.imageWidth / img.imageHeight
        img.drawHeight = 40
        img.drawWidth = 40 * aspect
        header_table_data = [[img, Paragraph("NAPI TERMELÉSI JELENTÉS", title_style), ""]]
        header_table = Table(header_table_data, colWidths=[60, 415, 60])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (1, 0), (1, 0), 'CENTER'),
        ]))
        elements.append(header_table)
    else:
        elements.append(Paragraph(f"NAPI TERMELÉSI JELENTÉS", title_style))
        elements.append(Paragraph(f"<b>Cég:</b> EcoPaper Solutions", normal_style))

    # Info táblázat: Gép/Dátum (bal) és Generálás ideje (jobb)
    info_style_right = ParagraphStyle('NormalRight', parent=normal_style, alignment=2)
    info_data = [[
        Paragraph(f"<b>Gép:</b> {machine_id} | <b>Dátum:</b> {selected_date.strftime('%Y-%m-%d')}", normal_style),
        Paragraph(f"Jelentés készült: {pd.Timestamp.now(tz='Europe/Budapest').strftime('%Y-%m-%d %H:%M')}", info_style_right)
    ]]
    info_table = Table(info_data, colWidths=[300, 235])
    info_table.setStyle(TableStyle([
        ('LEFTPADDING', (0, 0), (0, 0), 0),
        ('RIGHTPADDING', (1, 0), (1, 0), 0),
        ('VALIGN', (0, 0), (-1, -1), 'BOTTOM'),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 10))

    # --- 2. KPI ÖSSZEFOGLALÓ ---
    if summary:
        elements.append(Paragraph("Teljesítménymutatók", section_style))
        kpi_data = [
            [Paragraph("<b>Megnevezés</b>", normal_style), Paragraph("<b>Érték</b>", normal_style), Paragraph("<b>Mérték</b>", normal_style)],
            [Paragraph("TERMELÉS (Tény / Cél)", normal_style), f"{summary.total_tons:.1f} / {summary.target_tons:.1f}", "t"],
            [Paragraph("OEE MUTATÓ", normal_style), f"{summary.oee_pct:.1f}", "%"],
            [Paragraph("  - Rendelkezésre állás", normal_style), f"{summary.availability_pct:.1f}", "%"],
            [Paragraph("  - Teljesítmény index", normal_style), f"{summary.performance_pct:.1f}", "%"],
            [Paragraph("  - Minőségi mutató", normal_style), f"{summary.quality_pct:.1f}", "%"],
            [Paragraph("ÁTLAGSEBESSÉG", normal_style), f"{summary.avg_speed_m_min:.0f}", "m/perc"],
            [Paragraph("ÖSSZES ÁLLÁSIDŐ", normal_style), f"{summary.total_downtime_min:.0f}", "perc"],
            [Paragraph("SZAKADÁSSZÁM", normal_style), f"{summary.break_count}", "db"]
        ]
        kt = Table(kpi_data, colWidths=[250, 100, 100])
        kt.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), BASE_FONT),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0d6efd")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), BOLD_FONT),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(kt)
        elements.append(Spacer(1, 15))

        # --- 3. KÖZMŰVEK (Abszolút + Fajlagos) ---
        elements.append(Paragraph("Erőforrás-felhasználás", section_style))
        u_data = [
            [Paragraph("<b>Erőforrás</b>", normal_style), Paragraph("<b>Összes fogyasztás</b>", normal_style), Paragraph("<b>Fajlagos mutató</b>", normal_style)],
            ["Villamos energia", f"{(summary.spec_electricity_kwh_t * summary.total_tons):.0f} kWh", f"{summary.spec_electricity_kwh_t:.0f} kWh/t"],
            ["Frissvíz", f"{(summary.spec_water_m3_t * summary.total_tons):.0f} m³", f"{summary.spec_water_m3_t:.1f} m³/t"],
            ["Gőz", f"{(summary.spec_steam_t_t * summary.total_tons):.1f} t", f"{summary.spec_steam_t_t:.2f} t/t"],
            ["Alapanyag (Rost)", f"{(summary.spec_fiber_t_t * summary.total_tons):.1f} t", f"{summary.spec_fiber_t_t:.2f} t/t"]
        ]
        ut = Table(u_data, colWidths=[150, 150, 150])
        ut.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), BASE_FONT),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#6c757d")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('FONTNAME', (0, 0), (-1, 0), BOLD_FONT),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(ut)
        elements.append(Spacer(1, 10))

    # --- 4. GYÁRTOTT TERMÉKEK ÉS MINŐSÉG ---
    run_events = [e for e in events if e.event_type == "RUN"]
    if run_events and article_names:
        elements.append(Paragraph("Gyártási és minőségi adatok termékenként", section_style))
        prod_stats = {}
        for e in run_events:
            aid = e.article_id
            if aid not in prod_stats:
                prod_stats[aid] = {"name": article_names.get(aid, aid), "w": 0, "d": 0, "s_sum": 0, "s_cnt": 0}
            prod_stats[aid]["w"] += (e.weight_kg / 1000)
            prod_stats[aid]["d"] += (e.duration_seconds / 60)
            if e.average_speed:
                prod_stats[aid]["s_sum"] += e.average_speed
                prod_stats[aid]["s_cnt"] += 1
        
        if quality:
            for q in quality:
                aid = q.article_id
                if aid in prod_stats:
                    if "q_gsm" not in prod_stats[aid]:
                        prod_stats[aid].update({"q_gsm": [], "q_moist": [], "q_str": []})
                    prod_stats[aid]["q_gsm"].append(q.gsm_measured)
                    prod_stats[aid]["q_moist"].append(q.moisture_pct)
                    prod_stats[aid]["q_str"].append(q.strength_knm)

        header = [
            Paragraph("<b>Termék megnevezése</b>", normal_style), 
            Paragraph("<b>Súly (t)</b>", normal_style), 
            Paragraph("<b>Seb (m/p)</b>", normal_style),
            Paragraph("<b>GSM</b>", normal_style), 
            Paragraph("<b>Nedv (%)</b>", normal_style), 
            Paragraph("<b>Szil (kN/m)</b>", normal_style)
        ]
        table_data = [header]
        
        for aid, v in prod_stats.items():
            avg_speed = v["s_sum"] / v["s_cnt"] if v["s_cnt"] > 0 else 0
            avg_gsm = sum(v["q_gsm"])/len(v["q_gsm"]) if "q_gsm" in v and v["q_gsm"] else 0
            avg_moist = sum(v["q_moist"])/len(v["q_moist"]) if "q_moist" in v and v["q_moist"] else 0
            avg_str = sum(v["q_str"])/len(v["q_str"]) if "q_str" in v and v["q_str"] else 0
            
            table_data.append([
                Paragraph(v["name"], normal_style),
                f"{v['w']:.1f}",
                f"{avg_speed:.0f}",
                f"{avg_gsm:.1f}" if avg_gsm > 0 else "-",
                f"{avg_moist:.1f}" if avg_moist > 0 else "-",
                f"{avg_str:.1f}" if avg_str > 0 else "-"
            ])

        pt = Table(table_data, colWidths=[150, 60, 60, 60, 60, 60])
        pt.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), BASE_FONT),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2ecc71")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (1, 1), (-1, -1), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
        ]))
        elements.append(pt)
        elements.append(Spacer(1, 15))

    # --- 5. LEÁLLÁSI STATISZTIKA ---
    stop_events = [e for e in events if e.event_type in ["STOP", "BREAK"]]
    if stop_events:
        elements.append(Paragraph("Állásidők és leállási okok", section_style))
        stop_stats = {}
        for s in stop_events:
            reason = s.description if s.description else ("Tervszerű leállás" if s.event_type == "STOP" else "Papiros szakadás")
            if reason not in stop_stats:
                stop_stats[reason] = 0
            stop_stats[reason] += (s.duration_seconds / 60)
        
        stop_header = [Paragraph("<b>Leállás oka / típusa</b>", normal_style), Paragraph("<b>Időtartam (perc)</b>", normal_style)]
        stop_table_data = [stop_header]
        for reason in sorted(stop_stats, key=stop_stats.get, reverse=True):
            stop_table_data.append([Paragraph(reason, normal_style), f"{stop_stats[reason]:.0f}"])
            
        st = Table(stop_table_data, colWidths=[350, 100])
        st.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), BASE_FONT),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#dc3545")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
        ]))
        elements.append(st)


    doc.build(elements)
    buffer.seek(0)
    return buffer
