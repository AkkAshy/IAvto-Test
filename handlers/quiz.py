# from aiogram import Router, F
# from aiogram.types import Message, PollAnswer
# from aiogram.filters import Command
# from sqlalchemy import delete
# from services.quiz_service import load_quiz_data, load_image
# from database.db import add_quiz_progress, update_quiz_progress, get_current_question, get_user, async_session
# from utils.logging import setup_logging
# from database.models import QuizProgress

# router = Router()
# logger = setup_logging()



# @router.message(F.text == "🚀 Начать тест")
# async def start_quiz(message: Message):
    
#     logger.info(f"User {message.from_user.id} started quiz")
#     user = await get_user(message.from_user.id)
#     if not user:
#         logger.warning(f"User {message.from_user.id} not registered")
#         await message.answer("Сначала отправь свой номер через /start, бро! 😎")
#         return
    
#     # Получаем текущий прогресс
#     current_progress = await get_current_question(message.from_user.id)
    
#     # Читаем вопросы из JSON
#     try:
#         quiz_data = await load_quiz_data()
#         logger.info(f"Loaded quiz data with {len(quiz_data[0]['questions'])} questions")
#         # Логируем доступные ID вопросов
#         question_ids = [q["id"] for q in quiz_data[0]["questions"]]
#         logger.info(f"Available question IDs: {question_ids}")
#     except Exception as e:
#         logger.error(f"Failed to load quiz data: {e}")
#         await message.answer("Ошибка загрузки вопросов, бро! Попробуй позже. 😎")
#         return
    
#     # Проверяем, есть ли вопросы
#     if not quiz_data or not quiz_data[0].get("questions"):
#         logger.error("Quiz data is empty or has no questions")
#         await message.answer("Нет вопросов для викторины, бро! 😎")
#         return
    
#     # Определяем ID следующего вопроса
#     if current_progress:
#         # Ищем следующий ID из доступных
#         current_id = current_progress.question_id
#         available_ids = sorted([q["id"] for q in quiz_data[0]["questions"]])
#         next_id = next((id for id in available_ids if id > current_id), None)
#         question_id = next_id if next_id else available_ids[0]  # Если нет следующего, берем первый
#     else:
#         # Берем первый доступный ID
#         question_id = min(q["id"] for q in quiz_data[0]["questions"])
    
#     logger.info(f"User {message.from_user.id} current question_id: {question_id}")
    
#     # Ищем вопрос по ID
#     question = next((q for q in quiz_data[0]["questions"] if q["id"] == question_id), None)
#     if not question:
#         logger.warning(f"No question found for ID {question_id}")
#         await message.answer("Викторина закончена или вопросов больше нет! Молодец, бро! 🚀")
#         return
    
#     # Добавляем вопрос в прогресс
#     try:
#         await add_quiz_progress(message.from_user.id, question_id)
#         logger.info(f"Added quiz progress for user {message.from_user.id}, question {question_id}")
#     except Exception as e:
#         logger.error(f"Failed to add quiz progress: {e}")
#         await message.answer("Ошибка сохранения прогресса, бро! Попробуй позже. 😎")
#         return
    
#     # Извлекаем текст вопроса и путь к изображению
#     try:
#         question_text = next(item["value"] for item in question["body"] if item["type"] == 1)
#         image_path = next((item["value"] for item in question["body"] if item["type"] == 2), None)
#         logger.info(f"Question {question_id} text: {question_text}, image: {image_path}")
#     except Exception as e:
#         logger.error(f"Failed to parse question {question_id}: {e}")
#         await message.answer("Ошибка в формате вопроса, бро! Попробуй позже. 😎")
#         return
    
#     # Подготавливаем варианты ответов для Quiz-Mode
#     try:
#         options = []
#         correct_option_id = None
        
