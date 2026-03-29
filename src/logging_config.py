"""
NAPLÓZÁSI RENDSZER (LOGGING CONFIGURATION)
==========================================
Ez a modul felelős az alkalmazás szintű eseményrögzítésért.
Két kimenetet kezelünk párhuzamosan:
1. Konzol: Csak a figyelmeztetések és hibák megjelenítéséhez.
2. Fájl (logs/app.log): Minden fontos esemény (INFO) rögzítéséhez.
"""

import logging
import sys
from pathlib import Path

def setup_logging(log_level: str = "INFO") -> None:
    """
    Konfigurálja az alkalmazás naplózási rendszerét.
    
    A funkció létrehozza a 'logs/' könyvtárat, beállítja az üzenetek formátumát 
    és szétválasztja a kimeneti csatornákat.
    
    Args:
        log_level (str): A minimális naplózási szint (DEBUG, INFO, WARNING, ERROR).
                        Alapértelmezett: INFO.
    """
    log_dir = Path(__file__).resolve().parent.parent / "logs"
    log_dir.mkdir(exist_ok=True)
    
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    
    file_handler = logging.FileHandler(log_dir / "app.log", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    
    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt=date_format,
        handlers=[console_handler, file_handler]
    )
    
    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        root_logger.handlers.clear()
        
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    root_logger.setLevel(log_level)
    
    logging.info("--- A naplózási rendszer sikeresen elindult ---")
