"""
ADATBÁZIS KAPCSOLAT KEZELŐ (DATABASE LAYER)
===========================================
Ez a modul felelős a PostgreSQL adatbázis kapcsolódásáért, munkamenetek (Sessions) 
kezeléséért és az adatbázis sémák inicializálásáért. A SQLAlchemy ORM 
technológiát használjuk az adatok kezeléséhez.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator

from .config import settings
from .models import Base

engine = create_engine(
    settings.DATABASE_URL,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db() -> None:
    """
    Adatbázis inicializálása.
    Létrehozza az összes táblát a 'src/models.py'-ban definiált sémák alapján.
    Ha a táblák már léteznek, nem történik változás.
    """
    Base.metadata.create_all(bind=engine)
    print(f"Adatbázis sémák inicializálva")

@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Biztonságos adatbázis-kapcsolat kezelő (Context Manager).
    Biztosítja, hogy minden művelet végén a munkamenet lezáruljon, 
    illetve hiba esetén tranzakciós visszagörgetést (rollback) végez.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