#         for i, answer in enumerate(question["answers"]):
#             # Извлекаем текст ответа из body массива (аналогично вопросу)
#             try:
#                 answer_text = next(item["value"] for item in answer["body"] if item["type"] == 1)
#                 options.append(answer_text)
                
#                 # Проверяем правильность ответа
#                 if answer["check"] == 1:
#                     correct_option_id = i
                    
#             except Exception as e:
#                 logger.error(f"Failed to parse answer {i} for question {question_id}: {e}")
#                 logger.error(f"Answer structure: {answer}")
#                 continue
        
#         if not options:
#             logger.error(f"No valid options found for question {question_id}")
#             await message.answer("Ошибка в вариантах ответа, бро! Попробуй позже. 😎")
#             return
        
#         if correct_option_id is None:
#             logger.error(f"No correct answer found for question {question_id}")
#             logger.error(f"Answers with check field: {[(i, a.get('check')) for i, a in enumerate(question['answers'])]}")
#             await message.answer("Ошибка в вопросе - нет правильного ответа, бро! 😎")
#             return
            
#         logger.info(f"Question {question_id} options: {options}, correct: {correct_option_id}")
#     except Exception as e:
#         logger.error(f"Failed to prepare options for question {question_id}: {e}")
#         logger.error(f"Question structure: {question}")
#         await message.answer("Ошибка подготовки вариантов ответа, бро! Попробуй позже. 😎")
#         return
    
#     # Отправляем вопрос в Quiz-Mode
#     try:
#         if image_path:
#             # Загружаем картинку
#             try:
#                 image_data = await load_image(image_path)
#                 logger.info(f"Loaded image for question {question_id}: {image_path}")
                
#                 # Отправляем картинку отдельно
#                 await message.answer_photo(
#                     photo=image_data,
#                     caption="Вот картинка к вопросу 📸"
#                 )
#             except Exception as e:
#                 logger.error(f"Failed to load image {image_path}: {e}")
#                 # Продолжаем без картинки
        
#         # Отправляем Quiz Poll
#         poll_message = await message.answer_poll(
#             question=question_text,
#             options=options,
#             type="quiz",
#             correct_option_id=correct_option_id,
#             is_anonymous=False,
#             explanation="Проверь свои знания! 🧠",
#             open_period=30
#         )
        
#         # Сохраняем ID опроса для связи с вопросом
#         # В реальном проекте лучше создать отдельную таблицу для этого
#         logger.info(f"Sent quiz poll {poll_message.poll.id} for question {question_id} to user {message.from_user.id}")
        
#     except Exception as e:
#         logger.error(f"Failed to send quiz poll for question {question_id}: {e}")
#         await message.answer("Ошибка отправки опроса, бро! Попробуй позже. 😎")

# @router.poll_answer()
# async def handle_poll_answer(poll_answer: PollAnswer):
#     """Обрабатываем ответы на Quiz Poll"""
#     user_id = poll_answer.user.id
#     selected_option_ids = poll_answer.option_ids
#     poll_id = poll_answer.poll_id
    
#     logger.info(f"User {user_id} answered poll {poll_id} with options: {selected_option_ids}")
    
#     # Получаем текущий прогресс пользователя
#     try:
#         current_progress = await get_current_question(user_id)
#         if not current_progress:
#             logger.warning(f"No current progress found for user {user_id}")
#             return
        
#         question_id = current_progress.question_id
#         logger.info(f"Processing poll answer for user {user_id}, question {question_id}")
        
#         # Загружаем данные викторины
#         quiz_data = await load_quiz_data()
#         question = next((q for q in quiz_data[0]["questions"] if q["id"] == question_id), None)
        
#         if not question:
#             logger.warning(f"No question found for ID {question_id}")
#             return
        
#         # Определяем правильный ответ (обновленная логика под твою структуру)
#         correct_answer_index = None
#         for i, answer in enumerate(question["answers"]):
#             if answer.get("check") == 1:
#                 correct_answer_index = i
#                 break
        
