from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config.config import LANG_FILES
import logging

logger = logging.getLogger(__name__)

def get_phone_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [[KeyboardButton(text="Отправить мой номер", request_contact=True)]]
    return ReplyKeyboardMarkup(keyboard=keyboard, one_time_keyboard=True, resize_keyboard=True)

def get_test_selection_keyboard(tests_json):
    """
    Создаёт клавиатуру с выбором тестов по ID.
    Каждый тест представлен как кнопка с его ID.
    """
    try:
        logger.info(f"get_test_selection_keyboard received data type: {type(tests_json)}")
        logger.info(f"Tests JSON length: {len(tests_json) if tests_json else 0}")
        
        buttons = []

        # Берём все уникальные ID шаблонов тестов
        template_ids = set()  # используем set для уникальности
        
        for q in tests_json:
            template = q.get('exam_center_test_template')
            if template and isinstance(template, dict):
                template_id = template.get('id')
                if template_id:
                    template_ids.add(template_id)

        logger.info(f"Found unique template IDs: {sorted(template_ids)}")

        # Создаём кнопки для каждого уникального ID
        for template_id in sorted(template_ids):
            button_text = f"📝 Тест ID: {template_id}"
            buttons.append([KeyboardButton(text=button_text)])
            logger.info(f"Created button: {button_text}")

        if not buttons:
            logger.warning("No template IDs found, creating default button")
            buttons.append([KeyboardButton(text="📝 Тест по умолчанию")])

        # Создаём клавиатуру
        keyboard = ReplyKeyboardMarkup(
            keyboard=buttons,
            resize_keyboard=True
        )

        logger.info(f"Created keyboard with {len(buttons)} buttons")
        return keyboard
        
    except Exception as e:
        logger.error(f"Failed to load tests from JSON: {e}")
        logger.error(f"Exception type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        # Возвращаем базовую клавиатуру в случае ошибки
        return ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📝 Тест")]],
            resize_keyboard=True
        )


STOP_BUTTON = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="🛑 Стоп")]],
    resize_keyboard=True
)

def main_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🚀 Начать тест")],
            [KeyboardButton(text="🌐 Установить язык")]
        ],
        resize_keyboard=True
    )

def language_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=f"🌐 {lang.upper()}") for lang in LANG_FILES]
        ]
    )