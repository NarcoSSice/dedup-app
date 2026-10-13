import logging

from core.settings import settings

logger = logging.getLogger("dedup")
logger.setLevel(getattr(logging, settings.LOG_LEVEL, logging.INFO))

handler = logging.StreamHandler()
formatter = logging.Formatter("[%(asctime)s] %(levelname)s in %(module)s: %(message)s")
handler.setFormatter(formatter)

logger.addHandler(handler)
