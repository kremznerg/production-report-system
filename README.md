# 📊 Production Report System - Demo Projekt

Ez egy **jól strukturált ETL (Extract-Transform-Load) rendszer** termelési jelentések kezeléséhez. A projekt jelenleg **demo/template állapotban** van, de tiszta architektúrát követ és kiváló alapot ad egy komplex reporting rendszer kiépítéséhez.

## 🎯 Projekt Célja

A rendszer különböző forrásokból (API, Excel fájlok) gyűjt termelési adatokat, validálja őket, majd egy központi SQLite adatbázisba tölti be. A cél egy egységes, strukturált adatbázis létrehozása, amelyből később riportokat és analitikát lehet készíteni.

---

## 📁 Projekt Struktúra

```
production-report-system/
│
├── data/                      # Adatbázis és input fájlok
│   ├── production.db         # SQLite adatbázis (generált)
│   ├── planning.xlsx         # Termelési terv (30 nap × 2 gép = 60 sor)
│   ├── lab_data.xlsx         # Labor mérések (30 nap × ~8 mérés = ~240 sor)
│   └── utilities.xlsx        # Közüzemi fogyasztás (30 nap × 2 gép = 60 sor)
│
├── logs/                      # Alkalmazás naplók (automatikusan létrejön)
│   └── app.log               # Részletes log fájl
│
├── scripts/                   # Futtatható scriptek
│   ├── init_db.py            # Adatbázis inicializálás
│   ├── seed_master_data.py   # Törzsadatok feltöltése
│   ├── create_sample_data.py # ✨ Minta Excel fájlok generálása
│   ├── run_pipeline.py       # ETL pipeline futtatása
│   └── test_logging.py       # Logging rendszer tesztelése
│
├── src/                       # Fő forráskód
│   ├── __init__.py
│   ├── config.py             # Központi konfiguráció (Pydantic Settings)
│   ├── database.py           # SQLAlchemy engine és session kezelés
│   ├── logging_config.py     # Logging beállítások
│   ├── models.py             # Adatbázis modellek (SQLAlchemy + Pydantic)
│   ├── pipeline.py           # Fő ETL pipeline orchestrator
│   │
│   ├── extractors/           # Adatforrás extractorok
│   │   ├── __init__.py
│   │   ├── api_client.py     # API client (termelési események)
│   │   └── excel_reader.py   # Excel olvasó (planning, lab, utilities)
│   │
│   ├── transformers/         # (Üres - jövőbeli data transformation logika)
│   │   └── __init__.py
│   │
│   └── reports/              # (Üres - jövőbeli report generálás)
│       └── __init__.py
│
├── .env.example              # Környezeti változók sablon
├── .gitignore               # Git ignore szabályok
├── requirements.txt         # Python függőségek
└── README.md                # Ez a fájl
```

---

## 🗄️ Adatbázis Modellek

A rendszer **6 fő táblával** dolgozik:

### **1. Törzsadatok (Master Data)**

| Tábla | Leírás | Kulcs Mezők |
|-------|--------|-------------|
| **`machines`** | Gép törzsadatok | `id` (PM1, PM2), `name`, `location` |
| **`articles`** | Termék törzsadatok | `id` (cikkszám), `name`, `nominal_gsm`, `product_group` |

### **2. Tranzakciós adatok (Fact Tables)**

| Tábla | Leírás | Adatforrás | Kulcs Mezők |
|-------|--------|------------|-------------|
| **`production_events`** | Termelési események | API | `timestamp`, `machine_id`, `article_id`, `weight_kg`, `average_speed` |
| **`production_plans`** | Gyártási terv | Excel | `date`, `machine_id`, `article_id`, `target_quantity_tons`, `target_speed` |
| **`quality_reports`** | Labor minőségi mérések | Excel | `timestamp`, `machine_id`, `article_id`, `moisture_pct`, `gsm_measured`, `strength_knm` |
| **`utility_consumption`** | Közüzemi fogyasztás | Excel | `date`, `machine_id`, `water_m3`, `electricity_kwh`, `steam_tons`, `fiber_tons` |

---

## 🔄 ETL Pipeline Működése

