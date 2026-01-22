# 🚀 Gyors Indítási Útmutató

## Egyszerű Setup (3 lépés)

### Windows felhasználóknak:

```bash
# 1. Telepítsd a függőségeket
pip install -r requirements.txt

# 2. Futtasd a setup scriptet
setup_demo.bat

# 3. Kész! Futtasd az ETL-t
python scripts\run_pipeline.py
```

### Linux/Mac felhasználóknak:

```bash
# 1. Telepítsd a függőségeket
pip install -r requirements.txt

# 2. Futtasd a setup lépéseket manuálisan
python scripts/init_db.py
python scripts/seed_master_data.py
python scripts/create_sample_data.py

# 3. Kész! Futtasd az ETL-t
python scripts/run_pipeline.py
```

---

## Mi történik a háttérben?

1. **init_db.py** - Létrehozza a SQLite adatbázist (6 táblával)
2. **seed_master_data.py** - Feltölti a törzsadatokat (2 gép, 3 termék)
3. **create_sample_data.py** - Generál 3 Excel fájlt demo adatokkal
4. **run_pipeline.py** - Beolvassa az Excel fájlokat és betölti az adatbázisba

---

## Hasznos parancsok

```bash
# Adatbázis tartalmának megtekintése
python scripts/inspect_db.py

# Log fájl ellenőrzése
type logs\app.log          # Windows
cat logs/app.log           # Linux/Mac

# Újraindítás tiszta lappal (törli az adatbázist és Excel fájlokat)
del data\*.db data\*.xlsx  # Windows
rm data/*.db data/*.xlsx   # Linux/Mac
```

---

## Fájlok a `data/` mappában a setup után:

- ✅ `production.db` - SQLite adatbázis (~360 rekord)
- ✅ `planning.xlsx` - Termelési terv (60 sor - 30 nap × 2 gép)
- ✅ `lab_data.xlsx` - Labor mérések (~240 sor - 30 nap)
- ✅ `utilities.xlsx` - Közüzemi adatok (60 sor - 30 nap × 2 gép)

---

## Következő lépések

A demo működik! Most már hozzáadhatsz:

1. 📊 **Dashboard** - Streamlit alapú vizualizáció
2. 📈 **Riportok** - Excel/PDF export
3. 🔗 **Valós adatforrások** - API integráció
4. 🧮 **Transformers** - Komplex számítások

Részletek: Lásd a **README.md** fájlt
