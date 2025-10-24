import asyncio

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# класс для работы с бд
class Database:
    def __init__(self, db_url: str = "sqlite+aiosqlite:///./search.db"):
        self.engine = create_async_engine(
            db_url,
            echo=True,
            future=True,
        )
        self.async_session_maker = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False,
        )

    # основные методы для конфига бд
    async def create_tables(self):
        """Создание всех таблиц"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    async def drop_tables(self):
        """Удаление всех таблиц (для тестов)"""
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

    async def get_session(self):
        try:
            async with self.async_session_maker() as session:
                yield session
                await session.commit()
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_405_METHOD_NOT_ALLOWED,
                detail=f"Error with db query {e}",
            )


# Создаем экземпляр базы данных
database = Database()


if __name__ == "__main__":
    asyncio.run(database.drop_tables())
    asyncio.run(database.create_tables())
