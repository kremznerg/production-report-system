# 1. Alap kép kiválasztása (Python 3.12 slim verzió a kisebb méret érdekében)
FROM python:3.12-slim

# 2. Munkakönyvtár beállítása a konténeren belül
WORKDIR /app

# 3. Rendszer függőségek telepítése
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 4. Python függőségek másolása és telepítése
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# 5. A teljes forráskód másolása a konténerbe
COPY . .

# 6. Streamlit portjának megnyitása (alapértelmezett: 8501)
EXPOSE 8501

# 7. Egészségügyi ellenőrzés beállítása (opcionális, de ajánlott)
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# 8. Az alkalmazás indítása
ENTRYPOINT ["streamlit", "run", "ui/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
