import pandas as pd
from datetime import datetime, timedelta, date
from typing import List, Dict, Tuple, Optional
from sqlalchemy import func
from src.database import get_db
from src.models import (
    MachineDB, ArticleDB, ProductionEventDB, 
    DailySummaryDB, QualityDataDB,
    Machine, ProductionEvent, QualityMeasurement, DailySummary
)

def load_articles_map() -> Dict[str, str]:
    """Betölti a termék törzsadatokat és egy formázott név-térképet ad vissza."""
    with get_db() as db:
        articles = db.query(ArticleDB).all()
        return {a.id: f"{a.name} {a.nominal_gsm:.0f}g" for a in articles}

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

def get_pareto_data(machine_id: str, target_date: date, days: int = 30) -> pd.DataFrame:
    """Lekéri a cél dátumot megelőző X nap leállási okait Pareto elemzéshez."""
    with get_db() as db:
        start_date = target_date - timedelta(days=days)
        
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

def get_trend_data(machine_id: str, target_date: date, days: int = 10) -> List[DailySummary]:
    """Lekéri az elmúlt X nap összesítő adatait trendvonalhoz."""
    with get_db() as db:
        start_date = target_date - timedelta(days=days-1)
        db_summaries = db.query(DailySummaryDB).filter(
            DailySummaryDB.machine_id == machine_id,
            DailySummaryDB.date >= start_date,
            DailySummaryDB.date <= target_date
        ).order_by(DailySummaryDB.date).all()
        
        return [DailySummary.model_validate(s) for s in db_summaries]

def get_data_availability():
    """Lekéri az adatbázisból az elérhető dátumtartományt."""
    with get_db() as db:
        res = db.query(
            func.min(ProductionEventDB.timestamp),
            func.max(ProductionEventDB.timestamp),
            func.count(ProductionEventDB.id)
        ).first()
        return res
