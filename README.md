# EcoPaper Solutions - Operations Dashboard

Egy papíripari (és általános gyártási) környezetre tervezett termelési dashboard és ETL folyamatkezelő rendszer.
A rendszer célja a különböző forrásokból (MES - Manufacturing Execution System adatbázis és hálózati Excel fájlok) érkező nyers gyártási adatok kinyerése, tisztítása, aggregálása és vizualizációja, kiegészítve automatizált PDF riportgenerálással.

## Funkcionalitás
- **Adatkinyerés (Extract):** Közvetlen kapcsolat külső MES adatbázissal (PostgreSQL) gépi események (RUN, STOP, BREAK) letöltéséhez. Opcionális hálózati mappás Excel-olvasó technológia a minőségi, közmű és termelési tervek kezelésére.
- **Adatvédelem és Validáció:** Pydantic alapú típusellenőrzés (Anti-Corruption Layer) az adatintegritás megőrzésére a betöltésekkor.
- **Üzleti Logika (Transformers):** Automatikus aggregálás (OEE számítás, fajlagos energiafogyasztás). A kiszámolt adatok biztonságos Upsert (Delete-then-Insert) metodikával kerülnek a fő adatbázisba, támogatva az ismételt futtatásokat (Idempotens architektúra).
- **Dashboard (Streamlit + Plotly):**
  - KPI mérőszámok trendvonalakkal (Sparkline).
  - Interaktív gépállapot idősáv (Gantt-diagram).
  - Termékösszetétel oszlop- és tortadiagramokon.
  - Pareto-elemzés a leállási okok elemzésére a kiválasztott visszatekintési intervallum alapján.
- **Jelentés Generálás:** Beépített ReportLab motor magyar ékezetes (Custom Font) nyomtatható PDF riportok generálására a lekérdezett nap alapján.

## Konténerizált Architektúra

A fejlesztési és tesztelési környezet Docker (docker-compose) alapokon nyugszik:

1. **db (5432):** A fő, belső PostgreSQL 15 adatbázis, ami a feldolgozott, riportolásra kész adatokat (pl. napi aggregációkat) tárolja.
2. **mes_db (5433):** Szimulált gyári PostgreSQL 15 adatbázis, az események (nyers adatok) forrása. A port ütközések elkerülése végett 5433-ra natolva kívülről.
3. **adminer (8080):** Könnyűsúlyú vizuális web-kliens a háttér adatbázisok monitorozásához és hibakereséséhez.
4. **dashboard (8501):** Maga a Streamlit alkalmazás, amely az ETL folyamatokat és a UI megjelenítést végzi.

## Csomagstruktúra

```text
production-report-system/
├── ui/                 # Streamlit felület (Frontend), UI komponensek, PDF generáló
├── src/                # Backend üzleti logika, ETL pipeline (Extractor, Transformer) és SQLAlchemy modellek
├── scripts/            # Karbantartó scriptek (Adatbázis inicializálás, szimulációs mintaadat-gyártás)
├── tests/              # Pytest Unit tesztek
├── data/network_share/ # Szimulált hálózati mappa a Labor és Közmű Excel fájloknak
├── logs/               # Rendszer log fájlok
├── assets/             # Statikus fájlok (Logók, betűtípusok)
├── Dockerfile          # Dashboard build konfiguráció
└── docker-compose.yml  # Konténer orchestráció
```

## Telepítés és Futtatás

A javasolt indítás Docker Engine használatával történik.

1. **A rendszer felépítése és elindítása:**
   ```bash
   docker-compose up -d --build
   ```

2. **Kezdeti adatok feltöltése (Első indításkor):**
   Mivel ez a rendszer demózásra/vizsgára fókuszál, a `scripts` mappában található szkriptekkel lépésről-lépésre inicializálható és feltölthető az adatvédett adatbázis:
   
   ```bash
   # 1. Adatbázis sémák (SQL Táblák) felépítése a semmiből
   docker exec -it production_dashboard python3 scripts/init_db.py

   # 2. Alapadatok (Gép, Termék törzsadatok) betöltése az üres táblákba
   docker exec -it production_dashboard python3 scripts/seed_master_data.py

   # 3. Teljes demó környezet telepítése (Nyers adatok generálása Excelbe és MES-be)
   docker exec -it production_dashboard python3 scripts/create_sample_data.py
   ```

A dashboard a böngészőből elérhető a [http://localhost:8501](http://localhost:8501) címen.
A webes adatbáziskezelő az [http://localhost:8080](http://localhost:8080) címen található.

## Tesztelés
A forráskód ellenőrzése és az egységtesztek futtatása parancssorból:
```bash
python3 -m pytest tests/
```
