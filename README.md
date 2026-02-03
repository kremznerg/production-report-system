# 📊 EcoPaper Solutions - Operations Dashboard 🚀

Ez egy professzionális, ipari környezetre tervezett **ETL (Extract-Transform-Load) és Vizualizációs rendszer** papírgyári termelési jelentések kezeléséhez. A projekt egy teljes körű megoldást kínál az adatgyűjtéstől az automatizált PDF jelentéskészítésig.

https://eps-dashboard.streamlit.app/

---

## 🏗️ Főbb Mérföldkövek & Funkciók

A rendszer mára túllépett a demo fázison, és az alábbi professzionális funkciókkal rendelkezik:

- ✅ **Interaktív Dashboard**: Streamlit alapú vezérlőpult KPI mutatókkal, trendgrafikonokkal és Pareto-elemzéssel.
- ✅ **OEE Számítás**: Teljes eszközhatékonyság (Availability × Performance × Quality) automatikus kalkulációja.
- ✅ **Automatizált PDF Export**: Nyomdakész, magyar nyelvű napi termelési jelentések generálása céges logóval.
- ✅ **Adatintegritás**: Pydantic alapú validáció és Upsert logika az adatok duplikációja ellen.
- ✅ **Unit Tesztelés**: Átfogó tesztcsomag (pytest) a kalkulációs logika és az adatbetöltés ellenőrzésére.
- ✅ **CI/CD Pipeline**: GitHub Actions integráció, amely minden kódmódosításnál automatikusan futtatja a teszteket.
- ✅ **Dockerizálás**: Teljes körű konténerizáció a könnyű és gyors telepíthetőség érdekében.

---

## 📁 Projekt Struktúra

```
production-report-system/
│
├── .github/workflows/         # CI/CD konfiguráció (GitHub Actions)
├── assets/                    # Céges logó és UI ikonok
├── data/                      # SQLite adatbázis és bemeneti Excel fájlok
├── logs/                      # Rendszernaplók (app.log)
├── scripts/                   # Karbantartó és adatgeneráló scriptek
├── src/                       # Üzleti logika (Pipeline, Kalkulációk, Modellek)
│   ├── extractors/            # Adatforrás kezelők (Excel, MES API)
│   ├── transformers/          # KPI és OEE számítási logika
│   └── reports/               # Jelentéskészítő modulok
├── tests/                     # Unit és Integrációs tesztek (pytest)
├── ui/                        # Streamlit Dashboard forráskódja
│   └── pdf_export.py          # PDF generáló motor (ReportLab)
├── Dockerfile                 # Konténer recept
├── docker-compose.yml         # Többkonténeres futtatási konfiguráció
└── requirements.txt           # Python függőségek
```

---

## 🚀 Gyorsindítás (Getting Started)

### **A) Futtatás Dockerrel (Ajánlott)**
A legegyszerűbb módja a rendszer indításának, nem igényel helyi Python telepítést:

```bash
docker-compose up --build
```
Ezután nyisd meg a böngészőben: `http://localhost:8501`

### **B) Helyi futtatás (Fejlesztéshez)**

1. **Függőségek telepítése:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Adatbázis és mintaadatok inicializálása:**
   ```bash
   python scripts/init_db.py
   python scripts/seed_master_data.py
   python scripts/create_sample_data.py
   ```

3. **Pipeline és Dashboard indítása:**
   ```bash
   python scripts/run_pipeline.py
   streamlit run ui/app.py
   ```

---

## 🧪 Minőségbiztosítás (Testing)

A projekt kiemelt figyelmet fordít a stabilitásra. A tesztek futtatása:

```bash
PYTHONPATH=. pytest tests/
```

Minden `push` művelet után a **GitHub Actions** automatikusan elvégzi ezt az ellenőrzést, biztosítva, hogy csak működő kód kerüljön a tárolóba.

---

A projekt az **EcoPaper Solutions** fiktív vállalat számára készült ipari esettanulmányként. 

**Technológiai stack:**
- **Backend:** Python 3.12, SQLAlchemy, Pydantic
- **Frontend:** Streamlit, Plotly
- **Reporting:** ReportLab (PDF)
- **DevOps:** Docker, GitHub Actions

---
*Készült: Kremzner Gábor - 2026*
