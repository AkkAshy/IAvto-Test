from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, ContentType
from keyboards.reply import get_phone_keyboard, main_menu, language_menu
from database.db import get_user, add_user
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config.config import LANG_FILES
from database.db import set_user_language, get_user_language
import logging
from services.quiz_service import t

logger = logging.getLogger(__name__)


router = Router()

@router.message(CommandStart())
async def start(message: Message):
    # Получаем язык пользователя (например, из БД)
    lang = await get_user_language(message.from_user.id)

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
    
    # Сохраняем пользователя в БД
    await add_user(telegram_id, phone_number)
    
    # Отправляем главное меню
    await message.answer(
        f"Спасибо, бро! Твой номер: {phone_number} сохранён ✅\n"
        "Теперь можешь начать викторину! 🚀",
        reply_markup=main_menu()
    )


@router.message(F.text == "🌐 Установить язык")
async def select_language(message: Message):
    await message.answer("Выберите язык:", reply_markup=language_menu())



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
        f"Язык установлен на {lang_code.upper()} ✅",
        reply_markup=main_menu()
    )



@router.message(F.text == "🛑 Стоп")
async def stop(message: Message):
    await message.answer("До свидания, бро! 😎",reply_markup=main_menu())