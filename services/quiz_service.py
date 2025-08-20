import json
import os
import aiofiles
from aiogram.types import FSInputFile
from config.config import  IMAGES_DIR, LANG_FILES
from utils.logging import setup_logging
from database.db import get_user_language

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
logger = setup_logging()

async def select_quiz(user_id: int):
    lang = await get_user_language(user_id)


    logger.info(f"User {user_id} language from DB: {lang}")
    return await load_quiz_data(lang)

async def load_quiz_data(lang: str):

    logger.info(f"load_quiz_data called with parameter: '{lang}'")
    logger.info(f"Parameter type: {type(lang)}")
    
    # Находим путь к JSON-файлу
    relative_path = LANG_FILES.get(lang)
    logger.info(f"LANG_FILES lookup result: {relative_path}")
    # Находим путь к JSON-файлу
    relative_path = LANG_FILES.get(lang)
    if not relative_path:
        logger.error(f"No quiz file mapped for language: {lang}")
        raise ValueError(f"Нет файла тестов для языка: {lang}")

    json_file_path = os.path.join(BASE_DIR, "..", relative_path)  # абсолютный путь
    json_file_path = os.path.abspath(json_file_path)

    logger.info(f"Resolved absolute path for {lang}: {json_file_path}")

    # Проверяем, существует ли файл
    if not os.path.exists(json_file_path):
        logger.error(f"Quiz file does not exist: {json_file_path}")
        raise FileNotFoundError(f"Файл {json_file_path} не найден")

    # Читаем JSON
    try:
        async with aiofiles.open(json_file_path, mode="r", encoding="utf-8") as file:
            content = await file.read()
            data = json.loads(content)
            logger.info(f"Successfully loaded quiz data from {json_file_path}")
            return data
    except Exception as e:
        logger.error(f"Failed to load quiz data from {json_file_path}: {e}")
        raise


async def load_image(image_path: str):
    
    try:
        # Убираем начальный слэш и префикс 'images/'
        clean_path = image_path.lstrip("/").removeprefix("images/")
        full_path = os.path.join(IMAGES_DIR, clean_path)

        if not os.path.exists(full_path):
            logger.error(f"Image file does not exist: {full_path}")
            raise FileNotFoundError(f"Image file does not exist: {full_path}")

        logger.info(f"Successfully loaded image: {full_path}")
        return FSInputFile(full_path)

    except Exception as e:
        logger.error(f"Failed to load image {image_path}: {e}")
        raise


BASE_DIR = os.path.dirname(os.path.abspath(__file__))  
TRANSLATIONS_PATH = os.path.join(BASE_DIR, "translations.json")

with open(TRANSLATIONS_PATH, "r", encoding="utf-8") as f:
    translations = json.load(f)

def t(lang: str, key: str):
    """ Получить перевод по ключу """
    parts = key.split(".")
    text = translations.get(lang, translations["ru"])
    for part in parts:
        text = text.get(part, None)
        if text is None:
            return key  # если ключа нет
    return text
