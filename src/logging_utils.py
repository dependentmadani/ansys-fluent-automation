from __future__ import annotations
import logging
import os

# Default log level can be overridden by setting WING_AERO_LOGLEVEL env var
_DEFAULT_LEVEL = os.environ.get("WING_AERO_LOGLEVEL", "INFO").upper()

def get_logger(name: str = "wing_aero", level: str = _DEFAULT_LEVEL) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logging.basicConfig(level=getattr(logging, level, logging.INFO),
                            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    logger.setLevel(getattr(logging, level, logging.INFO))
    return logger