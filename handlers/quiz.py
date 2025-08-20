import os
from aiogram import Router, F
from aiogram.types import Message, PollAnswer
from aiogram.filters import Command
from sqlalchemy import delete
from services.quiz_service import load_quiz_data, load_image, t
from database.db import (
    add_quiz_progress, update_quiz_progress, get_current_question, 
    get_user, async_session, get_user_language,
    get_current_question_for_test, reset_test_progress  # новые функции
)
from utils.logging import setup_logging
from database.models import QuizProgress
from keyboards.reply import get_test_selection_keyboard, get_stop_button, main_menu
from config.config import LANG_FILES

router = Router()
logger = setup_logging()

# Кэш для переводов кнопок
TEST_BUTTON_CACHE = None

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

async def get_quiz_results(user_id: int, test_id: int, lang_code: str):
    """Получаем результаты прохождения теста"""
    try:
        async with async_session() as session:
            from sqlalchemy import select, func
            
            # Получаем все ответы пользователя для данного test_id
            result = await session.execute(
                select(
                    func.count(QuizProgress.id).label('total'),
                    func.sum(QuizProgress.is_correct).label('correct')
                ).filter_by(
                    telegram_id=user_id, 
                    test_id=test_id
                ).where(
                    QuizProgress.is_correct.isnot(None)  # только отвеченные вопросы
                )
            )
            
            stats = result.first()
            total = stats.total or 0
            correct = stats.correct or 0
            
            if total == 0:
                return t(lang_code, "results.no_answers")
            
            percentage = round((correct / total) * 100, 1)
            
            result_text = t(lang_code, "results.summary").format(
                correct=correct,
                total=total,
                percentage=percentage
            )
            
            # Добавляем оценку
            if percentage >= 80:
                result_text += "\n" + t(lang_code, "results.excellent")
            elif percentage >= 60:
                result_text += "\n" + t(lang_code, "results.good")
            elif percentage >= 40:
                result_text += "\n" + t(lang_code, "results.satisfactory")
            else:
                result_text += "\n" + t(lang_code, "results.needs_improvement")
                
            return result_text
            
    except Exception as e:
        logger.error(f"Failed to get quiz results for user {user_id}, test {test_id}: {e}")
        return t(lang_code, "results.error")

