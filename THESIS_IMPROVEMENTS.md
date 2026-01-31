# 🎓 Szakdolgozat Fejlesztési Terv & Javítások

## 1. Adat-Integritás és Robusztusság (Data Integrity)
- [x] **Upsert Logika**: Az Excel alapú adatok (terv, labor, közmű) és események törlése/újrabeszúrása megvalósítva (duplikáció elleni védelem).
- [x] **Tranzakciókezelés**: SQLAlchemy session context manager használata (automatikus commit/rollback).

## 2. Üzleti Logika és Adatfeldolgozás (Transformers)
- [x] **OEE Számítás**: Teljes Eszközhatékonyság (Availability × Performance × Quality) implementálva.
- [x] **Súlyozott Mutatók**: Tényleges és tervezett sebesség idő/tonna alapú súlyozása a módszertani pontosság érdekében.
- [x] **Bővített KPI-ok**: `DailySummaryDB` bővítve: állásidő, szakadásszám, fajlagos rostfelhasználás (fiber), minőségi átlagok és terv/tény összehasonlítás.
- [x] **Dinamikus Gépkezelés**: Pipeline automatikusan lekérdezi az aktív gépeket a törzsadatokból.

## 3. Tesztelés (Software Quality Assurance)
- [ ] **Unit Tesztek**: Pydantic modellek és validációs logika tesztelése.
- [ ] **Integrációs Tesztek**: Excel olvasók és adatbázis réteg tesztelése.
- [ ] **Pipeline Teszt**: A teljes folyamat végigfuttatása teszt környezetben.

## 5. Vizualizáció és Felhasználói Élmény (UI/UX)
- [ ] **KPI Sparklines**: Az elmúlt 7 nap trendjének megjelenítése a fő mutatók (OEE, Termelés) mellett apró grafikonokkal.
- [ ] **Modern Ikonográfia**: Professzionális, egységes ikonrendszer bevezetése a Dashboardon az emojik helyett.
- [ ] **PDF Export**: Automatikus "Műszaknapló" generálása PDF formátumban a napi eredményekből.

---
*Készült a szoftverfejlesztési folyamat monitorozására és a szakdolgozati követelmények teljesítésére.*
