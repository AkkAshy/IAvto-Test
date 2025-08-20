import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
API_URL = os.getenv("API_URL")  # URL сервера для тестов

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///quiz_bot.db")
IMAGES_DIR = os.getenv("IMAGES_DIR", "data/images")
JSON_FILE_PATH = os.getenv("JSON_FILE_PATH", "data/kiril.fixed.json")
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "data/quiz_bot.log")


LANG_FILES = {
    "kk": "data/kaa_kiril.fixed.json",   # Каракалпакский
    "kiril": "data/kiril.fixed.json",    # Узб кирилица
    "ru": "data/template_ru.fixed.json", # Русский
    "uz": "data/template_uz.fixed.json"  # Узб латиница
}
