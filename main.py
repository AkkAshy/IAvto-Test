from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from config.config import TELEGRAM_TOKEN
from handlers.start import router as start_router
from database.db import init_db
from handlers.quiz import router as quiz_router
from utils.logging import setup_logging

async def main():
    # Инициализация базы данных
    await init_db()

    logger = setup_logging()
    logger.info("Starting bot...")
    
    # Инициализация бота и диспетчера
    bot = Bot(token=TELEGRAM_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Подключаем роутеры
    dp.include_router(start_router)
    dp.include_router(quiz_router).poll_answer()
    
    # Запускаем бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())