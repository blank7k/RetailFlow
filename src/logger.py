
import logging
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

log_dir = PROJECT_ROOT / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(
            log_dir / "retailflow.log",
            encoding="utf-8"
        ),
        logging.StreamHandler()
    ],
    force=True
)

logger = logging.getLogger("retailflow")
