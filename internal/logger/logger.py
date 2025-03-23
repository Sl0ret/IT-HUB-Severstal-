import logging
import os
from logging.config import fileConfig

def setup_logger():
    os.makedirs("logs", exist_ok=True)
    fileConfig("instance/logging.ini")
    return logging.getLogger("api")

logger: logging.Logger = setup_logger()