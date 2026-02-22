"""
ADATMODELL ÉS VALIDÁCIÓS RÉTEG
==============================
Ez a modul definiálja a rendszer adatstruktúráit.
Két technológiát használunk:
1. SQLAlchemy: Az adatbázis táblák leképezéséhez (ORM).
2. Pydantic: Az adatok validálásához és a modulok közötti biztonságos adatcseréhez.
"""

from datetime import datetime, date
from typing import Optional
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey
from sqlalchemy.orm import DeclarativeBase, relationship
from pydantic import BaseModel, ConfigDict

# --- ADATBÁZIS MODELLEK (SQLALCHEMY) ---

class Base(DeclarativeBase):
    """Alaposztály az összes adatbázis modellhez."""
    pass

class MachineDB(Base):
    """
    Papírgép törzsadat.
    A gyár fő termelőegységeinek listája (pl. PM1, PM2).
    """
    __tablename__ = "machines"
    
    id = Column(String(20), primary_key=True)
    name = Column(String(100), nullable=False)
    location = Column(String(100)) # Üzemegység helyszíne
    
    # --- KAPCSOLATOK (Relationships) ---
    production_events = relationship("ProductionEventDB", back_populates="machine")
    production_plans = relationship("ProductionPlanDB", back_populates="machine")
    quality_data = relationship("QualityDataDB", back_populates="machine")
    utilities = relationship("UtilityConsumptionDB", back_populates="machine")
    daily_summaries = relationship("DailySummaryDB", back_populates="machine")

class ArticleDB(Base):
    """
    Termék / Cikk törzsadat.
    A gyártott papírtípusok katalógusa (pl. Kraftliner, Testliner, Fluting).
    Minden termékhez tartozik egy névleges grammsúly (nominal_gsm).
    """
    __tablename__ = "articles"
    
    id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    product_group = Column(String(50)) # Termékcsoport (pl. Liner, Medium)
    nominal_gsm = Column(Float)        # Névleges négyzetmétersúly (g/m2)
    
    # --- KAPCSOLATOK (Relationships) ---
    production_events = relationship("ProductionEventDB", back_populates="article")
    production_plans = relationship("ProductionPlanDB", back_populates="article")
    quality_data = relationship("QualityDataDB", back_populates="article")

class ProductionEventDB(Base):
    """
    Termelési eseménynapló (MES adatok).
    Itt tároljuk a gép minden állapotváltozását:
    - RUN: Gyártás (minden legyártott tekercs egy sor)
    - STOP: Tervezett vagy műszaki állás
    - BREAK: Papírszakadás (váratlan esemény)
    """
    __tablename__ = "production_events"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False, index=True) 
    duration_seconds = Column(Integer) # Az esemény időtartama másodperceben
    
    event_type = Column(String(20), nullable=False) # RUN, STOP, BREAK
    status = Column(String(20)) # RUN esetén: GOOD (Jó) vagy SCRAP (Selejt)
    
    weight_kg = Column(Float)      # Gyártott mennyiség kg-ban (csak RUN esetén)
    average_speed = Column(Float)   # Átlagsebesség a szakasz alatt (m/min)
    
    machine_id = Column(String(20), ForeignKey("machines.id"))
    article_id = Column(String(50), ForeignKey("articles.id"))
    
    description = Column(String(255)) # Megjegyzés (pl. állás oka)
    
    # --- KAPCSOLATOK (Relationships) ---
    machine = relationship("MachineDB", back_populates="production_events")
    article = relationship("ArticleDB", back_populates="production_events")

class ProductionPlanDB(Base):
    """
    Napi termelési terv (Excel forrásból).
    Tartalmazza az elvárt mennyiségi és sebességi célokat.
    """
    __tablename__ = "production_plans"
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False, index=True)
    machine_id = Column(String(20), ForeignKey("machines.id"))
    article_id = Column(String(50), ForeignKey("articles.id"))
    
    target_quantity_tons = Column(Float) # Tervezett mennyiség (tonna)
    target_speed = Column(Float)         # Tervezett sebesség (m/min)
    
    # --- KAPCSOLATOK (Relationships) ---
    machine = relationship("MachineDB", back_populates="production_plans")
    article = relationship("ArticleDB", back_populates="production_plans")
    
class QualityDataDB(Base):
    """
    Laboratóriumi minőségi mérések (Excel forrásból).
    A mintavételezések eredményei a gyártás során.
    """
    __tablename__ = "quality_data"
    
    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, nullable=False)
    machine_id = Column(String(20), ForeignKey("machines.id"))
    article_id = Column(String(50), ForeignKey("articles.id"))
    
    moisture_pct = Column(Float)  # Mért nedvességtartalom (%)
    gsm_measured = Column(Float)  # Mért négyzetmétersúly (g/m2)
    strength_knm = Column(Float)  # Mért szakítószilárdság (kNm)
    
    # --- KAPCSOLATOK (Relationships) ---
    machine = relationship("MachineDB", back_populates="quality_data")
    article = relationship("ArticleDB", back_populates="quality_data")

