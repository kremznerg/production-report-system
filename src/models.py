from datetime import datetime, date
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey
from sqlalchemy.orm import DeclarativeBase
from pydantic import BaseModel, ConfigDict

# --- ADATBÁZIS MODELLEK (SQLALCHEMY) ---

class Base(DeclarativeBase):
    pass

class MachineDB(Base):
    """Gép törzsadatok."""
    __tablename__ = "machines"
    
    id = Column(String(20), primary_key=True)
    name = Column(String(100), nullable=False)
    location = Column(String(100))

class ArticleDB(Base):
    """Termék törzsadatok."""
    __tablename__ = "articles"
    
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    product_group = Column(String(50)) 
    nominal_gsm = Column(Float)

class ProductionEventDB(Base):
    """
    Termelési események (API-ból).
    Ez a 'Fact' tábla alapja.
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
    """Napi gyártási terv (Excel-ből)."""
    __tablename__ = "production_plans"
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False, index=True)
    machine_id = Column(String(20), ForeignKey("machines.id"))
    article_id = Column(String(50), ForeignKey("articles.id"))
    
    target_quantity_tons = Column(Float)
    target_speed = Column(Float)
    
class QualityDataDB(Base):
    """Labor mérési adatok (Excel-ből)."""
    __tablename__ = "quality_reports"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    machine_id = Column(String(20), ForeignKey("machines.id"))
    article_id = Column(String(50), ForeignKey("articles.id"))
    
    moisture_pct = Column(Float)
    gsm_measured = Column(Float)
    strength_knm = Column(Float)

class UtilityConsumptionDB(Base):
    """Napi közüzemi és anyag fogyasztás (Excel-ből)."""
    __tablename__ = "utility_consumption"
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False, index=True)
    machine_id = Column(String(20), ForeignKey("machines.id"))
    
    water_m3 = Column(Float)
    electricity_kwh = Column(Float)
    steam_tons = Column(Float)
    fiber_tons = Column(Float)
    additives_kg = Column(Float)

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
