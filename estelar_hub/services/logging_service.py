"""Rotating application log storage for the standalone Hub."""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from qgis.PyQt.QtCore import QStandardPaths


def configurar_logger(name="EstelarHub"):
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if logger.handlers:
        return logger

    data_path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppLocalDataLocation)
    log_directory = Path(data_path or Path.home() / "AppData" / "Local" / "Estelar Hub") / "logs"
    log_directory.mkdir(parents=True, exist_ok=True)

    handler = RotatingFileHandler(
        log_directory / "estelar-hub.log",
        maxBytes=2_000_000,
        backupCount=5,
        encoding="utf-8",
    )
    handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)s %(name)s [%(threadName)s] %(message)s"
    ))
    logger.addHandler(handler)
    return logger