# 🎓 Szakdolgozat Fejlesztési Terv & Javítások

## 1. Adat-Integritás és Robusztusság (Data Integrity)

- [X] **Upsert Logika**: Az Excel alapú adatok (terv, labor, közmű) és események törlése/újrabeszúrása megvalósítva (duplikáció elleni védelem).
- [X] **Tranzakciókezelés**: SQLAlchemy session context manager használata (automatikus commit/rollback).

## 2. Üzleti Logika és Adatfeldolgozás (Transformers)

- [X] **OEE Számítás**: Teljes Eszközhatékonyság (Availability × Performance × Quality) implementálva.
- [X] **Súlyozott Mutatók**: Tényleges és tervezett sebesség idő/tonna alapú súlyozása a módszertani pontosság érdekében.
- [X] **Bővített KPI-ok**: `DailySummaryDB` bővítve: állásidő, szakadásszám, fajlagos rostfelhasználás (fiber), minőségi átlagok és terv/tény összehasonlítás.
- [X] **Dinamikus Gépkezelés**: Pipeline automatikusan lekérdezi az aktív gépeket a törzsadatokból.

## 3. Tesztelés (Software Quality Assurance)

- [X] **Unit Tesztek**: Pydantic modellek és kalkulációs logika tesztelése.
- [X] **Integrációs Tesztek**: Excel olvasók és adatbázis réteg tesztelése.
- [X] **Pipeline Teszt**: A teljes folyamat vezérlésének ellenőrzése.

## 4. Automatizálás és DevOps

- [X] **GitHub Actions**: Automatikus CI pipeline létrehozása (minden push-ra lefutó tesztek).
- [ ] **Dockerizálás**: Az alkalmazás konténerbe csomagolása a könnyű telepíthetőségért.

## 5. Vizualizáció és Felhasználói Élmény (UI/UX)

- [X] **KPI Sparklines**: Az elmúlt 7 nap trendjének megjelenítése a fő mutatók (OEE, Termelés) mellett apró grafikonokkal.
- [ ] **Modern Ikonográfia**: Professzionális, egységes ikonrendszer bevezetése a Dashboardon az emojik helyett.
- [X] **PDF Export**: Automatikus magyar nyelvű napi jelentés generálása.

---

*Készült a szoftverfejlesztési folyamat monitorozására és a szakdolgozati követelmények teljesítésére.*
