from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import WordModel


class WordRepository:
    async def add_word(
        word: str,
        significance: float,
        file_id: int,
        session: AsyncSession,
        ) -> None:
        word = WordModel(word, significance, file_id)
        session.add(word)