#         # Проверяем, правильно ли ответил пользователь
#         is_correct = correct_answer_index in selected_option_ids
        
#         # Обновляем прогресс
#         await update_quiz_progress(user_id, question_id, 1 if is_correct else 0)
#         logger.info(f"Updated quiz progress for user {user_id}, question {question_id}, correct: {is_correct}")
        
#         # Отправляем сообщение о результате (необязательно, так как Telegram сам показывает результат)
#         # Но можно добавить дополнительную мотивацию
#         if is_correct:
#             await poll_answer.bot.send_message(
#                 user_id, 
#                 "Правильно, бро! 🎉 Продолжаем? /quiz"
#             )
#         else:
#             await poll_answer.bot.send_message(
#                 user_id, 
#                 "Не угадал, бро! 😅 Но не сдавайся! /quiz"
#             )
            
#     except Exception as e:
#         logger.error(f"Failed to process poll answer for user {user_id}: {e}")
#         try:
#             await poll_answer.bot.send_message(
#                 user_id, 
#                 "Ошибка обработки ответа, бро! Попробуй позже. 😎"
#             )
#         except:
#             pass

# @router.message(Command("reset"))
# async def reset_progress(message: Message):
#     logger.info(f"User {message.from_user.id} requested progress reset")
#     user = await get_user(message.from_user.id)
#     if not user:
#         logger.warning(f"User {message.from_user.id} not registered")
#         await message.answer("Сначала отправь свой номер через /start, бро! 😎")
#         return
    
#     try:
#         async with async_session() as session:
#             async with session.begin():
#                 await session.execute(
#                     delete(QuizProgress).filter_by(telegram_id=message.from_user.id)
#                 )
#                 await session.commit()
#         logger.info(f"Progress reset for user {message.from_user.id}")
#         await message.answer("Твой прогресс сброшен, бро! Начать викторину? /quiz")
#     except Exception as e:
#         logger.error(f"Failed to reset progress for user {message.from_user.id}: {e}")
#         await message.answer("Ошибка сброса прогресса, бро! Попробуй позже. 😎")

# @router.message(Command("list_questions"))
# async def list_questions(message: Message):
#     logger.info(f"User {message.from_user.id} requested question list")
#     try:
#         quiz_data = await load_quiz_data()
#         question_ids = [q["id"] for q in quiz_data[0]["questions"]]
#         logger.info(f"Question IDs for user {message.from_user.id}: {question_ids}")
#         await message.answer(f"Доступные ID вопросов: {question_ids}")
#     except Exception as e:
#         logger.error(f"Failed to list questions: {e}")
#         await message.answer("Ошибка загрузки вопросов, бро! Попробуй позже. 😎")

import os
from aiogram import Router, F
from aiogram.types import Message, PollAnswer
from aiogram.filters import Command
from sqlalchemy import delete
from services.quiz_service import load_quiz_data, load_image
from database.db import add_quiz_progress, update_quiz_progress, get_current_question, get_user, async_session, get_user_language
from utils.logging import setup_logging
from database.models import QuizProgress
from keyboards.reply import get_test_selection_keyboard, STOP_BUTTON
from config.config import LANG_FILES

router = Router()
logger = setup_logging()



