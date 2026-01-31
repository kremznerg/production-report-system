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

## 4. Technikai Standardok & Polírozás
- [x] **Típusvizsgálat (Type Hinting)**: Teljes körű Python Type Hinting bevezetése a forráskódban.
- [ ] **Konzisztencia**: Angol nyelvű kód és kommentek, magyar/angol UI szétválasztása.
- [ ] **Dokumentáció**: Adatbázis séma (ERD) és Architektúra diagramok készítése.

---
*Készült a szoftverfejlesztési folyamat monitorozására és a szakdolgozati követelmények teljesítésére.*
