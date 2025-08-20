from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_quiz_keyboard(question_id: int, answers: list) -> InlineKeyboardMarkup:
    buttons = []
    for answer in answers:
        # Текст кнопки — из тела ответа
        answer_text = next((item["value"] for item in answer["body"] if item["type"] == 1), "???")
        answer_id = answer["id"]
        
        buttons.append([
            InlineKeyboardButton(
                text=answer_text,
                callback_data=f"answer_{question_id}_{answer_id}"
            )
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)