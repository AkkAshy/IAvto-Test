from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.ext.asyncio import create_async_engine, AsyncAttrs
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime



class Base(AsyncAttrs, DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    telegram_id = Column(Integer, primary_key=True)
    language = Column(String, nullable=False, default="kk")
    phone_number = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

class QuizProgress(Base):
    __tablename__ = "quiz_progress"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer)          # сохраняем telegram_id пользователя
    test_id = Column(Integer)              # просто ID теста из JSON
    question_id = Column(Integer)
    is_correct = Column(Integer, nullable=True)  # 1 - правильно, 0 - неправильно, NULL - не отвечено
    created_at = Column(DateTime, default=datetime.utcnow)