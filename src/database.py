from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
from typing import Generator

from .config import settings
from .models import Base

# SQLite engine létrehozása
engine = create_engine(
    settings.DATABASE_URL,
    echo=False,  
    connect_args={"check_same_thread": False}  
)

# Session factory (adatbázis munkamenetekhez)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db() -> None:
    """
    Létrehozza az összes táblát az adatbázisban (ha még nem léteznek).
    Ezt egyszer kell meghívni a projekt indulásakor.
    """
    Base.metadata.create_all(bind=engine)
    print(f"Adatbázis inicializálva: {settings.DATABASE_URL}")

@contextmanager
def get_db() -> Generator[Session, None, None]:
    """
    Context manager az adatbázis munkamenetek kezeléséhez.
    Biztosítja az automatikus commit/rollback műveleteket.
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