async def send_next_question(user_id: int, bot, test_id: int):
    """Отправляет следующий вопрос пользователю"""
    
    # Получаем текущий прогресс
    current_progress = await get_current_question(user_id)
    
    # Читаем вопросы из JSON
    try:
        lang_code = await get_user_language(user_id)
        quiz_data = await load_quiz_data(lang=lang_code)
        logger.info(f"Loaded quiz data with {len(quiz_data[0]['questions'])} questions")
        question_ids = [q["id"] for q in quiz_data[0]["questions"]]
        logger.info(f"Available question IDs: {question_ids}")
    except Exception as e:
        logger.error(f"Failed to load quiz data: {e}")
        await bot.send_message(user_id, "Ошибка загрузки вопросов, бро! Попробуй позже. 😎")
        return False
    
    # Проверяем, есть ли вопросы
    if not quiz_data or not quiz_data[0].get("questions"):
        logger.error("Quiz data is empty or has no questions")
        await bot.send_message(user_id, "Нет вопросов для викторины, бро! 😎")
        return False
    
    # Определяем ID следующего вопроса
    if current_progress:
        # Ищем следующий ID из доступных
        current_id = current_progress.question_id
        available_ids = sorted([q["id"] for q in quiz_data[0]["questions"]])
        next_id = next((id for id in available_ids if id > current_id), None)
        
        if not next_id:
            # Викторина завершена
            await bot.send_message(user_id, "🎉 Викторина завершена! Молодец, бро! 🚀\n\nЧтобы пройти снова: /reset затем /quiz")
            return False
            
        question_id = next_id
    else:
        # Берем первый доступный ID
        question_id = min(q["id"] for q in quiz_data[0]["questions"])
    
    logger.info(f"User {user_id} next question_id: {question_id}")
    
    # Ищем вопрос по ID
    question = next((q for q in quiz_data[0]["questions"] if q["id"] == question_id), None)
    if not question:
        logger.warning(f"No question found for ID {question_id}")
        await bot.send_message(user_id, "Викторина закончена или вопросов больше нет! Молодец, бро! 🚀")
        return False
    
    # Добавляем вопрос в прогресс
    try:
        await add_quiz_progress(user_id, question_id)
        logger.info(f"Added quiz progress for user {user_id}, question {question_id}")
    except Exception as e:
        logger.error(f"Failed to add quiz progress: {e}")
        await bot.send_message(user_id, "Ошибка сохранения прогресса, бро! Попробуй позже. 😎")
        return False
    
    # Извлекаем текст вопроса и путь к изображению
    try:
        question_text = next(item["value"] for item in question["body"] if item["type"] == 1)
        image_path = next((item["value"] for item in question["body"] if item["type"] == 2), None)
        logger.info(f"Question {question_id} text: {question_text}, image: {image_path}")
    except Exception as e:
        logger.error(f"Failed to parse question {question_id}: {e}")
        await bot.send_message(user_id, "Ошибка в формате вопроса, бро! Попробуй позже. 😎")
        return False
    
    # Подготавливаем варианты ответов для Quiz-Mode
    try:
        options = []
        correct_option_id = None
        
        for i, answer in enumerate(question["answers"]):
            # Извлекаем текст ответа из body массива
            try:
                answer_text = next(item["value"] for item in answer["body"] if item["type"] == 1)
                options.append(answer_text)
                
                # Проверяем правильность ответа
                if answer["check"] == 1:
                    correct_option_id = i
                    
            except Exception as e:
                logger.error(f"Failed to parse answer {i} for question {question_id}: {e}")
                continue
        
        if not options:
            logger.error(f"No valid options found for question {question_id}")
            await bot.send_message(user_id, "Ошибка в вариантах ответа, бро! Попробуй позже. 😎")
            return False
        
        if correct_option_id is None:
            logger.error(f"No correct answer found for question {question_id}")
            await bot.send_message(user_id, "Ошибка в вопросе - нет правильного ответа, бро! 😎")
            return False
            
        logger.info(f"Question {question_id} options: {options}, correct: {correct_option_id}")
    except Exception as e:
        logger.error(f"Failed to prepare options for question {question_id}: {e}")
        await bot.send_message(user_id, "Ошибка подготовки вариантов ответа, бро! Попробуй позже. 😎")
        return False
    
    # Отправляем вопрос в Quiz-Mode
    try:
        if image_path:
            try:
                image_data = await load_image(image_path)
                await bot.send_photo(user_id, photo=image_data)
            except Exception as e:
                logger.error(f"Image load failed: {e}")
   


        full_text = f"❓ {question_text}\n\n" + "\n".join(
            [f"{i+1}. {opt}" for i, opt in enumerate(options)]
        )

        await bot.send_message(user_id, full_text)

        # Короткие варианты для опроса
        poll_options = [str(i+1) for i in range(len(options))]
        poll_message = await bot.send_poll(
            chat_id=user_id,
            question="Выберите номер ответа 👇",   # фиксированный заголовок
            options=poll_options,
            type="quiz",
            correct_option_id=correct_option_id,
            is_anonymous=False
        )
        logger.info(f"Sent quiz poll {poll_message.poll.id} for question {question_id} to user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send quiz poll for question {question_id}: {e}")
        await bot.send_message(user_id, "Ошибка отправки опроса, бро! Попробуй позже. 😎")
        return False
    