class UtilityConsumptionDB(Base):
    """
    Közmű- és alapanyag-felhasználás (Excel forrásból).
    Napi szintű fogyasztási adatok gépenként.
    """
    __tablename__ = "utility_consumption"
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False, index=True)
    machine_id = Column(String(20), ForeignKey("machines.id"))
    
    water_m3 = Column(Float)        # Frissvíz fogyasztás (m3)
    electricity_kwh = Column(Float)  # Villamosenergia fogyasztás (kWh)
    steam_tons = Column(Float)       # Gőzfelhasználás (tonna)
    fiber_tons = Column(Float)       # Alapanyag (Rost/Recovered Paper) felvétel (tonna)
    additives_kg = Column(Float)     # Vegyszer/Adalékanyag felhasználás (kg)
    
    # --- KAPCSOLATOK (Relationships) ---
    machine = relationship("MachineDB", back_populates="utilities")

class DailySummaryDB(Base):
    """
    Napi összesítő jelentés (Dashboard alapja).
    Ide kerülnek a MetricsCalculator által kiszámított KPI mutatók.
    Ez a tábla szolgál a Dashboard gyors és hatékony megjelenítéséhez.
    """
    __tablename__ = "daily_summaries"
    
    id = Column(Integer, primary_key=True)
    date = Column(Date, nullable=False, index=True)
    machine_id = Column(String(20), ForeignKey("machines.id"))
    
    # --- KPI MUTATÓK ---
    oee_pct = Column(Float)           # Teljes Eszközhatékonyság (%)
    availability_pct = Column(Float)  # Rendelkezésre állás (%)
    performance_pct = Column(Float)   # Teljesítmény index (%)
    quality_pct = Column(Float)       # Minőségi mutató (%)
    
    # --- MENNYISÉGI ADATOK (Tonna) ---
    total_tons = Column(Float)   # Összes termelt mennyiség (Gross)
    good_tons = Column(Float)    # Értékesíthető minőség (Net)
    scrap_tons = Column(Float)   # Selejt mennyisége
    target_tons = Column(Float)  # Tervezett mennyiség
    
    # --- HATÉKONYSÁG ÉS SEBESSÉG ---
    total_downtime_min = Column(Float) # Összes állásidő (perc)
    break_count = Column(Integer)      # Szakadások száma (db)
    avg_speed_m_min = Column(Float)    # Súlyozott átlagsebesség (m/min)
    target_speed_m_min = Column(Float) # Súlyozott tervsebesség (m/min)
    
    # --- MINŐSÉGI ÁTLAGOK ---
    avg_moisture_pct = Column(Float)   # Átlagos nedvesség (%)
    avg_gsm_measured = Column(Float)   # Átlagos mért GSM (g/m2)
    
    # --- FAJLAGOS MUTATÓK (Egységnyi késztermékre vetítve) ---
    spec_electricity_kwh_t = Column(Float) # Fajlagos áram (kWh/t)
    spec_water_m3_t = Column(Float)        # Fajlagos víz (m3/t)
    spec_steam_t_t = Column(Float)         # Fajlagos gőz (t/t)
    spec_fiber_t_t = Column(Float)         # Fajlagos rost (t/t)

    # --- KAPCSOLATOK (Relationships) ---
    machine = relationship("MachineDB", back_populates="daily_summaries")

# --- VALIDÁTOR ÉS ADATÁTVITELI MODELLEK (PYDANTIC) ---

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
    """Állapot-validált termelési esemény."""
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
    """Állapot-validált termelési terv."""
    date: date
    machine_id: str
    article_id: str
    target_quantity_tons: float
    target_speed: float
    model_config = ConfigDict(from_attributes=True)

class QualityMeasurement(BaseModel):
    """Állapot-validált labor eredmény."""
    timestamp: datetime
    machine_id: str
    article_id: str
    moisture_pct: float
    gsm_measured: float
    strength_knm: float
    model_config = ConfigDict(from_attributes=True)

class UtilityData(BaseModel):
    """Állapot-validált közmű fogyasztás."""
    date: date
    machine_id: str
    water_m3: float
    electricity_kwh: float
    steam_tons: float
    fiber_tons: float
    additives_kg: float
    model_config = ConfigDict(from_attributes=True)

class DailySummary(BaseModel):
    """Állapot-validált KPI összesítő."""
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