async def send_next_question(user_id: int, bot, test_id: int):
    """Отправляет следующий вопрос пользователю"""
    
    # Получаем язык пользователя
    lang_code = await get_user_language(user_id)
    if not lang_code:
        lang_code = "kk"
    
    # Получаем текущий прогресс для данного test_id
    async with async_session() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(QuizProgress)
            .filter_by(telegram_id=user_id, test_id=test_id)
            .order_by(QuizProgress.created_at.desc())
        )
        current_progress = result.scalars().first()
    
    # Читаем вопросы из JSON
    try:
        quiz_data = await load_quiz_data(lang=lang_code)
        logger.info(f"Loaded quiz data with {len(quiz_data)} tests")
        
        # Находим тест по test_id
        current_test = next((test for test in quiz_data if test.get('exam_center_test_template', {}).get('id') == test_id), None)
        if not current_test:
            await bot.send_message(user_id, t(lang_code, "errors.test_not_found"))
            return False
            
        questions = current_test.get('questions', [])
        if not questions:
            await bot.send_message(user_id, t(lang_code, "errors.no_questions"))
            return False
            
        question_ids = [q["id"] for q in questions]
        logger.info(f"Available question IDs for test {test_id}: {question_ids}")
    except Exception as e:
        logger.error(f"Failed to load quiz data: {e}")
        await bot.send_message(user_id, t(lang_code, "errors.loading_questions"))
        return False
    
    # Определяем ID следующего вопроса
    if current_progress:
        # Ищем следующий ID из доступных
        current_id = current_progress.question_id
        available_ids = sorted([q["id"] for q in questions])
        next_id = next((id for id in available_ids if id > current_id), None)
        
        if not next_id:
            # Викторина завершена - показываем результаты
            results = await get_quiz_results(user_id, test_id, lang_code)
            await bot.send_message(user_id, results)
            
            # Возвращаем в главное меню
            await bot.send_message(
                user_id, 
                t(lang_code, "quiz.completed"),
                reply_markup=main_menu(lang_code)
            )
            return False
            
        question_id = next_id
    else:
        # Берем первый доступный ID
        question_id = min(q["id"] for q in questions)
    
    logger.info(f"User {user_id} next question_id: {question_id}")
    
    # Ищем вопрос по ID
    question = next((q for q in questions if q["id"] == question_id), None)
    if not question:
        logger.warning(f"No question found for ID {question_id}")
        await bot.send_message(user_id, t(lang_code, "quiz.completed"))
        return False
    
    # Добавляем вопрос в прогресс с test_id
    try:
        async with async_session() as session:
            async with session.begin():
                progress = QuizProgress(
                    telegram_id=user_id, 
                    test_id=test_id,  # Сохраняем test_id
                    question_id=question_id
                )
                session.add(progress)
                await session.commit()
        logger.info(f"Added quiz progress for user {user_id}, test {test_id}, question {question_id}")
    except Exception as e:
        logger.error(f"Failed to add quiz progress: {e}")
        await bot.send_message(user_id, t(lang_code, "errors.save_progress"))
        return False
    
    # Извлекаем текст вопроса и путь к изображению
    try:
        question_text = next(item["value"] for item in question["body"] if item["type"] == 1)
        image_path = next((item["value"] for item in question["body"] if item["type"] == 2), None)
        logger.info(f"Question {question_id} text: {question_text}, image: {image_path}")
    except Exception as e:
        logger.error(f"Failed to parse question {question_id}: {e}")
        await bot.send_message(user_id, t(lang_code, "errors.question_format"))
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
            await bot.send_message(user_id, t(lang_code, "errors.answer_options"))
            return False
        
        if correct_option_id is None:
            logger.error(f"No correct answer found for question {question_id}")
            await bot.send_message(user_id, t(lang_code, "errors.no_correct_answer"))
            return False
            
        logger.info(f"Question {question_id} options: {options}, correct: {correct_option_id}")
    except Exception as e:
        logger.error(f"Failed to prepare options for question {question_id}: {e}")
        await bot.send_message(user_id, t(lang_code, "errors.answer_options"))
        return False
    
    # Отправляем вопрос в Quiz-Mode
    try:
        if image_path:
            try:
                image_data = await load_image(image_path)
                await bot.send_photo(
                    user_id, 
                    photo=image_data, 
                    caption=t(lang_code, "quiz.image_caption")
                )
            except Exception as e:
                logger.error(f"Image load failed: {e}")

        # Формируем полный текст вопроса с вариантами
        full_text = t(lang_code, "quiz.question_prompt").format(question=question_text) + "\n\n" + "\n".join(
            [f"{i+1}. {opt}" for i, opt in enumerate(options)]
        )

        await bot.send_message(user_id, full_text)

        # Короткие варианты для опроса
        poll_options = [str(i+1) for i in range(len(options))]
        poll_message = await bot.send_poll(
            chat_id=user_id,
            question=t(lang_code, "quiz.select_answer"),
            options=poll_options,
            type="quiz",
            correct_option_id=correct_option_id,
            is_anonymous=False
        )
        logger.info(f"Sent quiz poll {poll_message.poll.id} for question {question_id} to user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send quiz poll for question {question_id}: {e}")
        await bot.send_message(user_id, t(lang_code, "errors.send_poll"))
        return False

