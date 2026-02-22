"""
TERMELÉSI MUTATÓK ÉS KPI KALKULÁTOR (TRANSFORMERS)
==================================================
Ez a modul tartalmazza a rendszer "agyát" és az üzleti logikát. 
Felelős a nyers adatokból (események, közművek, labor) származó 
főbb teljesítménymutatók (OEE, fajlagos fogyasztások) kiszámításáért.
"""

from datetime import date
import logging
from typing import List, Optional
from ..database import get_db
from ..models import (
    ProductionEventDB, ProductionPlanDB, 
    QualityDataDB, UtilityConsumptionDB, 
    DailySummaryDB
)
from sqlalchemy import func

# Naplózás beállítása a modulhoz
logger = logging.getLogger(__name__)

class MetricsCalculator:
    """
    KPI Kalkulátor osztály.
    Összetett számításokat végez a gépek hatékonyságának és
    erőforrás-felhasználásának elemzéséhez.
    """
    
    def __init__(self) -> None:
        """Kalkulátor inicializálása."""
        pass

    def calculate_daily_metrics(self, machine_id: str, target_date: date) -> Optional[DailySummaryDB]:
        """
        Kiszámítja egy gép napi összesített mutatóit.
        
        A folyamat lépései:
        1. Alapadatok begyűjtése az adatbázisból (Események, Terv, Közművek).
        2. Termelt tonnák összesítése (Jó termék vs Selejt).
        3. Súlyozott átlagsebesség számítása.
        4. OEE (Teljes Eszközhatékonyság) kalkuláció.
        5. Fajlagos erőforrás-felhasználás (Áram, Víz, Gőz, Rost).
        
        Args:
            machine_id: A gép azonosítója.
            target_date: A vizsgált nap.
            
        Returns:
            Optional[DailySummaryDB]: A kiszámított mutatókat tartalmazó adatbázis rekord.
        """
        logger.info(f"KPI kalkuláció indítása: {machine_id} | {target_date}")
        
        with get_db() as db:
            # --- 1. ADATGYŰJTÉS ---
            from datetime import datetime
            start_dt = datetime.combine(target_date, datetime.min.time())
            end_dt = datetime.combine(target_date, datetime.max.time())
            
            # Minden esemény az adott napon
            events = db.query(ProductionEventDB).filter(
                ProductionEventDB.machine_id == machine_id,
                ProductionEventDB.timestamp >= start_dt,
                ProductionEventDB.timestamp <= end_dt
            ).all()
            
            # Tervezési adatok (napi célok)
            plans = db.query(ProductionPlanDB).filter(
                ProductionPlanDB.machine_id == machine_id,
                ProductionPlanDB.date == target_date
            ).all()
            
            # Közműfogyasztási adatok
            utility = db.query(UtilityConsumptionDB).filter(
                UtilityConsumptionDB.machine_id == machine_id,
                UtilityConsumptionDB.date == target_date
            ).first()
            
            # Ha nincs esemény adat, nem tudunk mit számolni
            if not events:
                logger.warning(f"Nem található termelési esemény: {machine_id} | {target_date}. Számítás megszakítva.")
                return None

            # --- 2. TERMELÉSI ÖSSZESÍTŐK (TONNÁK) ---
            
            run_events = [e for e in events if e.event_type == "RUN"]
            total_tons = sum(e.weight_kg for e in run_events) / 1000.0 if run_events else 0.0
            scrap_tons = sum(e.weight_kg for e in run_events if e.status == "SCRAP") / 1000.0 if run_events else 0.0
            good_tons = total_tons - scrap_tons
            
            # Súlyozott átlagsebesség (Actual Speed)
            # Képlet: Σ (Sebesség * Súly) / Össz Súly
            if total_tons > 0:
                weighted_actual_speed_sum = sum(e.average_speed * e.weight_kg for e in run_events)
                avg_speed = weighted_actual_speed_sum / (total_tons * 1000.0)
            else:
                avg_speed = 0.0
            
            # --- 3. IDŐ ÉS HATÉKONYSÁG ---
            
            total_time_sec = sum(e.duration_seconds for e in events) or 1 # Nullával való osztás ellen
            run_time_sec = sum(e.duration_seconds for e in run_events)
            
            downtime_sec = sum(e.duration_seconds for e in events if e.event_type in ["STOP", "BREAK"])
            break_count = len([e for e in events if e.event_type == "BREAK"])
            
            # Tervezett tonna és tervezett sebesség (súlyozva)
            target_tons = sum(p.target_quantity_tons for p in plans) if plans else 0.0
            if target_tons > 0:
                weighted_target_speed_sum = sum(p.target_speed * p.target_quantity_tons for p in plans)
                target_speed = weighted_target_speed_sum / target_tons
            else:
                target_speed = (sum(p.target_speed for p in plans) / len(plans)) if plans else 0.0
            
            # --- 4. OEE KOMPONENSEK SZÁMÍTÁSA ---
            
            # A) Rendelkezésre állás (Availability) = Hasznos idő / Naptári idő
            avail_pct = (run_time_sec / total_time_sec * 100.0)
            
            # B) Teljesítmény (Performance) = Tényleges Tonna / Tervezett Tonna
            perf_pct = (total_tons / target_tons * 100.0) if target_tons > 0 else 0.0
            # A teljesítmény nem haladhatja meg a 100%-ot a standard OEE modellben
            if perf_pct > 100.0: perf_pct = 100.0 
            
            # C) Minőség (Quality) = Jó Tonna / Összes Termelt Tonna
            qual_pct = (good_tons / total_tons * 100.0) if total_tons > 0 else 0.0
            
            # Végleges OEE = A * P * Q
            oee_pct = (avail_pct/100.0 * perf_pct/100.0 * qual_pct/100.0) * 100.0
            
            # --- 5. MINŐSÉGI ÁTLAGOK ---
            
            quality_measurements = db.query(QualityDataDB).filter(
                QualityDataDB.machine_id == machine_id,
                QualityDataDB.timestamp >= start_dt,
                QualityDataDB.timestamp <= end_dt
            ).all()
            
            avg_moisture = sum(q.moisture_pct for q in quality_measurements) / len(quality_measurements) if quality_measurements else 0.0
            avg_gsm = sum(q.gsm_measured for q in quality_measurements) / len(quality_measurements) if quality_measurements else 0.0

            # --- 6. FAJLAGOS KÖZMŰ ÉS ALAPANYAG MUTATÓK ---
            
            # A mutatók egy tonna késztermékre (Total Tons) vetítve értendők
            spec_elec = (utility.electricity_kwh / total_tons) if utility and total_tons > 0 else 0.0
            spec_water = (utility.water_m3 / total_tons) if utility and total_tons > 0 else 0.0
            spec_steam = (utility.steam_tons / total_tons) if utility and total_tons > 0 else 0.0
            # Fibler/Rost mutató (Spec Fiber): mennyiségű tonna rost szükséges egy tonna papírhoz
            spec_fiber = (utility.fiber_tons / total_tons) if utility and total_tons > 0 else 0.0
            
            # --- EREDMÉNY OBJEKTUM ÖSSZEÁLLÍTÁSA ---
            return DailySummaryDB(
                date=target_date,
                machine_id=machine_id,
                oee_pct=round(oee_pct, 2),
                availability_pct=round(avail_pct, 2),
                performance_pct=round(perf_pct, 2),
                quality_pct=round(qual_pct, 2),
                total_tons=round(total_tons, 2),
                good_tons=round(good_tons, 2),
                scrap_tons=round(scrap_tons, 2),
                target_tons=round(target_tons, 2),
                total_downtime_min=round(downtime_sec / 60.0, 1),
                break_count=break_count,
                avg_speed_m_min=round(avg_speed, 1),
                target_speed_m_min=round(target_speed, 1),
                avg_moisture_pct=round(avg_moisture, 2),
                avg_gsm_measured=round(avg_gsm, 1),
                spec_electricity_kwh_t=round(spec_elec, 2),
                spec_water_m3_t=round(spec_water, 2),
                spec_steam_t_t=round(spec_steam, 2),
                spec_fiber_t_t=round(spec_fiber, 2)
            )

    def save_summary(self, summary: DailySummaryDB) -> None:
        """
        Elmenti vagy frissíti a kiszámított napi összefoglalót.
        Gondoskodik az adatok konzisztenciájáról (Upsert logika).
        """
        with get_db() as db:
            # Régi rekord törlése azonos dátum és gép esetén (elkerüli a duplikációt)
            db.query(DailySummaryDB).filter(
                DailySummaryDB.date == summary.date,
                DailySummaryDB.machine_id == summary.machine_id
            ).delete()
            
            db.add(summary)
            # A változtatások elmentése (commit) a context manager végén automatikus
            logger.info(f"Napi riport mentve: {summary.machine_id} | {summary.date}")
