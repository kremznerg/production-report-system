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

logger = logging.getLogger(__name__)

class MetricsCalculator:
    """
    Üzleti logika réteg. 
    Itt történik az OEE, a súlyozott sebesség és a fajlagos mutatók kiszámítása.
    """
    def __init__(self):
        pass

    def calculate_daily_metrics(self, machine_id: str, target_date: date) -> Optional[DailySummaryDB]:
        """
        A napi KPI-ok kiszámításának fő belépési pontja.
        Összegyűjti a nyers adatokat és elvégzi a súlyozott kalkulációkat.
        """
        logger.info(f"KPI számítás folyamatban: {machine_id} -> {target_date}")
        
        with get_db() as db:
            # 1. Gather all necessary base data
            events = db.query(ProductionEventDB).filter(
                ProductionEventDB.machine_id == machine_id,
                func.date(ProductionEventDB.timestamp) == target_date
            ).all()
            
            plan = db.query(ProductionPlanDB).filter(
                ProductionPlanDB.machine_id == machine_id,
                ProductionPlanDB.date == target_date
            ).first()
            
            utility = db.query(UtilityConsumptionDB).filter(
                UtilityConsumptionDB.machine_id == machine_id,
                UtilityConsumptionDB.date == target_date
            ).first()
            
            if not events:
                logger.warning(f"No production events found for {machine_id} on {target_date}. Skipping summary.")
                return None

            # 2. Basic Production Aggregates (Tons)
            run_events = [e for e in events if e.event_type == "RUN"]
            total_tons = sum(e.weight_kg for e in run_events) / 1000.0
            scrap_tons = sum(e.weight_kg for e in run_events if e.status == "SCRAP") / 1000.0
            good_tons = total_tons - scrap_tons
            
            # --- TÉNYLEGES SEBESSÉG (SÚLYOZVA A TÉNYLEGES TONNÁVAL) ---
            # Σ (Tényleges_Sebesség * Tényleges_Súly_kg) / Σ Tényleges_Súly_kg
            if total_tons > 0:
                weighted_actual_speed_sum = sum(e.average_speed * e.weight_kg for e in run_events)
                avg_speed = weighted_actual_speed_sum / (total_tons * 1000.0)
            else:
                avg_speed = 0.0
            
            # 3. Efficiency, Downtime & Breaks
            total_time_sec = sum(e.duration_seconds for e in events)
            run_time_sec = sum(e.duration_seconds for e in run_events)
            
            downtime_sec = sum(e.duration_seconds for e in events if e.event_type in ["STOP", "BREAK"])
            break_count = len([e for e in events if e.event_type == "BREAK"])
            
            # 4. Planning data
            plans = db.query(ProductionPlanDB).filter(
                ProductionPlanDB.machine_id == machine_id,
                ProductionPlanDB.date == target_date
            ).all()
            
            target_tons = sum(p.target_quantity_tons for p in plans) if plans else 0.0
            
            # --- TERV SEBESSÉG (SÚLYOZVA A TERVEZETT TONNÁVAL) ---
            # Σ (Terv_Sebesség * Terv_Tonna) / Σ Terv_Tonna
            if target_tons > 0:
                weighted_target_speed_sum = sum(p.target_speed * p.target_quantity_tons for p in plans)
                target_speed = weighted_target_speed_sum / target_tons
            else:
                target_speed = (sum(p.target_speed for p in plans) / len(plans)) if plans else 0.0
            
            # OEE Components
            # A) Availability = RUN time / Total scheduled time
            avail_pct = (run_time_sec / total_time_sec * 100.0) if total_time_sec > 0 else 0.0
            
            # B) Performance = Actual Tons / Target Tons
            perf_pct = (total_tons / target_tons * 100.0) if target_tons > 0 else 0.0
            if perf_pct > 100.0: perf_pct = 100.0 
            
            # C) Quality = Good Tons / Total Tons
            qual_pct = (good_tons / total_tons * 100.0) if total_tons > 0 else 0.0
            
            # Final OEE
            oee_pct = (avail_pct/100.0 * perf_pct/100.0 * qual_pct/100.0) * 100.0
            
            # 5. Quality Averages
            quality_measurements = db.query(QualityDataDB).filter(
                QualityDataDB.machine_id == machine_id,
                func.date(QualityDataDB.timestamp) == target_date
            ).all()
            
            avg_moisture = sum(q.moisture_pct for q in quality_measurements) / len(quality_measurements) if quality_measurements else 0.0
            avg_gsm = sum(q.gsm_measured for q in quality_measurements) / len(quality_measurements) if quality_measurements else 0.0

            # 6. Specific Utilities & Materials
            spec_elec = (utility.electricity_kwh / total_tons) if utility and total_tons > 0 else 0.0
            spec_water = (utility.water_m3 / total_tons) if utility and total_tons > 0 else 0.0
            spec_steam = (utility.steam_tons / total_tons) if utility and total_tons > 0 else 0.0
            spec_fiber = (utility.fiber_tons / total_tons) if utility and total_tons > 0 else 0.0
            
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
        """Elmenti vagy frissíti a napi összefoglalót az adatbázisban."""
        with get_db() as db:
            # Delete existing to prevent duplicates (Upsert)
            db.query(DailySummaryDB).filter(
                DailySummaryDB.date == summary.date,
                DailySummaryDB.machine_id == summary.machine_id
            ).delete()
            
            db.add(summary)
            logger.info(f"Saved daily summary for {summary.machine_id} on {summary.date}")