@router.message(F.text == "🚀 Начать тест")
async def start_quiz(message: Message):
    user = await get_user(message.from_user.id)
    if not user:
        await message.answer("Сначала отправь свой номер через /start, бро! 😎")
        return

    # Берем язык пользователя
    lang_code = await get_user_language(message.from_user.id)
    if not lang_code:
        await message.answer("Сначала выбери язык через 🌐 Установить язык 😎")
        return

    # Проверяем, есть ли JSON для языка
    import os

    file_path = LANG_FILES.get(lang_code)
    print(f"lang_code={lang_code}, file_path={file_path}, exists={os.path.isfile(file_path)}")

    if not file_path:
        logger.error(f"No quiz file mapped for language: {lang_code}")
        await message.answer("Для этого языка пока нет тестов 😢")
        return
    # Загружаем тесты для выбранного языка
    try:
        tests_json = await load_quiz_data(lang_code)
    except Exception as e:
        user_id = message.from_user.id
        logger.error(f"Ошибка при загрузке тестов для {lang_code}: {e}")
        lang_code = await get_user_language(message.from_user.id)
        logger.error(f"Failed to get user language for user {user_id}, ger: {lang_code}")
        await message.answer("Произошла ошибка при загрузке тестов 😢")
        return

    if not tests_json:
        await message.answer("Тесты пока пусты 😢")
        return

    # Генерируем клавиатуру
    keyboard = get_test_selection_keyboard(tests_json)

    await message.answer(
        f"Выбери шаблон теста ({lang_code.upper()}):",
        reply_markup=keyboard
    )
import re


# 2️⃣ Пользователь выбрал конкретный тест
@router.message(F.text.startswith("📝 "))
async def select_test(message: Message):
    # Загружаем тесты из JSON
    try:
        lang_code = await get_user_language(message.from_user.id)
        tests_json = await load_quiz_data(lang_code) 
        logger.info(f"Loaded {len(tests_json)} tests from JSON")
    except Exception:
        await message.answer("Не удалось загрузить тесты 😢")
        logger.error("Failed to load tests from JSON")
        return

    # Получаем ID теста из сообщения
    match = re.search(r'\d+', message.text)
    if not match:
        await message.answer("Некорректный ID теста.")
        return

    test_id = int(match.group())
    try:
        test_id = test_id
    except ValueError:
        await message.answer("Некорректный ID теста.")
        return

    # Ищем тест по ID
    selected_test = next(
        (t for t in tests_json if t.get('exam_center_test_template', {}).get('id') == test_id),
        None
    )
    print(f"Выбранный ID: {test_id}")
    print(f"Доступные ID: {[t.get('exam_center_test_template', {}).get('id') for t in tests_json]}")

    
    if not selected_test:
        await message.answer("Не удалось найти тест, попробуй снова.")
        return
    await message.answer("Тест начался! Нажми 🛑 Стоп, чтобы завершить.", reply_markup=STOP_BUTTON)
    user_id = message.from_user.id
    # Запуск викторины по выбранному тесту
    await send_next_question(user_id, message.bot, test_id=test_id)

