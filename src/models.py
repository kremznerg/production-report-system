from datetime import datetime, date
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey
from sqlalchemy.orm import DeclarativeBase
from pydantic import BaseModel, ConfigDict

# --- ADATBÁZIS MODELLEK (SQLALCHEMY) ---

class Base(DeclarativeBase):
    pass

class MachineDB(Base):
    """Papírgép törzsadat - a gyár fő termelőegységei listája."""
    __tablename__ = "machines"
    
    id = Column(String(20), primary_key=True)
    name = Column(String(100), nullable=False)
    location = Column(String(100))

class ArticleDB(Base):
    """Termék törzsadat - a gyártott papírtípusok (pl. Kraftliner, Testliner)."""
    __tablename__ = "articles"
    
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    product_group = Column(String(50)) 
    nominal_gsm = Column(Float)

class ProductionEventDB(Base):
    """
    Termelési események (MES adatok).
    Minden tekercs gyártása vagy minden leállás egy-egy bejegyzés itt.
    """
    __tablename__ = "production_events"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True) 
    duration_seconds = Column(Integer) 
    
    event_type = Column(String(20), nullable=False) 
    status = Column(String(20)) 
    
    weight_kg = Column(Float) 
    average_speed = Column(Float)
    
    machine_id = Column(String(20), ForeignKey("machines.id"))
    article_id = Column(String(50), ForeignKey("articles.id"))
    
    description = Column(String(255)) 

class ProductionPlanDB(Base):
    """Termelési terv adatok (Excelből). Tartalmazza a célmennyiséget és célsebességet."""
    __tablename__ = "production_plans"
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False, index=True)
    machine_id = Column(String(20), ForeignKey("machines.id"))
    article_id = Column(String(50), ForeignKey("articles.id"))
    
    target_quantity_tons = Column(Float)
    target_speed = Column(Float)
    
class QualityDataDB(Base):
    """Labor mérési eredmények (Excelből)."""
    __tablename__ = "quality_data"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    machine_id = Column(String(20), ForeignKey("machines.id"))
    article_id = Column(String(50), ForeignKey("articles.id"))
    
    moisture_pct = Column(Float)
    gsm_measured = Column(Float)
    strength_knm = Column(Float)

class UtilityConsumptionDB(Base):
    """Közműfogyasztási adatok (Excelből). Áram, víz, gőz és rost felvétel."""
    __tablename__ = "utility_consumption"
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False, index=True)
    machine_id = Column(String(20), ForeignKey("machines.id"))
    
    water_m3 = Column(Float)
    electricity_kwh = Column(Float)
    steam_tons = Column(Float)
    fiber_tons = Column(Float)
    additives_kg = Column(Float)

class DailySummaryDB(Base):
    """
    Összesített napi jelentés tábla.
    Ez a tábla szolgál a Dashboard alapjául (OEE, fajlagos mutatók).
    """
    __tablename__ = "daily_summaries"
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False, index=True)
    machine_id = Column(String(20), ForeignKey("machines.id"))
    
    # KPIs
    oee_pct = Column(Float)
    availability_pct = Column(Float)
    performance_pct = Column(Float)
    quality_pct = Column(Float)
    
    # Production (Tons)
    total_tons = Column(Float)
    good_tons = Column(Float)
    scrap_tons = Column(Float)
    target_tons = Column(Float)
    
    # Efficiency & Downtime
    total_downtime_min = Column(Float)
    break_count = Column(Integer)
    avg_speed_m_min = Column(Float)
    target_speed_m_min = Column(Float)
    
    # Quality Averages
    avg_moisture_pct = Column(Float)
    avg_gsm_measured = Column(Float)
    
    # Specifics
    spec_electricity_kwh_t = Column(Float)
    spec_water_m3_t = Column(Float)
    spec_steam_t_t = Column(Float)
    spec_fiber_t_t = Column(Float)

# --- VALIDÁTOROK (PYDANTIC) ---

class Machine(BaseModel):
    id: str
    name: str
    location: str
    model_config = ConfigDict(from_attributes=True)

class Article(BaseModel):
    id: str
    name: str
    nominal_gsm: float
    model_config = ConfigDict(from_attributes=True)

class ProductionEvent(BaseModel):
    timestamp: datetime
    duration_seconds: Optional[int] = 0
    event_type: str
    status: Optional[str] = "GOOD"
    weight_kg: Optional[float] = 0.0
    average_speed: Optional[float] = 0.0
    machine_id: str
    article_id: Optional[str] = None
    description: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class ProductionPlan(BaseModel):
    date: date
    machine_id: str
    article_id: str
    target_quantity_tons: float
    target_speed: float
    model_config = ConfigDict(from_attributes=True)

class QualityMeasurement(BaseModel):
    timestamp: datetime
    machine_id: str
    article_id: str
    moisture_pct: float
    gsm_measured: float
    strength_knm: float
    model_config = ConfigDict(from_attributes=True)

class UtilityData(BaseModel):
    date: date
    machine_id: str
    water_m3: float
    electricity_kwh: float
    steam_tons: float
    fiber_tons: float
    additives_kg: float
    model_config = ConfigDict(from_attributes=True)
class DailySummary(BaseModel):
    date: date
    machine_id: str
    oee_pct: float
    availability_pct: float
    performance_pct: float
    quality_pct: float
    total_tons: float
    good_tons: float
    scrap_tons: float
    target_tons: Optional[float] = 0.0
    total_downtime_min: Optional[float] = 0.0
    break_count: Optional[int] = 0
    avg_speed_m_min: Optional[float] = 0.0
    target_speed_m_min: Optional[float] = 0.0
    avg_moisture_pct: Optional[float] = 0.0
    avg_gsm_measured: Optional[float] = 0.0
    spec_electricity_kwh_t: Optional[float] = 0.0
    spec_water_m3_t: Optional[float] = 0.0
    spec_steam_t_t: Optional[float] = 0.0
    spec_fiber_t_t: Optional[float] = 0.0
    model_config = ConfigDict(from_attributes=True)