# Динамический обработчик кнопки "Начать тест" на всех языках
@router.message(F.text.in_(get_test_buttons_cache()))
async def start_quiz(message: Message):
    user = await get_user(message.from_user.id)
    lang_code = await get_user_language(message.from_user.id) or "kk"
    
    if not user:
        await message.answer(t(lang_code, "errors.not_registered"))
        return

    if not lang_code:
        await message.answer(t(lang_code, "errors.no_language"))
        return

    # Проверяем, есть ли JSON для языка
    file_path = LANG_FILES.get(lang_code)
    
    if not file_path or not os.path.isfile(file_path):
        logger.error(f"No quiz file mapped for language: {lang_code}")
        await message.answer(t(lang_code, "language.no_tests"))
        return

    # Загружаем тесты для выбранного языка
    try:
        tests_json = await load_quiz_data(lang_code)
    except Exception as e:
        logger.error(f"Failed to load tests for {lang_code}: {e}")
        await message.answer(t(lang_code, "errors.load_tests"))
        return

    if not tests_json:
        await message.answer(t(lang_code, "errors.empty_tests"))
        return

    # Генерируем клавиатуру
    keyboard = get_test_selection_keyboard(tests_json)

    await message.answer(
        t(lang_code, "quiz.select_template").format(lang=lang_code.upper()),
        reply_markup=keyboard
    )

import re

# Пользователь выбрал конкретный тест
@router.message(F.text.startswith("📝 "))
async def select_test(message: Message):
    lang_code = await get_user_language(message.from_user.id) or "kk"
    
    # Загружаем тесты из JSON
    try:
        tests_json = await load_quiz_data(lang_code) 
        logger.info(f"Loaded {len(tests_json)} tests from JSON")
    except Exception:
        await message.answer(t(lang_code, "errors.load_tests"))
        logger.error("Failed to load tests from JSON")
        return

    # Получаем ID теста из сообщения
    match = re.search(r'\d+', message.text)
    if not match:
        await message.answer(t(lang_code, "errors.invalid_test_id"))
        return

    test_id = int(match.group())

    # Ищем тест по ID
    selected_test = next(
        (test for test in tests_json if test.get('exam_center_test_template', {}).get('id') == test_id),
        None
    )
    
    if not selected_test:
        await message.answer(t(lang_code, "errors.test_not_found"))
        return
    
    user_id = message.from_user.id

    try:
        await reset_test_progress(user_id) # Используем новую функцию
        logger.info(f"Automatically reset progress for user {user_id}")
    except Exception as e:
        logger.error(f"Failed to automatically reset progress for user {user_id}: {e}")
    
    await message.answer(
        t(lang_code, "quiz.started"), 
        reply_markup=get_stop_button(lang_code)
    )
    
    # Запуск викторины по выбранному тесту
    await send_next_question(user_id, message.bot, test_id=test_id)

