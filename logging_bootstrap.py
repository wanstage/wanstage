import logging
import logging.handlers
import os
import sys
import warnings

LOG_DIR = os.path.expanduser("~/WANSTAGE/logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "app.log")
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
fh = logging.handlers.TimedRotatingFileHandler(
    LOG_FILE, when="midnight", backupCount=14, encoding="utf-8"
)
fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s - %(message)s"))
fh.setLevel(logging.DEBUG)
ch = logging.StreamHandler(sys.stdout)
ch.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
ch.setLevel(logging.WARNING)
logger.handlers.clear()
logger.addHandler(fh)
logger.addHandler(ch)


def _ex(ex_t, ex, tb):
    logging.exception("UNCAUGHT EXCEPTION", exc_info=(ex_t, ex, tb))


sys.excepthook = _ex
logging.captureWarnings(True)
warnings.simplefilter("default")
logging.info("WANSTAGE logger initialized")
