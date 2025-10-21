from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
import asyncio


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
            self.engine, class_=AsyncSession, expire_on_commit=False
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


# Создаем экземпляр базы данных
database = Database()


if __name__ == "__main__":
    asyncio.run(database.drop_tables())
    asyncio.run(database.create_tables())