A `pipeline.py` központi orchestrator, amely:

### **1. Extract (Kinyerés)**
- **API-ból**: termelési események lekérése (jelenleg placeholder URL)
- **Excel fájlokból**: planning, labor és utility adatok beolvasása pandas segítségével

### **2. Transform (Transzformáció)**
- **Pydantic validáció**: típusellenőrzés, kötelező mezők
- **Dátum konverziók**: egységes datetime/date formátum
- **Hibás adatok kiszűrése**: ValidationError esetén log + skip

### **3. Load (Betöltés)**
- **SQLAlchemy ORM-el** adatbázisba írás
- **Tranzakció kezelés**: automatikus commit/rollback
- **Context manager** alapú session kezelés

---

## ⚙️ Technológiai Stack

| Kategória | Technológia | Verzió Követelmény | Cél |
|-----------|-------------|-------------------|-----|
| **Nyelv** | Python | 3.9+ | Core nyelv |
| **Adatbázis** | SQLite | beépített | Könnyű, fájl alapú adatbázis |
| **ORM** | SQLAlchemy | latest | Adatbázis absztrakció |
| **Validáció** | Pydantic | 2.x | Típus és adatvalidáció |
| **Konfiguráció** | pydantic-settings | latest | .env alapú környezeti változók |
| **Data Processing** | Pandas | latest | Excel adatok beolvasása |
| **Excel olvasás** | openpyxl | latest | .xlsx fájl kezelés |
| **HTTP Kliens** | Requests | latest | API kommunikáció |
| **Logging** | Python logging | beépített | Strukturált naplózás |

---

## 🚀 Használat

### **1. Első indítás (Setup)**

```bash
# 1. Lépj be a projekt könyvtárba
cd production-report-system

# 2. Környezet beállítása (opcionális)
cp .env.example .env
# Szerkeszd a .env fájlt a saját útvonalaiddal, ha szükséges

# 3. Függőségek telepítése
pip install -r requirements.txt

# 4. Adatbázis inicializálás
python scripts/init_db.py

# 5. Törzsadatok feltöltése (demo gépek és termékek)
python scripts/seed_master_data.py

# 6. ✨ Minta Excel fájlok létrehozása (demo adatok)
python scripts/create_sample_data.py
```

### **2. ETL Pipeline futtatása**

```bash
# Most már teljesen működik demo adatokkal!
python scripts/run_pipeline.py

# Ellenőrizd a naplókat
cat logs/app.log   # Linux/Mac
type logs\app.log  # Windows
```

---

## 📋 Főbb Jellemzők

✅ **Tiszta architektúra** - Szeparált extractors, models, pipeline  
✅ **Típusbiztos validáció** - Pydantic modellek minden data layeren  
✅ **Konfiguráció központosítva** - Environment variables (.env)  
✅ **Strukturált logging** - Fájlba (INFO+) és konzolra (WARNING+)  
✅ **Context manager pattern** - Biztonságos adatbázis műveletek, automatikus rollback  
✅ **Moduláris design** - Könnyen bővíthető új adatforrásokkal  
✅ **Type hints** - Teljes kód type annotációkkal  
✅ **Error handling** - Try-except blokkok + logging

---

## 🔧 Fejlesztési Lehetőségek

A projekt jelenleg egy **működőképes demo**, amit már lehet tesztelni minta adatokkal!

### **✅ Elkészült funkciók**
1. ✅ **Adatbázis struktúra** - SQLite alapú, 6 táblával
2. ✅ **ETL Pipeline** - Excel fájlok beolvasása és betöltése
3. ✅ **Minta adat generálás** - `create_sample_data.py` script
4. ✅ **Logging rendszer** - File és konzol alapú naplózás
5. ✅ **Validáció** - Pydantic modellek minden szinten

