from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship
from pydantic import BaseModel, ConfigDict

# --- SZERKEZET (DATABASE TABLES) ---

class Base(DeclarativeBase):
    pass

class MachineDB(Base):
    """Gép törzsadatok."""
    __tablename__ = "machines"
    
    id = Column(String(20), primary_key=True)
    name = Column(String(100), nullable=False)
    width_mm = Column(Float) # Gép munkaszélessége

class ArticleDB(Base):
    """Termék törzsadatok."""
    __tablename__ = "articles"
    
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    product_group = Column(String(50))
    nominal_gsm = Column(Float) # Névleges grammsúly

class ProductionEventDB(Base):
    """Termelési események (API-ból)."""
    __tablename__ = "production_events"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    event_type = Column(String(50), nullable=False)
    machine_id = Column(String(20), ForeignKey("machines.id"))
    article_id = Column(String(50), ForeignKey("articles.id"))
    description = Column(String(255))

class ProductionPlanDB(Base):
    """Napi tervek és célkitűzések (Excel-ből)."""
    __tablename__ = "production_plans"
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False, index=True)
    machine_id = Column(String(20), ForeignKey("machines.id"))
    article_id = Column(String(50), ForeignKey("articles.id"))
    target_speed = Column(Float)
    target_quantity_tons = Column(Float)
    target_energy_kwh_per_ton = Column(Float) # Energiahatékonysági cél

class QualityDataDB(Base):
    """Labor mérési adatok (Excel-ből)."""
    __tablename__ = "quality_reports"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    article_id = Column(String(50), ForeignKey("articles.id"))
    moisture_pct = Column(Float)
    gsm_measured = Column(Float)
    strength_knm = Column(Float)

class UtilityConsumptionDB(Base):
    """Napi közüzemi fogyasztás (Excel-ből)."""
    __tablename__ = "utility_consumption"
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False, index=True)
    water_m3 = Column(Float)
    electricity_kwh = Column(Float)
    steam_tons = Column(Float)

# --- VALIDÁCIÓ (PYDANTIC MODELS) ---

class Machine(BaseModel):
    id: str
    name: str
    width_mm: float
    model_config = ConfigDict(from_attributes=True)

class Article(BaseModel):
    id: str
    name: str
    product_group: str
    nominal_gsm: float
    model_config = ConfigDict(from_attributes=True)

class ProductionEvent(BaseModel):
    timestamp: datetime
    event_type: str
    machine_id: str
    article_id: Optional[str] = None
    description: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class ProductionPlan(BaseModel):
    date: date
    machine_id: str
    article_id: str
    target_speed: float
    target_quantity_tons: float
    model_config = ConfigDict(from_attributes=True)

class UtilityConsumption(BaseModel):
    date: date
    water_m3: float
    electricity_kwh: float
    steam_tons: float
    model_config = ConfigDict(from_attributes=True)
