from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, delete
from config.config import DATABASE_URL
from .models import Base, User, QuizProgress

# Создаем асинхронный движок
engine = create_async_engine(DATABASE_URL, echo=False)

# Создаем фабрику сессий
async_session = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def add_user(telegram_id: int, phone_number: str):
    async with async_session() as session:
        async with session.begin():
            user = User(telegram_id=telegram_id, phone_number=phone_number)
            session.add(user)
            await session.commit()

async def get_user(telegram_id: int):
    async with async_session() as session:
        result = await session.execute(select(User).filter_by(telegram_id=telegram_id))
        return result.scalars().first()

async def add_quiz_progress(telegram_id: int, question_id: int, test_id: int = None):
    async with async_session() as session:
        async with session.begin():
            progress = QuizProgress(
                telegram_id=telegram_id, 
                question_id=question_id,
                test_id=test_id
            )
            session.add(progress)
            await session.commit()

async def update_quiz_progress(telegram_id: int, question_id: int, is_correct: int, test_id: int = None):
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(QuizProgress).filter_by(
                    telegram_id=telegram_id, 
                    question_id=question_id,
                    test_id=test_id
                )
            )
            progress = result.scalars().first()
            if progress:
                progress.is_correct = is_correct
                await session.commit()

async def get_current_question_for_test(telegram_id: int, test_id: int):
    """Получить текущий прогресс для конкретного теста"""
    async with async_session() as session:
        result = await session.execute(
            select(QuizProgress)
            .filter_by(telegram_id=telegram_id, test_id=test_id)
            .order_by(QuizProgress.created_at.desc())
        )
        return result.scalars().first()

async def reset_test_progress(telegram_id: int, test_id: int):
    """Сбросить прогресс только для конкретного теста"""
    async with async_session() as session:
        async with session.begin():
            await session.execute(
                delete(QuizProgress).filter_by(telegram_id=telegram_id, test_id=test_id)
            )
            await session.commit()

async def get_test_results(telegram_id: int, test_id: int):
    """Получить результаты теста"""
    async with async_session() as session:
        from sqlalchemy import func
        result = await session.execute(
            select(
                func.count(QuizProgress.id).label('total'),
                func.sum(QuizProgress.is_correct).label('correct')
            ).filter_by(
                telegram_id=telegram_id, 
                test_id=test_id
            ).where(
                QuizProgress.is_correct.isnot(None)
            )
        )
        return result.first()

async def get_current_question(telegram_id: int):
    async with async_session() as session:
        result = await session.execute(
            select(QuizProgress).filter_by(telegram_id=telegram_id).order_by(QuizProgress.created_at.desc())
        )
        return result.scalars().first()
    
async def set_user_language(telegram_id: int, lang_code: str):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalars().first()
        
        if user:
            user.language = lang_code
        else:
            user = User(telegram_id=telegram_id, language=lang_code)
            session.add(user)
            

        await session.commit()


async def get_user_language(user_id: int) -> str:
    user = await get_user(user_id)
    if user and user.language:
        return user.language
    return "kaa"  # язык по умолчанию