### **Továbbfejlesztési lehetőségek**
1. ⚠️ **Valós API integráció** - Az `api_client.py`-ban placeholder URL van
2. 📊 **Transformers logika** - Komplex számítások (napi összesítések, hatékonyság mutatók)
3. 📈 **Dashboard** - Streamlit alapú vizualizáció
4. 📝 **Report generálás** - PDF/Excel riportok készítése
5. ⏰ **Ütemezett futtatás** - Cron job / Windows Task Scheduler integráció
6. 🔔 **Alert rendszer** - Email/Slack értesítések hibák esetén
7. 🔄 **Retry logika** - API hívások újrapróbálása
8. 🧪 **Unit tesztek** - pytest alapú tesztek
9. 📏 **Data quality checks** - Automatikus adatminőség ellenőrzések

---

## 🛠️ Konfigurációs Lehetőségek

A `.env` fájlban (vagy környezeti változókban) beállítható:

```bash
# Projekt alapok
PROJECT_NAME=Production Report System
LOG_LEVEL=INFO

# Adatbázis (SQLite)
DATABASE_URL=sqlite:///./data/production.db

# API konfiguráció
API_BASE_URL=https://api.example.com/v1

# Fájl útvonalak (opcionális felülírás)
# PLANNING_FILE=./data/planning.xlsx
# LAB_DATA_FILE=./data/lab_data.xlsx
# UTILITIES_FILE=./data/utilities.xlsx
```

---

## 📖 Kód Példák

### **Adatbázis lekérdezések**

```python
from src.database import get_db
from src.models import MachineDB

# Összes gép lekérdezése
with get_db() as db:
    machines = db.query(MachineDB).all()
    for machine in machines:
        print(f"{machine.id}: {machine.name}")
```

### **Új adat beszúrása**

```python
from src.database import get_db
from src.models import ArticleDB

with get_db() as db:
    new_article = ArticleDB(
        id="ART004",
        name="Special Liner",
        product_group="Premium",
        nominal_gsm=180.0
    )
    db.add(new_article)
    # Az adatbázis automatikusan commit-olódik
```

---

## ⚠️ Megjegyzések és Limitációk

### **Státusz: Működő Demo Projekt**
- ✅ Struktúra és alapvető funkcionalitás kész
- ✅ Excel adatok beolvasása és betöltése működik
- ✅ Minta adatok generálása működik
- ⚠️ Valós API integráció hiányzik (placeholder URL)
- ⚠️ Nincs riport modul (`reports/` mappa üres)
- ⚠️ Nincs transformation logika (`transformers/` mappa üres)
- ⚠️ Csak demo adatokkal működik, valós adatforrásokat be kell kötni

### **SQLite limitációk**
- ⚠️ Egyidejű írás korlátozott
- ⚠️ Nagy adatmennyiségnél lassú lehet
- 💡 Production környezetben érdemes PostgreSQL/MySQL-re váltani

### **Python verzió**
- ✅ Python 3.9+ szükséges (Pydantic 2.x miatt)
- ✅ Tesztelve: Python 3.13

---

## 📞 Támogatás

Ez egy **demo/template projekt**, ami kiváló kiindulási pont egy komplex reporting rendszerhez.

**Következő lépések:**
1. 🔗 **Valós adatforrások bekötése** (API credentials, Excel fájlok)
2. 📊 **Üzleti logika implementálása** (transformers, calculations)
3. 📈 **Vizualizáció hozzáadása** (Streamlit dashboard)
4. 🚀 **Production deployment** (Docker, scheduler, monitoring)

---

## 🎓 Tanulságok és Best Practices

Ez a projekt demonstrálja:

✅ **Layered Architecture** - Tiszta szeparáció (data, business, presentation)  
✅ **Dependency Injection** - Config és database objektumok  
✅ **Single Responsibility** - Minden modul egy feladatot lát el  
✅ **Error Handling** - Minden kritikus ponton try-except  
✅ **Logging Strategy** - File (debug) + Console (warnings)  
✅ **Type Safety** - Pydantic validation + type hints  
✅ **Context Managers** - Biztonságos resource kezelés  
✅ **Demo Data Generation** - Automatikus minta adat létrehozás teszteléshez  

---

**Készült:** 2026. január 22.  
**Státusz:** ✅ Működő Demo Projekt (teljesen futtatható minta adatokkal)  
**Következő feladatok:** Valós adatforrások integrálása, transformers logika, dashboard, riportok
