# EcoPaper Solutions - Operations Dashboard

Ez a projekt egy papírgyári termelési dashboard, ami képes az adatokat MES rendszerből (szimulált Postgres) és Excel fájlokból (labor, közmű) összesíteni, majd ezekből PDF riportot generálni.

Demo: https://eps-dashboard.streamlit.app/

## Felépítés

A rendszer Docker konténerekben fut, hogy ne kelljen a helyi gépen adatbázisokkal bajlódni:

1.  **mes_db**: PostgreSQL konténer, ez szimulálja a gyári MES rendszert (nyers adatok).
2.  **production_db**: PostgreSQL konténer, ide kerülnek a feldolgozott, riportolásra kész adatok.
3.  **dashboard**: Maga a Streamlit app, ami az ETL folyamatokat végzi és megjeleníti az adatokat.

## Mappa struktúra

```
production-report-system/
├── ui/assets/          # Logók, betűtípusok
├── data/network_share/ # Labor és közmű Excel fájlok (szimulált hálózat)
├── logs/               # Log fájlok
├── scripts/            # Karbantartó és adatgeneráló scriptek
├── src/                # Üzleti logika, pipeline, adatbázis modellek
├── tests/              # Pytest tesztek
├── ui/                 # Streamlit felület és PDF generáló
├── Dockerfile          # App build recept
└── docker-compose.yml  # A teljes rendszer összefogása
```

## Indítás

### Dockerrel (ajánlott)

1. **Indítás:**
   ```bash
   docker-compose up -d --build
   ```

2. **Adatok feltöltése (csak az első alkalommal):**
   ```bash
   # Alapadatok (gépek, termékek) betöltése
   docker exec -it production_dashboard python3 scripts/seed_master_data.py
   
   # Mintaadatok generálása az Excel fájlokba és a MES adatbázisba
   docker exec -it production_dashboard python3 scripts/create_sample_data.py
   ```

A dashboard a `http://localhost:8501` címen érhető el.

### Tesztelés

Ha szeretnéd ellenőrizni a logikát:
```bash
python3 -m pytest tests/
```