@router.poll_answer()
async def handle_poll_answer(poll_answer: PollAnswer):
    """Обрабатываем ответы на Quiz Poll и автоматически отправляем следующий вопрос"""
    user_id = poll_answer.user.id
    selected_option_ids = poll_answer.option_ids
    poll_id = poll_answer.poll_id
    
    logger.info(f"User {user_id} answered poll {poll_id} with options: {selected_option_ids}")
    
    # Получаем текущий прогресс пользователя
    try:
        current_progress = await get_current_question(user_id)
        if not current_progress:
            logger.warning(f"No current progress found for user {user_id}")
            return
        
        question_id = current_progress.question_id
        logger.info(f"Processing poll answer for user {user_id}, question {question_id}")
        
        # Загружаем данные викторины
        lang_code = await get_user_language(user_id)
        quiz_data = await load_quiz_data(lang=lang_code)
        question = next((q for q in quiz_data[0]["questions"] if q["id"] == question_id), None)
        
        if not question:
            logger.warning(f"No question found for ID {question_id}")
            return
        
        # Определяем правильный ответ (обновленная логика под твою структуру)
        correct_answer_index = None
        for i, answer in enumerate(question["answers"]):
            if answer.get("check") == 1:
                correct_answer_index = i
                break
        
        # Проверяем, правильно ли ответил пользователь
        is_correct = correct_answer_index in selected_option_ids
        
        # Обновляем прогресс
        await update_quiz_progress(user_id, question_id, 1 if is_correct else 0)
        logger.info(f"Updated quiz progress for user {user_id}, question {question_id}, correct: {is_correct}")
        
        # Отправляем короткое сообщение о результате
        result_message = "✅ Правильно!" if is_correct else "❌ Неправильно!"
        await poll_answer.bot.send_message(user_id, result_message)
        
        # Автоматически отправляем следующий вопрос через 1 секунду
        import asyncio
        await asyncio.sleep(1)
        
        success = await send_next_question(user_id, poll_answer.bot, test_id=current_progress.test_id)
        if not success:
            # Если следующего вопроса нет, викторина завершена
            logger.info(f"Quiz completed for user {user_id}")
            
    except Exception as e:
        logger.error(f"Failed to process poll answer for user {user_id}: {e}")
        try:
            await poll_answer.bot.send_message(
                user_id, 
                "Ошибка обработки ответа, бро! Попробуй позже. 😎"
            )
        except:
            pass

@router.message(Command("reset"))
async def reset_progress(message: Message):
    logger.info(f"User {message.from_user.id} requested progress reset")
    user = await get_user(message.from_user.id)
    if not user:
        logger.warning(f"User {message.from_user.id} not registered")
        await message.answer("Сначала отправь свой номер через /start, бро! 😎")
        return
    
    try:
        async with async_session() as session:
            async with session.begin():
                await session.execute(
                    delete(QuizProgress).filter_by(telegram_id=message.from_user.id)
                )
                await session.commit()
        logger.info(f"Progress reset for user {message.from_user.id}")
        await message.answer("Твой прогресс сброшен, бро! Начать викторину? /quiz")
    except Exception as e:
        logger.error(f"Failed to reset progress for user {message.from_user.id}: {e}")
        await message.answer("Ошибка сброса прогресса, бро! Попробуй позже. 😎")

@router.message(Command("list_questions"))
async def list_questions(message: Message):
    logger.info(f"User {message.from_user.id} requested question list")
    try:
        user_id = message.from_user.id
        lang_code = await get_user_language(user_id)
        quiz_data = await load_quiz_data(lang=lang_code)
        question_ids = [q["id"] for q in quiz_data[0]["questions"]]
        logger.info(f"Question IDs for user {message.from_user.id}: {question_ids}")
        await message.answer(f"Доступные ID вопросов: {question_ids}")
    except Exception as e:
        logger.error(f"Failed to list questions: {e}")
        await message.answer("Ошибка загрузки вопросов, бро! Попробуй позже. 😎")