import logging
from config.config import LOG_FILE_PATH

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler(LOG_FILE_PATH),
            logging.StreamHandler()  # Для вывода в консоль
        ]
    )
    return logging.getLogger(__name__)