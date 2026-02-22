"""
ADATBÁZIS KAPCSOLAT KEZELŐ (DATABASE LAYER)
===========================================
Ez a modul felelős az SQLite adatbázis kapcsolódásáért, munkamenetek (Sessions) 
kezeléséért és az adatbázis sémák inicializálásáért. A SQLAlchemy ORM 
technológiát használjuk az adatok kezeléséhez.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator

from .config import settings
from .models import Base

# --- SQLALCHEMY ENGINE INICIALIZÁLÁSA ---
# Az SQLite adatbázis szálkezelésének engedélyezése a check_same_thread=False kapcsolóval
engine_kwargs = {}
if settings.DATABASE_URL.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    **engine_kwargs
)

# Adatbázis munkamenet gyár (Session Factory)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db() -> None:
    """
    Adatbázis inicializálása.
    Létrehozza az összes táblát a 'src/models.py'-ban definiált sémák alapján.
    Ha a táblák már léteznek, nem történik változás.
    """
    Base.metadata.create_all(bind=engine)
    print(f"✅ Adatbázis sémák inicializálva: {settings.DATABASE_URL}")

@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Biztonságos adatbázis-kapcsolat kezelő (Context Manager).
    Biztosítja, hogy minden művelet végén a munkamenet lezáruljon, 
    illetve hiba esetén tranzakciós visszagörgetést (rollback) végez.
    
    Használata:
        with get_db() as db:
            db.query(...)
            
    Yields:
        Generator[Session, None, None]: Aktív adatbázis munkamenet.
    """
    db = SessionLocal()
    try:
        yield db
        # Alapértelmezett commit a tranzakció végén
        db.commit()
    except Exception as e:
        # Hiba esetén azonnali visszagörgetés az adatkonzisztencia megőrzése érdekében
        db.rollback()
        raise e
    finally:
        # Kapcsolat lezárása a memóriaszivárgás elkerülésére
        db.close()