@router.poll_answer()
async def handle_poll_answer(poll_answer: PollAnswer):
    """Обрабатываем ответы на Quiz Poll и автоматически отправляем следующий вопрос"""
    user_id = poll_answer.user.id
    selected_option_ids = poll_answer.option_ids
    poll_id = poll_answer.poll_id
    
    lang_code = await get_user_language(user_id) or "kk"
    
    logger.info(f"User {user_id} answered poll {poll_id} with options: {selected_option_ids}")
    
    # Получаем текущий прогресс пользователя
    try:
        # Получаем последний активный прогресс
        async with async_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(QuizProgress)
                .filter_by(telegram_id=user_id)
                .where(QuizProgress.is_correct.is_(None))  # не отвеченные
                .order_by(QuizProgress.created_at.desc())
            )
            current_progress = result.scalars().first()
            
        if not current_progress:
            logger.warning(f"No current progress found for user {user_id}")
            return
        
        question_id = current_progress.question_id
        test_id = current_progress.test_id
        logger.info(f"Processing poll answer for user {user_id}, test {test_id}, question {question_id}")
        
        # Загружаем данные викторины
        quiz_data = await load_quiz_data(lang=lang_code)
        current_test = next((test for test in quiz_data if test.get('exam_center_test_template', {}).get('id') == test_id), None)
        
        if not current_test:
            logger.warning(f"No test found for ID {test_id}")
            return
            
        question = next((q for q in current_test.get('questions', []) if q["id"] == question_id), None)
        
        if not question:
            logger.warning(f"No question found for ID {question_id}")
            return
        
        # Определяем правильный ответ
        correct_answer_index = None
        for i, answer in enumerate(question["answers"]):
            if answer.get("check") == 1:
                correct_answer_index = i
                break
        
        # Проверяем, правильно ли ответил пользователь
        is_correct = correct_answer_index in selected_option_ids
        
        # Обновляем прогресс
        async with async_session() as session:
            async with session.begin():
                result = await session.execute(
                    select(QuizProgress).filter_by(
                        telegram_id=user_id, 
                        test_id=test_id,
                        question_id=question_id
                    )
                )
                progress = result.scalars().first()
                if progress:
                    progress.is_correct = 1 if is_correct else 0
                    await session.commit()
        
        logger.info(f"Updated quiz progress for user {user_id}, test {test_id}, question {question_id}, correct: {is_correct}")
        
        # Отправляем короткое сообщение о результате
        result_message = t(lang_code, "quiz.correct") if is_correct else t(lang_code, "quiz.incorrect")
        await poll_answer.bot.send_message(user_id, result_message)
        
        # Автоматически отправляем следующий вопрос через 1 секунду
        import asyncio
        await asyncio.sleep(1)
        
        success = await send_next_question(user_id, poll_answer.bot, test_id=test_id)
        if not success:
            # Если следующего вопроса нет, викторина завершена
            logger.info(f"Quiz completed for user {user_id}, test {test_id}")
            
    except Exception as e:
        logger.error(f"Failed to process poll answer for user {user_id}: {e}")
        try:
            await poll_answer.bot.send_message(
                user_id, 
                t(lang_code, "errors.process_answer")
            )
        except:
            pass

@router.message(Command("reset"))
async def reset_progress(message: Message):
    lang_code = await get_user_language(message.from_user.id) or "kk"
    logger.info(f"User {message.from_user.id} requested progress reset")
    user = await get_user(message.from_user.id)
    if not user:
        logger.warning(f"User {message.from_user.id} not registered")
        await message.answer(t(lang_code, "errors.not_registered"))
        return
    
    try:
        async with async_session() as session:
            async with session.begin():
                await session.execute(
                    delete(QuizProgress).filter_by(telegram_id=message.from_user.id)
                )
                await session.commit()
        logger.info(f"Progress reset for user {message.from_user.id}")
        await message.answer(t(lang_code, "commands.reset"), reply_markup=main_menu(lang_code))
    except Exception as e:
        logger.error(f"Failed to reset progress for user {message.from_user.id}: {e}")
        await message.answer(t(lang_code, "errors.reset_progress"))

@router.message(Command("list_questions"))
async def list_questions(message: Message):
    lang_code = await get_user_language(message.from_user.id) or "kk"
    logger.info(f"User {message.from_user.id} requested question list")
    try:
        quiz_data = await load_quiz_data(lang=lang_code)
        # Показываем вопросы для всех тестов
        all_question_ids = []
        for test in quiz_data:
            test_id = test.get('exam_center_test_template', {}).get('id')
            questions = test.get('questions', [])
            question_ids = [q["id"] for q in questions]
            all_question_ids.append(f"Тест {test_id}: {question_ids}")
        
        result_text = "\n".join(all_question_ids)
        logger.info(f"Question IDs for user {message.from_user.id}: {result_text}")
        await message.answer(t(lang_code, "commands.list_questions").format(ids=result_text))
    except Exception as e:
        logger.error(f"Failed to list questions: {e}")
        await message.answer(t(lang_code, "errors.loading_questions"))