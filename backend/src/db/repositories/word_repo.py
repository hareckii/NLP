from sqlalchemy.ext.asyncio import AsyncSession

from src.db.models import WordModel
from src.db.repositories.repo import Repository


class WordRepository(Repository):
    def __init__(self, session: AsyncSession):
        super().__init__(session)

    async def add_word(
        self,
        word: WordModel,
        ) -> None:
        self.session.add(word)
