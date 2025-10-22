from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import WordModel
from src.db.repositories.repo import Repository


class WordRepository(Repository):
    def __init__(self, session):
        super().__init__(session)

    async def add_word(
        word: str,
        significance: float,
        file_id: int,
        session: AsyncSession,
        ) -> None:
        word = WordModel(word, significance, file_id)
        session.add(word)
