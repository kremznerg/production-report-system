# Production Report System – Mentorált Újraírás Dokumentáció

Ez a dokumentum a projektünk "alkotmánya". Ez alapján dolgozunk, hogy a kód tiszta, anonimizált és szakdolgozati szintű legyen.

## 🎯 Célkitűzések
1. **Mentorált fejlesztés:** A kód logikáját közösen beszéljük át, a megvalósítás tiszta és érthető kell legyen.
2. **Anonimizálás:** Semmilyen cég-specifikus adat (Hamburger, HCB, Prinzhorn, éles jelszavak stb.) nem kerülhet a kódba.
3. **Egyszerűség & Hatékonyság:** A korábbi v3-as projekt 52 fájlját egy moduláris, ~15 fájlos rendszerre cseréljük.

## 🏗️ Architektúra (ETL Pipeline)
A rendszer egy klasszikus Extract-Transform-Load folyamatot követ:

### 1. Extract (Adatnyerés)
Két fő forrásunk van:
- **REST API:** Nyers termelési események (JSON). Itt látjuk, mikor állt vagy ment a gép.
- **Excel fájlok:**
  - `planning.xlsx`: Napi tervek és cikk-specifikus célsebességek.
  - `lab_data.xlsx`: Minőségi mutatók (nedvesség, szakítás, gsm).
  - `utilities.xlsx`: Óraállások (víz, villamos energia).

### 2. Transform (Feldolgozás)
Az `src/transformers/` modul fésüli össze az adatokat:
- Kiszámolja az állásidőket és a futási hatékonyságot.
- A termelési adatokhoz (API) hozzárendeli a tervadatokat (Excel).
- Kiszámolja a fajlagos fogyasztásokat (pl. víz/tonna).

### 3. Load (Tárolás)
Minden feldolgozott adat egy **SQLite** adatbázisba kerül (`data/production.db`). 
- **SQLAlchemy ORM**-et használunk az adatkezeléshez.
- **Pydantic** modellekkel validáljuk az adatokat a mentés előtt.

## 📁 Fájlstruktúra és Felelősségek
- `src/config.py`: Konfiguráció management (Pydantic Settings).
- `src/database.py`: DB kapcsolat és tábla létrehozás.
- `src/models.py`: Adatmodellek (Pydantic & SQLAlchemy).
- `src/extractors/api_client.py`: Az események beolvasása.
- `src/extractors/excel_reader.py`: A labor, terv és óraállások beolvasása.
- `src/transformers/data_transformer.py`: Az üzleti logika helye.
- `src/pipeline.py`: A teljes folyamatot vezérlő script.
- `ui/dashboard.py`: Streamlit interaktív Dashboard.

## 🎓 Mentori Irányelvek
- Használjunk explicit típusjelöléseket (Type Hinting).
- Minden funkcióhoz írjunk Docstring-et (miért és mit csinál).
- Kerüljük a "mágikus számokat", mindent configból vagy konstansokból kezeljünk.
