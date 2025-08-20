from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, ContentType
from keyboards.reply import get_phone_keyboard, main_menu, language_menu
from database.db import get_user, add_user, set_user_language, get_user_language
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config.config import LANG_FILES
import logging
from services.quiz_service import t

logger = logging.getLogger(__name__)
router = Router()

# Кэш для переводов кнопок (создается один раз)
LANGUAGE_BUTTON_CACHE = None
TEST_BUTTON_CACHE = None
STOP_BUTTON_CACHE = None

def get_language_buttons_cache():
    """Возвращает все переводы кнопки 'Установить язык' на всех языках"""
    global LANGUAGE_BUTTON_CACHE
    if LANGUAGE_BUTTON_CACHE is None:
        LANGUAGE_BUTTON_CACHE = []
        for lang_code in LANG_FILES.keys():
            try:
                translation = t(lang_code, "menu.language")
                if translation and translation != "menu.language":
                    LANGUAGE_BUTTON_CACHE.append(translation)
            except:
                continue
        logger.info(f"Language buttons cache: {LANGUAGE_BUTTON_CACHE}")
    return LANGUAGE_BUTTON_CACHE

def get_test_buttons_cache():
    """Возвращает все переводы кнопки 'Начать тест' на всех языках"""
    global TEST_BUTTON_CACHE
    if TEST_BUTTON_CACHE is None:
        TEST_BUTTON_CACHE = []
        for lang_code in LANG_FILES.keys():
            try:
                translation = t(lang_code, "menu.test")
                if translation and translation != "menu.test":
                    TEST_BUTTON_CACHE.append(translation)
            except:
                continue
        logger.info(f"Test buttons cache: {TEST_BUTTON_CACHE}")
    return TEST_BUTTON_CACHE

def get_stop_buttons_cache():
    """Возвращает все переводы кнопки 'Стоп' на всех языках"""
    global STOP_BUTTON_CACHE
    if STOP_BUTTON_CACHE is None:
        STOP_BUTTON_CACHE = []
        for lang_code in LANG_FILES.keys():
            try:
                translation = t(lang_code, "menu.stop")
                if translation and translation != "menu.stop":
                    STOP_BUTTON_CACHE.append(translation)
            except:
                continue
        logger.info(f"Stop buttons cache: {STOP_BUTTON_CACHE}")
    return STOP_BUTTON_CACHE

@router.message(CommandStart())
async def start(message: Message):
    # Получаем язык пользователя (например, из БД)
    lang = await get_user_language(message.from_user.id)
    if not lang:
        lang = "kk"  # язык по умолчанию

    user = await get_user(message.from_user.id)

    if user:
        await message.answer(
            t(lang, "start_message.registered").format(phone=user.phone_number),
            reply_markup=main_menu(lang)
        )
    else:
        await message.answer(
            t(lang, "start_message.not_registered"),
            reply_markup=get_phone_keyboard(lang)
        )

@router.message(F.content_type == ContentType.CONTACT)
async def handle_contact(message: Message):
    contact = message.contact
    phone_number = contact.phone_number
    telegram_id = message.from_user.id
    
    # Получаем язык пользователя
    lang = await get_user_language(telegram_id)
    if not lang:
        lang = "kk"  # язык по умолчанию
    
    # Сохраняем пользователя в БД
    await add_user(telegram_id, phone_number)
    
    # Отправляем главное меню с локализацией
    await message.answer(
        t(lang, "contact.saved").format(phone=phone_number),
        reply_markup=main_menu(lang)
    )

# Динамический обработчик кнопки "Установить язык"
@router.message(F.text.in_(get_language_buttons_cache()))
async def select_language(message: Message):
    lang = await get_user_language(message.from_user.id) or "kk"
    await message.answer(t(lang, "language.select"), reply_markup=language_menu())

# Обработчик выбора конкретного языка
@router.message(F.text.in_([f"🌐 {lang.upper()}" for lang in LANG_FILES]))
async def select_language_to_test(message: Message):
    text = message.text.strip()

    possible_buttons = [f"🌐 {lang.upper()}" for lang in LANG_FILES]
    if text not in possible_buttons:
        return

    lang_code = text.split()[1].lower()  # достаём именно код: kiril, ru, uz, kk

    # Сохраняем только код языка
    await set_user_language(message.from_user.id, lang_code)

    await message.answer(
        t(lang_code, "language.set").format(lang=lang_code.upper()),
        reply_markup=main_menu(lang_code)
    )

# Динамический обработчик кнопки "Стоп"
@router.message(F.text.in_(get_stop_buttons_cache()))
async def stop(message: Message):
    lang = await get_user_language(message.from_user.id) or "kk"
    await message.answer(
        t(lang, "commands.goodbye"),
        reply_markup=main_menu(lang)
    )